// Street View capture with a hard monthly budget.
// Metadata calls are free; only image downloads are billed (~$0.007 each).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const HOME = path.join(os.homedir(), "claude");
const LEDGER = path.join(HOME, "google-usage.json");
const MONTHLY_IMAGE_CAP = 300;
const MAX_IMAGES_PER_ADDRESS = 3;

function apiKey() {
  const env = fs.readFileSync(path.join(HOME, ".env"), "utf8");
  const m = env.match(/GOOGLE_MAPS_API_KEY=(\S+)/);
  if (!m) throw new Error("GOOGLE_MAPS_API_KEY missing in ~/claude/.env");
  return m[1];
}
function ledger() {
  const month = new Date().toISOString().slice(0, 7);
  let L = { month, images: 0, metadata: 0 };
  try { const x = JSON.parse(fs.readFileSync(LEDGER, "utf8")); if (x.month === month) L = x; } catch (e) {}
  return L;
}
const saveLedger = L => fs.writeFileSync(LEDGER, JSON.stringify(L, null, 2));

const bearing = (lat1, lon1, lat2, lon2) => {
  const t = Math.PI / 180, y = Math.sin((lon2 - lon1) * t) * Math.cos(lat2 * t);
  const x = Math.cos(lat1 * t) * Math.sin(lat2 * t) - Math.sin(lat1 * t) * Math.cos(lat2 * t) * Math.cos((lon2 - lon1) * t);
  return (Math.atan2(y, x) / t + 360) % 360;
};
const meters = (a, b) => Math.hypot((a.lat - b.lat) * 111320, (a.lng - b.lng) * 111320 * Math.cos(a.lat * Math.PI / 180));

// target: {lat, lon}; probes: extra points (e.g. parcel corners) to find side-angle panoramas
export async function captureStreetView(target, probes, outDir, get) {
  const key = apiKey(), L = ledger();
  const found = new Map();
  for (const p of [target, ...probes]) {
    const url = `https://maps.googleapis.com/maps/api/streetview/metadata?location=${p.lat},${p.lon}&radius=50&source=outdoor&key=${key}`;
    const m = JSON.parse(await get(url));
    L.metadata++;
    if (m.status === "OK" && !found.has(m.pano_id)) found.set(m.pano_id, { pano: m.pano_id, date: m.date || null, lat: m.location.lat, lng: m.location.lng });
  }
  saveLedger(L);
  const panos = [...found.values()]
    .map(p => ({ ...p, dist: meters(p, { lat: target.lat, lng: target.lon }) }))
    .sort((a, b) => a.dist - b.dist);
  if (!panos.length) return { status: "NO_IMAGERY", images: [], note: "No Street View panorama within 50 m." };

  // keep panoramas that view the house from different angles
  const picks = [];
  for (const p of panos) {
    const h = bearing(p.lat, p.lng, target.lat, target.lon);
    if (picks.every(q => Math.abs(((q.heading - h + 540) % 360) - 180) > 25)) picks.push({ ...p, heading: Math.round(h) });
    if (picks.length >= MAX_IMAGES_PER_ADDRESS) break;
  }
  const remaining = MONTHLY_IMAGE_CAP - L.images;
  if (remaining <= 0) return { status: "BUDGET_CAP", images: [], panos, note: `Monthly cap of ${MONTHLY_IMAGE_CAP} images reached.` };
  fs.mkdirSync(outDir, { recursive: true });
  const images = [];
  for (const p of picks.slice(0, Math.min(picks.length, remaining))) {
    const url = `https://maps.googleapis.com/maps/api/streetview?size=640x640&pano=${p.pano}&heading=${p.heading}&fov=${p.dist < 25 ? 90 : 70}&pitch=5&source=outdoor&key=${key}`;
    const r = await fetch(url, { signal: AbortSignal.timeout(60000) });
    if (!r.ok) continue;
    const file = path.join(outDir, `sv_${images.length + 1}_h${p.heading}.jpg`);
    fs.writeFileSync(file, Buffer.from(await r.arrayBuffer()));
    L.images++; saveLedger(L);
    images.push({ file, pano: p.pano, date: p.date, heading: p.heading, distM: Math.round(p.dist) });
  }
  return { status: "OK", images, newest: panos.map(p => p.date).filter(Boolean).sort().pop() || null, ledger: { month: L.month, imagesThisMonth: L.images, cap: MONTHLY_IMAGE_CAP } };
}
