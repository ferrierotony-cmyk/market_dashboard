"""Long test of the Morning Market Dashboard's window score, December 2003 on.

The ICE index behind the live score has only three years of history on FRED since April 2026, so this uses
Moody's Baa yield over the 10 year Treasury in its place. Six of the seven rules run. There is no high yield rule.
The label on a morning uses the prior close. Outcomes run five trading days.

Run: python3 -I long_test.py <data dir> [chart.png]
Data dir: fred_BAA10Y.csv, fred_DGS10.csv, fred_VIXCLS.csv, fred_BAMLC0A0CM.csv, fred_BAMLH0A0HYM2.csv,
          yahoo_MOVE.csv and yahoo_GSPC.csv with date and close columns."""
import sys, os, json
import numpy as np, pandas as pd

D = sys.argv[1]
RULES = [("vix", 18, 25, 1), ("move", 100, 120, 1), ("w1", 3, 8, 1), ("hy_w1", 10, 25, 1),
         ("spx_d1", -0.5, -1.5, -1), ("ust", 5, 10, 1), ("pct1y", 0.5, 0.8, 1)]


def fred(sid):
    d = pd.read_csv(os.path.join(D, "fred_%s.csv" % sid)); d.columns = ["date", "v"]
    d["date"] = pd.to_datetime(d["date"])
    return pd.to_numeric(d.set_index("date")["v"], errors="coerce").dropna()


def yahoo(name):
    d = pd.read_csv(os.path.join(D, "yahoo_%s.csv" % name)); d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")["close"].astype(float)


def features(sp, hy=None):
    ix = sp.index; f = pd.DataFrame(index=ix)
    f["sp"] = sp; f["vix"] = fred("VIXCLS").reindex(ix).ffill(limit=5); f["move"] = yahoo("MOVE").reindex(ix).ffill(limit=5)
    f["w1"] = sp - sp.shift(5)
    if hy is not None:
        h = hy.reindex(ix).ffill(); f["hy_w1"] = h - h.shift(5)
    f["spx_d1"] = yahoo("GSPC").reindex(ix).ffill().pct_change(fill_method=None) * 100
    f["ust"] = (fred("DGS10").reindex(ix).ffill().diff() * 100).abs()
    lo, hi = sp.rolling(252).min(), sp.rolling(252).max(); f["pct1y"] = (sp - lo) / (hi - lo)
    return f


def label(f, need):
    pts = {}
    for m, good, warn, sign in RULES:
        if m in f:
            v = sign * f[m]; p = np.where(v <= sign * good, 2.0, np.where(v <= sign * warn, 1.0, 0.0))
            pts[m] = np.where(f[m].isna(), np.nan, p)
    pts = pd.DataFrame(pts, index=f.index); n = pts.notna().sum(axis=1); ratio = pts.sum(axis=1) / (2 * n)
    ratio[n < need] = np.nan
    return ratio.shift(1)  # a morning only knows the prior close


def episodes(flag, gap=10):
    """Number runs of challenging mornings. A new one starts after more than `gap` trading days without one."""
    out, k, last = np.full(len(flag), -1), 0, -10**6
    for i, c in enumerate(flag):
        if c:
            k += i - last > gap; last = i; out[i] = k
    return out


def interval(groups, fn, seed=11, runs=5000):
    rng = np.random.default_rng(seed)
    z = [fn(np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])) for _ in range(runs)]
    return [round(float(q), 3) for q in np.percentile(z, [2.5, 97.5])]


out = {}
# ---- the two year window, all seven rules, on the ICE index ----
s = features(fred("BAMLC0A0CM") * 100, fred("BAMLH0A0HYM2") * 100); r = label(s, 5)
m = (s.index >= "2024-10-11") & (s.index <= "2026-11-02"); ch = m & (r < 0.5).values
from_day, from_known = s.sp.shift(-5) - s.sp, s.sp.shift(-4) - s.sp.shift(1)
wk = m & (s.w1.shift(1) > 8).values
out["two_year"] = {"mornings": int(m.sum()), "challenging": int(ch.sum()), "episodes": int(len(set(episodes(ch))) - 1),
                   "tighter_from_same_close": int((from_day[ch] < 0).sum()), "tighter_from_known_close": int((from_known[ch] < 0).sum()),
                   "week_over_8bp": int(wk.sum()), "week_over_8bp_tighter": int((from_day[wk] < 0).sum())}

# ---- the long window, six rules, on the Baa spread ----
f = features(fred("BAA10Y") * 100); f["next5"] = f.sp.shift(-5) - f.sp; r = label(f, 6)
keep = (f.index >= "2003-12-01") & r.notna().values; f, r = f[keep], r[keep]
ch = (r < 0.5).values; ep = episodes(ch); x = f.next5.values; ok = ~np.isnan(x)
a, b = x[ch & ok], x[~ch & ok]
grp = [x[(ep == e) & ok] for e in sorted(set(ep)) if e > 0]; grp = [g for g in grp if len(g)]
first = [np.where(ep == e)[0][0] for e in sorted(set(ep)) if e > 0]; fx = x[first]; fx = fx[~np.isnan(fx)]
big = ok & (x > 20)
out["long"] = {
    "start": str(f.index[0].date()), "end": str(f.index[-1].date()), "mornings": int(len(f)), "challenging": int(ch.sum()), "episodes": int(len(set(ep)) - 1),
    "n_outcomes": [len(a), len(b)], "tighter": [int((a < 0).sum()), round(float((a < 0).mean()), 4), round(float((b < 0).mean()), 4)], "tighter_interval": interval(grp, lambda z: (z < 0).mean()),
    "mean_bp": [round(float(a.mean()), 2), round(float(b.mean()), 2)], "mean_interval": interval(grp, np.mean),
    "abs_bp": [round(float(np.abs(a).mean()), 2), round(float(np.abs(b).mean()), 2)], "wider_10": [round(float((a > 10).mean()), 4), round(float((b > 10).mean()), 4)],
    "wider_10_interval": interval(grp, lambda z: (z > 10).mean()), "before_20bp": [int(big.sum()), int((big & ch).sum())], "share_challenging": round(float(ch.mean()), 4),
    "first_of_episode": [len(fx), int((fx < 0).sum())]}
j = pd.DataFrame({"a": fred("BAMLC0A0CM") * 100, "b": fred("BAA10Y") * 100}).dropna()
out["proxy_corr"] = {"levels": round(j.a.corr(j.b), 3), "five_day_changes": round(j.a.diff(5).corr(j.b.diff(5)), 3)}
bins = [("tighter by\nmore than 10", lambda z: z < -10), ("tighter by\n10 or less", lambda z: (z < 0) & (z >= -10)), ("unchanged", lambda z: z == 0),
        ("wider by\n10 or less", lambda z: (z > 0) & (z <= 10)), ("wider by\nmore than 10", lambda z: z > 10)]
out["bins"] = {n.replace("\n", " "): [round(float(q(a).mean()) * 100, 1), round(float(q(b).mean()) * 100, 1)] for n, q in bins}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "long_test_summary.json"), "w"), indent=1)
print(json.dumps(out, indent=1))

if len(sys.argv) > 2:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    have = {q.name for q in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next((q for q in ("Inter", "Segoe UI", "Arial") if q in have), "DejaVu Sans")
    BG, INK, MUTE, GRID, ORANGE, GREY = "#101114", "#F2F0EA", "#A6A49C", "#26272B", "#D95926", "#8C8A82"
    fig, ax = plt.subplots(figsize=(11.3, 6.0), dpi=150, facecolor=BG); ax.set_facecolor(BG)
    k = np.arange(len(bins)); va = [q[0] for q in out["bins"].values()]; vb = [q[1] for q in out["bins"].values()]
    for off, v, c, n in [(-.2, vb, GREY, "All other mornings"), (.2, va, ORANGE, "After a challenging morning")]:
        ax.bar(k + off, v, .37, color=c, label=n)
        for i, y in zip(k, v): ax.text(i + off, y + .8, "%.0f%%" % y, ha="center", va="bottom", color=INK, fontsize=13)
    ax.set_xticks(k, [n for n, _ in bins], color=INK, fontsize=13); ax.set_yticks([]); ax.set_ylim(0, max(va + vb) * 1.2)
    for sp in ("top", "left", "right"): ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#4A4B50"); ax.tick_params(length=0, pad=8)
    ax.set_title("Where the spread was five trading days later, in bp", loc="left", color=INK, fontsize=17, pad=40)
    ax.legend(loc="lower left", bbox_to_anchor=(-.012, 1.0), ncol=2, frameon=False, labelcolor=INK, fontsize=13, handlelength=1, handleheight=1)
    fig.text(.035, .03, "Moody's Baa over the 10 year Treasury, %s to %s. %s challenging mornings and %s others. FRED and Yahoo data." % (
        f.index[0].strftime("%B %Y"), f.index[-1].strftime("%B %Y"), format(len(a), ","), format(len(b), ",")), color=MUTE, fontsize=11)
    fig.subplots_adjust(left=.035, right=.975, top=.80, bottom=.20)
    fig.savefig(sys.argv[2], facecolor=BG)
