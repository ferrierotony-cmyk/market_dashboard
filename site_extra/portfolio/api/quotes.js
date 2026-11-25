// Delayed quotes for the portfolio pages. Vercel runs this when a page asks for it.
// Free public data only. FRED does not answer Vercel's servers, so spreads come from the dashboard snapshot instead.
// The symbol list is fixed, so nobody can use this to fetch anything else.
const SYMBOLS = { SKYD: "stock", NFLX: "stock", DIS: "stock", CMCSA: "stock", FOXA: "stock", FOX: "stock", "^VIX": "index", "^MOVE": "index", "^TNX": "index" };
const AGENT = "portfolio-live-data/1.0";
const TIMEOUT = 6000;

async function get(url, type) {
  const r = await fetch(url, { headers: { "User-Agent": AGENT }, signal: AbortSignal.timeout(TIMEOUT) });
  if (!r.ok) throw new Error("status " + r.status);
  return type === "json" ? r.json() : r.text();
}

function fromYahoo(j) {
  const m = j && j.chart && j.chart.result && j.chart.result[0] && j.chart.result[0].meta;
  if (!m || !(m.regularMarketPrice > 0)) throw new Error("no price");
  return { price: m.regularMarketPrice, prev: m.chartPreviousClose || m.previousClose || null, time: new Date(m.regularMarketTime * 1000).toISOString(), source: "Yahoo Finance" };
}

function fromStooq(text) {
  const rows = text.trim().split(/\r?\n/);
  const head = rows[0].toLowerCase().split(","), vals = (rows[1] || "").split(",");
  const pick = (k) => vals[head.indexOf(k)];
  const price = Number(pick("close")), date = pick("date");
  if (!(price > 0) || !/^\d{4}-\d{2}-\d{2}$/.test(date || "")) throw new Error("no price");
  return { price: price, prev: null, time: date, source: "Stooq" };
}

async function quote(sym, kind) {
  try {
    return fromYahoo(await get("https://query1.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(sym) + "?range=1d&interval=1d", "json"));
  } catch (e) {
    if (kind !== "stock") throw e;
    return fromStooq(await get("https://stooq.com/q/l/?s=" + sym.toLowerCase() + ".us&f=sd2t2ohlcv&h&e=csv", "text"));
  }
}

async function build() {
  const out = { asof: new Date().toISOString(), quotes: {}, missing: [] };
  const jobs = Object.keys(SYMBOLS).map((s) => quote(s, SYMBOLS[s]).then((q) => { out.quotes[s] = q; }, () => out.missing.push(s)));
  await Promise.all(jobs);
  return out;
}

module.exports = async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  if (req.method && req.method !== "GET" && req.method !== "HEAD") { res.statusCode = 405; return res.end('{"error":"GET only"}'); }
  const out = await build();
  const any = Object.keys(out.quotes).length > 0;
  // five minutes fresh, then an hour of serving the old answer while a new one is fetched. Failures are not kept.
  res.setHeader("Cache-Control", any ? "public, max-age=60, s-maxage=300, stale-while-revalidate=3600" : "no-store");
  res.statusCode = any ? 200 : 502;
  res.end(JSON.stringify(out));
};
module.exports.parts = { fromYahoo, fromStooq, build, SYMBOLS };
