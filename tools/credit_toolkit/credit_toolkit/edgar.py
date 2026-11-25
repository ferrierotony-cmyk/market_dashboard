"""SEC EDGAR client + XBRL financial spreading for credit analysis.

Standard library only (urllib); pandas/openpyxl are used by the CLI scripts for output.
SEC fair-access rules: <=10 requests/second and a descriptive User-Agent.
Set SEC_USER_AGENT to "YourFirm YourName you@yourfirm.com" for production use.
"""
from __future__ import annotations

import gzip
import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

USER_AGENT = os.environ.get("SEC_USER_AGENT", "CreditResearchToolkit/1.0 research-tool@example.com")
CACHE_DIR = Path(os.environ.get("CREDIT_CACHE_DIR", Path(__file__).resolve().parent.parent / ".cache"))
CACHE_TTL_HOURS = float(os.environ.get("CREDIT_CACHE_TTL_HOURS", "12"))
_MIN_INTERVAL = 0.15  # seconds between SEC requests (~6-7 req/s, under the 10/s limit)
_last_request = 0.0


# --------------------------------------------------------------------------- HTTP
def _get_json(url: str, cache_name: str | None = None, ttl_hours: float = CACHE_TTL_HOURS) -> dict:
    global _last_request
    if cache_name:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / cache_name
        if path.exists() and (time.time() - path.stat().st_mtime) < ttl_hours * 3600:
            return json.loads(path.read_text(encoding="utf-8"))
    wait = _MIN_INTERVAL - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
    _last_request = time.time()
    text = raw.decode("utf-8")
    if text.lstrip().startswith("<"):
        raise RuntimeError(
            f"SEC returned HTML instead of JSON for {url} (likely rate-limited or User-Agent rejected). "
            "Set SEC_USER_AGENT to 'Firm Name your@email.com' and retry."
        )
    data = json.loads(text)
    if cache_name:
        (CACHE_DIR / cache_name).write_text(text, encoding="utf-8")
    return data


def resolve_cik(identifier: str) -> tuple[str, str]:
    """Ticker or CIK -> (10-digit CIK, company name)."""
    ident = identifier.strip().upper()
    if ident.isdigit():
        cik = ident.zfill(10)
        sub = get_submissions(cik)
        return cik, sub.get("name", cik)
    tickers = _get_json("https://www.sec.gov/files/company_tickers.json", "company_tickers.json", ttl_hours=168)
    for row in tickers.values():
        if row["ticker"].upper() == ident:
            return str(row["cik_str"]).zfill(10), row["title"]
    raise ValueError(f"Ticker '{identifier}' not found in SEC ticker map. Try the CIK instead.")


def get_submissions(cik: str) -> dict:
    return _get_json(f"https://data.sec.gov/submissions/CIK{cik}.json", f"submissions_{cik}.json", ttl_hours=1)


def get_company_facts(cik: str) -> dict:
    return _get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", f"facts_{cik}.json")


# --------------------------------------------------------------------------- concept map
# Ordered fallbacks: the first concept with data for the period wins. The concept used is
# recorded in the audit trail so every number traces back to a tagged XBRL fact.
DURATION_CONCEPTS: dict[str, list[str]] = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"],
    "operating_income": ["OperatingIncomeLoss"],
    "d_and_a": ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
                "DepreciationAndAmortization", "Depreciation"],
    "interest_expense": ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt",
                         "InterestAndDebtExpense", "InterestPaidNet"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
}
INSTANT_CONCEPTS: dict[str, list[str]] = {
    "cash": ["CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "lt_debt_total": ["LongTermDebt", "DebtLongtermAndShorttermCombinedAmount"],
    "lt_debt_noncurrent": ["LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"],
    "lt_debt_current": ["LongTermDebtCurrent", "DebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent"],
    "short_term_borrowings": ["ShortTermBorrowings", "CommercialPaper"],
    "equity": ["StockholdersEquity",
               "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "total_assets": ["Assets"],
}


def _parse(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


def _usd_facts(facts: dict, concept: str) -> list[dict]:
    node = facts.get("facts", {}).get("us-gaap", {}).get(concept)
    if not node:
        return []
    return node.get("units", {}).get("USD", [])


def _dedupe_latest_filed(rows: list[dict], key) -> dict:
    """Keep the most recently filed fact per period key (captures restatements)."""
    best: dict = {}
    for r in rows:
        k = key(r)
        if k not in best or r.get("filed", "") > best[k].get("filed", ""):
            best[k] = r
    return best


@dataclass
class Period:
    label: str            # e.g. "FY2024" or "LTM 2025-09-30"
    end: date
    values: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)  # metric -> "Concept (form, filed)"


def _annual_duration(facts: dict, concepts: list[str]) -> tuple[dict[date, float], dict[date, str]]:
    """Per fiscal year, take the highest-priority concept that has a value for that year.
    (Issuers switch tags over time, e.g. InterestExpense -> InterestExpenseNonoperating.)"""
    vals: dict[date, float] = {}
    srcs: dict[date, str] = {}
    for concept in concepts:
        rows = [r for r in _usd_facts(facts, concept)
                if r.get("start") and r.get("form", "").startswith("10-K")
                and 350 <= (_parse(r["end"]) - _parse(r["start"])).days <= 380]
        for k, v in _dedupe_latest_filed(rows, lambda r: r["end"]).items():
            d = _parse(k)
            if d not in vals:
                vals[d] = float(v["val"])
                srcs[d] = f"{concept} ({v['form']}, filed {v['filed']})"
    return vals, srcs


def _all_duration(facts: dict, concept: str) -> dict[tuple[date, date], dict]:
    rows = [r for r in _usd_facts(facts, concept) if r.get("start")]
    best = _dedupe_latest_filed(rows, lambda r: (r["start"], r["end"]))
    return {(_parse(s), _parse(e)): v for (s, e), v in best.items()}


def _instant_at(facts: dict, concepts: list[str], when: date) -> tuple[float | None, str | None]:
    for concept in concepts:
        rows = [r for r in _usd_facts(facts, concept) if not r.get("start") and r["end"] == when.isoformat()]
        if rows:
            r = max(rows, key=lambda x: x.get("filed", ""))
            return float(r["val"]), f"{concept} ({r['form']}, filed {r['filed']})"
    return None, None


def _ltm_value(facts: dict, concepts: list[str], fy_end: date, fy_val: float | None):
    """LTM = latest FY + current YTD - prior-year YTD, using the first concept that supports it."""
    for concept in concepts:
        durs = _all_duration(facts, concept)
        ytd = [(s, e, v) for (s, e), v in durs.items()
               if e > fy_end and v.get("form", "").startswith("10-Q") and 80 <= (e - s).days <= 290]
        if not ytd:
            continue
        s, e, cur = max(ytd, key=lambda t: (t[1], (t[1] - t[0]).days))
        length = (e - s).days
        prior = [(ps, pe, pv) for (ps, pe), pv in durs.items()
                 if abs((e - pe).days - 365) <= 10 and abs((pe - ps).days - length) <= 10]
        fy = None
        for (fs, fe), fv in durs.items():
            if fe == fy_end and 350 <= (fe - fs).days <= 380:
                fy = float(fv["val"])
        if fy is None:
            fy = fy_val
        if prior and fy is not None:
            pv = prior[0][2]
            val = fy + float(cur["val"]) - float(pv["val"])
            return e, val, f"{concept} LTM = FY + YTD to {e} ({cur['form']}, filed {cur['filed']}) - prior YTD"
    return None, None, None


def spread_issuer(identifier: str, years: int = 5) -> dict:
    """Pull EDGAR XBRL facts and build an annual + LTM credit spread for one issuer."""
    cik, name = resolve_cik(identifier)
    facts = get_company_facts(cik)

    annual: dict[str, dict[date, float]] = {}
    annual_src: dict[str, dict[date, str]] = {}
    for metric, concepts in DURATION_CONCEPTS.items():
        annual[metric], annual_src[metric] = _annual_duration(facts, concepts)

    fy_ends = sorted({d for m in ("revenue", "operating_income", "cfo") for d in annual[m]})[-years:]
    if not fy_ends:
        raise ValueError(f"{name}: no annual 10-K XBRL data found (foreign filers on IFRS/20-F are not supported).")

    periods: list[Period] = []
    for fe in fy_ends:
        p = Period(label=f"FY{fe.year}" if fe.month >= 6 else f"FY{fe.year - 1}", end=fe)
        for metric in DURATION_CONCEPTS:
            if fe in annual[metric]:
                p.values[metric] = annual[metric][fe]
                p.sources[metric] = annual_src[metric][fe]
        periods.append(p)

    # LTM column if a 10-Q exists after the last fiscal year end
    last_fy = fy_ends[-1]
    ltm = Period(label="", end=last_fy)
    for metric, concepts in DURATION_CONCEPTS.items():
        end, val, src = _ltm_value(facts, concepts, last_fy, annual[metric].get(last_fy))
        if end is not None:
            ltm.end = max(ltm.end, end)
            ltm.values[metric] = val
            ltm.sources[metric] = src
    if ltm.end > last_fy and ltm.values:
        # fill gaps (metric not reported quarterly) with FY value and say so
        for metric in DURATION_CONCEPTS:
            if metric not in ltm.values and last_fy in annual[metric]:
                ltm.values[metric] = annual[metric][last_fy]
                ltm.sources[metric] = annual_src[metric][last_fy] + " [FY value - no quarterly tag]"
        ltm.label = f"LTM {ltm.end.isoformat()}"
        periods.append(ltm)

    for p in periods:
        for metric, concepts in INSTANT_CONCEPTS.items():
            v, s = _instant_at(facts, concepts, p.end)
            if v is not None:
                p.values[metric] = v
                p.sources[metric] = s
        _derive(p)

    gaps = []
    latest = periods[-1].values
    for key, label in [("total_debt", "Total debt (likely company-specific XBRL tags - enter from filing)"),
                       ("ebitda", "EBITDA (operating income or D&A not tagged)"),
                       ("interest_expense", "Interest expense (not separately tagged)"),
                       ("capex", "Capex"), ("revenue", "Revenue")]:
        if latest.get(key) is None:
            gaps.append(label)
    return {"cik": cik, "name": name, "ticker": identifier.upper(), "periods": periods, "gaps": gaps}


def _div(a, b):
    if a is None or b in (None, 0):
        return None
    return a / b


def _derive(p: Period) -> None:
    v = p.values
    # Total debt on one basis for every issuer: carrying value from the balance sheet pieces.
    # The all-in LongTermDebt tag is principal at some issuers (Carnival) and carrying value at others,
    # so it is only the fallback.
    debt, st = None, v.get("short_term_borrowings", 0.0)
    if "lt_debt_noncurrent" in v and "lt_debt_current" in v:
        debt = v["lt_debt_noncurrent"] + v["lt_debt_current"]
        # DebtCurrent already holds commercial paper and other short term borrowings
        if p.sources.get("lt_debt_current", "").startswith("DebtCurrent"):
            st = 0.0
        p.sources["total_debt"] = "carrying value: lt_debt_noncurrent + lt_debt_current" + (" + short_term_borrowings" if st else "")
    elif "lt_debt_total" in v:
        debt = v["lt_debt_total"]
        p.sources["total_debt"] = "all-in LongTermDebt tag, may be principal" + (" + short_term_borrowings" if st else "")
    elif "lt_debt_noncurrent" in v:
        debt = v["lt_debt_noncurrent"]
        p.sources["total_debt"] = "lt_debt_noncurrent only, current portion not tagged" + (" + short_term_borrowings" if st else "")
    if debt is not None:
        debt += st
    v["total_debt"] = debt

    oi, da = v.get("operating_income"), v.get("d_and_a")
    v["ebitda"] = oi + da if oi is not None and da is not None else None
    cfo, capex = v.get("cfo"), v.get("capex")
    v["fcf"] = cfo - capex if cfo is not None and capex is not None else None
    cash = v.get("cash")
    net_debt = debt - cash if debt is not None and cash is not None else None
    v["net_debt"] = net_debt
    v["gross_leverage"] = _div(debt, v["ebitda"])
    v["net_leverage"] = _div(net_debt, v["ebitda"])
    v["interest_coverage"] = _div(v["ebitda"], v.get("interest_expense"))
    v["ebitda_margin"] = _div(v["ebitda"], v.get("revenue"))
    v["fcf_to_debt"] = _div(v["fcf"], debt)
    eq = v.get("equity")
    v["debt_to_capital"] = _div(debt, (debt + eq) if debt is not None and eq is not None else None)


# --------------------------------------------------------------------------- filings
# 8-K items that matter for credit surveillance
CREDIT_8K_ITEMS = {
    "1.01": ("Material definitive agreement", "MEDIUM"),
    "1.02": ("Termination of material agreement", "MEDIUM"),
    "1.03": ("Bankruptcy or receivership", "HIGH"),
    "2.01": ("Acquisition or disposition of assets", "MEDIUM"),
    "2.03": ("New direct financial obligation", "MEDIUM"),
    "2.04": ("Triggering event accelerating debt", "HIGH"),
    "2.05": ("Exit or restructuring costs", "MEDIUM"),
    "2.06": ("Material impairment", "MEDIUM"),
    "3.01": ("Delisting / listing standard failure", "HIGH"),
    "4.01": ("Change in auditor", "MEDIUM"),
    "4.02": ("Non-reliance on prior financials", "HIGH"),
    "5.02": ("Officer / director departure", "LOW"),
}


def recent_filings(cik: str, since: date) -> list[dict]:
    sub = get_submissions(cik)
    r = sub.get("filings", {}).get("recent", {})
    out = []
    for i, form in enumerate(r.get("form", [])):
        fdate = _parse(r["filingDate"][i])
        if fdate <= since:
            continue
        acc = r["accessionNumber"][i]
        doc = r["primaryDocument"][i]
        out.append({
            "form": form,
            "filed": fdate,
            "accession": acc,
            "items": [x.strip() for x in (r.get("items", [""] * (i + 1))[i] or "").split(",") if x.strip()],
            "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{doc}",
        })
    return out
