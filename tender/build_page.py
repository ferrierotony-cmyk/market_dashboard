"""Build the readable tender tracker page from offers.csv and events.csv.

Usage: python tender/build_page.py [out_dir]
Writes out_dir/index.html (full page, for GitHub Pages) and out_dir/page_fragment.html (for the Artifact tool).
Data comes only from public SEC filings. The reliability numbers on the page are from the blind evaluation windows in tender/eval/README.md."""
import csv, datetime as dt, json, os, re, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "out")
OFFER_KINDS = {"launch", "early_results", "final_results", "extension", "pricing_terms", "amendment", "terminated"}


def money(s):
    s = (s or "").strip()
    if not s:
        return ""
    m = re.match(r"^\$?\s*([\d,\.]+)\s*(million|billion|bn|mm|m|b)?", s, re.I)
    if not m:
        return s
    try:
        n = float(m.group(1).replace(",", ""))
    except ValueError:
        return s
    u = (m.group(2) or "").lower()
    if u in ("million", "mm", "m"):
        n *= 1e6
    elif u in ("billion", "bn", "b"):
        n *= 1e9
    if n >= 1e9:
        return "$%.2fbn" % (n / 1e9)
    if n >= 1e6:
        return "$%dm" % round(n / 1e6) if abs(n / 1e6 - round(n / 1e6)) < 0.05 else "$%.1fm" % (n / 1e6)
    return "$%s" % format(int(n), ",")


def rows(name):
    p = os.path.join(OUT, name)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


def build():
    offers, events = rows("offers.csv"), rows("events.csv")
    ev = []
    for e in events:
        ev.append([e["file_date"], e["subject"], e["kind"], e["securities"], money(e["cap"]), e["expiration_date"],
                   e["early_date"], e["url"], e["title"][:160]])
    off = []
    for o in offers:
        off.append({"subject": o["subject"], "first": o["first"], "last": o["last"], "kinds": [k for k in o["event_kinds"].split(">") if k],
                    "securities": [s.strip() for s in o["securities"].split(";") if s.strip()], "cap": money(o["cap"]),
                    "exp": o["expiration_latest"], "launch": o["has_launch"] == "True", "urls": o["urls"].split()})
    off.sort(key=lambda x: x["last"], reverse=True)
    last_date = max([e[0] for e in ev] or [""])
    data = {"offers": off, "events": ev, "through": last_date, "built": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
            "offerKinds": sorted(OFFER_KINDS)}
    return json.dumps(data, separators=(",", ":")).replace("</", "<\\/")


TEMPLATE = open(os.path.join(os.path.dirname(__file__), "page_template.html"), encoding="utf-8").read()

if __name__ == "__main__":
    frag = TEMPLATE.replace("__DATA__", build())
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "page_fragment.html"), "w", encoding="utf-8").write(frag)
    full = '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n' + frag
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(full)
    print("page built", len(full), "bytes")
