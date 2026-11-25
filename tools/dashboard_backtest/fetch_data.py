"""Downloads the free data long_test.py needs.

Run: python fetch_data.py <data dir>
FRED series come from its API when FRED_API_KEY is set, and from the public CSV download otherwise.
The CSV download hangs when a data center asks for it, so the GitHub job needs the key. MOVE and the S&P 500 come from Yahoo Finance, the same source the dashboard uses."""
import csv, io, json, os, sys, time, urllib.parse, urllib.request

AGENT = "portfolio-live-data/1.0"
FRED = ("BAA10Y", "DGS10", "VIXCLS", "BAMLC0A0CM", "BAMLH0A0HYM2")
YAHOO = {"MOVE": "^MOVE", "GSPC": "^GSPC"}
MIN_ROWS = {"BAA10Y": 8000, "DGS10": 12000, "VIXCLS": 8000, "BAMLC0A0CM": 600, "BAMLH0A0HYM2": 600, "MOVE": 5000, "GSPC": 10000}


def get(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=60) as r:
                return r.read().decode("utf-8")
        except Exception:
            if k == tries - 1: raise
            time.sleep(5 * (k + 1))


def fred_csv(j):
    """The API's JSON as the same two columns the CSV download gives. A dot means no print that day."""
    return "observation_date,value\n" + "".join("%s,%s\n" % (o["date"], "" if o["value"] == "." else o["value"]) for o in j["observations"])


def fred(s):
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key: return get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + s)
    return fred_csv(json.loads(get("https://api.stlouisfed.org/fred/series/observations?file_type=json&series_id=%s&api_key=%s" % (s, urllib.parse.quote(key)))))


def main(d):
    os.makedirs(d, exist_ok=True)
    for s in FRED:
        t = fred(s)
        n = sum(1 for _ in csv.reader(io.StringIO(t))) - 1
        if n < MIN_ROWS[s]: raise SystemExit("%s has only %d rows" % (s, n))
        open(os.path.join(d, "fred_%s.csv" % s), "w", encoding="utf-8", newline="").write(t); print(s, n)
    for name, sym in YAHOO.items():
        j = json.loads(get("https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=0&period2=%d&interval=1d" % (urllib.parse.quote(sym), time.time())))["chart"]["result"][0]
        off = j["meta"].get("gmtoffset", 0); q = j["indicators"]["quote"][0]["close"]
        rows = [(time.strftime("%Y-%m-%d", time.gmtime(t + off)), c) for t, c in zip(j["timestamp"], q) if c is not None]
        # today's row is a price in the middle of the day, not a close
        rows = [r for r in rows if r[0] < time.strftime("%Y-%m-%d", time.gmtime())]
        if len(rows) < MIN_ROWS[name]: raise SystemExit("%s has only %d rows" % (name, len(rows)))
        with open(os.path.join(d, "yahoo_%s.csv" % name), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh); w.writerow(["date", "close"]); w.writerows(rows)
        print(name, len(rows), rows[-1][0])


if __name__ == "__main__":
    main(sys.argv[1])
