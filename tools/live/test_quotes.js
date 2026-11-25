// Offline checks for the quote function. Run: node tools/live/test_quotes.js
const path = require("path");
const file = path.join(__dirname, "..", "..", "site_extra", "portfolio", "api", "quotes.js");
const handler = require(file);
const { fromYahoo, fromStooq } = handler.parts;
let n = 0;
function check(name, ok) { n++; console.log((ok ? "pass " : "FAIL ") + name); if (!ok) process.exit(1); }
function throws(f) { try { f(); return false; } catch (e) { return true; } }

const Y = (p) => ({ chart: { result: [{ meta: { regularMarketPrice: p, chartPreviousClose: 6.3, regularMarketTime: 1795640400 } }] } });
check("yahoo price", fromYahoo(Y(6.5)).price === 6.5);
check("yahoo zero is refused", throws(() => fromYahoo(Y(0))));
check("yahoo error body is refused", throws(() => fromYahoo({ chart: { result: null, error: {} } })));
check("stooq price", fromStooq("Symbol,Date,Time,Open,High,Low,Close,Volume\nSKYD.US,2026-11-24,22:00:00,6.4,6.6,6.3,6.5,1000").price === 6.5);
check("stooq missing is refused", throws(() => fromStooq("Symbol,Date,Time,Open,High,Low,Close,Volume\nSKYD.US,N/D,N/D,N/D,N/D,N/D,N/D,N/D")));

function call(fake, method) {
  const keep = global.fetch; global.fetch = fake;
  const res = { headers: {}, statusCode: 0, body: "", setHeader(k, v) { this.headers[k] = v; }, end(b) { this.body = b; } };
  return handler({ method: method || "GET" }, res).then(() => { global.fetch = keep; return res; });
}
const ok = (b) => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(b), text: () => Promise.resolve(b) });
(async () => {
  let seen = [];
  let r = await call((u) => { seen.push(u); return /yahoo/.test(u) ? ok(Y(10)) : ok("observation_date,X\n2026-11-23,0.97"); });
  let j = JSON.parse(r.body);
  check("all symbols answered", r.statusCode === 200 && Object.keys(j.quotes).length === 9 && j.missing.length === 0);
  check("answer is cacheable and open to the page", /s-maxage=300/.test(r.headers["Cache-Control"]) && r.headers["Access-Control-Allow-Origin"] === "*");
  check("only the two known hosts are called", seen.every((u) => /^https:\/\/(query1\.finance\.yahoo\.com|stooq\.com)\//.test(u)));
  r = await call((u) => /yahoo/.test(u) ? Promise.resolve({ ok: false, status: 429 }) : /stooq/.test(u) ? ok("Symbol,Date,Time,Open,High,Low,Close,Volume\nA,2026-11-24,22:00:00,1,1,1,9,1") : ok("observation_date,X\n2026-11-23,0.97"));
  j = JSON.parse(r.body);
  check("stocks fall back when Yahoo refuses, indexes go missing", j.quotes.SKYD.source === "Stooq" && j.missing.includes("^VIX") && r.statusCode === 200);
  r = await call(() => Promise.reject(new Error("down")));
  check("everything down is a 502 that is not cached", r.statusCode === 502 && r.headers["Cache-Control"] === "no-store");
  r = await call(() => ok(Y(1)), "POST");
  check("only GET", r.statusCode === 405);
  console.log(n + " checks passed");
})();
