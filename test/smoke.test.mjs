import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { keyFor, loadFacts } from "../tx-screen.mjs";
import { readApiKey, usagePath } from "../streetview.mjs";
import { createServer, resolveRequest } from "../scripts/serve.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CHECK_IDS = ["E1","E2","E3","E4","E5","E6","E7","E8","E9","E10","S1","S2","S3","S4","S5","S6","S7","S8","S9","S10"];

function runNode(args, extraEnv = {}) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, args, { cwd: root, env: { ...process.env, ...extraEnv } });
    let stdout = "", stderr = "";
    child.stdout.on("data", (d) => { stdout += d; });
    child.stderr.on("data", (d) => { stderr += d; });
    child.on("close", (code) => resolve({ code, stdout, stderr }));
  });
}

test("address keys match the saved record files", () => {
  const cases = {
    "8014 Chateau St, Houston, TX 77028": "8014-chateau-st",
    "104 Gunner Rd, Buda, TX 78610": "104-gunner-rd",
    "1510 W 30th St, Austin, TX 78703": "1510-w-30th-st",
    "1510 West 30th Street, Austin, TX": "1510-w-30th-st",
  };
  for (const [addr, key] of Object.entries(cases)) {
    assert.equal(keyFor(addr), key);
    assert.equal(fs.existsSync(path.join(root, "records", key + ".json")), true, key);
  }
});

test("checker.html uses the same address key", () => {
  const html = fs.readFileSync(path.join(root, "checker.html"), "utf8");
  const m = html.match(/const keyFor = a => \{[\s\S]*?\n\};/);
  assert.ok(m, "keyFor in checker.html");
  const fn = new Function(`${m[0]}; return keyFor;`)();
  for (const addr of ["8014 Chateau St, Houston, TX 77028", "104 Gunner Road, Buda, TX", "1510 West 30th Street"]) {
    assert.equal(fn(addr), keyFor(addr), addr);
  }
});

test("checker script parses and the standalone path is present", () => {
  const html = fs.readFileSync(path.join(root, "checker.html"), "utf8");
  assert.match(html, /id="runtimeBanner"/);
  assert.match(html, /demo\/recorded-reading\.json/);
  assert.match(html, /window\.claude && window\.claude\.use/);
  assert.match(html, /pdfjsLib\.GlobalWorkerOptions\.workerSrc/);
  assert.doesNotMatch(html, /pdf\.worker\.min\.js"><\/script>/);
  const parts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  assert.equal(parts.length, 1);
  const tmp = path.join(os.tmpdir(), "checker-inline-check.js");
  fs.writeFileSync(tmp, parts[0][1]);
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ["--check", tmp]);
    let stderr = "";
    child.stderr.on("data", (d) => { stderr += d; });
    child.on("close", (code) => code === 0 ? resolve() : reject(new Error(stderr)));
  });
});

test("saved JSON has the 20 checks and the recorded reading has a layout", () => {
  for (const file of fs.readdirSync(path.join(root, "records")).filter(f => f.endsWith(".json"))) {
    const rec = JSON.parse(fs.readFileSync(path.join(root, "records", file), "utf8"));
    assert.equal(rec.key, file.replace(/\.json$/, ""));
    assert.ok(rec.address);
    assert.ok(rec.facts);
    for (const id of CHECK_IDS) assert.ok(rec.checks[id] && rec.checks[id].status, `${file} ${id}`);
  }
  for (const file of fs.readdirSync(path.join(root, "facts")).filter(f => f.endsWith(".json"))) {
    const facts = JSON.parse(fs.readFileSync(path.join(root, "facts", file), "utf8"));
    assert.equal(typeof facts, "object");
    assert.ok(!Array.isArray(facts));
  }
  const recorded = JSON.parse(fs.readFileSync(path.join(root, "demo", "recorded-reading.json"), "utf8"));
  for (const id of CHECK_IDS) assert.ok(recorded.checks[id] && recorded.checks[id].note, id);
  assert.equal(recorded.layout.clear_wall_from_meter_ft, 9);
  assert.equal(recorded.layout.gas_service, "no");
  assert.equal(recorded.main_breaker_amps, 200);
});

test("facts loader accepts the sample file and rejects a missing one", () => {
  const good = loadFacts(["--facts", path.join(root, "facts", "104-gunner-rd.json"), "104 Gunner Rd, Buda, TX 78610"]);
  assert.equal(good.argv.join(" "), "104 Gunner Rd, Buda, TX 78610");
  assert.equal(good.facts.units, 2);
  assert.throws(() => loadFacts(["--facts"]), /Missing facts file/);
  assert.throws(() => loadFacts(["--facts", path.join(root, "no-such-facts.json"), "x"]), /Could not read facts file/);
});

test("tx-screen prints usage and does not geocode when arguments are missing", async () => {
  const usage = await runNode(["tx-screen.mjs"]);
  assert.equal(usage.code, 1);
  assert.match(usage.stderr, /Usage:/);
  const missing = await runNode(["tx-screen.mjs", "--facts", path.join(root, "missing.json"), "1 Main St, Austin, TX"]);
  assert.equal(missing.code, 1);
  assert.match(missing.stderr, /Could not read facts file/);
  assert.doesNotMatch(missing.stderr, /FAILED:/);
});

test("Street View key comes from the environment or a dotenv file", () => {
  assert.equal(readApiKey({ GOOGLE_MAPS_API_KEY: "test-key" }, { files: [] }), "test-key");
  assert.equal(readApiKey({ GOOGLE_MAPS_API_KEY: "\"quoted-key\"" }, { files: [] }), "quoted-key");
  assert.equal(readApiKey({}, {
    files: ["mem.env"],
    readFile: () => "export GOOGLE_MAPS_API_KEY='from-file' # comment\n",
  }), "from-file");
  assert.throws(() => readApiKey({}, { files: ["none"], readFile() { throw new Error("missing"); } }), /GOOGLE_MAPS_API_KEY/);
  const prev = process.env.GOOGLE_USAGE_PATH;
  process.env.GOOGLE_USAGE_PATH = path.join(os.tmpdir(), "usage.json");
  try { assert.equal(usagePath(), process.env.GOOGLE_USAGE_PATH); }
  finally { if (prev === undefined) delete process.env.GOOGLE_USAGE_PATH; else process.env.GOOGLE_USAGE_PATH = prev; }
});

test("streetview ledger path is not the image path", () => {
  const src = fs.readFileSync(path.join(root, "streetview.mjs"), "utf8");
  assert.match(src, /saveLedger\(L, ledgerFile\);/);
  assert.doesNotMatch(src, /saveLedger\(L, file\);/);
});

test("gitignore still blocks secrets, imagery, and bulk data", () => {
  const gi = fs.readFileSync(path.join(root, ".gitignore"), "utf8");
  assert.match(gi, /^\.env\r?$/m);
  assert.match(gi, /records\/\*_streetview\//);
  assert.match(gi, /^bulk\//m);
  assert.match(gi, /google-usage\.json/);
  const example = fs.readFileSync(path.join(root, ".env.example"), "utf8");
  assert.match(example, /GOOGLE_MAPS_API_KEY=/);
  assert.match(example, /GOOGLE_USAGE_PATH/);
  assert.match(example, /^# PORT=$/m);
  assert.doesNotMatch(example, /AIza/);
});

test("readme screenshots exist", () => {
  for (const name of ["checker-address.png", "checker-recorded.png"]) {
    const file = path.join(root, "docs", name);
    assert.equal(fs.existsSync(file), true, name);
    assert.ok(fs.statSync(file).size > 10000, name);
  }
});

test("published prose has no em or en dashes", () => {
  for (const file of ["README.md", "LICENSE", ".env.example", "index.html", "package.json"]) {
    const text = fs.readFileSync(path.join(root, file), "utf8");
    assert.doesNotMatch(text, /\u2013|\u2014/, file);
  }
});

test("static server serves the demo and refuses secrets", async () => {
  assert.equal(resolveRequest("/.env"), null);
  assert.equal(resolveRequest("/.git/HEAD"), null);
  assert.equal(resolveRequest("/demo/../.env"), null);
  const server = createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  const get = (p) => fetch(`http://127.0.0.1:${port}${p}`);
  try {
    const index = await get("/");
    assert.equal(index.status, 200);
    assert.match(await index.text(), /checker\.html/);
    const checker = await get("/checker.html");
    assert.equal(checker.status, 200);
    assert.match(checker.headers.get("content-type"), /text\/html/);
    const recorded = await get("/demo/recorded-reading.json");
    assert.equal(recorded.status, 200);
    const body = await recorded.json();
    assert.equal(body.address.includes("Gunner"), true);
    const rec = await get("/records/8014-chateau-st.json");
    assert.equal(rec.status, 200);
    assert.equal((await rec.json()).key, "8014-chateau-st");
    assert.equal((await get("/.env")).status, 403);
    assert.equal((await get("/nope")).status, 404);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
