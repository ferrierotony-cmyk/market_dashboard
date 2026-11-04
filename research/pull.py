"""One-off research pull for the portfolio analysis. Public sources only.
Writes research/out/*.csv. Needs SEC_CONTACT_EMAIL in the environment for the EDGAR calls."""
import os, sys, time, json, csv, datetime as dt, requests

OUT = "research/out"; os.makedirs(OUT, exist_ok=True)
CONTACT = os.environ.get("SEC_CONTACT_EMAIL", "")
UA = {"User-Agent": "market_dashboard research student project " + CONTACT, "Accept-Encoding": "gzip, deflate"}
BROWSER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}

def get(url, headers, tries=2, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=headers, timeout=25, **kw)
            if r.status_code == 200: return r
            print("http", r.status_code, url[:120]); time.sleep(2 + 3 * i)
        except Exception as e:
            print("err", e, url[:120]); time.sleep(2 + 3 * i)
    return None

# 1. FRED, ten years
for sid in ["BAMLC0A0CM", "BAMLH0A0HYM2", "DGS10", "VIXCLS", "BAMLC0A4CBBB", "BAMLH0A1HYBB"]:
    r = get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s&cosd=2016-01-01" % sid, BROWSER)
    if r: open(os.path.join(OUT, "fred_%s.csv" % sid), "w").write(r.text); print("fred", sid, len(r.text.splitlines()))

# 2. Yahoo daily bars, ten years
for sym in ["^MOVE", "^GSPC", "^VIX", "ES=F", "LQD", "HYG"]:
    r = get("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=10y&interval=1d" % requests.utils.quote(sym), BROWSER)
    if not r: continue
    try:
        res = r.json()["chart"]["result"][0]; ts = res["timestamp"]; q = res["indicators"]["quote"][0]
        with open(os.path.join(OUT, "yahoo_%s.csv" % sym.replace("^", "").replace("=", "_")), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["date", "open", "high", "low", "close"])
            for i, t in enumerate(ts):
                w.writerow([dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"), q["open"][i], q["high"][i], q["low"][i], q["close"][i]])
        print("yahoo", sym, len(ts))
    except Exception as e:
        print("yahoo parse fail", sym, e)

# 3. EDGAR full text search: daily counts of pricing term sheets on Form FWP, and of 424B5 prospectus supplements.
#    Used as a public proxy for investment grade new issue activity by day.
if not CONTACT:
    print("no SEC contact, skipping EDGAR"); sys.exit(0)
def count(q, forms, d):
    url = "https://efts.sec.gov/LATEST/search-index?q=%s&forms=%s&dateRange=custom&startdt=%s&enddt=%s" % (requests.utils.quote(q), forms, d, d)
    r = get(url, UA); time.sleep(0.12)
    if not r: return ""
    try: return r.json().get("hits", {}).get("total", {}).get("value", "")
    except Exception: return ""
start = dt.date(2023, 1, 1); today = dt.date.today(); t0 = time.time(); BUDGET = float(os.environ.get("EDGAR_BUDGET_SEC", "2100"))
with open(os.path.join(OUT, "edgar_daily.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "fwp_pricing_term_sheet", "fwp_all", "b5_all", "b2_all"])
    d = start; n = 0
    # newest first, so a time budget cuts the oldest history, not the recent months
    days = [d for d in (start + dt.timedelta(i) for i in range((today - start).days + 1)) if d.weekday() < 5][::-1]
    for d in days:
        if time.time() - t0 > BUDGET: print("budget reached at", d); break
        if True:
            ds = d.isoformat()
            w.writerow([ds, count('"pricing term sheet"', "FWP", ds), count('*', "FWP", ds), count('*', "424B5", ds), ""])
            n += 1
            if n % 50 == 0: print("edgar days", n, ds); f.flush()
print("done")
