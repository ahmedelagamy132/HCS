// HCS Dev Server — run with: bun serve.mjs
import { join, extname } from "path";
import postgres from "postgres";

const PORT = 3000;
const ROOT = import.meta.dir;
const sql = postgres("postgres://postgres:postgres@localhost:5432/hcs_db"); // Adjust connection string if needed

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

Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    let pathname = url.pathname;

    // API Routes
    if (pathname.startsWith("/api/")) {
      try {
        if (pathname === "/api/kpis" && req.method === "GET") {
          const stats = await sql`SELECT * FROM public.v_system_kpis LIMIT 1`;
          return new Response(JSON.stringify(stats[0] || {}), { headers: { "Content-Type": "application/json" } });
        }
        if (pathname === "/api/clients" && req.method === "GET") {
          const clients = await sql`SELECT * FROM public.v_client_summary ORDER BY created_at DESC`;
          return new Response(JSON.stringify(clients), { headers: { "Content-Type": "application/json" } });
        }
        if (pathname === "/api/horses" && req.method === "GET") {
          const horses = await sql`SELECT * FROM public.v_horse_summary ORDER BY created_at DESC`;
          return new Response(JSON.stringify(horses), { headers: { "Content-Type": "application/json" } });
        }
        if (pathname === "/api/stables" && req.method === "GET") {
          const stables = await sql`SELECT * FROM public.v_stable_occupancy ORDER BY created_at DESC`;
          return new Response(JSON.stringify(stables), { headers: { "Content-Type": "application/json" } });
        }
        if (pathname === "/api/recent-activity" && req.method === "GET") {
          const activity = await sql`SELECT * FROM public.v_recent_activity LIMIT 10`;
          return new Response(JSON.stringify(activity), { headers: { "Content-Type": "application/json" } });
        }
        if (pathname === "/api/models" && req.method === "GET") {
          try {
            const ollamaRes = await fetch("http://127.0.0.1:11434/api/tags");
            if (!ollamaRes.ok) throw new Error("Ollama unavailable");
            const data = await ollamaRes.json();
            const models = data.models.map(m => {
              let cat = 'Text Generation';
              if (m.name.includes('vl') || m.name.includes('vision') || m.name.includes('llava')) cat = 'Vision Model';
              else if (m.name.includes('embed')) cat = 'Embedding Model';
              
              return {
                id: m.name,
                name: m.name.split(':')[0].toUpperCase(),
                version: m.name.split(':')[1] || 'latest',
                category: cat,
                size: (m.size / 1024 / 1024 / 1024).toFixed(1) + ' GB',
                status: 'Running'
              };
            });
            return new Response(JSON.stringify(models), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
             return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }
        
        return new Response(JSON.stringify({ error: "API route not found" }), { status: 404, headers: { "Content-Type": "application/json" } });
      } catch (err) {
        console.error("DB Error:", err);
        return new Response(JSON.stringify({ error: err.message }), { status: 500, headers: { "Content-Type": "application/json" } });
      }
    }

    // Default to index.html
    if (pathname === "/" || pathname === "") pathname = "/index.html";
    if (pathname === "/admin" || pathname === "/admin/") pathname = "/admin/dashboard.html";

    const filePath = join(ROOT, pathname);
    const file = Bun.file(filePath);

    if (await file.exists()) {
      const ext = extname(filePath).toLowerCase();
      const contentType = MIME[ext] ?? "application/octet-stream";
      return new Response(file, {
        headers: { "Content-Type": contentType },
      });
    }

    // 404 fallback
    return new Response("Not found", { status: 404 });
  },
});

console.log(`\n  HCS Dev Server`);
console.log(`  Local: http://localhost:${PORT}\n`);
