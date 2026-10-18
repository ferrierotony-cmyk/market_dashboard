"""Stage 2: parse cached press releases into events and offers. No network. Run: python tender/parse.py [out_dir]

Public SEC data only. Rules are plain regex so every field can be traced back to the source text."""
import csv, json, os, random, re, sys
from collections import Counter, defaultdict
from datetime import datetime

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "out")
meta = json.load(open(os.path.join(OUT, "meta.json")))

MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
DATE = rf"{MONTH}\s+\d{{1,2}},\s+20\d\d"
VERB = r"(Announces|Announce|Announcing|Commences|Commence|Launches|Reports|Prices|Extends)"
DATELINE = (rf"\s(?:[A-Z][A-Za-z\.]+,?\s){{1,3}}[\(\-–—,]*\s*\(?{MONTH}\s\d{{1,2}},\s20\d\d|"
            rf"\s[A-Z][A-Za-z\.]+,\s[A-Z][A-Za-z\.]+\s?[\(\-–—,]|/PRNewswire/|\(GLOBE NEWSWIRE\)|\(BUSINESS WIRE\)")
SUFFIX = {"inc", "inc.", "corp", "corp.", "corporation", "company", "co", "co.", "ltd", "ltd.", "plc", "llc", "group", "the", "&"}


OFFERKW = r"tender|exchange offer|offers? to purchase|offer to exchange|consent solicitation"


def get_title(text):
    """headline = text from the announcing verb to the dateline. Returns (display title, classify text)."""
    ms = list(re.finditer(rf"\b{VERB}\b", text[:3000], re.I))
    if not ms:
        return "", ""
    pick = next((m for m in ms if re.search(OFFERKW, text[m.start():m.start() + 260], re.I)), ms[0])
    body = text[pick.start():pick.start() + 300]
    d = re.search(DATELINE, body)
    title = body[:d.start()] if d else body[:230]
    ctext = body[:d.end()] if d else body[:230]
    return title.strip(), ctext.strip()


def clean_issuer(name):
    n = re.split(r"\s+\(", name)[0].strip(" ,")
    return n.title()


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def classify(title, text, doc=""):
    """kind from the headline only; the body is never used to decide the kind."""
    t = title.lower()
    if doc == "8-K":
        return "filing_body"
    if not t:
        return "no_title"
    has_offer = re.search(r"tender|exchange offer|offers? to purchase|offer to exchange|consent solicitation", t)
    if re.search(r"redemption|redeem", t) and not has_offer:
        return "redemption"
    if re.search(r"notes offering|offering of|offering to redeem|private offering|senior notes", t) and re.search(r"offering", t):
        return "financing_linked" if has_offer else "other"
    if re.search(r"registered exchange", t):
        return "registered_exchange"
    if not has_offer:
        return "other"
    if re.search(r"warrants|preferred stock|common stock|shares of", t) and not re.search(r"notes|debt|debentures|securities", t):
        return "equity_offer"
    if re.search(r"early (?:tender |participation )?results|early tender", t):
        return "early_results"
    if re.search(r"amendments? to|amended", t):
        return "amendment"
    if re.search(r"final results|expiration and (?:final )?results|results of|and results|expiration, pricing", t):
        return "final_results"
    if re.search(r"extension|extends|extended", t):
        return "extension"
    if re.search(r"pricing terms|pricing for|price determination", t):
        return "pricing_terms"
    if re.search(r"amend", t):
        return "amendment"
    if re.search(r"announces|commence|launch", t):
        return "launch"
    return "other"


def first(pats, text, flags=0, grp=1):
    for p in pats:
        m = re.search(p, text, flags)
        if m:
            return m
    return None


def money(m):
    if not m:
        return ""
    v, unit = m.group(1).rstrip(",."), (m.group(2) or "").lower()
    return v + (" " + unit if unit else "")


AMT = r"\$\s?([\d,]+(?:\.\d+)?)\s*(million|billion)?"
CAP_TERMS = r"(?:Aggregate Maximum Tender Amount|Maximum Tender Cap|Maximum Tender Amount|Maximum Amount|Tender Cap|Offer Cap|Waterfall Cap|Aggregate Cap|Total Cap|Maximum Purchase Price|Aggregate Maximum Purchase Price|Series Cap)"
TERM_EXP = r"Expiration (?:Date|Time)"
TERM_EARLY = r"Early (?:Tender|Participation|Consent|Exchange)? ?(?:Deadline|Date|Time)"


def to_iso(d):
    m = re.match(r"([A-Za-z]+)\.?\s+(\d{1,2}),\s+(20\d\d)", d or "")
    if not m:
        return d or ""
    try:
        return datetime.strptime(f"{m.group(1)[:3]} {m.group(2)} {m.group(3)}", "%b %d %Y").strftime("%Y-%m-%d")
    except ValueError:
        return d


def def_date(text, term, kind=""):
    """date attached to a defined term. The definition looks like: on August 14, 2026 (such date and time, the “Expiration Date”).
    Using the definition avoids settlement dates, which are defined with different terms."""
    if term == TERM_EXP and (kind in ("extension", "amendment") or re.search(r"extension|extends", text[:260], re.I)):
        ds = []
        for m in re.finditer(r"expir|extended|extends", text, re.I):
            ds += re.findall(DATE, text[m.start():m.start() + 200])
        parsed = [d for d in (to_iso(x) for x in ds) if d]
        if parsed:
            return max(parsed)
    for m in re.finditer(rf"[“\"]\s*{term}\s*[”\"]", text):
        before = re.findall(DATE, text[max(0, m.start() - 230):m.start()])
        if before:
            return before[-1]
        after = re.match(rf"[\s\S]{{0,80}}?\b(?:on|until)\s+({DATE})", text[m.end():m.end() + 140])
        if after:
            return after.group(1)
    if term == TERM_EXP:
        for m in re.finditer(rf"(?:will expire|is scheduled to expire|scheduled to expire|offers? expired)[\s\S]{{0,40}}?(?:at|on)[\s\S]{{0,70}}?({DATE})", text, re.I):
            if "ithdrawal" not in text[max(0, m.start() - 50):m.start() + 20]:
                return m.group(1)
        m = re.search(rf"Expiration (?:Date|Time),? which is[\s\S]{{0,70}}?({DATE})", text)
        if m:
            return m.group(1)
    return ""


NEWNOTE_BEFORE = r"redeem|redemption|new .{0,25}notes|issuance of|offering of|priced|financing transaction"
NEWNOTE_AFTER = r"^[^.]{0,90}?[“\"](?:New |Financing)"


def extract(text, kind=""):
    r = {}
    exchange = bool(re.search(r"exchange offers?|offers? to exchange", text[:2500], re.I)) and not re.search(r"cash tender offer", text[:2500], re.I)
    pats = [
        rf"{AMT}[^$]{{0,200}}?[“\"]\s*{CAP_TERMS}",
        rf"{CAP_TERMS}[”\"]?\s*(?:means|of|is|equal to)[^$.]{{0,120}}{AMT}",
        rf"[“\"]\s*{CAP_TERMS}\s*[”\"][^$]{{0,60}}{AMT}",
        rf"subject to a {AMT} cap",
        rf"exceed(?:s|ing) {AMT}",
    ]
    if not exchange:
        pats.append(rf"up to (?:a combined )?(?:an )?(?:aggregate )?(?:principal )?(?:amount|purchase price)?(?: of)?\s*{AMT}")
    m = first(pats, text)
    r["cap"] = money(m)
    if kind in ("amendment", "extension", "early_results"):
        m2 = re.search(rf"(?:reduced|increased|decreased|raised|upsized)[\s\S]{{0,160}}?from {AMT}[\s\S]{{0,30}}?to {AMT}", text, re.I)
        if m2:
            r["cap"] = m2.group(3).rstrip(",.") + (" " + m2.group(4).lower() if m2.group(4) else "")
    if m:
        ctx = text[max(0, m.start() - 200):m.end() + 200].lower()
        r["cap_basis"] = "purchase_price" if re.search(r"purchase price|tender consideration|total consideration", ctx) else "principal"
    else:
        r["cap_basis"] = ""
    r["any_and_all"] = "yes" if re.search(r"any and all", text[:2500], re.I) else ""
    r["early_date"] = to_iso(def_date(text, TERM_EARLY, kind))
    r["expiration_date"] = to_iso(def_date(text, TERM_EXP, kind))
    # securities: coupon + maturity year, skipping new notes, redeemed notes and financing
    s = set()
    for m in re.finditer(r"(\d{1,2}\.\d{1,3})%\s+(?:[A-Za-z\-]+\s+){0,5}?(?:notes|debentures|bonds|securities)\s+due\s+(?:\w+\s+\d{0,2},?\s*)?(20\d\d|21\d\d)", text, re.I):
        before = text[max(0, m.start() - 150):m.start()]
        after = text[m.end():m.end() + 140]
        if re.search(NEWNOTE_BEFORE, before, re.I) or re.search(NEWNOTE_AFTER, after):
            continue
        s.add(f"{m.group(1)}% {m.group(2)}")
    s = sorted(s)
    r["securities"] = "; ".join(s)
    r["n_securities"] = len(s)
    cus = set()
    if re.search(r"CUSIP", text):
        for a, b, c in re.findall(r"\b(\d[0-9A-Z]{5})\s?([0-9A-Z]{2})\s?(\d)\b", text):
            cu = a + b + c
            if re.search(r"[A-Z]", cu):
                cus.add(cu)
    r["cusips"] = "; ".join(sorted(cus))
    r["n_cusips"] = len(cus)
    m = first([
        rf"a total of {AMT} in aggregate principal amount[^.]{{0,40}}(?:had been )?validly tendered",
        rf"{AMT}[^.$]{{0,80}}(?:aggregate )?principal amount[^.$]{{0,80}}validly tendered",
        rf"validly tendered[^.$]{{0,120}}{AMT}",
    ], text, re.I)
    r["tendered_total"] = money(m) if kind != "launch" else ""
    if m and not m.group(2) and float(m.group(1).replace(",", "") or 0) < 100000:
        r["tendered_total"] = ""
    r["table_only"] = "yes" if (not r["tendered_total"] and re.search(r"Principal Amount Tendered|Amount Tendered at", text)) else ""
    r["offer_type"] = "exchange" if exchange else "cash_tender"
    r["consent_solicitation"] = "yes" if re.search(r"consent solicitation", text[:2500], re.I) else ""
    return r


events = []
for mm in meta:
    text = open(os.path.join(OUT, "texts", mm["key"] + ".txt"), encoding="utf-8").read()
    text = re.sub(r"\b(Januar|Februar|Septembe|Octobe|Novembe|Decembe)\s(y|r)\b", r"\1\2", text)  # HTML sometimes splits a month
    title, ctext = get_title(text)
    subject = clean_issuer(mm["issuer"])
    kind = classify(ctext, text, mm["doc"])
    if kind == "other" and re.search(r"notes offering|offering of .{0,40}notes|pricing of .{0,60}notes", ctext, re.I) and not re.search(r"results|earnings|quarter", ctext, re.I) and re.search(r"(?:fund|finance|repurchase)[^.]{0,160}tender offer", text[:5000], re.I):
        kind = "financing_linked"
    if kind == "no_title":
        # fall back to the first 700 characters when no headline verb was found, and say so
        probe = text[:700].lower()
        kind = "unverified_offer" if re.search(r"tender offer|exchange offer|offer to purchase", probe) else "other"
    ev = {"file_date": mm["file_date"], "issuer_sec": mm["issuer"], "subject": subject, "doc": mm["doc"], "kind": kind,
          "title": title[:200], "url": mm["url"]}
    if kind not in ("other", "equity_offer", "redemption", "financing_linked", "filing_body", "registered_exchange"):
        ev.update(extract(text, kind))
    events.append(ev)

# dedupe: same headline on the same date is one release filed by several entities
seen, uniq = {}, []
for e in sorted(events, key=lambda e: e["file_date"]):
    k = (norm(e["title"])[:100], e["kind"]) if e["title"] else (e["url"],)
    if k in seen:
        seen[k]["n_filers"] = seen[k].get("n_filers", 1) + 1
        continue
    e["n_filers"] = 1
    seen[k] = e
    uniq.append(e)

offer_kinds = ("launch", "early_results", "final_results", "extension", "pricing_terms", "amendment", "unverified_offer")
ev_offer = [e for e in uniq if e["kind"] in offer_kinds]
other_rel = [e for e in uniq if e["kind"] == "financing_linked"]

# offers: group lifecycle events by subject company and securities overlap, start a new offer at each launch
groups = defaultdict(list)
RANK = {"launch": 0, "amendment": 1, "extension": 2, "early_results": 3, "pricing_terms": 4, "final_results": 5, "unverified_offer": 6}
for e in sorted(ev_offer, key=lambda e: (e["file_date"], RANK.get(e["kind"], 9))):
    groups[norm(e["issuer_sec"].split()[0] if e["issuer_sec"] else e["subject"])].append(e)
offers = []
for subj, lst in groups.items():
    cur = None
    for e in lst:
        sec = set(filter(None, e.get("securities", "").split("; ")))
        newoffer = (cur is None or e["kind"] == "launch"
                    or (sec and cur["sec"] and not (sec & cur["sec"]))
                    or (datetime.fromisoformat(e["file_date"]) - datetime.fromisoformat(cur["last"])).days > 75)
        if newoffer:
            cur = {"subject": e["subject"] or e["issuer_sec"], "first": e["file_date"], "last": e["file_date"], "events": [],
                   "sec": set(), "has_launch": False}
            offers.append(cur)
        cur["events"].append(e)
        cur["last"] = e["file_date"]
        cur["sec"] |= sec
        cur["has_launch"] |= e["kind"] == "launch"
for o in offers:
    last = None
    for e in o["events"]:
        if e.get("cap"):
            last = e
        elif last:
            e["cap"], e["cap_basis"], e["cap_source"] = last["cap"], last["cap_basis"], "inherited from an earlier release in the same offer"
        if e.get("cap") and last and e["cap"] == last["cap"] and last["cap_basis"] == "purchase_price":
            e["cap_basis"] = "purchase_price"
    exp = early = ""
    for e in o["events"]:
        if e.get("expiration_date"):
            exp = e["expiration_date"]
        elif exp:
            e["expiration_date"], e["expiration_source"] = exp, "inherited"
        if e.get("early_date"):
            early = e["early_date"]
        elif early:
            e["early_date"], e["early_source"] = early, "inherited"
for o in offers:
    ks = [e["kind"] for e in o["events"]]
    o["status"] = "closed" if "final_results" in ks else "open_or_unknown"
    o["event_kinds"] = ">".join(ks)
    o["cap"] = next((e["cap"] for e in o["events"] if e.get("cap")), "")
    o["expiration_latest"] = next((e["expiration_date"] for e in reversed(o["events"]) if e.get("expiration_date")), "")
    o["securities"] = "; ".join(sorted(o["sec"]))[:200]
    o["urls"] = " ".join(e["url"] for e in o["events"])

def w(name, rows, cols):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        for r in rows:
            wr.writerow({c: r.get(c, "") for c in cols})

ecols = ["file_date", "subject", "issuer_sec", "doc", "kind", "offer_type", "consent_solicitation", "securities", "n_securities", "n_cusips",
         "cusips", "cap", "cap_basis", "any_and_all", "early_date", "early_source", "expiration_date", "expiration_source", "cap_source", "tendered_total", "table_only", "n_filers", "title", "url"]
w("events.csv", uniq, ecols)
w("offers.csv", [dict(o, n_events=len(o["events"])) for o in offers],
  ["subject", "first", "last", "status", "n_events", "event_kinds", "securities", "cap", "expiration_latest", "has_launch", "urls"])

# hand check sheet: every offer event, plus 15 documents we called "not an offer" to estimate what the classifier misses
random.seed(17)
non = [e for e in uniq if e["kind"] in ("other", "financing_linked", "redemption", "registered_exchange", "equity_offer")]
neg = random.sample(non, min(15, len(non)))
hc = []
for grp, rows_ in (("offer event", ev_offer), ("called not an offer", neg)):
    for e in sorted(rows_, key=lambda e: e["file_date"]):
        hc.append({"group": grp, "file_date": e["file_date"], "subject": e["subject"], "url": e["url"], "title": e["title"],
                   "kind_found": e["kind"], "kind_ok_YN": "", "securities_found": e.get("securities", ""), "securities_ok_YN": "",
                   "cap_found": e.get("cap", ""), "cap_basis": e.get("cap_basis", ""), "cap_ok_YN": "",
                   "expiration_found": e.get("expiration_date", ""), "expiration_ok_YN": "",
                   "early_found": e.get("early_date", ""), "early_ok_YN": "", "notes": ""})
w("handcheck.csv", hc, list(hc[0].keys()))

# summary
L = []
L.append(f"cached documents {len(meta)}, unique releases {len(uniq)}")
L.append("kinds " + str(dict(Counter(e["kind"] for e in uniq))))
L.append(f"offer lifecycle events {len(ev_offer)}, grouped into {len(offers)} offers, {sum(1 for o in offers if o['has_launch'])} with a launch release seen")
L.append(f"financing linked to a tender {len(other_rel)}")
def cov(k, sub):
    return "%d/%d" % (sum(1 for e in sub if e.get(k)), len(sub))
for kind in offer_kinds:
    sub = [e for e in ev_offer if e["kind"] == kind]
    if sub:
        L.append(f"{kind} n={len(sub)} securities {cov('securities', sub)} cusips {cov('cusips', sub)} early_date {cov('early_date', sub)} "
                 f"expiration {cov('expiration_date', sub)} cap {cov('cap', sub)} tendered_total {cov('tendered_total', sub)} table_only {cov('table_only', sub)}")
open(os.path.join(OUT, "summary_v3.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
