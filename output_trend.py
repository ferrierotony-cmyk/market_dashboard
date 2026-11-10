"""Economic output trend lines. Pure functions on a dict {FRED id: Series}.

Trend definitions, chosen so they never use future data:
  * CBO potential GDP        the official benchmark; gap = actual / potential - 1.
  * trailing log-linear trend  at each date, fit a straight line to the log of the last N
                              observations and read it at that date. Backward-looking, so the
                              history does not get rewritten when new data arrive, unlike an
                              HP filter whose end point moves. N = 40 quarters for GDP and
                              120 months for industrial production.
Real-time gauges: Atlanta Fed GDPNow (current-quarter nowcast) and the NY Fed Weekly
Economic Index. Labor and breadth: payroll trend, unemployment with the Sahm rule, and the
Chicago Fed activity index.

Sahm rule: the 3-month average unemployment rate minus its lowest value over the previous 12
months. A reading of 0.5 or more has marked the start of every US recession since 1970.
CFNAI 3-month average below -0.7 has historically signaled elevated recession risk.
These are historical regularities, not forecasts.
"""
import numpy as np
import pandas as pd

import pipeline


def trailing_loglinear(s: pd.Series, window: int) -> pd.Series:
    """Causal trend: value at t of the least-squares line through log(s) over the last `window` points."""
    y = np.log(s.astype(float).to_numpy())
    x = np.arange(window, dtype=float)
    xm, sxx = x.mean(), ((x - x.mean()) ** 2).sum()
    out = np.full(len(y), np.nan)
    for t in range(window - 1, len(y)):
        w = y[t - window + 1: t + 1]
        if np.isnan(w).any():
            continue
        slope = ((x - xm) * (w - w.mean())).sum() / sxx
        out[t] = w.mean() + slope * (x[-1] - xm)
    return pd.Series(np.exp(out), index=s.index)


def gdp_block(s: dict) -> pd.DataFrame:
    g = pipeline.regular(s["GDPC1"], "Q")
    out = pd.DataFrame({
        "Real GDP": g,
        "q/q ann %": ((g / g.shift(1)) ** 4 - 1) * 100,
        "y/y %": (g / g.shift(4) - 1) * 100,
    })
    if "GDPPOT" in s:
        pot = s["GDPPOT"].reindex(g.index)
        out["Potential (CBO)"] = pot
        out["Gap to potential %"] = (g / pot - 1) * 100
    trend = trailing_loglinear(g, 40)
    out["Trailing 10y trend"] = trend
    out["Dev from trend %"] = (np.log(g) - np.log(trend)) * 100
    return out


def activity_block(s: dict) -> pd.DataFrame:
    cols = {}
    if "INDPRO" in s:
        ip = pipeline.regular(s["INDPRO"], "M")
        cols["IP y/y %"] = (ip / ip.shift(12) - 1) * 100
        cols["IP 3m ann %"] = ((ip / ip.shift(3)) ** 4 - 1) * 100
        cols["IP trend"] = trailing_loglinear(ip, 120)
        cols["IP dev from trend %"] = (np.log(ip) - np.log(cols["IP trend"])) * 100
    if "PAYEMS" in s:
        p = pipeline.regular(s["PAYEMS"], "M")
        cols["Payrolls 3m avg chg (k)"] = p.diff().rolling(3, min_periods=2).mean()
        cols["Payrolls 12m avg chg (k)"] = p.diff().rolling(12, min_periods=10).mean()
        cols["Payrolls y/y %"] = (p / p.shift(12) - 1) * 100
    if "UNRATE" in s:
        # Tolerates a missing month (the household survey skipped October 2025): the 3-month
        # average needs 2 readings and the 12-month low needs 9.
        u = pipeline.regular(s["UNRATE"], "M")
        u3 = u.rolling(3, min_periods=2).mean()
        cols["Unemployment %"] = u
        cols["Sahm indicator"] = u3 - u3.shift(1).rolling(12, min_periods=9).min()
    if "CFNAI" in s:
        cols["CFNAI 3m avg"] = pipeline.regular(s["CFNAI"], "M").rolling(3, min_periods=2).mean()
    return pd.DataFrame(cols)


def output_table(s: dict) -> pd.DataFrame:
    """Latest reading of every output gauge, with its date and a plain-language read."""
    rows = []

    def add(name, series, fmt="{:,.2f}", note=""):
        series = series.dropna()
        if series.empty:
            return
        rows.append({"gauge": name, "as_of": series.index[-1].date(), "latest": series.iloc[-1], "note": note})

    if "GDPC1" in s:
        g = gdp_block(s)
        add("Real GDP y/y %", g["y/y %"])
        add("Real GDP q/q annualized %", g["q/q ann %"])
        if "Gap to potential %" in g:
            add("Gap to CBO potential %", g["Gap to potential %"], note="negative = slack")
        add("GDP deviation from trailing trend %", g["Dev from trend %"])
    if "GDPNOW" in s:
        add("GDPNow, current quarter q/q ann %", s["GDPNOW"], note="Atlanta Fed nowcast")
    if "WEI" in s:
        add("Weekly Economic Index (y/y GDP %)", s["WEI"], note="NY Fed, weekly")
    a = activity_block(s)
    for col, note in [("IP y/y %", ""), ("IP dev from trend %", ""), ("Payrolls 3m avg chg (k)", "thousands per month"),
                      ("Unemployment %", ""), ("Sahm indicator", "0.5 or more has marked recession starts"),
                      ("CFNAI 3m avg", "below -0.7 = elevated recession risk")]:
        if col in a:
            add(col, a[col], note=note)
    return pd.DataFrame(rows).set_index("gauge") if rows else pd.DataFrame()


def _last(fn):
    try:
        v = fn()
        return float(v) if v is not None and np.isfinite(v) else float("nan")
    except (KeyError, IndexError, ValueError):
        return float("nan")


def output_pulse(s: dict) -> dict:
    """Headline numbers for alerts and dashboards. NaN when a series is unavailable."""
    return {
        "gdp_yoy": _last(lambda: gdp_block(s)["y/y %"].dropna().iloc[-1]),
        "gdp_gap": _last(lambda: gdp_block(s)["Gap to potential %"].dropna().iloc[-1]),
        "gdp_trend_dev": _last(lambda: gdp_block(s)["Dev from trend %"].dropna().iloc[-1]),
        "gdpnow": _last(lambda: s["GDPNOW"].iloc[-1]),
        "wei": _last(lambda: s["WEI"].iloc[-1]),
        "ip_yoy": _last(lambda: activity_block(s)["IP y/y %"].dropna().iloc[-1]),
        "ip_trend_dev": _last(lambda: activity_block(s)["IP dev from trend %"].dropna().iloc[-1]),
        "payroll_3m_avg_k": _last(lambda: activity_block(s)["Payrolls 3m avg chg (k)"].dropna().iloc[-1]),
        "sahm": _last(lambda: activity_block(s)["Sahm indicator"].dropna().iloc[-1]),
        "cfnai_ma3": _last(lambda: activity_block(s)["CFNAI 3m avg"].dropna().iloc[-1]),
    }
