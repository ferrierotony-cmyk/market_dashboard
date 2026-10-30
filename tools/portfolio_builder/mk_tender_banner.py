import csv, collections, datetime as dt, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
BG="#0b0b0c"; AMB="#f26a1b"; GREY="#8a8a92"; LIGHT="#3a3a40"
OFFER={"launch","early_results","final_results","extension","pricing_terms","amendment"}
rows=list(csv.DictReader(open('tr_r7/events.csv')))
cnt=collections.defaultdict(lambda:[0,0])
for r in rows:
    d=r['file_date']; k=0 if r['kind'] in OFFER else 1
    cnt[d][k]+=1
start=dt.date(2026,7,29); end=dt.date(2026,10,27)
days=[start+dt.timedelta(n) for n in range((end-start).days+1)]
off=np.array([cnt[str(d)][0] for d in days]); oth=np.array([cnt[str(d)][1] for d in days])
fig=plt.figure(figsize=(24,10.3),dpi=100,facecolor=BG); ax=fig.add_axes([0,0,1,1]); ax.set_facecolor(BG); ax.axis('off')
x=np.arange(len(days))
ax.bar(x,oth,0.7,color=LIGHT); ax.bar(x,off,0.7,bottom=oth,color=AMB)
ax.set_xlim(-1,len(days)); ax.set_ylim(0,(off+oth).max()*1.4)

fig.savefig('wt_pl/site_extra/portfolio/assets/banners/tender.jpg',dpi=100,facecolor=BG); print(off.sum(),oth.sum())
# 16:9 thumb for the project card
fig=plt.figure(figsize=(16,9),dpi=100,facecolor=BG); ax=fig.add_axes([0.02,0,0.96,1]); ax.set_facecolor(BG); ax.axis('off')
ax.bar(x,oth,0.7,color=LIGHT); ax.bar(x,off,0.7,bottom=oth,color=AMB); ax.set_xlim(-1,len(days)); ax.set_ylim(0,(off+oth).max()*1.9)
fig.savefig('wt_pl/site_extra/portfolio/assets/thumbs/tender.jpg',dpi=100,facecolor=BG)
