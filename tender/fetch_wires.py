"""Stage 1b: newswire search. Many issuers announce a tender or exchange offer only on PR Newswire, GlobeNewswire or Business Wire
and never file an 8-K for it, so the SEC search alone misses them. This pulls the newswire search pages for the last 90 days,
keeps headlines about notes, caches the release text next to the SEC texts and adds rows to meta.json with doc "WIRE".

Public pages only. Runs after fetch.py. Any failure here is logged and the SEC results stand on their own."""
import datetime as dt, html, json, os, re, sys, time
import requests

OUT = os.path.join(os.path.dirname(__file__), "out")
TXT = os.path.join(OUT, "texts")
os.makedirs(TXT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 TenderTrackerResearch",
      "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-US,en;q=0.8"}
OFFSET = int(os.environ.get("OFFSET_DAYS", "0"))
today = dt.date.today() - dt.timedelta(days=OFFSET)
start = today - dt.timedelta(days=90)
MAX_WIRE = int(os.environ.get("MAX_WIRE", "400"))
log_lines = []


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log_lines.append(s)


def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=40)
            if r.status_code == 200:
                return r
            log("HTTP", r.status_code, url[:120])
            if r.status_code in (403, 429):
                time.sleep(4 * (i + 1))
        except Exception as e:
            log("ERR", type(e).__name__, url[:100]); time.sleep(2)
    return None


def clean(t):
    t = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


KEEP = re.compile(r"tender offer|exchange offer|offer to purchase|offers to purchase|offer to exchange|consent solicitation|any and all|early tender|early participation", re.I)
NOTES = re.compile(r"\bnotes?\b|debentures|bonds|securities|\bdebt\b|consent", re.I)
EQUITY = re.compile(r"common stock|common shares|ordinary shares|per share|dutch auction|units of|preferred stock|warrants|shares of|closed-end fund|\bshares\b", re.I)
TERMS = ["tender offer notes", "tender offers senior notes", "exchange offer notes", "any and all notes", "consent solicitation notes",
         "early tender results", "offer to purchase notes", "cash tender offer"]

# Each source: a search URL builder, a regex for release links, how dates appear on the release page.
SOURCES = {
    "prnewswire": {
        "search": lambda term, page: "https://www.prnewswire.com/search/news/?keyword=%s&page=%d&pagesize=100" % (requests.utils.quote(term), page),
        "link": re.compile(r'href="(/news-releases/[^"]+?\.html)"', re.I), "base": "https://www.prnewswire.com", "pages": 3,
    },
    "globenewswire": {
        "search": lambda term, page: "https://www.globenewswire.com/search/keyword/%s?pageSize=50&page=%d" % (requests.utils.quote(term), page),
        "link": re.compile(r'href="(/news-release/20\d\d/\d\d/\d\d/[^"]+?\.html)"', re.I), "base": "https://www.globenewswire.com", "pages": 3,
    },
    "businesswire": {
        "search": lambda term, page: "https://www.businesswire.com/newsroom?searchTerm=%s&page=%d" % (requests.utils.quote(term), page),
        "link": re.compile(r'href="(https://www\.businesswire\.com/news/home/\d{14}/en/[^"]+)"', re.I), "base": "", "pages": 2,
    },
}


def page_date(raw, url):
    for pat in (r'"datePublished"\s*:\s*"(20\d\d-\d\d-\d\d)', r'property="article:published_time"\s+content="(20\d\d-\d\d-\d\d)',
                r'content="(20\d\d-\d\d-\d\d)[^"]*"\s+(?:property|name)="(?:article:published_time|pubdate|date|dc\.date)',
                r'"dateModified"\s*:\s*"(20\d\d-\d\d-\d\d)'):
        m = re.search(pat, raw, re.I)
        if m:
            return m.group(1)
    m = re.search(r"/(20\d\d)/(\d\d)/(\d\d)/", url)
    if m:
        return "%s-%s-%s" % m.groups()
    m = re.search(r"/home/(20\d\d)(\d\d)(\d\d)\d{6}/", url)
    if m:
        return "%s-%s-%s" % m.groups()
    return ""


def dateline_name(text):
    """issuer from the first sentence: 'General Mills, Inc. (NYSE: GIS) today announced'"""
    m = re.search(r"(?:/PRNewswire/|\(GLOBE NEWSWIRE\)|\(BUSINESS WIRE\))\s*-+\s*(.{3,80}?)\s+(?:\(|today|announced|announces)", text[:3000])
    if m:
        return m.group(1).strip(" ,-–—")
    return ""


RSS_SOURCES = {
    # Bing News returns direct article links, so it covers GlobeNewswire, Business Wire and investor relations sites that block scrapers.
    "bing": lambda term: "https://www.bing.com/news/search?q=%s&format=rss&count=100" % requests.utils.quote(term),
    "globenewswire_rss": lambda term: "https://www.globenewswire.com/RssFeed/keyword/%s/feedTitle/tender" % requests.utils.quote(term),
}
RSS_TERMS = ['"tender offer" notes', '"tender offers" "senior notes"', '"exchange offer" notes', '"any and all" notes tender', '"consent solicitation" notes',
             '"early tender" results notes', '"offer to purchase" notes cash', '"cash tender offer"', '"tender offer" debentures', '"expiration" "tender offer" notes results']

found = {}
titles = {}
for src, mk in RSS_SOURCES.items():
    n0 = len(found)
    for term in RSS_TERMS:
        r = get(mk(term), tries=2)
        time.sleep(0.5)
        if r is None or "<item" not in r.text:
            if src == "globenewswire_rss":
                break
            continue
        for item in re.findall(r"(?s)<item>(.*?)</item>", r.text):
            lk = re.search(r"<link>\s*(https?://[^<\s]+)", item) or re.search(r"<link[^>]*href=\"(https?://[^\"]+)", item)
            if not lk:
                continue
            u = html.unescape(lk.group(1).strip())
            if "bing.com/news/apiclick" in u:
                m = re.search(r"[?&]url=([^&]+)", u)
                if not m:
                    continue
                u = requests.utils.unquote(m.group(1))
            u = u.split("?")[0]
            t = re.search(r"(?s)<title>(.*?)</title>", item)
            d = re.search(r"<pubDate>(.*?)</pubDate>", item)
            if u not in found:
                found[u] = src
                titles[u] = (clean(t.group(1)) if t else "", d.group(1) if d else "")
    log(src, "release links", len(found) - n0)
for src, cfg in SOURCES.items():
    n0 = len(found)
    for term in TERMS:
        for page in range(1, cfg["pages"] + 1):
            r = get(cfg["search"](term, page), tries=2)
            time.sleep(0.6)
            if r is None:
                break
            links = cfg["link"].findall(r.text)
            if not links:
                break
            anchors = {}
            for m in re.finditer(r'(?s)<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r.text):
                t = clean(m.group(2))
                if len(t) > 25:
                    anchors[m.group(1)] = t
            new = 0
            for lk in links:
                u = cfg["base"] + lk if lk.startswith("/") else lk
                u = u.split("?")[0]
                if u not in found:
                    found[u] = src; new += 1
                    if lk in anchors:
                        titles[u] = (anchors[lk], "")
            if new == 0:
                break
    log(src, "release links", len(found) - n0)
log("newswire links total", len(found))

meta_path = os.path.join(OUT, "meta.json")
meta = json.load(open(meta_path)) if os.path.exists(meta_path) else []
have = {m.get("url") for m in meta}
added = 0
for n, (u, src) in enumerate(list(found.items())[:MAX_WIRE * 3]):
    if added >= MAX_WIRE:
        break
    if u in have:
        continue
    rss_title, rss_date = titles.get(u, ("", ""))
    if rss_title and not (KEEP.search(rss_title) and NOTES.search(rss_title)):
        continue  # headline from the feed is not about a notes offer, so skip the page fetch
    r = get(u, tries=1)
    time.sleep(0.4)
    raw = ""
    if r is not None:
        if "charset" not in (r.headers.get("content-type") or "").lower():
            r.encoding = "utf-8"
        raw = r.text
    d = page_date(raw, u) if raw else ""
    if not d and rss_date:
        try:
            d = dt.datetime.strptime(rss_date[:25].strip(), "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
        except ValueError:
            d = ""
    if not d or d < str(start) or d > str(today):
        continue
    tm = re.search(r"<title>(.*?)</title>", raw, re.I | re.S)
    title = clean(tm.group(1)) if tm else rss_title
    if not raw or len(raw) < 2000 or re.search(r"access denied|request blocked|captcha|are you a robot|oops, something went wrong|just a moment", raw[:6000], re.I):
        title = rss_title or title
        raw = ""  # page blocked: keep the headline and the link, the parser reads the kind from the headline
    head = title[:260]
    if not KEEP.search(head) or not NOTES.search(head) or (EQUITY.search(head) and not re.search(r"\bnotes?\b|debentures", head, re.I)):
        continue
    text = clean(raw) if raw else title
    # drop the page chrome before the release body: start at the dateline or the headline
    i = text.find(title[:60]) if title else -1
    if i > 0:
        text = text[i:]
    text = text[:80000]
    doc = "WIRE" if raw else "WIRE-TITLE"
    key = "wire_" + re.sub(r"[^A-Za-z0-9]", "_", u.split("//", 1)[-1])[-120:]
    with open(os.path.join(TXT, key + ".txt"), "w", encoding="utf-8") as f:
        f.write(text)
    issuer = ""
    parts = re.split(r"\s+(?:Announces?|Commences?|Extends?|Launches?|Reports?|Prices?|Increases?|Amends?|Completes?|Receives?)\b", title, 1, flags=re.I)
    if len(parts) == 2 and 2 < len(parts[0]) < 70:
        issuer = parts[0]
    issuer = issuer or dateline_name(text) or title[:60]
    issuer = re.sub(r"^(?:[A-Z][a-z]{2,8}\.? \d{1,2}, 20\d\d\s*-+\s*)?", "", issuer)  # a leading dateline date
    issuer = re.split(r"\s+\((?:NYSE|NASDAQ|Nasdaq|TSX|LSE|OTC)[^)]*\)", issuer)[0].strip(" ,-–—|")
    issuer = re.split(r"\s+(?:intends|plans|to issue|completes|successfully|has|today)\b", issuer, 1, flags=re.I)[0].strip(" ,-–—|")[:60]
    meta.append({"key": key, "file_date": d, "issuer": issuer, "doc": doc, "url": u, "adsh": src})
    added += 1
    if added % 25 == 0:
        log("wire releases kept", added)
json.dump(meta, open(meta_path, "w"))
log("wire releases added", added, "meta rows now", len(meta))
with open(os.path.join(OUT, "wire_log.txt"), "w") as f:
    f.write("\n".join(log_lines) + "\n")
