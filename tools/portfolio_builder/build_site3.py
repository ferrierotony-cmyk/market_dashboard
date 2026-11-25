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
from widgets import EXPLORER, explorer_html, POWER_HTML, day_html
import json
from cine import split, page_head, fp, focal_css, vt, vt_css
import cine as _cine
_cine.AI_DIR = OUT

STYLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles")
TOKENS_CSS = open(os.path.join(STYLES, "tokens.css"), encoding="utf-8").read()
SITE_CSS = open(os.path.join(STYLES, "site.css"), encoding="utf-8").read()
# Browser chrome colour for the theme-color meta tag. Mirrors --color-slate-050 and --color-slate-950 in tokens.css.
THEME_LIGHT, THEME_DARK = "#faf9f5", "#141413"

NAV = [("index.html", "Anthony Ferriero"), ("projects.html", "Work"), ("experience.html", "Experience"), (LINKEDIN, "LinkedIn"), ("contact.html", "Get in touch")]
HUBS = ("projects.html", "experience.html", "leadership.html", "education.html", "contact.html")

HEAD_FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
              '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500&display=swap">')
JS = """(function(){var mb=document.getElementById('motion-btn');if(!mb)return;var root=document.documentElement;function sync(){var off=root.getAttribute('data-motion')==='off';mb.setAttribute('aria-pressed',off?'true':'false');mb.setAttribute('aria-label',off?'Turn motion on':'Turn motion off');}sync();mb.addEventListener('click',function(){var off=root.getAttribute('data-motion')==='off';if(off){root.removeAttribute('data-motion');}else{root.setAttribute('data-motion','off');}try{localStorage.setItem('af-motion',off?'on':'off');}catch(e){}sync();});})();
(function(){var bs=[].slice.call(document.querySelectorAll('.mode button'));var root=document.documentElement;var mq=window.matchMedia?matchMedia('(prefers-color-scheme: dark)'):null;function saved(){try{return localStorage.getItem('af-theme');}catch(e){return null;}}
function set(t){root.setAttribute('data-theme',t);bs.forEach(function(x){x.setAttribute('aria-pressed',x.getAttribute('data-mode')===t?'true':'false');});var m=document.querySelector('meta[name=theme-color]');if(m)m.setAttribute('content',t==='dark'?'%s':'%s');}
set(root.getAttribute('data-theme')==='dark'?'dark':'light');bs.forEach(function(x){x.addEventListener('click',function(){var t=x.getAttribute('data-mode');set(t);try{localStorage.setItem('af-theme',t);}catch(e){}var o=bs.filter(function(y){return y!==x;})[0];if(o&&!x.offsetParent)o.focus();});});
if(mq&&mq.addEventListener)mq.addEventListener('change',function(e){if(!saved())set(e.matches?'dark':'light');});})();
(function(){if(!('IntersectionObserver' in window)||matchMedia('(prefers-reduced-motion: reduce)').matches||document.documentElement.getAttribute('data-motion')==='off')return;
var els=[].filter.call(document.querySelectorAll('.section h2, .group, .cards > li, .figs > li, .photos > li, .mosaic > li, .more'),function(el){return el.getBoundingClientRect().top>window.innerHeight*.9;});
var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting||x.boundingClientRect.top<0){x.target.classList.add('in');io.unobserve(x.target);}});},{rootMargin:'0px 0px -80px 0px'});
els.forEach(function(el){el.classList.add('rv');io.observe(el);});})();
""" % (THEME_DARK, THEME_LIGHT)


# The motion switch also turns off the change from page to page.
FLOW_JS = """window.addEventListener('pagereveal',function(ev){if(ev.viewTransition&&document.documentElement.getAttribute('data-motion')==='off')ev.viewTransition.skipTransition();});"""


def e(s):
    return html.escape(s, quote=True)


def shell(fname, title, desc, main):
    def link(f, l):
        here = ' aria-current="page"' if f == fname else ' aria-current="true"' if f == "projects.html" and fname != "index.html" and fname not in HUBS else ""
        if f == "contact.html": l = '<span class="nav-full">%s</span><span class="nav-short">Contact</span>' % l
        if f == "index.html": l = '<span class="nav-full">%s</span><span class="nav-short">AF</span>' % l
        return '<li%s><a href="%s"%s%s>%s</a></li>' % (' class="nav-wide"' if f == LINKEDIN else "", f, here, ' rel="noopener"' if f == LINKEDIN else "", l)
    name, nav = link(*NAV[0]).replace("<li>", "").replace("</li>", ""), "".join(link(f, l) for f, l in NAV[1:])
    pageurl = "" if fname == "index.html" else fname
    live = '<script src="live.js" defer></script>' if "data-live=" in main else ""
    full_title = "Anthony Ferriero" if fname == "index.html" else "%s | Anthony Ferriero" % title
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="{THEME_LIGHT}">
<script>(function(){{var t=null;try{{t=localStorage.getItem('af-theme');}}catch(e){{}}if(t!=='dark'&&t!=='light'){{t=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}}document.documentElement.setAttribute('data-theme',t);var m=document.querySelector('meta[name=theme-color]');if(m)m.setAttribute('content',t==='dark'?'{THEME_DARK}':'{THEME_LIGHT}');}})();</script>
<script>try{{if(localStorage.getItem('af-motion')==='off')document.documentElement.setAttribute('data-motion','off');}}catch(e){{}}</script>
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://anthonyferriero.vercel.app/{pageurl}">
<meta property="og:image" content="https://anthonyferriero.vercel.app/assets/og-card-2.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(full_title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="https://anthonyferriero.vercel.app/assets/og-card-2.png">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="canonical" href="https://anthonyferriero.vercel.app/{pageurl}">
{HEAD_FONTS}
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="style.css">
<script>document.documentElement.classList.add('js');{FLOW_JS}</script>
</head>
<body class="{'home' if fname == 'index.html' else 'inner'}">
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="bar"><nav class="bar-nav" aria-label="Main"><span class="nav name">{name}</span><ul class="nav">{nav}</ul></nav><div class="nav mode" role="group" aria-label="Color mode"><button type="button" data-mode="light" aria-label="Light mode" aria-pressed="true" title="Light mode"><svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button><button type="button" data-mode="dark" aria-label="Dark mode" aria-pressed="false" title="Dark mode"><svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button></div></div></header>
<main id="main">
{main}
</main>
<footer class="site-foot"><div class="wrap">
  <div class="row"><span>&copy; 2026 Anthony Ferriero</span>
  <span class="foot-links"><a href="leadership.html">Leadership</a><a href="education.html">Education</a><a href="skills.html">Skills</a><a href="{GITHUB}" rel="noopener">GitHub</a><a href="mailto:{EMAIL}">Email</a></span>
  <div class="foot-tools">
  <button class="theme-btn motion-btn" id="motion-btn" type="button" aria-label="Turn motion off" aria-pressed="false" title="Motion on or off">
    <svg class="i-motion" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 9c3-3 6 3 9 0s6-3 9 0M3 15c3-3 6 3 9 0s6-3 9 0"/></svg>
    <svg class="i-still" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 9h18M3 15h18"/></svg>
  </button>
  </div></div>
  <p>Research figures are preliminary. Nothing here is investment advice or comes from an employer.</p>
</div></footer>
<script>{JS}</script>
{live}
</body>
</html>
"""


def strip(kind, head, foot="", co=""):
    """A live strip. Empty and hidden until live.js fills it, so a page without feeds loses nothing."""
    return '<div class="tape live" data-live="%s"%s><div class="tape-head"><span>%s</span><b class="live-when"></b></div><ul aria-live="polite"></ul>%s</div>' % (kind, ' data-co="%s"' % co if co else "", head, '<div class="tape-foot">%s</div>' % foot if foot else "")


def model_data(*names):
    """The model inputs the live strip needs, the same ones the calculator uses."""
    return '<script type="application/json" id="model-data">%s</script>' % json.dumps({n: EXPLORER[n] for n in names or EXPLORER}, separators=(",", ":"))


def model_strip(co):
    return model_data(co) + strip("model", "The price now, against the model", 'The model is from November 25, 2026. Only the price moves. <span data-flag="%s"></span>' % co, co)


def plot(kind, head, foot):
    return '<div class="tape live" data-live="%s"><div class="tape-head"><span>%s</span><b class="live-when"></b></div><div class="plot"></div><div class="tape-foot">%s</div></div>' % (kind, head, foot)


def P(*paras):
    return "".join("<p>%s</p>" % p for p in paras)


def photos(items, extra=""):
    out = '<ul class="photos%s">' % extra
    for f, cap, cls in items:
        out += '<li class="%s"><figure><a href="assets/photos/%s.jpg"><img src="assets/photos/%s.jpg" alt="%s" loading="lazy"%s></a><figcaption>%s</figcaption></figure></li>' % (cls, f, f, e(cap), ppos(f), e(cap))
    return out + "</ul>"


def pills(items):
    return '<ul class="pills">' + "".join("<li>%s</li>" % e(i) for i in items) + "</ul>"


def bul(items):
    return '<ul class="bul">' + "".join("<li>%s</li>" % i for i in items) + "</ul>"


STORY_KEYS = ("The question", "Data and method", "What I found", "What it means")


def story(q, m, f, w):
    """The four lines a recruiter reads first: question, data and method, finding, and what it means for the market."""
    return '<dl class="story">' + "".join('<div><dt>%s</dt><dd>%s</dd></div>' % (k, e(v)) for k, v in zip(STORY_KEYS, (q, m, f, w))) + "</dl>"


CASES = [
    ("media.html", "Project", "Media DCF models and credit comps", "Five media companies on one template, compared as credits.", ("6.6x", "Skydance net leverage")),
    ("research.html", "Project", "Green bond pricing", "Do green bonds price tighter at issue? 153 matched pairs.", ("2.4 bps", "average gap, not significant")),
    ("tender.html", "Project", "Tender Tracker", "A daily tracker of bond tender and exchange offers.", ("9 in 10", "types and dates right on unseen filings")),
    ("dashboard.html", "Project", "Morning Market Dashboard", "Is the new issue window open? One score, every morning.", ("7 inputs", "from VIX to the 10 year")),
    ("lab.html", "Project", "Fed Liquidity Lab", "Does Fed liquidity tell you when to own less? I tested it.", ("6.0%", "a year, against 8.1% for buy and hold")),
    ("creditkit.html", "Project", "Credit Research Toolkit", "Spreads an issuer from SEC filings and flags what changed.", ("$159.6bn", "AT&T debt, matched to its release")),
    ("finsight.html", "Role", "Finsight", "Order books on 15 to 20 new deals a day.", ("25+", "liability management headlines")),
    ("ccr.html", "Role", "Commonwealth Capital Research", "Rates and credit newsletter for 200 subscribers.", None),
    ("bloomberg.html", "Role", "Bloomberg at UMass Lowell", "Terminal Assistant, and captain of the UML trading team.", ("$1M", "virtual book, long only")),
    ("valuation.html", "Competition", "2026 Valuation Challenge", "Discount rate, DCF and LBO for an ESOP sale.", ("16.8%", "cost of capital I built")),
    ("finance-society.html", "Leadership", "UML Finance Society", "President of a 500 member club.", None),
    ("sales-team.html", "Leadership", "Intercollegiate Sales Team", "Captain. Top four at a national competition.", None),
    ("consulting.html", "Role", "Mill City Consulting", "Due diligence for a 1931 duckpin alley.", None),
    ("education.html", "Education", "UMass Lowell", "Finance and marketing, May 2027.", None),
    ("skills.html", "Skills", "Tools and certifications", "Bloomberg, R, Stata and Excel.", None),
]
order = [c[0] for c in CASES] + ["contact.html"]
order[order.index("media.html") + 1:order.index("media.html") + 1] = ["dcf.html", "dcf-nflx.html", "dcf-dis.html", "dcf-cmcsa.html", "dcf-foxa.html"]
label_of = {c[0]: c[2] for c in CASES}
label_of["contact.html"] = "Contact"
label_of.update({"dcf.html": "Skydance DCF", "dcf-nflx.html": "Netflix DCF", "dcf-dis.html": "Disney DCF", "dcf-cmcsa.html": "Comcast DCF", "dcf-foxa.html": "Fox DCF"})


def nxt(f):
    if f not in order:
        return "projects.html", "All work"
    i = order.index(f)
    n = order[(i + 1) % len(order)]
    return n, label_of[n]


# Sections that open on a click. A reader gets the finding first and the working when they ask for it.
FOLD = {"Method", "Against the market", "What I got wrong first", "What comes next", "Sources", "Why this company", "How it is built", "What would change the answer", "Since the model",
        "Why I built this", "What I would watch", "What is the same and what is not", "Since the models", "How often it is right", "What the score said when nothing priced", "What it does not show",
        "What to know", "The tenor screens", "The end of day tally", "Volume against the Street", "Backfilling the database", "What I did on my own time", "One pull in detail", "How I run the team",
        "What past winners did", "What I am learning", "The competition", "My four slides", "Where I disagreed with management", "What I would do differently", "Process",
        "What I am building for after me", "Partnerships", "The client", "What I owned", "Checked against the releases"}


def case_page(fname, title, desc, kind, h1, meta, lede, sections, banner=None):
    def block(label, h2, body):
        return f'<section class="section"{" id=\"figures\"" if label == "Figures" else ""}><div class="wrap"><h2>{e(h2)}</h2>{body}</div></section>\n'
    last = [x for x in sections if x[0] == "Download"]
    secs = "".join(block(*x) for x in sections if x[0] not in FOLD and x not in last)
    folds = "".join('<details class="fold"><summary>%s</summary><div class="fold-body">%s</div></details>' % (e(l), b) for l, h, b in sections if l in FOLD)
    if folds:
        secs += '<section class="section"><div class="wrap"><div class="folds">%s</div></div></section>\n' % folds
    secs += "".join(block(*x) for x in last)
    nf, nl = nxt(fname)
    crumb = "" if fname in HUBS else '<p class="crumb"><a href="projects.html">&larr; All work</a></p>'
    if banner:
        src = banner[0] if "/" in banner[0] else "assets/photos/%s.jpg" % banner[0]
        pos = banner[2] if len(banner) > 2 else (PHOTO_POS.get(src.split("/")[-1].replace(".jpg", ""), "center 30%") if "/photos/" in src else "center center")
        head = page_head(crumb, h1, meta, lede, src, banner[1], pos, vt(fname) if fname in THUMBS else "")
    else:
        head = page_head(crumb, h1, meta, lede)
    main = f"""{head}
{secs}{"" if fname in HUBS else f'<section class="section"><div class="wrap next"><a href="projects.html">&larr; All work</a><a href="{nf}">Next: {e(nl)} &rarr;</a></div></section>'}"""
    open(os.path.join(OUT, fname), "w", encoding="utf-8").write(shell(fname, title, desc, main))


# ---------- index ----------
THUMBS = {
    "research.html": "assets/thumbs/research.jpg", "tender.html": "assets/thumbs/tender.jpg", "dashboard.html": "assets/thumbs/dashboard.jpg", "lab.html": "assets/thumbs/lab.jpg", "creditkit.html": "assets/thumbs/creditkit.jpg",
    "media.html": "assets/thumbs/media.jpg", 
    "valuation.html": "assets/thumbs/valuation.jpg",
    
    "skills.html": "assets/thumbs/skills.jpg",
    "finance-society.html": "assets/photos/fs-fireside.jpg", "sales-team.html": "assets/photos/sales-certificates.jpg", "consulting.html": "assets/photos/mill-city.jpg",
    "ccr.html": "assets/photos/ccr-elward.jpg", "education.html": "assets/photos/babylon-panel.jpg",
}


PHOTO_POS = {
    "nyse-stage": "center 68%", "nyse-seated": "center 55%", "nyse-podium": "center 22%", "nyse-podium-side": "center 22%",
    "ccr-elward": "center 38%", "careers-stairs": "center 28%", "class-team": "center 36%", "mill-city": "22% 30%", "fs-group": "right 22%", "guest-speaker": "center 20%", "fs-lunch": "center 30%", "resume-recharge-1": "center 45%", "resume-recharge-2": "center 48%", "fs-social": "center 35%", "fs-fireside": "center 42%", "babylon-talk": "center 40%", "class-presenting": "center 30%",
    "babylon-podium": "center 22%", "babylon-panel": "center 40%", "club-fair": "center 30%", "sales-award": "center 28%",
    "sales-certificates": "center 45%", "sales-comp-day": "center 40%", "fintech-rooftop": "center 45%", "fintech-rooftop-2": "center 40%",
    "fintech-career-summit": "center 45%",
}
def ppos(src):
    k = src.split("/")[-1].replace(".jpg", "")
    return ' class="%s"' % fp(PHOTO_POS[k]) if k in PHOTO_POS else ""

def card_html(f, kind, t, d, num, big=False):
    fact = '<span class="num">%s<small>%s</small></span>' % (e(num[0]), e(num[1])) if num else ""
    th = '<span class="thumb vt-%s"><img src="%s" alt="" loading="lazy"%s></span>' % (vt(f), THUMBS[f], ppos(THUMBS[f])) if f in THUMBS else ""
    return '<li><a class="card%s" href="%s"><span class="card-body"><b>%s</b><em>%s</em></span>%s<span class="strip%s">%s<span class="go">Open</span></span></a></li>' % (" feature" if big else "", f, e(t), e(d), th, "" if num else " solo", fact)


def card_group(kinds):
    return '<ul class="cards">' + "".join(card_html(*c) for c in CASES if c[1] in kinds) + "</ul>"


def pick(*files, big=False):
    by = {c[0]: c for c in CASES}
    return '<ul class="cards">' + "".join(card_html(*by[f], big=big) for f in files) + "</ul>"


WORK = pick("finsight.html", big=True) + pick("media.html", "research.html", "tender.html", "dashboard.html", "creditkit.html", "valuation.html")

timeline = [
    ("Nov 2026", "Credit Research Toolkit", "Spreads an issuer from SEC filings and checks a watchlist.", "creditkit.html"),
    ("Nov 2026", "Fed Liquidity Lab", "Rules tested against buy and hold. The rules lost, and I published that.", "lab.html"),
    ("Oct 2026", "Media DCF models and credit comps", "Five companies on one template, then a credit comparison.", "media.html"),
    ("Oct 2026 to now", "Tender Tracker", "Bond tenders and exchanges, with published error rates.", "tender.html"),
    ("Oct 2026 to now", "Captain, Bloomberg Global Trading Challenge", "A million virtual dollars, long only, scored against the WLS index.", "bloomberg.html"),
    ("Sep 2026 to now", "Bloomberg Terminal Assistant, UMass Lowell", "Training students across 10 classes and pulling data for faculty.", "bloomberg.html"),
    ("Sep to Oct 2026", "2026 Valuation Challenge", "Discount rate, DCF, LBO and comparables. Submitted October 19.", "valuation.html"),
    ("Jun 2026 to now", "Morning Market Dashboard", "An R dashboard that scores the new issue window.", "dashboard.html"),
    ("May 2026 to now", "Fixed Income Research Analyst, UMass Lowell", "Green bond pricing research. Results are preliminary.", "research.html"),
    ("Apr 2026 to now", "President, UML Finance Society", "Membership up 200+ to over 500.", "finance-society.html"),
    ("Feb to Apr 2026", "Bloomberg Global Trading Challenge, spring round", "Analyst on the UML team.", "bloomberg.html"),
    ("Dec 2025 to Sep 2026", "Debt Capital Markets Analyst Intern, Finsight", "New issues and 25+ liability management deals, in high yield and investment grade.", "finsight.html"),
    ("Nov 2025 to now", "Captain, UML Intercollegiate Sales Team", "Top four at the Love's Travel Stops national competition.", "sales-team.html"),
    ("Feb 2024 to now", "Research Analyst, Commonwealth Capital Research", "Rates and credit newsletter for 200 subscribers.", "ccr.html"),
]
tl = '<ol class="tl">' + "".join('<li><span class="when">%s</span><b><a href="%s">%s</a></b><p>%s</p></li>' % (e(w), f, e(t), e(d)) for w, t, d, f in timeline) + "</ol>"

def mosaic(items):
    return '<ul class="mosaic">' + "".join('<li class="%s"><a href="%s"><img src="assets/photos/%s.jpg" alt="%s" loading="lazy"%s><span>%s</span></a></li>' % (cls, href, f, e(cap), ppos(f), e(cap)) for f, cap, cls, href in items) + "</ul>"


HOME_PHOTOS = mosaic([
    ("nyse-stage", "On stage at the NYSE after the ICE Fixed Income Forum, October 21, 2026.", "big", "finsight.html"),
    ("fintech-rooftop", "The Finance Society on the roof of the Boston Fed, Boston Fintech Week.", "", "finance-society.html"),
    ("sales-award", "Fourth in Speed Sell at the Challenger Sales Institute invitational.", "", "sales-team.html"),
    ("ccr-elward", "With Nick Elward of Natixis after the CCR fireside chat.", "", "ccr.html"),
    ("fs-fireside", "After our fireside chat, The Future of Trading on Wall Street, November 19.", "", "finance-society.html"),
])
index_main = f"""<section class="hero" id="top"><div class="wrap">
  <div class="hero-text">
    <h1>{split("Anthony Ferriero")}</h1>
    <p class="tag">Fixed income. Credit research, syndicate and debt capital markets.</p>
    <p class="sub">Nine months on a primary bond desk at Finsight. UMass Lowell, class of 2027.</p>
  </div>
  <figure class="hero-portrait"><img src="assets/headshot.jpg" width="720" height="720" alt="Anthony Ferriero" fetchpriority="high"></figure>
</div></section>
<section class="section" id="case-files"><div class="wrap">
  <h2>Work</h2>
  {WORK}
  <p class="more"><a class="btn outline" href="projects.html">See all work</a></p>
</div></section>
<div class="wrap data-block">{strip("tape", "Read when you open this page. Each number shows its own time.", 'Free data. From the <a href="dashboard.html">Morning Market Dashboard</a>. Not a trading tool.')}</div>
<section class="section" id="desks"><div class="wrap">
  <h2>One body of work, four desks</h2>
  <dl class="story">
    <div><dt>Fixed income</dt><dd><a href="research.html">Green bond pricing</a> &middot; <a href="ccr.html">Commonwealth Capital Research</a></dd></div>
    <div><dt>Credit research</dt><dd><a href="media.html">Media DCF models and credit comps</a> &middot; <a href="creditkit.html">Credit Research Toolkit</a></dd></div>
    <div><dt>Syndicate</dt><dd><a href="finsight.html">Finsight</a> &middot; <a href="dashboard.html">Morning Market Dashboard</a></dd></div>
    <div><dt>Debt capital markets</dt><dd><a href="finsight.html">Finsight</a> &middot; <a href="tender.html">Tender Tracker</a></dd></div>
  </dl>
</div></section>
<section class="section"><div class="wrap">
  <h2>Recent events</h2>
  {HOME_PHOTOS}
</div></section>
"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(shell("index.html", "Anthony Ferriero",
    "Finance student at UMass Lowell, class of 2027, working in fixed income: credit research, syndicate and debt capital markets. Primary market experience at Finsight, five DCF models with a credit comparison, green bond pricing research, a bond tender tracker and a new issue window dashboard.", index_main))

# ---------- research ----------
FIGS = [
    ("fig1_universe_by_year.png", "The dataset", "663 green bonds by issue year. The 153 in the sample are in grey.", False),
    ("fig3_credit_beta.png", "Why the credit adjustment matters", "The gap moves with credit spreads almost one for one. The slope is 0.97.", False),
    ("fig2_adjustment_steps.png", "Three steps from coupons to a greenium", "Each step cuts the noise, from 104 bps to 64 to 27.", True),
    ("fig4_specification_chart.png", "The estimate across 24 specifications", "Versions that keep every pair land between 2 and 4 bps tighter. The splits are exploratory.", True),
    ("fig5_groups.png", "By sector and rating", "Financials show 5.1 bps tighter, p 0.20. No group is significant.", False),
    ("fig6_greenium_by_year.png", "By issue year", "No year departs from the pooled estimate.", False),
    ("fig7_events.png", "Seven dated events", "None shifts the gap detectably. The test can only see moves of roughly 27 bps.", True),
    ("fig8_market_backdrop.png", "The market behind the sample", "The 10 year Treasury and the credit index, with each issue date marked.", False),
    ("fig9_power.png", "How many pairs it would take", "Detecting 5 bps would take about 265 pairs, and 3 bps about 735.", False),
    ("fig10_permutation.png", "A test that does not depend on the model's assumptions", "A mean this large shows up by chance about 31 percent of the time.", False),
    ("fig12_distribution_noise.png", "The 153 gaps, and why the date gap matters", "Noise grows with the time between the two issue dates.", False),
    ("fig11_specifications.png", "Mean versus robust estimators", "Robust estimators give 3.5 to 4.5 bps. Adding back excluded pairs gives 0.2 to 1.2.", True),
    ("fig13_posteriors.png", "What the data say under different starting beliefs", "A skeptic ends at 1.5 bps tighter, a believer at 3.4.", True),
]
figs_html = '<ul class="figs">' + "".join(
    '<li%s><figure><a class="img" href="assets/figures/%s"><img src="assets/figures/%s" alt="%s" loading="lazy"></a><figcaption><b>%s</b>%s</figcaption></figure></li>'
    % (' class="full"' if full else "", f, f, e(t), e(t), e(c)) for f, t, c, full in FIGS) + "</ul>"

stats = [
    ("2.4 bps", "Average gap, green tighter. 153 pairs, 88 issuers, p 0.30. Not significant."),
    ("0 to 5 bps", "Range across other estimators and samples. The data cannot narrow it."),
    ("+3.7 bps", "The 10 pairs sold within a week of each other. No discount, but too few to be sure."),
    ("p 0.67", "No detectable change across four periods, 2016 to 2026."),
    ("6.6 bps", "Smallest true gap this sample can detect reliably."),
    ("663 bonds", "After cleaning 1,226 rows. 40 countries, about $386 billion of face value."),
]
stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in stats) + "</div>"
case_page("research.html", "Green bond pricing research", "Preliminary results on whether green bonds price tighter than matched conventional bonds from the same issuer.",
          "Project, preliminary results", "Green bond pricing research", "Fixed Income Research Analyst, UMass Lowell. May 2026 to now.",
          "Do investors accept a lower yield on a green bond than on a conventional bond from the same issuer?",
          [("In short", "In short",
            story("Do green bonds price tighter than the same issuer's conventional bonds?",
                  "153 matched pairs from 663 green bonds, adjusted for rates, credit and maturity.",
                  "2.4 bps tighter on average, p 0.30. Not significant. Results are preliminary.",
                  "About $120,000 a year on a $500 million 10 year. Investor demand is a better reason to issue green.")),
           ("Method", "Matched pairs, adjusted for rates, credit and maturity",
            P("The dataset holds 663 green bonds, of which 153 have a conventional bond from the same issuer that passes four pairing rules. The twin must be denominated in US dollars and hold the same payment rank, both bonds must be at least $250 million, and neither may be callable before 90 percent of its life. Each pair is dated at its Bloomberg pricing date and adjusted for rates, credit spreads and maturity with Treasury and Moody's data from FRED. Matches were first screened with help from Claude. Every number here is preliminary.")),
           ("Results", "A small gap that the data cannot pin down", stat_html +
            P("One pattern I cannot explain. Pairs where the conventional bond came after the green bond show a gap 11.8 bps larger, p 0.008. That needs a reason before anyone leans on the headline.")),
           ("Try it", "How many pairs would it take", POWER_HTML),
           ("Figures", "The research in thirteen charts",
            P("Click any chart to open it.") + figs_html),
           ("Against the market", "What the issuers with real twins see",
            P("The cleanest measurements of the greenium come from sovereigns that sell a green bond and a conventional bond with the same coupon and maturity, so that the only difference between the two is the label. Germany's March 2026 green Bund, 4 billion euros at a 3.14 percent yield, priced 1 bp through its twin, and the Finanzagentur puts the year's greenium at about half a basis point. Denmark's central bank says its recent twins trade 0 to 1 bp apart, down from 2 to 4 a few years ago, with its newest 10 year coming 1.5 to 2 bp inside.",
              "My corporate pairs say about the same thing with more noise. The gap is in the low single digits, it is shrinking, and on any one deal you cannot tell it from zero. Bankers at Crédit Agricole cite 5 bp or more on bank paper. My financials subsample shows 5.1 bps tighter on 36 pairs, which seems to agree until you see the p value of 0.20.")),
           ("What I got wrong first", "Two results that did not hold up",
            P("The first was a 25 bps result that turned out to be an artifact. An early version showed the gap shrinking by 25 bps. I had measured credit spreads over the 10 year Treasury, so I was picking up the slope of the curve. Measured over the 30 year, the credit index tracks the ICE BofA investment grade index at a correlation of 0.95, compared with 0.40 before. I withdrew the claim.",
              "The second was a dating error in my own file. In October 2026 I checked the largest residuals on the terminal and found that the file used settlement dates where pricing dates belonged. I pulled the Bloomberg pricing dates and applied the four pairing rules my supervisor adopted, which require a US dollar twin, the same payment rank, a minimum size of $250 million for both bonds and no early call. The average moved from 4.7 to 2.4 bps and the p value from 0.11 to 0.30. The rules were set after I had seen the earlier results, and the paper discloses that.")),
           ("What comes next", "Three things that would change these numbers",
            bul(["Verifying the largest residuals and 20 random pairs on the terminal, then rerunning with the confirmed set.",
                 "Replacing coupons with offering yields and daily prices, which needs TRACE and Mergent FISD access.",
                 "Finishing the twin search for the 164 live green bonds that still have no conventional match."])),
           ("Sources", "Where the numbers come from",
            '<p class="note">Built from Bloomberg, Climate Bonds Initiative and FRED data. My supervisor approved publishing summary statistics in writing. No bond level data is shown. Last updated October 2026.</p>')], banner=("assets/banners/pairs.jpg", "All 153 matched pairs in issue date order. Orange is the green bond priced tighter."))

# ---------- dcf ----------
dstats = [
    ("$9.58", "Perpetuity method, on the debt reported in November. It was $8.80 in October."),
    ("$5.70", "Exit multiple at 7 times 2031 EBITDA. It was $4.97."),
    ("$6.50", "The close on November 24. It was $7.77 when I built the model."),
    ("6.6x", "Net debt to EBITDA. Press reports put S&P at 7.6 and Fitch at 7.8."),
    ("2.0x", "EBITDA to interest, on about $6 billion a year."),
    ("71%", "Share of enterprise value in the terminal value."),
]
dstat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in dstats) + "</div>"
DFIGS = [
    ("dcf1_ebitda.png", "Where the EBITDA growth comes from", "Every dollar of growth from 2026 to 2031 is realized synergies."),
    ("dcf2_fcff.png", "Unlevered free cash flow", "Conversion rises from about half of EBITDA to two thirds. It does not reach management's target."),
    ("dcf3_sensitivity.png", "Cost of capital against long term growth", "One point of discount rate moves the value by $3 to $4 a share."),
    ("dcf4_football.png", "Four answers on one line", "The price falls inside every range."),
]
dfigs_html = '<ul class="figs">' + "".join(
    '<li class="dark"><figure><a class="img" href="assets/figures/%s"><img src="assets/figures/%s" alt="%s" loading="lazy"></a><figcaption><b>%s</b>%s</figcaption></figure></li>' % (f, f, e(t), e(t), e(c)) for f, t, c in DFIGS) + "</ul>"
case_page("dcf.html", "Skydance DCF model", "A pro forma discounted cash flow model of Skydance Corporation, formerly Paramount Skydance, after its purchase of Warner Bros. Discovery. Public filings only.",
          "Project", "Skydance DCF model", "Built October 24, updated November 25, 2026. Excel, 450 formulas, 24 sources. Prices as of November 24.",
          "What is the company that bought Warner Bros. Discovery worth?",
          [("In short", "In short",
            story("What is Skydance worth, and can it carry $87 billion of debt?",
                  "A pro forma base year from filings, three revenue lines, a synergy line and a 9.2 percent WACC.",
                  "$9.58 a share on one method and $5.70 on the other, against $6.50. In the bear case the equity is worth almost nothing.",
                  "Every free dollar to debt gets leverage to 4.6 times in 2029. The target is 3.0.")),
           ("Why this company", "I covered its tender at Finsight",
            P("I covered the Paramount Skydance tender at Finsight and wanted to value a company whose bonds I had watched trade. By the time I built it, Paramount Skydance had closed its $110 billion purchase of Warner Bros. Discovery and become Skydance Corporation, SKYD on the NYSE. So the model values the combined company: about $67 billion of revenue, $87 billion of gross debt and 5.04 billion shares.",
              "The deal was paid for with $47 billion of new equity at $12 a share and $57 billion of new secured debt. S&P cut the company to BB, and in October Debtwire had the old Paramount bonds yielding 10 to 13 percent. With that capital structure, the discount rate is a harder judgment than the forecast.")),
           ("The result", "The price sits between the two methods", model_strip("Skydance") + dstat_html +
            P("These are model outputs under stated assumptions. Nothing on this page is a recommendation to buy or sell anything.")),
           ("How it is built", "Pro forma from two companies' filings, with every input on one sheet",
            bul(["<b>Base year.</b> Paramount Skydance's fiscal 2025 results plus Warner Bros. Discovery's, giving $66 billion of revenue and $12 billion of adjusted EBITDA, which matches the pro forma 8-K and the Street's 2026 consensus.",
                 "<b>Revenue.</b> Three lines, streaming, linear networks and studios, each with its own growth path. Streaming grows 9 percent fading to 4, linear falls 8 percent fading to 6, studios grow 3.",
                 "<b>EBITDA.</b> An underlying margin that drifts down as linear shrinks, plus a separate synergy line so the reader can see how much of the value is the merger.",
                 "<b>Cash flow.</b> EBITDA less stock compensation, integration cash costs, cash taxes at 23 percent, capex at 2.1 percent of revenue and a content and working capital line. Stock compensation is treated as a real cost.",
                 "<b>Discount rate.</b> A 0.9 unlevered media beta relevered for a 2.5 debt to equity ratio gives a 2.6 levered beta and a 16.7 percent cost of equity. An 8 percent cost of debt, blended from the new 7.05 and 8.875 percent notes and the legacy unsecured yields, at market weights gives a 9.2 percent WACC.",
                 "<b>Equity bridge.</b> Enterprise value less $80.9 billion of net debt and $1 billion of noncontrolling interests, over 5.04 billion shares. October used Debtwire's $84.3 billion. The 471 million warrants struck at $12 dilute only when the value is above $12, by the treasury stock method.",
                 "<b>Three scenarios</b> on one switch: base, bear and management's plan.",
                 "<b>Four peers and a credit comp on the same template.</b> Netflix, Disney, Comcast and Fox, built the same way, then leverage, coverage and cushion across all five. See <a href=\"media.html\">Media DCF models and credit comps</a>."])),
           ("Charts", "The model in four pictures", dfigs_html),
           ("What I got wrong first", "The company I set out to value no longer existed",
            P("My first pass used Paramount Skydance's own filings: $30 billion of revenue, $15 billion of debt, 1.1 billion shares. The company that trades today is twice that size with six times the debt. That would have produced a precise answer for a company that no longer trades, so I rebuilt the base year from both companies' filings.",
              "Then the debt. I used Debtwire's estimate at close, $89.3 billion of debt and $5 billion of cash. On November 9 the company reported $87 billion and about $10 billion. Part of that cash is set aside, including about $3.9 billion to pay off a securitization, so the fair comparison is $80.9 billion of net debt against my $84.3 billion. I had interest at $6.7 billion. The 10-Q, as quoted in the press, says about $6 billion, so coverage is 2.0 times and not 1.8.",
              "I also wrote that November 9 would be the first combined report. It was Paramount alone, because the deal closed on October 6, after the quarter ended.")),
           ("What would change the answer", "In order of how much they move it",
            bul(["<b>Synergy realization.</b> The base case takes $5.4 billion of the $6 billion target by 2030. Each $1 billion of run rate synergies is worth about $1.50 a share.",
                 "<b>Linear decline.</b> Three points a year faster, which is what Warner Bros. Discovery's linear networks did in the second quarter of 2026, takes the base case most of the way to the bear case.",
                 "<b>The discount rate.</b> Market weights give 9.2 percent. If management reaches its 3.0 times leverage target by 2029, the equity weight rises and so does the WACC, which lowers the value even as the business gets safer.",
                 "<b>Content cash spend.</b> It sits inside the working capital line at about 1 percent of revenue and I could not source it. The fourth quarter will be the first combined report, and the first check on it."])),
           ("Since the model", "What has moved since October 23",
            bul(["<b>The price.</b> $7.77 on October 23, $8.70 on November 9 and $6.50 on November 24. The model still sits on both sides of it.",
                 "<b>The third quarter.</b> Paramount alone, with $7.03 billion of revenue. Management expects $3.9 billion of adjusted EBITDA for it in 2026. I had $3.85 billion.",
                 "<b>Synergies.</b> Management now says 30 percent of at least $6 billion in year one and 70 percent through year two. I have $1.75 billion in 2027 and $3.75 billion in 2028, a little below that.",
                 "<b>Cost to get there.</b> About $4 billion, per management. I spend $7.1 billion, so my base case is the harsher one.",
                 "<b>Interest.</b> The company expects about $6 billion a year. I built it tranche by tranche from the 8-Ks and got $5.75 billion, so coverage is between 2.0 and 2.1 times. A point on the floating debt is $145 million.",
                 "<b>The covenant.</b> The term loans A and the revolver cap leverage at 5.5 times. I measure 6.6. Debtwire says their EBITDA adds back synergies with no cap. Add all $6 billion and I get 4.4. The notes have no such test.",
                 "<b>Equity.</b> Elon Musk put in about $1 billion on October 22, per Semafor and CNBC. Reaching 3.0 times at today's EBITDA means cutting about $44 billion of net debt.",
                 "<b>What is missing.</b> Public counts of the debt run from $80 billion to $89 billion. The fourth quarter balance sheet should settle it."])),
           ("Download", "The model and its sources",
            '<p class="links"><a href="assets/Skydance_DCF_Model.xlsx">Download the Excel model</a></p>' +
            P("Blue cells are inputs. 24 numbered sources, mostly SEC filings. October and November sit side by side on one sheet, and the interest is built on another. Nothing from a Bloomberg Terminal or any employer."))], banner=("assets/banners/skypath.jpg", "Skydance net leverage if every free dollar pays down debt. Grey is my October model, orange is the reported debt. The target is 3.0 times by 2029."))

# ---------- media five ----------
def dfig(items):
    return '<ul class="figs">' + "".join(
        '<li class="dark%s"><figure><a class="img" href="assets/figures/%s"><img src="assets/figures/%s" alt="%s" loading="lazy"></a><figcaption><b>%s</b>%s</figcaption></figure></li>' % (" full" if full else "", f, f, e(t), e(t), e(c)) for f, t, c, full in items) + "</ul>"


M5 = [
    ("Skydance", "dcf.html", "6.6x", "9.2%", "9.3x", "$9.58", "$5.70", "$6.50", "0.1%", "7.4x", "71%"),
    ("Netflix", "dcf-nflx.html", "0.4x", "10.3%", "15.1x", "$52.02", "$69.97", "$58.87", "4.0%", "11.3x", "73%"),
    ("Disney", "dcf-dis.html", "1.7x", "9.4%", "10.5x", "$77.72", "$109.82", "$122.51", "4.7%", "11.2x", "68%"),
    ("Comcast", "dcf-cmcsa.html", "2.3x", "7.5%", "4.9x", "$49.05", "$36.13", "$25.38", "-5.1%", "3.9x", "70%"),
    ("Fox with Roku", "dcf-foxa.html", "3.3x", "8.8%", "10.7x", "$59.59", "$50.24", "$62.62", "1.8%", "10.1x", "68%"),
]
m5_table = '<div class="tablewrap"><table class="cmp"><thead><tr><th>Company</th><th>Net debt to EBITDA</th><th>WACC</th><th>Market EV to EBITDA</th><th>Perpetuity, base</th><th>Exit multiple, base</th><th>Market price</th><th>Growth the price implies</th><th>Exit multiple the price implies</th><th>Terminal share</th></tr></thead><tbody>' + \
    "".join('<tr><td><a href="%s">%s</a></td>' % (f, e(n)) + "".join("<td>%s</td>" % e(v) for v in vals) + "</tr>" for n, f, *vals in M5) + "</tbody></table></div>"
m5_stats = [
    ("5", "Companies on one DCF template, with the same rules."),
    ("2,113", "Formulas across the models and the comps workbook, zero errors."),
    ("6.6x", "Skydance net debt to EBITDA. Fox is next at 3.3, now that it owns Roku."),
    ("2.0x", "Skydance EBITDA to interest. The other four cover 4 to 22 times."),
    ("-29%", "EBITDA miss that wipes out Skydance's equity at the November 24 price."),
    ("4.0x", "Skydance leverage by 2031 on cash flow. The target is 3.0 by 2029."),
]
m5_stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in m5_stats) + "</div>"
CREDIT = [
    ("Skydance", "dcf.html", "6.6x", "2.0x", "1%", "71%", "0.6x", "-29%", "309 bp", "BB"),
    ("Netflix", "dcf-nflx.html", "0.4x", "22.3x", "135%", "3%", "30.1x", "-97%", "85 bp", "A"),
    ("Disney", "dcf-dis.html", "1.7x", "11.7x", "21%", "15%", "3.5x", "-82%", "75 bp", "A"),
    ("Comcast", "dcf-cmcsa.html", "2.3x", "8.4x", "18%", "47%", "2.2x", "-53%", "95 bp", "A minus, on watch"),
    ("Fox with Roku", "dcf-foxa.html", "3.3x", "3.9x", "13%", "28%", "2.4x", "-71%", "145 bp", "BBB"),
]
credit_table = '<div class="tablewrap"><table class="cmp"><thead><tr><th>Company</th><th>Net debt to EBITDA</th><th>EBITDA to interest</th><th>Free cash flow after interest to net debt</th><th>Net debt share of enterprise value</th><th>DCF equity over net debt</th><th>EBITDA miss that wipes out the equity</th><th>Spread to Treasury on the cost of debt</th><th>S&amp;P rating, where sourced</th></tr></thead><tbody>' + \
    "".join('<tr><td><a href="%s">%s</a></td>' % (f, e(n)) + "".join("<td>%s</td>" % e(v) for v in vals) + "</tr>" for n, f, *vals in CREDIT) + "</tbody></table></div>"
case_page("media.html", "Media DCF models and credit comps", "Five discounted cash flow models of Skydance, Netflix, Disney, Comcast and Fox on one template, then a credit comparison built the way a credit analyst or a debt capital markets desk would build it.",
          "Project", "Media DCF models and credit comps", "Built October 24 and 25, updated November 25, 2026. Five Excel models plus a credit comps workbook. 2,113 formulas, 77 sources. Prices as of November 24.",
          "Five media companies, valued the same way and read as credits.",
          [("In short", "In short",
            story("Which of five media companies can carry its debt?",
                  "Five DCF models on one template from SEC filings, then a credit comparison.",
                  "Skydance is far past the rest, at 6.6 times leverage and 2.0 times coverage. Fox went from 0.6 to 3.3 times when it bought Roku.",
                  "Cash flow alone does not get Skydance to 3.0 times. Fox gets there by fiscal 2028, but only if it holds off on buybacks.")),
           ("Why I built this", "One tender, then the whole capital structure",
            P("I covered the Paramount Skydance tender at Finsight, then watched the market reprice every bond it had when the Warner Bros. Discovery debt was sold. One company on its own does not tell you whether that price is fair. So I built four peers the same way and read all five as credits.")),
           ("The five models", "One template, five companies, and what each price already assumes", model_data() + strip("five", "Prices now, and how far each value sits from them", "Perpetuity value first, then exit value. The models and the table below are from November 25, 2026.") + m5_stat_html + m5_table +
            P("Reversing each DCF gives the growth and multiple the price already assumes. Comcast is priced as if cash flow shrinks 5 percent a year forever. The Fox price is the average of its two share classes. Nothing here is a recommendation to buy or sell anything.")),
           ("Try it", "Move the inputs and watch the value move", explorer_html()),
           ("The credit comps", "The same five, read the way a desk reads them", credit_table +
            P("Skydance fails every test the others pass. Net debt is 71 percent of enterprise value, and free cash flow after interest is close to zero in year one. Fox's spread is its own November new issue and Skydance's rests on October levels. The other three are my inputs.")),
           ("The deleveraging question", "Can Skydance and Fox pay it down",
            P("Skydance first. With every free dollar going to debt, net leverage is 5.9 times at the end of 2027, 4.6 at the end of 2029 and 4.0 at the end of 2031. Reaching 3.0 at today's EBITDA means cutting about $44 billion.") +
            dfig([("m5_skypath.png", "Skydance net leverage, year by year", "Base case. Neither line reaches the target.", True)]) +
            P("Fox wants gross leverage of 2.25 to 3.0 times within two years. On my base case it is 2.9 at the end of fiscal 2028 with no buybacks and 3.4 with $1.5 billion a year. Management says buybacks resume.") +
            dfig([("m5_foxpath.png", "Fox gross leverage, year by year", "Base case. Buybacks push the target out two years, to fiscal 2030.", True)])),
           ("What I would watch", "If I covered Skydance's debt",
            bul(["<b>Free cash flow after interest.</b> About $0.4 billion in year one of my base case, before $1.1 billion of dividends. The fourth quarter will be the first combined report.",
                 "<b>Asset sales or equity.</b> Getting to 3.0 times means cutting about $44 billion of net debt. The $1 billion of equity in October is 2 percent of that.",
                 "<b>The first liens.</b> The 7.05 percent notes traded at 272 bp on October 13, per Debtwire, 170 bp wide of the BBB index. I have found no published level since the stock fell to $6.50. With this little equity under them, I expect them to react to the stock more than a BBB bond would.",
                 "<b>Fox.</b> Whether buybacks come before debt, and whether Roku's margin gets past 15 percent. The 10 year came at 145 bp on November 10, and the two year term loan is the first thing to repay.",
                 "<b>The other three.</b> Netflix and Disney carry less than 2 times leverage. Comcast is at 2.3 times and nearly half its capital is debt, with the spin still ahead."])),
           ("Charts", "Five charts, one per question",
            dfig([("m5_credit.png", "Leverage and coverage", "Skydance stands alone on both. Fox is now second.", True),
                  ("m5_cushion.png", "The equity cushion", "Skydance hits zero at a 29 percent miss, Comcast at 53, Fox at 71.", True),
                  ("m5_vs_market.png", "Where each DCF lands against its price", "Comcast's range sits almost entirely above its price.", True),
                  ("m5_implied.png", "Reverse the DCF", "Comcast and Disney are the two I disagree with most.", True),
                  ("m5_wacc_tv.png", "Cost of capital and terminal value share", "Two thirds or more of every valuation sits past the forecast.", True)])),
           ("What is the same and what is not", "The rules I held constant",
            bul(["<b>Same discount rate inputs.</b> 10 year Treasury 4.91 percent, equity risk premium 4.5 percent, cash tax 23 percent, market weights, Hamada relevering. Cost of debt 75 to 145 bp over Treasuries for the four investment grade names, 8 percent blended for Skydance.",
                 "<b>Same cash flow definition.</b> Adjusted EBITDA less stock compensation, cash restructuring, cash taxes on profit after tax depreciation, capex and a working capital and content line. Stock compensation is a real cost in all five, and it comes out once.",
                 "<b>Same mechanics.</b> Mid year discounting, a first year stub, perpetuity and exit multiple side by side, three scenarios on one switch.",
                 "<b>Different fiscal years.</b> Disney and Fox run FY2027 to FY2032 with stubs of 0.85 and 0.60. The other three run calendar 2026 to 2031 with a 0.10 stub.",
                 "<b>Different pending deals.</b> Comcast is modeled before the NBCUniversal and Sky spin. Fox includes Roku and Skydance includes Warner Bros. Discovery, because both have closed.",
                 "<b>Interest expense.</b> Gross, for all five. Disney is reported. Netflix and Comcast are annualized from 2026 filings. Fox is the new coupons plus its first quarter. Skydance is about $6 billion, quoted from its 10-Q."])),
           ("What I got wrong first", "Betas off a quote page, and a cost of debt below the Treasury yield",
            P("First I used quoted betas as if they were unlevered. Netflix came out at an 11.6 percent WACC and $42 a share, and Comcast's unlevered beta fell below that of a utility. I set the betas by hand, at 0.6 for Fox, 0.7 for Comcast, 0.9 for Skydance, 1.05 for Disney and 1.2 for Netflix, and recorded the reasoning on each WACC sheet.",
              "Then the one a desk would catch first. I had the four investment grade names borrowing at 5 to 5.5 percent with the 10 year at 4.95. That is 5 to 55 bp of spread, and nobody in investment grade prices there. I moved them to 75 to 125 bp over Treasuries. The change has little effect on three of them and takes $3 off Comcast, because half its capital is debt.",
              "On October 26 I checked those inputs on a terminal against where each name's long dated debt trades. Disney, Netflix and Fox were close enough. Comcast was the miss. After three agencies placed it on negative watch for the spin, the market had it wider than my 95 bp by a margin that would not surprise a desk. Moving Comcast's cost of debt to the market level lifts its WACC to 7.8 percent and takes about $2 more off the perpetuity value. It does not change any conclusion, because the model still lands well above the price. The levels themselves are not published on this site.",
              "The last one took me until November. Fox, Netflix and Comcast report EBITDA after stock compensation, and my template took it out again. That cost Comcast about $5 a share, Fox $4 and Netflix $1. At Disney I left out corporate costs and added back amortization that segment income already excludes, so EBITDA was $2.3 billion too high. The Excel files also still had the old cost of debt. All of it is fixed, on the pages and in the files.")),
           ("Since the models", "What has moved since October 23",
            bul(["<b>One date.</b> All five are on November 24 prices and a 4.91 percent 10 year. October used 4.95.",
                 "<b>Fox.</b> Rebuilt with Roku, which closed on November 6. I had written that it would close in the first half of 2027 at the earliest. See <a href=\"dcf-foxa.html\">the Fox page</a>.",
                 "<b>Skydance.</b> On the $87 billion of debt it reported on November 9. The stock went from $8.70 that day to $6.50. See <a href=\"dcf.html\">the Skydance page</a>.",
                 "<b>Disney.</b> On its reported fiscal 2026, after corporate costs.",
                 "<b>Netflix and Comcast.</b> Stock compensation counted once, and the real Netflix share count.",
                 "<b>The market.</b> The ICE investment grade index was 97 bp on November 23, from 92 on November 17. Reuters, on LSEG data, had $1.88 trillion of investment grade sales through November 4, a record."])),
           ("Download", "Five models and the credit comps",
            '<p class="links"><a href="assets/Media_Credit_Comps.xlsx">Credit comps workbook</a> &nbsp;&middot;&nbsp; <a href="assets/Skydance_DCF_Model.xlsx">Skydance</a> &nbsp;&middot;&nbsp; <a href="assets/NFLX_DCF_Model.xlsx">Netflix</a> &nbsp;&middot;&nbsp; <a href="assets/DIS_DCF_Model.xlsx">Disney</a> &nbsp;&middot;&nbsp; <a href="assets/CMCSA_DCF_Model.xlsx">Comcast</a> &nbsp;&middot;&nbsp; <a href="assets/FOXA_DCF_Model.xlsx">Fox</a></p>' +
            P("Blue cells are inputs. No input comes from a Bloomberg Terminal or any employer."))], banner=("assets/banners/media.jpg", "Net debt to EBITDA, November 24, 2026. Fox includes Roku."))


def company_dcf_page(fname, name, h1, meta, lede, why, stats, build, charts, wrong, change, xlsx, extra_note, short=None, since=None):
    stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in stats) + "</div>"
    case_page(fname, "%s DCF model" % name, "A discounted cash flow model of %s on the same template as my Skydance model. Public filings only." % name,
              "Project", h1, meta, lede,
              ([("In short", "In short", story(*short))] if short else []) +
              [("Why this company", why[0], P(*why[1])),
               ("The result", "The numbers", model_strip(name) + stat_html + P("These are model outputs under stated assumptions. Nothing on this page is a recommendation to buy or sell anything.")),
               ("How it is built", "Inputs that differ from the template", bul(build)),
               ("Charts", "In pictures", dfig(charts)),
               ("What I got wrong first", wrong[0], P(*wrong[1])),
               ("What would change the answer", "In order of how much they move it", bul(change)),
               ("Since the model", "What has moved since October", bul(since)),
               ("Download", "The model",
                '<p class="links"><a href="assets/%s">Download the Excel model</a> &nbsp;&middot;&nbsp; <a href="media.html">Back to the five</a></p>' % xlsx + P(extra_note))],
              banner=("assets/banners/%s.jpg" % fname.replace("dcf-", "").replace(".html", ""), "%s on the shared DCF template. Cost of capital, leverage and coverage from my model." % name))


company_dcf_page("dcf-nflx.html", "Netflix", "Netflix DCF model", "Built October 24, updated November 25, 2026. Excel, 312 formulas, 10 sources. Prices as of November 24.",
    "Netflix is the streaming business the other four are trying to build. At 15 times EBITDA, what does the price already assume?",
    ("The benchmark for the Skydance streaming line", [
        "Skydance's base case grows streaming 9 percent fading to 4. Netflix grew 13 percent in 2026 on $51 billion of revenue at a 31.5 percent operating margin. If I assume Skydance can grow streaming, I should know what the leader earns doing it and what the market pays for it.",
        "Netflix walked away from Warner Bros. Discovery in February 2026 with a $2.9 billion termination fee. I exclude that fee from cash flow."]),
    [("$52.02", "Perpetuity method, base case. The close was $58.87 on November 24, 2026."),
     ("$69.97", "Exit multiple at 14 times 2031 EBITDA."),
     ("4.0%", "Perpetual growth the price implies."),
     ("73%", "Share of value after 2031."),
     ("$36 to $84", "Bear to bull, both methods."),
     ("15.1x", "Market EV to 2026 EBITDA. Skydance trades at 9.")],
    ["<b>Base year.</b> 2026 guidance of about $51.1 billion of revenue and a 31.5 percent operating margin from the October 20 shareholder letter, split into subscription and about $2.7 billion of advertising.",
     "<b>Revenue.</b> Subscription grows 10 percent fading to 5. Advertising grows 40 percent fading to 15 off a small base, with 15 new ad markets in 2027.",
     "<b>EBITDA.</b> Operating income plus property depreciation only. Content amortization, $16.4 billion in 2025, stays inside costs. The margin rises about a point a year to 36 percent by 2031.",
     "<b>Content cash.</b> Netflix spends about 1.1 times what it amortizes. The excess, about 3.3 percent of revenue, sits in the working capital and content line and fades to 2 percent as spending growth slows.",
     "<b>Discount rate.</b> Unlevered beta 1.2, almost no leverage, so the WACC is close to the 10.4 percent cost of equity. Cost of debt 5.8 percent, the July 2026 notes repriced about 85 bp over today's Treasury.",
     "<b>Equity bridge.</b> $15.3 billion of gross debt, $8.2 billion of cash and 4,106 million shares, from the 10-Q cover. Stock compensation is already in operating income, so it is not taken out again."],
    [("m5_nflx_cash.png", "Base case EBITDA and free cash flow", "Both nearly double by 2031.", False),
     ("m5_nflx_football.png", "Where the answers land", "The price sits between the two methods.", False)],
    ("I took the quoted beta at face value", [
        "A beta of 1.61 taken from a quote page gave an 11.6 percent WACC and $42 a share. That beta is a five year regression on a stock that fell by half in 2022. I used 1.2 and recorded the reasoning, and the sensitivity grid runs from 8 to 11 percent so that a reader can restore the 1.61."]),
    ["<b>The exit multiple.</b> Each turn of EBITDA is worth about $4 a share. 14 times is below the 15 the market pays today and above where a company growing 5 percent should trade in 2031.",
     "<b>Margin ceiling.</b> The base case stops at 36 percent. Every point of terminal margin is worth about $1.50 a share.",
     "<b>Advertising.</b> The October 20 letter cut 2026 ad guidance from about $3 billion to $2.7 billion. Advertising is 5 percent of revenue. It is a small line that the market treats like a big one.",
     "<b>The share count.</b> On the diluted 4,195 million, every value on this page is about 2 percent lower."],
    "NFLX_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. Sources are numbered and cited next to each figure. Nothing in the model comes from a Bloomberg Terminal or from any employer.",
    short=("At 15 times EBITDA, what does the Netflix price assume?",
           "2026 guidance, content amortization kept in costs and a 10.3 percent WACC.",
           "$52.02 and $69.97 a share, against $58.87. The price needs 4.0 percent growth forever or 11 times EBITDA in 2031.",
           "The market prices it as the safest credit of the five and the richest equity."),
    since=["<b>The price.</b> $58.87 on November 24, from $65.85 in October. It moved toward the model.",
           "<b>Two corrections.</b> October took stock compensation out twice, worth about $1 a share, and used 58 million shares too many.",
           "<b>Buybacks.</b> $4.8 billion in the third quarter, well above a quarter of the year's free cash flow guidance."])

company_dcf_page("dcf-dis.html", "Disney", "Disney DCF model", "Built October 24, updated November 25, 2026. Excel, 325 formulas, 12 sources. Fiscal year ends around October 1. Prices as of November 24.",
    "The closest thing to Skydance that already runs as one company.",
    ("Skydance with parks and twenty years of integration", [
        "Disney has the same three pieces as the combined Skydance, studio, linear networks and streaming, and has already made them one company. Its Entertainment segment is the best public read on where Skydance's margins could settle. Experiences is the piece Skydance does not have, and it is more than half of Disney's operating income.",
        "The base year is fiscal 2026 as reported on November 17."]),
    [("$77.72", "Perpetuity method, base case. The price is $122.51."),
     ("$109.82", "Exit multiple at 10 times FY2032 EBITDA."),
     ("4.7%", "Perpetual growth the price implies."),
     ("68%", "Share of value after FY2032."),
     ("$32 to $133", "Bear to bull, both methods."),
     ("$9bn", "FY2027 capex guidance, after $8.7 billion in FY2026.")],
    ["<b>Base year.</b> Segment operating income of $19.7 billion, less $1.5 billion of corporate costs, plus $4.6 billion of depreciation. That is $22.8 billion of EBITDA, or $22.4 billion without the 53rd week.",
     "<b>Revenue.</b> Entertainment $48 billion growing 3 percent fading to 2, Sports $18.5 billion growing 3 fading to 2, Experiences $39 billion growing 6 fading to 4. The FY2027 total of $105.5 billion is within $100 million of consensus.",
     "<b>EBITDA.</b> One blended margin starting at 22.9 percent, in line with guidance, and drifting up to 24.2 as streaming scales. Restructuring of $300 million in FY2027 fading to zero.",
     "<b>Discount rate.</b> Unlevered beta 1.05, 0.2 debt to equity, cost of equity 10.3 percent, cost of debt 5.7 percent on a single A rating. WACC 9.4 percent.",
     "<b>Equity bridge.</b> $44.5 billion of borrowings, $6.7 billion of cash, $7.1 billion of noncontrolling interests and 1,708 million shares, all from the 10-K.",
     "<b>Stub.</b> 85 percent of FY2027 remains from November 24."],
    [("m5_dis_cash.png", "Base case EBITDA and free cash flow", "Cash flow steps up as capex comes down from the cruise ship peak.", False),
     ("m5_dis_football.png", "Where the answers land", "The price is above both methods.", False)],
    ("I tried to use the reported tax rate", [
        "Fiscal 2025 shows a tax benefit from a $3.3 billion Hulu item, so I could not use the reported rate. I use the same 23 percent cash rate as the other four, with the FY2024 derived 23.7 percent as the check.",
        "Then EBITDA itself. I said corporate costs were inside segment income. They are not. I also added back all of the depreciation and amortization line, and $1.0 billion of that is deal amortization segment income already leaves out. EBITDA was $2.3 billion too high."]),
    ["<b>Linear decline inside Entertainment.</b> Linear was $3 billion of the segment's $4.7 billion of operating income in FY2025. If it falls 10 percent a year and streaming does not fill the hole, the base case becomes the bear case.",
     "<b>Capex.</b> Each point of revenue in terminal capex is worth about $8 a share. The cruise ships are the reason this input matters.",
     "<b>Experiences growth.</b> The segment is 57 percent of operating income. Two points of growth there is worth more than five points in Sports."],
    "DIS_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. Nothing in the model comes from a Bloomberg Terminal or from any employer.",
    short=("What is Disney worth with linear networks shrinking?",
           "Reported FY2026, three segments and a 9.4 percent WACC.",
           "$77.72 and $109.82 a share, against $122.51. The price implies 4.7 percent growth forever.",
           "Experiences is 57 percent of operating income, and Skydance does not have it."),
    since=["<b>The base year.</b> Revenue was $102.3 billion and segment operating income $19.7 billion. I had estimated $101 billion and $19.7 billion. A 53rd week added about $1.6 billion and $490 million.",
           "<b>What the fixes did.</b> Corporate costs and the amortization took EBITDA down. Counting stock compensation once brought it back up, and net debt came in $3 billion lower. The perpetuity value went from $79.11 to $77.72.",
           "<b>Guidance.</b> For fiscal 2027, segment operating income up about 8 percent and free cash flow of about $11 billion after interest. My base case has $10.0 billion before interest, so it is the harsher one.",
           "<b>The price.</b> $110.16 in October, $122.51 on November 24."])

company_dcf_page("dcf-cmcsa.html", "Comcast", "Comcast DCF model", "Built October 24, updated November 25, 2026. Excel, 312 formulas, 14 sources. Prices as of November 24.",
    "The one company the model cannot reconcile with its price.",
    ("A media company that is breaking itself up", [
        "Comcast resembles what Skydance might look like after a decade, with cable, a studio, parks, a streaming service that has just turned profitable and 2.3 times leverage. It spun off its cable networks in January 2026 and will spin NBCUniversal and Sky in mid 2027, so it is becoming a broadband utility.",
        "I value it as it is today, before the spin, on nine months of 2026 actuals. That is the only basis the filings support."]),
    [("$49.05", "Perpetuity method, base case. The price is $25.38."),
     ("$36.13", "Exit multiple at 5.5 times 2031 EBITDA."),
     ("-5.1%", "Perpetual decline in cash flow the price implies."),
     ("3.9x", "Exit multiple the price implies. The market pays 4.9 today."),
     ("7.5%", "The WACC, lowest of the five. Nearly half the capital is debt."),
     ("70%", "Share of value after 2031.")],
    ["<b>Base year.</b> 2026 as now reported, without Versant and from the second quarter without Sky Deutschland. Nine months of $90.7 billion of revenue and $25.9 billion of adjusted EBITDA, annualized to $120.5 billion and $35 billion.",
     "<b>Revenue.</b> Two lines. Connectivity and Platforms, $79 billion, falls 1 percent a year then flattens as price offsets broadband losses. Content and Experiences, $41.5 billion net of eliminations, grows 2 percent.",
     "<b>EBITDA.</b> Margin 29 percent drifting down to 28. My own estimates of separation costs are $500 million in 2026, $800 million in 2027 and $300 million in 2028.",
     "<b>Cash flow.</b> Capex 9.5 percent of revenue. Depreciation of $16 billion a year shelters a lot of the profit from cash tax. That is a big reason cable cash flow is high relative to EBITDA.",
     "<b>Discount rate.</b> Unlevered beta 0.7, 0.9 debt to equity, levered beta 1.18, cost of equity 10.2 percent, cost of debt 5.9 percent. Market weights give 7.5 percent.",
     "<b>Equity bridge.</b> $87.4 billion of debt, $7.6 billion of cash, 3,551 million shares from the October 15 cover."],
    [("m5_cmcsa_cash.png", "Base case EBITDA and free cash flow", "About $18 billion of unlevered cash flow a year.", False),
     ("m5_cmcsa_football.png", "Where the answers land", "Almost every range starts above the price. It does not make me trust the model more.", False)],
    ("I believed the first answer", [
        "The first build gave $60 a share. When a model is that far from the price of a $78 billion company, the first thing to check is the model. I raised the beta, cut growth to 0.5 percent, cut the exit multiple to 5.5, put the cost of debt at 95 bp over Treasuries and ran the bear case harder. It still landed at $35 to $44 in October, and at $36 to $49 now that stock compensation comes out once. So I am not saying Comcast is cheap. I am showing what the price assumes, a decline of 5 percent a year forever, and leaving the reader to decide whether broadband and parks will do that."]),
    ["<b>The discount rate.</b> Each point of WACC is worth $8 to $15 a share on the perpetuity method. If the spin leaves the broadband company with a higher cost of debt, the value would change quickly.",
     "<b>Broadband losses.</b> Comcast is losing subscribers to fixed wireless and fiber. The bear case runs connectivity down 3 percent a year. The price implies a steeper decline.",
     "<b>The spin itself.</b> A sum of the parts after mid 2027 is a different model with two balance sheets, and the S-4 or Form 10 is the document to build it from.",
     "<b>Theme parks.</b> Segment EBITDA fell 17 percent in the third quarter of 2026 on a tough Epic Universe comparison. I grow the segment 2 percent, which may be generous."],
    "CMCSA_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. The 2026 base year is annualized from nine months and marked that way. Nothing in the model comes from a Bloomberg Terminal or from any employer.",
    short=("Why does the market pay 4.9 times EBITDA for Comcast?",
           "2026 annualized from nine months, two revenue lines, a 7.5 percent WACC and a hard bear case.",
           "$49.05 and $36.13 a share, against $25.38. The price implies cash flow falling 5.1 percent a year forever.",
           "Nearly half the capital is debt, so each point of WACC is worth $8 to $15 a share."),
    since=["<b>The price.</b> $25.38 on November 24, up from $22.04 and still below both methods.",
           "<b>One correction.</b> Comcast reports EBITDA after stock compensation and I took it out again. That was worth about $5 a share.",
           "<b>The spin.</b> The 10-Q still says mid 2027. Comcast can keep up to 19.9 percent for up to a year.",
           "<b>Ratings.</b> Moody's and S&amp;P put the company on review in June. I have not found either result."])

company_dcf_page("dcf-foxa.html", "Fox", "Fox and Roku DCF model", "Built October 24, rebuilt with Roku November 25, 2026. Excel, 466 formulas, 9 sources. Fiscal year ends June 30. Prices as of November 24.",
    "What Fox is worth now that it owns Roku, and how fast it can pay for it.",
    ("The company I modeled in October is gone", [
        "In October I modeled Fox alone, because Roku had not closed. It closed on November 6, so that company no longer trades. Fox paid about $14 billion of cash and 144 million shares, sold $8.4 billion of notes and took a $2 billion term loan.",
        "I rebuilt it from the pro forma 8-K/A, the notes prospectus and Roku's filings. A linear network company with almost no debt became a levered one that is part technology."]),
    [("$59.59", "Perpetuity method, base case. The average of the two share classes is $62.62."),
     ("$50.24", "Exit multiple at 8 times FY2032 EBITDA."),
     ("1.8%", "Perpetual growth the price implies."),
     ("3.3x", "Net debt to EBITDA. It was 0.6 before Roku."),
     ("3.9x", "EBITDA to interest, on about $1.1 billion a year."),
     ("$24 to $82", "Bear to bull, both methods.")],
    ["<b>Base year.</b> Fiscal 2026, pro forma. Fox has $17.1 billion of revenue and $3.9 billion of EBITDA. Roku has $5.2 billion and $0.7 billion before stock compensation. The $302 million they sell each other comes out.",
     "<b>Fox.</b> The same three lines and growth rates as in October. The margin holds at 22.8 percent in FY2027 after a World Cup quarter, then drifts to 20.",
     "<b>Roku.</b> Platform revenue grows 17 percent, fading to 8. The margin before stock compensation goes from 15 to 21 percent. That starts a little above Fox management's case in the proxy, since Roku has beaten it, and ends a little below. Stock compensation comes out on its own line.",
     "<b>Synergies.</b> $360 million of the $400 million target by FY2030. Each $100 million is worth about $1.80 a share.",
     "<b>One time cash.</b> About $680 million for Roku award payouts and integration. Fox has not disclosed an integration figure, so part of that is mine.",
     "<b>Taxes.</b> Roku's losses and credits save about $640 million over five years, worth about $1 a share. The limit after a change of ownership is not disclosed.",
     "<b>Discount rate.</b> Unlevered beta 0.93, with Fox at 0.6 and Roku at 1.4 weighted by deal value. Cost of equity 10.4 percent. Cost of debt 6.4 percent, from Fox's own November 10 year. WACC 8.8 percent.",
     "<b>Equity bridge.</b> $16.9 billion of debt, $2.75 billion of cash and 570 million shares. The prospectus table prints $4.4 billion of cash, and its own footnotes work out to $2.75 billion. I used the footnotes."],
    [("m5_foxa_cash.png", "Base case EBITDA and free cash flow", "Roku's growth covers the decline in cable.", False),
     ("m5_foxa_football.png", "Where the answers land", "The price is above both methods and inside the range.", False),
     ("m5_foxpath.png", "Gross leverage, year by year", "Back under 3.0 times by fiscal 2028 without buybacks, and by 2030 with them.", True)],
    ("I took stock compensation out twice", [
        "Fox's EBITDA is revenue less operating costs less overhead, so stock compensation is already out of it. My template took out another $140 million a year. Fixing that alone moves the October value from $72.52 to $76.31.",
        "I also wrote that Roku would close in the first half of 2027 at the earliest. It closed on November 6. And I credited fiscal 2026 to Super Bowl LX, which was on NBC. Fox's revenue grew 5 percent without it."]),
    ["<b>The discount rate.</b> A point of WACC is worth about $11 a share. Roku's beta is my judgment, and it is the biggest one here.",
     "<b>Roku's margin.</b> Each point, every year, is worth about $1.60 a share.",
     "<b>Roku's growth.</b> One more point of platform growth a year is worth about $1.20.",
     "<b>Cable decline.</b> One more point a year takes away about $0.80. It was $2 when cable was most of the company.",
     "<b>The lawsuit.</b> Newsmax has asked a court to unwind the deal, per the Washington Times. It is not in the model."],
    "FOXA_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. The debt, the paydown and the October numbers have their own sheets. Nothing in the model comes from a Bloomberg Terminal or from any employer.",
    short=("What is Fox worth now that it owns Roku?",
           "The deal pro formas, Roku's filings and an 8.8 percent WACC that weights the two businesses.",
           "$59.59 and $50.24 a share, against $62.62. Net leverage went from 0.6 to 3.3 times.",
           "Gross leverage gets under 3.0 by fiscal 2028 without buybacks, and not until 2030 with $1.5 billion a year."),
    since=["<b>The notes.</b> $8.4 billion in seven parts on November 10, from 85 bp over Treasuries at 3 years to 200 bp at 40. The 10 year came at 145 bp and yielded 6.435 percent.",
           "<b>The first quarter.</b> Revenue rose 22 percent to $4.6 billion. Free cash flow was $503 million, against negative $234 million a year earlier. The 10-Q credits the World Cup, so one quarter does not settle the weak fiscal 2026.",
           "<b>Ratings.</b> Baa2 and BBB, both stable, per the 10-K. I have not found a new action since the deal closed.",
           "<b>The advisers.</b> In the proxy, Roku's adviser put 8 to 11 times on the two together, before stock compensation. My 8 times is after it. Fox's adviser used 5.5 to 7.5 on Fox alone and 15 to 20 on Roku."])

# ---------- tender ----------
case_page("tender.html", "Tender Tracker", "A daily tracker of bond tender and exchange offers built from SEC filings and newswires, with its error rates published.",
          "Project, live", "Tender Tracker", "Personal project. October 2026 to now.",
          "A daily tracker of cash tender and exchange offers for corporate bonds.",
          [("In short", "In short",
            story("What does a bond tender look like in a record year, and can a free script keep the list?",
                  "SEC filings and three newswires, read by rules. AI reviewers graded them on filings the rules had not seen.",
                  "Two kinds. Through November 3, two thirds expired in four to seven business days and the rest ran about 20. About one in five changed after launch.",
                  "The fast tender is a refinancing. The slow one is a negotiation. Type and dates are right about nine times in ten, securities and caps three in four.")),
           ("What it does", "One row per offer, with a link to the filing",
            P("One row per offer, with its terms, its status and a link to the filing. It rebuilds every day from public filings and newswires.") +
            strip("tender", "The tracker now", "Read from the tracker's own feed. The analysis below is dated.") +
            '<span data-live="tender-chart" hidden></span>' +
            '<p class="links"><a href="https://ferrierotony-cmyk.github.io/market_dashboard/tender/">Open the tracker</a> &nbsp;&middot;&nbsp; <a href="%s" rel="noopener">Code</a></p>' % TENDER_CODE),
           ("How often it is right", "Nine in ten on type and dates, three in four on securities and caps",
            P("AI reviewers graded it against the filings on releases the rules had never seen. Offer type and dates were right about nine times in ten. Securities and caps were right about three times in four. Nobody has checked these rows by hand.") +
            P("The most common mistake is counting new notes being issued, or notes being redeemed, as the notes targeted. On the period the rules were built on, it found 32 of 33 offer releases. That is a best case. On October 26 I fixed the redeemed notes case and a few grouping errors. Those fixes have not been tested on new filings yet, so I do not claim a new number for them.") +
            P("The weakness was recall. Through October 26 the search only read Form 8-K exhibits with six phrasings, and it found 17 offers in 90 days. Many issuers never file an 8-K for a tender and issue only a press release. On October 27 I widened the SEC search to 54 phrasings and Form 6-K, added PR Newswire and Bing News as sources, and the same window went to 44 offers. Fourteen more came from issuer sites and wires the script cannot reach, typed in by hand with the source linked and tagged HAND on the page. The accuracy numbers above cover the rules only. They leave out the rows I typed in.")),
           ("What the data say so far", "Two kinds of tender, and which one a record year produces",
            '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in [('35', "Launches read from SEC filings, August 5 to November 3, 2026."), ('4 to 7 days', "To expiration for 21 of the 31 dated launches. None had an early deadline."), ('20 to 22 days', "The slower 9. Seven had an early deadline."), ('$500m', "Median cap across the 18 offers with a dollar cap."), ('9 of 50', "Offers extended or amended after launch."), ('$1.76tn', "US investment grade issuance through October 26, 2026. Bloomberg's count.")]) + '</div>' +
            P("The 14 hand rows are not in these counts. I would want a person to check the caps before anyone traded on them.", "I reran it on November 25 for launches since August 27. Fifteen from SEC filings had dates. Eight ran 4 to 10 weekdays with no early deadline, and seven ran 21 or 22 with one. The two kinds hold. The fast kind went from two thirds to about half.")),
           ("How it is built", "Two stages, no paid services",
            bul(["A fetch step searches EDGAR full text search for tender and exchange offer press releases, then PR Newswire and Bing News for releases that never reached EDGAR, and caches the text.",
                 "An offline rules step extracts offer type, securities, cap and dates, then groups releases into offers.",
                 "A GitHub Actions job runs both every morning and publishes the page. It costs nothing to run."]))], banner=("assets/banners/tender.jpg", "Filings and releases the tracker read, by weekday, August 27 to November 25. Orange is a step in a tender or exchange offer, grey is everything else."))

# ---------- dashboard ----------
case_page("dashboard.html", "Morning Market Dashboard", "A market dashboard that scores whether the new issue window is open, built in R from free data.",
          "Project, live", "Morning Market Dashboard", "Personal project. June 2026 to now.",
          "One screen for one question every morning: is the new issue window open?",
          [("In short", "In short",
            story("When the score says shut, what do spreads do next?",
                  "538 mornings on all seven rules, then 5,744 back to December 2003 on six rules and Moody's Baa spread.",
                  "No direction. Spreads were tighter 43 percent of the time, against 50. The five day move was bigger, 11.9 bp against 4.5.",
                  "It tells you how big the next move is likely to be. I would not use it to call spreads.")),
           ("What it does", "A score built from the inputs a syndicate desk watches",
            strip("tape", "Read when you open this page", "Each number shows its own time. Not a trading tool.") +
            P("Seven readings: VIX, MOVE, the one week move in IG and HY spreads, stock futures, the 10 year, and where spreads sit in their one year range. Built in R.") +
            '<p class="links"><a href="https://ferrierotony-cmyk.github.io/market_dashboard/">Open the dashboard</a> &nbsp;&middot;&nbsp; <a href="%s" rel="noopener">Code</a></p>' % REPO +
            '<a class="shot" href="https://ferrierotony-cmyk.github.io/market_dashboard/"><img src="https://ferrierotony-cmyk.github.io/market_dashboard/market_dashboard.png" alt="Dashboard snapshot: Treasury curve, 2, 10 and 30 year history, curve slope and credit spreads" loading="lazy" onerror="this.parentNode.style.display=\'none\'"></a><p class="note">The snapshot is rebuilt with the dashboard on weekdays.</p>'),
           ("Does the score mean anything", "It tells you size. It cannot tell you direction.",
            strip("window", "The long test, rerun each month", "Mornings after a challenging reading. The findings below are from November 25, 2026.") +
            '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in [
                ('43%', "Challenging mornings followed by tighter spreads. Other mornings, 50 percent."),
                ('11.9 bp', "Average five day move after a challenging morning. Otherwise 4.5 bp."),
                ('24%', "Followed by a widening of more than 10 bp. Otherwise 4 percent."),
                ('52 of 84', "Mornings before a widening of more than 20 bp that already read challenging."),
                ('1.3 a day', "Term sheets on 14 challenging mornings, against 3.0 on open ones. Rho with the score, 0.04."),
                ('Friday', "Moves the term sheet count more than the score does.")]) + '</div>' +
            dfig([("dash_long_test.png", "Where spreads were five days later", "Orange is after a challenging morning. The large moves are more common both ways.", True),
                  ("dash_backtest.png", "The first test, October 2024 to November 2026", "Orange marks the 14 challenging mornings. Ten of them are one event.", True)])),
           ("What the score said when nothing priced", "Two shutdowns, read after the fact",
            P("In April 2025 no investment grade deal priced after April 2, according to Reuters and Bloomberg. Paychex reopened the market on April 8. My rebuilt score read 9 of 14, selective, on April 3, and 2 of 14 on the morning the market came back.",
              "In March 2026 press reports describe three sessions without a deal before the market reopened on Monday, March 23. In the three sessions before that, the score read 11, 9 and 13 of 14. It said open the morning before the market came back.",
              "Headlines close the window before the levels do, and issuers come back before the levels recover. The score has no headlines in it and no calendar. A calendar is the first thing I would add.")),
           ("What I got wrong first", "Two quiet years and one large shock",
            P("The first version of this page said spreads tighten after a challenging morning 13 times out of 14, and that the score had never warned before a widening. I withdrew both. Ten of the 14 mornings were the April 2025 tariff episode, so I had four separate events. A rerun on current data adds October 23, 2026 and makes it 13 of 15. One rule did as well alone. When investment grade had widened by more than 8 bp over the prior week, spreads tightened 10 times out of 11.",
              "The test also started counting a day late. A morning only knows the prior close. I measured from the close of the same day, so I skipped the first move. Counted from the close the score knew, it is 11 of 15. The script now counts it that way.",
              "I also said the MOVE index and stock futures had only two years of public history. Both go back more than 20 years. The limit was the ICE spread series on FRED, which has carried only three years since April 2026.")),
           ("What it does not show", "The limits of both tests",
            P("The long test uses Moody's Baa yield over the 10 year, because the ICE index is no longer public that far back. The five day changes have a correlation of 0.79, but the levels do not match well. There is no high yield rule, and it uses cash S&amp;P closes.", "The 533 challenging mornings fall in about 50 episodes, so I resampled whole episodes. The 95 percent interval on 43 percent runs from 37 to 50, and on 24 percent from 13 to 30. LQD against IEF also shows no direction.", "The term sheet count is a proxy. It catches about three filings a day against ten or so deals. At 7am the newest spread print is two closes old, so the dashboard shows its date. The code for both tests is in the repo.")),
           ("What to know", "Free data only, and a sample portfolio",
            P("The public build uses free data feeds only. The portfolio panel on the public build is a sample book and is labeled as one. A private version on my laptop pulls Bloomberg data through the API, with ten panels on the Treasury curve, DV01, P&amp;L and credit spreads, and refreshes every morning. That version is not published."))],
          banner=("assets/banners/rates.jpg", "The 10 year Treasury and the Baa spread since 2015, two of the inputs behind the window score. FRED data."))

# ---------- fed liquidity lab ----------
case_page("lab.html", "Fed Liquidity Lab", "A weekly tracker of the Fed's balance sheet, inflation and output, with rules tested against buy and hold on public data.",
          "Project", "Fed Liquidity Lab", "Personal project. November 2026. Public data only.",
          "Net liquidity is the Fed's balance sheet less the Treasury's cash and the overnight reverse repo facility. I tracked it, then tested it.",
          [("In short", "In short",
            story("Does net liquidity tell you when to hold less stock?",
                  "FRED data, 18 rules, then a second design locked before I ran it.",
                  "No. 6.0 percent a year against 8.1 for buy and hold. The second design failed its own test.",
                  "A fair gauge of conditions and a poor timing signal. I would not trade on it.")),
           ("What it does", "A weekly tracker with alerts",
            strip("lab", "The latest reading", "FRED, read by the lab's own code. The tests below are dated.") +
            P("It pulls the Fed's balance sheet every week, tracks seven measures of inflation and the main gauges of output, and alerts me when a trigger is crossed. The scenarios replay past episodes. I would not read them as forecasts.") +
            plot("lab-chart", "Net liquidity, weekly since 2021", "The Fed's balance sheet less the Treasury's cash and reverse repo. FRED.") +
            '<p class="links"><a href="%s" rel="noopener">Code</a></p>' % LAB_CODE +
            dfig([("lab_liquidity.png", "Net liquidity, and what two past episodes would do to it", "As of November 2026. Net liquidity since 2021, and two past episodes replayed. Source: FRED.", True),
                  ("lab_inflation.png", "Inflation, seven ways", "As of November 2026. Left, year over year. Right, 3 month annualized. Source: FRED, Cleveland Fed.", True)])),
           ("What the tests say", "Two designs against buy and hold",
            '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in [
                ('6.0%', "A year for the rules since 2020, against 8.1 percent for buy and hold."),
                ('4.3 pts', "What the Sahm rule cost, the most of any rule."),
                ('3 of 4', "Criteria the locked design passed. It failed the one that counts."),
                ('6.6 pts', "How far it beat the same mix in 2008. It was behind in the other 13 years."),
                ('1.2', "Best t-stat out of sample. It needs 2 to tilt.")]) + '</div>' +
            dfig([("lab_backtest_v1.png", "The 18 rules against buy and hold", "Orange is the rules. White is buy and hold. Net of 5 bps costs. Source: FRED.", True),
                  ("lab_backtest_v2.png", "The locked design on a clean window", "It cut the 2008 loss and ended slightly ahead, inside the noise. Source: FRED.", True)]) +
            P("The second design used four fast nodes, with pass and fail fixed before I ran it. It failed, and I left it alone.")),
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

# ---------- credit toolkit ----------
KIT = [("AT&T", "3.7x", "5.8x", "Re-underwrite", "Leverage over my 3.5x limit"),
       ("Carnival", "3.3x", "6.2x", "Intact", "Nothing new since the 8-K of November 4"),
       ("Ford", "not read", "6.1x", "Intact", "Debt uses company tags, so it is flagged as a gap"),
       ("Apple", "0.5x", "not tagged", "Intact", "No triggers")]
kit_table = '<div class="tablewrap" data-kit><table class="cmp"><thead><tr><th>Issuer</th><th>Gross debt to EBITDA</th><th>EBITDA to interest</th><th>Route</th><th>Why</th></tr></thead><tbody>' + \
    "".join("<tr>" + "".join("<td>%s</td>" % e(v) for v in row) + "</tr>" for row in KIT) + "</tbody></table></div>"
case_page("creditkit.html", "Credit Research Toolkit", "Two Python scripts that spread an issuer from SEC filings and check a watchlist for credit triggers.",
          "Project", "Credit Research Toolkit", "Personal project. November 2026. Python and SEC EDGAR.",
          "Two scripts for the parts of a credit analyst's job that are the same every time.",
          [("In short", "In short",
            story("Can the routine half of credit work come straight from the filings?",
                  "Tagged SEC data, five fiscal years and the last twelve months, for any company that files in US GAAP.",
                  "AT&T at $159.6 billion and Carnival at $23.9 billion, both matching what the companies report. The first version had Carnival wrong.",
                  "Good for a first pass and for noticing a change. Someone still has to read the filing.")),
           ("What it does", "Spread, then watch",
            bul(["<b>Spread.</b> Revenue, EBITDA, free cash flow, leverage and coverage, with a sheet that names the tag and the filing behind every number.",
                 "<b>Watch.</b> It checks each name against limits I set for leverage, coverage and covenant room, and reads new 10-Ks, 10-Qs and 8-Ks.",
                 "<b>Route.</b> Every name comes out as broken, re-underwrite or intact, with the reason."])),
           ("The latest run", "Four names, checked every weekday", kit_table +
            '<p class="note" data-live="kit">Run on November 25, 2026.</p>' +
            P("The limits are samples I set to test the rules. Nothing here is a recommendation to buy or sell anything.")),
           ("Checked against the releases", "One match, one miss, one fix",
            P("I checked the debt against what each company reports. AT&amp;T came out at $159.6 billion in both. Carnival came out at $24.6 billion against $23.9 billion. The script took the principal tag for Carnival and the carrying value for AT&amp;T. Two bases in one comparison is a mistake. It now uses carrying value for every issuer, and Carnival comes out at $23.9 billion. Four offline tests cover the rule.")),
           ("How it is built", "Two scripts and a map",
            '<p class="links"><a href="%s/tree/public-live/tools/credit_toolkit" rel="noopener">Code</a></p>' % REPO + P("Python, with no paid data. I first drew a buy side credit process from idea to exit, then built the two steps that repeat most, spreading and surveillance. It caches what it pulls and remembers what it has already seen, so the second run only reports what is new.")),
           ("What it does not show", "The limits",
            bul(["<b>Reported EBITDA.</b> Nothing is added back. AT&amp;T's 2022 shows 10.1 times because of impairments.",
                 "<b>US GAAP only.</b> Some companies use their own debt tags. Ford does, so its leverage is blank.",
                 "<b>Finance arms.</b> They are consolidated. An analyst would split them out.",
                 "<b>Spreads and ratings.</b> There is no free feed, so spreads are typed in and rating actions are not read.",
                 "<b>The schedule.</b> It failed for a week on my laptop after I moved the folder, and nothing told me. A job that fails quietly is worse than no job. It now runs on GitHub every weekday, and a failed check sends me an email."]))],
          banner=("assets/banners/creditkit.jpg", "Gross debt to reported EBITDA, straight from the filings. The 10.1x is AT&T's 2022 impairments. The dashed line is my limit."))

# ---------- roles ----------
case_page("finsight.html", "Finsight", "Debt Capital Markets Analyst Intern at Finsight, December 2025 to September 2026.",
          "Role", "Finsight", "Debt Capital Markets Analyst Intern. New York. December 2025 to September 2026.",
          "A fintech platform that tracks the primary bond market. I collected the order books.",
          [("The job", "Collecting order books",
            P("Syndicate desks run the book, and none of them has to tell you what is in it. I called 30 plus banks for book sizes from talk to launch, and got the numbers out before the next update. Fifteen to twenty deals a day.")),
           ("A day on the desk", "A normal day, hour by hour", day_html()),
           ("High yield, then investment grade", "Two desks, two different markets",
            P("High yield in the spring, where every deal turns on the company. Investment grade over the summer, where much depends on the window.")),
           ("Deals I covered", "Transactions that stayed with me",
            bul(["<b>Alphabet's $25 billion offering.</b> Ten tranches out to 40 years, a book around $115 billion.", "<b>The Paramount Skydance exchange and tender offers.</b> It led to the tender tracker and the Skydance DCF.", "<b>Relative value comps.</b> Screens on tenor, rating and spread to gauge concession."])),
           ("The tenor screens", "Where does this print sit against every comparable deal since 2022?",
            P("I kept ten daily screens of the lowest spreads and lowest coupons printed in the 3, 5, 7, 10 and 30 year. They covered every investment grade deal back to 2022, by week, month and year. Each row had the issuer, ratings, size, call, final book, coupon, yield and spread. A check sheet held any prints that looked wrong until I had confirmed them.",
              "When a banker asked how a new 5 year compared, the answer was on a single screen. You judge concession by holding one deal up against a lot of others. There is no formula.")),
           ("The end of day tally", "What priced, where it came from, and how far it moved",
            P("Every afternoon the day's investment grade prints went into one table: issuer, rating, size, tenor, final book, leads, price talk, where it priced, the move from talk to print, and the identifiers. That table is where the morning wire's numbers came from.")),
           ("Volume against the Street", "Did the month come in where the desks said it would?",
            P("I tracked issuance volume against the Street's estimates by day, week and month, with deal counts, tranche size, talk to print, final book, attrition, concession and end of week trading. The daily sheet went back years, with holidays, zero days and Fed days marked. It is the table you open when someone says nothing prices in August.")),
           ("Backfilling the database", "Checking 2019 Latin America deals one by one",
            P("The platform's history had gaps. I checked a list of 2019 Latin American deals one by one against what the platform had and returned the missing, incorrect and doubtful entries as a task list. It was slow work, and it is what makes a dataset worth paying for.")),
           ("What I did on my own time", "Treating the internship like a full time job",
            bul(["I reached out to the syndicate bankers I was collecting books from, at BBVA, Scotiabank and HSBC, to learn how they read demand and set concession. I still speak regularly with three of them.",
                 "I taught myself the Bloomberg API in R and built the first version of the market dashboard, so that I could review the curve, DV01, spreads and new issue comps every morning.",
                 "I flew to New York in July at my own expense to work from the office for a few days and meet the team in person."])),
           ("Since Finsight", "ICE Fixed Income Forum at the NYSE, October 2026",
            P("ICE Fixed Income Forum at the New York Stock Exchange, October 21, 2026.") +
            photos([("nyse-podium", "The podium.", ""), ("nyse-seated", "The panel chairs, after the panel.", ""), ("nyse-podium-side", "Getting a feel for the room.", "")]))], banner=("assets/banners/d-finsight.jpg", "Illustration of an order book from price talk to print. Not a real deal."))
tc_stats = [
    ("$1M", "Virtual capital. Long only, no ETFs, no leverage."),
    ("WLS", "The benchmark. Losing less than the index can win."),
    ("20%", "Position limit. Ours is lower."),
    ("2,600+", "Teams in the fall 2025 edition."),
    ("5 weeks", "October 12 to November 13."),
    ("4 lanes", "Book, pitches, trade log, earnings calendar."),
]
tc_stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in tc_stats) + "</div>"
case_page("bloomberg.html", "Bloomberg at UMass Lowell", "Bloomberg Terminal Assistant at UMass Lowell since September 2026, and captain of the UML team in the Bloomberg Global Trading Challenge.",
          "Role", "Bloomberg at UMass Lowell", "Terminal Assistant, September 2026 to now. Trading Challenge captain, fall 2026. Investment Analyst, spring 2026 round.",
          "I train students on the Terminal, pull data for faculty and captain the UML trading team.",
          [("Terminal Assistant", "Training and data pulls",
            bul(["Training across 10 classes, from SRCH and YAS to curves and spreads.", "Data pulls for faculty research. The green bond study began as one."])),
           ("One pull in detail", "ESG scores for 2,172 US listed companies",
            P("A professor asked whether the terminal had ESG scores. I screened every US listed company with a Bloomberg ESG score, pulled ten years of history plus the current MSCI, Sustainalytics and S&P scores, and sent a values only file with a field guide tab. I made two mistakes before getting it right. The first list was built by hand and contained duplicate tickers, and the first file still had live Bloomberg formulas in it.")),
           ("The Trading Challenge", "A university competition run entirely inside the terminal", tc_stat_html +
            P("UMass Lowell's teams are run by Professor Weicker. I was an analyst on the spring 2026 round, and I captain the fall 2026 team.")),
           ("How I run the team", "Four lanes and a rule set written down before the first trade",
            bul(["<b>Lanes.</b> I own the book, the final decision on every trade and the sizing. Two analysts pitch names with a one line summary covering what the company is, why now, the catalyst and its date, and what would invalidate the idea. One member keeps the trade log and another owns the earnings calendar.",
                 "<b>Entry rule.</b> We only buy a stock that is above its open and beating the WLS benchmark that morning. We do not buy names that are falling.",
                 "<b>Sizing and exits.</b> We keep position caps below the 20 percent limit and write down an exit for every name before it enters the book. The log records the reason for every trade.",
                 "<b>The screens.</b> EQS for candidates, EE and ANR for what is priced in, the earnings calendar, N and CN for news, GP for charts, PORT for exposures. My R dashboard points at the book for the daily snapshot."])),
           ("The book", "Two energy names and four passes",
            P("On October 12 we bought Exxon and Chevron after oil rebounded. We passed on Goldman Sachs, Nvidia, ASML and General Dynamics. The window closed on November 13. I will post the official result when there is one, good or bad.")),
           ("What past winners did", "Volatility backed by a thesis",
            P("Past winners focused on earnings and catalysts inside the window. They did not sit in safe long term holdings. RIT's 2024 team leaned into volatility and foreign names. USF's 2025 captain ran an earnings volatility book. The fall 2025 grand prize team from the Chinese University of Hong Kong won on discipline and Bloomberg's own data.",
              "The cautionary example is a team that took a large early bet, rose 18 percent, moved to cash and was not invited to the finals because the judges decided it was not investing. For that reason every name in our book has a written thesis, and we keep the log clean enough to show a judge.")),
           ("What I am learning", "Equities are not my home market",
            P("My background is in bonds. A long only equity book scored against an index is a different game. Two weeks of it taught me more about sizing, and about passing on a trade, than anything I had read. The rule that kept us out of tech during CPI week is now my risk management example.")),
           ("Sources", "Where the competition facts come from",
            '<p class="note">Bloomberg press release on the fall 2025 edition, January 2026. Bloomberg for Education challenge page. TUM School of Management challenge page for the 2026 format. Our rules, trades and passes are from my own trade log.</p>')], banner=("assets/banners/d-bloomberg.jpg", "Ten classes and the Trading Challenge book. Drawn from the numbers on this page."))
wacc = [
    ("4.2%", "Risk free rate on the valuation date."),
    ("1.16", "Beta from four clean peers, relevered."),
    ("5.0%", "Equity risk premium, Kroll."),
    ("7.06%", "Size premium, Kroll microcap decile. The biggest judgment."),
    ("0%", "Company specific premium. Those risks are in the forecast."),
    ("16.8%", "The WACC, 97.7 percent equity."),
]
wacc_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in wacc) + "</div>"
case_page("valuation.html", "2026 Valuation Challenge", "Valuation Analyst on the UMass Lowell team in the 2026 Business Valuation Challenge: discount rate, DCF, LBO and public comparables.",
          "Competition", "2026 Valuation Challenge", "Valuation Analyst. UMass Lowell team led by Professor Sangphil Kim. September to October 2026.",
          "We valued a Gulf Coast engineering contractor for an ESOP. I was responsible for the discount rate, the DCF, the LBO and the public comparables.",
          [("In short", "In short",
            story("What is a private engineering contractor worth to an ESOP?",
                  "A 16.8 percent discount rate, a five year DCF, an LBO check, and public peers for beta only.",
                  "The two DCF methods landed within 1 percent of each other. The LBO came close.",
                  "The size premium is the whole gap between public and private multiples, so public multiples got zero weight.")),
           ("The competition", "A 25 minute recorded valuation, no questions allowed",
            P("The competition is run out of Georgia State University. Round 1 is a recorded presentation of up to 25 minutes with no live questions, and the top five teams advance to the in person final. We submitted on October 19, 2026.",
              "With no question period, every judgment has to hold up inside the video. Each of my four slides is built to answer the question a judge would otherwise ask.")),
           ("My four slides", "Risk, value, a buyer's check, and what public peers can and cannot tell you",
            bul(["<b>Discount rate.</b> What return does a buyer need to own this risk? I built the cost of capital in layers and landed at 16.8 percent.",
                 "<b>Discounted cash flow.</b> What are the cash flows worth at that rate? A five year forecast to 2031, tested two ways, growing forever at 2 to 3 percent or selling at 4.5 to 5.5 times EBITDA. The two methods landed within 1 percent of each other.",
                 "<b>Leveraged buyout.</b> Could a real buyer pay that? I modeled a private equity purchase at 2.5 times EBITDA of debt, kept low because a bonded contractor cannot carry heavy leverage, and solved for the most a fund could pay at its target return. It landed close to the DCF, so the LBO became a floor and a check, with zero weight in the conclusion.",
                 "<b>Guideline public companies.</b> What do public peers tell you? They tell you about risk. They tell you much less about price. I used the peer set for beta only. Companies worth $4.7 billion to $16.8 billion with hundreds of projects and liquid stock say little about a control sale of a private contractor with two owners, so their multiples carried zero weight."])),
           ("The discount rate build", "Six inputs and one big judgment", wacc_html +
            '<ul class="figs"><li class="full light"><figure><a class="img" href="assets/figures/val_discount_rate.png"><img src="assets/figures/val_discount_rate.png" alt="Discount rate slide: cost of debt 5.93 percent after tax, cost of equity 17.06 percent, WACC 16.80 percent" loading="lazy"></a><figcaption><b>The slide as submitted</b>My discount rate page from the deck. The company, its figures and the conclusion stay off this site.</figcaption></figure></li></ul>' +
            P("Without the size premium the implied multiple goes from about 5 times to about 10.")),
           ("Where I disagreed with management", "The disagreement was about growth",
            P("Management projected revenue growth of 6.5 to 7.5 percent a year. The company had missed its own 2025 budget and new orders had been flat. I accepted 2026 because backlog supported it, then faded growth to 2.5 percent by 2031. All of the difference between our value and management's case comes from that growth call. None of it is margins. The DCF runs on a 6.5 percent mid cycle margin, a normal year.")),
           ("What I would do differently", "Three things the judges could have pushed on",
            bul(["<b>Four betas is thin.</b> Four clean betas beat eleven noisy ones, but every reasonable change to the beta still kept the value inside our range, and I should have shown that range on the slide.",
                 "<b>The 10 year or the 20 year Treasury.</b> Kroll pairs its 5 percent premium with the 20 year yield, which was 4.65 percent. Using it would have raised the WACC to about 17.2 percent and cut the value by under 3 percent, still inside the range. I used 4.2 percent and should have footnoted the choice.",
                 "<b>Bonding caps leverage harder than I modeled.</b> At 2.5 times EBITDA the contractor's tangible net worth goes negative, which a surety would not accept. A 1.5 times case lowers the LBO ceiling and does not change the conclusion, but it is the more defensible figure."])),
           ("Process", "Three mock presentations and a content freeze",
            P("We held three mock presentations between September 18 and early October, froze the content on October 9 and recorded on October 10 and 11. My segment ran six minutes fifty in the second mock against a target of four and a half, so I spent the last two weeks cutting the script.",
              "The company and the data room are confidential, so the dollar figures stay off this page. The method and the judgment calls are mine."))], banner=("assets/banners/valuation.jpg", "The cost of capital build, from a 4.2 percent risk free rate to a 16.8 percent WACC. Every input here is already on the public slide."))
open(os.path.join(OUT, "trading.html"), "w", encoding="utf-8").write('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=bloomberg.html"><title>Bloomberg Global Trading Challenge | Anthony Ferriero</title><link rel="canonical" href="bloomberg.html"></head><body><p>Moved to <a href="bloomberg.html">Bloomberg at UMass Lowell</a>.</p></body></html>')
case_page("finance-society.html", "UML Finance Society", "President of the UML Finance Society since April 2026.",
          "Leadership", "UML Finance Society", "President. April 2026 to now.",
          "I lead a nine person executive board for a student finance club of over 500 members.",
          [("What changed", "500 members, a nine person board and well attended events",
            '<img class="logo" src="assets/umlfs-logo.svg" alt="UMLFS, UMass Lowell Finance Society" width="520" height="150">' +
            P("Membership has grown by 200+ to over 500. The board has nine members, and each owns an area.")),
           ("This fall", "What we ran this fall",
            bul(["<b>September 21.</b> From Gold to Tokens, with Professor Ravi Jain.", "<b>September 22.</b> Boston Fintech Week at the Boston Fed.", "<b>September 25.</b> The Fintech That Thinks career summit.", "<b>October 1.</b> Corporate financial acumen with Kim Kinsley of Pratt &amp; Whitney.", "<b>October 28.</b> Link Up, a LinkedIn workshop with the Real Estate Club.", "<b>November 19.</b> The Future of Trading on Wall Street, a fireside chat."])),
           ("What I am building for after me", "An analyst group the next board runs",
            P("The group produces a weekly market newsletter and a case every three weeks. It is run by the two youngest e-board members and has four new analysts, and the top case team is recognized on LinkedIn. It gives members who want an e-board seat a way to earn one. It also means the club does not depend on whoever is president.")),
           ("Photos", "This fall so far",
            photos([
                ("fintech-rooftop", "On the roof of the Boston Fed, Boston Fintech Week, September 22.", ""),
                ("fintech-career-summit", "Crack the Fintech Career Code, the student panel at the Boston Fed.", ""),
                ("guest-speaker", "A guest speaker session with Bob Landry of H‑E‑B.", ""),
                ("babylon-talk", "Babylon to Blockchain, presented by Professor Ravi Jain, September 21.", ""),
                ("babylon-podium", "Opening the evening.", ""),
                ("resume-recharge-1", "Resume Recharge, with the Finance Society among the hosts.", ""),
            ])),
           ("Partnerships", "Getting members in rooms they could not get into alone",
            P("I am working to get UMass Lowell into the Mass Fintech Hub so the Boston Fintech Week tickets come every year. I am also talking with CFA Society Boston about getting members into their events. And I am setting up alumni site visits, starting with a trip to New York."))], banner=("fs-fireside", "After our fireside chat, The Future of Trading on Wall Street, November 19, 2026."))
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
                ("sales-award", "Speed Sell, fourth place, at the Challenger Sales Institute invitational, March 26, 2026.", ""),
                ("sales-comp-day", "Competition day in the Manning School, April 2026.", ""),
            ], " duo"))], banner=("sales-certificates", "Two UMass Lowell placings on the same day."))
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
            P("The newsletter's rates section follows the shape of this curve and the credit spreads on top of it. The inversion that began in 2022, and the way it unwound, has been my main subject for two years."))], banner=("ccr-elward", "With Nick Elward of Natixis after the Commonwealth Capital Research fireside chat."))
case_page("consulting.html", "Mill City Consulting", "Research and due diligence for a UMass Lowell student consulting client.",
          "Role", "Mill City Consulting", "Research and due diligence lead. UMass Lowell student consulting group.",
          "The client was a six lane duckpin bowling alley that has been open since 1931, with new owners and no financial system.",
          [("In short", "In short",
            story("Can two new owners run a 1931 duckpin alley with no books?",
                  "Owner interviews, revenue by line, and a question bank I wrote.",
                  "Leagues were about 87 percent of revenue, parties 9, food and drink 4. The risk was the pinsetters.",
                  "A subscription business with one point of failure.")),
           ("The client", "Leagues, parties, and 1960s pinsetters",
            P("Two owners had recently bought the business. Leagues were about 87 percent of revenue, parties 9 and food and drink 4. Its strengths were its position as one of the last duckpin houses in the region, owners who do their own repairs and an active Facebook following. Its weaknesses were fragile sixty year old machines, no website and no formal books.")),
           ("What we built", "Visibility first",
            bul(["An Excel financial tracker with a live profit and loss, so the owners could see the business for the first time.",
                 "A QR code payment setup, a website, new signage and a brand story.",
                 "An introduction to the UML engineering department about the pinsetters."])),
           ("What I owned", "The question bank",
            P("My part was research and due diligence. I wrote the five section client question bank the group uses on new engagements: understanding the business, current operations, customers and market, pain points, and goals. I presented it to the next Mill City cohort in September 2026.")),
           ("Photos", "Presenting the work",
            photos([("class-presenting", "Presenting the research and due diligence template.", ""), ("class-team", "The team after the presentation.", "")], " duo"))], banner=("mill-city", "The Mill City Consulting team."))
case_page("education.html", "Education", "Business Administration at UMass Lowell, expected graduation May 2027.",
          "Education", "UMass Lowell", "Bachelor of Science in Business Administration. Expected May 2027.",
          "My concentrations are Finance and Marketing, with a minor in Quantitative Economics. My GPA is 3.6 out of 4.0.",
          [("Coursework", "Relevant classes", pills(["Financial Derivatives", "Financial Institutions and Markets", "Financial Statement Analysis"])),
           ("Certifications", "Credentials", pills(["Capital Markets and Securities Analyst, CMSA", "Bloomberg Finance Fundamentals", "Spreadsheet Analysis"]))], banner=("babylon-panel", "With Professor Ravi Jain and the Donahue Center team before From Gold to Tokens, September 21."))
case_page("skills.html", "Skills", "Tools, models and data skills.",
          "Skills", "Tools and certifications", "Terminal, code, models and AI tools.",
          "What I use to read the bond market and to build and test the work on this site.",
          [("Technical", "Tools and data", pills(["Bloomberg Terminal", "BQL", "SRCH, YAS, DES, GC", "Refinitiv", "R", "Stata", "Excel", "DCF and LBO modeling", "SEC filings"])),
           ("Certifications", "Credentials", pills(["Capital Markets and Securities Analyst, CMSA", "Bloomberg Finance Fundamentals", "Spreadsheet Analysis"])),
           ("AI tools", "How I use them", pills(["Claude", "ChatGPT", "Microsoft Copilot", "Google Gemini"]) +
            P("I use Claude to help write and debug code and to screen first pass matches in the research. I test the results myself before relying on them."))], banner=("assets/banners/skills.jpg", "The screens and tools behind the work on this site."))
case_page("contact.html", "Contact", "Contact Anthony Ferriero.", "Contact", "Get in touch", "Lowell, Massachusetts.",
          "The fastest way to reach me is email.",
          [("Where to find me", "Email first",
            '<div class="two"><div>' +
            '<div class="hero-cta contact-cta"><a class="btn primary" href="mailto:%s">Email me <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a><a class="btn outline" href="%s" rel="noopener">LinkedIn</a><a class="btn outline" href="%s" rel="noopener">GitHub</a></div>' % (EMAIL, LINKEDIN, GITHUB) +
            '<p class="note"><a href="mailto:%s">%s</a><br>Lowell, Massachusetts. I can be in Boston or New York on short notice.</p>' % (EMAIL, EMAIL) +
            P("I graduate in May 2027. I want to work in credit research, syndicate or debt capital markets.") + '</div>' +
            '<div><figure class="banner photo"><img src="assets/photos/careers-stairs.jpg" alt="Anthony Ferriero on campus"><figcaption>On campus.</figcaption></figure></div></div>')], banner=("assets/banners/d-contact.jpg", "Lowell, with Boston and New York as rings. Schematic, not to scale."))
# projects hub page
case_page("projects.html", "Work", "Projects, roles, competitions and leadership, each with its own case file.", "Projects", "Work", "Projects, roles, competitions and leadership.",
          "The parts of a credit, syndicate and DCM job I can do with public data, and the roles behind them.",
          [("Projects", "Projects", card_group(("Project",))), ("Roles", "Roles", pick("finsight.html", "bloomberg.html", "ccr.html", "consulting.html")), ("Competitions", "Competition", card_group(("Competition",))),
           ("Leadership", "Leadership", card_group(("Leadership",))), ("Education", "Education and skills", card_group(("Education", "Skills")))])
# experience and leadership hub pages
case_page("experience.html", "Experience", "Roles, projects and competitions in order.", "Experience", "Experience", "Internship, campus roles and competitions.",
          "Everything is listed in date order with the most recent first, and each entry opens its case file.",
          [("Timeline", "Roles, projects and competitions", tl)], banner=("nyse-stage", "On stage at the NYSE after the ICE Fixed Income Forum, October 21, 2026."))
lead = card_group(("Leadership",))
case_page("leadership.html", "Leadership", "Finance Society and Sales Team leadership.", "Leadership", "Leadership", "Two teams at UMass Lowell.",
          "I lead the Finance Society and captain the sales team.",
          [("Roles", "Finance Society and Sales Team", lead),
           ("Photos", "With the teams", photos([("fintech-rooftop-2", "Boston Fintech Week, on the roof of the Boston Fed.", ""), ("resume-recharge-2", "Resume Recharge, with the Finance Society and campus partners.", ""), ("club-fair", "The involvement fair table in the Honors College.", ""), ("fs-social", "Members at a Finance Society event.", ""), ("fs-lunch", "At a Finance Society event with a member.", "")]))], banner=("fs-group", "The Finance Society at an event by the water."))

open(os.path.join(OUT, "live.js"), "w", encoding="utf-8", newline="\n").write(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "psky", "live.js"), encoding="utf-8").read())
open(os.path.join(OUT, "tokens.css"), "w", encoding="utf-8", newline="\n").write(TOKENS_CSS)
open(os.path.join(OUT, "style.css"), "w", encoding="utf-8", newline="\n").write(SITE_CSS + focal_css() + vt_css())
print("built", sorted(os.listdir(OUT)))
