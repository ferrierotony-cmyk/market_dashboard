"""Upcoming macro releases and FOMC meetings.

Sources, both public pages that need no key:
  * FRED's release calendar (https://fred.stlouisfed.org/releases/calendar), one request per
    release. FRED shows times in US Central Time.
  * The Fed's FOMC calendar page, for meeting dates.
Page layouts can change. If a source fails, that source is reported as unavailable and the
rest still works; nothing here raises on a network or parsing problem.

Usage:
  python macro_calendar.py              # next 14 days
  python macro_calendar.py --days 45
"""
import argparse
import re
import time
import urllib.request
from datetime import date, datetime, timedelta

import pandas as pd

import fredcfg

UA = {"User-Agent": "Mozilla/5.0 (fedliq research script)"}
CAL_URL = "https://fred.stlouisfed.org/releases/calendar?view=list&rid={rid}&vs={vs}&ve={ve}"
FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

# FRED release id: (label, importance, (context series, transform, context label) or None)
RELEASES = {
    10: ("CPI inflation", "high", ("CPIAUCSL", "yoy12", "CPI y/y %")),
    54: ("PCE inflation", "high", ("PCEPILFE", "yoy12", "core PCE y/y %")),
    50: ("Jobs report", "high", ("UNRATE", "level", "unemployment rate %")),
    53: ("GDP", "high", ("A191RL1Q225SBEA", "level", "real GDP growth, q/q annualized %")),
    46: ("PPI", "medium", None),
    9: ("Retail sales", "medium", None),
    180: ("Jobless claims", "medium", ("ICSA", "level", "initial claims")),
    192: ("JOLTS job openings", "medium", None),
    20: ("Fed balance sheet (H.4.1)", "medium", ("WALCL", "bn_from_mn", "Fed assets, $B")),
    13: ("Industrial production", "low", None),
}

_DATE = r'<span style="font-weight: bold;">\s*([A-Za-z]+ [A-Za-z]+ \d{1,2}, \d{4})\s*</span>'
_ROW = (r'<td nowrap[^>]*>\s*([^<]*?)\s*</td>\s*<td[^>]*>\s*'
        r'<a href="/release\?rid=(\d+)">([^<]+)</a>(.*?)</td>')
_CAL_RE = re.compile(_DATE + "|" + _ROW, re.S)


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


# ------------------------------------------------------------------ FRED release calendar
def parse_calendar(html: str) -> list[dict]:
    """Rows of {date, time, rid, release, released} from a FRED calendar list page."""
    body = html[html.find("<tbody>"):] if "<tbody>" in html else html
    cur, out = None, []
    for m in _CAL_RE.finditer(body):
        if m.group(1):
            cur = datetime.strptime(m.group(1), "%A %B %d, %Y").date()
        elif cur is not None:
            out.append({"date": cur, "time": m.group(2), "rid": int(m.group(3)),
                        "release": m.group(4).strip(), "released": "fa-check" in (m.group(5) or "")})
    return out


def fetch_release_events(start: date, end: date, rids=None, pause: float = 0.3) -> tuple[list[dict], list[str]]:
    events, problems = [], []
    for rid in (rids or RELEASES):
        try:
            html = _get(CAL_URL.format(rid=rid, vs=start.isoformat(), ve=end.isoformat()))
            events += [e for e in parse_calendar(html) if e["rid"] == rid]
        except Exception as e:
            problems.append(f"release {rid} ({RELEASES.get(rid, ('?',))[0]}): {str(e)[:60]}")
        time.sleep(pause)
    return events, problems


# ------------------------------------------------------------------ FOMC
def _month_number(text: str) -> int:
    first = text.split("/")[0].strip()
    for fmt in ("%B", "%b"):
        try:
            return datetime.strptime(first[:9] if fmt == "%B" else first[:3], fmt).month
        except ValueError:
            continue
    raise ValueError(f"unrecognized month {text!r}")


def parse_fomc(html: str, years=None) -> list[dict]:
    """Decision dates (last day of each meeting). A '*' on the page marks meetings with projections."""
    heads = list(re.finditer(r"(\d{4}) FOMC Meetings", html))
    out = []
    for i, h in enumerate(heads):
        year = int(h.group(1))
        if years and year not in years:
            continue
        seg = html[h.start(): heads[i + 1].start() if i + 1 < len(heads) else h.start() + 20000]
        months = re.findall(r'fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>', seg)
        days = re.findall(r'fomc-meeting__date[^>]*>\s*([^<]+?)\s*<', seg)
        for mo, dy in zip(months, days):
            nums = re.findall(r"\d+", dy)
            if not nums:
                continue
            start_day, end_day = int(nums[0]), int(nums[-1])
            month = _month_number(mo)
            if end_day < start_day:           # meeting spans two months, e.g. Oct 31 - Nov 1
                month += 1
            y = year + (1 if month > 12 else 0)
            month = (month - 1) % 12 + 1
            out.append({"date": date(y, month, end_day), "projections": "*" in dy})
    return sorted(out, key=lambda e: e["date"])


def fetch_fomc(years) -> tuple[list[dict], list[str]]:
    try:
        return parse_fomc(_get(FOMC_URL), set(years)), []
    except Exception as e:
        return [], [f"FOMC calendar: {str(e)[:60]}"]


# ------------------------------------------------------------------ combined view
def upcoming(days: int = 14, today: date | None = None, source=None, with_context: bool = True) -> tuple[pd.DataFrame, list[str]]:
    """Upcoming events within `days`, soonest first, plus a list of sources that failed."""
    today = today or date.today()
    end = today + timedelta(days=days)
    events, problems = fetch_release_events(today, end)
    rows = []
    for e in events:
        if e["released"] or not (today <= e["date"] <= end):
            continue
        label, importance, ctx = RELEASES[e["rid"]]
        rows.append({"date": e["date"], "time (CT)": e["time"], "event": label, "importance": importance,
                     "rid": e["rid"], "_ctx": ctx})
    fomc, fprob = fetch_fomc({today.year, end.year})
    problems += fprob
    for f in fomc:
        if today <= f["date"] <= end:
            rows.append({"date": f["date"], "time (CT)": "1:00 pm",
                         "event": "FOMC rate decision" + (" + projections" if f["projections"] else ""),
                         "importance": "high", "rid": 101, "_ctx": ("DFF", "level", "fed funds effective %")})
    df = pd.DataFrame(rows, columns=["date", "time (CT)", "event", "importance", "rid", "_ctx"])
    if df.empty:
        return df.drop(columns="_ctx").assign(**{"days away": [], "latest": []}), problems
    clock = pd.to_datetime(df["time (CT)"], format="%I:%M %p", errors="coerce")   # "N/A" sorts last
    df = df.assign(_clock=clock).sort_values(["date", "_clock"], na_position="last").drop(columns="_clock")
    df = df.reset_index(drop=True)
    df["days away"] = [(d - today).days for d in df["date"]]
    df["latest"] = ""
    if with_context:
        src = source or fredcfg.get_source()
        cache = {}
        for i, ctx in df["_ctx"].items():
            if not ctx:
                continue
            sid, kind, label = ctx
            try:
                if sid not in cache:
                    cache[sid] = fredcfg._transform(src.series(sid, "2023-01-01"), kind)
                s = cache[sid]
                df.loc[i, "latest"] = f"{label}: {s.iloc[-1]:,.2f} ({s.index[-1]:%Y-%m-%d})"
            except Exception:
                pass
    return df.drop(columns="_ctx"), problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args(argv)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 80)
    df, problems = upcoming(args.days)
    print(f"Upcoming releases, next {args.days} days (times as shown by FRED, US Central):")
    print(df.drop(columns="rid").to_string(index=False) if len(df) else "  none found")
    for p in problems:
        print("  unavailable:", p)


if __name__ == "__main__":
    main()
