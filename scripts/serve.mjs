// Tiny static server for the checker. No dependencies.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".css": "text/css; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
};

export function resolveRequest(urlPath) {
  let decoded;
  try { decoded = decodeURIComponent((urlPath || "/").split("?")[0]); }
  catch (e) { return null; }
  const rel = decoded === "/" ? "index.html" : decoded.replace(/^\/+/, "");
  if (!rel || rel.split("/").some(p => p === ".git" || p === ".env" || p.startsWith(".env") || p === "node_modules")) return null;
  const full = path.resolve(ROOT, rel);
  const rootWithSep = ROOT.endsWith(path.sep) ? ROOT : ROOT + path.sep;
  if (full !== ROOT && !full.startsWith(rootWithSep)) return null;
  return full;
}

function send(res, status, body, type) {
  res.writeHead(status, {
    "Content-Type": type || "text/plain; charset=utf-8",
    "Cache-Control": "no-cache",
    "X-Content-Type-Options": "nosniff",
  });
  res.end(body);
}

export function createServer() {
  return http.createServer((req, res) => {
    const full = resolveRequest(req.url || "/");
    if (!full) { send(res, 403, "Forbidden"); return; }
    fs.stat(full, (err, st) => {
      if (err) { send(res, 404, "Not found"); return; }
      const file = st.isDirectory() ? path.join(full, "index.html") : full;
      if (file !== full && !file.startsWith(full + path.sep) && file !== full) { send(res, 403, "Forbidden"); return; }
      fs.readFile(file, (err2, data) => {
        if (err2) { send(res, 404, "Not found"); return; }
        const type = TYPES[path.extname(file).toLowerCase()] || "application/octet-stream";
        send(res, 200, data, type);
      });
    });
  });
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const port = Number(process.env.PORT) || 4173;
  const server = createServer();
  server.on("error", (err) => { console.error(err.message); process.exit(1); });
  server.listen(port, "127.0.0.1", () => {
    console.log(`http://127.0.0.1:${server.address().port}/`);
  });
}
