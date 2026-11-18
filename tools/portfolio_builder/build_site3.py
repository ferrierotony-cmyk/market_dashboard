"""Builds the portfolio into OUT (which already holds assets/). Slate and ivory with one clay accent.
Styling lives in styles/tokens.css and styles/site.css. This file writes no style attributes and no colours."""
import os, sys, html

OUT = sys.argv[1]
EMAIL = "ferrierotony@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/anthony-ferriero"
GITHUB = "https://github.com/ferrierotony-cmyk"
REPO = "https://github.com/ferrierotony-cmyk/market_dashboard"
TENDER_CODE = "https://github.com/ferrierotony-cmyk/market_dashboard/tree/tender-lab/tender"
LAB_CODE = "https://github.com/ferrierotony-cmyk/market_dashboard/tree/fed-liquidity-lab"

import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "psky"))
from widgets import explorer_html, POWER_HTML, day_html
from cine import split, page_head, fp, focal_css
import cine as _cine
_cine.AI_DIR = OUT

STYLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles")
TOKENS_CSS = open(os.path.join(STYLES, "tokens.css"), encoding="utf-8").read()
SITE_CSS = open(os.path.join(STYLES, "site.css"), encoding="utf-8").read()
# Browser chrome colour for the theme-color meta tag. Mirrors --color-slate-050 and --color-slate-950 in tokens.css.
THEME_LIGHT, THEME_DARK = "#faf9f5", "#141413"

NAV = [("index.html", "Home"), ("projects.html", "Projects"), ("experience.html", "Experience"), ("leadership.html", "Leadership"), ("education.html", "Education"), ("contact.html", "Contact")]

HEAD_FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
              '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500&display=swap">')
JS = """(function(){var tb=document.getElementById('theme-btn');if(tb){var root=document.documentElement;function sync(){var d=root.getAttribute('data-theme')==='dark';tb.setAttribute('aria-pressed',d?'true':'false');tb.setAttribute('aria-label',d?'Switch to light mode':'Switch to dark mode');var m=document.querySelector('meta[name=theme-color]');if(m)m.setAttribute('content',d?'%s':'%s');}
sync();tb.addEventListener('click',function(){var n=root.getAttribute('data-theme')==='dark'?'light':'dark';root.setAttribute('data-theme',n);try{localStorage.setItem('af-theme',n);}catch(e){}sync();});}})();
(function(){var b=document.getElementById('menu-btn'),n=document.getElementById('nav');if(b&&n){b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o?'true':'false');});}})();
(function(){var t=document.getElementById('tape');if(!t)return;
fetch('https://ferrierotony-cmyk.github.io/market_dashboard/market_snapshot.json',{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(s){
function find(o,keys){if(!o)return null;var ks=Object.keys(o);for(var i=0;i<keys.length;i++){for(var j=0;j<ks.length;j++){if(ks[j].toUpperCase().indexOf(keys[i].toUpperCase())>=0)return o[ks[j]];}}return null;}
function num(x,d,suf){return (x==null||isNaN(x))?null:(Number(x).toFixed(d)+(suf||''));}
var items=[];
if(s.window){var w=String(s.window);var cls=/open/i.test(w)?'good':(/closed|shut/i.test(w)?'bad':'warn');items.push(['New issue window',w,cls,'my score']);}
if(s.health&&s.health.score!=null){items.push(['Market health',s.health.score,'',s.health.label||'']);}
var f=s.fred||{},y=s.yahoo||{};
var r10=find(f,['DGS10','10Y']);if(r10&&r10.last!=null)items.push(['UST 10Y',num(r10.last,2,'%%'),'',r10.d1!=null?('1d '+(r10.d1>=0?'+':'')+num(r10.d1*100,0,' bp')):'']);
var ig=find(f,['BAMLC0A0CM','IG OAS','US IG']);if(ig&&ig.last!=null)items.push(['IG OAS',num(ig.last,0,' bp'),'',ig.w1!=null?('1w '+(ig.w1>=0?'+':'')+num(ig.w1,0,' bp')):'']);
var hy=find(f,['BAMLH0A0HYM2','HY OAS','US HY']);if(hy&&hy.last!=null)items.push(['HY OAS',num(hy.last,0,' bp'),'',hy.w1!=null?('1w '+(hy.w1>=0?'+':'')+num(hy.w1,0,' bp')):'']);
var vix=find(y,['^VIX','VIX']);if(vix&&vix.last!=null)items.push(['VIX',num(vix.last,1),'',vix.d1_pct!=null?('1d '+(vix.d1_pct>=0?'+':'')+num(vix.d1_pct,1,'%%')):'']);
var mv=find(y,['MOVE']);if(mv&&mv.last!=null)items.push(['MOVE',num(mv.last,0),'',mv.d1_pct!=null?('1d '+(mv.d1_pct>=0?'+':'')+num(mv.d1_pct,1,'%%')):'']);
if(items.length<3)return;
document.getElementById('tape-ul').innerHTML=items.map(function(i){return '<li>'+i[0]+'<b class="'+i[2]+'">'+i[1]+'</b><small>'+i[3]+'</small></li>';}).join('');
document.getElementById('tape-when').textContent=s.built_at?('built '+String(s.built_at).slice(0,16)):'';t.classList.add('on');}).catch(function(){});})();
""" % (THEME_DARK, THEME_LIGHT)


def e(s):
    return html.escape(s, quote=True)


def shell(fname, title, desc, main):
    nav = "".join('<li><a href="%s"%s>%s</a></li>' % (f, ' aria-current="page"' if f == fname else "", l) for f, l in NAV)
    pageurl = "" if fname == "index.html" else fname
    full_title = "Anthony Ferriero" if fname == "index.html" else "%s | Anthony Ferriero" % title
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="{THEME_LIGHT}">
<script>(function(){{var t=null;try{{t=localStorage.getItem('af-theme');}}catch(e){{}}if(t!=='dark'&&t!=='light'){{t=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}}document.documentElement.setAttribute('data-theme',t);var m=document.querySelector('meta[name=theme-color]');if(m)m.setAttribute('content',t==='dark'?'{THEME_DARK}':'{THEME_LIGHT}');}})();</script>
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://anthonyferriero.vercel.app/{pageurl}">
<meta property="og:image" content="https://anthonyferriero.vercel.app/assets/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(full_title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="https://anthonyferriero.vercel.app/assets/og-card.png">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="canonical" href="https://anthonyferriero.vercel.app/{pageurl}">
{HEAD_FONTS}
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="style.css">
<script>document.documentElement.classList.add('js')</script>
</head>
<body class="{'home' if fname == 'index.html' else 'inner'}">
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap bar">
  <a class="brand" href="index.html">AF<i>.</i></a>
  <ul class="nav" id="nav">{nav}</ul>
  <div class="bar-tools">
  <button class="menu-btn" id="menu-btn" type="button" aria-expanded="false" aria-controls="nav">Menu</button>
  <button class="theme-btn" id="theme-btn" type="button" aria-label="Switch to dark mode" aria-pressed="false" title="Light or dark">
    <svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    <svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
  </button>
  </div>
</div></header>
<main id="main">
{main}
</main>
<footer class="site-foot"><div class="wrap">
  <div class="row"><span>&copy; 2026 Anthony Ferriero &middot; Lowell, MA</span><span><a href="contact.html">Contact</a> &nbsp;&middot;&nbsp; <a href="{LINKEDIN}" rel="noopener">LinkedIn</a> &nbsp;&middot;&nbsp; <a href="{GITHUB}" rel="noopener">GitHub</a></span></div>
  <p>This is a personal portfolio. The research figures are preliminary. Nothing here is investment advice, and none of the material comes from an employer.</p>
</div></footer>
<script>{JS}</script>
</body>
</html>
"""


def P(*paras):
    return "".join("<p>%s</p>" % p for p in paras)


def photos(items, extra=""):
    out = '<ul class="photos%s">' % extra
    for f, cap, cls in items:
        out += '<li class="%s"><figure><a href="assets/photos/%s.jpg"><img src="assets/photos/%s.jpg" alt="%s" loading="lazy"%s></a><figcaption>%s</figcaption></figure></li>' % (cls, f, f, e(cap), ppos(f), e(cap))
    return out + "</ul>"


def statement(photo, big, cap, pos="center 75%", sub="", dark=False, chips=()):
    """A rounded statement panel on the centre axis. Shows an AI generated image beside the line only if one exists in assets/ai."""
    fig = ""
    if photo and os.path.exists(os.path.join(OUT, photo)):
        pc = fp(pos)
        fig = ('<figure><img src="%s" alt=""%s loading="lazy"><figcaption>AI generated image, not a photo of the real place.</figcaption></figure>' % (photo, ' class="%s"' % pc if pc else ""))
    subh = '<p class="sub">%s</p>' % e(sub) if sub else ""
    if chips:
        subh += '<ul class="chips">' + "".join("<li><b>%s</b><span>%s</span></li>" % (e(a), e(b)) for a, b in chips) + "</ul>"
    return ('<section class="statement%s" aria-label="%s"><div class="wrap"><div class="statement-panel%s"><div><p class="big">%s</p>%s</div>%s</div></div></section>'
            % (" dark" if dark else "", e(cap), " has-fig" if fig else "", e(big), subh, fig))


def pills(items):
    return '<ul class="pills">' + "".join("<li>%s</li>" % e(i) for i in items) + "</ul>"


def bul(items):
    return '<ul class="bul">' + "".join("<li>%s</li>" % i for i in items) + "</ul>"


STORY_KEYS = ("The question", "Data and method", "What I found", "What it means")


def story(q, m, f, w):
    """The four lines a recruiter reads first: question, data and method, finding, and what it means for the market."""
    return '<dl class="story">' + "".join('<div><dt>%s</dt><dd>%s</dd></div>' % (k, e(v)) for k, v in zip(STORY_KEYS, (q, m, f, w))) + "</dl>"


CASES = [
    ("media.html", "Project", "Media DCF models and credit comps", "Five media companies valued on a single template and then compared as credits on leverage, coverage, equity cushion and spread.", ("6.9x", "Skydance net leverage, against a 3.0x target that cash flow alone does not reach")),
    ("research.html", "Project", "Green bond pricing", "A study of whether green bonds price tighter at new issue than conventional bonds from the same issuer, based on 153 matched pairs.", ("2.4 bps", "average gap at new issue, which is not statistically significant")),
    ("tender.html", "Project", "Tender Tracker", "A daily tracker of bond tender and exchange offers that reads SEC filings and newswires and records the terms and caps of each offer.", ("9 in 10", "offer types and dates read correctly on filings the rules had not seen")),
    ("dashboard.html", "Project", "Morning Market Dashboard", "A daily score for whether the new issue window is open, built from the inputs a syndicate desk reviews before a launch.", ("6 inputs", "VIX, MOVE, IG and HY spreads, futures, spread range")),
    ("lab.html", "Project", "Fed Liquidity Lab", "A test of whether the Fed's net liquidity is a useful signal for reducing risk, run on public data against buy and hold.", ("6.0%", "a year for the rules, against 8.1% for buy and hold")),
    ("finsight.html", "Role", "Finsight", "I covered order books, pricing from initial talk to final terms, volume against estimates and liability management on 15 to 20 new deals a day, from December 2025 to September 2026.", ("25+", "liability management deals for which I wrote the headlines")),
    ("ccr.html", "Role", "Commonwealth Capital Research", "I have written the rates and credit section of a newsletter for 200 subscribers since February 2024.", None),
    ("bloomberg.html", "Role", "Bloomberg at UMass Lowell", "I train students across 10 classes as a Terminal Assistant and captain the UML team in the Bloomberg Global Trading Challenge.", ("$1M", "virtual book, long only, scored against the WLS index")),
    ("valuation.html", "Competition", "2026 Valuation Challenge", "The discount rate, DCF and LBO for a contractor with $132MM of revenue that was being sold to an ESOP. I was responsible for the cost of capital.", ("16.8%", "cost of capital I built and defended")),
    ("finance-society.html", "Leadership", "UML Finance Society", "I am president of a student finance club with 500 members.", None),
    ("sales-team.html", "Leadership", "Intercollegiate Sales Team", "I captain a team that placed in the top four at a national competition.", None),
    ("consulting.html", "Project", "Mill City Consulting", "Research and due diligence for a duckpin bowling alley that has operated since 1931.", None),
    ("education.html", "Education", "UMass Lowell", "A degree in Business Administration with concentrations in finance and marketing, expected in May 2027.", None),
    ("skills.html", "Skills", "Tools and certifications", "Bloomberg, R, Stata and Excel, along with the AI tools I use.", None),
]
order = [c[0] for c in CASES] + ["contact.html"]
order[order.index("media.html") + 1:order.index("media.html") + 1] = ["dcf.html", "dcf-nflx.html", "dcf-dis.html", "dcf-cmcsa.html", "dcf-foxa.html"]
label_of = {c[0]: c[2] for c in CASES}
label_of["contact.html"] = "Contact"
label_of.update({"dcf.html": "Skydance DCF", "dcf-nflx.html": "Netflix DCF", "dcf-dis.html": "Disney DCF", "dcf-cmcsa.html": "Comcast DCF", "dcf-foxa.html": "Fox DCF"})


def nxt(f):
    if f not in order:
        return "index.html#case-files", "All case files"
    i = order.index(f)
    n = order[(i + 1) % len(order)]
    return n, label_of[n]


def case_page(fname, title, desc, kind, h1, meta, lede, sections, banner=None):
    secs = "".join(f'<section class="section"{" id=\"figures\"" if label == "Figures" else ""}><div class="wrap"><h2>{e(h2)}</h2>{body}</div></section>\n' for label, h2, body in sections)
    nf, nl = nxt(fname)
    crumb = '<p class="crumb"><a href="index.html#case-files">&larr; All case files</a></p>'
    if banner:
        src = banner[0] if "/" in banner[0] else "assets/photos/%s.jpg" % banner[0]
        pos = banner[2] if len(banner) > 2 else (PHOTO_POS.get(src.split("/")[-1].replace(".jpg", ""), "center 30%") if "/photos/" in src else "center center")
        head = page_head(crumb, h1, meta, lede, src, banner[1], pos)
    else:
        head = page_head(crumb, h1, meta, lede)
    main = f"""{head}
{secs}<section class="section"><div class="wrap next"><a href="index.html#case-files">&larr; All case files</a><a href="{nf}">Next: {e(nl)} &rarr;</a></div></section>"""
    open(os.path.join(OUT, fname), "w", encoding="utf-8").write(shell(fname, title, desc, main))


# ---------- index ----------
board_rows = [
    ("6.9x", "Skydance net leverage in my DCF", "the thinnest equity cushion of the five credits I modeled"),
    ("2.4 bps", "New issue discount I measured on green bonds", "153 matched pairs with a p value of 0.30, so not statistically significant"),
    ("663", "Green bonds in my dataset", "cleaned from 1,226 tracker rows, 40 countries"),
    ("15 to 20", "New bond deals a day I collected order books on", "from 30+ IG and HY syndicate desks at Finsight"),
    ("25+", "Liability management deals I wrote headlines for", "tenders, exchanges and consents"),
    ("9 in 10", "Tender Tracker offer types and dates read correctly", "on filings the rules had never seen"),
]
board = '<div class="board"><div class="board-head"><span>Anthony Ferriero &middot; key numbers</span><b>updated Oct 2026</b></div><ul>' + \
    "".join('<li><div><span>%s</span><small>%s</small></div><b>%s</b></li>' % (e(l), e(s), e(n)) for n, l, s in board_rows) + "</ul></div>"

THUMBS = {
    "research.html": "assets/thumbs/research.jpg", "tender.html": "assets/thumbs/tender.jpg", "dashboard.html": "assets/thumbs/dashboard.jpg", "lab.html": "assets/thumbs/lab.jpg",
    "media.html": "assets/thumbs/media.jpg", 
    "valuation.html": "assets/thumbs/valuation.jpg",
    
    "skills.html": "assets/thumbs/skills.jpg",
}


PHOTO_POS = {
    "nyse-stage": "center 68%", "nyse-seated": "center 55%", "nyse-podium": "center 22%", "nyse-podium-side": "center 22%",
    "ccr-elward": "center 38%", "careers-stairs": "center 28%", "class-team": "center 36%", "mill-city": "22% 30%", "fs-group": "right 22%", "guest-speaker": "center 20%", "fs-lunch": "center 30%", "resume-recharge-1": "center 45%", "resume-recharge-2": "center 48%", "fs-social": "center 35%", "babylon-talk": "center 40%", "class-presenting": "center 30%",
    "babylon-podium": "center 22%", "babylon-panel": "center 40%", "club-fair": "center 30%", "sales-award": "center 28%",
    "sales-certificates": "center 45%", "sales-comp-day": "center 40%", "fintech-rooftop": "center 45%", "fintech-rooftop-2": "center 40%",
    "fintech-career-summit": "center 45%",
}
def ppos(src):
    k = src.split("/")[-1].replace(".jpg", "")
    return ' class="%s"' % fp(PHOTO_POS[k]) if k in PHOTO_POS else ""

def card_html(f, kind, t, d, num):
    numh = '<span class="num">%s<small>%s</small></span>' % (e(num[0]), e(num[1])) if num else ""
    th = '<span class="thumb"><img src="%s" alt="" loading="lazy"%s></span>' % (THUMBS[f], ppos(THUMBS[f])) if f in THUMBS else ""
    return '<li><a class="card" href="%s">%s<span class="card-body"><b>%s</b><em>%s</em>%s</span></a></li>' % (f, th, e(t), e(d), numh)


def card_group(kinds):
    return '<ul class="cards">' + "".join(card_html(*c) for c in CASES if c[1] in kinds) + "</ul>"


cards = ""
for label, kinds in [("Roles", ("Role",)), ("Projects", ("Project",)), ("Competitions", ("Competition",)), ("Leadership", ("Leadership",)), ("Education and skills", ("Education", "Skills"))]:
    cards += '<h3 class="group">%s</h3>' % label + card_group(kinds)

timeline = [
    ("Nov 2026", "Fed Liquidity Lab", "A weekly tracker of the Fed's balance sheet, inflation and output, with trading rules tested against buy and hold. The rules underperformed, and I published the result as it came out.", "lab.html"),
    ("Oct 2026", "Media DCF models and credit comps", "DCF models of Skydance, Netflix, Disney, Comcast and Fox built on one template from SEC filings, followed by a credit comparison covering leverage, coverage, equity cushion, spreads and Skydance's path to its 3.0 times leverage target.", "media.html"),
    ("Oct 2026 to now", "Tender Tracker", "A daily tracker of bond tender and exchange offers built from SEC filings and newswires, with its error rates published.", "tender.html"),
    ("Oct 2026 to now", "Captain, Bloomberg Global Trading Challenge", "I captain the UML team in the fall 2026 round. Each team manages one million virtual dollars in a long only book that is scored against the WLS index. Our book opened on October 12.", "bloomberg.html"),
    ("Sep 2026 to now", "Bloomberg Terminal Assistant, UMass Lowell", "I train students across 10 classes and pull data for faculty research.", "bloomberg.html"),
    ("Sep to Oct 2026", "2026 Valuation Challenge", "I built the discount rate, DCF, LBO and public comparables for a Gulf Coast contractor with $132MM of revenue. The team submitted on October 19.", "valuation.html"),
    ("Jun 2026 to now", "Morning Market Dashboard", "A dashboard built in R that scores whether the new issue window is open. The public version runs on free data.", "dashboard.html"),
    ("May 2026 to now", "Fixed Income Research Analyst, UMass Lowell", "Research on green bond pricing with a faculty supervisor. The preliminary results are published on this site.", "research.html"),
    ("Apr 2026 to now", "President, UML Finance Society", "Membership has grown by 200+ to over 500, and the club has run six or more events and trips this year.", "finance-society.html"),
    ("Feb to Apr 2026", "Bloomberg Global Trading Challenge, spring round", "I was an analyst on the UML team, working on research, position sizing and execution in the terminal.", "bloomberg.html"),
    ("Dec 2025 to Sep 2026", "Debt Capital Markets Analyst Intern, Finsight", "I covered new issuance, pricing and spreads, along with 25+ liability management deals. I worked on high yield in the spring and investment grade in the summer.", "finsight.html"),
    ("Nov 2025 to now", "Captain, UML Intercollegiate Sales Team", "The team placed in the top four at the Love's Travel Stops national sales competition.", "sales-team.html"),
    ("Feb 2024 to now", "Research Analyst, Commonwealth Capital Research", "I write the rates and credit section of a newsletter for 200 subscribers and co-wrote a report on the SpaceX IPO.", "ccr.html"),
]
tl = '<ol class="tl">' + "".join('<li><span class="when">%s</span><b><a href="%s">%s</a></b><p>%s</p></li>' % (e(w), f, e(t), e(d)) for w, t, d, f in timeline) + "</ol>"

def mosaic(items):
    return '<ul class="mosaic">' + "".join('<li class="%s"><a href="%s"><img src="assets/photos/%s.jpg" alt="%s" loading="lazy"%s><span>%s</span></a></li>' % (cls, href, f, e(cap), ppos(f), e(cap)) for f, cap, cls, href in items) + "</ul>"


HOME_PHOTOS = mosaic([
    ("nyse-stage", "On stage at the NYSE after the ICE Fixed Income Forum, October 21, 2026.", "big", "finsight.html"),
    ("fintech-rooftop", "The Finance Society on the roof of the Boston Fed, Boston Fintech Week.", "", "finance-society.html"),
    ("babylon-podium", "Opening From Gold to Tokens with Professor Ravi Jain, September 21.", "tall", "finance-society.html"),
    ("sales-award", "Fourth in Speed Sell at the Challenger Sales Institute invitational.", "", "sales-team.html"),
    ("mill-city", "The Mill City Consulting team.", "", "consulting.html"),
    ("ccr-elward", "With Nick Elward of Natixis after the CCR fireside chat.", "", "ccr.html"),
    ("club-fair", "The Finance Society table at the involvement fair.", "", "finance-society.html"),
    ("fintech-career-summit", "Crack the Fintech Career Code, the student panel at the Boston Fed.", "", "finance-society.html"),
    ("fs-group", "The Finance Society at an event by the water.", "wide", "finance-society.html"),
    ("fs-social", "Members at a Finance Society event.", "wide", "finance-society.html"),
    ("guest-speaker", "A guest speaker session with Bob Landry of H-E-B.", "wide", "finance-society.html"),
    ("fs-lunch", "At a Finance Society event.", "", "finance-society.html"),
    ("resume-recharge-1", "Resume Recharge.", "", "finance-society.html"),
])
index_main = f"""<section class="hero" id="top"><div class="wrap hero-grid">
  <div class="hero-text">
    <h1>{split("Anthony Ferriero")}</h1>
    <p class="kick">I am seeking a 2027 analyst position in fixed income, in credit research, syndicate or debt capital markets.</p>
    <p class="tag">I spent nine months on a primary bond desk at Finsight, where I collected order books on 15 to 20 deals a day. Since then I have built five DCF models with a credit comparison, a green bond pricing study, a tender offer tracker and a score for the new issue window. Each project sets out its assumptions and its limitations.</p>
    <div class="hero-cta">
      <a class="btn primary" href="#case-files">See the case files <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
      <a class="btn outline" href="contact.html">Get in touch</a>
    </div>
    <div class="contact-row">
      <a href="mailto:{EMAIL}">{EMAIL}</a>
      <a href="{LINKEDIN}" rel="noopener">LinkedIn</a>
      <a href="{GITHUB}" rel="noopener">GitHub</a>
    </div>
  </div>
  <figure class="hero-portrait"><img src="assets/headshot.jpg" width="720" height="720" alt="Anthony Ferriero" fetchpriority="high"><figcaption>Anthony Ferriero. UMass Lowell, class of 2027.</figcaption></figure>
</div></section>
<section class="section" id="about"><div class="wrap two">
  <div>
    <h2>Manning School of Business, class of 2027</h2>
    <p>I am a senior at UMass Lowell studying finance and marketing, with a minor in quantitative economics. My GPA is 3.6.</p>
    <p>From December 2025 to September 2026 I was a debt capital markets analyst intern at Finsight, where I collected order book updates on 15 to 20 new bond deals a day. I now train students on the Bloomberg Terminal, lead the Finance Society and conduct research on green bond pricing. I also write the rates and credit section of a student research newsletter.</p>
  </div>
  <div>
    <h2>At Finsight, and on my own</h2>
    <p>At Finsight I covered order books and allocations, the move from price talk to final pricing, volume against Street estimates, attrition and new issue concession. I also wrote headlines on 25 or more liability management deals.</p>
    <p>Independently, I built five DCF models and a credit comparison of the media companies, a study of whether green bonds price tighter at issue, a daily tracker of tender and exchange offers drawn from SEC filings and newswires, and a score for whether the new issue window is open.</p>
  </div>
</div></section>
<div class="wrap data-block">{board}
<div class="tape" id="tape"><div class="tape-head"><span>Live from my dashboard &middot; free data that can be 15 minutes delayed</span><b id="tape-when"></b></div><ul id="tape-ul"></ul><div class="tape-foot">The window score and the levels come from the <a href="dashboard.html">Morning Market Dashboard</a>, which is rebuilt on weekdays. It is not intended as a trading tool.</div></div></div>
{statement("assets/ai/home-price.jpg", "I like working out why a bond prices where it does.", "Why I want to work in credit", "center", "The answer depends on leverage, coverage, the equity beneath the bonds and where comparable paper has priced, and the market tests that answer quickly.")}
<section class="section" id="desks"><div class="wrap">
  <h2>How the work applies across four desks</h2>
  <dl class="story">
    <div><dt>Fixed income</dt><dd>A study of whether green bonds price tighter than conventional bonds from the same issuer, together with the rates section of a research newsletter. <a href="research.html">Green bond pricing</a> &middot; <a href="ccr.html">Commonwealth Capital Research</a></dd></div>
    <div><dt>Credit research</dt><dd>Five media companies valued on one template and compared on leverage, coverage and the equity cushion beneath the bonds. <a href="media.html">Media DCF models and credit comps</a> &middot; <a href="dcf.html">Skydance</a></dd></div>
    <div><dt>Syndicate</dt><dd>Nine months spent collecting order books from 30 or more desks on 15 to 20 deals a day, and a daily score for whether the new issue window is open. <a href="finsight.html">Finsight</a> &middot; <a href="dashboard.html">Morning Market Dashboard</a></dd></div>
    <div><dt>Debt capital markets</dt><dd>Coverage of new issues from initial talk to final pricing, headlines on 25 or more liability management deals, and a tracker of bond tender and exchange offers. <a href="finsight.html">Finsight</a> &middot; <a href="tender.html">Tender Tracker</a></dd></div>
  </dl>
</div></section>
<section class="section" id="case-files"><div class="wrap">
  <h2>Projects, roles and results</h2>
  {cards}
</div></section>
{statement("assets/ai/home-club.jpg", "The Finance Society now has 500 members.", "The Finance Society", "center", "That is 200 more than when I became president in April 2026.", True, (("500+", "members"), ("9", "person e-board"), ("6", "events in six weeks")))}
<section class="section"><div class="wrap">
  <h2>Recent events</h2>
  {HOME_PHOTOS}
</div></section>
<section class="section"><div class="wrap">
  <h2>Experience, most recent first</h2>
  {tl}
</div></section>"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(shell("index.html", "Anthony Ferriero",
    "Finance student at UMass Lowell seeking a 2027 analyst position in fixed income, in credit research, syndicate or debt capital markets. Primary market experience at Finsight, five DCF models with a credit comparison, green bond pricing research, a bond tender tracker and a new issue window dashboard.", index_main))

# ---------- research ----------
FIGS = [
    ("fig1_universe_by_year.png", "The dataset", "663 green bonds by issue year, with the 153 in the pricing sample in grey. Issuance peaked in 2021 and 2022.", False),
    ("fig3_credit_beta.png", "Why the credit adjustment matters", "The gap between each pair moves almost one for one with the change in credit spreads between the two issue dates. The slope is 0.97. Without this step, any greenium estimate mostly measures the credit cycle.", False),
    ("fig2_adjustment_steps.png", "Three steps from coupons to a greenium", "The raw coupon gap has a standard deviation of 104 bps. Taking out Treasury rates at each bond's own tenor cuts it to 64. Taking out credit, rates and tenor together cuts it to 27 and leaves a mean of 2.4 bps tighter.", True),
    ("fig4_specification_chart.png", "The estimate across 24 specifications", "Versions that keep every pair land between 2 and 4 bps tighter. Subsamples scatter more: non US issuers sit at 7.5 tighter and the 10 same week pairs at 3.7 wider. The sample splits are exploratory.", True),
    ("fig5_groups.png", "By sector and rating", "Financials show 5.1 bps tighter, p 0.20, on 36 pairs. Across the seven sector and rating groups none is significant, and after correcting for seven tests the smallest p value is 0.81. In the earlier version the financials result appeared meaningful, and it no longer does.", False),
    ("fig6_greenium_by_year.png", "By issue year", "No year departs from the pooled estimate. The confidence intervals are wide because no year holds more than 34 pairs.", False),
    ("fig7_events.png", "Seven dated events", "None of them, from the EU disclosure rules to the DeepSeek shock, shifts the greenium detectably. The smallest raw p value is 0.08 and none survives correction. These tests can only see moves of roughly 27 bps.", True),
    ("fig8_market_backdrop.png", "The market behind the sample", "The 10 year Treasury yield and the credit index used, Moody's Baa over the 30 year Treasury, with each pair's issue date marked as a tick. The pairs cluster from 2020 to 2023.", False),
    ("fig9_power.png", "How many pairs it would take", "With 153 pairs the smallest gap the test can reliably detect is 6.6 bps. Detecting 5 bps would take about 265 pairs and 3 bps about 735. The sample can reject a gap of 8 bps or more. It cannot distinguish 2 bps from zero.", False),
    ("fig10_permutation.png", "A test that does not depend on the model's assumptions", "Flipping the sign of each issuer's gaps at random 20,000 times produces a mean at least as large as 2.4 bps about 31 percent of the time.", False),
    ("fig12_distribution_noise.png", "The 153 gaps, and why the date gap matters", "The mean is 2.4 bps tighter and the median 4.3. Noise grows with the time between the two issue dates, from 20 bps within a week to 35 beyond two years.", False),
    ("fig11_specifications.png", "Mean versus robust estimators", "Estimators that ignore the outliers, the median and trimmed means, give 3.5 to 4.5 bps tighter. Adding back excluded pairs gives 0.2 to 1.2. A reasonable range is therefore about 0 to 5 bps.", True),
    ("fig13_posteriors.png", "What the data say under different starting beliefs", "A sceptic who expects zero ends at 1.5 bps tighter. Someone who expects the larger discounts found in cross issuer studies ends at 3.4. Under either starting belief, the data point toward a small number.", True),
]
figs_html = '<ul class="figs">' + "".join(
    '<li%s><figure><a class="img" href="assets/figures/%s"><img src="assets/figures/%s" alt="%s" loading="lazy"></a><figcaption><b>%s</b>%s</figcaption></figure></li>'
    % (' class="full"' if full else "", f, f, e(t), e(t), e(c)) for f, t, c, full in FIGS) + "</ul>"

stats = [
    ("2.4 bps", "The average gap by which green bonds priced tighter than their matched conventional bonds, across 153 pairs from 88 issuers. The result is not statistically significant, with a p value of 0.30, and the 95 percent interval runs from 7.1 bps tighter to 2.2 bps wider."),
    ("0 to 5 bps", "The range across other estimators and sample choices. The median pair is 4.3 bps tighter and the outlier robust estimators give 3.5 to 4.5, while adding back the pairs I had excluded reduces the average to 1.2 or less. The data do not support a narrower range."),
    ("+3.7 bps", "The average for the 10 pairs sold within a week of each other. The closest matches show no discount, although 10 pairs are too few to draw a firm conclusion."),
    ("p 0.67", "A test of whether the gap was the same across four periods from 2016 to 2026, which found no detectable change. After the ChatGPT launch the gap was 2.5 bps smaller, with a p value of 0.61, which is not significant."),
    ("6.6 bps", "The smallest true gap this sample can detect reliably. A gap of 8 bps or more is rejected, and distinguishing 5 bps from zero would require about 265 pairs. Tests for a shift over time can only detect changes of roughly 27 bps."),
    ("663 bonds", "Unique green bonds after cleaning 1,226 tracker rows. They come from 291 parent issuers in 40 countries, represent about $386 billion of face value and were issued between April 2009 and May 2026. Of these, 270 have matured."),
]
stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in stats) + "</div>"
case_page("research.html", "Green bond pricing research", "Preliminary results on whether green bonds price tighter than matched conventional bonds from the same issuer.",
          "Project, preliminary results", "Green bond pricing research", "Fixed Income Research Analyst, UMass Lowell. May 2026 to now.",
          "Do investors accept a lower yield on a green bond than on a conventional bond from the same issuer?",
          [("In short", "The question, the method, the finding, and what it means",
            story("Is the greenium real, and is it big enough to change what an issuer should do?",
                  "I started with 663 green bonds from Bloomberg and the Climate Bonds Initiative and narrowed them to 153 same issuer pairs under four pairing rules. Each pair is adjusted for Treasury rates, credit spreads and maturity using FRED data.",
                  "Green bonds priced 2.4 bps tighter on average. The result is not statistically significant, with a p value of 0.30, and the sample cannot distinguish 2 bps from zero. The two sovereigns that issue true twin bonds report a similar result, and Germany's March 2026 green Bund priced 1 bp through its twin.",
                  "On a $500 million 10 year deal, 2.4 bps is about $120,000 a year of coupon, which is less than the cost of the second party opinion and the reporting. On this evidence, the case for issuing a green bond rests on investor demand more than on a lower cost of funding.")),
           ("Method", "Matched pairs, adjusted for rates, credit and maturity",
            P("The dataset holds 663 green bonds, of which 153 have a conventional bond from the same issuer that passes four pairing rules. The twin must be denominated in US dollars and hold the same payment rank, both bonds must be at least $250 million, and neither may be callable before 90 percent of its life. Each pair is dated at its Bloomberg pricing date and adjusted for rates, credit spreads and maturity with Treasury and Moody's data from FRED. Matches were first screened with help from Claude. Every number here is preliminary.")),
           ("Results", "A small gap that the data cannot pin down", stat_html +
            P("On a $500 million, 10 year deal one basis point of coupon is worth about $50,000 a year, so 2.4 bps would be worth about $120,000 a year if the gap were real. The data do not establish that it is.",
            "There is one pattern I cannot yet explain. Pairs in which the conventional bond was issued after the green bond show a gap 11.8 bps larger than pairs in which it was issued first, with a p value of 0.008. When the twin came first the average is 3.2 bps wider, and when it came after the average is 8.6 tighter. A symmetric model should show no difference, so this needs an explanation before the headline figure is relied upon.")),
           ("Try it", "How many pairs would it take", POWER_HTML),
           ("Figures", "The research in thirteen charts",
            P("One script builds every chart from the results files, so the page and the charts always agree. Click any chart to open it.") + figs_html),
           ("Against the market", "What the issuers with real twins see",
            P("The cleanest measurements of the greenium come from sovereigns that sell a green bond and a conventional bond with the same coupon and maturity, so that the only difference between the two is the label. Germany's March 2026 green Bund, 4 billion euros at a 3.14 percent yield, priced 1 bp through its twin, and the Finanzagentur puts the year's greenium at about half a basis point. Denmark's central bank says its recent twins trade 0 to 1 bp apart, down from 2 to 4 a few years ago, with its newest 10 year coming 1.5 to 2 bp inside.",
              "My corporate pairs give a similar answer with more noise, which is a gap in the low single digits that is shrinking and cannot be distinguished from zero on a single deal. Bankers at Crédit Agricole cite 5 bp or more on bank paper. My financials subsample shows 5.1 bps tighter on 36 pairs, which appears consistent with that view, although a p value of 0.20 means the result is not reliable.")),
           ("What I got wrong first", "Two results that did not hold up",
            P("The first was a 25 bps result that turned out to be an artifact. An early version showed the gap shrinking by 25 bps, which came from measuring credit spreads over the 10 year Treasury and therefore picking up the slope of the curve. Measured over the 30 year, the credit index tracks the ICE BofA investment grade index at a correlation of 0.95, compared with 0.40 before. I withdrew the claim.",
              "The second was a dating error in my own file. In October 2026 I checked the largest residuals on the terminal and found that the file used settlement dates where pricing dates belonged. I pulled the Bloomberg pricing dates and applied the four pairing rules my supervisor adopted, which require a US dollar twin, the same payment rank, a minimum size of $250 million for both bonds and no early call. The average moved from 4.7 to 2.4 bps and the p value from 0.11 to 0.30. The rules were set after I had seen the earlier results, and the paper discloses that.")),
           ("What comes next", "Three things that would change these numbers",
            bul(["Verifying the largest residuals and 20 random pairs on the terminal, then rerunning with the confirmed set.",
                 "Replacing coupons with offering yields and daily prices, which needs TRACE and Mergent FISD access.",
                 "Finishing the twin search for the 164 live green bonds that still have no conventional match."])),
           ("Sources", "Where the numbers come from",
            '<p class="note">Built from Bloomberg, Climate Bonds Initiative and FRED data. My supervisor approved publishing summary statistics in writing. No bond level data is shown. Last updated October 2026.</p>')], banner=("assets/banners/pairs.jpg", "All 153 matched pairs in issue date order. Orange is the green bond priced tighter."))

# ---------- dcf ----------
dstats = [
    ("$8.80", "The implied value per share in the base case, using the perpetuity method at a 9.2 percent cost of capital and 1.5 percent long term growth. The shares closed at $7.77 on October 23, 2026."),
    ("$4.97", "The implied value per share in the base case, using the exit multiple method at 7 times 2031 EBITDA. The two methods disagree, and I report both figures instead of choosing one."),
    ("$3 to $15", "The range across the sensitivity grid, with the cost of capital at 8 to 11 percent and growth at 1 to 2 percent. Street price targets run from $2 to $13.74."),
    ("Below zero", "The equity value in the bear case. If half the synergies are realized and linear television declines 11 percent a year, the $84 billion of net debt exceeds the value of the business."),
    ("71%", "The share of enterprise value that sits in the terminal value. The result therefore depends more on what the company looks like after 2031 than on the next five years."),
    ("$5.4bn", "The synergies realized by 2030 in the base case, against a management target of $6 billion. Almost all of the EBITDA growth comes from this line."),
]
dstat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in dstats) + "</div>"
DFIGS = [
    ("dcf1_ebitda.png", "Where the EBITDA growth comes from", "Underlying EBITDA before synergies drifts down as linear television shrinks. Every dollar of growth from 2026 to 2031 is realized synergies."),
    ("dcf2_fcff.png", "Unlevered free cash flow", "Conversion rises from about half of EBITDA to two thirds as integration costs roll off. Management's own target is more than $10 billion of free cash flow after interest by 2030, which this model does not reach."),
    ("dcf3_sensitivity.png", "Cost of capital against long term growth", "One point of discount rate moves the value by $3 to $4 a share. The company's own leverage makes the cost of capital the least certain input."),
    ("dcf4_football.png", "Four answers on one line", "The two DCF methods, the three scenarios and the Street's targets, next to the market price. The market price falls inside every range."),
]
dfigs_html = '<ul class="figs">' + "".join(
    '<li class="dark"><figure><a class="img" href="assets/figures/%s"><img src="assets/figures/%s" alt="%s" loading="lazy"></a><figcaption><b>%s</b>%s</figcaption></figure></li>' % (f, f, e(t), e(t), e(c)) for f, t, c in DFIGS) + "</ul>"
case_page("dcf.html", "Skydance DCF model", "A pro forma discounted cash flow model of Skydance Corporation, formerly Paramount Skydance, after its purchase of Warner Bros. Discovery. Public filings only.",
          "Project", "Skydance DCF model", "Built October 24, 2026. Excel, 344 formulas, 18 sources. Market data as of October 23, 2026.",
          "This model anchors the media set. It asks what the company that just bought Warner Bros. Discovery is worth, and what must hold for the shares to be worth more than $7.77 with $89 billion of debt.",
          [("In short", "The question, the method, the finding, and what it means",
            story("What is the combined Skydance worth under $89 billion of debt, and how much of that value is the merger itself?",
                  "The model uses a pro forma base year from both companies' filings and the October 2026 8-Ks, three revenue lines, a separate synergy line, and a 9.2 percent WACC built from a 2.4 levered beta and an 8 percent cost of debt.",
                  "The model gives $8.80 a share on the perpetuity method and $4.97 on the exit multiple, against a price of $7.77. Almost all of the EBITDA growth comes from synergies, and the bear case takes the equity below zero.",
                  "The discount rate is a harder judgment than the forecast. One point of WACC is worth $3 to $4 a share, which helps explain why the bonds yield 10 to 13 percent and the equity trades like an option on the synergies.")),
           ("Why this company", "I covered its tender at Finsight",
            P("I covered the Paramount Skydance tender at Finsight and wanted to value a company whose bonds I had watched trade. By the time I built it, Paramount Skydance had closed its $110 billion purchase of Warner Bros. Discovery and become Skydance Corporation, SKYD on the NYSE. The model therefore values the combined company, which has about $70 billion of revenue, $89 billion of gross debt and 5.04 billion shares.",
              "The deal was paid for with $47 billion of new equity at $12 a share and about $52 billion of new debt. The stock closed at $7.77 on October 23. S&P cut the company to BB and the old Paramount bonds yield 10 to 13 percent. With that capital structure, the discount rate is a harder judgment than the forecast.")),
           ("The result", "A small premium on one method and a discount on the other", dstat_html +
            P("These are model outputs under stated assumptions. Nothing on this page is a recommendation to buy or sell anything.")),
           ("How it is built", "Pro forma from two companies' filings, with every input on one sheet",
            bul(["<b>Base year.</b> Paramount Skydance's fiscal 2025 results plus Warner Bros. Discovery's, giving $66 billion of revenue and $12 billion of adjusted EBITDA, which matches the pro forma 8-K and the Street's 2026 consensus.",
                 "<b>Revenue.</b> Three lines, streaming, linear networks and studios, each with its own growth path. Streaming grows 9 percent fading to 4, linear falls 8 percent fading to 6, studios grow 3.",
                 "<b>EBITDA.</b> An underlying margin that drifts down as linear shrinks, plus a separate synergy line so the reader can see how much of the value is the merger.",
                 "<b>Cash flow.</b> EBITDA less stock compensation, integration cash costs, cash taxes at 23 percent, capex at 2.1 percent of revenue and a content and working capital line. Stock compensation is treated as a real cost.",
                 "<b>Discount rate.</b> A 0.9 unlevered media beta relevered for a 2.2 debt to equity ratio gives a 2.4 levered beta and a 15.7 percent cost of equity. An 8 percent cost of debt, blended from the new 7.05 and 8.875 percent notes and the legacy unsecured yields, at market weights gives a 9.2 percent WACC.",
                 "<b>Equity bridge.</b> Enterprise value less $84 billion of net debt at close and $1 billion of noncontrolling interests, over 5.04 billion shares. The 471 million warrants struck at $12 dilute only when the value is above $12, by the treasury stock method.",
                 "<b>Three scenarios</b> on one switch: base, bear and management's plan.",
                 "<b>Four peers and a credit comp on the same template.</b> Netflix, Disney, Comcast and Fox, built the same way, then leverage, coverage and cushion across all five. See <a href=\"media.html\">Media DCF models and credit comps</a>."])),
           ("Charts", "The model in four pictures", dfigs_html),
           ("What I got wrong first", "The company I set out to value no longer existed",
            P("My first pass used Paramount Skydance's own filings: $30 billion of revenue, $15 billion of debt, 1.1 billion shares. The company that trades today is twice that size with six times the debt. That would have produced a precise answer for a company that no longer trades, so I rebuilt the base year from both companies' filings and took the debt and share count from the October 2026 8-Ks.")),
           ("What would change the answer", "In order of how much they move it",
            bul(["<b>Synergy realization.</b> The base case takes $5.4 billion of the $6 billion target by 2030. Each $1 billion of run rate synergies is worth about $1.50 a share.",
                 "<b>Linear decline.</b> Three points a year faster, which is what Warner Bros. Discovery's linear networks did in the second quarter of 2026, takes the base case most of the way to the bear case.",
                 "<b>The discount rate.</b> Market weights give 9.2 percent. If management reaches its 3.0 times leverage target by 2029, the equity weight rises and so does the WACC, which lowers the value even as the business gets safer.",
                 "<b>Content cash spend.</b> It sits inside the working capital line at about 1 percent of revenue and I could not source it. The first combined quarterly report, due in November 2026, will say whether that is right."])),
           ("Since the model", "What has moved since October 23",
            P("On October 22, the day before the model's market data, Elon Musk invested about $1 billion in Skydance equity, per Semafor and CNBC. JPMorgan upgraded the stock on October 23 and Citi put a buy on it on October 26, a day it fell 6 percent. It closed at $8.07 on November 2. The perpetuity method says $8.80 and the exit multiple says $4.97, so the price remains where the model placed it, between two methods that disagree.",
              "The model's deleveraging path needs about $47 billion of net debt to go away to hit 3.0 times. One billion dollars of equity is 2 percent of that amount. It is the path I expected the company to need, and it has now begun. The first combined quarterly report comes November 9 and will say whether the content cash spend assumption is right.")),
           ("Download", "The model and its sources",
            '<p class="links"><a href="assets/Skydance_DCF_Model.xlsx">Download the Excel model</a></p>' +
            P("Blue cells are inputs, and the scenario switch is in Inputs C5. The model cites 18 numbered sources, most of them SEC filings, and analyst judgments are labelled where they appear. No input comes from a Bloomberg Terminal or from any employer."))], banner=("assets/banners/skypath.jpg", "Skydance net leverage on the base case, with every free dollar going to debt. The target is 3.0 times by 2029."))

# ---------- media five ----------
def dfig(items):
    return '<ul class="figs">' + "".join(
        '<li class="dark%s"><figure><a class="img" href="assets/figures/%s"><img src="assets/figures/%s" alt="%s" loading="lazy"></a><figcaption><b>%s</b>%s</figcaption></figure></li>' % (" full" if full else "", f, f, e(t), e(t), e(c)) for f, t, c, full in items) + "</ul>"


M5 = [
    ("Skydance", "dcf.html", "6.9x", "9.2%", "10.1x", "$8.80", "$4.97", "$7.77", "1.1%", "8.4x", "71%"),
    ("Netflix", "dcf-nflx.html", "0.4x", "10.3%", "17.1x", "$49.79", "$68.16", "$65.85", "5.1%", "13.4x", "72%"),
    ("Disney", "dcf-dis.html", "1.6x", "9.4%", "9.2x", "$79.11", "$114.42", "$110.16", "4.1%", "9.6x", "68%"),
    ("Comcast", "dcf-cmcsa.html", "2.3x", "7.5%", "4.5x", "$44.48", "$34.81", "$22.04", "-5.3%", "3.6x", "69%"),
    ("Fox", "dcf-foxa.html", "0.6x", "7.6%", "7.9x", "$72.52", "$58.88", "$68.27", "0.5%", "8.7x", "67%"),
]
m5_table = '<div class="tablewrap"><table class="cmp"><thead><tr><th>Company</th><th>Net debt to EBITDA</th><th>WACC</th><th>Market EV to EBITDA</th><th>Perpetuity, base</th><th>Exit multiple, base</th><th>Market price</th><th>Growth the price implies</th><th>Exit multiple the price implies</th><th>Terminal share</th></tr></thead><tbody>' + \
    "".join('<tr><td><a href="%s">%s</a></td>' % (f, e(n)) + "".join("<td>%s</td>" % e(v) for v in vals) + "</tr>" for n, f, *vals in M5) + "</tbody></table></div>"
m5_stats = [
    ("5", "Companies built on one DCF template, with the same sheets, the same formulas and the same 4.95 percent risk free rate and 4.5 percent equity premium. Only the company specific inputs change."),
    ("1,860", "Formulas across the five models and the credit comps workbook, with zero errors on recalculation. Every sensitivity cell is a closed form formula."),
    ("6.9x", "Skydance net debt to EBITDA, against 0.4 for Netflix, 0.6 for Fox, 1.6 for Disney and 2.3 for Comcast. It is the first figure a desk would ask for."),
    ("1.8x", "Skydance EBITDA to interest. The other four cover interest 8 to 22 times. Coverage below 2 times is where covenants and ratings begin to constrain a company."),
    ("-31%", "The EBITDA miss that wipes out Skydance's equity at today's multiple. Comcast's equity survives a 50 percent miss, and the equity of Fox and Netflix survives more than 90."),
    ("4.5x", "Where Skydance's net leverage lands by 2031 with every free dollar going to debt. Management's target is 3.0 by 2029. Closing the gap would require asset sales or new equity."),
]
m5_stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in m5_stats) + "</div>"
CREDIT = [
    ("Skydance", "dcf.html", "6.9x", "1.8x", "0%", "68%", "0.5x", "-31%", "305 bp", "BB"),
    ("Netflix", "dcf-nflx.html", "0.4x", "21.6x", "130%", "3%", "29.2x", "-97%", "85 bp", "A"),
    ("Disney", "dcf-dis.html", "1.6x", "19.3x", "22%", "17%", "3.3x", "-80%", "75 bp", "A"),
    ("Comcast", "dcf-cmcsa.html", "2.3x", "7.9x", "16%", "50%", "2.0x", "-50%", "95 bp", "A range"),
    ("Fox", "dcf-foxa.html", "0.6x", "10.9x", "88%", "8%", "12.7x", "-92%", "125 bp", "not found"),
]
credit_table = '<div class="tablewrap"><table class="cmp"><thead><tr><th>Company</th><th>Net debt to EBITDA</th><th>EBITDA to interest</th><th>Free cash flow after interest to net debt</th><th>Net debt share of enterprise value</th><th>DCF equity over net debt</th><th>EBITDA miss that wipes out the equity</th><th>Spread to Treasury on the cost of debt</th><th>S&amp;P rating, where sourced</th></tr></thead><tbody>' + \
    "".join('<tr><td><a href="%s">%s</a></td>' % (f, e(n)) + "".join("<td>%s</td>" % e(v) for v in vals) + "</tr>" for n, f, *vals in CREDIT) + "</tbody></table></div>"
case_page("media.html", "Media DCF models and credit comps", "Five discounted cash flow models of Skydance, Netflix, Disney, Comcast and Fox on one template, then a credit comparison built the way a credit analyst or a debt capital markets desk would build it.",
          "Project", "Media DCF models and credit comps", "Built October 24 and 25, 2026. Five Excel models plus a credit comps workbook. 1,860 formulas, 71 sources. Market data as of October 22 and 23, 2026.",
          "Five media companies valued on the same basis and then compared as a credit analyst would compare them, on leverage, coverage, cash flow against debt, the equity cushion beneath the bonds and where the debt prices.",
          [("In short", "The question, the method, the finding, and what it means",
            story("Valued the same way, which of five media capital structures can carry its debt, and what does each share price already assume?",
                  "Five DCF models built from SEC filings on one template, with the same risk free rate, equity premium and cash flow definition, then a credit comparison on leverage, coverage and the equity cushion under the bonds.",
                  "Four prices reconcile with their filings within a point of growth. Comcast is priced as if cash flow shrinks 5 percent a year forever. Skydance is the only one past 3 times leverage and under 2 times coverage, and a 31 percent EBITDA miss wipes out its equity.",
                  "That cushion is why Skydance's first liens trade 170 bp wide of the BBB index while Netflix printed a 10 year at 5.346 percent in July. The 3.0 times target cannot be reached on cash flow alone, so the path runs through asset sales or equity, and I expect that to be the subject of the next transaction.")),
           ("Why I built this", "The primary market, and why a bond prices where it does",
            P("I am seeking a position in fixed income, in credit research, syndicate or debt capital markets. What interests me most is working out why a bond prices where it does, from where price talk begins to where the deal prints and how it trades the following day. The market tests that analysis within hours.",
              "At Finsight I spent nine months as close to that process as an intern can be. I collected order books from 30 or more syndicate desks on 15 to 20 deals a day, and followed price talk to print and volume against Street estimates. I also wrote headlines on more than 25 liability management deals.",
              "This page covers five companies I either covered or followed, valued on the same basis and then assessed as credits. Skydance is the anchor because I covered the Paramount tender and then watched the market reprice the whole capital structure when the Warner Bros. Discovery debt was issued.")),
           ("The five models", "One template, five companies, and what each price already assumes", m5_stat_html + m5_table +
            P("One page per company: <a href=\"dcf.html\">Skydance</a>, <a href=\"dcf-nflx.html\">Netflix</a>, <a href=\"dcf-dis.html\">Disney</a>, <a href=\"dcf-cmcsa.html\">Comcast</a>, <a href=\"dcf-foxa.html\">Fox</a>. Reversing each DCF gives the growth and exit multiple the share price already assumes, in the last three columns. Four prices reconcile with their filings within a point of growth. Comcast is priced as if its cash flow shrinks 5 percent a year forever, and none of the scenarios I built is that severe. I do not conclude that the market is wrong. The point is that the price and the filings disagree, and the table shows by how much.",
              "These are model outputs under stated assumptions. Nothing here is a recommendation to buy or sell anything.")),
           ("Try it", "Move the inputs and watch the value move", explorer_html()),
           ("The credit comps", "The same five, read the way a desk reads them", credit_table +
            P("A desk starts with net debt to EBITDA, then coverage, then years of free cash flow to repay the debt, then how much equity sits under the bonds if EBITDA misses. Skydance fails every test the other four pass. Net debt is 68 percent of enterprise value, free cash flow after interest is about zero in year one, and a 31 percent EBITDA miss leaves nothing for the equity.",
              "That is why the first lien 2031s trade at 272 bp, 170 bp wide of the BBB index, and the second liens at 483 bp, while Netflix printed a 10 year at 5.346 percent in July. The spreads in the table are where I think a new 10 year prints for each name. Only the Skydance figure is anchored on sourced levels. The other four are my own inputs and are labelled as such in the workbook.")),
           ("The deleveraging question", "Can Skydance get to 3.0 times on cash flow alone",
            P("Management's target is 3.0 times by 2029. On my base case, with every free dollar going to debt, net leverage is 6.3 times at the end of 2027, 5.0 at the end of 2029 and 4.5 at the end of 2031. Getting to 3.0 means cutting about $47 billion of net debt on under a billion of first year free cash flow after interest. That implies asset sales or equity, which is the purpose of the second lien equity clawback.") +
            dfig([("m5_skypath.png", "Net debt and net leverage, year by year", "The base case, with no asset sales and no new equity. The line does not reach the target.", True)])),
           ("What I would watch", "If I covered Skydance's debt",
            bul(["<b>Free cash flow after interest.</b> It is about zero in year one of my base case. The first combined quarterly report on November 9 will be the first real indication of it.",
                 "<b>Asset sales or equity.</b> Getting to 3.0 times means cutting about $47 billion of net debt. The $1 billion of equity in October is 2 percent of that.",
                 "<b>The first liens.</b> They trade at 272 bp, 170 bp wide of the BBB index. With this little equity under them, I expect them to react to the stock more than a BBB bond would.",
                 "<b>The other four.</b> Netflix, Fox and Disney carry less than 2 times leverage and have the cushion to take a miss. Comcast sits in the middle at 2.3 times, and half of its capital is debt."])),
           ("Charts", "Five charts, one per question",
            dfig([("m5_credit.png", "Leverage and coverage", "Skydance is the only one past 3 times leverage and the only one under 2 times coverage.", True),
                  ("m5_cushion.png", "The equity cushion", "Equity value for each EBITDA miss at today's multiple. Skydance hits zero at 31 percent, Comcast at 50, the other three past 80.", True),
                  ("m5_vs_market.png", "Where each DCF lands against its price", "Dots are the base case on each method, bars run bear to bull. Only Comcast's whole range sits above its price.", True),
                  ("m5_implied.png", "Reverse the DCF", "What I assumed against what the price implies. They agree everywhere except Comcast.", True),
                  ("m5_wacc_tv.png", "Cost of capital and terminal value share", "The risk free rate and premium are the same in all five, so the spread in WACC comes from beta and leverage. Two thirds or more of every valuation sits past the forecast.", True)])),
           ("What is the same and what is not", "The rules I held constant",
            bul(["<b>Same discount rate inputs.</b> 10 year Treasury 4.95 percent, equity risk premium 4.5 percent, cash tax 23 percent, market weights, Hamada relevering. Cost of debt 75 to 125 bp over Treasuries for the four investment grade names, 8 percent blended for Skydance.",
                 "<b>Same cash flow definition.</b> Adjusted EBITDA less stock compensation, cash restructuring, cash taxes on profit after tax depreciation, capex and a working capital and content line. Stock compensation is a real cost in all five.",
                 "<b>Same mechanics.</b> Mid year discounting, a first year stub, perpetuity and exit multiple side by side, three scenarios on one switch.",
                 "<b>Different fiscal years.</b> Disney and Fox run FY2027 to FY2032 with stubs of 0.94 and 0.68. The other three run calendar 2026 to 2031 with a 0.19 stub.",
                 "<b>Different pending deals.</b> Comcast is modelled before the NBCUniversal and Sky spin, Fox without Roku, and Skydance after Warner Bros. Discovery, because that deal has closed.",
                 "<b>Interest expense.</b> Comcast's and Disney's are reported. Skydance's, Netflix's and Fox's are estimates from gross debt and a blended coupon, flagged in the comps."])),
           ("What I got wrong first", "Betas off a quote page, and a cost of debt below the Treasury yield",
            P("The first error was treating quoted betas as unlevered betas. Netflix came out at an 11.6 percent WACC and $42 a share, and Comcast's unlevered beta fell below that of a utility. I set the betas by hand, at 0.6 for Fox, 0.7 for Comcast, 0.9 for Skydance, 1.05 for Disney and 1.2 for Netflix, and recorded the reasoning on each WACC sheet.",
              "The second is the one a desk would notice first. I had the four investment grade names borrowing at 5 to 5.5 percent with the 10 year at 4.95, which implies 5 to 55 bp of spread, and no investment grade issuer prices at those levels. I moved them to 75 to 125 bp over Treasuries. The change has little effect on three of them and takes $3 off Comcast, because half its capital is debt.",
              "On October 26 I checked those inputs on a terminal against where each name's long dated debt trades. Disney, Netflix and Fox were within a normal margin of error. Comcast was the exception. After three agencies placed it on negative watch for the spin, the market had it wider than my 95 bp by a margin that would not surprise a desk. Moving Comcast's cost of debt to the market level lifts its WACC to 7.8 percent and takes about $2 more off the perpetuity value. It does not change any conclusion, because the model still lands well above the price. The levels themselves are not published on this site.")),
           ("Since the models", "What has moved since October 23",
            bul(["<b>Skydance.</b> On October 22 Elon Musk put about $1 billion of equity into the company, per Semafor and CNBC, and the stock was upgraded at JPMorgan on October 23 and at Citi on October 26. It closed at $8.07 on November 2 against the $7.77 in the model, inside the range on both methods. Third quarter results come November 9, the first combined print.",
                 "<b>What $1 billion does.</b> The deleveraging page above says reaching 3.0 times means cutting about $47 billion of net debt. One billion of new equity is 2 percent of that. It is the equity path the model indicated the company would need. It has begun, and it is far from complete.",
                 "<b>Fox and Roku.</b> Both sets of shareholders approved the $22 billion deal in October. The Justice Department issued a second request, so closing is now first half of 2027 at the earliest. The Fox model remains standalone, and that decision still looks appropriate.",
                 "<b>Rates.</b> The 10 year Treasury was at 5.00 percent on October 26 after 5.31 on October 5. The five models use 4.95. A move of that size within a month shows why the WACC sensitivity grids matter.",
                 "<b>Supply.</b> Investment grade issuance passed the 2020 record on October 26 at $1.76 trillion, with cloud and data center borrowers selling almost $368 billion of debt this year. That is the backdrop for the credit comps, a market that will fund almost any borrower at the right spread."])),
           ("Download", "Five models and the credit comps",
            '<p class="links"><a href="assets/Media_Credit_Comps.xlsx">Credit comps workbook</a> &nbsp;&middot;&nbsp; <a href="assets/Skydance_DCF_Model.xlsx">Skydance</a> &nbsp;&middot;&nbsp; <a href="assets/NFLX_DCF_Model.xlsx">Netflix</a> &nbsp;&middot;&nbsp; <a href="assets/DIS_DCF_Model.xlsx">Disney</a> &nbsp;&middot;&nbsp; <a href="assets/CMCSA_DCF_Model.xlsx">Comcast</a> &nbsp;&middot;&nbsp; <a href="assets/FOXA_DCF_Model.xlsx">Fox</a></p>' +
            P("Blue cells are inputs, and the scenario switch is in Inputs C5 of each model. The comps workbook names the model every figure came from. No input in these files comes from a Bloomberg Terminal or any employer. The October 26 check above was a comparison only."))], banner=("assets/banners/media.jpg", "The five companies compared on leverage first and on value second."))


def company_dcf_page(fname, name, h1, meta, lede, why, stats, build, charts, wrong, change, xlsx, extra_note, short=None):
    stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in stats) + "</div>"
    case_page(fname, "%s DCF model" % name, "A discounted cash flow model of %s on the same template as my Skydance model. Public filings only." % name,
              "Project", h1, meta, lede,
              ([("In short", "The question, the method, the finding, and what it means", story(*short))] if short else []) +
              [("Why this company", why[0], P(*why[1])),
               ("The result", "The numbers", stat_html + P("These are model outputs under stated assumptions. Nothing on this page is a recommendation to buy or sell anything.")),
               ("How it is built", "Inputs that differ from the template", bul(build)),
               ("Charts", "Two pictures", dfig(charts)),
               ("What I got wrong first", wrong[0], P(*wrong[1])),
               ("What would change the answer", "In order of how much they move it", bul(change)),
               ("Download", "The model",
                '<p class="links"><a href="assets/%s">Download the Excel model</a> &nbsp;&middot;&nbsp; <a href="media.html">Back to the five</a></p>' % xlsx + P(extra_note))],
              banner=("assets/banners/%s.jpg" % fname.replace("dcf-", "").replace(".html", ""), "%s on the shared DCF template. Cost of capital, leverage and coverage from my model." % name))


company_dcf_page("dcf-nflx.html", "Netflix", "Netflix DCF model", "Built October 24, 2026. Excel, 311 formulas, 10 sources. Market data as of October 23, 2026.",
    "Netflix is the streaming business the other four are trying to build. At 17 times EBITDA, what does the price already assume?",
    ("The benchmark for the Skydance streaming line", [
        "Skydance's base case grows streaming 9 percent fading to 4. Netflix grew 13 percent in 2026 on $51 billion of revenue at a 31.5 percent operating margin. If I assume Skydance can grow streaming, I should know what the leader earns doing it and what the market pays for it.",
        "Netflix walked away from Warner Bros. Discovery in February 2026 with a $2.9 billion termination fee. I exclude that fee from cash flow."]),
    [("$49.79", "The base case on the perpetuity method, at a 10.3 percent WACC and 3 percent long term growth. This is below the $65.85 close on October 23, 2026."),
     ("$68.16", "The base case on the exit multiple method, at 14 times 2031 EBITDA. This is above the market price. The two methods disagree by $18, and that gap is the central finding."),
     ("5.1%", "The perpetual growth the price implies. A 10 percent discount rate and 3 percent growth cannot reach $66 on a business that already earns 32 percent margins."),
     ("72%", "The share of value that falls after 2031. As with most growth companies, the valuation rests largely on the terminal value."),
     ("$34 to $82", "The range from bear to bull across both methods. The bear case fades subscription growth to 3 percent with flat margins, and the bull case keeps growth in double digits through 2028 and lifts margins to 39 percent."),
     ("17.1x", "Market EV to 2026 EBITDA. By comparison, Skydance trades at 10, Disney at 9, Fox at 8 and Comcast at 4.5.")],
    ["<b>Base year.</b> 2026 guidance of about $51.1 billion of revenue and a 31.5 percent operating margin from the October 20 shareholder letter, split into subscription and about $2.7 billion of advertising.",
     "<b>Revenue.</b> Subscription grows 10 percent fading to 5. Advertising grows 40 percent fading to 15 off a small base, with 15 new ad markets in 2027.",
     "<b>EBITDA.</b> Operating income plus property depreciation only. Content amortization, $16.4 billion in 2025, stays inside costs. The margin rises about a point a year to 36 percent by 2031.",
     "<b>Content cash.</b> Netflix spends about 1.1 times what it amortizes. The excess, about 3.3 percent of revenue, sits in the working capital and content line and fades to 2 percent as spending growth slows.",
     "<b>Discount rate.</b> Unlevered beta 1.2, almost no leverage, so the WACC is close to the 10.5 percent cost of equity. Cost of debt 5.8 percent, the July 2026 notes repriced about 85 bp over today's Treasury.",
     "<b>Equity bridge.</b> $15.3 billion of gross debt, $8.2 billion of cash, about 4,164 million shares. The share count is an estimate from market cap over price because I could not retrieve the 10-Q cover, and it is flagged in the model."],
    [("m5_nflx_cash.png", "Base case EBITDA, free cash flow and revenue", "Revenue reaches about $80 billion by 2031. Free cash flow conversion is high because capex is 1.5 percent of revenue and the content line is small relative to the margin.", False),
     ("m5_nflx_football.png", "Where the answers land", "The perpetuity grid reaches the price only below a 9.5 percent WACC. The exit multiple grid straddles it at every WACC. Street targets run $57 to $126.", False)],
    ("I took the quoted beta at face value", [
        "A beta of 1.61 taken from a quote page gave an 11.6 percent WACC and $42 a share. That beta is a five year regression on a stock that fell by half in 2022. I used 1.2 and recorded the reasoning, and the sensitivity grid runs from 8 to 11 percent so that a reader can restore the 1.61."]),
    ["<b>The exit multiple.</b> Each turn of EBITDA is worth about $4 a share. 14 times is below the 17 the market pays today and above where a company growing 5 percent should trade in 2031.",
     "<b>Margin ceiling.</b> The base case stops at 36 percent. Every point of terminal margin is worth about $1.50 a share.",
     "<b>Advertising.</b> The October 20 letter cut 2026 ad guidance from about $3 billion to $2.7 billion. Advertising is 5 percent of revenue, so this is a small line to which the market gives considerable weight.",
     "<b>The share count.</b> If the real count is 4,195 million, the diluted figure, every value on this page is about 0.7 percent lower."],
    "NFLX_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. Sources are numbered and cited next to each figure. Nothing in the model comes from a Bloomberg Terminal or from any employer.",
    short=("At 17 times EBITDA, what growth and margin does the Netflix price already assume, and is that a fair benchmark for Skydance's streaming line?",
           '2026 guidance of $51 billion of revenue and a 31.5 percent operating margin, split into subscription and advertising, discounted at a 10.3 percent WACC with content amortization kept inside costs.',
           'The model gives $49.79 a share on the perpetuity method and $68.16 on the exit multiple, against a $65.85 price. The price requires 5.1 percent growth in perpetuity or a multiple of 14 times or more in 2031.',
           "Netflix borrows at 85 bp over Treasuries with almost no leverage, so the market prices it as the safest credit of the five and the richest equity. Skydance's streaming case rests on reaching margins Netflix took a decade to earn."))

company_dcf_page("dcf-dis.html", "Disney", "Disney DCF model", "Built October 24, 2026. Excel, 323 formulas, 12 sources. Fiscal year ends in late September. Market data as of October 16, 2026.",
    "Disney is the closest comparison to Skydance that already operates as one company, with studios, linear networks and streaming under one roof, in addition to the parks.",
    ("Skydance with parks and twenty years of integration", [
        "Disney has the same three pieces as the combined Skydance, studio, linear networks and streaming, and has already made them one company. Its Entertainment segment is the best public read on where Skydance's margins could settle. Experiences is the piece Skydance does not have, and it is more than half of Disney's operating income.",
        "Fiscal 2026 results come November 17. The base year is nine months of actuals plus fourth quarter guidance, and the model states this."]),
    [("$79.11", "The base case on the perpetuity method, at a 9.4 percent WACC and 2 percent long term growth. This is below the $110.16 price."),
     ("$114.42", "The base case on the exit multiple method, at 10 times FY2032 EBITDA. This is in line with the price. The market pays about 9 times today."),
     ("4.1%", "The perpetual growth the price implies on the perpetuity method. For a company whose linear networks are shrinking, that is a demanding assumption to hold in perpetuity."),
     ("68%", "The share of value that falls after FY2032."),
     ("$33 to $138", "The range from bear to bull across both methods. The bear case shrinks Entertainment 1 percent a year with margins falling to 21 percent, and the bull case grows all three segments and takes margins to 28 percent."),
     ("$9bn", "FY2026 capex guidance, up from $5.4 billion two years earlier, almost all of it cruise ships. The base case brings it back to 7 percent of revenue by FY2030.")],
    ["<b>Base year.</b> Revenue about $101 billion and total segment operating income about $19.7 billion for FY2026, from nine months of actuals plus guidance. EBITDA adds $5.3 billion of depreciation.",
     "<b>Revenue.</b> Entertainment $48 billion growing 3 percent fading to 2, Sports $18.5 billion growing 3 fading to 2, Experiences $39 billion growing 6 fading to 4. The FY2027 total of $105.5 billion is within $100 million of consensus.",
     "<b>EBITDA.</b> One blended margin starting at 24.5 percent and drifting up to 25.8 as streaming scales. Restructuring of $300 million in FY2027 fading to zero.",
     "<b>Discount rate.</b> Unlevered beta 1.05, 0.2 debt to equity, cost of equity 10.5 percent, cost of debt 5.7 percent on a single A rating. WACC 9.4 percent.",
     "<b>Equity bridge.</b> $46 billion of borrowings, $5.2 billion of cash, $6.8 billion of noncontrolling interests after the Fubo and NFL deals, 1,727 million shares from the 10-Q cover.",
     "<b>Stub.</b> 94 percent of FY2027 remains from the valuation date, so almost a full first year is discounted at a mid year 0.47."],
    [("m5_dis_cash.png", "Base case EBITDA, free cash flow and revenue", "Free cash flow steps up as capex comes down from the cruise ship peak. That capex path is the biggest judgment in the model after the margin.", False),
     ("m5_dis_football.png", "Where the answers land", "The exit multiple range straddles the price. The perpetuity grid reaches it only below an 8 percent WACC or with 3 percent growth. Street targets run $111 to $164.", False)],
    ("I tried to use the reported tax rate", [
        "Fiscal 2025 shows a tax benefit from a $3.3 billion Hulu item, so the reported rate is not usable. I use the same 23 percent cash rate as the other four, with the FY2024 derived 23.7 percent as the check. The $110.16 price is from October 16 and not October 23, and the model flags this."]),
    ["<b>Linear decline inside Entertainment.</b> Linear was $3 billion of the segment's $4.7 billion of operating income in FY2025. If it falls 10 percent a year and streaming does not fill the hole, the base case becomes the bear case.",
     "<b>Capex.</b> Each point of revenue in terminal capex is worth about $8 a share. The cruise ships are the reason this input matters.",
     "<b>Experiences growth.</b> The segment is 57 percent of operating income. Two points of growth there is worth more than five points in Sports.",
     "<b>The November 17 results.</b> They replace my estimated base year with a real one."],
    "DIS_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. The base year is labelled as an estimate until the FY2026 10-K is out. Nothing in the model comes from a Bloomberg Terminal or from any employer.",
    short=("What is Disney worth with linear networks shrinking inside Entertainment, and where could Skydance's margins settle if it finished integrating?",
           'FY2026 revenue of about $101 billion from nine months of actuals plus guidance, three segments with separate growth paths, capex fading from a $9 billion cruise ship peak, and a 9.4 percent WACC.',
           'The model gives $79.11 a share on the perpetuity method and $114.42 on the exit multiple, against a $110.16 price. The price implies 4.1 percent growth forever for a company whose linear networks are shrinking.',
           'Experiences is 57 percent of operating income and the piece Skydance does not have. Disney shows what an integrated media company earns, and it still only reaches its price on the exit multiple.'))

company_dcf_page("dcf-cmcsa.html", "Comcast", "Comcast DCF model", "Built October 24, 2026. Excel, 311 formulas, 14 sources. Market data as of October 23, 2026.",
    "Comcast is the one company the model cannot reconcile with its price. At $22 the market is pricing Comcast as a business in permanent decline, and the filings do not support that view.",
    ("A media company that is breaking itself up", [
        "Comcast resembles what Skydance might look like after a decade, with cable, a studio, parks, a streaming service that has just turned profitable and 2.3 times leverage. It spun off its cable networks in January 2026 and will spin NBCUniversal and Sky in mid 2027, so it is becoming a broadband utility.",
        "I value it as it is today, before the spin, on nine months of 2026 actuals. That is the only basis the filings support."]),
    [("$44.48", "The base case on the perpetuity method, at a 7.5 percent WACC and 0.5 percent long term growth. This is more than twice the $22.04 price."),
     ("$34.81", "The base case on the exit multiple method, at 5.5 times 2031 EBITDA. The market pays 4.5 times today and paid 6 to 7 for most of the last decade."),
     ("-5.3%", "The perpetual decline in cash flow that the price implies. The bear case, with connectivity falling 3 percent a year and margins down to 25 percent, still lands at $23 to $27."),
     ("3.6x", "The exit multiple the price implies, which is below where any large cable company has traded outside a crisis."),
     ("7.5%", "The WACC. Half of Comcast's capital is debt at about 4.5 percent after tax, which is why the discount rate is the lowest of the five and the value is the most sensitive to it."),
     ("69%", "The share of value that falls after 2031.")],
    ["<b>Base year.</b> 2026 as now reported, without Versant and from the second quarter without Sky Deutschland. Nine months of $90.7 billion of revenue and $25.9 billion of adjusted EBITDA, annualized to $120.5 billion and $35 billion.",
     "<b>Revenue.</b> Two lines. Connectivity and Platforms, $79 billion, falls 1 percent a year then flattens as price offsets broadband losses. Content and Experiences, $41.5 billion net of eliminations, grows 2 percent.",
     "<b>EBITDA.</b> Margin 29 percent drifting down to 28. Separation costs of $500 million in 2026, $800 million in 2027 and $300 million in 2028, which are my estimates.",
     "<b>Cash flow.</b> Capex 9.5 percent of revenue. Depreciation of $16 billion a year shelters a lot of the profit from cash tax, which is a real reason cable cash flow is high relative to EBITDA.",
     "<b>Discount rate.</b> Unlevered beta 0.7, 1.0 debt to equity, levered beta 1.24, cost of equity 10.6 percent, cost of debt 5.9 percent. Market weights give 7.5 percent.",
     "<b>Equity bridge.</b> $87.4 billion of debt, $7.6 billion of cash, 3,551 million shares from the October 15 cover."],
    [("m5_cmcsa_cash.png", "Base case EBITDA, free cash flow and revenue", "Flat revenue, flat EBITDA, and unlevered free cash flow of about $17 billion a year. The market enterprise value is about nine years of that.", False),
     ("m5_cmcsa_football.png", "Where the answers land", "Every range starts above the price. That is unusual, and I treat it as the finding itself and not as a reason to place more trust in the model.", False)],
    ("I believed the first answer", [
        "The first build gave $60 a share. For a $78 billion company, a result that far from the price is a signal to recheck the model before drawing any conclusion. I raised the beta, cut growth to 0.5 percent, cut the exit multiple to 5.5, put the cost of debt at 95 bp over Treasuries and ran the bear case harder. The model still lands at $35 to $44. The page therefore does not claim that Comcast is cheap. It sets out what the price assumes, which is a decline of 5 percent a year in perpetuity, and leaves the reader to judge whether broadband and parks are likely to decline at that rate."]),
    ["<b>The discount rate.</b> Each point of WACC is worth $8 to $15 a share on the perpetuity method. If the spin leaves the broadband company with a higher cost of debt, the value would change quickly.",
     "<b>Broadband losses.</b> Comcast is losing subscribers to fixed wireless and fiber. The bear case runs connectivity down 3 percent a year. The price implies a steeper decline.",
     "<b>The spin itself.</b> A sum of the parts after mid 2027 is a different model with two balance sheets, and the S-4 or Form 10 is the document to build it from.",
     "<b>Theme parks.</b> Segment EBITDA fell 17 percent in the third quarter of 2026 on a tough Epic Universe comparison. I grow the segment 2 percent, which may be generous."],
    "CMCSA_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. The 2026 base year is annualized from nine months and labelled as such. Nothing in the model comes from a Bloomberg Terminal or from any employer.",
    short=('Why does the market price Comcast at 4.5 times EBITDA, and do the filings support a business that shrinks forever?',
           '2026 annualized from nine months, with Versant out and Sky Deutschland out from the second quarter. Two revenue lines, a 7.5 percent WACC with half the capital in debt, and a bear case run harder than usual.',
           'The model gives $44.48 a share on the perpetuity method and $34.81 on the exit multiple, against a $22.04 price. The price implies cash flow falling 5.3 percent a year forever and a 3.6 times exit multiple.',
           "Half of Comcast's capital is debt at 4.5 percent after tax, so each point of WACC is worth $8 to $15 a share. Three agencies have it on negative watch for the spin, and that is the gap between my cost of debt and the market's."))

company_dcf_page("dcf-foxa.html", "Fox", "Fox DCF model", "Built October 24, 2026. Excel, 323 formulas, 9 sources. Fiscal year ends June 30. Market data as of October 22, 2026.",
    "A pure linear network company with no debt problem, so it isolates the one assumption that drives the Skydance bear case: how fast cable networks decline.",
    ("The clean read on linear decline", [
        "Skydance's bear case breaks because linear television shrinks 11 percent a year under $89 billion of debt. Fox is two thirds cable and broadcast networks with almost no net debt, so it shows what linear is worth on its own. Fiscal 2026 revenue still grew 5 percent with Super Bowl LX, so the decline is not a straight line.",
        "Fox agreed in June 2026 to buy Roku for about $22 billion. The deal has not closed, so Roku is excluded."]),
    [("$72.52", "The base case on the perpetuity method, at a 7.6 percent WACC and 1 percent long term growth. This is just above the $68.27 price."),
     ("$58.88", "The base case on the exit multiple method, at 7 times FY2032 EBITDA. The market pays about 8 times today."),
     ("0.5%", "The perpetual growth the price implies. The market and I agree on Fox within a point, which is the best check I have that the template works."),
     ("67%", "The share of value that falls after FY2032, the lowest of the five. A long first year and flat cash flow put more of the value inside the forecast."),
     ("$42 to $97", "The range from bear to bull across both methods. The bear case runs cable down 4 to 5 percent a year with margins at 17 percent, and the bull case holds margins at 23 and grows Tubi.")],
    ["<b>Base year.</b> Fiscal 2026 actuals: revenue $17.1 billion, adjusted EBITDA $3.9 billion, capex $502 million, depreciation $410 million.",
     "<b>Revenue.</b> Three lines. Cable $7.5 billion, Television $9.9 billion and Other $400 million for FY2027. Growth alternates, up in even fiscal years with political advertising, Super Bowls and the World Cup, down in odd years.",
     "<b>EBITDA.</b> Margin 22 percent drifting down to 20 as sports rights grow faster than revenue. Fiscal 2026 was 22.8 percent.",
     "<b>Cash flow.</b> Capex 2.5 percent of revenue and a 0.5 percent working capital line for sports rights prepayments. Fiscal 2026 free cash flow fell to $1.5 billion from $3 billion with no explanation in the release, and the model does not assume it recovers all the way.",
     "<b>Discount rate.</b> Unlevered beta 0.6, under 0.1 debt to equity, cost of equity 7.8 percent, cost of debt 6.2 percent. WACC 7.6 percent.",
     "<b>Equity bridge.</b> $6.6 billion of debt, $4.2 billion of cash, 419.65 million shares from the 10-K cover, Class A and B together. The stub is 68 percent of FY2027."],
    [("m5_foxa_cash.png", "Base case EBITDA, free cash flow and revenue", "The sawtooth is the even year political cycle. EBITDA drifts down through it because rights costs do not follow the same cycle.", False),
     ("m5_foxa_football.png", "Where the answers land", "Both methods bracket the price. Street targets run $60 to $97 and the consensus is $78.", False)],
    ("I almost built the combined company", [
        "Roku adds $14.2 billion of cash consideration, a bridge loan, 143 million new shares and $400 million of synergies. Modelling that from a press release would mean guessing at the capital structure. I kept Fox standalone, and the Roku model will wait for the S-4."]),
    ["<b>Cable decline.</b> Each point of annual cable revenue decline is worth about $2 a share. This is the same lever as the Skydance bear case, without the debt.",
     "<b>Sports rights.</b> The margin path assumes rights costs grow faster than revenue. If Fox lets a rights package go, margins would hold and the bull case becomes plausible.",
     "<b>Roku.</b> Shareholders of both companies approved the deal in October 2026 and the Justice Department issued a second request, so closing is the first half of 2027 at the earliest. When it closes it changes the share count, the debt and the growth rate at once.",
     "<b>The missing FCF.</b> The base case assumes about $2.4 billion of unlevered free cash flow a year. If fiscal 2026 was the new normal rather than timing, the base case is high by about $30 a share."],
    "FOXA_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. Roku is excluded on purpose. Nothing in the model comes from a Bloomberg Terminal or from any employer.",
    short=('What is a linear network company worth on its own, with no debt to cloud the answer, and how fast does cable decline?',
           'Fiscal 2026 actuals of $17.1 billion of revenue and $3.9 billion of EBITDA, three revenue lines with an even year political cycle, margins drifting down as sports rights grow, and a 7.6 percent WACC.',
           'The model gives $72.52 a share on the perpetuity method and $58.88 on the exit multiple, against a $68.27 price. The price implies 0.5 percent growth, and the market and I agree within a point.',
           'Each point of annual cable decline is worth about $2 a share. That is the same lever as the Skydance bear case, without the $89 billion of debt, which is why Fox is the cleanest read of the five.'))

# ---------- tender ----------
case_page("tender.html", "Tender Tracker", "A daily tracker of bond tender and exchange offers built from SEC filings and newswires, with its error rates published.",
          "Project, live", "Tender Tracker", "Personal project. October 2026 to now.",
          "A daily tracker of cash tender offers and exchange offers for corporate bonds, read from SEC filings and newswire press releases.",
          [("In short", "The question, the method, the finding, and what it means",
            story("What does a bond tender look like in the busiest issuance year on record, and can a free script keep the list current?",
                  "SEC EDGAR full text search over Forms 8-K and 6-K plus three newswires, read by a set of rules that extracts offer type, securities, cap and dates. Accuracy was graded on filings the rules had never seen, then the offers were measured on size, speed and what changed after launch.",
                  "Tenders fall into two groups. Two thirds of launches expire within four to seven business days with no early deadline and a cash cap, median $500 million. The rest run about 20 business days and carry almost every early deadline, exchange and consent solicitation. About one in five offers was extended or amended after launch.",
                  "The fast tender is a refinancing tool that runs alongside a new issue, which is why there are so many of them in a record year. The slow tender is a negotiation with holders. A desk should price the two differently, and a tracker is only useful if it can distinguish between them. For a credit analyst, the cap and the price show how much debt the issuer wants gone and what it will pay to remove it.")),
           ("What it does", "One row per offer, with a link to the filing",
            P("Each offer shows its securities, cap, expiration and the steps seen so far, with a link to the filing or press release behind every row. It reads public SEC filings and public newswire pages and rebuilds every day.") +
            P("I designed the page to match my market dashboard. It has a table of offers that can be sorted and searched, a panel of offers by status that can be clicked to filter, a count of filings read by day and a list of the offers expiring next.") +
            '<p class="links"><a href="https://ferrierotony-cmyk.github.io/market_dashboard/tender/">Open the tracker</a> &nbsp;&middot;&nbsp; <a href="%s" rel="noopener">Code</a></p>' % TENDER_CODE +
            '<a class="shot" href="https://ferrierotony-cmyk.github.io/market_dashboard/tender/"><img src="assets/tender-tracker.jpg" alt="The Tender Tracker page on a dark background, showing a table of offers with their status, securities, caps and expiration dates, with panels for offers by status, filings read by day and the offers expiring next" width="1920" height="960" loading="lazy"></a>'),
           ("How often it is right", "Nine in ten on type and dates, three in four on securities and caps",
            P("AI reviewers graded it against the filings on releases the rules had never seen. Offer type and dates were right about nine times in ten. Securities and caps were right about three times in four. These rows have not been checked by a person.") +
            P("The most common mistake is counting new notes being issued, or notes being redeemed, as the notes targeted. On the period the rules were built on, it found 32 of 33 offer releases, which is a best case. On October 26 I fixed the redeemed notes case and a few grouping errors. Those fixes have not been tested on new filings yet, so I do not claim a new number for them.") +
            P("The weakness was recall. Through October 26 the search only read Form 8-K exhibits with six phrasings, and it found 17 offers in 90 days. Many issuers never file an 8-K for a tender and issue only a press release. On October 27 I widened the SEC search to 54 phrasings and Form 6-K, added PR Newswire and Bing News as sources, and the same window went to 44 offers. Fourteen more came from issuer sites and wires the script cannot reach, typed in by hand with the source linked and tagged HAND on the page. The accuracy figures above apply to the rules and not to the rows entered by hand.")),
           ("What the data say so far", "Two kinds of tender, and which one a record year produces",
            '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in [('35', 'Launches read from SEC filings between August 5 and November 3, 2026. They comprise 28 cash tenders and 7 exchange offers, in addition to 14 offers added by hand.'), ('4 to 7 days', 'Business days from launch to expiration for 21 of the 31 launches with a date. None of the 21 had an early tender deadline. 13 carried a cash cap and 6 were any and all.'), ('20 to 22 days', 'The other 9 launches. Seven of them had an early deadline, five were exchange offers and five carried a consent solicitation. Corteva, Tyson, Oneok and Kimberly Clark were in this group.'), ('$500m', "Median cap across the 18 offers with a dollar cap. HSBC's $5 billion was the largest, then Oneok and Cloud Software Group at $2 billion. The 18 caps add up to $16.4 billion."), ('9 of 50', 'Offers that were extended or amended after launch, 5 extensions and 6 amendments, with two offers doing both. Where the results were read, Baxter drew $757 million against a $600 million cap and Brandywine $350 million against $120 million.'), ('$1.76tn', "US investment grade issuance for 2026 through October 26, the day it passed the 2020 record, running 29 percent ahead of last year's pace. Bloomberg's count. Tenders are the other side of that supply.")]) + '</div>' +
            P("The split between the two groups is the main finding. A tender that expires in five business days with no early deadline is a refinancing, in which the issuer prices a new bond the same week, uses the proceeds to retire the old one and does not need holders to deliberate. Eight of the releases state this directly by tying the tender to new notes. A tender that runs four weeks with an early premium, a consent fee or an exchange ratio asks holders to make a decision, and the issuer pays for the time.",
              "In a year when investment grade supply passed $1.76 trillion in October, most of the tenders the tracker reads are the fast kind, and most of the caps are under a billion dollars. That pattern reflects issuers addressing near maturities with inexpensive new money and does not point to distressed exchanges. The nine slower offers are where the credit analysis matters most.",
              "Everything above is the rules' reading of the filings as of November 3, with the error rates stated in the section before this one. The 14 hand rows are not in these counts. I would want the caps checked by a person before anyone relied on them to trade.")),
           ("How it is built", "Two stages, no paid services",
            bul(["A fetch step searches EDGAR full text search for tender and exchange offer press releases, then PR Newswire and Bing News for releases that never reached EDGAR, and caches the text.",
                 "An offline rules step extracts offer type, securities, cap and dates, then groups releases into offers.",
                 "A GitHub Actions job runs both every morning and publishes the page. It costs nothing to run."]))], banner=("assets/banners/tender.jpg", "Filings and releases the tracker read, by day, July 29 to October 27. Orange is a step in a tender or exchange offer, grey is everything else."))

# ---------- dashboard ----------
case_page("dashboard.html", "Morning Market Dashboard", "A market dashboard that scores whether the new issue window is open, built in R from free data.",
          "Project, live", "Morning Market Dashboard", "Personal project. June 2026 to now.",
          "A single screen that addresses one question each morning, which is whether the new issue window is open.",
          [("In short", "The question, the method, the finding, and what it means",
            story("When the score says the window is shut, is the next week actually worse, and do fewer deals price?",
                  "The seven rules rebuilt from FRED and Yahoo closes for every morning from October 2024 to November 2026, 538 mornings, then matched against the next five days of spread moves and a public count of pricing term sheets filed on Form FWP.",
                  "The score read challenging on 14 mornings, 10 of them in the April 2025 tariff week. Term sheets ran at about half the normal rate on those days. However, spreads were tighter a week later on 13 of the 14. The score therefore signals at the peak, after the move has occurred.",
                  "The score describes current conditions and does not forecast them. It confirms that the window is shut on days when that is already visible on a screen, and it has not given a warning the week before. The more useful signal runs the other way, because the morning after a challenging reading has been followed by tighter spreads 13 times out of 14.")),
           ("What it does", "A score built from the inputs a syndicate desk watches",
            P("It reads Treasury yields, credit spreads, volatility and macro data from free sources and scores the window from VIX, MOVE, the one week move in IG and HY spreads, stock futures and where spreads sit in their one year range. It is built in R and rebuilds several times a day on weekdays.") +
            '<p class="links"><a href="https://ferrierotony-cmyk.github.io/market_dashboard/">Open the dashboard</a> &nbsp;&middot;&nbsp; <a href="%s" rel="noopener">Code</a></p>' % REPO +
            '<a class="shot" href="https://ferrierotony-cmyk.github.io/market_dashboard/"><img src="https://ferrierotony-cmyk.github.io/market_dashboard/market_dashboard.png" alt="Dashboard snapshot: Treasury curve, 2, 10 and 30 year history, curve slope and credit spreads" loading="lazy" onerror="this.parentNode.style.display=\'none\'"></a><p class="note">The snapshot is rebuilt with the dashboard on weekdays.</p>'),
           ("Does the score mean anything", "I tested the score, and it measures conditions without predicting them",
            '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in [('538', 'Mornings scored, October 10, 2024 to November 2, 2026, the span where every input has public history. Open on 76 percent of them, selective on 21, challenging on 3. Two mornings in five scored a perfect seven.'), ('14', 'Mornings the score read challenging. Ten were April 4 to 22, 2025, the tariff week, when investment grade spreads went from 94 to 121 bp. The others were two in March 2025, August 4, 2025 and March 13, 2026.'), ('13 of 14', 'Challenging mornings that were followed by tighter investment grade spreads over the next five trading days, by 4 bp on average and 22 bp in high yield. The one miss was April 4, the first day of the shock.'), ('1.3 a day', 'Pricing term sheets filed on Form FWP on challenging mornings, against 3.0 on open ones. On April 4, 7 and 9, 2025 there were none. Across all 538 mornings the score has no rank correlation with the count, rho 0.04.'), ('19 of 409', 'Open mornings followed by a 5 bp or wider move in investment grade spreads within a week. The score did not warn before any of them. It has flagged a widening only after the fact and never in advance.'), ('Friday', 'The day of the week moves the term sheet count more than the score does: 1.4 filings on a Friday against 3.5 midweek. An issuance model that ignores the calendar will mostly capture noise.')]) + '</div>' +
            dfig([("dash_backtest.png", "The score against the spread it reads", "Orange marks the 14 challenging mornings. They sit at the top of the April 2025 spike and do not precede it. The lower panel is the daily count of pricing term sheets on Form FWP, a public proxy for investment grade supply.", True)]) +
            P("I built the score to answer a question every morning, and for a year I did not check whether the answer carried any information. I therefore rebuilt the seven rules from public history for every morning since October 2024 and asked two questions. When the score reads challenging, do spreads widen over the following week, and do fewer deals price?",
              "The answer to the second question is a weak yes. On the 14 challenging mornings the market filed about half as many pricing term sheets as usual, and on the three worst days of April 2025 it filed none. The answer to the first question is no, and it is the more informative of the two. Spreads were tighter a week after 13 of the 14 challenging mornings. The score is built from the one week change in spreads, so it cannot signal until the widening has already happened, and by then the following week is typically the recovery. In April 2025 investment grade peaked at 121 bp on April 9, the morning the score hit zero, and was 8 bp tighter five trading days later.",
              "In that sense the score works like a thermometer. It reports that the window is shut on mornings when a desk already knows it, and it has not once signalled shut before a widening. The more useful signal turns out to run the other way. The morning after a challenging reading has been followed by tighter spreads 13 times out of 14. If I added a fourth state to the scorecard it would be reopening, and it is the one I would most want to see.",
              "The test has clear limits. Fourteen events is a small sample, and ten of them fall in a single week. The term sheet count captures about three filings a day against the ten or so deals the market prices, so it should be read as a proxy and not as a full tally. The MOVE index and the stock futures only have two years of public history, which is why the test starts in October 2024 and not earlier. The scoring uses the prior day's closes, which is what the dashboard sees at 7am. The backtest code is in the repo.")),
           ("What to know", "Free data only, and a sample portfolio",
            P("The public build uses free data feeds only. The portfolio panel on the public build is a sample book and is labeled as one. A private version on my laptop pulls Bloomberg data through the API, with ten panels on the Treasury curve, DV01, P&amp;L and credit spreads, and refreshes every morning. That version is not published."))],
          banner=("assets/banners/rates.jpg", "The 10 year Treasury and the Baa spread since 2015, two of the inputs behind the window score. FRED data."))

# ---------- fed liquidity lab ----------
case_page("lab.html", "Fed Liquidity Lab", "A weekly tracker of the Fed's balance sheet, inflation and output, with rules tested against buy and hold on public data.",
          "Project", "Fed Liquidity Lab", "Personal project. November 2026. Public data only.",
          "Net liquidity is the Fed's balance sheet less the Treasury's cash account and the overnight reverse repo facility. Many people watch it as a guide to risk assets. I built a tracker for it, then tested whether it works.",
          [("In short", "The question, the method, the finding, and what it means",
            story("Does net liquidity, with inflation and output, tell you when to hold less stock and more cash?",
                  "The test uses FRED data only. I began with eighteen rules and then wrote a second design, which I documented and locked before running it. Every week is tested with only the data that had been published by then, net of trading costs, against buy and hold.",
                  "It does not. From 2020 the 18 rules returned 6.0 percent a year against 8.1 percent for buy and hold. The second design lost less in 2008 but failed its own test, because its edge over a plain mix of the same weights could not be distinguished from zero.",
                  "Net liquidity is a reasonable gauge of conditions and a poor timing signal. I would monitor it, but I would not trade on it. The most durable part of the project is the testing framework.")),
           ("What it does", "A weekly tracker with alerts",
            P("It pulls the Fed's balance sheet from FRED every week and works out net liquidity. It tracks seven measures of consumer inflation and the main gauges of output. Every series is checked for gaps, stale data and odd prints before anything uses it.",
              "A rules engine sends me a desktop alert when a trigger is crossed. A calendar tells me the day before CPI, the jobs report and a Fed decision.",
              "The scenarios replay what the balance sheet did in March 2020 and in mid 2022 and apply those dollar flows to today's levels. In the 2020 replay the Fed adds $2.8 trillion of assets and the Treasury takes $1.3 trillion into its cash account, so net liquidity rises $1.5 trillion, or 26 percent. These scenarios are historical analogues and should not be read as forecasts.") +
            '<p class="links"><a href="%s" rel="noopener">Code</a></p>' % LAB_CODE +
            dfig([("lab_liquidity.png", "Net liquidity, and what two past episodes would do to it", "Left, net liquidity and Fed assets since 2021. Right, the next 26 weeks if the balance sheet moved as it did in March 2020 and in mid 2022. Source: FRED.", True),
                  ("lab_inflation.png", "Inflation, seven ways", "Left, year over year. Right, 3 month annualized, the pace that matters for the next decision. The dotted line is the 2 percent target. A break in a line is a month the BLS never published. Source: FRED, Cleveland Fed.", True)])),
           ("What the tests say", "Two designs against buy and hold",
            '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in [
                ('6.0%', 'A year for the 18 rules since 2020, against 8.1 percent for buy and hold. They held less stock, and the timing cost about another point on top of that.'),
                ('4.3 pts', 'What the Sahm recession rule cost, the most of any rule. It turned on after the 2020 crash and stayed on through the rebound.'),
                ('3 of 4', 'Pre-registered criteria the second design passed. It cut the worst drawdown from 24.2 to 17.9 percent over 2006 to 2019. It failed the most important one, which asks whether its edge over a matched static mix is above zero. The interval ran from minus 0.3 to plus 1.5 percent a year.'),
                ('6.6 pts', 'How far the second design beat the same mix rebalanced in 2008. In the other 13 years it was about a third of a point a year behind.'),
                ('1.2', 'The best t-stat the allocator reached out of sample, on stocks. It only tilts at 2 or more, so it holds the neutral mix.')]) + '</div>' +
            dfig([("lab_backtest_v1.png", "The 18 rules against buy and hold", "Orange is the rules. White is buy and hold of a 50 / 30 / 10 / 10 mix of stocks, Treasuries, credit and cash. Net of 5 bps costs. Source: FRED.", True),
                  ("lab_backtest_v2.png", "The locked design on a clean window", "Written down and hashed before it was tested, on 2006 to 2019, with the Nasdaq Composite standing in for stocks. It cut the 2008 loss and ended slightly ahead of buy and hold, but the gap is inside the noise. Source: FRED.", True)]) +
            P("The first set of rules reflected my own view of what the data should say. It had eighteen nodes, several of them slow to react. My reading is that they stayed defensive through rebounds, which is consistent with what the Sahm rule did after 2020.",
              "The second design used four fast nodes with thresholds taken only from the trailing three years, and I fixed the pass and fail criteria before running it. Locking the design in advance matters, because with only a few years of data and many ways to cut it, almost any strategy can be made to look good after the fact.",
              "The design failed, and I left it unchanged. Even a pass would have led only to paper trading it forward, and not to trading real money.")),
           ("How it is built", "Public data, tests and a lock",
            bul(["Every series is declared once with its frequency, publication lag and plausible range. The pipeline caches it, records where it came from, and holds back anything that was not public yet on the date being tested.",
                 "Growth rates count calendar months. The October 2025 CPI was never published, and counting rows instead of months made headline CPI look 0.3 points too high.",
                 "The second design was hashed before it was tested, and the script refuses to run if the file has changed.",
                 "More than 140 tests cover the point in time logic, the alerts and the backtest, including checks that changing the future cannot change the past."])),
           ("What it does not show", "The limits of the analysis",
            P("Stocks are price only. Treasuries and credit are duration proxies with no defaults. The clean window uses the Nasdaq Composite as its equity sleeve, because FRED carries the S&amp;P 500 only from late 2016. The 2020 to 2026 window is one bull market and one drawdown, so it cannot prove much either way, and I designed the second test after seeing it.",
              "CPI, GDP and a few other series are used as last revised, not as first published, so some revision look ahead remains. Real vintages need an API key I have not used yet.",
              "Nothing here is investment advice. Data from FRED at the Federal Reserve Bank of St. Louis, the Cleveland Fed, the Atlanta Fed and the NY Fed. No Bloomberg data and nothing from an employer."))],
          banner=("assets/banners/lab.jpg", "Net liquidity, orange, and the Treasury General Account, grey, 2021 to 2026. FRED data."))

# ---------- roles ----------
case_page("finsight.html", "Finsight", "Debt Capital Markets Analyst Intern at Finsight, December 2025 to September 2026.",
          "Role", "Finsight", "Debt Capital Markets Analyst Intern. New York. December 2025 to September 2026.",
          "Finsight is a fintech platform that tracks the primary bond market for bankers and investors. I was responsible for collecting order book updates on new deals.",
          [("The job", "Collecting order books",
            P("Syndicate desks run the order book on every new bond deal, and none of them is obliged to share what is in it. I called and messaged desks at 30 plus investment grade and high yield banks for book sizes as deals moved from talk to guidance to launch, and then published the figures to the bankers and investors on the platform before the next update arrived. I covered fifteen to twenty deals a day.",
              "Once a relationship is established, the information comes more quickly. None of those bankers owed me anything, and that was the most instructive part of the role.")),
           ("A day on the desk", "A normal day, hour by hour", day_html()),
           ("High yield, then investment grade", "Two desks, two different markets",
            P("I covered high yield in the spring, where every deal turns on the company, its covenants, its call structure and the use of proceeds. I moved to investment grade over the summer, where issuers are large and frequent, spreads are tight and much depends on choosing the right window.")),
           ("Deals I covered", "Transactions that stayed with me",
            bul(["<b>Alphabet's $25 billion offering</b>, ten tranches out to 40 years, book around $115 billion. It was notable because a company that had always funded itself from cash was borrowing for data centers. I followed that book throughout the day.",
                 "<b>The Paramount Skydance exchange and tender offers.</b> Consent solicitations, exchange offers into second lien notes, and cash tenders on the 2027 and 2028 notes. I wrote the wire headlines on the liability management flow, 25 plus deals across tenders, exchanges and consents. That work led directly to the tender tracker and the Skydance DCF.",
                 "<b>Relative value comps.</b> Screens on tenor, rating and spread to gauge new issue concession, sent out with the deal terms."])),
           ("The tenor screens", "Where does this print sit against every comparable deal since 2022?",
            P("I maintained ten daily screens showing the lowest spreads and lowest coupons printed in the 3, 5, 7, 10 and 30 year, covering every investment grade deal back to 2022 by week, month and year, with issuer, ratings, size, call, final book, coupon, yield and spread on every row. A check sheet held any prints that looked wrong until I had confirmed them.",
              "When a banker asked how a new 5 year compared, the answer was on a single screen. In practice, concession is judged by comparing one deal with a large set of others and not by applying a formula.")),
           ("The end of day tally", "What priced, where it came from, and how far it moved",
            P("Every afternoon the day's investment grade prints went into one table: issuer, rating, size, tenor, final book, leads, price talk, where it priced, the move from talk to print, and the identifiers. That table is where the morning wire's numbers came from.")),
           ("Volume against the Street", "Did the month come in where the desks said it would?",
            P("I tracked issuance volume against the Street's estimates by day, week and month, with deal counts, tranche size, talk to print, final book, attrition, concession and end of week trading. The daily sheet went back years, with holidays, zero days and Fed days marked. It is the table to consult when someone claims that issuance stops in August.")),
           ("Backfilling the database", "Checking 2019 Latin America deals one by one",
            P("The platform's history had gaps. I checked a list of 2019 Latin American deals one by one against what the platform had and returned the missing, incorrect and doubtful entries as a task list. The work was routine, but it is the kind of checking that makes a dataset worth paying for.")),
           ("What I did on my own time", "Approaching the internship as a full time role",
            bul(["I reached out to the syndicate bankers I was collecting books from, at BBVA, Scotiabank and HSBC, to learn how they read demand and set concession. I still speak regularly with three of them.",
                 "I taught myself the Bloomberg API in R and built the first version of the market dashboard, so that I could review the curve, DV01, spreads and new issue comps every morning.",
                 "I travelled to New York in July at my own expense to work from the office for a few days and meet the team in person."])),
           ("Since Finsight", "ICE Fixed Income Forum at the NYSE, October 2026",
            P("ICE Fixed Income Forum at the New York Stock Exchange, October 21, 2026.") +
            photos([("nyse-stage", "On stage at the NYSE after the forum, October 21, 2026.", "wide"), ("nyse-podium", "The podium.", "tall"), ("nyse-seated", "The panel chairs, after the panel.", ""), ("nyse-podium-side", "Getting a feel for the room.", "tall")]))], banner=("assets/banners/d-finsight.jpg", "Illustration of an order book from price talk to print. Not a real deal."))
tc_stats = [
    ("$1M", "Virtual starting capital for each team. The book is long only and limited to single name stocks from the WLS index, with no ETFs and no leverage."),
    ("WLS", "The benchmark is the Bloomberg World Large, Mid and Small Cap Price Return Index. Teams are ranked on relative P&L against it and not on raw return, so in a falling market a team can win by losing less than the index."),
    ("20%", "The largest share of the book that any one position may hold. We set our own cap lower so that a single poor position cannot determine the result."),
    ("2,600+", "Teams in the fall 2025 edition, with more than 11,000 students from 50 countries and 72,000 virtual trades. The grand prize team returned more than 400 percent."),
    ("8 weeks", "The approximate length of the trading cycle. Winners are announced around the end of November, so most of the return has to come from events that occur inside the window."),
    ("Oct 12", "The day our book opened for the fall 2026 round."),
]
tc_stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in tc_stats) + "</div>"
case_page("bloomberg.html", "Bloomberg at UMass Lowell", "Bloomberg Terminal Assistant at UMass Lowell since September 2026, and captain of the UML team in the Bloomberg Global Trading Challenge.",
          "Role", "Bloomberg at UMass Lowell", "Terminal Assistant, September 2026 to now. Trading Challenge captain, fall 2026. Investment Analyst, spring 2026 round.",
          "I train business school students on the Bloomberg Terminal, pull data for faculty research, and captain the UML team in the Bloomberg Global Trading Challenge. Both roles use the same room and the same terminals, but they are two different jobs.",
          [("Terminal Assistant", "Training and data pulls",
            bul(["I train business school students across 10 classes on functions from SRCH and YAS to curves and spreads, including bond screens, yield and spread checks and company financials.",
                 "I pull Bloomberg data for faculty research and class assignments. The green bond research on this site began as one of those requests."])),
           ("One pull in detail", "ESG scores for 2,172 US listed companies",
            P("A professor asked whether the terminal had ESG scores. I screened every US listed company with a Bloomberg ESG score, pulled ten years of history plus the current MSCI, Sustainalytics and S&P scores, and sent a values only file with a field guide tab. I made two mistakes before getting it right. The first list was built by hand and contained duplicate tickers, and the first file still had live Bloomberg formulas in it.")),
           ("The Trading Challenge", "A university competition run entirely inside the terminal", tc_stat_html +
            P("Scoring on relative P&L against the WLS index changes the approach. Beating a falling index by holding up is worth as much as beating a rising one by running ahead of it.",
              "UMass Lowell's teams are run by Professor Weicker. I was an analyst on the spring 2026 round and I captain the fall 2026 team.")),
           ("How I run the team", "Four lanes and a rule set written down before the first trade",
            bul(["<b>Lanes.</b> I own the book, the final decision on every trade and the sizing. Two analysts pitch names with a one line summary covering what the company is, why now, the catalyst and its date, and what would invalidate the idea. One member keeps the trade log and another owns the earnings calendar.",
                 "<b>Entry rule.</b> We only buy a stock that is above its open and beating the WLS benchmark that morning. We do not buy names that are falling.",
                 "<b>Sizing and exits.</b> We keep position caps below the 20 percent limit and write down an exit for every name before it enters the book. The log records the reason for every trade.",
                 "<b>The screens.</b> EQS for candidates, EE and ANR for what is priced in, the earnings calendar, N and CN for news, GP for charts, PORT for exposures. My R dashboard points at the book for the daily snapshot."])),
           ("The book so far", "Two energy names and four passes",
            P("On October 12 we bought Exxon and Chevron after oil rebounded. We passed on Goldman Sachs, Nvidia, ASML and General Dynamics the same week, and General Dynamics missed the entry rule by 39 cents on October 15. We stayed out of technology after the high CPI and PPI prints and the selloff in chip stocks, which is the decision I would defend most strongly. Chevron's exit is written down at $225, or earlier if Brent falls below $102.",
              "I do not post a running return here. The result will be published when the window closes, whatever it is.")),
           ("What past winners did", "Volatility backed by a thesis",
            P("What past winners have in common is a focus on earnings and catalysts inside the window, as opposed to safe long term holdings. RIT's 2024 team leaned into volatility and foreign names. USF's 2025 captain ran an earnings volatility book. The fall 2025 grand prize team from the Chinese University of Hong Kong won on discipline and Bloomberg's own data.",
              "The cautionary example is a team that took a large early bet, rose 18 percent, moved to cash and was not invited to the finals because the judges decided it was not investing. For that reason every name in our book has a written thesis, and the log is kept to a standard that would hold up to a judge's review.")),
           ("What I am learning", "Equities are not my home market",
            P("My background is in bonds. A long only equity book scored against an index is a different discipline, and two weeks of it taught me more about sizing and about passing on a trade than anything I had read. The rule that kept us out of technology during CPI week is now the example I give when asked about risk management.")),
           ("Sources", "Where the competition facts come from",
            '<p class="note">Bloomberg press release on the fall 2025 edition, January 2026. Bloomberg for Education challenge page. TUM School of Management challenge page for the 2026 format. Our rules, trades and passes are from my own trade log.</p>')], banner=("assets/banners/d-bloomberg.jpg", "Ten classes and the Trading Challenge book. Drawn from the numbers on this page."))
wacc = [
    ("4.2%", "Risk free rate, the Treasury yield on the October 31, 2025 valuation date."),
    ("1.16", "Beta. Eleven public engineering and construction companies screened down to the four with clean five year data, median unlevered beta 1.14, relevered for the company's small debt."),
    ("5.0%", "Equity risk premium, the Kroll recommended figure on the valuation date."),
    ("7.06%", "The size premium, from the Kroll microcap decile. It is the largest single judgment in the build, and without it the value would nearly double."),
    ("0%", "Company specific premium. The named risks were priced into the forecast instead, by cutting management's growth. Adding a premium too would count the same risk twice."),
    ("16.8%", "Weighted average cost of capital, 97.7 percent equity at 17.06 percent and 2.3 percent debt at 5.93 percent after tax."),
]
wacc_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in wacc) + "</div>"
case_page("valuation.html", "2026 Valuation Challenge", "Valuation Analyst on the UMass Lowell team in the 2026 Business Valuation Challenge: discount rate, DCF, LBO and public comparables.",
          "Competition", "2026 Valuation Challenge", "Valuation Analyst. UMass Lowell team led by Professor Sangphil Kim. September to October 2026.",
          "We valued 100 percent of a $132MM revenue Gulf Coast engineering contractor, an owner operated S corporation, for an ESOP acquisition at fair market value. I was responsible for the discount rate, the DCF, the LBO and the public comparables.",
          [("In short", "The question, the method, the finding, and what it means",
            story("What is a $132MM revenue, owner operated contractor worth to an ESOP buying 100 percent of it at fair market value?",
                  "A discount rate built in layers to 16.8 percent, a five year DCF tested by perpetuity and exit multiple, an LBO as a buyer's check, and public peers used for beta only.",
                  "The two DCF methods landed within half a million dollars of each other, and the LBO ceiling landed close to the DCF. The 7.06 percent size premium is worth about five turns of EBITDA and is the whole gap between public and private multiples.",
                  "Public multiples say little about a control sale of a private contractor with two owners, so they received zero weight. The value is set by what a surety and a lender would support, and not by where a listed peer trades.")),
           ("The competition", "A 25 minute recorded valuation, no questions allowed",
            P("The competition is run out of Georgia State University. Round 1 is a recorded presentation of up to 25 minutes with no live questions, and the top five teams advance to the in person final. We submitted on October 19, 2026.",
              "Because there is no question period, every judgment has to be justified within the video. Each of my four slides is built to answer the question a judge would otherwise ask.")),
           ("My four slides", "Risk, value, a buyer's check, and what public peers can and cannot tell you",
            bul(["<b>Discount rate.</b> What return does a buyer need to own this risk? I built the cost of capital in layers and landed at 16.8 percent.",
                 "<b>Discounted cash flow.</b> What are the cash flows worth at that rate? A five year forecast to 2031, tested two ways, growing forever at 2 to 3 percent or selling at 4.5 to 5.5 times EBITDA. The two methods landed within half a million dollars of each other.",
                 "<b>Leveraged buyout.</b> Could a real buyer pay that? I modeled a private equity purchase at 2.5 times EBITDA of debt, kept low because a bonded contractor cannot carry heavy leverage, and solved for the most a fund could pay at its target return. It landed close to the DCF, so the LBO became a floor and a check, with zero weight in the conclusion.",
                 "<b>Guideline public companies.</b> What do public peers tell you? They indicate risk more reliably than price. I used the peer set for beta only. Companies worth $4.7 billion to $16.8 billion with hundreds of projects and liquid stock say little about a control sale of a private contractor with two owners, so their multiples carried zero weight."])),
           ("The discount rate build", "Six inputs and one big judgment", wacc_html +
            '<ul class="figs"><li class="full light"><figure><a class="img" href="assets/figures/val_discount_rate.png"><img src="assets/figures/val_discount_rate.png" alt="Discount rate slide: cost of debt 5.93 percent after tax, cost of equity 17.06 percent, WACC 16.80 percent" loading="lazy"></a><figcaption><b>The slide as submitted</b>My discount rate page from the deck. The company, its figures and the conclusion stay off this site.</figcaption></figure></li></ul>' +
            P("The 7.06 percent size premium is worth about five turns of EBITDA. Without it the implied multiple goes from about 5 times to about 10, which is the whole gap between where public peers trade and where private contractors this size sell. That is why the public multiples received zero weight.")),
           ("Where I disagreed with management", "The disagreement was about growth",
            P("Management projected revenue growth of 6.5 to 7.5 percent a year. The company had missed its own 2025 budget by 14 percent and new orders had been flat for two years. I accepted 2026 because backlog supported it, then faded growth to 2.5 percent by 2031. The entire difference between our value and management's case comes from that growth assumption and none of it from margins. The DCF runs on a 6.5 percent mid cycle margin, which represents a normal year and not a good or bad one.")),
           ("What I would do differently", "Three things the judges could have pushed on",
            bul(["<b>Four betas is thin.</b> Four clean betas beat eleven noisy ones, but every reasonable change to the beta still kept the value inside our range, and I should have shown that range on the slide.",
                 "<b>The 10 year or the 20 year Treasury.</b> Kroll pairs its 5 percent premium with the 20 year yield, which was 4.65 percent. Using it would have raised the WACC to about 17.2 percent and cut the value by about $1.4 million, still inside the range. I used 4.2 percent and should have footnoted the choice.",
                 "<b>Bonding caps leverage harder than I modeled.</b> At 2.5 times EBITDA the contractor's tangible net worth goes negative, which a surety would not accept. A 1.5 times case changes the LBO ceiling by a few million and does not change the conclusion, but it is the more defensible figure."])),
           ("Process", "Three mock presentations and a content freeze",
            P("We held three mock presentations between September 18 and early October, froze the content on October 9 and recorded on October 10 and 11. My segment ran six minutes fifty in the second mock against a target of four and a half, so I spent the last two weeks tightening the script and added no new analysis.",
              "The company and the data room are confidential, so the dollar figures stay off this page. The method and the judgment calls are mine."))], banner=("assets/banners/valuation.jpg", "The cost of capital build, from a 4.2 percent risk free rate to a 16.8 percent WACC. Every input here is already on the public slide."))
open(os.path.join(OUT, "trading.html"), "w", encoding="utf-8").write('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=bloomberg.html"><title>Bloomberg Global Trading Challenge | Anthony Ferriero</title><link rel="canonical" href="bloomberg.html"></head><body><p>Moved to <a href="bloomberg.html">Bloomberg at UMass Lowell</a>.</p></body></html>')
case_page("finance-society.html", "UML Finance Society", "President of the UML Finance Society since April 2026.",
          "Leadership", "UML Finance Society", "President. April 2026 to now.",
          "I lead a nine person executive board for a student finance club of over 500 members.",
          [("What changed", "500 members, a nine person board and well attended events",
            '<img class="logo" src="assets/umlfs-logo.svg" alt="UMLFS, UMass Lowell Finance Society" width="520" height="150">' +
            P("I became president in April 2026. Membership has grown by 200+ to over 500. The e-board has nine members, and each is responsible for an area such as events, merchandise, partnerships or the newsletter. My role is largely to choose the right people and give them room to do the work.")),
           ("This fall", "Six events in six weeks",
            bul(["<b>September 21.</b> From Gold to Tokens, with Professor Ravi Jain and the Donahue Center for Business Ethics. The talk covered the history of money from Babylon to AI, with Chipotle provided, and was open to every major.",
                 "<b>September 22.</b> Boston Fintech Week at the Federal Reserve Bank of Boston. Ten of us attended the opening day, on a school shuttle that I arranged for the dean's office to fund.",
                 "<b>September 25.</b> The Fintech That Thinks career summit at the Boston Fed, open to all finance students on a second bus.",
                 "<b>October 1.</b> Develop Your Corporate Financial Acumen with Kim Kinsley of Pratt &amp; Whitney, co-hosted with the DifferenceMaker Institute.",
                 "<b>October 28.</b> Link Up, a LinkedIn workshop in the Bloomberg Terminal room, held jointly with the Real Estate Club. It offered free headshots, a talk on how to set up a profile and live reviews of members' profiles on the screen.",
                 "<b>Fall.</b> The Bloomberg Global Trading Challenge, with practice time booked in the terminal room."])),
           ("What I am building for after me", "An analyst group the next board runs",
            P("The group produces a weekly market newsletter and a case every three weeks. It is run by the two youngest e-board members and has four new analysts, and the top case team is recognized on LinkedIn. The aim is to give members who want an e-board seat a way to earn one, and to ensure the club does not depend on whoever is president.")),
           ("Photos", "This fall so far",
            photos([
                ("fintech-rooftop", "The group on the roof of the Federal Reserve Bank of Boston on the opening day of Boston Fintech Week, September 22.", "wide"),
                ("fintech-rooftop-2", "Another rooftop shot from Boston Fintech Week.", "sq"),
                ("fs-group", "The group at a Finance Society event by the water.", "wide"),
                ("fintech-career-summit", "Crack the Fintech Career Code, the student panel at the Boston Fed.", "sq"),
                ("babylon-podium", "Opening the evening, which covered Babylon to blockchain in 75 minutes, with Chipotle.", "tall"),
                ("babylon-talk", "Babylon to Blockchain, presented by Professor Ravi Jain, September 21. I opened the night.", "tall"),
                ("club-fair", "The involvement fair table in the Honors College, with the Resume Recharge and Babylon flyers.", "tall"),
                ("fs-social", "Members at a Finance Society event.", "wide"),
                ("fs-lunch", "At a Finance Society event with a member.", "sq"),
                ("guest-speaker", "A guest speaker session with Bob Landry, CFA, CAIA, Senior Director, Investments and Retirement at H-E-B.", "wide"),
                ("babylon-panel", "With Professor Ravi Jain and the Donahue Center team before From Gold to Tokens, September 21.", "sq"),
            ]) + photos([
                ("resume-recharge-1", "Resume Recharge, with the Finance Society among the hosts.", ""),
                ("resume-recharge-2", "Resume Recharge, with the Finance Society and campus partners.", ""),
            ], " duo")),
           ("Partnerships", "Getting members in rooms they could not get into alone",
            P("I am working to bring UMass Lowell into the Mass Fintech Hub so that the Boston Fintech Week tickets become an annual arrangement. I am also in contact with CFA Society Boston about access to their events for members, and I am arranging alumni site visits, starting with a trip to New York."))], banner=("assets/banners/d-finance-society.jpg", "The dated events of the fall, then the Trading Challenge running under all of them. Drawn from the list on this page."))
case_page("sales-team.html", "UML Intercollegiate Sales Team", "Captain of the UML Intercollegiate Sales Team since November 2025.",
          "Leadership", "Intercollegiate Sales Team", "Captain. November 2025 to now.",
          "The team placed in the top four at a national competition. I captain the team and lead preparation on pitching and handling objections.",
          [("Results", "Where the team placed",
            bul(["Love's Travel Stops national sales competition, Oklahoma City. The team placed in the top four.",
                 "March 26, 2026. Fourth in Speed Sell at the Challenger Sales Institute invitational, with two UMass Lowell placings that day."])),
           ("What I run", "Prep and the sponsor list",
            P("I lead preparation on pitching and objection handling. I also keep the list of competitions and sponsors we bring to our advisors each year.")),
           ("Photos", "Competition days",
            photos([
                ("sales-award", "Speed Sell, fourth place, at the Challenger Sales Institute invitational, March 26, 2026.", "tall"),
                ("sales-certificates", "Two UMass Lowell placings on the same day.", ""),
                ("sales-comp-day", "Competition day in the Manning School, April 2026.", "tall"),
            ]))], banner=("assets/banners/d-sales-team.jpg", "The team placed top four. Drawn, not a photo."))
case_page("ccr.html", "Commonwealth Capital Research", "Research Analyst at Commonwealth Capital Research since February 2024.",
          "Role", "Commonwealth Capital Research", "Research Analyst. February 2024 to now.",
          "I write the rates and credit section of a newsletter with about 200 subscribers.",
          [("What I do", "Newsletter and research",
            '<div class="logo-row"><img src="assets/ccr-logo.png" alt="Commonwealth Capital Research logo"><p class="note">Commonwealth Capital Research is a student run research group.</p></div>' +
            bul(["I write the rates and credit section of the newsletter, which has about 200 subscribers.",
                 "A SpaceX IPO report, co-written with a colleague from the group.",
                 "An oil market piece that is in progress. It tracks how the Middle East risk premium faded through 2026."])),
           ("The curve", "What the rates section is about",
            '<figure class="banner"><img src="assets/banners/curve.jpg" alt="The Treasury curve at each year end since 2018 in grey and the latest curve in orange" loading="lazy"><figcaption>The Treasury curve at each year end since 2018, grey, and the latest, orange. FRED data.</figcaption></figure>' +
            P("The newsletter's rates section follows the shape of this curve and the credit spreads on top of it. The inversion that began in 2022 and the way it unwound has been my main subject for two years.")),
           ("Photos", "Fireside chat",
            photos([("ccr-elward", "With Nick Elward of Natixis after the Commonwealth Capital Research fireside chat.", "tall")]))], banner=("assets/banners/d-ccr-news.jpg", "The layout of the newsletter's rates and credit section. An illustration, not an issue."))
case_page("consulting.html", "Mill City Consulting", "Research and due diligence for a UMass Lowell student consulting client.",
          "Project", "Mill City Consulting", "Research and due diligence lead. UMass Lowell student consulting group.",
          "The client was a six lane duckpin bowling alley that has been open since 1931, with new owners and no financial system.",
          [("In short", "The question, the method, the finding, and what it means",
            story("Can two new owners run a 1931 duckpin alley as a business when it has no books, no website and machines older than they are?",
                  "Interviews with the owners, a revenue breakdown by line, and a five section question bank I wrote for the research and due diligence work: the business, operations, customers and market, pain points and goals.",
                  "Leagues were about 87 percent of revenue, parties 9 and food and drink 4. The owners had not seen that split before. The main risk was the pinsetting machines and not the market.",
                  "In effect this is a subscription business with a single point of failure. The profit and loss tracker gave the owners their first view of it, and the introduction to the engineering department addressed the equipment risk that could close it.")),
           ("The client", "Leagues, parties, and 1960s pinsetters",
            P("Two owners had recently bought the business. Leagues were about 87 percent of revenue, parties 9 and food and drink 4. Its strengths were its position as one of the last duckpin houses in the region, owners who do their own repairs and an active Facebook following. Its weaknesses were fragile sixty year old machines, no website and no formal books.")),
           ("What we built", "Visibility first",
            bul(["An Excel financial tracker with a live profit and loss, so the owners could see the business for the first time.",
                 "A QR code payment setup, a website, new signage and a brand story.",
                 "An introduction to the UML engineering department about the pinsetters."])),
           ("What I owned", "The question bank",
            P("My part was research and due diligence. I wrote the five section client question bank the group uses on new engagements: understanding the business, current operations, customers and market, pain points, and goals. I presented it to the next Mill City cohort in September 2026.")),
           ("Photos", "Presenting the work",
            photos([("class-presenting", "Presenting the research and due diligence template.", ""), ("class-team", "The team after the presentation.", "")]))], banner=("assets/banners/d-consulting.jpg", "Six duckpin lanes. A drawing, not the client's floor plan."))
case_page("education.html", "Education", "Business Administration at UMass Lowell, expected graduation May 2027.",
          "Education", "UMass Lowell", "Bachelor of Science in Business Administration. Expected May 2027.",
          "My concentrations are Finance and Marketing, with a minor in Quantitative Economics. My GPA is 3.6 out of 4.0.",
          [("Coursework", "Relevant classes", pills(["Financial Derivatives", "Financial Institutions and Markets", "Financial Statement Analysis"])),
           ("Certifications", "Credentials", pills(["Capital Markets and Securities Analyst, CMSA", "Bloomberg Finance Fundamentals", "Spreadsheet Analysis"]))], banner=("assets/banners/d-education.jpg", "Eight semesters, the seventh under way. Drawn, not a transcript."))
case_page("skills.html", "Skills", "Tools, models and data skills.",
          "Skills", "Tools and certifications", "Terminal, code, models and AI tools.",
          "What I use to read the bond market and to build and test the work on this site.",
          [("Technical", "Tools and data", pills(["Bloomberg Terminal", "BQL", "SRCH, YAS, DES, GC", "Refinitiv", "R", "Stata", "Excel", "DCF and LBO modeling", "SEC filings"])),
           ("Certifications", "Credentials", pills(["Capital Markets and Securities Analyst, CMSA", "Bloomberg Finance Fundamentals", "Spreadsheet Analysis"])),
           ("AI tools", "How I use them", pills(["Claude", "ChatGPT", "Microsoft Copilot", "Google Gemini"]) +
            P("I use Claude to help write and debug code and to screen first pass matches in the research. I test the results myself before relying on them."))], banner=("assets/banners/skills.jpg", "The screens and tools behind the work on this site."))
case_page("contact.html", "Contact", "Contact Anthony Ferriero.", "Contact", "Get in touch", "Lowell, Massachusetts.",
          "The fastest way to reach me is email. I reply to every message about fixed income, credit research, syndicate, debt capital markets or the tools on this site.",
          [("Where to find me", "Email first",
            '<div class="two"><div>' +
            '<div class="hero-cta contact-cta"><a class="btn primary" href="mailto:%s">Email me <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a><a class="btn outline" href="%s" rel="noopener">LinkedIn</a><a class="btn outline" href="%s" rel="noopener">GitHub</a></div>' % (EMAIL, LINKEDIN, GITHUB) +
            '<p class="note"><a href="mailto:%s">%s</a><br>Lowell, Massachusetts. I can be in Boston or New York on short notice.</p>' % (EMAIL, EMAIL) +
            P("I am seeking a 2027 analyst position in fixed income, in credit research, syndicate or debt capital markets, or an internship that leads to one. I graduate in May 2027.",
              "If you run a desk and would like to see the tender tracker or the dashboard in person, I would be glad to bring a laptop and walk through them.") + '</div>' +
            '<div><figure class="banner photo"><img src="assets/photos/careers-stairs.jpg" alt="Anthony Ferriero on campus"><figcaption>On campus.</figcaption></figure></div></div>')], banner=("assets/banners/d-contact.jpg", "Lowell, with Boston and New York as rings. Schematic, not to scale."))
# projects hub page
case_page("projects.html", "Projects", "Research, tools and models, each with its error rates published.", "Projects", "Projects", "Six case files, built on public data only.",
          "These projects cover the parts of the work of a credit analyst, a syndicate desk and a debt capital markets team that I can do with public data. They include five DCF models with a credit comparison, a study of green bond pricing, a tender offer tracker, a score for the new issue window and a test of whether Fed liquidity helps time the market.",
          [("Case files", "Research, tools and models", card_group(("Project",))),
           ("Competitions", "Where the models were tested", card_group(("Competition",)))], banner=("assets/banners/projects.jpg", "Investment grade spreads since October 2023, the backdrop every one of these tools reads. FRED data."))
# experience and leadership hub pages
case_page("experience.html", "Experience", "Roles, projects and competitions in order.", "Experience", "Experience", "Internship, campus roles and competitions.",
          "Everything is listed in date order with the most recent first, and each entry opens its case file.",
          [("Timeline", "Roles, projects and competitions", tl)], banner=("assets/banners/d-experience.jpg", "Every role on the site as a bar, January 2024 to now."))
lead = card_group(("Leadership",))
case_page("leadership.html", "Leadership", "Finance Society and Sales Team leadership.", "Leadership", "Leadership", "Two teams at UMass Lowell.",
          "I lead the Finance Society and captain the sales team.",
          [("Roles", "Finance Society and Sales Team", lead)], banner=("assets/banners/d-leadership.jpg", "Five hundred members, two hundred of them new, and a rank ladder. One dot is one member."))

open(os.path.join(OUT, "tokens.css"), "w", encoding="utf-8", newline="\n").write(TOKENS_CSS)
open(os.path.join(OUT, "style.css"), "w", encoding="utf-8", newline="\n").write(SITE_CSS + focal_css())
print("built", sorted(os.listdir(OUT)))
