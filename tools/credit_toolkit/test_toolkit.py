"""Offline checks on cached SEC data. Run: python test_toolkit.py"""
import os
os.environ["CREDIT_CACHE_TTL_HOURS"] = "999999"
import urllib.request


def blocked(*a, **k):
    raise RuntimeError("network blocked in tests")


urllib.request.urlopen = blocked
import json
from credit_toolkit import edgar
from credit_toolkit.edgar import Period, _derive, spread_issuer
from datetime import date

# read the cache whatever its age
edgar._get_json = lambda url, cache_name=None, ttl_hours=0: json.loads((edgar.CACHE_DIR / cache_name).read_text(encoding="utf-8"))


def check(name, ok, detail=""):
    print(("pass " if ok else "FAIL ") + name, detail)
    if not ok:
        raise SystemExit(1)


# one debt basis: pieces win over the all-in tag
p = Period("x", date(2026, 1, 1), {"lt_debt_total": 110.0, "lt_debt_noncurrent": 90.0, "lt_debt_current": 10.0, "short_term_borrowings": 5.0}, {"lt_debt_current": "LongTermDebtCurrent"})
_derive(p); check("carrying pieces plus short term", p.values["total_debt"] == 105.0, p.values["total_debt"])
p = Period("x", date(2026, 1, 1), {"lt_debt_noncurrent": 90.0, "lt_debt_current": 10.0, "short_term_borrowings": 5.0}, {"lt_debt_current": "DebtCurrent (10-Q)"})
_derive(p); check("DebtCurrent is not counted twice", p.values["total_debt"] == 100.0, p.values["total_debt"])
p = Period("x", date(2026, 1, 1), {"lt_debt_total": 110.0}, {})
_derive(p); check("all-in tag is the fallback", p.values["total_debt"] == 110.0)
p = Period("x", date(2026, 1, 1), {}, {})
_derive(p); check("no debt tag stays empty", p.values["total_debt"] is None and p.values["gross_leverage"] is None)
for t in ("T", "CCL", "AAPL", "F"):
    try:
        r = spread_issuer(t, 2)["periods"][-1]
        print(t, r.label, "debt", None if r.values["total_debt"] is None else round(r.values["total_debt"] / 1e6), "lev", r.values["gross_leverage"] and round(r.values["gross_leverage"], 2), "cov", r.values["interest_coverage"] and round(r.values["interest_coverage"], 1), "|", r.sources.get("total_debt"))
    except (RuntimeError, OSError) as e:
        print(t, "not cached:", str(e)[:60])
print("all checks passed")
