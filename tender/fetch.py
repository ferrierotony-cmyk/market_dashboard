"""Stage 1: search SEC EDGAR full text for tender and exchange offer press releases and cache the cleaned text.

Public data only. Parsing happens in parse.py from the cache, so the rules can be improved without hitting the SEC."""
import csv, datetime as dt, html, json, os, re, sys, time
import requests

CONTACT = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
if not CONTACT:
    sys.exit("SEC_CONTACT_EMAIL is not set. The SEC requires a contact in the User-Agent, so no requests were sent.")
UA = {"User-Agent": "TenderTrackerResearch student project " + CONTACT, "Accept-Encoding": "gzip, deflate"}
OUT = os.path.join(os.path.dirname(__file__), "out")
TXT = os.path.join(OUT, "texts")
os.makedirs(TXT, exist_ok=True)
MAX_DOCS = int(os.environ.get("MAX_DOCS", "400"))
OFFSET = int(os.environ.get("OFFSET_DAYS", "0"))
today = dt.date.today() - dt.timedelta(days=OFFSET)
start = today - dt.timedelta(days=90)
log_lines = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s); log_lines.append(s)

def get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=40, **kw)
            if r.status_code == 200: return r
            log("HTTP", r.status_code, url[:120])
            if r.status_code in (403, 429): time.sleep(5 * (i + 1))
        except Exception as e:
            log("ERR", type(e).__name__, url[:100]); time.sleep(2)
    return None

# 1. search -------------------------------------------------------------------------------------
queries = ['"cash tender offer" "notes"', '"early tender" "expiration" "notes"', '"announces" "exchange offer" "notes"',
           '"announces" "tender offer" "any and all"', '"announces" "tender offers" "notes"', '"announces" "offer to purchase" "notes"']
hits = {}
for q in queries:
    frm = 0
    while frm < 600:
        url = ("https://efts.sec.gov/LATEST/search-index?q=%s&forms=8-K&dateRange=custom&startdt=%s&enddt=%s&from=%d"
               % (requests.utils.quote(q), start, today, frm))
        r = get(url)
        time.sleep(0.2)
        if r is None: break
        try: j = r.json()
        except Exception: log("bad json for", q); break
        hs = j.get("hits", {}).get("hits", [])
        if not hs: break
        for h in hs:
            hits.setdefault(h["_id"], h)
        frm += len(hs)
        if frm >= j.get("hits", {}).get("total", {}).get("value", 0): break
    log("query", q, "-> unique hits so far", len(hits))
log("total unique documents", len(hits))
if not hits:
    with open(os.path.join(OUT, "summary.txt"), "w") as f: f.write("\n".join(log_lines) + "\n")
    sys.exit("No search results. Check the SEC response codes above.")

# keep press release exhibits and the 8-K body, newest first
def pr_like(h):
    ft = (h["_source"].get("file_type") or "")
    return ft.startswith("EX-99") or ft == "8-K"
cands = [h for h in hits.values() if pr_like(h)]
log("press release style documents", len(cands), "of", len(hits))
docs = sorted(cands, key=lambda h: h["_source"].get("file_date", ""), reverse=True)[:MAX_DOCS]

# 2. fetch text ---------------------------------------------------------------------------------
def clean(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def clean(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()

meta = []
for n, h in enumerate(docs):
    s = h["_source"]
    adsh, fname = h["_id"].split(":", 1)
    cik = (s.get("ciks") or [""])[0].lstrip("0")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-', '')}/{fname}"
    r = get(url); time.sleep(0.15)
    if r is None: continue
    text = clean(r.text)[:80000]
    key = re.sub(r"[^A-Za-z0-9]", "_", h["_id"])
    with open(os.path.join(TXT, key + ".txt"), "w", encoding="utf-8") as f: f.write(text)
    meta.append({"key": key, "file_date": s.get("file_date"), "issuer": (s.get("display_names") or [""])[0],
                 "doc": s.get("file_type"), "url": url, "adsh": adsh})
    if n % 25 == 0: log("fetched", n + 1, "of", len(docs))
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"))
log("cached", len(meta), "documents")
with open(os.path.join(OUT, "fetch_log.txt"), "w") as f: f.write("\n".join(log_lines) + "\n")
