"""Draws the Tender Tracker banner and card from events.csv on the tender-results branch.
Run: python -I mk_tender_banner.py <events.csv> <assets dir>"""
import csv, collections, datetime as dt, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np

BG, ORANGE, GREY = "#0b0b0c", "#f26a1b", "#55555c"
OFFER = {"launch", "early_results", "final_results", "extension", "pricing_terms", "amendment"}
cnt = collections.defaultdict(lambda: [0, 0])
for r in csv.DictReader(open(sys.argv[1], encoding="utf-8")):
    cnt[r["file_date"]][0 if r["kind"] in OFFER else 1] += 1
first, last = (dt.date.fromisoformat(x) for x in (min(cnt), max(cnt)))
days = [d for d in (first + dt.timedelta(n) for n in range((last - first).days + 1)) if d.weekday() < 5]
off = np.array([cnt[str(d)][0] for d in days]); oth = np.array([cnt[str(d)][1] for d in days])
print(first, last, off.sum(), oth.sum(), "weekdays", len(days))
x = np.arange(len(days))
for name, size, top in (("banners", (24, 10.3), 1.35), ("thumbs", (16, 9), 1.6)):
    fig = plt.figure(figsize=size, dpi=100, facecolor=BG); ax = fig.add_axes([.03, 0, .94, 1]); ax.axis("off")
    ax.bar(x, off, .72, color=ORANGE); ax.bar(x, oth, .72, bottom=off, color=GREY)
    ax.set_xlim(-.6, len(days) - .4); ax.set_ylim(0, (off + oth).max() * top)
    fig.savefig("%s/%s/tender.jpg" % (sys.argv[2], name), dpi=100, facecolor=BG, pil_kwargs={"quality": 88}); plt.close(fig)
