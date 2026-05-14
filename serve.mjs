// HCS Dev Server — run with: bun serve.mjs
import { join, extname } from "path";
import { mkdir, rm, readdir, unlink } from "node:fs/promises";
import { exec, spawn } from "child_process";
import util from "util";
import postgres from "postgres";
import { randomBytes } from "crypto";

const execAsync = util.promisify(exec);

async function startDatabase() {
  console.log("--> Checking PostgreSQL status...");
  try {
    await execAsync('net start postgresql-x64-15 || net start postgresql-x64-16 || net start postgresql-x64-14 || net start postgresql-x64-13');
    console.log("--> PostgreSQL started successfully (or was already running).");
  } catch (err) {
    console.log("--> Notice: Could not automatically start PostgreSQL service.");
    console.log("    (You may need to run this terminal as Administrator, or the database is already running.)");
  }
}

await startDatabase();

const PORT = 3000;
const PYTHON_PORT = 8000;
const ROOT = import.meta.dir;
const sql = postgres("postgres://postgres:postgres@localhost:5432/hcs_db", {
  onnotice: () => {},
  connect_timeout: 2,
  idle_timeout: 5,
  max_lifetime: 5,
  max: 1
});

const MIME = {
  ".html": "text/html",
  ".css":  "text/css",
  ".js":   "application/javascript",
  ".mjs":  "application/javascript",
  ".json": "application/json",
  ".png":  "image/png",
  ".jpg":  "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif":  "image/gif",
  ".svg":  "image/svg+xml",
  ".ico":  "image/x-icon",
  ".woff": "font/woff",
  ".woff2":"font/woff2",
  ".ttf":  "font/ttf",
  ".webp": "image/webp",
};

// ═══ RTSP → WebSocket stream handler ═══
const activeStreams = new Map();

function startRtspStream(ws, rtspUrl) {
  try {
    const ffmpeg = spawn("ffmpeg", [
      "-rtsp_transport", "tcp",
      "-i", rtspUrl,
      "-f", "image2pipe",
      "-vcodec", "mjpeg",
      "-q:v", "8",
      "-r", "15",
      "-an",
      "pipe:1"
    ], {
      stdio: ["ignore", "pipe", "pipe"],
    });

    const streamId = randomBytes(8).toString("hex");
    let buffer = Buffer.alloc(0);
    let frameCount = 0;

    ffmpeg.stdout.on("data", (chunk) => {
      buffer = Buffer.concat([buffer, chunk]);
      while (true) {
        const soiIdx = buffer.indexOf(Buffer.from([0xFF, 0xD8]));
        if (soiIdx === -1) break;
        const eoiIdx = buffer.indexOf(Buffer.from([0xFF, 0xD9]), soiIdx);
        if (eoiIdx === -1) break;
        const frame = buffer.slice(soiIdx, eoiIdx + 2);
        try {
          if (ws.readyState === 1) {
            ws.send(frame);
            frameCount++;
          }
        } catch (e) {}
        buffer = buffer.slice(eoiIdx + 2);
      }
      if (buffer.length > 2 * 1024 * 1024) buffer = buffer.slice(-1 * 1024 * 1024);
    });

    ffmpeg.stderr.on("data", (d) => {
      // ffmpeg logs to stderr
    });

    ffmpeg.on("close", (code) => {
      console.log(`[RTSP Stream ${streamId}] ffmpeg exited code ${code}, frames: ${frameCount}`);
      try { ws.close(); } catch (e) {}
    });

    ffmpeg.on("error", (err) => {
      console.error(`[RTSP Stream ${streamId}] spawn error:`, err.message);
      try {
        ws.send(JSON.stringify({ type: "error", message: "FFmpeg not available. Install ffmpeg for RTSP streaming." }));
        ws.close();
      } catch (e) {}
    });

    activeStreams.set(ws, { ffmpeg, streamId });
  } catch (err) {
    console.error("RTSP stream start error:", err.message);
    try {
      ws.send(JSON.stringify({ type: "error", message: "Failed to start RTSP stream: " + err.message }));
    } catch (e) {}
  }
}

function stopRtspStream(ws) {
  const stream = activeStreams.get(ws);
  if (stream) {
    try { stream.ffmpeg.kill(); } catch (e) {}
    activeStreams.delete(ws);
  }
}

// ═══ SERVER ═══
Bun.serve({
  port: PORT,
  websocket: {
    open(ws) {
      const { rtspUrl } = ws.data || {};
      if (rtspUrl) {
        startRtspStream(ws, rtspUrl);
      }
    },
    close(ws) {
      stopRtspStream(ws);
    },
    message(ws, msg) {},
  },
  async fetch(req, server) {
    const url = new URL(req.url);
    let pathname = url.pathname;

    // ═══ WebSocket upgrade for RTSP streaming ═══
    if (pathname === "/ws/stream" && req.headers.get("upgrade")?.toLowerCase() === "websocket") {
      const rtspUrl = url.searchParams.get("url") || "";
      if (!rtspUrl) {
        return new Response("Missing ?url parameter", { status: 400 });
      }
      const upgraded = server.upgrade(req, {
        data: { rtspUrl }
      });
      if (!upgraded) {
        return new Response("WebSocket upgrade failed", { status: 500 });
      }
      return undefined;
    }

    // ═══ Proxy ALL /api/* routes to Python FastAPI backend ═══
    if (pathname.startsWith("/api/")) {
      try {
        const targetUrl = `http://127.0.0.1:${PYTHON_PORT}${pathname}${url.search}`;
        const proxyRes = await fetch(targetUrl, {
          method: req.method,
          headers: req.headers,
          body: req.method !== "GET" && req.method !== "HEAD" ? req.body : undefined,
          duplex: "half",
        });
        return new Response(proxyRes.body, {
          status: proxyRes.status,
          headers: proxyRes.headers,
        });
      } catch (err) {
        console.error("FastAPI proxy error:", err.message);
        return new Response(JSON.stringify({ error: "FastAPI backend unavailable. Is it running on port 8000?" }), {
          status: 502,
          headers: { "Content-Type": "application/json" },
        });
      }
    }

    // ═══ Static file routing ═══
    // Landing page
    if (pathname === "/" || pathname === "") pathname = "/admin/pages/landing-page.html";
    // Admin dashboard
    if (pathname === "/admin" || pathname === "/admin/") pathname = "/admin/pages/dashboard.html";

    // User portal routes
    if (pathname === "/user" || pathname === "/user/") pathname = "/user/dashboard.html";
    if (pathname === "/user/login" || pathname === "/user/login.html") pathname = "/user/login.html";
    if (pathname === "/user/dashboard") pathname = "/user/dashboard.html";
    if (pathname === "/user/horse-view") pathname = "/user/horse-view.html";

    // Map clean admin URLs to pages directory
    if (
      pathname.startsWith("/admin/") &&
      !pathname.startsWith("/admin/components/") &&
      !pathname.startsWith("/admin/css/") &&
      !pathname.startsWith("/admin/js/") &&
      !pathname.startsWith("/admin/assets/") &&
      !pathname.startsWith("/admin/pages/")
    ) {
      pathname = pathname.replace("/admin/", "/admin/pages/");
    }

    // Try exact path
    let filePath = join(ROOT, pathname);
    let file = Bun.file(filePath);
    if (await file.exists()) {
      const ext = extname(filePath).toLowerCase();
      const contentType = MIME[ext] ?? "application/octet-stream";
      return new Response(file, { headers: { "Content-Type": contentType } });
    }

    // Try appending .html
    const htmlFilePath = join(ROOT, pathname + ".html");
    const htmlFile = Bun.file(htmlFilePath);
    if (await htmlFile.exists()) {
      return new Response(htmlFile, { headers: { "Content-Type": "text/html" } });
    }

    // 404
    return new Response("Not found", { status: 404 });
  },
});

console.log(`\n  HCS Dev Server`);
console.log(`  Local: http://localhost:${PORT}`);
console.log(`  API proxy: http://localhost:${PORT}/api/* -> http://127.0.0.1:${PYTHON_PORT}\n`);
