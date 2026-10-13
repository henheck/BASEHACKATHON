// Texas address pre-screen for Base Power installs.
// Usage: node tx-screen.mjs "104 Gunner Rd, Buda, TX 78610"
// Queries free public sources, logs which ones answered, maps evidence to the 20 install
// requirements (yes / no / maybe) and writes records/<key>.json in the checker's record format.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { captureStreetView } from "./streetview.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const UA = { "User-Agent": "Mozilla/5.0 (base-install-screen)" };
const log = [];

async function get(url, opts = {}, tries = 4) {
  let last;
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(url, { ...opts, headers: { ...UA, ...(opts.headers || {}) }, signal: AbortSignal.timeout(60000) });
      const text = await r.text();
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return text;
    } catch (e) { last = e; await new Promise(res => setTimeout(res, 800 * (i + 1))); }
  }
  throw last;
}
const getJSON = async (url, opts) => JSON.parse(await get(url, opts));
async function source(name, url, fn) {
  const t0 = Date.now();
  try {
    const v = await fn();
    log.push({ name, url, ok: true, ms: Date.now() - t0, found: v != null && !(Array.isArray(v) && !v.length) });
    return v;
  } catch (e) {
    log.push({ name, url, ok: false, ms: Date.now() - t0, error: String(e.message || e).slice(0, 120) });
    return null;
  }
}
export const keyFor = a => {
  const map = { street: "st", avenue: "ave", road: "rd", drive: "dr", lane: "ln", court: "ct", boulevard: "blvd", place: "pl", west: "w", east: "e", north: "n", south: "s" };
  return String(a).toLowerCase().split(",")[0].replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter(Boolean).map(w => map[w] || w).join("-").slice(0, 120);
};

// geometry helpers (local feet)
const FT_PER_DEG = 364000;
const proj = (lat0, lon0) => ([x, y]) => [(x - lon0) * FT_PER_DEG * Math.cos(lat0 * Math.PI / 180), (y - lat0) * FT_PER_DEG];
const segDist = (p, a, b) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy;
  const t = L ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) : 0;
  return Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy));
};
const polyDist = (p, ring) => Math.min(...ring.slice(1).map((b, i) => segDist(p, ring[i], b)));
const inside = (pt, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const [xi, yi] = poly[i], [xj, yj] = poly[j]; if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) c = !c; } return c; };

async function main(address, facts = {}) {
  // 1. Geocode (Esri World rooftop-level, Census as fallback)
  let geo = await source("Geocoder · Esri World", "geocode.arcgis.com/.../findAddressCandidates", async () => {
    const r = await getJSON(`https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?SingleLine=${encodeURIComponent(address)}&f=json&outFields=Addr_type,Subregion,City,Region,RegionAbbr&maxLocations=1`);
    const c = r.candidates && r.candidates[0];
    return c && c.score >= 90 ? { lon: c.location.x, lat: c.location.y, matched: c.address, type: c.attributes.Addr_type, county: c.attributes.Subregion, city: c.attributes.City, state: c.attributes.RegionAbbr || c.attributes.Region } : null;
  });
  if (!geo) geo = await source("Geocoder · US Census", "geocoding.geo.census.gov/geocoder", async () => {
    const r = await getJSON(`https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address=${encodeURIComponent(address)}&benchmark=Public_AR_Current&format=json`);
    const m = r.result.addressMatches[0];
    return m ? { lon: m.coordinates.x, lat: m.coordinates.y, matched: m.matchedAddress, type: "range-interpolated", city: m.addressComponents.city, state: m.addressComponents.state } : null;
  });
  if (!geo) throw new Error("Address not found by any geocoder.");
  if (!/^(TX|Texas)$/i.test(geo.state || "")) throw new Error(`Outside Texas (${geo.state}). This screen is Texas-only.`);
  const { lat, lon } = geo;

  // 2. Statewide parcel (TxGIO StratMap, identify)
  const parcel = await source("Parcel · TxGIO StratMap statewide", "feature.geographic.texas.gov/.../stratmap_land_parcels_48_most_recent/MapServer/identify", async () => {
    const d = 0.0012;
    const r = await getJSON(`https://feature.geographic.texas.gov/arcgis/rest/services/Parcels/stratmap_land_parcels_48_most_recent/MapServer/identify?geometry=${lon},${lat}&geometryType=esriGeometryPoint&sr=4326&layers=all&tolerance=2&mapExtent=${lon - d},${lat - d},${lon + d},${lat + d}&imageDisplay=800,600,96&returnGeometry=true&f=json`);
    const f = r.results && r.results[0];
    if (!f) return null;
    const a = f.attributes;
    return { propId: a.PROP_ID, geoId: a.GEO_ID, county: a.COUNTY, legal: a.LEGAL_DESC, acres: Number(a.LEGAL_AREA || a.GIS_AREA) || null,
      landValue: Number(a.LAND_VALUE) || 0, impValue: Number(a.IMP_VALUE) || 0, valuesPublished: Number(a.LAND_VALUE) > 0, yearBuilt: Number(a.YEAR_BUILT) || null, taxYear: a.TAX_YEAR,
      acquired: a.DATE_ACQ, ownerIsEntity: /\b(LLC|INC|LP|LTD|HOLDINGS|HOMES|BUILDERS|CORP)\b/i.test(a.OWNER_NAME || ""), situs: (a.SITUS_ADDR || "").replace(/\s+/g, " "),
      ring: f.geometry && f.geometry.rings && f.geometry.rings[0] };
  });

  // 3. Utility (PUCT certified service areas: IOU / co-op / municipal)
  const PUCT = "https://services6.arcgis.com/N6Lzvtb46cpxThhu/arcgis/rest/services";
  const utility = await source("Utility · PUCT service areas (IOU, co-op, muni)", `${PUCT}/{IOU,COOP_DIST,MUNI}/FeatureServer`, async () => {
    const out = [];
    for (const [svc, id, type] of [["IOU", 300, "IOU"], ["COOP_DIST", 310, "Co-op"], ["MUNI", 320, "Municipal"]]) {
      const r = await getJSON(`${PUCT}/${svc}/FeatureServer/${id}/query?geometry=${lon}%2C${lat}&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=COMPANY_NAME&returnGeometry=false&f=json`);
      (r.features || []).forEach(f => out.push({ name: f.attributes.COMPANY_NAME, type }));
    }
    return out;
  });

  // 4. FEMA flood zone
  const flood = await source("Flood · FEMA NFHL", "hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28", async () => {
    const r = await getJSON(`https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query?geometry=${lon},${lat}&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=FLD_ZONE,ZONE_SUBTY,SFHA_TF&returnGeometry=false&f=json`);
    const f = r.features && r.features[0];
    return f ? { zone: f.attributes.FLD_ZONE, sfha: f.attributes.SFHA_TF === "T", sub: f.attributes.ZONE_SUBTY } : null;
  });

  // 5. Building footprint (OpenStreetMap; falls back to mirror)
  const footprint = await source("Footprint · OpenStreetMap Overpass", "overpass-api.de/api/interpreter", async () => {
    const q = `[out:json][timeout:40];way["building"](around:45,${lat},${lon});out geom;`;
    let r;
    for (const host of ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]) {
      try { r = JSON.parse(await get(host, { method: "POST", body: "data=" + encodeURIComponent(q), headers: { "Content-Type": "application/x-www-form-urlencoded" } }, 1)); break; } catch (e) {}
    }
    if (!r) throw new Error("Overpass unavailable");
    const ways = (r.elements || []).filter(e => e.geometry);
    if (!ways.length) return null;
    const P = proj(lat, lon), me = [0, 0];
    ways.sort((a, b) => polyDist(me, a.geometry.map(g => P([g.lon, g.lat]))) - polyDist(me, b.geometry.map(g => P([g.lon, g.lat]))));
    return ways[0].geometry.map(g => [g.lon, g.lat]);
  });

  // 5b. County appraisal district, current roll (wired: Hays)
  let cad = null;
  const county = ((parcel && parcel.county) || geo.county || "").toUpperCase().replace(/ COUNTY$/, "");
  if (county === "HAYS") cad = await source("Appraisal · Hays CAD map service (current roll)", "utility.arcgis.com/.../HaysCADWebService1/FeatureServer/0", async () => {
    const r = await getJSON(`https://utility.arcgis.com/usrsvcs/servers/02e3ae8dad2b4fba9d1927407c322e27/rest/services/HaysCADWebService1/FeatureServer/0/query?geometry=${lon}%2C${lat}&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=prop_id,land_val,imprv_val,Deed_Date,legal_desc&returnGeometry=false&f=json`);
    const f = r.features && r.features[0];
    return f ? { propId: f.attributes.prop_id, land: f.attributes.land_val, imprv: f.attributes.imprv_val, deed: f.attributes.Deed_Date } : null;
  });
  else log.push({ name: `Appraisal · ${county || "county"} CAD current roll`, url: "not wired yet (bulk export or portal)", ok: false, error: "Current-roll values not automated for this county yet" });

  let fp = footprint;
  if (!fp && (geo.city || "").toUpperCase() === "AUSTIN") fp = await source("Footprint · City of Austin building footprints", "services.arcgis.com/0L95CJ0VTaxqcmED/.../building_footprints_2017", async () => {
    const d = 0.0004;
    const r = await getJSON(`https://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/UTILITIESCOMMUNICATION_building_footprints_2017/FeatureServer/0/query?geometry=${lon - d},${lat - d},${lon + d},${lat + d}&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=OBJECTID&outSR=4326&returnGeometry=true&f=json`);
    const feats = (r.features || []).filter(f => f.geometry && f.geometry.rings);
    if (!feats.length) return null;
    const ring = parcel && parcel.ring, P = proj(lat, lon);
    const inParcel = ring ? feats.filter(f => inside(P(f.geometry.rings[0][0]), ring.map(P))) : feats;
    const pool = inParcel.length ? inParcel : feats;
    const area = rg => { let a = 0; const q = rg.map(P); for (let i = 0, j = q.length - 1; i < q.length; j = i++) a += (q[j][0] + q[i][0]) * (q[j][1] - q[i][1]); return Math.abs(a / 2); };
    pool.sort((a, b) => area(b.geometry.rings[0]) - area(a.geometry.rings[0]));
    return pool[0].geometry.rings[0];
  });

  // 6. Slope (USGS 3DEP point elevations inside the parcel)
  const slope = await source("Slope · USGS 3DEP (EPQS)", "epqs.nationalmap.gov/v1/json", async () => {
    const ring = parcel && parcel.ring;
    const xs = ring ? ring.map(p => p[0]) : [lon - 0.0002, lon + 0.0002], ys = ring ? ring.map(p => p[1]) : [lat - 0.0002, lat + 0.0002];
    const bx = [Math.min(...xs), Math.max(...xs)], by = [Math.min(...ys), Math.max(...ys)];
    const pts = [[0.5, 0.5], [0.2, 0.5], [0.8, 0.5], [0.5, 0.2], [0.5, 0.8]].map(([a, b]) => [bx[0] + a * (bx[1] - bx[0]), by[0] + b * (by[1] - by[0])]);
    const els = [];
    for (const [x, y] of pts) { const r = await getJSON(`https://epqs.nationalmap.gov/v1/json?x=${x}&y=${y}&units=Feet&wkid=4326`); els.push([x, y, Number(r.value)]); }
    const P = proj(lat, lon);
    let best = 0;
    for (const a of els) for (const b of els) { const d = Math.hypot(...P([a[0], a[1]]).map((v, i) => v - P([b[0], b[1]])[i])); if (d > 20) best = Math.max(best, Math.abs(a[2] - b[2]) / d); }
    return { pct: Math.round(best * 1000) / 10, elevFt: Math.round(els[0][2]) };
  });

  // 6b. Street View (free metadata first; max 3 billed images, hard monthly cap)
  const sv = await source("Street View · Google (metadata + up to 3 images)", "maps.googleapis.com/maps/api/streetview", async () => {
    const ring = parcel && parcel.ring;
    const probes = ring ? ring.filter((_, i) => i % Math.max(1, Math.floor(ring.length / 4)) === 0).slice(0, 4).map(([x, y]) => ({ lat: y, lon: x })) : [];
    return captureStreetView({ lat, lon }, probes, path.join(HERE, "records", keyFor(geo.matched || address) + "_streetview"), get);
  });

  // 7. Permits (city open data where a query API exists)
  const city = (geo.city || "").toUpperCase(), num = (address.match(/^\s*(\d+)/) || [])[1];
  const street = (address.split(",")[0].replace(/^\s*\d+\s*/, "").split(/\s+/).filter(w => !/^(st|street|rd|road|ave|avenue|dr|drive|ln|lane|ct|court|blvd|pl|way|cir|trl|pkwy)$/i.test(w)).pop() || "").toUpperCase();
  let permits = null;
  if (city === "AUSTIN") permits = await source("Permits · City of Austin (Socrata)", "data.austintexas.gov/resource/3syk-w9eu.json", async () =>
    (await getJSON(`https://data.austintexas.gov/resource/3syk-w9eu.json?$where=${encodeURIComponent(`original_address1 like '${num} %${street}%'`)}&$limit=100`)).map(p => ({ id: p.permit_number, type: p.permit_type_desc, work: p.work_class, desc: p.description, issued: (p.issue_date || "").slice(0, 10), status: p.status_current })));
  else if (city === "DALLAS") permits = await source("Permits · City of Dallas (Socrata)", "dallasopendata.com/resource/e7gq-4sah.json", async () =>
    (await getJSON(`https://www.dallasopendata.com/resource/e7gq-4sah.json?$q=${encodeURIComponent(num + " " + street)}&$limit=100`)).map(p => ({ id: p.permit_number, type: p.permit_type, desc: p.work_description, issued: (p.issue_date || "").slice(0, 10) })));
  else log.push({ name: `Permits · ${geo.city || "city"} / ${parcel ? parcel.county : geo.county}`, url: "no public query API", ok: false, error: "No machine-readable permit API for this jurisdiction" });

  return decide({ address, geo, parcel, cad, utility, flood, footprint: fp, slope, permits, sv, facts });
}

function decide(d) {
  const { geo, parcel, cad, utility, flood, footprint, slope, permits, sv } = d;
  const X = d.facts || {};
  const county = ((parcel && parcel.county) || geo.county || "").toUpperCase().replace(/ COUNTY$/, "");
  const C = {}, set = (id, status, note) => C[id] = { status, note };
  const ids = ["E1","E2","E3","E4","E5","E6","E7","E8","E9","E10","S1","S2","S3","S4","S5","S6","S7","S8","S9","S10"];
  ids.forEach(id => set(id, "maybe", "Not in public data."));
  const austin = (geo.city || "").toUpperCase() === "AUSTIN";
  const hasPermits = permits && permits.length > 0;
  const vacantByCad = cad ? Number(cad.imprv) === 0 : (parcel && parcel.valuesPublished && parcel.impValue === 0);
  const newBuild = !!vacantByCad && !footprint && !hasPermits && !X.yearBuilt;
  const yb = X.yearBuilt || (parcel && parcel.yearBuilt) || null;
  const units = Number(X.units) || 1;
  const text = (permits || []).map(p => `${p.desc || ""}`).join(" | ");
  const ampM = text.match(/(\d{3})\s*-?\s*amp/i); const amps = ampM ? Number(ampM[1]) : null;
  const solarPermit = /solar|photovoltaic|\bPV\b/i.test(text), genPermit = /generator/i.test(text);
  const overhead = /overhead/i.test(text) ? true : /underground/i.test(text) ? false : null;

  if (amps) {
    const lo = austin ? 150 : 100;
    set("E1", amps >= lo && amps <= 200 ? "yes" : "no", `${amps}A per permit${austin ? " (Austin 150–200A)" : ""}.`);
    set("E2", amps === 200 ? "yes" : "no", `${amps}A service per permit.`);
    set("E4", amps <= 200 ? "yes" : "no", amps <= 200 ? "Single service ≤200A per permit." : "Service over 200A: likely split panels.");
    if (/meter/i.test(text)) set("E9", "yes", "Meter base replaced under a finaled permit.");
  } else if (newBuild) {
    set("E1", "maybe", "New construction: Texas production builds are typically 200A; confirm on builder plans.");
    set("E2", "maybe", "New build: 200A expected; confirm with builder.");
    set("E4", "maybe", "New build: single 200A panel expected unless the plan exceeds ~4,000 sq ft.");
    set("E9", "maybe", "New meter and conduit at completion; verify at final.");
  }
  if (!amps && yb) {
    const recent = yb >= 1995;
    set("E1", "maybe", recent ? `Built ${yb}: 150–200A typical for this era; confirm panel label.` : `Built ${yb}, no service-upgrade permit found: may be under 150A.`);
    set("E2", "maybe", recent ? `Built ${yb}: 200A likely but not confirmed.` : `Built ${yb}: 200A unlikely without an upgrade.`);
  }
  if (units > 1) set("E4", "maybe", `${X.propertyType || units + " units"}: one meter and panel per unit; screen each unit as its own install.`);
  if (!solarPermit && (permits || newBuild || X.solar === "no")) set("E3", "yes", newBuild ? "Vacant lot, no solar yet; if builder adds PV, panel must be 200A." : permits ? "No solar permits on record." : "No solar in listings or appraisal records.");
  if (yb && yb >= 2015) {
    if (C.E7.status === "maybe") set("E7", "yes", `Built ${yb}: meter set to current utility standard (4–6 ft). Inferred.`);
    if (C.E9.status === "maybe") set("E9", "yes", `Built ${yb}: meter and conduit are new. Inferred.`);
    if (C.S10.status === "maybe") set("S10", "yes", `Built ${yb}: Texas residential meters are exterior. Inferred.`);
  }
  if (parcel && parcel.acres && X.sqft) {
    const ground = X.stories > 1 ? X.sqft / X.stories * 1.35 : X.sqft * 1.2;
    const cover = ground / (parcel.acres * 43560);
    if (cover < 0.4 && C.S2.status === "maybe") set("S2", "yes", `≈${Math.round(cover * 100)}% lot coverage on ${parcel.acres} ac: room for 3×3 ft pads.`);
  }
  if (solarPermit) set("E3", amps === 200 ? "yes" : "maybe", "Solar permit on record: requires 200A panel.");
  if (overhead != null) set("S10", "yes", `Service ${overhead ? "overhead" : "underground"} to exterior meter per permit.`);

  // spacing from parcel + footprint
  let clr = null, yards = null;
  if (parcel && parcel.ring && footprint) {
    const P = proj(geo.lat, geo.lon), par = parcel.ring.map(P), fp = footprint.map(P);
    const dists = fp.map(p => polyDist(p, par));
    clr = Math.round(Math.min(...dists) * 12);
    yards = `${(Math.min(...dists)).toFixed(1)}–${(Math.max(...dists)).toFixed(1)} ft wall-to-lot-line`;
    set("S7", clr >= 56 ? "yes" : "maybe", clr >= 56 ? `Narrowest wall-to-lot-line ≈${clr} in (needs ≥56 in).` : `Narrowest side ≈${clr} in; check which wall has the meter.`);
    set("S2", "yes", "Yard space around the house exceeds a 3×3 ft pad.");
  } else if (parcel && parcel.acres && newBuild) {
    set("S2", "yes", `${parcel.acres} ac lot; pad space available if planned before construction.`);
    set("S7", "maybe", "No house yet; side yards depend on the builder's plot plan.");
  }
  if (slope) set("S8", slope.pct <= 8 ? "yes" : "maybe", `≈${slope.pct}% grade across the lot (USGS 3DEP).`);
  if (flood && flood.sfha) set("S8", "no", `FEMA ${flood.zone}: special flood hazard area; ground unit at risk.`);

  const util = utility && utility.length ? utility.map(u => `${u.name} (${u.type})`).join(" / ") : "Unknown";
  const coop = utility && utility.length && !utility.some(u => u.type === "IOU") && !utility.some(u => /austin energy/i.test(u.name));
  const flags = [];
  if (newBuild) flags.push("NEW CONSTRUCTION · builder channel: install during build");
  if (units > 1) flags.push(`MULTI-UNIT · ${X.propertyType || units + " units"}: separate meter per unit`);
  if (X.hoa) flags.push(`HOA · ${X.hoa}: check exterior-equipment rules`);
  if (coop) flags.push("CO-OP / MUNI UTILITY · no retail choice: confirm Base product availability");
  if (flood && flood.sfha) flags.push("FLOOD ZONE");

  const yes = Object.values(C).filter(c => c.status === "yes").length;
  return {
    address: geo.matched || d.address, key: keyFor(geo.matched || d.address), state: "TX",
    amps, solar: solarPermit ? "yes" : (permits || newBuild) ? "no" : null, clr, clrText: clr ? null : (newBuild ? "Lot vacant" : null),
    facts: {
      yearBuilt: yb || (newBuild ? "Not built (vacant lot)" : "Unknown"),
      sqft: X.sqft || null, stories: X.stories || null, type: X.propertyType || null, builder: X.builder || null, hoa: X.hoa || null, utility: util, service: overhead == null ? "Unknown" : overhead ? "Overhead" : "Underground",
      gas: X.gas || "Unknown", flood: flood ? `Zone ${flood.zone}` : "Unknown", slope: slope ? `≈${slope.pct}%` : "Unknown",
      parcel: parcel ? `${parcel.county} CAD ${parcel.propId} · ${parcel.legal}` : "Unknown", lot: parcel && parcel.acres ? `${parcel.acres} ac` : null
    },
    flags,
    evidence: [
      cad ? `${county} CAD ${cad.propId} (current roll): improvements $${Number(cad.imprv).toLocaleString()}, land $${Number(cad.land).toLocaleString()}${cad.deed ? `, deed ${cad.deed}` : ""}.` : null,
      parcel ? `${parcel.county} CAD ${parcel.propId}: ${parcel.legal}.` : null,
      ...(X.evidence || []),
      newBuild ? "No structure on the parcel (improvements $0, no building mapped): new construction lot." : null,
      parcel && parcel.ownerIsEntity && newBuild ? `Owned by a business entity since ${String(parcel.acquired).replace(/(\d{4})(\d{2})(\d{2})/, "$1-$2-$3")}: likely builder or developer.` : null,
      `Electric utility: ${util}.`,
      flood ? `FEMA flood zone ${flood.zone} (${flood.sub || ""}).` : null,
      slope ? `Grade ≈${slope.pct}% across the lot; elevation ≈${slope.elevFt} ft.` : null,
      permits ? `${permits.length} permit(s) found${amps ? `; service ${amps}A` : ""}.` : null,
      yards ? `Side clearance ${yards}.` : null,
      sv ? (sv.images && sv.images.length ? `Street View: ${sv.images.length} image(s) saved, imagery dated ${sv.newest || "unknown"}.` : `Street View: ${sv.note}`) : null,
    ].filter(Boolean),
    streetView: sv ? { status: sv.status, newest: sv.newest || null, images: (sv.images || []).map(i => ({ file: path.basename(i.file), date: i.date, heading: i.heading, distM: i.distM })) } : null,
    checks: C, yesCount: yes, sourceLog: log, updatedAt: new Date().toISOString().slice(0, 10)
  };
}

export function loadFacts(argv) {
  const args = argv.slice();
  const fi = args.indexOf("--facts");
  if (fi < 0) return { argv: args, facts: {} };
  const file = args[fi + 1];
  if (!file || file.startsWith("--")) throw new Error('Missing facts file. Usage: node tx-screen.mjs "<address>" [--facts facts/<file>.json]');
  let text;
  try { text = fs.readFileSync(file, "utf8"); }
  catch (e) { throw new Error(`Could not read facts file: ${file}`); }
  let facts;
  try { facts = JSON.parse(text); }
  catch (e) { throw new Error(`Facts file is not JSON: ${file}`); }
  if (!facts || typeof facts !== "object" || Array.isArray(facts)) throw new Error(`Facts file must be a JSON object: ${file}`);
  args.splice(fi, 2);
  return { argv: args, facts };
}

function cli() {
  let parsed;
  try { parsed = loadFacts(process.argv.slice(2)); }
  catch (e) { console.error(e.message); process.exit(1); }
  const address = parsed.argv.join(" ").trim();
  if (!address) { console.error('Usage: node tx-screen.mjs "<address>" [--facts facts/<file>.json]'); process.exit(1); }
  main(address, parsed.facts).then(rec => {
    const dir = path.join(HERE, "records"); fs.mkdirSync(dir, { recursive: true });
    const file = path.join(dir, rec.key + ".json");
    fs.writeFileSync(file, JSON.stringify(rec, null, 2));
    console.log(JSON.stringify({ file, address: rec.address, yes: rec.yesCount, flags: rec.flags, sources: rec.sourceLog.map(s => `${s.ok ? "OK " : "ERR"} ${s.name}${s.ok ? (s.found ? "" : " (no match)") : " · " + s.error}`) }, null, 2));
  }).catch(e => { console.error("FAILED:", e.message); console.error(JSON.stringify(log, null, 2)); process.exit(1); });
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) cli();
