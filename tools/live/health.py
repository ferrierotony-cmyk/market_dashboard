"""Checks the live sites and feeds, and exits 1 with a list when something is wrong, so the GitHub job fails and sends an email.

Run: python health.py [--site url] [--pages url] [--feed url]"""
import argparse, json, re, sys, time, urllib.request
from datetime import datetime, timezone

AGENT = "portfolio-live-data/1.0"
SITE = "https://anthonyferriero.vercel.app/"
PAGES = "https://ferrierotony-cmyk.github.io/market_dashboard/"
FEED = "https://raw.githubusercontent.com/ferrierotony-cmyk/market_dashboard/live-results/live.json"
# oldest a section may be, in days. The weekend and one missed run are allowed for.
MAX_AGE = {"models": 5, "toolkit": 5, "tender": 5, "lab": 10, "window": 45}
WANT = ("SKYD", "NFLX", "DIS", "CMCSA", "FOXA", "FOX", "^VIX")


def get(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=40) as r:
                return r.read()
        except Exception as e:
            err = e
            if k < tries - 1: time.sleep(4 * (k + 1))
    raise err


def age_days(stamp, now=None):
    stamp = stamp.replace(" ", "T").rstrip("Z")
    t = datetime.fromisoformat(stamp[:19] if len(stamp) >= 19 else stamp)
    return ((now or datetime.now(timezone.utc)) - t.replace(tzinfo=timezone.utc)).total_seconds() / 86400


def business_gap(now):
    """Days of silence that are normal today: a price from Friday is fine on Sunday."""
    return 1.5 + {5: 1, 6: 2, 0: 2}.get(now.weekday(), 0)


def check_quotes(j, now):
    out = []
    q = j.get("quotes", {})
    for s in WANT:
        if s not in q: out.append("no quote for " + s)
        elif not q[s].get("price", 0) > 0: out.append("bad quote for " + s)
        elif age_days(q[s]["time"], now) > business_gap(now) + 2: out.append("%s quote is %.1f days old" % (s, age_days(q[s]["time"], now)))
    return out


def check_snapshot(j, now):
    out = []
    d = age_days(j["built_at"], now)
    if d > business_gap(now) + .5: out.append("dashboard snapshot is %.1f days old" % d)
    for s in ("DGS10", "BAMLC0A0CM", "BAMLH0A0HYM2"):
        x = j.get("fred", {}).get(s)
        if not x or x.get("last") is None: out.append("no print for " + s)
        elif age_days(x["date"], now) > 7: out.append("%s print is %.0f days old" % (s, age_days(x["date"], now)))
    return out


def check_feed(j, now):
    out = []
    for s, lim in MAX_AGE.items():
        x = j.get("sections", {}).get(s)
        if not x or not x.get("data"): out.append("feed has no %s section" % s); continue
        if not x.get("ok"): out.append("%s failed on its last run: %s" % (s, x.get("error", "")))
        if age_days(x["built"], now) > lim: out.append("%s is %.0f days old" % (s, age_days(x["built"], now)))
    return out


def check_page(name, html):
    out = []
    vis = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    if "<h1" not in html and name != "trading.html": out.append(name + " has no title")
    if 'style="' in vis: out.append(name + " has an inline style")
    if "—" in vis or "–" in vis: out.append(name + " has a long dash")
    return out


def main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--site", default=SITE); p.add_argument("--pages", default=PAGES); p.add_argument("--feed", default=FEED)
    a = p.parse_args(argv); now = datetime.now(timezone.utc); bad, n = [], 0

    def tryit(label, f):
        nonlocal n
        n += 1
        try: bad.extend(f() or [])
        except Exception as e: bad.append("%s: %s" % (label, str(e)[:120]))

    seen, todo = set(), ["index.html"]
    while todo:
        name = todo.pop()
        if name in seen: continue
        seen.add(name)

        def page(name=name):
            html = get(a.site + name).decode("utf-8")
            for u in re.findall(r'(?:href|src)="([^"#?]+)"', html):
                if re.match(r"https?:|mailto:|data:", u): continue
                if u.endswith(".html"): todo.append(u)
                elif u not in seen:
                    seen.add(u); tryit(u, lambda u=u: (get(a.site + u.replace(" ", "%20")), [])[1])
            return check_page(name, html)
        tryit(name, page)
    for u in ("", "portfolio/index.html", "tender/", "tender/data.json"): tryit("github pages " + u, lambda u=u: (get(a.pages + u), [])[1])
    tryit("quotes", lambda: check_quotes(json.loads(get(a.site + "api/quotes")), now))
    tryit("feed", lambda: check_feed(json.loads(get(a.feed)), now))
    tryit("dashboard snapshot", lambda: check_snapshot(json.loads(get(a.pages + "market_snapshot.json")), now))
    print("%d checks, %d problems" % (n, len(bad)))
    for b in bad: print("PROBLEM " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
