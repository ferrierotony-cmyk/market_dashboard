"""Backtest of the Morning Market Dashboard's window score.
Rebuilds the seven rules in config.R from public history, labels every morning, then asks what happened next.
Run: python3 -I backtest.py <research-data dir>"""
import sys, os, csv, json, math, statistics as st
import pandas as pd, numpy as np

D = sys.argv[1]
def fred(sid):
    df = pd.read_csv(os.path.join(D, "fred_%s.csv" % sid)); df.columns = ["date", "v"]
    df["v"] = pd.to_numeric(df["v"], errors="coerce"); df["date"] = pd.to_datetime(df["date"]); return df.set_index("date")["v"]
def yahoo(name):
    df = pd.read_csv(os.path.join(D, "yahoo_%s.csv" % name)); df["date"] = pd.to_datetime(df["date"]); return df.set_index("date")["close"].astype(float)

ig, hy, dgs10, vix = fred("BAMLC0A0CM") * 100, fred("BAMLH0A0HYM2") * 100, fred("DGS10"), fred("VIXCLS")
move, spx = yahoo("MOVE"), yahoo("GSPC")
idx = ig.dropna().index
f = pd.DataFrame(index=idx)
f["vix"] = vix.reindex(idx).ffill()
f["move"] = move.reindex(idx).ffill()
f["ig"] = ig; f["hy"] = hy.reindex(idx).ffill()
f["ig_w1"] = f["ig"] - f["ig"].shift(5)
f["hy_w1"] = f["hy"] - f["hy"].shift(5)
f["spx_d1"] = spx.reindex(idx).ffill().pct_change() * 100
f["ust10_absd1"] = (dgs10.reindex(idx).ffill().diff() * 100).abs()
lo, hi = f["ig"].rolling(252).min(), f["ig"].rolling(252).max()
f["ig_pct1y"] = (f["ig"] - lo) / (hi - lo)

RULES = [("vix", 18, 25, "below"), ("move", 100, 120, "below"), ("ig_w1", 3, 8, "below"), ("hy_w1", 10, 25, "below"),
         ("spx_d1", -0.5, -1.5, "above"), ("ust10_absd1", 5, 10, "below"), ("ig_pct1y", 0.5, 0.8, "below")]
def grade(v, good, warn, d):
    if pd.isna(v): return np.nan
    if d == "below": return 2 if v <= good else 1 if v <= warn else 0
    return 2 if v >= good else 1 if v >= warn else 0
pts = pd.DataFrame({m: f[m].map(lambda v: grade(v, g, w, d)) for m, g, w, d in RULES})
valid = pts.notna().sum(axis=1); ratio = pts.sum(axis=1) / (2 * valid)
f["ratio"] = ratio
f["label"] = np.where(valid < 5, "na", np.where(ratio >= 0.8, "open", np.where(ratio >= 0.5, "selective", "challenging")))
# the morning reading uses yesterday's closes, so shift the label one day forward before matching outcomes
f["label"] = f["label"].shift(1); f["ratio"] = f["ratio"].shift(1)
f["ig_next5"] = f["ig"].shift(-5) - f["ig"]
f["hy_next5"] = f["hy"].shift(-5) - f["hy"]
f["ig_next1"] = f["ig"].shift(-1) - f["ig"]
f = f[f["label"].isin(["open", "selective", "challenging"])]

out = {"start": str(f.index.min().date()), "end": str(f.index.max().date()), "days": int(len(f))}
out["share"] = {k: round(v, 3) for k, v in f["label"].value_counts(normalize=True).items()}
out["ig_next5"] = {}
for lab, g in f.groupby("label"):
    s = g["ig_next5"].dropna()
    out["ig_next5"][lab] = {"n": int(len(s)), "mean_bp": round(float(s.mean()), 2), "median_bp": round(float(s.median()), 2), "share_wider": round(float((s > 0).mean()), 3), "share_wider_5bp": round(float((s > 5).mean()), 3), "p90_bp": round(float(s.quantile(0.9)), 1)}
s = f["ig_next5"].dropna(); out["ig_next5"]["all"] = {"n": int(len(s)), "mean_bp": round(float(s.mean()), 2), "share_wider": round(float((s > 0).mean()), 3), "share_wider_5bp": round(float((s > 5).mean()), 3)}
out["hy_next5"] = {lab: {"mean_bp": round(float(g["hy_next5"].dropna().mean()), 2), "share_wider": round(float((g["hy_next5"].dropna() > 0).mean()), 3)} for lab, g in f.groupby("label")}

# issuance proxy: pricing term sheets on Form FWP, by day, 2023 on
ep = os.path.join(D, "edgar_daily.csv")
if os.path.exists(ep):
    e = pd.read_csv(ep); e["date"] = pd.to_datetime(e["date"]); e = e.set_index("date")
    for c in e.columns: e[c] = pd.to_numeric(e[c], errors="coerce")
    j = f.join(e, how="inner")
    j = j[j.index >= "2023-01-01"]
    out["fwp"] = {"days": int(len(j)), "share_labels": {k: round(v, 3) for k, v in j["label"].value_counts(normalize=True).items()}}
    for col in ["fwp_pricing_term_sheet", "b5_all"]:
        d = {}
        for lab, g in j.groupby("label"):
            s = g[col].dropna(); d[lab] = {"n": int(len(s)), "mean_per_day": round(float(s.mean()), 2), "median": float(s.median()), "share_zero": round(float((s == 0).mean()), 3)}
        s = j[col].dropna(); d["all"] = {"n": int(len(s)), "mean_per_day": round(float(s.mean()), 2), "median": float(s.median())}
        # weekday effect check: Mondays and Fridays are quiet regardless
        d["by_weekday_all"] = {int(k): round(float(v), 2) for k, v in j.groupby(j.index.weekday)[col].mean().items()}
        out[col] = d
    # score ratio vs next day FWP count, rank correlation
    from scipy.stats import spearmanr
    jj = j[["ratio", "fwp_pricing_term_sheet"]].dropna()
    r, p = spearmanr(jj["ratio"], jj["fwp_pricing_term_sheet"]); out["spearman_ratio_vs_fwp"] = {"rho": round(float(r), 3), "p": float(p), "n": int(len(jj))}
    # the worst mornings: lowest 5 percent of ratio
    cut = j["ratio"].quantile(0.05); w = j[j["ratio"] <= cut]
    out["worst5pct"] = {"n": int(len(w)), "ratio_cut": round(float(cut), 3), "fwp_mean": round(float(w["fwp_pricing_term_sheet"].mean()), 2), "ig_next5_mean": round(float(w["ig_next5"].mean()), 2), "share_wider": round(float((w["ig_next5"] > 0).mean()), 3)}
    # same for the best mornings
    cut2 = j["ratio"].quantile(0.95); b = j[j["ratio"] >= cut2]
    out["best5pct"] = {"n": int(len(b)), "ratio_cut": round(float(cut2), 3), "fwp_mean": round(float(b["fwp_pricing_term_sheet"].mean()), 2), "ig_next5_mean": round(float(b["ig_next5"].mean()), 2), "share_wider": round(float((b["ig_next5"] > 0).mean()), 3)}
    j.to_csv(os.path.join(D, "backtest_daily.csv"))
f.to_csv(os.path.join(D, "backtest_full.csv"))
json.dump(out, open(os.path.join(D, "backtest_summary.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
