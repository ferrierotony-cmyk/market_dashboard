"""Feasibility test: can bond tender offer and exchange offer details be extracted from SEC 8-K press releases?

Public data only. Pulls the last 90 days of 8-K exhibits that mention a tender or exchange offer, classifies each
press release, extracts a few fields with plain rules, and writes coverage numbers so we know how clean it is.
"""
import csv, datetime as dt, html, json, os, re, sys, time
import requests

CONTACT = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
if not CONTACT:
    sys.exit("SEC_CONTACT_EMAIL is not set. The SEC requires a contact in the User-Agent, so no requests were sent.")
UA = {"User-Agent": "TenderTrackerResearch student project " + CONTACT, "Accept-Encoding": "gzip, deflate"}
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)
MAX_DOCS = int(os.environ.get("MAX_DOCS", "400"))
today = dt.date.today()
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

MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DATE = rf"{MONTH}\s+\d{{1,2}},\s+20\d\d"
rows = []
for n, h in enumerate(docs):
    s = h["_source"]
    adsh, fname = h["_id"].split(":", 1)
    cik = (s.get("ciks") or [""])[0].lstrip("0")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-', '')}/{fname}"
    r = get(url); time.sleep(0.15)
    if r is None: continue
    text = clean(r.text)
    head = text[:1500]
    low = text.lower()
    row = {"file_date": s.get("file_date"), "issuer": (s.get("display_names") or [""])[0], "doc": s.get("file_type"),
           "url": url, "chars": len(text)}
    # classification of the press release
    body_start = re.sub(r"^\S+ \d+ \S+ ", "", text)[:900].lower()
    if not re.search(r"tender offer|exchange offer|offer to purchase|offer to exchange|tender results|exchange results", body_start):
        row["kind"] = "not_relevant"
    else:
        h2 = head.lower()
        if re.search(r"final results|expiration and final|announces (?:the )?(?:final|expiration)", h2): kind = "final_results"
        elif re.search(r"early (?:tender )?results|early participation results|early tender date results", h2): kind = "early_results"
        elif re.search(r"extend|extension", h2): kind = "extension"
        elif re.search(r"pricing|price determination|determination of the (?:total )?consideration", h2): kind = "pricing"
        elif re.search(r"launch|commence|announces .*(?:tender|exchange) offer|announces cash tender", h2): kind = "launch"
        else: kind = "unclear"
        row["kind"] = kind
    row["offer_type"] = "exchange" if re.search(r"exchange offer|offer to exchange", low) and not re.search(r"cash tender offer", low) else (
        "cash_tender" if re.search(r"cash tender offer|tender offers?", low) else "")
    # securities: coupon and maturity
    secs = re.findall(r"(\d{1,2}\.\d{1,3})%\s+(?:[A-Z][A-Za-z\-]+\s+){0,4}?(?:Notes|Debentures|Bonds)\s+due\s+(?:\w+\s+\d{0,2},?\s*)?(20\d\d|21\d\d)", text)
    row["securities"] = "; ".join(sorted({f"{c}% {y}" for c, y in secs}))[:200]
    row["n_securities"] = len({f"{c}% {y}" for c, y in secs})
    row["cusips"] = "; ".join(sorted(set(re.findall(r"\b([0-9]{3}[0-9A-Z]{5}[0-9])\b", text)) ))[:120] if re.search(r"CUSIP", text) else ""
    m = re.search(rf"[Ee]arly (?:[Tt]ender|[Pp]articipation|[Cc]onsent)[\\s\\S]{{0,80}}?(?:Date|Deadline)[\\s\\S]{{0,220}}?({DATE})", text)
    row["early_date"] = m.group(1) if m else ""
    m = re.search(rf"[Ee]xpiration (?:[Dd]ate|[Tt]ime)[\\s\\S]{{0,220}}?({DATE})", text)
    row["expiration_date"] = m.group(1) if m else ""
    m = re.search(r"(?:up to|maximum (?:aggregate )?(?:principal )?(?:amount|tender)[^$]{0,60})\s*(?:an aggregate principal amount of\s*)?\$\s?([\d,\.]+)\s*(million|billion)?", text, re.I)
    row["cap"] = (m.group(1) + (" " + m.group(2) if m.group(2) else "")) if m else ""
    m = re.search(r"(?:aggregate )?principal amount (?:of [^.$]{0,80})?(?:validly )?tendered[^.$]{0,80}\$\s?([\d,\.]+)\s*(million|billion)?", text, re.I)
    row["tendered"] = (m.group(1) + (" " + m.group(2) if m.group(2) else "")) if m else ""
    row["head"] = head[:260]
    rows.append(row)
    if n % 25 == 0: log("fetched", n + 1, "of", len(docs))

# 3. outputs --------------------------------------------------------------------------------------
cols = ["file_date", "issuer", "doc", "kind", "offer_type", "securities", "n_securities", "cusips", "early_date",
        "expiration_date", "cap", "tendered", "chars", "url", "head"]
with open(os.path.join(OUT, "tender_extraction.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); [w.writerow({c: r.get(c, "") for c in cols}) for r in rows]
rel = [r for r in rows if r["kind"] != "not_relevant"]
log("documents fetched", len(rows), "relevant", len(rel))
from collections import Counter
log("kinds", dict(Counter(r["kind"] for r in rows)))
log("offer types", dict(Counter(r["offer_type"] for r in rel)))
def cov(k, subset): 
    return "%d/%d" % (sum(1 for r in subset if r.get(k)), len(subset))
for kind in ("launch", "early_results", "final_results", "extension", "pricing", "unclear"):
    sub = [r for r in rel if r["kind"] == kind]
    if sub:
        log(kind, "n=%d" % len(sub), "securities", cov("securities", sub), "cusips", cov("cusips", sub), "early_date", cov("early_date", sub),
            "expiration", cov("expiration_date", sub), "cap", cov("cap", sub), "tendered", cov("tendered", sub))
with open(os.path.join(OUT, "summary.txt"), "w") as f: f.write("\n".join(log_lines) + "\n")
