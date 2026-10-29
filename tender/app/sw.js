/* Tender Tracker service worker. Build __VERSION__.
   Shell: stale-while-revalidate, so the app opens instantly and offline.
   data.json: network first, falling back to the last copy, so a phone never shows stale rows when it is online. */
const VERSION = "__VERSION__";
const SHELL = "tt-shell-" + VERSION;
const DATA = "tt-data";
const FILES = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("tt-shell-") && k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;           // filings and the raw data feed go straight to the network
  if (url.pathname.endsWith("/data.json")) {
    e.respondWith(fetch(req, { cache: "no-store" }).then(r => {
      if (r.ok) { const copy = r.clone(); caches.open(DATA).then(c => c.put("data.json", copy)); }
      return r;
    }).catch(() => caches.open(DATA).then(c => c.match("data.json")).then(r => {
      if (!r) return Response.error();
      const h = new Headers(r.headers); h.set("x-tt-cached", "1");   // tells the page this is the last saved copy, not a fresh check
      return r.blob().then(body => new Response(body, { status: 200, headers: h }));
    })));
    return;
  }
  e.respondWith(caches.open(SHELL).then(c => c.match(req, { ignoreSearch: true }).then(hit => {
    const net = fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  })));
});
