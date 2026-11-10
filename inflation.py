"""Consumer inflation tracker. Pure functions on a dict {FRED id: Series}.

Several measures, because no single one is reliable:
  headline and core CPI, headline and core PCE      price indexes, so growth is computed here
  median CPI and 16% trimmed-mean CPI (Cleveland)   strip out the extreme price moves
  sticky CPI (Atlanta Fed)                          the slow-moving components
  breakevens, 5y5y forward, Michigan expectations   what markets and households expect
  gasoline                                          weekly, the fastest-moving price input

Momentum is shown three ways: 1-month annualized (noisy), 3-month annualized (the trend that
matters for the next decision), and year over year (slow, backward-looking). When the 3-month
rate sits well above the year-over-year rate, inflation is accelerating, and the reverse.

Missing series never raise: the affected rows and metrics are simply absent or NaN.
"""
import numpy as np
import pandas as pd

import pipeline

TARGET = 2.0
ACCEL_BAND = 0.3     # percentage points between 3m annualized and y/y before calling a direction


def ann_growth(idx: pd.Series, months: int) -> pd.Series:
    """Annualized percent growth over `months` calendar months of a monthly price index.

    Calendar-aware: a month that was never published is NaN, so growth that would have to
    span it is NaN instead of silently stretching over an extra month.
    """
    idx = pipeline.regular(idx, "M")
    return ((idx / idx.shift(months)) ** (12 / months) - 1) * 100


def yoy(idx: pd.Series) -> pd.Series:
    idx = pipeline.regular(idx, "M")
    return (idx / idx.shift(12) - 1) * 100


def compound_from_monthly_pct(pct_mm: pd.Series, months: int) -> pd.Series:
    """Annualized growth from a series of 1-month percent changes, compounded over `months`."""
    growth = (1 + pipeline.regular(pct_mm, "M") / 100).rolling(months).apply(np.prod, raw=True)
    return (growth ** (12 / months) - 1) * 100


def mean_last(x: pd.Series, n: int, min_obs: int) -> float:
    """Average of the last n calendar months, tolerating a missing month or two."""
    w = pipeline.regular(x, "M").iloc[-n:]
    return float(w.mean()) if w.notna().sum() >= min_obs else float("nan")


def direction(three_m: float, year: float) -> str:
    if np.isnan(three_m) or np.isnan(year):
        return "n/a"
    if three_m > year + ACCEL_BAND:
        return "accelerating"
    if three_m < year - ACCEL_BAND:
        return "decelerating"
    return "steady"


def _measure_rows(s: dict) -> list[dict]:
    rows = []
    for sid, label in [("CPIAUCSL", "Headline CPI"), ("CPILFESL", "Core CPI"), ("PCEPI", "Headline PCE"),
                       ("PCEPILFE", "Core PCE"), ("TRMMEANCPIM094SFRBCLE", "Trimmed-mean CPI")]:
        if sid not in s:
            continue
        x = s[sid]
        m1, m3, m6, y = (ann_growth(x, 1).iloc[-1], ann_growth(x, 3).iloc[-1],
                         ann_growth(x, 6).iloc[-1], yoy(x).iloc[-1])
        rows.append({"measure": label, "as_of": x.index[-1].date(), "1m ann %": m1, "3m ann %": m3,
                     "6m ann %": m6, "y/y %": y, "y/y vs 2% target": y - TARGET, "direction": direction(m3, y)})
    if "MEDCPIM158SFRBCLE" in s:        # already 1m annualized, so average it for longer windows
        x = s["MEDCPIM158SFRBCLE"]
        m3, y = mean_last(x, 3, 2), mean_last(x, 12, 10)
        rows.append({"measure": "Median CPI", "as_of": x.index[-1].date(), "1m ann %": x.iloc[-1], "3m ann %": m3,
                     "6m ann %": mean_last(x, 6, 5), "y/y %": y, "y/y vs 2% target": y - TARGET,
                     "direction": direction(m3, y)})
    if "STICKCPIM157SFRBATL" in s:       # 1m percent change, not annualized
        x = s["STICKCPIM157SFRBATL"]
        r = {k: compound_from_monthly_pct(x, k).iloc[-1] for k in (1, 3, 6, 12)}
        rows.append({"measure": "Sticky CPI", "as_of": x.index[-1].date(), "1m ann %": r[1], "3m ann %": r[3],
                     "6m ann %": r[6], "y/y %": r[12], "y/y vs 2% target": r[12] - TARGET,
                     "direction": direction(r[3], r[12])})
    return rows


def inflation_table(s: dict) -> pd.DataFrame:
    rows = _measure_rows(s)
    return pd.DataFrame(rows).set_index("measure") if rows else pd.DataFrame()


def expectations_table(s: dict) -> pd.DataFrame:
    rows = []
    for sid, label, back in [("T5YIE", "5y breakeven", 21), ("T10YIE", "10y breakeven", 21),
                             ("T5YIFR", "5y5y forward", 21), ("MICH", "Michigan 1y expectation", 1)]:
        if sid not in s:
            continue
        x = s[sid]
        n3 = back * 3
        rows.append({"measure": label, "as_of": x.index[-1].date(), "latest %": x.iloc[-1],
                     "chg vs 1 period/month back": x.iloc[-1] - x.iloc[-1 - back] if len(x) > back else np.nan,
                     "chg vs 3 months back": x.iloc[-1] - x.iloc[-1 - n3] if len(x) > n3 else np.nan})
    if "GASREGW" in s:
        x = s["GASREGW"]
        rows.append({"measure": "Gasoline $/gal", "as_of": x.index[-1].date(), "latest %": x.iloc[-1],
                     "chg vs 1 period/month back": (x.iloc[-1] / x.iloc[-5] - 1) * 100 if len(x) > 5 else np.nan,
                     "chg vs 3 months back": (x.iloc[-1] / x.iloc[-14] - 1) * 100 if len(x) > 14 else np.nan})
    return pd.DataFrame(rows).set_index("measure") if rows else pd.DataFrame()


def inflation_trends(s: dict) -> pd.DataFrame:
    """Monthly time series for charts: year over year and 3-month annualized, by measure."""
    cols = {}
    for sid, label in [("CPIAUCSL", "Headline CPI"), ("CPILFESL", "Core CPI"), ("PCEPILFE", "Core PCE"),
                       ("TRMMEANCPIM094SFRBCLE", "Trimmed-mean CPI")]:
        if sid in s:
            cols[f"{label} y/y"] = yoy(s[sid])
            cols[f"{label} 3m ann"] = ann_growth(s[sid], 3)
    if "MEDCPIM158SFRBCLE" in s:
        med = pipeline.regular(s["MEDCPIM158SFRBCLE"], "M")
        cols["Median CPI 12m avg"] = med.rolling(12, min_periods=10).mean()
        cols["Median CPI 3m avg"] = med.rolling(3, min_periods=2).mean()
    return pd.DataFrame(cols)


def _last(fn):
    try:
        v = fn()
        return float(v) if v is not None and np.isfinite(v) else float("nan")
    except (KeyError, IndexError, ValueError):
        return float("nan")


def inflation_pulse(s: dict) -> dict:
    """Headline numbers for alerts and dashboards. NaN when a series is unavailable."""
    return {
        "cpi_yoy": _last(lambda: yoy(s["CPIAUCSL"]).iloc[-1]),
        "core_cpi_yoy": _last(lambda: yoy(s["CPILFESL"]).iloc[-1]),
        "core_cpi_3m_ann": _last(lambda: ann_growth(s["CPILFESL"], 3).iloc[-1]),
        "core_pce_yoy": _last(lambda: yoy(s["PCEPILFE"]).iloc[-1]),
        "core_pce_3m_ann": _last(lambda: ann_growth(s["PCEPILFE"], 3).iloc[-1]),
        "median_cpi_3m_ann": _last(lambda: mean_last(s["MEDCPIM158SFRBCLE"], 3, 2)),
        "trimmed_mean_3m_ann": _last(lambda: ann_growth(s["TRMMEANCPIM094SFRBCLE"], 3).iloc[-1]),
        "breakeven_5y": _last(lambda: s["T5YIE"].iloc[-1]),
        "breakeven_5y5y": _last(lambda: s["T5YIFR"].iloc[-1]),
        "mich_1y": _last(lambda: s["MICH"].iloc[-1]),
        "gas_yoy_pct": _last(lambda: (s["GASREGW"].iloc[-1] / s["GASREGW"].iloc[-53] - 1) * 100),
    }
