// HCS Dev Server — run with: bun serve.mjs
import { join, extname } from "path";
import { mkdir, rm, readdir, unlink } from "node:fs/promises";
import { exec } from "child_process";
import util from "util";
import postgres from "postgres";

const execAsync = util.promisify(exec);

async function startDatabase() {
  console.log("--> Checking PostgreSQL status...");
  try {
    // Try multiple common Windows PostgreSQL service names
    await execAsync('net start postgresql-x64-15 || net start postgresql-x64-16 || net start postgresql-x64-14 || net start postgresql-x64-13');
    console.log("--> PostgreSQL started successfully (or was already running).");
  } catch (err) {
    // Will fail if not running as Admin, or if service name differs/already running
    console.log("--> Notice: Could not automatically start PostgreSQL service.");
    console.log("    (You may need to run this terminal as Administrator, or the database is already running.)");
  }
}

// Start the database before serving
await startDatabase();

const PORT = 3000;
const ROOT = import.meta.dir;
const sql = postgres("postgres://postgres:postgres@localhost:5432/hcs_db", {
  onnotice: () => {},
  connect_timeout: 2,
  idle_timeout: 5,
  max_lifetime: 5,
  max: 1 // only one connection for dev
}); // Adjust connection string if needed

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
      try {        if (pathname === "/api/dashboard/charts" && req.method === "GET") {
          const alertsRes = await sql`SELECT severity as type, title, description as detail, created_at FROM health_alerts WHERE status = 'active' ORDER BY created_at DESC LIMIT 5`;
          const barItems = await sql`SELECT
            (SELECT COUNT(*) FROM horse_health_records) as heatlh_count,
            (SELECT COUNT(*) FROM gait_analyses) as gait_count,
            (SELECT COUNT(*) FROM behavior_records) as behavior_count,
            (SELECT COUNT(*) FROM diet_plans) as diet_count,
            (SELECT COUNT(*) FROM medical_records) as disease_count`;
          const regRes = await sql`
            WITH months AS (
              SELECT generate_series(date_trunc('month', current_date) - interval '11 months', date_trunc('month', current_date), '1 month'::interval) as m_start
            )
            SELECT to_char(m.m_start, 'Mon') as month, COUNT(h.id) as count
            FROM months m
            LEFT JOIN horses h ON date_trunc('month', h.created_at) = m.m_start
            GROUP BY m.m_start
            ORDER BY m.m_start;
          `;
          return new Response(JSON.stringify({ alerts: alertsRes, bar: barItems[0] || {}, reg: regRes }), { headers: { "Content-Type": "application/json" } });
        }        if (pathname === "/api/kpis" && req.method === "GET") {
          const stats = await sql`SELECT * FROM public.v_system_kpis LIMIT 1`;
          return new Response(JSON.stringify(stats[0] || {}), { headers: { "Content-Type": "application/json" } });
        }
        if (pathname === "/api/clients" && req.method === "GET") {
          try {
            const clients = await sql`SELECT * FROM public.v_client_summary ORDER BY created_at DESC`;
            return new Response(JSON.stringify(clients), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            console.error("DB Error fetching clients, returning mock data:", e.message);
            return new Response(JSON.stringify([]), { headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/clients" && req.method === "POST") {
          try {
            const body = await req.json();
            const { full_name, email, phone, region } = body;
            const client_code = 'CLT-' + Math.random().toString(36).substring(2,8).toUpperCase();
            
            try {
              await sql`INSERT INTO clients (client_code, full_name, email, phone, region, status)
                        VALUES (${client_code}, ${full_name}, ${email}, ${phone || null}, ${region || null}, 'active')`;
            } catch(dbErr) {
              console.error("DB failed on insert:", dbErr.message); throw dbErr;
            }
            
            return new Response(JSON.stringify({ success: true }), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/horses" && req.method === "GET") {
          try {
            const horses = await sql`SELECT * FROM public.v_horse_summary ORDER BY created_at DESC`;
            return new Response(JSON.stringify(horses), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            console.error("DB Error fetching horses, returning mock data:", e.message);
            return new Response(JSON.stringify([]), { headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/horses" && req.method === "POST") {
          try {
            const body = await req.json();
            const { name, breed, color, gender } = body;
            const horse_code = 'HRS-' + Math.random().toString(36).substring(2,8).toUpperCase();
            
            try {
              await sql`INSERT INTO horses (horse_code, name, breed, color, health_status, is_active)
                        VALUES (${horse_code}, ${name}, ${breed || null}, ${color || null}, 'good', true)`;
            } catch(dbErr) {
              console.error("DB failed on insert:", dbErr.message); throw dbErr;
            }
            
            return new Response(JSON.stringify({ success: true }), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/stables" && req.method === "GET") {
          try {
            const stables = await sql`SELECT * FROM public.v_stable_occupancy`;
            return new Response(JSON.stringify(stables), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            console.error("DB Error fetching stables, returning mock data:", e.message);
            return new Response(JSON.stringify([]), { headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/stables" && req.method === "POST") {
          try {
            const body = await req.json();
            const { name, location, capacity } = body;
            const stable_code = 'STB-' + Math.random().toString(36).substring(2,8).toUpperCase();
            
            try {
              await sql`INSERT INTO stables (stable_code, name, city, capacity, status)
                        VALUES (${stable_code}, ${name}, ${location || null}, ${capacity || 0}, 'active')`;
            } catch(dbErr) {
              console.error("DB failed on insert:", dbErr.message); throw dbErr;
            }
            
            return new Response(JSON.stringify({ success: true }), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/admins" && req.method === "GET") {
          try {
            const admins = await sql`SELECT id, admin_code, full_name, email, role, is_active, created_at FROM admin_users ORDER BY created_at DESC`;
            return new Response(JSON.stringify(admins), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            console.error("DB Error fetching admins, returning mock data:", e.message);
            return new Response(JSON.stringify([]), { headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/admins" && req.method === "POST") {
          try {
            const body = await req.json();
            const { full_name, email, role, password } = body;
              let dbRole = 'view_only';
              if (role) {
                 const rl = role.toLowerCase();
                 if (rl.includes('super')) dbRole = 'super_admin';
                 else if (rl.includes('staff') || rl.includes('system') || rl.includes('admin')) dbRole = 'staff_admin';
              }
            const admin_code = 'ADM-' + Math.random().toString(36).substring(2,8).toUpperCase();
            
            try {
              await sql`INSERT INTO admin_users (admin_code, full_name, email, role, password_hash)
                        VALUES (${admin_code}, ${full_name}, ${email}, ${dbRole}, crypt(${password || 'welcome123'}, gen_salt('bf',12)))`;
            } catch(dbErr) {
              console.error("DB failed on insert:", dbErr.message); throw dbErr;
            }
            
            return new Response(JSON.stringify({ success: true }), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/recent-activity" && req.method === "GET") {
          const activity = await sql`SELECT * FROM public.v_recent_activity LIMIT 10`;
          return new Response(JSON.stringify(activity), { headers: { "Content-Type": "application/json" } });
        }
        if (pathname === "/api/analyze" && req.method === "POST") {
          try {
            const body = await req.json();
            const ollamaReq = {
              model: body.model || "llava",
              prompt: body.prompt || "Analyze this image.",
              stream: false
            };
            if (body.image) {
               ollamaReq.images = [body.image];
            }
            const ollamaRes = await fetch("http://127.0.0.1:11434/api/generate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(ollamaReq)
            });
            if (!ollamaRes.ok) {
              const errText = await ollamaRes.text();
              throw new Error("Ollama generation failed: " + ollamaRes.status + " " + errText);
            }
            const data = await ollamaRes.json();
            return new Response(JSON.stringify({ response: data.response }), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
             return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/account" && req.method === "GET") {
          try {
            // Mocking hardcoded admin for UI design purposes
            let acc;
            try {
              acc = await sql`SELECT * FROM admin_users WHERE admin_code = 'ADM-001' LIMIT 1`;
            } catch (dbErr) {
              console.warn("DB connection or query failed for account. Falling back to mock data.", dbErr.message);
            }
            
            if (!acc || !acc[0]) {
              console.warn("Returning mock account data to prevent 404 on frontend.");
              return new Response(JSON.stringify({
                admin_code: "ADM-001",
                full_name: "Ahmed Al-Mansouri (Mock)",
                email: "ahmed@hcs.ai",
                role: "super_admin",
                login_count: 42,
                last_login_at: new Date().toISOString(),
                created_at: new Date(Date.now() - 365*24*60*60*1000).toISOString()
              }), { headers: { "Content-Type": "application/json" } });
            }
            return new Response(JSON.stringify(acc[0]), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/account" && req.method === "POST") {
          try {
            const body = await req.json();
            const { full_name, email } = body;
            await sql`UPDATE admin_users SET full_name = ${full_name}, email = ${email}, updated_at = NOW() WHERE admin_code = 'ADM-001'`;
            return new Response(JSON.stringify({ success: true }), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/account/password" && req.method === "POST") {
          try {
            const body = await req.json();
            // Crypt and update password logic
            await sql`UPDATE admin_users SET password_hash = crypt(${body.password}, gen_salt('bf',12)), updated_at = NOW() WHERE admin_code = 'ADM-001'`;
            return new Response(JSON.stringify({ success: true }), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }
        if (pathname === "/api/models" && req.method === "GET") {
          try {
            let models = [];
            try {
              const ollamaRes = await fetch("http://127.0.0.1:11434/api/tags");
              if (ollamaRes.ok) {
                const data = await ollamaRes.json();
                models = data.models.map(m => {
                  let cat = 'Text Generation';
                  if (m.name.includes('vl') || m.name.includes('vision') || m.name.includes('llava') || m.name.includes('moondream')) cat = 'Vision Model';
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
              }
            } catch (err) {
              console.warn("Ollama unavailable, continuing without Ollama models.");
            }
            
            // Add DLC Gait Analysis to the models list
            models.push({
              id: "dlc-gait-pose",
              name: "GAIT & POSE ANALYSIS",
              version: "v2.0",
              category: "Vision Model",
              size: "2.4 GB",
              status: "Running"
            });

            return new Response(JSON.stringify(models), { headers: { "Content-Type": "application/json" } });
          } catch(e) {
             return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: { "Content-Type": "application/json" } });
          }
        }

        if (pathname === "/api/analyze-direct-dlc" && req.method === "POST") {
            try {
              console.log("[API] Receiving video for Direct DeepLabCut Analysis...");
              const formData = await req.formData();
              const videoFile = formData.get("file");
              if (!videoFile) throw new Error("No video provided");
  
              // Save video locally
              const tempDir = join(ROOT, 'testing_videos');
              await mkdir(tempDir, { recursive: true });
              
              const safeName = Date.now() + '-' + videoFile.name.replace(/[^a-zA-Z0-9.]/g, '');
              const inputVideoPath = join(tempDir, safeName);
              await Bun.write(inputVideoPath, videoFile);
  
              console.log(`[API] Saved video to ${inputVideoPath}, booting DeepLabCut script...`);
              
              // Spawn conda shell to run the local script
              const { exec } = require('child_process');
              const scriptPath = join(ROOT, 'ml_scripts', 'analyze_video_dlc.py');
              
              // We return a promise that resolves when the python script exits
              const dlcResult = await new Promise((resolve, reject) => {
                    const cmd = `conda run -p "E:\\DEEPLABCUT2" python "${scriptPath}" "${inputVideoPath}" --shuffle 4`;
                    const pyProcess = exec(cmd, { cwd: ROOT, maxBuffer: 1024 * 1024 * 10, env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }, (error, stdout, stderr) => {
                        const match = stdout.match(/__DLC_JSON_RESULT__=(.*)/);
                        if (match && match[1]) {
                            try {
                                resolve(JSON.parse(match[1].trim()));
                            } catch (e) {
                                console.error("[API DLC OUTPUT PARSE ERROR]:", e);
                                reject(new Error("Analysis succeeded but JSON parsing failed."));
                            }
                        } else if (error) {
                            console.error(`[API DLC ERROR]: ${stderr || error.message}`);
                            return reject(new Error(stderr || error.message));
                      } else {
                          console.error("[API DLC OUTPUT]:", stdout);
                          reject(new Error("Analysis succeeded but could not locate the output JSON in the script output."));
                      }
                  });
                  pyProcess.stdout.pipe(process.stdout);
                  pyProcess.stderr.pipe(process.stderr);                });            const dlcOutputVid = dlcResult.output_video_path;
            let finalUrl = '';
            if (dlcOutputVid) {
                const relativePath = dlcOutputVid.replace(ROOT, '').replace(/\\/g, '/');
                finalUrl = relativePath.startsWith('/') ? relativePath : '/' + relativePath;
            }
            
            return new Response(JSON.stringify({
                status: 'success',
                download_url: finalUrl,
                behavior_statistics: dlcResult.behavior_statistics,
                total_frames: dlcResult.total_frames,
                fps: dlcResult.fps,
                  message: 'Analysis complete.'
              }), { headers: { "Content-Type": "application/json" } });
  
            } catch (e) {
               console.error("DLC Route Error:", e);
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

    // Try finding the exact file
    let filePath = join(ROOT, pathname);
    let file = Bun.file(filePath);

    if (await file.exists()) {
      const ext = extname(filePath).toLowerCase();
      const contentType = MIME[ext] ?? "application/octet-stream";
      return new Response(file, {
        headers: { "Content-Type": contentType },
      });
    }

    // Try appending .html (clean URL routes)
    const htmlFilePath = join(ROOT, pathname + ".html");
    const htmlFile = Bun.file(htmlFilePath);
    if (await htmlFile.exists()) {
      return new Response(htmlFile, {
        headers: { "Content-Type": "text/html" },
      });
    }

    // 404 fallback
    return new Response("Not found", { status: 404 });
  },
});

console.log(`\n  HCS Dev Server`);
console.log(`  Local: http://localhost:${PORT}\n`);



