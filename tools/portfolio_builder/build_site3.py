"""Builds the dark portfolio into OUT (which already holds assets/). Navy base, terminal amber accent, one quote board as the signature element."""
import os, sys, html

OUT = sys.argv[1]
EMAIL = "ferrierotony@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/anthony-ferriero"
GITHUB = "https://github.com/ferrierotony-cmyk"
REPO = "https://github.com/ferrierotony-cmyk/market_dashboard"
TENDER_CODE = "https://github.com/ferrierotony-cmyk/market_dashboard/tree/tender-lab/tender"

import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "psky"))
from widgets import WIDGET_CSS, GLOBAL_JS, explorer_html, POWER_HTML, day_html
from cine import CINE_CSS, CINE_JS, split, band, marquee, cine_head
import cine as _cine
_cine.AI_DIR = OUT

CSS = r"""
:root {
  --bg: #FFFBF5; --bg2: #FFF4E8; --surface: #FFFFFF; --surface2: #FFF4E8; --line: #F1E4D3; --line2: #E5D2BB;
  --ink: #1F2A44; --muted: #5B6478; --amber: #C2410C; --amber-deep: #9A3412; --amber-ink: #ffffff; --accent: #C2410C;
  --display: "Nunito", system-ui, -apple-system, "Segoe UI", sans-serif;
  --body: "Nunito", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "Nunito", system-ui, -apple-system, "Segoe UI", sans-serif;
  --t-peach: #FFE8D6; --t-sage: #E3EFE4; --t-sun: #FFF1C9; --t-sky: #DCEBFA;
  color-scheme: light;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: var(--body); font-size: 17px; line-height: 1.65; -webkit-font-smoothing: antialiased; }
body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background: radial-gradient(900px 500px at 85% -10%, rgba(242,106,27,.08), transparent 60%); }
a { color: var(--amber); text-decoration-color: rgba(242,106,27,.45); text-underline-offset: 3px; }
a:hover { text-decoration-color: var(--amber); }
:focus-visible { outline: 2px solid var(--amber); outline-offset: 3px; border-radius: 3px; }
.skip { position: absolute; left: -999px; top: 8px; background: var(--surface); padding: 8px 12px; border: 1px solid var(--line); z-index: 20; }
.skip:focus { left: 8px; }
.wrap { position: relative; z-index: 1; max-width: 1120px; margin: 0 auto; padding-left: max(22px, env(safe-area-inset-left, 0px)); padding-right: max(22px, env(safe-area-inset-right, 0px)); }
h1, h2, h3 { font-family: var(--display); font-weight: 700; letter-spacing: -0.02em; margin: 0; text-wrap: balance; }

/* header */
.site-head { position: sticky; top: 0; z-index: 10; background: rgba(11,11,12,.88); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); }
.bar { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 62px; flex-wrap: nowrap; }
.brand { font-family: var(--display); font-weight: 800; font-size: 1.3rem; letter-spacing: -0.02em; color: var(--ink); text-decoration: none; }
.brand i { font-style: normal; color: var(--amber); }
.nav { display: flex; gap: 2px; list-style: none; margin: 0; padding: 0; }
.nav a { display: block; padding: 6px 10px; font-size: 14.5px; font-weight: 500; color: var(--muted); text-decoration: none; border-radius: 6px; white-space: nowrap; }
.nav a:hover { color: var(--ink); background: var(--surface); }
.nav a[aria-current="page"] { color: var(--amber); background: rgba(242,106,27,.12); }
.menu-btn { display: none; font: inherit; font-size: 14px; font-weight: 600; color: var(--ink); background: var(--surface); border: 1px solid var(--line2); border-radius: 6px; padding: 6px 12px; cursor: pointer; }
@media (max-width: 900px) {
  .menu-btn { display: inline-block; }
  .nav { display: none; position: absolute; left: 0; right: 0; top: 100%; flex-direction: column; background: var(--bg2); border-bottom: 1px solid var(--line); padding: 8px max(22px, env(safe-area-inset-left, 0px)) 14px; }
  .nav.open { display: flex; }
  .nav a { padding: 10px 6px; font-size: 16px; }
}

/* hero, after shadcn hero-34: text on a muted panel, image bleeding the other column */
.hero-wrap { padding-top: 40px; }
.hero { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); background: var(--surface); border: 1px solid var(--line2); border-radius: 16px; overflow: hidden; box-shadow: 0 40px 80px -50px rgba(0,0,0,.9); }
.hero-text { min-width: 0; padding: 56px 48px 52px; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; text-align: left; }
.badge { display: inline-block; font-family: var(--mono); font-size: 12.5px; color: var(--amber); border: 1px solid var(--line2); background: var(--bg2); border-radius: 999px; padding: 5px 12px; margin: 0 0 20px; }
h1 { font-size: clamp(2.6rem, 5.4vw, 4.4rem); line-height: 1; letter-spacing: -0.035em; font-weight: 700; margin: 0; }
h1 i { font-style: normal; color: var(--amber); }
.tag { font-size: 1.12rem; line-height: 1.6; max-width: 30em; margin: 20px 0 0; color: var(--muted); }
.hero-cta { display: flex; flex-wrap: wrap; gap: 12px; margin: 28px 0 0; }
.btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; border-radius: 8px; font-weight: 600; font-size: 15px; text-decoration: none; border: 1px solid transparent; transition: background .15s, border-color .15s, color .15s; }
.btn.primary { background: var(--amber); color: var(--amber-ink); }
.btn.primary:hover { background: var(--amber-deep); }
.btn.outline { border-color: var(--line2); color: var(--ink); background: transparent; }
.btn.outline:hover { border-color: var(--amber); color: var(--amber); }
.btn svg { width: 16px; height: 16px; }
.contact-row { display: flex; flex-wrap: wrap; gap: 8px 20px; margin: 26px 0 0; font-size: 14.5px; font-weight: 500; }
.contact-row a { overflow-wrap: anywhere; text-decoration: none; color: var(--muted); border-bottom: 1px solid var(--line2); padding-bottom: 1px; }
.contact-row a:hover { border-bottom-color: var(--amber); color: var(--amber); }
.hero-img { min-width: 0; min-height: 420px; position: relative; background: #fff; }
.hero-img img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: center top; display: block; }
@media (max-width: 420px) { .hide-s { display: none; } }
@media (max-width: 760px) {
  .hero-wrap { padding-top: 24px; }
  .hero { grid-template-columns: 1fr; }
  .hero-text { padding: 36px 22px 34px; align-items: center; text-align: center; }
  .tag { margin-left: auto; margin-right: auto; }
  .hero-cta, .contact-row { justify-content: center; }
  .hero-img { min-height: 0; aspect-ratio: 1; order: -1; }
}

/* live tape from the dashboard */
.tape { display: none; margin: 14px 0 0; background: #0e0e10; border: 1px solid var(--line2); border-radius: 12px; overflow: hidden; }
.tape.on { display: block; }
.tape-head { display: flex; justify-content: space-between; gap: 12px; padding: 9px 18px; font-family: var(--mono); font-size: 12.5px; color: var(--muted); border-bottom: 1px solid var(--line); background: var(--bg2); }
.tape-head b { color: var(--amber); font-weight: 500; }
.tape ul { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
.tape li { padding: 12px 18px; border-right: 1px dashed var(--line); font-size: 13px; color: var(--muted); }
.tape li:last-child { border-right: 0; }
.tape li b { display: block; font-family: var(--mono); font-weight: 500; font-size: 1.15rem; color: var(--ink); }
.tape li b.good { color: #4fc38a; } .tape li b.warn { color: var(--amber); } .tape li b.bad { color: #e45b5b; }
.tape li small { font-family: var(--mono); font-size: 11.5px; }
.tape-foot { padding: 8px 18px; font-size: 12.5px; color: var(--muted); border-top: 1px solid var(--line); }

/* quote board: the signature element */
.board { margin: 10px 0 0; background: #0e0e10; border: 1px solid var(--line2); border-radius: 12px; overflow: hidden; box-shadow: 0 30px 60px -40px rgba(0,0,0,.9); }
.board-head { display: flex; justify-content: space-between; gap: 12px; padding: 10px 18px; font-family: var(--mono); font-size: 12.5px; color: var(--muted); border-bottom: 1px solid var(--line); background: var(--bg2); }
.board-head b { color: var(--amber); font-weight: 500; }
.board ul { list-style: none; margin: 0; padding: 6px 0; display: grid; grid-template-columns: 1fr 1fr; }
.board li { display: grid; grid-template-columns: 1fr auto; gap: 14px; align-items: baseline; padding: 11px 18px; border-bottom: 1px dashed var(--line); font-size: 15px; color: var(--muted); animation: rowin .5s both; }
.board li:nth-child(odd) { border-right: 1px dashed var(--line); }
.board li:nth-last-child(-n+2) { border-bottom: 0; }
.board li b { font-family: var(--mono); font-weight: 500; font-size: 1.15rem; color: var(--amber); letter-spacing: -0.01em; }
.board li span { color: var(--ink); }
.board li small { display: block; font-size: 13px; color: var(--muted); }
.board li:nth-child(1) { animation-delay: .05s } .board li:nth-child(2) { animation-delay: .12s } .board li:nth-child(3) { animation-delay: .19s } .board li:nth-child(4) { animation-delay: .26s }
.board li:nth-child(5) { animation-delay: .33s } .board li:nth-child(6) { animation-delay: .40s } .board li:nth-child(7) { animation-delay: .47s } .board li:nth-child(8) { animation-delay: .54s }
@keyframes rowin { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
@media (max-width: 700px) { .board ul { grid-template-columns: 1fr; } .board li:nth-child(odd) { border-right: 0; } .board li:nth-last-child(-n+2) { border-bottom: 1px dashed var(--line); } .board li:last-child { border-bottom: 0; } }

/* sections */
.section { padding: 44px 0; border-top: 1px solid var(--line); }
.label { font-family: var(--mono); font-size: 13.5px; color: var(--amber); margin: 0 0 10px; }
h2 { font-size: clamp(1.6rem, 3.6vw, 2.3rem); line-height: 1.12; margin: 0 0 16px; }
.section p { max-width: 62ch; margin: 0 0 14px; }
.section p:last-child { margin-bottom: 0; }
.two { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap: 28px 48px; }
.two > div { min-width: 0; }
@media (max-width: 760px) { .two { grid-template-columns: 1fr; } }

/* now list */
.now { list-style: none; margin: 0; padding: 0; display: grid; gap: 0; max-width: 62ch; }
.now li { display: grid; grid-template-columns: 7.5rem 1fr; gap: 16px; padding: 12px 0; border-top: 1px dashed var(--line); }
.now li:first-child { border-top: 0; }
.now li span { font-family: var(--mono); font-size: 13.5px; color: var(--muted); padding-top: 3px; }
@media (max-width: 520px) { .now li { grid-template-columns: 1fr; gap: 2px; } }

/* case files */
.cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 14px 0 28px; padding: 0; list-style: none; }
h3.group { font-family: var(--mono); font-weight: 500; font-size: 13.5px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin: 26px 0 0; padding-top: 18px; border-top: 1px solid var(--line); }
h3.group:first-of-type { margin-top: 10px; border-top: 0; padding-top: 0; }
.card { position: relative; display: flex; flex-direction: column; gap: 6px; height: 100%; padding: 20px 20px 18px; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; color: var(--ink); text-decoration: none; transition: border-color .2s, background .2s, transform .2s, box-shadow .2s; }
.card .thumb { display: block; margin: -20px -20px 14px; aspect-ratio: 16 / 9; overflow: hidden; border-bottom: 1px solid var(--line); background: var(--bg); }
.card .thumb img { display: block; width: 100%; height: 100%; object-fit: cover; object-position: center 30%; filter: saturate(.8) brightness(.92); transition: transform .4s ease, filter .3s; }
.card:hover .thumb img { transform: scale(1.04); filter: saturate(1.05) brightness(1); }
.card::after { content: "\2192"; position: absolute; right: 16px; bottom: 16px; color: var(--amber); opacity: 0; transition: opacity .2s, transform .2s; transform: translateX(-4px); }
.card:hover { border-color: var(--amber); background: var(--surface2); transform: translateY(-3px); box-shadow: 0 20px 40px -28px rgba(242,106,27,.5); }
.card:hover::after { opacity: 1; transform: none; }
.card .kind { font-family: var(--mono); font-size: 12px; letter-spacing: .04em; text-transform: uppercase; color: var(--amber); }
.card b { font-family: var(--display); font-weight: 700; font-size: 1.2rem; letter-spacing: -0.01em; }
.card em { font-style: normal; color: var(--muted); font-size: 15px; line-height: 1.5; }
.card .num { margin-top: auto; padding-top: 14px; font-family: var(--mono); font-size: 1.35rem; color: var(--amber); }
.card .num small { display: block; font-family: var(--body); font-size: 13px; color: var(--muted); }
.card.wide { grid-column: span 1; }
@media (max-width: 900px) { .cards { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 560px) { .cards { grid-template-columns: 1fr; } }
.cta { display: inline-block; margin-top: 26px; font-family: var(--display); font-weight: 700; font-size: 1.05rem; text-decoration: none; background: var(--amber); color: var(--amber-ink); padding: 12px 22px; border-radius: 8px; }
.cta:hover { background: var(--amber-deep); }

/* timeline: a real sequence, so it gets a spine */
.tl { list-style: none; margin: 10px 0 0; padding: 0; border-left: 2px solid var(--line2); }
.tl li { position: relative; padding: 0 0 22px 26px; }
.tl li::before { content: ""; position: absolute; left: -7px; top: 9px; width: 12px; height: 12px; border-radius: 50%; background: var(--bg); border: 2px solid var(--amber); transition: background .2s; }
.tl li:hover::before { background: var(--amber); }
.tl li:last-child { padding-bottom: 4px; }
.tl .when { font-family: var(--mono); font-size: 13px; color: var(--muted); }
.tl b { display: block; font-family: var(--display); font-size: 1.12rem; margin: 2px 0 2px; }
.tl p { margin: 0; color: var(--muted); max-width: 60ch; }
.tl a { color: var(--ink); }

/* banners and strips */
.banner { margin: 28px 0 0; border-radius: 14px; overflow: hidden; border: 1px solid var(--line2); aspect-ratio: 21 / 9; position: relative; background: var(--bg2); }
.banner img { width: 100%; height: 100%; object-fit: cover; display: block; }
.banner figcaption { position: absolute; left: 0; right: 0; bottom: 0; padding: 28px 18px 12px; font-size: 13px; color: var(--ink); background: linear-gradient(transparent, rgba(0,0,0,.75)); font-family: var(--mono); }
@media (max-width: 640px) { .banner { aspect-ratio: 16 / 10; } }
.mosaic { list-style: none; margin: 18px 0 0; padding: 0; display: grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: 180px; gap: 10px; }
.mosaic li { position: relative; overflow: hidden; border-radius: 10px; border: 1px solid var(--line); background: var(--bg2); }
.mosaic li.big { grid-column: span 2; grid-row: span 2; }
.mosaic li.tall { grid-row: span 2; }
.mosaic li.wide { grid-column: span 2; }
.mosaic a, .mosaic img { display: block; width: 100%; height: 100%; }
.mosaic img { object-fit: cover; transition: transform .5s ease; }
.mosaic li:hover img { transform: scale(1.05); }
.mosaic span { position: absolute; left: 0; right: 0; bottom: 0; padding: 26px 12px 10px; font-size: 12.5px; color: var(--ink); background: linear-gradient(transparent, rgba(0,0,0,.8)); opacity: 0; transition: opacity .25s; }
.mosaic li:hover span { opacity: 1; }
@media (max-width: 760px) { .mosaic { grid-template-columns: repeat(2, 1fr); grid-auto-rows: 150px; } }
.logo-row { display: flex; align-items: center; gap: 18px; margin: 10px 0 18px; }
.logo-row img { width: 96px; height: 96px; border-radius: 12px; border: 1px solid var(--line2); background: #fff; }

/* case file pages */
.crumb { font-family: var(--mono); font-size: 13px; margin: 0 0 22px; }
.crumb a { text-decoration: none; color: var(--muted); }
.crumb a:hover { color: var(--amber); }
.meta { font-family: var(--mono); font-size: 13.5px; color: var(--muted); margin: 16px 0 0; }
.lede { font-size: 1.2rem; line-height: 1.55; max-width: 36em; margin: 22px 0 0; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; margin: 18px 0 10px; }
.stat { position: relative; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 16px 18px 16px 22px; overflow: hidden; transition: border-color .2s, transform .2s; }
.stat::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--amber); }
.stat:hover { border-color: var(--line2); transform: translateY(-2px); }
.stat .n { font-family: var(--mono); font-size: 1.7rem; font-weight: 500; letter-spacing: -0.02em; color: var(--amber); line-height: 1.2; }
.stat p { margin: 6px 0 0; font-size: 15px; color: var(--muted); line-height: 1.5; max-width: none; }
.note { font-size: 15px; color: var(--muted); }
.pills { display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 0; padding: 0; list-style: none; }
.pills li { background: var(--surface); border: 1px solid var(--line2); border-radius: 99px; padding: 4px 14px; font-size: 15px; }
.bul { margin: 0; padding-left: 1.2em; max-width: 62ch; }
.bul li { margin: 0 0 8px; }
.next { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; font-weight: 600; }
.links { font-family: var(--mono); font-size: 14px; }

/* figures */
.figs { list-style: none; margin: 18px 0 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.figs li { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; overflow: hidden; display: flex; flex-direction: column; }
.figs li.full { grid-column: 1 / -1; background: var(--bg); }
.figs li.full figcaption { background: var(--surface); }
.tablewrap { overflow-x: auto; margin: 18px 0; border: 1px solid var(--line); border-radius: 10px; }
table.cmp { border-collapse: collapse; width: 100%; min-width: 860px; font-size: 14px; }
table.cmp th, table.cmp td { padding: 10px 12px; text-align: right; border-bottom: 1px solid var(--line); white-space: nowrap; }
table.cmp th:first-child, table.cmp td:first-child { text-align: left; }
table.cmp th { background: var(--surface); color: var(--muted); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; white-space: normal; }
table.cmp tbody tr:last-child td { border-bottom: 0; }
table.cmp tbody tr { transition: background .15s; }
table.cmp tbody tr:hover { background: var(--surface); }
table.cmp td a { color: var(--accent); font-weight: 600; }
.figs li.dark a.img { background: var(--bg); }
.figs li.light a.img { background: #fff; }
.figs li.full a.img { max-width: 900px; margin: 0 auto; width: 100%; }
.figs a.img { display: block; background: var(--bg); padding: 8px; overflow: hidden; }
.figs img { transition: transform .35s ease; }
.figs li:hover img { transform: scale(1.015); }
.figs li { transition: border-color .2s; }
.figs li:hover { border-color: var(--line2); }
.figs img { display: block; width: 100%; height: auto; }
.figs figcaption { padding: 14px 16px 16px; font-size: 15px; line-height: 1.5; color: var(--muted); }
.figs figcaption b { display: block; color: var(--ink); font-weight: 600; margin-bottom: 3px; }
.figs figure { margin: 0; display: flex; flex-direction: column; height: 100%; }
@media (max-width: 760px) { .figs { grid-template-columns: 1fr; } }
.shot { display: block; margin: 18px 0 0; border: 1px solid var(--line2); border-radius: 10px; overflow: hidden; box-shadow: 0 30px 60px -40px rgba(0,0,0,.9); }
.shot img { display: block; width: 100%; height: auto; }
.strip { list-style: none; margin: 18px 0 0; padding: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.strip li a { display: block; background: #fff; border-radius: 8px; padding: 8px; border: 1px solid var(--line); }
.strip img { display: block; width: 100%; height: auto; }
.strip span { display: block; margin-top: 8px; font-size: 14px; color: var(--muted); }
@media (max-width: 700px) { .strip { grid-template-columns: 1fr; } }

/* photos */
.photos { list-style: none; margin: 18px 0 0; padding: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.photos li { margin: 0; align-self: start; }
.photos figure { margin: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; overflow: hidden; display: flex; flex-direction: column; }
.photos a { display: block; aspect-ratio: 4 / 3; overflow: hidden; background: #0e0e10; }
.photos li.tall a { aspect-ratio: 3 / 4; }
.photos li.wide { grid-column: span 2; }
.photos li.wide a { aspect-ratio: 2 / 1; }
.photos li.sq a { aspect-ratio: 1 / 1; }
.photos.duo { grid-template-columns: repeat(2, 1fr); }
.photos.duo li a { aspect-ratio: 1 / 1; }
@media (max-width: 480px) { .photos.duo { grid-template-columns: 1fr; } }
.photos img { display: block; width: 100%; height: 100%; object-fit: cover; }
.photos figcaption { padding: 10px 14px 12px; font-size: 14px; line-height: 1.45; color: var(--muted); }
@media (max-width: 760px) { .photos { grid-template-columns: repeat(2, 1fr); } .photos li.wide { grid-column: span 2; } }
@media (max-width: 480px) { .photos { grid-template-columns: 1fr; } .photos li.wide { grid-column: span 1; } }
.logo { display: block; width: min(100%, 360px); margin: 6px 0 18px; border-radius: 8px; }

/* reveal on scroll */
.rv { opacity: 0; transform: translateY(14px); transition: opacity .6s ease, transform .6s ease; }
.rv.in { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) { .rv { opacity: 1; transform: none; transition: none; } .card, .stat, .figs img { transition: none; } }

""" + WIDGET_CSS + CINE_CSS + r"""
/* portrait hero */
.cine.portrait .cine-bg { background: radial-gradient(720px 520px at 78% 40%, rgba(242,106,27,.14), transparent 65%), radial-gradient(900px 600px at 10% 90%, rgba(255,255,255,.03), transparent 60%); }
.cine.portrait .cine-bg::after { display: none; }
.cine-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 400px); gap: 48px; align-items: center; }
.cine-grid > .cine-text > * { max-width: 620px; }
.portrait-box { margin: 0; justify-self: end; width: 100%; opacity: 0; animation: fadeup 1.1s .35s cubic-bezier(.2,.75,.15,1) forwards; }
.portrait-box img { display: block; width: 100%; height: auto; aspect-ratio: 1; object-fit: cover; border-radius: 18px; border: 1px solid var(--line2); box-shadow: 0 0 0 1px rgba(242,106,27,.35), 0 30px 80px rgba(0,0,0,.65), 0 0 120px rgba(242,106,27,.12); background: #fff; }
.portrait-box figcaption { margin: 12px 2px 0; font-family: var(--mono); font-size: 12px; color: var(--muted); text-align: right; }
@media (max-width: 760px) {
  .cine.portrait { align-items: center; }
  .cine.portrait .cine-in { padding-top: 88px; padding-bottom: 80px; }
  .cine-grid { grid-template-columns: 1fr; gap: 28px; }
  .portrait-box { order: -1; justify-self: start; width: min(62vw, 260px); }
  .portrait-box figcaption { text-align: left; }
}

/* one grade for every photo so phone shots sit with the dark charts */
.card .thumb.photo img, .mosaic img, .photos img, .banner img[src*="/photos/"] { filter: saturate(.72) brightness(.82) contrast(1.06); }
.card .thumb.photo::after, .mosaic li::after { content: ""; position: absolute; inset: 0; pointer-events: none; background: linear-gradient(180deg, rgba(11,11,12,.08), rgba(11,11,12,.0) 40%, rgba(11,11,12,.55) 100%); }
.card .thumb { position: relative; }
.card:hover .thumb.photo img { filter: saturate(.9) brightness(.95) contrast(1.04); }
.mosaic li:hover img { filter: saturate(.9) brightness(.95) contrast(1.04); }

.sband { margin: 40px 0 0; padding: 64px 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); background: linear-gradient(180deg, var(--bg), #0e0e10 50%, var(--bg)); }
.sband .wrap { display: grid; grid-template-columns: 1.05fr .95fr; gap: 52px; align-items: center; }
.sband .big { max-width: 16ch; text-shadow: none; }
.sband figure { margin: 0; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: var(--surface); }
.sband figure img { display: block; width: 100%; aspect-ratio: 5 / 4; object-fit: cover; }
.sband figcaption { padding: 10px 14px 12px; font-family: var(--mono); font-size: 12px; color: var(--muted); line-height: 1.45; }
@media (max-width: 800px) { .sband { padding: 40px 0; } .sband .wrap { grid-template-columns: 1fr; gap: 26px; } }
/* footer */
.site-foot { border-top: 1px solid var(--line); margin-top: 40px; padding: 26px 0 48px; color: var(--muted); font-size: 14px; }
.site-foot .row { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px 24px; }
.site-foot a { color: var(--muted); }
.site-foot a:hover { color: var(--amber); }
.site-foot p { margin: 12px 0 0; max-width: 70ch; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } .board li { animation: none; } .card { transition: none; } }
@media (max-width: 560px) { body { font-size: 16px; } }
/* ---------- warm look: light ground, navy ink, soft rounded tiles ---------- */
body { font-weight: 400; font-variant-numeric: tabular-nums; }
body::before, .grain, .glow { display: none !important; }
h1, h2, h3, .big, .kick { letter-spacing: -0.015em; font-weight: 800; }
a { text-decoration-color: rgba(194,65,12,.35); }
.site-head { background: rgba(255,251,245,.92); border-bottom: 1px solid var(--line); }
html.scrolled body.home .site-head, html.scrolled body.hashead .site-head { background: rgba(255,251,245,.94); border-bottom-color: var(--line); }
body.home .site-head, body.hashead .site-head { background: rgba(255,251,245,.0); border-bottom-color: transparent; }
body.home .nav.open, body.hashead .nav.open, .nav.open { background: #fff; }
.nav a { border-radius: 999px; padding: 8px 14px; font-weight: 700; font-size: 15.5px; color: var(--ink); }
.nav a:hover { background: var(--t-peach); color: var(--ink); }
.nav a[aria-current="page"], .nav a.on { background: var(--t-peach); color: var(--ink); }
.menu-btn { border-radius: 999px; padding: 8px 16px; font-weight: 700; }
.btn { border-radius: 999px; font-weight: 800; padding: 13px 24px; font-size: 16px; }
.btn.primary, .cta { background: var(--amber); color: #fff; border-color: var(--amber); }
.btn.primary:hover, .cta:hover { background: var(--amber-deep); border-color: var(--amber-deep); color: #fff; }
.btn.outline { background: #fff; color: var(--ink); border: 2px solid var(--line2); }
.btn.outline:hover { background: var(--t-peach); border-color: #E9C9A8; color: var(--ink); }
.cta { border-radius: 999px; }
.badge { font-family: var(--body); font-weight: 700; font-size: 14px; color: var(--amber-deep); background: var(--t-peach); border: 0; padding: 6px 14px; }
.eyebrow, .label { font-family: var(--body); font-weight: 800; color: var(--amber); letter-spacing: .02em; }
.label::before { color: var(--muted); }

/* home hero */
.cine.portrait .cine-bg { background: radial-gradient(760px 520px at 82% 30%, rgba(255,232,214,.9), transparent 70%), radial-gradient(700px 480px at 6% 100%, rgba(227,239,228,.8), transparent 70%); }
.cine h1 { text-shadow: none; color: var(--ink); }
.cine .tag { color: #3B4560; }
.cine-grid > .cine-text > * { max-width: 620px; }
.portrait-box img { border-radius: 32px; border: 0; box-shadow: 0 24px 60px -28px rgba(31,42,68,.35); }
.portrait-box figcaption { font-family: var(--body); font-size: 14px; color: var(--muted); }
.byline .pic { border-color: var(--amber); box-shadow: none; }
.cue, .cine-cap { font-family: var(--body); color: var(--muted); }

/* strips and boards */
.marq { background: var(--t-sun); border-color: var(--line); color: var(--ink); font-family: var(--body); font-weight: 700; font-size: 15px; }
.marq-in b { color: var(--amber-deep); font-weight: 800; }
.tape, .board { background: #fff; border: 1px solid var(--line); border-radius: 28px; box-shadow: 0 20px 50px -34px rgba(31,42,68,.25); }
.tape-head, .board-head { color: var(--muted); }

/* sections and cards */
.hero { background: #fff; border-radius: 32px; box-shadow: 0 20px 50px -30px rgba(31,42,68,.25); border-color: var(--line); }
.card { background: #fff; border: 1px solid var(--line); border-radius: 24px; padding: 22px 22px 20px; transition: transform .2s, box-shadow .2s, border-color .2s; }
.card:hover { border-color: #E9C9A8; background: #fff; transform: translateY(-3px); box-shadow: 0 18px 40px -26px rgba(194,65,12,.35); }
.card::before { display: none; }
.card .thumb { border-radius: 18px; overflow: hidden; border: 0; }
.card .thumb::after { display: none; }
.card .kind { display: inline-block; align-self: flex-start; border-radius: 999px; padding: 3px 12px; background: var(--t-peach); color: var(--amber-deep); font-family: var(--body); font-weight: 800; font-size: 13px; letter-spacing: 0; text-transform: none; }
.cards > li:nth-child(4n+2) .card .kind { background: var(--t-sage); color: #2F5D3A; }
.cards > li:nth-child(4n+3) .card .kind { background: var(--t-sun); color: #7A5A00; }
.cards > li:nth-child(4n+4) .card .kind { background: var(--t-sky); color: #1E3A5F; }
.card .num { color: var(--amber); }
.stat, .figs li, .photos figure, .tablewrap, .shot, .mosaic li, .banner { border-radius: 24px; border-color: var(--line); box-shadow: none; }
.stats .stat:nth-child(4n+1), .stat:nth-child(4n+1) { background: var(--t-peach); border-color: transparent; }
.stat:nth-child(4n+2) { background: var(--t-sage); border-color: transparent; }
.stat:nth-child(4n+3) { background: var(--t-sun); border-color: transparent; }
.stat:nth-child(4n+4) { background: var(--t-sky); border-color: transparent; }
.stat::before { display: none; }
.pills li { border-radius: 999px; background: #fff; border-color: var(--line); font-weight: 700; padding: 6px 16px; }
.photos a { background: var(--bg2); }
.banner figcaption, .mosaic span { background: linear-gradient(transparent, rgba(31,42,68,.78)); color: #fff; font-family: var(--body); }
.card .thumb.photo img, .mosaic img, .photos img, .banner img[src*="/photos/"] { filter: none; }
.card .thumb.photo::after, .mosaic li::after { display: none; }
.tl li::before { background: #fff; }
.next a { border-radius: 999px; }
table.cmp th { background: var(--bg2); }

/* case page heads: tinted, calm, one figure under the title */
.chead { min-height: 0; display: block; margin-top: 0; padding-top: 0; overflow: visible; border-bottom: 0; background: var(--tint, var(--t-peach)); border-radius: 0 0 44px 44px; }
.chead-in { padding-top: 56px; padding-bottom: 40px; }
.chead h1, .phead h1 { text-shadow: none; max-width: 22ch; letter-spacing: -0.015em; color: var(--ink); }
.chead .meta, .phead .meta { color: #3B4560; }
.chead .crumb a, .phead .crumb a { font-weight: 700; }
.chead-fig { margin: 0 auto; padding-bottom: 44px; }
.chead-fig img { display: block; width: 100%; max-height: 420px; object-fit: cover; border-radius: 32px; background: #fff; box-shadow: 0 24px 60px -34px rgba(31,42,68,.35); }
.chead-fig figcaption { margin: 10px 6px 0; font-size: 14px; color: #3B4560; }
.chead-cap { display: none; }
.phead { background: var(--tint, var(--t-peach)); border-radius: 0 0 44px 44px; }
.phead::before { display: none; }
.phead .lede { color: #2F3A55; }
.lede-wrap { padding-top: 34px; }
.lede { color: #2F3A55; }

/* home statement band */
.sband { margin: 48px 0 0; padding: 0; border: 0; background: none; }
.sband .wrap { display: block; }
.sband .panel { display: grid; grid-template-columns: 1fr; gap: 28px; align-items: center; background: var(--panel, var(--t-sun)); border-radius: 40px; padding: 56px 52px; }
.sband .panel.has-fig { grid-template-columns: 1.05fr .95fr; }
.sband .big { max-width: 18ch; text-shadow: none; color: var(--ink); }
.sband .sub { margin: 14px 0 0; font-size: 19px; font-weight: 700; color: #3B4560; max-width: 36ch; }
.sband figure { border: 0; border-radius: 28px; background: #fff; }
.sband figure img { aspect-ratio: 5 / 4; }
.sband figcaption { font-family: var(--body); font-size: 14px; color: #3B4560; background: transparent; padding: 10px 6px 0; }
@media (max-width: 800px) { .sband .panel, .sband .panel.has-fig { grid-template-columns: 1fr; padding: 34px 26px; border-radius: 32px; } }
.sband.navy .panel { background: var(--ink); }
.sband.navy .big { color: #fff; }
.sband.navy .sub { color: #D8DEEC; }


.card.nt { border-color: transparent; }
.card.nt.k-role { background: var(--t-sky); }
.card.nt.k-leadership { background: var(--t-sun); }
.card.nt.k-education { background: var(--t-sage); }
.card.nt.k-project, .card.nt.k-competition { background: var(--t-peach); }
.card.nt:hover { background: #fff; border-color: #E9C9A8; }
.card.nt .kind { background: rgba(255,255,255,.7); }
.chips { list-style: none; margin: 22px 0 0; padding: 0; display: flex; flex-wrap: wrap; gap: 12px; }
.chips li { background: rgba(255,255,255,.12); border-radius: 22px; padding: 12px 18px; min-width: 120px; }
.chips b { display: block; font-size: 30px; font-weight: 800; line-height: 1.1; color: #fff; }
.chips span { font-size: 14.5px; font-weight: 700; color: #D8DEEC; }
/* footer */
.site-foot { border-top: 1px solid var(--line); }
.site-foot a:hover { color: var(--amber-deep); }
@media (max-width: 760px) { .chead, .phead { border-radius: 0 0 32px 32px; } .chead-in { padding-top: 36px; } .chead-fig img { max-height: 260px; border-radius: 24px; } }

/* ---------- dark mode: same layout, night colors. Switch is in the header. ---------- */
.theme-btn { display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; flex: none; border-radius: 999px; border: 2px solid var(--line2); background: var(--surface); color: var(--ink); cursor: pointer; padding: 0; }
.theme-btn:hover { background: var(--t-peach); }
.theme-btn svg { width: 20px; height: 20px; display: block; }
.theme-btn .i-moon { display: block; } .theme-btn .i-sun { display: none; }
html[data-theme="dark"] .theme-btn .i-moon { display: none; } html[data-theme="dark"] .theme-btn .i-sun { display: block; }
html[data-theme="dark"] {
  color-scheme: dark;
  --bg: #12151C; --bg2: #1A1F2C; --surface: #1B2030; --surface2: #222842; --line: #2B3348; --line2: #3A4562;
  --ink: #EEF1F8; --muted: #A9B2C8; --amber: #FB923C; --amber-deep: #FDBA74; --accent: #FB923C;
  --t-peach: #3B2B22; --t-sage: #22362B; --t-sun: #3A321B; --t-sky: #1F3047;
}
html[data-theme="dark"] a { text-decoration-color: rgba(251,146,60,.45); }
html[data-theme="dark"] .site-head { background: rgba(18,21,28,.92); }
html[data-theme="dark"].scrolled body.home .site-head, html[data-theme="dark"].scrolled body.hashead .site-head { background: rgba(18,21,28,.94); }
html[data-theme="dark"] body.home .site-head, html[data-theme="dark"] body.hashead .site-head { background: rgba(18,21,28,0); }
html[data-theme="dark"] body.home .nav.open, html[data-theme="dark"] body.hashead .nav.open, html[data-theme="dark"] .nav.open { background: var(--surface); }
html[data-theme="dark"] .btn.primary, html[data-theme="dark"] .cta { background: var(--amber); border-color: var(--amber); color: #1A1205; }
html[data-theme="dark"] .btn.primary:hover, html[data-theme="dark"] .cta:hover { background: var(--amber-deep); border-color: var(--amber-deep); color: #1A1205; }
html[data-theme="dark"] .btn.outline { background: var(--surface); color: var(--ink); }
html[data-theme="dark"] .btn.outline:hover { background: var(--t-peach); border-color: var(--line2); }
html[data-theme="dark"] .cine.portrait .cine-bg { background: radial-gradient(760px 520px at 82% 30%, rgba(251,146,60,.16), transparent 70%), radial-gradient(700px 480px at 6% 100%, rgba(90,150,110,.14), transparent 70%); }
html[data-theme="dark"] .cine .tag, html[data-theme="dark"] .chead .meta, html[data-theme="dark"] .phead .meta,
html[data-theme="dark"] .chead-fig figcaption, html[data-theme="dark"] .sband .sub, html[data-theme="dark"] .sband figcaption { color: #C3CADC; }
html[data-theme="dark"] .phead .lede, html[data-theme="dark"] .lede { color: #D3D9E8; }
html[data-theme="dark"] .portrait-box img, html[data-theme="dark"] .chead-fig img, html[data-theme="dark"] .hero, html[data-theme="dark"] .tape, html[data-theme="dark"] .board { box-shadow: 0 24px 60px -30px rgba(0,0,0,.7); }
html[data-theme="dark"] .tape, html[data-theme="dark"] .board, html[data-theme="dark"] .hero, html[data-theme="dark"] .card, html[data-theme="dark"] .pills li { background: var(--surface); border-color: var(--line); }
html[data-theme="dark"] .card:hover, html[data-theme="dark"] .card.nt:hover { background: var(--surface2); border-color: var(--line2); box-shadow: 0 18px 40px -26px rgba(251,146,60,.35); }
html[data-theme="dark"] .tl li::before { background: var(--bg); }
html[data-theme="dark"] .card .kind { color: var(--amber-deep); }
html[data-theme="dark"] .cards > li:nth-child(4n+2) .card .kind { color: #A8DDB4; }
html[data-theme="dark"] .cards > li:nth-child(4n+3) .card .kind { color: #F2D27A; }
html[data-theme="dark"] .cards > li:nth-child(4n+4) .card .kind { color: #A9CBF2; }
html[data-theme="dark"] .card.nt .kind { background: rgba(255,255,255,.08); }
html[data-theme="dark"] .badge { color: var(--amber-deep); }
html[data-theme="dark"] .chead-fig img, html[data-theme="dark"] .sband figure { background: var(--surface); }
html[data-theme="dark"] .chead, html[data-theme="dark"] .phead { background: var(--bg2); background: color-mix(in srgb, var(--tint, #FFE8D6) 12%, #161A26); }
html[data-theme="dark"] .sband .panel { background: var(--bg2); background: color-mix(in srgb, var(--panel, #FFF1C9) 13%, #161A26); }
html[data-theme="dark"] .sband.navy .panel { background: #26325A; }
html[data-theme="dark"] .sband.navy .big, html[data-theme="dark"] .chips b { color: #fff; }
html[data-theme="dark"] .sband.navy .sub, html[data-theme="dark"] .chips span { color: #D8DEEC; }
html[data-theme="dark"] .photos a { background: var(--bg2); }
html[data-theme="dark"] img { filter: brightness(.94); }
html[data-theme="dark"] .logo-row img, html[data-theme="dark"] .figs li.light a.img, html[data-theme="dark"] .strip li a, html[data-theme="dark"] .hero-img { filter: none; }
html[data-theme="dark"] .byline .pic { background: var(--surface); }
@media (prefers-reduced-motion: no-preference) { body, .card, .site-head, .tape, .board, .hero, .chead, .phead, .sband .panel { transition: background-color .25s, color .25s, border-color .25s; } }
"""

NAV = [("index.html", "Home"), ("projects.html", "Projects"), ("experience.html", "Experience"), ("leadership.html", "Leadership"), ("education.html", "Education"), ("contact.html", "Contact")]

HEAD_FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
              '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap">')
JS = """(function(){var tb=document.getElementById('theme-btn');if(tb){var root=document.documentElement;function sync(){var d=root.getAttribute('data-theme')==='dark';tb.setAttribute('aria-pressed',d?'true':'false');tb.setAttribute('aria-label',d?'Switch to light mode':'Switch to dark mode');var m=document.querySelector('meta[name=theme-color]');if(m)m.setAttribute('content',d?'#12151C':'#FFFBF5');}
sync();tb.addEventListener('click',function(){var n=root.getAttribute('data-theme')==='dark'?'light':'dark';root.setAttribute('data-theme',n);try{localStorage.setItem('af-theme',n);}catch(e){}sync();});}})();
(function(){var b=document.getElementById('menu-btn'),n=document.getElementById('nav');if(b&&n){b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o?'true':'false');});}
var els=document.querySelectorAll('.section .wrap > *, .cards li, .stat, .figs li, .tl li, .photos li, .mosaic li, .band .big, .sband .big');
if(!('IntersectionObserver' in window)||window.matchMedia('(prefers-reduced-motion: reduce)').matches){return;}
els.forEach(function(el,i){el.classList.add('rv');el.style.transitionDelay=((i%6)*60)+'ms';});
var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target);}});},{rootMargin:'0px 0px -8% 0px',threshold:0.05});
els.forEach(function(el){io.observe(el);});setTimeout(function(){els.forEach(function(el){el.classList.add('in');});},1400);})();
(function(){var t=document.getElementById('tape');if(!t)return;
fetch('https://ferrierotony-cmyk.github.io/market_dashboard/market_snapshot.json',{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(s){
function find(o,keys){if(!o)return null;var ks=Object.keys(o);for(var i=0;i<keys.length;i++){for(var j=0;j<ks.length;j++){if(ks[j].toUpperCase().indexOf(keys[i].toUpperCase())>=0)return o[ks[j]];}}return null;}
function num(x,d,suf){return (x==null||isNaN(x))?null:(Number(x).toFixed(d)+(suf||''));}
var items=[];
if(s.window){var w=String(s.window);var cls=/open/i.test(w)?'good':(/closed|shut/i.test(w)?'bad':'warn');items.push(['New issue window',w,cls,'my score']);}
if(s.health&&s.health.score!=null){items.push(['Market health',s.health.score,'',s.health.label||'']);}
var f=s.fred||{},y=s.yahoo||{};
var r10=find(f,['DGS10','10Y']);if(r10&&r10.last!=null)items.push(['UST 10Y',num(r10.last,2,'%'),'',r10.d1!=null?('1d '+(r10.d1>=0?'+':'')+num(r10.d1*100,0,' bp')):'']);
var ig=find(f,['BAMLC0A0CM','IG OAS','US IG']);if(ig&&ig.last!=null)items.push(['IG OAS',num(ig.last,0,' bp'),'',ig.w1!=null?('1w '+(ig.w1>=0?'+':'')+num(ig.w1,0,' bp')):'']);
var hy=find(f,['BAMLH0A0HYM2','HY OAS','US HY']);if(hy&&hy.last!=null)items.push(['HY OAS',num(hy.last,0,' bp'),'',hy.w1!=null?('1w '+(hy.w1>=0?'+':'')+num(hy.w1,0,' bp')):'']);
var vix=find(y,['^VIX','VIX']);if(vix&&vix.last!=null)items.push(['VIX',num(vix.last,1),'',vix.d1_pct!=null?('1d '+(vix.d1_pct>=0?'+':'')+num(vix.d1_pct,1,'%')):'']);
var mv=find(y,['MOVE']);if(mv&&mv.last!=null)items.push(['MOVE',num(mv.last,0),'',mv.d1_pct!=null?('1d '+(mv.d1_pct>=0?'+':'')+num(mv.d1_pct,1,'%')):'']);
if(items.length<3)return;
document.getElementById('tape-ul').innerHTML=items.map(function(i){return '<li>'+i[0]+'<b class="'+i[2]+'">'+i[1]+'</b><small>'+i[3]+'</small></li>';}).join('');
document.getElementById('tape-when').textContent=s.built_at?('built '+String(s.built_at).slice(0,16)):'';t.classList.add('on');}).catch(function(){});})();
""" + GLOBAL_JS + CINE_JS


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
<meta name="theme-color" content="#FFFBF5">
<script>(function(){{var t=null;try{{t=localStorage.getItem('af-theme');}}catch(e){{}}if(t!=='dark'&&t!=='light'){{t=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}}document.documentElement.setAttribute('data-theme',t);var m=document.querySelector('meta[name=theme-color]');if(m)m.setAttribute('content',t==='dark'?'#12151C':'#FFFBF5');}})();</script>
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
<link rel="stylesheet" href="style.css">
<script>document.documentElement.classList.add('js')</script>
</head>
<body class="{'home' if fname == 'index.html' else ('inner hashead' if 'class="chead"' in main else 'inner')}">
<a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap bar">
  <a class="brand" href="index.html">AF<i>.</i></a>
  <button class="menu-btn" id="menu-btn" aria-expanded="false" aria-controls="nav">Menu</button>
  <ul class="nav" id="nav">{nav}</ul>
  <button class="theme-btn" id="theme-btn" type="button" aria-label="Switch to dark mode" aria-pressed="false" title="Light or dark">
    <svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    <svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
  </button>
</div></header>
<main id="main">
{main}
</main>
<footer class="site-foot"><div class="wrap">
  <div class="row"><span>&copy; 2026 Anthony Ferriero &middot; Lowell, MA</span><span><a href="contact.html">Contact</a> &nbsp;&middot;&nbsp; <a href="{LINKEDIN}" rel="noopener">LinkedIn</a> &nbsp;&middot;&nbsp; <a href="{GITHUB}" rel="noopener">GitHub</a></span></div>
  <p>Personal portfolio. The research figures are preliminary. Nothing here is investment advice, and nothing here comes from an employer.</p>
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


def split_band(photo, big, cap, pos="center 75%", sub="", tint="#FFF1C9", navy=False, chips=()):
    """A rounded statement panel. Shows an AI generated image beside the line only if one exists in assets/ai."""
    fig = ""
    if photo and os.path.exists(os.path.join(OUT, photo)):
        fig = ('<figure><img src="%s" alt="" style="object-position:%s" loading="lazy"><figcaption>AI generated image, not a photo of the real place.</figcaption></figure>' % (photo, pos))
    subh = '<p class="sub">%s</p>' % e(sub) if sub else ""
    if chips:
        subh += '<ul class="chips">' + "".join("<li><b>%s</b><span>%s</span></li>" % (e(a), e(b)) for a, b in chips) + "</ul>"
    return ('<section class="sband%s" aria-label="%s"><div class="wrap"><div class="panel%s" style="--panel:%s"><div><p class="big rv">%s</p>%s</div>%s</div></div></section>'
            % (" navy" if navy else "", e(cap), " has-fig" if fig else "", tint, e(big), subh, fig))


def pills(items):
    return '<ul class="pills">' + "".join("<li>%s</li>" % e(i) for i in items) + "</ul>"


def bul(items):
    return '<ul class="bul">' + "".join("<li>%s</li>" % i for i in items) + "</ul>"


CASES = [
    ("research.html", "Project", "Green bond pricing", "Do green bonds price tighter at new issue than the same issuer's conventional bonds? 153 matched pairs.", ("2.4 bps", "average new issue gap, not significant")),
    ("tender.html", "Project", "Tender Tracker", "A daily tracker of bond tender and exchange offers, read from SEC filings and newswires, with the terms and caps.", ("9 in 10", "offer types and dates right on unseen filings")),
    ("dashboard.html", "Project", "Morning Market Dashboard", "Is the new issue window open? One score built from the inputs a syndicate desk checks before launch.", ("6 inputs", "VIX, MOVE, IG and HY spreads, futures, spread range")),
    ("media.html", "Project", "Media DCF models and credit comps", "DCF models for Skydance, Netflix, Disney, Comcast and Fox on one template, then compared as credits on leverage, coverage, equity cushion and spread.", ("6.9x", "Skydance net leverage, against a 3.0x target it cannot reach on cash flow")),
    ("finsight.html", "Role", "Finsight", "Order books, price talk to print, volume against estimates and liability management on 15 to 20 new deals a day. December 2025 to September 2026.", ("25+", "liability management deals I wrote headlines for")),
    ("bloomberg.html", "Role", "Bloomberg at UMass Lowell", "Terminal Assistant across 10 classes, and captain of the UML team in the Bloomberg Global Trading Challenge.", ("$1M", "virtual book, long only, scored against the WLS index")),
    ("valuation.html", "Competition", "2026 Valuation Challenge", "Discount rate, DCF and LBO for a $132MM revenue contractor being sold to an ESOP. I owned the cost of capital.", ("16.8%", "cost of capital I built and defended")),
    ("finance-society.html", "Leadership", "UML Finance Society", "President of a 500 member student club.", None),
    ("sales-team.html", "Leadership", "Intercollegiate Sales Team", "Captain, top four at a national competition.", None),
    ("ccr.html", "Role", "Commonwealth Capital Research", "Rates and credit newsletter for 200 subscribers, since February 2024.", None),
    ("consulting.html", "Project", "Mill City Consulting", "Research and due diligence for a 1931 duckpin bowling alley.", None),
    ("education.html", "Education", "UMass Lowell", "Business Administration, finance and marketing, May 2027.", None),
    ("skills.html", "Skills", "Tools and certifications", "Bloomberg, R, Stata, Excel and the AI tools I use.", None),
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
    secs = "".join(f'<section class="section"{" id=\"figures\"" if label == "Figures" else ""}><div class="wrap"><p class="label">{e(label)}</p><h2>{e(h2)}</h2>{body}</div></section>\n' for label, h2, body in sections)
    nf, nl = nxt(fname)
    crumb = '<p class="crumb"><a href="index.html#case-files">&larr; All case files</a></p>'
    if banner:
        src = banner[0] if "/" in banner[0] else "assets/photos/%s.jpg" % banner[0]
        pos = banner[2] if len(banner) > 2 else (PHOTO_POS.get(src.split("/")[-1].replace(".jpg", ""), "center 30%") if "/photos/" in src else "center center")
        if src.endswith("mill-city.jpg"): pos += ";position:relative;top:-22px"
        head = cine_head(crumb, kind, h1, meta, src, banner[1], pos) + f'<div class="wrap lede-wrap"><p class="lede">{e(lede)}</p></div>'
    else:
        head = f"""<div class="phead" style="--tint:{_cine.tint_for(kind)};padding-top:56px;padding-bottom:40px"><div class="wrap" style="padding-top:0;padding-bottom:0">
  {crumb}
  <p class="eyebrow">{e(kind)}</p>
  <h1>{split(h1)}</h1>
  <p class="meta">{e(meta)}</p>
  <p class="lede">{e(lede)}</p>
</div></div>"""
    main = f"""{head}
{secs}<section class="section"><div class="wrap next"><a href="index.html#case-files">&larr; All case files</a><a href="{nf}">Next: {e(nl)} &rarr;</a></div></section>"""
    open(os.path.join(OUT, fname), "w", encoding="utf-8").write(shell(fname, title, desc, main))


# ---------- index ----------
board_rows = [
    ("15 to 20", "New bond deals a day I collected order books on", "from 30+ IG and HY syndicate desks at Finsight"),
    ("25+", "Liability management deals I wrote headlines for", "tenders, exchanges and consents"),
    ("2.4 bps", "New issue discount I measured on green bonds", "153 matched pairs, p 0.30, so not significant"),
    ("9 in 10", "Tender Tracker offer types and dates right", "on filings the rules had never seen"),
    ("663", "Green bonds in my dataset", "cleaned from 1,226 tracker rows, 40 countries"),
    ("6.9x", "Skydance net leverage in my DCF", "the thinnest equity cushion of the five companies I modeled"),
]
board = '<div class="board"><div class="board-head"><span>Anthony Ferriero &middot; key numbers</span><b>updated Oct 2026</b></div><ul>' + \
    "".join('<li><div><span>%s</span><small>%s</small></div><b>%s</b></li>' % (e(l), e(s), e(n)) for n, l, s in board_rows) + "</ul></div>"

THUMBS = {
    "research.html": "assets/thumbs/research.jpg", "tender.html": "assets/thumbs/tender.jpg", "dashboard.html": "assets/thumbs/dashboard.jpg",
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
    return ' style="object-position:%s"' % PHOTO_POS[k] if k in PHOTO_POS else ""

def card_html(f, kind, t, d, num):
    numh = '<span class="num">%s<small>%s</small></span>' % (e(num[0]), e(num[1])) if num else ""
    th = '<span class="thumb%s"><img src="%s" alt="" loading="lazy"%s></span>' % (" photo" if "/photos/" in THUMBS[f] else "", THUMBS[f], ppos(THUMBS[f])) if f in THUMBS else ""
    cls = "card" + ("" if th else " nt k-" + kind.split()[0].lower())
    return '<li><a class="%s" href="%s">%s<b>%s</b><em>%s</em>%s</a></li>' % (cls, f, th, e(t), e(d), numh)


def card_group(kinds):
    return '<ul class="cards">' + "".join(card_html(*c) for c in CASES if c[1] in kinds) + "</ul>"


cards = ""
for label, kinds in [("Roles", ("Role",)), ("Projects", ("Project",)), ("Competitions", ("Competition",)), ("Leadership", ("Leadership",)), ("Education and skills", ("Education", "Skills"))]:
    cards += '<h3 class="group">%s</h3>' % label + card_group(kinds)

timeline = [
    ("Oct 2026", "Media DCF models and credit comps", "Skydance, Netflix, Disney, Comcast and Fox on one DCF template from SEC filings, then a credit comparison: leverage, coverage, equity cushion, spreads and Skydance's path to its 3.0 times target.", "media.html"),
    ("Oct 2026 to now", "Tender Tracker", "Daily bond tender and exchange offer tracker from SEC filings and newswires, with published error rates.", "tender.html"),
    ("Oct 2026 to now", "Captain, Bloomberg Global Trading Challenge", "UML team, fall 2026 round. A million virtual dollars, long only, scored against the WLS index. Book opened October 12.", "bloomberg.html"),
    ("Sep 2026 to now", "Bloomberg Terminal Assistant, UMass Lowell", "Training students across 10 classes and pulling data for faculty research.", "bloomberg.html"),
    ("Sep to Oct 2026", "2026 Valuation Challenge", "Discount rate, DCF, LBO and public comparables for a $132MM revenue Gulf Coast contractor. Submitted October 19.", "valuation.html"),
    ("Jun 2026 to now", "Morning Market Dashboard", "An R dashboard that scores the new issue window. The public build runs on free data.", "dashboard.html"),
    ("May 2026 to now", "Fixed Income Research Analyst, UMass Lowell", "Green bond pricing research with a faculty supervisor. Preliminary results are published here.", "research.html"),
    ("Apr 2026 to now", "President, UML Finance Society", "Membership up 200+ to over 500. Six or more events and trips this year.", "finance-society.html"),
    ("Feb to Apr 2026", "Bloomberg Global Trading Challenge, spring round", "Analyst on the UML team. Research, sizing and execution in the terminal.", "bloomberg.html"),
    ("Dec 2025 to Sep 2026", "Debt Capital Markets Analyst Intern, Finsight", "New issuance, pricing and spreads, and 25+ liability management deals. High yield in the spring, investment grade in the summer.", "finsight.html"),
    ("Nov 2025 to now", "Captain, UML Intercollegiate Sales Team", "Top four at the Love's Travel Stops national sales competition.", "sales-team.html"),
    ("Feb 2024 to now", "Research Analyst, Commonwealth Capital Research", "Rates and credit newsletter for 200 subscribers, plus a SpaceX IPO report.", "ccr.html"),
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
MARQ = marquee([("15 to 20", "new bond deals a day, order books from 30+ desks"), ("25+", "liability management deals, headline to terms"), ("153", "matched green bond pairs, 2.4 bps tighter"),
                ("9 in 10", "tender offers read right on unseen filings"), ("6.9x", "Skydance net leverage, five DCFs on one template"), ("$1M", "virtual book, Bloomberg Global Trading Challenge"), ("500+", "Finance Society members, up 200 this year")])
index_main = f"""<section class="cine portrait" id="top">
  <div class="cine-bg"></div>
  <div class="wrap cine-in cine-grid">
  <div class="cine-text">
    <div class="byline"><span class="badge">Debt capital markets &middot; syndicate<span class="hide-s"> &middot; fixed income</span></span></div>
    <h1>{split("Anthony Ferriero")}</h1>
    <p class="kick">Looking for a 2027 analyst seat in debt capital markets.</p>
    <p class="tag">I spent nine months on a primary bond desk at Finsight, collecting order books on 15 to 20 deals a day. Since then I have built a new issue window score, a tender offer tracker and a green bond pricing study. Each one shows where it can be wrong.</p>
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
  <figure class="portrait-box"><img src="assets/headshot.jpg" width="720" height="720" alt="Anthony Ferriero" fetchpriority="high"><figcaption>Anthony Ferriero. UMass Lowell, class of 2027.</figcaption></figure>
  </div>
  <a class="cue" href="#about">Scroll</a>
</section>
{MARQ}
<section class="section" id="about"><div class="wrap two">
  <div>
    <p class="label">About</p>
    <h2>Manning School of Business, class of 2027</h2>
    <p>I am a senior at UMass Lowell studying finance and marketing, with a minor in quantitative economics. My GPA is 3.6.</p>
    <p>From December 2025 to September 2026 I was a debt capital markets analyst intern at Finsight, where I chased order books on 15 to 20 new bond deals a day. Now I train students on the Bloomberg Terminal, run the Finance Society and do green bond research.</p>
  </div>
  <div>
    <p class="label">What I have done</p>
    <h2>At Finsight, and on my own</h2>
    <p>At Finsight I covered order books and allocations, price talk to print, volume against Street estimates, attrition and new issue concession. I also wrote headlines on 25 or more liability management deals.</p>
    <p>On my own I built a score for whether the new issue window is open, a daily tracker of tender and exchange offers from SEC filings and newswires, and a study of whether green bonds price tighter at issue.</p>
  </div>
</div></section>
<div class="wrap">{board}
<div class="tape" id="tape"><div class="tape-head"><span>Live from my dashboard &middot; free data, can be 15 minutes late</span><b id="tape-when"></b></div><ul id="tape-ul"></ul><div class="tape-foot">The window score and the levels come from the <a href="dashboard.html">Morning Market Dashboard</a>, rebuilt on weekdays. Not a trading tool.</div></div></div>
{split_band("assets/ai/home-price.jpg", "I like the moment a new bond gets priced.", "Why I want to work in the primary market", "center", "Price talk, the book, the print. That is the part of the day I want to be close to.", "#FFF1C9")}
<section class="section" id="case-files"><div class="wrap">
  <p class="label">Case files</p>
  <h2>Projects, roles and results</h2>
  {cards}
</div></section>
{split_band("assets/ai/home-club.jpg", "500 members.", "The Finance Society", "center", "That is 200 more than when I became president in April 2026.", "#1F2A44", True, (("500+", "members"), ("9", "person e-board"), ("6", "events in six weeks")))}
<section class="section"><div class="wrap">
  <p class="label">Photos</p>
  <h2>Recent events</h2>
  {HOME_PHOTOS}
</div></section>
<section class="section"><div class="wrap">
  <p class="label">Timeline</p>
  <h2>My experience, newest first</h2>
  {tl}
</div></section>"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(shell("index.html", "Anthony Ferriero",
    "Finance student at UMass Lowell headed for debt capital markets, syndicate or fixed income research. Primary market experience at Finsight, a new issue window dashboard, a bond tender tracker, green bond pricing research and five DCF models.", index_main))

# ---------- research ----------
FIGS = [
    ("fig1_universe_by_year.png", "The dataset", "663 green bonds by issue year, with the 153 in the pricing sample in grey. Issuance peaked in 2021 and 2022.", False),
    ("fig3_credit_beta.png", "Why the credit adjustment matters", "The gap between each pair moves almost one for one with the change in credit spreads between the two issue dates. The slope is 0.97. Without this step, any greenium estimate mostly measures the credit cycle.", False),
    ("fig2_adjustment_steps.png", "Three steps from coupons to a greenium", "The raw coupon gap has a standard deviation of 104 bps. Taking out Treasury rates at each bond's own tenor cuts it to 64. Taking out credit, rates and tenor together cuts it to 27 and leaves a mean of 2.4 bps tighter.", True),
    ("fig4_specification_chart.png", "The estimate across 24 specifications", "Versions that keep every pair land between 2 and 4 bps tighter. Subsamples scatter more: non US issuers sit at 7.5 tighter and the 10 same week pairs at 3.7 wider. The sample splits are exploratory.", True),
    ("fig5_groups.png", "By sector and rating", "Financials show 5.1 bps tighter, p 0.20, on 36 pairs. Across the seven sector and rating groups none is significant, and after correcting for seven tests the smallest p value is 0.81. In the earlier version financials looked real. They do not now.", False),
    ("fig6_greenium_by_year.png", "By issue year", "No year departs from the pooled estimate. The confidence intervals are wide because no year holds more than 34 pairs.", False),
    ("fig7_events.png", "Seven dated events", "None of them, from the EU disclosure rules to the DeepSeek shock, shifts the greenium detectably. The smallest raw p value is 0.08 and none survives correction. These tests can only see moves of roughly 27 bps.", True),
    ("fig8_market_backdrop.png", "The market behind the sample", "The 10 year Treasury yield and the credit index used, Moody's Baa over the 30 year Treasury, with each pair's issue date marked as a tick. The pairs cluster from 2020 to 2023.", False),
    ("fig9_power.png", "How many pairs it would take", "With 153 pairs the smallest gap the test can reliably detect is 6.6 bps. Detecting 5 bps would take about 265 pairs and 3 bps about 735. The sample can reject a gap of 8 bps or more. It cannot tell 2 bps from zero.", False),
    ("fig10_permutation.png", "A test that does not depend on the model's assumptions", "Flipping the sign of each issuer's gaps at random 20,000 times produces a mean at least as large as 2.4 bps about 31 percent of the time.", False),
    ("fig12_distribution_noise.png", "The 153 gaps, and why the date gap matters", "The mean is 2.4 bps tighter and the median 4.3. Noise grows with the time between the two issue dates, from 20 bps within a week to 35 beyond two years.", False),
    ("fig11_specifications.png", "Mean versus robust estimators", "Estimators that ignore the outliers, the median and trimmed means, give 3.5 to 4.5 bps tighter. Adding back excluded pairs gives 0.2 to 1.2. The honest range is about 0 to 5 bps.", True),
    ("fig13_posteriors.png", "What the data say under different starting beliefs", "A sceptic who expects zero ends at 1.5 bps tighter. Someone who expects the larger discounts found in cross issuer studies ends at 3.4. The data pull everyone toward a small number.", True),
]
figs_html = '<ul class="figs">' + "".join(
    '<li%s><figure><a class="img" href="assets/figures/%s"><img src="assets/figures/%s" alt="%s" loading="lazy"></a><figcaption><b>%s</b>%s</figcaption></figure></li>'
    % (' class="full"' if full else "", f, f, e(t), e(t), e(c)) for f, t, c, full in FIGS) + "</ul>"

stats = [
    ("2.4 bps", "Average gap, green bonds priced tighter than the matched conventional bonds. 153 pairs from 88 issuers. Not statistically significant, p 0.30. The 95 percent interval runs from 7.1 bps tighter to 2.2 bps wider."),
    ("0 to 5 bps", "Range across other estimators and sample choices. The median pair is 4.3 bps tighter and the outlier robust estimators give 3.5 to 4.5. Adding back pairs I had excluded cuts the average to 1.2 or less. The data cannot narrow it."),
    ("+3.7 bps", "Average for the 10 pairs sold within a week of each other. The tightest matches show no discount, though 10 is too few to be sure."),
    ("p 0.67", "Test that the gap was the same across four periods from 2016 to 2026. No detectable change. After the ChatGPT launch the gap was 2.5 bps smaller, p 0.61, not significant."),
    ("6.6 bps", "Smallest true gap this sample can detect reliably. A gap of 8 bps or more is rejected. Telling 5 bps from zero would take about 265 pairs. Tests for a shift over time only see changes of roughly 27 bps."),
    ("663 bonds", "Unique green bonds after cleaning 1,226 tracker rows. 291 parent issuers, 40 countries, about $386 billion of face value, issued April 2009 to May 2026. 270 have matured."),
]
stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in stats) + "</div>"
case_page("research.html", "Green bond pricing research", "Preliminary results on whether green bonds price tighter than matched conventional bonds from the same issuer.",
          "Project, preliminary results", "Green bond pricing research", "Fixed Income Research Analyst, UMass Lowell. May 2026 to now.",
          "Do investors accept a lower yield on a green bond than on a conventional bond from the same issuer?",
          [("Method", "Matched pairs, adjusted for rates, credit and maturity",
            P("663 green bonds, of which 153 have a conventional bond from the same issuer that passes four pair rules: a US dollar twin, the same payment rank, both bonds at least $250 million, and no call before 90 percent of the life. Each pair is dated at its Bloomberg pricing date and adjusted for rates, credit spreads and maturity with Treasury and Moody's data from FRED. Matches were first screened with help from Claude. Every number here is preliminary.")),
           ("Results", "A small gap that the data cannot pin down", stat_html +
            P("On a $500 million, 10 year deal one basis point of coupon is worth about $50,000 a year, so 2.4 bps would be about $120,000 a year if it were real. The data do not show that it is.",
            "One pattern I cannot explain. Pairs where the conventional bond was issued after the green bond show a gap 11.8 bps larger than pairs where it was issued first, p 0.008. With the twin first the average is 3.2 bps wider. With the twin after it is 8.6 tighter. A symmetric model should show no difference, so this needs a reason before anyone leans on the headline.")),
           ("Try it", "How many pairs would it take", POWER_HTML),
           ("Figures", "The research in thirteen charts",
            P("One script builds every chart from the results files, so the page and the charts always agree. Click any chart to open it.") + figs_html),
           ("What I got wrong first", "Two results that did not hold up",
            P("A 25 bps result that was an artifact. An early version showed the gap shrinking by 25 bps. It came from measuring credit spreads over the 10 year Treasury, which picks up the slope of the curve. Over the 30 year the credit index tracks the ICE BofA investment grade index at 0.95 correlation, against 0.40 before. I withdrew the claim.",
              "A dating error in my own file. In October 2026 I checked the largest residuals on the terminal and found the file used settlement dates where the pricing dates belong. I pulled the Bloomberg pricing dates and applied four pair rules my supervisor adopted: a US dollar twin, the same payment rank, both bonds at least $250 million, and no early call. The average moved from 4.7 to 2.4 bps and the p value from 0.11 to 0.30. The rules were set after I had seen the earlier results, and the paper says so.")),
           ("What comes next", "Three things that would change these numbers",
            bul(["Verifying the largest residuals and 20 random pairs on the terminal, then rerunning with the confirmed set.",
                 "Replacing coupons with offering yields and daily prices, which needs TRACE and Mergent FISD access.",
                 "Finishing the twin search for the 164 live green bonds that still have no conventional match."])),
           ("Sources", "Where the numbers come from",
            '<p class="note">Built from Bloomberg, Climate Bonds Initiative and FRED data. My supervisor approved publishing summary statistics in writing. No bond level data is shown. Last updated October 2026.</p>')], banner=("assets/banners/pairs.jpg", "All 153 matched pairs in issue date order. Orange is the green bond priced tighter."))

# ---------- dcf ----------
dstats = [
    ("$8.80", "Implied value per share, base case, perpetuity method at a 9.2 percent cost of capital and 1.5 percent long term growth. The market closed at $7.77 on October 23, 2026."),
    ("$4.97", "Implied value per share, base case, exit multiple method at 7 times 2031 EBITDA. The two methods disagree, and I report the gap instead of picking one."),
    ("$3 to $15", "Range across the sensitivity grid, cost of capital 8 to 11 percent and growth 1 to 2 percent. Street price targets run $2 to $13.74."),
    ("Below zero", "Bear case equity value. If half the synergies show up and linear television falls 11 percent a year, the $84 billion of net debt is worth more than the business."),
    ("71%", "Share of enterprise value in the terminal value. The number depends on what the company looks like after 2031, not the next five years."),
    ("$5.4bn", "Synergies realized by 2030 in the base case, against a $6 billion management target. Almost all of the EBITDA growth is this line."),
]
dstat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in dstats) + "</div>"
DFIGS = [
    ("dcf1_ebitda.png", "Where the EBITDA growth comes from", "Underlying EBITDA before synergies drifts down as linear television shrinks. Every dollar of growth from 2026 to 2031 is realized synergies."),
    ("dcf2_fcff.png", "Unlevered free cash flow", "Conversion rises from about half of EBITDA to two thirds as integration costs roll off. Management's own target is more than $10 billion of free cash flow after interest by 2030, which this model does not reach."),
    ("dcf3_sensitivity.png", "Cost of capital against long term growth", "One point of discount rate moves the value by $3 to $4 a share. The company's own leverage makes the cost of capital the least certain input."),
    ("dcf4_football.png", "Four answers on one line", "The two DCF methods, the three scenarios and the Street's targets, next to the market price. The market sits inside every range."),
]
dfigs_html = '<ul class="figs">' + "".join(
    '<li class="dark"><figure><a class="img" href="assets/figures/%s"><img src="assets/figures/%s" alt="%s" loading="lazy"></a><figcaption><b>%s</b>%s</figcaption></figure></li>' % (f, f, e(t), e(t), e(c)) for f, t, c in DFIGS) + "</ul>"
case_page("dcf.html", "Skydance DCF model", "A pro forma discounted cash flow model of Skydance Corporation, formerly Paramount Skydance, after its purchase of Warner Bros. Discovery. Public filings only.",
          "Project", "Skydance DCF model", "Built October 24, 2026. Excel, 344 formulas, 18 sources. Market data as of October 23, 2026.",
          "The anchor of the media set. What is the company that just bought Warner Bros. Discovery worth, and what has to be true for the shares to be worth more than $7.77 under $89 billion of debt?",
          [("Why this company", "I covered its tender at Finsight",
            P("I covered the Paramount Skydance tender at Finsight and wanted to value a company whose bonds I had watched trade. By the time I built it, Paramount Skydance had closed its $110 billion purchase of Warner Bros. Discovery and become Skydance Corporation, SKYD on the NYSE. So the model values the combined company: about $70 billion of revenue, $89 billion of gross debt, 5.04 billion shares.",
              "The deal was paid for with $47 billion of new equity at $12 a share and about $52 billion of new debt. The stock closed at $7.77 on October 23. S&P cut the company to BB and the old Paramount bonds yield 10 to 13 percent. The discount rate, not the forecast, is the hard part.")),
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
            P("My first pass used Paramount Skydance's own filings: $30 billion of revenue, $15 billion of debt, 1.1 billion shares. The company that trades today is twice that size with six times the debt. I would have had a precise answer for a company nobody can buy. So I rebuilt the base year from both companies' filings and took the debt and share count from the October 2026 8-Ks.")),
           ("What would change the answer", "In order of how much they move it",
            bul(["<b>Synergy realization.</b> The base case takes $5.4 billion of the $6 billion target by 2030. Each $1 billion of run rate synergies is worth about $1.50 a share.",
                 "<b>Linear decline.</b> Three points a year faster, which is what Warner Bros. Discovery's linear networks did in the second quarter of 2026, takes the base case most of the way to the bear case.",
                 "<b>The discount rate.</b> Market weights give 9.2 percent. If management reaches its 3.0 times leverage target by 2029, the equity weight rises and so does the WACC, which lowers the value even as the business gets safer.",
                 "<b>Content cash spend.</b> It sits inside the working capital line at about 1 percent of revenue and I could not source it. The first combined quarterly report, due in November 2026, will say whether that is right."])),
           ("Download", "The model and its sources",
            '<p class="links"><a href="assets/Skydance_DCF_Model.xlsx">Download the Excel model</a></p>' +
            P("Blue cells are inputs. Scenario switch in Inputs C5. 18 numbered sources, mostly SEC filings. Analyst judgments are labelled where they sit. Nothing from a Bloomberg Terminal or any employer."))], banner=("assets/banners/skypath.jpg", "Skydance net leverage on the base case, with every free dollar going to debt. The target is 3.0 times by 2029."))

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
    ("5", "Companies on one DCF template. Same sheets, same formulas, same 4.95 percent risk free rate and 4.5 percent equity premium. Only the company specific inputs change."),
    ("1,860", "Formulas across the five models and the credit comps workbook, zero errors on recalculation. Every sensitivity cell is a closed form formula."),
    ("6.9x", "Skydance net debt to EBITDA, against 0.4 for Netflix, 0.6 for Fox, 1.6 for Disney and 2.3 for Comcast. The first number any desk asks for."),
    ("1.8x", "Skydance EBITDA to interest. The other four cover interest 8 to 22 times. Below 2 is where covenants and ratings start to bite."),
    ("-31%", "EBITDA miss that wipes out Skydance's equity at today's multiple. Comcast's equity survives a 50 percent miss, Fox's and Netflix's survive more than 90."),
    ("4.5x", "Where Skydance's net leverage lands by 2031 with every free dollar going to debt. Management's target is 3.0 by 2029. The gap is asset sales or equity."),
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
case_page("media.html", "Media DCF models and credit comps", "Five discounted cash flow models of Skydance, Netflix, Disney, Comcast and Fox on one template, then a credit comparison built the way a debt capital markets or syndicate desk would build it.",
          "Project", "Media DCF models and credit comps", "Built October 24 and 25, 2026. Five Excel models plus a credit comps workbook. 1,860 formulas, 71 sources. Market data as of October 22 and 23, 2026.",
          "Five media companies valued the same way, then lined up the way a desk lines them up: leverage, coverage, cash flow against debt, the equity cushion under the bonds, and where the paper prices.",
          [("Why I built this", "The primary market, and why a bond prices where it does",
            P("I want a debt capital markets or syndicate seat, or a fixed income research job. What I like most is the moment a new bond gets priced. Where the talk starts, how the book builds, where it prints and what it does the next day. The market checks your numbers within hours.",
              "At Finsight I spent nine months as close to that as an intern can get. I collected order books from 30 or more syndicate desks on 15 to 20 deals a day, and followed price talk to print and volume against Street estimates. I also wrote headlines on more than 25 liability management deals.",
              "This page is five companies I covered or watched, valued the same way and then read as credits. Skydance is the anchor because I covered the Paramount tender and then watched the market reprice the whole capital structure when the Warner Bros. Discovery debt came.")),
           ("The five models", "One template, five companies, and what each price already assumes", m5_stat_html + m5_table +
            P("One page per company: <a href=\"dcf.html\">Skydance</a>, <a href=\"dcf-nflx.html\">Netflix</a>, <a href=\"dcf-dis.html\">Disney</a>, <a href=\"dcf-cmcsa.html\">Comcast</a>, <a href=\"dcf-foxa.html\">Fox</a>. Reversing each DCF gives the growth and exit multiple the share price already assumes, in the last three columns. Four prices reconcile with their filings within a point of growth. Comcast is priced as if its cash flow shrinks 5 percent a year forever, and no scenario I built is that bad. I am not saying the market is wrong. I am saying the price and the filings disagree, and by how much.",
              "Model outputs under stated assumptions. Nothing here is a recommendation to buy or sell anything.")),
           ("Try it", "Move the inputs and watch the value move", explorer_html()),
           ("The credit comps", "The same five, read the way a desk reads them", credit_table +
            P("A desk starts with net debt to EBITDA, then coverage, then years of free cash flow to repay the debt, then how much equity sits under the bonds if EBITDA misses. Skydance fails every test the other four pass. Net debt is 68 percent of enterprise value, free cash flow after interest is about zero in year one, and a 31 percent EBITDA miss leaves nothing for the equity.",
              "That is why the first lien 2031s trade at 272 bp, 170 bp wide of the BBB index, and the second liens at 483 bp, while Netflix printed a 10 year at 5.346 percent in July. The spreads in the table are where I think a new 10 year prints for each name. Only Skydance's is anchored on sourced levels; the other four are my inputs, labelled in the workbook.")),
           ("The deleveraging question", "Can Skydance get to 3.0 times on cash flow alone",
            P("Management's target is 3.0 times by 2029. On my base case, with every free dollar going to debt, net leverage is 6.3 times at the end of 2027, 5.0 at the end of 2029 and 4.5 at the end of 2031. Getting to 3.0 means cutting about $47 billion of net debt on under a billion of first year free cash flow after interest. That is asset sales or equity, which is what the second lien equity clawback is for.") +
            dfig([("m5_skypath.png", "Net debt and net leverage, year by year", "Base case, no asset sales, no equity. The line never reaches the target.", True)])),
           ("Charts", "Five charts, one per question",
            dfig([("m5_credit.png", "Leverage and coverage", "Skydance is the only one past 3 times leverage and the only one under 2 times coverage.", True),
                  ("m5_cushion.png", "The equity cushion", "Equity value for each EBITDA miss at today's multiple. Skydance hits zero at 31 percent, Comcast at 50, the other three past 80.", True),
                  ("m5_vs_market.png", "Where each DCF lands against its price", "Dots are the base case on each method, bars run bear to bull. Only Comcast's whole range sits above its price.", True),
                  ("m5_implied.png", "Reverse the DCF", "What I assumed against what the price implies. They agree everywhere except Comcast.", True),
                  ("m5_wacc_tv.png", "Cost of capital and terminal value share", "Same risk free rate and premium in all five; the spread in WACC is beta and leverage. Two thirds or more of every valuation sits past the forecast.", True)])),
           ("What is the same and what is not", "The rules I held constant",
            bul(["<b>Same discount rate inputs.</b> 10 year Treasury 4.95 percent, equity risk premium 4.5 percent, cash tax 23 percent, market weights, Hamada relevering. Cost of debt 75 to 125 bp over Treasuries for the four investment grade names, 8 percent blended for Skydance.",
                 "<b>Same cash flow definition.</b> Adjusted EBITDA less stock compensation, cash restructuring, cash taxes on profit after tax depreciation, capex and a working capital and content line. Stock compensation is a real cost in all five.",
                 "<b>Same mechanics.</b> Mid year discounting, a first year stub, perpetuity and exit multiple side by side, three scenarios on one switch.",
                 "<b>Different fiscal years.</b> Disney and Fox run FY2027 to FY2032 with stubs of 0.94 and 0.68. The other three run calendar 2026 to 2031 with a 0.19 stub.",
                 "<b>Different pending deals.</b> Comcast before the NBCUniversal and Sky spin. Fox without Roku. Skydance after Warner Bros. Discovery, because that one closed.",
                 "<b>Interest expense.</b> Comcast's and Disney's are reported. Skydance's, Netflix's and Fox's are estimates from gross debt and a blended coupon, flagged in the comps."])),
           ("What I got wrong first", "Betas off a quote page, and a cost of debt below the Treasury yield",
            P("Quoted betas as unlevered betas. Netflix came out at an 11.6 percent WACC and $42 a share, and Comcast's unlevered below a utility's. I set them by hand, 0.6 for Fox, 0.7 for Comcast, 0.9 for Skydance, 1.05 for Disney, 1.2 for Netflix, and wrote down why on each WACC sheet.",
              "Then the one a desk would catch first: the four investment grade names borrowing at 5 to 5.5 percent with the 10 year at 4.95, which is 5 to 55 bp of spread. Nobody prints there. I moved them to 75 to 125 bp over. It barely touches three of them and takes $3 off Comcast, because half its capital is debt.",
              "On October 26 I checked those inputs against where each name's long paper actually trades, on a terminal. Disney, Netflix and Fox hold within the noise. Comcast is the miss: after three agencies put it on negative watch for the spin, the market has it wider than my 95 bp by a margin that would not surprise a desk. Moving Comcast's cost of debt to where the market is lifts its WACC to 7.8 percent and takes about $2 more off the perpetuity value. It changes no conclusion, because the model still lands far above the price. The levels themselves stay off this site.")),
           ("Download", "Five models and the credit comps",
            '<p class="links"><a href="assets/Media_Credit_Comps.xlsx">Credit comps workbook</a> &nbsp;&middot;&nbsp; <a href="assets/Skydance_DCF_Model.xlsx">Skydance</a> &nbsp;&middot;&nbsp; <a href="assets/NFLX_DCF_Model.xlsx">Netflix</a> &nbsp;&middot;&nbsp; <a href="assets/DIS_DCF_Model.xlsx">Disney</a> &nbsp;&middot;&nbsp; <a href="assets/CMCSA_DCF_Model.xlsx">Comcast</a> &nbsp;&middot;&nbsp; <a href="assets/FOXA_DCF_Model.xlsx">Fox</a></p>' +
            P("Blue cells are inputs. Scenario switch in Inputs C5 of any model. The comps workbook names the model every figure came from. No input in these files comes from a Bloomberg Terminal or any employer. The October 26 check above was a comparison only."))], banner=("assets/banners/media.jpg", "Leverage first, value second."))


def company_dcf_page(fname, name, h1, meta, lede, why, stats, build, charts, wrong, change, xlsx, extra_note):
    stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in stats) + "</div>"
    case_page(fname, "%s DCF model" % name, "A discounted cash flow model of %s on the same template as my Skydance model. Public filings only." % name,
              "Project", h1, meta, lede,
              [("Why this company", why[0], P(*why[1])),
               ("The result", "The numbers", stat_html + P("Model outputs under stated assumptions. Nothing on this page is a recommendation to buy or sell anything.")),
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
        "Netflix walked away from Warner Bros. Discovery in February 2026 with a $2.9 billion termination fee. I strip it out of cash flow."]),
    [("$49.79", "Base case, perpetuity method at a 10.3 percent WACC and 3 percent long term growth. Below the $65.85 close on October 23, 2026."),
     ("$68.16", "Base case, exit multiple method at 14 times 2031 EBITDA. Above the market. The two methods disagree by $18 and that gap is the whole story."),
     ("5.1%", "Perpetual growth the price implies. A 10 percent discount rate and 3 percent growth cannot reach $66 on a business that already earns 32 percent margins."),
     ("72%", "Share of value past 2031. Netflix is a terminal value with a forecast attached, like every growth company."),
     ("$34 to $82", "Bear to bull across both methods. Bear fades subscription growth to 3 percent with flat margins. Bull keeps double digits through 2028 and pushes margins to 39 percent."),
     ("17.1x", "Market EV to 2026 EBITDA. Skydance trades at 10, Disney at 9, Fox at 8, Comcast at 4.5.")],
    ["<b>Base year.</b> 2026 guidance of about $51.1 billion of revenue and a 31.5 percent operating margin from the October 20 shareholder letter, split into subscription and about $2.7 billion of advertising.",
     "<b>Revenue.</b> Subscription grows 10 percent fading to 5. Advertising grows 40 percent fading to 15 off a small base, with 15 new ad markets in 2027.",
     "<b>EBITDA.</b> Operating income plus property depreciation only. Content amortization, $16.4 billion in 2025, stays inside costs. The margin rises about a point a year to 36 percent by 2031.",
     "<b>Content cash.</b> Netflix spends about 1.1 times what it amortizes. The excess, about 3.3 percent of revenue, sits in the working capital and content line and fades to 2 percent as spending growth slows.",
     "<b>Discount rate.</b> Unlevered beta 1.2, almost no leverage, so the WACC is close to the 10.5 percent cost of equity. Cost of debt 5.8 percent, the July 2026 notes repriced about 85 bp over today's Treasury.",
     "<b>Equity bridge.</b> $15.3 billion of gross debt, $8.2 billion of cash, about 4,164 million shares. The share count is an estimate from market cap over price because I could not retrieve the 10-Q cover, and it is flagged in the model."],
    [("m5_nflx_cash.png", "Base case EBITDA, free cash flow and revenue", "Revenue reaches about $80 billion by 2031. Free cash flow conversion is high because capex is 1.5 percent of revenue and the content line is small relative to the margin.", False),
     ("m5_nflx_football.png", "Where the answers land", "The perpetuity grid reaches the price only below a 9.5 percent WACC. The exit multiple grid straddles it at every WACC. Street targets run $57 to $126.", False)],
    ("I took the quoted beta at face value", [
        "A 1.61 beta off a quote page gave an 11.6 percent WACC and $42 a share. It is a five year regression on a stock that fell by half in 2022. I used 1.2, wrote down why, and the sensitivity grid runs 8 to 11 percent so a reader can put the 1.61 back."]),
    ["<b>The exit multiple.</b> Each turn of EBITDA is worth about $4 a share. 14 times is below the 17 the market pays today and above where a company growing 5 percent should trade in 2031.",
     "<b>Margin ceiling.</b> The base case stops at 36 percent. Every point of terminal margin is worth about $1.50 a share.",
     "<b>Advertising.</b> The October 20 letter cut 2026 ad guidance from about $3 billion to $2.7 billion. Ads are 5 percent of revenue, so this is a small line that the market treats as a big one.",
     "<b>The share count.</b> If the real count is 4,195 million, the diluted figure, every value on this page is about 0.7 percent lower."],
    "NFLX_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. Sources are numbered and cited next to each figure. Nothing in the model comes from a Bloomberg Terminal or from any employer.")

company_dcf_page("dcf-dis.html", "Disney", "Disney DCF model", "Built October 24, 2026. Excel, 323 formulas, 12 sources. Fiscal year ends in late September. Market data as of October 16, 2026.",
    "The closest thing to Skydance that already works. Studios, linear networks and streaming under one roof, plus the parks.",
    ("Skydance with parks and twenty years of integration", [
        "Disney has the same three pieces as the combined Skydance, studio, linear networks and streaming, and has already made them one company. Its Entertainment segment is the best public read on where Skydance's margins could settle. Experiences is the piece Skydance does not have, and it is more than half of Disney's operating income.",
        "Fiscal 2026 results come November 17. The base year is nine months of actuals plus fourth quarter guidance, and the model says so."]),
    [("$79.11", "Base case, perpetuity method at a 9.4 percent WACC and 2 percent long term growth. Below the $110.16 price."),
     ("$114.42", "Base case, exit multiple method at 10 times FY2032 EBITDA. On the price. The market is paying about 9 times today."),
     ("4.1%", "Perpetual growth the price implies on the perpetuity method. For a company whose linear networks are shrinking, that is a lot to assume forever."),
     ("68%", "Share of value past FY2032."),
     ("$33 to $138", "Bear to bull across both methods. Bear shrinks Entertainment 1 percent a year with margins falling to 21 percent. Bull grows all three segments and takes margins to 28 percent."),
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
        "Fiscal 2025 shows a tax benefit from a $3.3 billion Hulu item, so the reported rate is useless. I use the same 23 percent cash rate as the other four, with the FY2024 derived 23.7 percent as the check. The $110.16 price is from October 16, not October 23, and it is flagged."]),
    ["<b>Linear decline inside Entertainment.</b> Linear was $3 billion of the segment's $4.7 billion of operating income in FY2025. If it falls 10 percent a year and streaming does not fill the hole, the base case becomes the bear case.",
     "<b>Capex.</b> Each point of revenue in terminal capex is worth about $8 a share. The ships are the reason this matters.",
     "<b>Experiences growth.</b> The segment is 57 percent of operating income. Two points of growth there is worth more than five points in Sports.",
     "<b>The November 17 results.</b> They replace my estimated base year with a real one."],
    "DIS_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. The base year is labelled as an estimate until the FY2026 10-K is out. Nothing in the model comes from a Bloomberg Terminal or from any employer.")

company_dcf_page("dcf-cmcsa.html", "Comcast", "Comcast DCF model", "Built October 24, 2026. Excel, 311 formulas, 14 sources. Market data as of October 23, 2026.",
    "The one the model cannot reconcile. At $22 the market is pricing Comcast as a business that shrinks forever, and the filings do not show that.",
    ("A media company that is breaking itself up", [
        "Comcast is what Skydance would look like after a decade: cable, a studio, parks, a streaming service that just turned profitable, 2.3 times leverage. It spun off its cable networks in January 2026 and will spin NBCUniversal and Sky in mid 2027, so it is becoming a broadband utility.",
        "I value it as it is today, before the spin, on nine months of 2026 actuals. That is the only basis the filings support."]),
    [("$44.48", "Base case, perpetuity method at a 7.5 percent WACC and 0.5 percent long term growth. More than twice the $22.04 price."),
     ("$34.81", "Base case, exit multiple method at 5.5 times 2031 EBITDA. The market pays 4.5 times today and paid 6 to 7 for most of the last decade."),
     ("-5.3%", "Perpetual decline in cash flow that the price implies. The bear case, with connectivity falling 3 percent a year and margins down to 25 percent, still lands at $23 to $27."),
     ("3.6x", "Exit multiple the price implies. Below where any large cable company has traded outside a crisis."),
     ("7.5%", "WACC. Half of Comcast's capital is debt at about 4.5 percent after tax, which is why the discount rate is the lowest of the five and the value is the most sensitive to it."),
     ("69%", "Share of value past 2031.")],
    ["<b>Base year.</b> 2026 as now reported, without Versant and from the second quarter without Sky Deutschland. Nine months of $90.7 billion of revenue and $25.9 billion of adjusted EBITDA, annualized to $120.5 billion and $35 billion.",
     "<b>Revenue.</b> Two lines. Connectivity and Platforms, $79 billion, falls 1 percent a year then flattens as price offsets broadband losses. Content and Experiences, $41.5 billion net of eliminations, grows 2 percent.",
     "<b>EBITDA.</b> Margin 29 percent drifting down to 28. Separation costs of $500 million in 2026, $800 million in 2027 and $300 million in 2028, which are my estimates.",
     "<b>Cash flow.</b> Capex 9.5 percent of revenue. Depreciation of $16 billion a year shelters a lot of the profit from cash tax, which is a real reason cable cash flow is high relative to EBITDA.",
     "<b>Discount rate.</b> Unlevered beta 0.7, 1.0 debt to equity, levered beta 1.24, cost of equity 10.6 percent, cost of debt 5.9 percent. Market weights give 7.5 percent.",
     "<b>Equity bridge.</b> $87.4 billion of debt, $7.6 billion of cash, 3,551 million shares from the October 15 cover."],
    [("m5_cmcsa_cash.png", "Base case EBITDA, free cash flow and revenue", "Flat revenue, flat EBITDA, and unlevered free cash flow of about $17 billion a year. The market enterprise value is about nine years of that.", False),
     ("m5_cmcsa_football.png", "Where the answers land", "Every range starts above the price. That is unusual and it is the finding, not a reason to trust the model more.", False)],
    ("I believed the first answer", [
        "The first build gave $60 a share. On a $78 billion company that is not a finding, it is a warning. I raised the beta, cut growth to 0.5 percent, cut the exit multiple to 5.5, put the cost of debt at 95 bp over Treasuries and ran the bear case harder. It still lands at $35 to $44. So the page does not say Comcast is cheap. It says what the price assumes, a 5 percent a year decline forever, and lets the reader decide whether broadband and parks do that."]),
    ["<b>The discount rate.</b> Each point of WACC is worth $8 to $15 a share on the perpetuity method. If the spin leaves the broadband company with a higher cost of debt, this moves fast.",
     "<b>Broadband losses.</b> Comcast is losing subscribers to fixed wireless and fiber. The bear case runs connectivity down 3 percent a year. The price implies worse.",
     "<b>The spin itself.</b> A sum of the parts after mid 2027 is a different model with two balance sheets, and the S-4 or Form 10 is the document to build it from.",
     "<b>Theme parks.</b> Segment EBITDA fell 17 percent in the third quarter of 2026 on a tough Epic Universe comparison. I grow the segment 2 percent, which may be generous."],
    "CMCSA_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. The 2026 base year is annualized from nine months and labelled as such. Nothing in the model comes from a Bloomberg Terminal or from any employer.")

company_dcf_page("dcf-foxa.html", "Fox", "Fox DCF model", "Built October 24, 2026. Excel, 323 formulas, 9 sources. Fiscal year ends June 30. Market data as of October 22, 2026.",
    "A pure linear network company with no debt problem, so it isolates the one assumption that drives the Skydance bear case: how fast cable networks decline.",
    ("The clean read on linear decline", [
        "Skydance's bear case breaks because linear television shrinks 11 percent a year under $89 billion of debt. Fox is two thirds cable and broadcast networks with almost no net debt, so it shows what linear is worth on its own. Fiscal 2026 revenue still grew 5 percent with Super Bowl LX, so the decline is not a straight line.",
        "Fox agreed in June 2026 to buy Roku for about $22 billion. It has not closed, so Roku is out."]),
    [("$72.52", "Base case, perpetuity method at a 7.6 percent WACC and 1 percent long term growth. Just above the $68.27 price."),
     ("$58.88", "Base case, exit multiple method at 7 times FY2032 EBITDA. The market pays about 8 times today."),
     ("0.5%", "Perpetual growth the price implies. The market and I agree on Fox within a point, which is the best check I have that the template works."),
     ("67%", "Share of value past FY2032. Lowest of the five. A long first year and flat cash flow put more of the value inside the forecast."),
     ("$42 to $97", "Bear to bull across both methods. Bear runs cable down 4 to 5 percent a year with margins at 17 percent. Bull holds margins at 23 and grows Tubi.")],
    ["<b>Base year.</b> Fiscal 2026 actuals: revenue $17.1 billion, adjusted EBITDA $3.9 billion, capex $502 million, depreciation $410 million.",
     "<b>Revenue.</b> Three lines. Cable $7.5 billion, Television $9.9 billion and Other $400 million for FY2027. Growth alternates, up in even fiscal years with political advertising, Super Bowls and the World Cup, down in odd years.",
     "<b>EBITDA.</b> Margin 22 percent drifting down to 20 as sports rights grow faster than revenue. Fiscal 2026 was 22.8 percent.",
     "<b>Cash flow.</b> Capex 2.5 percent of revenue and a 0.5 percent working capital line for sports rights prepayments. Fiscal 2026 free cash flow fell to $1.5 billion from $3 billion with no explanation in the release, and the model does not assume it recovers all the way.",
     "<b>Discount rate.</b> Unlevered beta 0.6, under 0.1 debt to equity, cost of equity 7.8 percent, cost of debt 6.2 percent. WACC 7.6 percent.",
     "<b>Equity bridge.</b> $6.6 billion of debt, $4.2 billion of cash, 419.65 million shares from the 10-K cover, Class A and B together. The stub is 68 percent of FY2027."],
    [("m5_foxa_cash.png", "Base case EBITDA, free cash flow and revenue", "The sawtooth is the even year political cycle. EBITDA drifts down through it because rights costs do not take years off.", False),
     ("m5_foxa_football.png", "Where the answers land", "Both methods bracket the price. Street targets run $60 to $97 and the consensus is $78.", False)],
    ("I almost built the combined company", [
        "Roku adds $14.2 billion of cash consideration, a bridge loan, 143 million new shares and $400 million of synergies. Modelling that from a press release would be guessing at the capital structure. Fox is standalone, and the Roku model waits for the S-4."]),
    ["<b>Cable decline.</b> Each point of annual cable revenue decline is worth about $2 a share. This is the same lever as the Skydance bear case, without the debt.",
     "<b>Sports rights.</b> The margin path assumes rights costs grow faster than revenue. If Fox lets a package go, margins hold and the bull case is in play.",
     "<b>Roku.</b> Closes in the first half of 2027 and changes the share count, the debt and the growth rate at once.",
     "<b>The missing FCF.</b> The base case assumes about $2.4 billion of unlevered free cash flow a year. If fiscal 2026 was the new normal rather than timing, the base case is high by about $30 a share."],
    "FOXA_DCF_Model.xlsx", "Blue cells are inputs. Pick a scenario in Inputs cell C5. Roku is excluded on purpose. Nothing in the model comes from a Bloomberg Terminal or from any employer.")

# ---------- tender ----------
case_page("tender.html", "Tender Tracker", "A daily tracker of bond tender and exchange offers built from SEC filings and newswires, with its error rates published.",
          "Project, live", "Tender Tracker", "Personal project. October 2026 to now.",
          "A daily tracker of cash tender offers and exchange offers for corporate bonds, read from SEC filings and newswire press releases.",
          [("What it does", "One row per offer, with a link to the filing",
            P("Each offer shows its securities, cap, expiration and the steps seen so far, with a link to the filing or press release behind every row. It reads public SEC filings and public newswire pages and rebuilds every day.") +
            P("I built the page to look like my market dashboard: a table of offers you can sort and search, a panel of offers by status that you can click to filter, filings read by day and the offers expiring next.") +
            '<p class="links"><a href="https://ferrierotony-cmyk.github.io/market_dashboard/tender/">Open the tracker</a> &nbsp;&middot;&nbsp; <a href="%s" rel="noopener">Code</a></p>' % TENDER_CODE +
            '<a class="shot" href="https://ferrierotony-cmyk.github.io/market_dashboard/tender/"><img src="assets/tender-tracker.jpg" alt="The Tender Tracker page on a dark background, showing a table of offers with their status, securities, caps and expiration dates, with panels for offers by status, filings read by day and the offers expiring next" width="1920" height="960" loading="lazy"></a>'),
           ("How often it is right", "Nine in ten on type and dates, three in four on securities and caps",
            P("AI reviewers graded it against the filings on releases the rules had never seen. Offer type and dates were right about nine times in ten. Securities and caps were right about three times in four. A person has not checked these rows.") +
            P("The most common mistake is counting new notes being issued, or notes being redeemed, as the notes targeted. On the period the rules were built on, it found 32 of 33 offer releases, which is a best case. On October 26 I fixed the redeemed notes case and a few grouping errors. Those fixes have not been tested on new filings yet, so I do not claim a new number for them.") +
            P("The weak spot was recall. Through October 26 the search only read Form 8-K exhibits with six phrasings, and it found 17 offers in 90 days. Many issuers never file an 8-K for a tender, they only put out a press release. On October 27 I widened the SEC search to 54 phrasings and Form 6-K, added PR Newswire and Bing News as sources, and the same window went to 44 offers. Fourteen more came from issuer sites and wires the script cannot reach, typed in by hand with the source linked and tagged HAND on the page. The accuracy numbers above are for the rules, not the hand rows.")),
           ("How it is built", "Two stages, no paid services",
            bul(["A fetch step searches EDGAR full text search for tender and exchange offer press releases, then PR Newswire and Bing News for releases that never reached EDGAR, and caches the text.",
                 "An offline rules step extracts offer type, securities, cap and dates, then groups releases into offers.",
                 "A GitHub Actions job runs both every morning and publishes the page. It costs nothing to run."]))], banner=("assets/banners/tender.jpg", "Filings and releases the tracker read, by day, July 29 to October 27. Orange is a step in a tender or exchange offer, grey is everything else."))

# ---------- dashboard ----------
case_page("dashboard.html", "Morning Market Dashboard", "A market dashboard that scores whether the new issue window is open, built in R from free data.",
          "Project, live", "Morning Market Dashboard", "Personal project. June 2026 to now.",
          "One screen that answers one question every morning: is the new issue window open?",
          [("What it does", "A score built from the inputs a syndicate desk watches",
            P("It reads Treasury yields, credit spreads, volatility and macro data from free sources and scores the window from VIX, MOVE, the one week move in IG and HY spreads, stock futures and where spreads sit in their one year range. Built in R. It rebuilds several times a day on weekdays.") +
            '<p class="links"><a href="https://ferrierotony-cmyk.github.io/market_dashboard/">Open the dashboard</a> &nbsp;&middot;&nbsp; <a href="%s" rel="noopener">Code</a></p>' % REPO +
            '<a class="shot" href="https://ferrierotony-cmyk.github.io/market_dashboard/"><img src="https://ferrierotony-cmyk.github.io/market_dashboard/market_dashboard.png" alt="Dashboard snapshot: Treasury curve, 2, 10 and 30 year history, curve slope and credit spreads" loading="lazy" onerror="this.parentNode.style.display=\'none\'"></a><p class="note">The snapshot is rebuilt with the dashboard on weekdays.</p>'),
           ("What to know", "Free data only, and a sample portfolio",
            P("The public build uses free data feeds only. The portfolio panel on the public build is a sample book and is labeled as one. A private version on my laptop pulls Bloomberg data through the API, with ten panels on the Treasury curve, DV01, P&amp;L and credit spreads, and refreshes every morning. That version is not published."))],
          banner=("assets/banners/rates.jpg", "The 10 year Treasury and the Baa spread since 2015, two of the inputs behind the window score. FRED data."))

# ---------- roles ----------
case_page("finsight.html", "Finsight", "Debt Capital Markets Analyst Intern at Finsight, December 2025 to September 2026.",
          "Role", "Finsight", "Debt Capital Markets Analyst Intern. New York. December 2025 to September 2026.",
          "Finsight is a fintech platform that tracks the primary bond market for bankers and investors. I chased the order books on new deals.",
          [("The job", "Chasing order books",
            P("Syndicate desks run the order book on every new bond deal, and none of them has to tell you what is in it. I called and messaged desks at 30 plus investment grade and high yield banks for book sizes as deals moved from talk to guidance to launch, then got it out to the bankers and investors on the platform before the next update hit. Fifteen to twenty deals a day.",
              "Once you build a relationship the books come faster. None of those bankers owed me anything, and that taught me the most.")),
           ("A day on the desk", "A normal day, hour by hour", day_html()),
           ("High yield, then investment grade", "Two desks, two different markets",
            P("In high yield, in the spring, every deal is a story about a company, its covenants, its call structure and where the money goes. In investment grade, over the summer, the issuers are big and frequent, spreads are tight, and a lot comes down to picking the window.")),
           ("Deals I covered", "Deals I still talk about",
            bul(["<b>Alphabet's $25 billion offering</b>, ten tranches out to 40 years, book around $115 billion. A company that had always funded itself from cash, borrowing for data centers. I chased that book all day.",
                 "<b>The Paramount Skydance exchange and tender offers.</b> Consent solicitations, exchange offers into second lien notes, and cash tenders on the 2027 and 2028 notes. I wrote the wire headlines on the liability management flow, 25 plus deals across tenders, exchanges and consents. That work is why the tender tracker and the Skydance DCF exist.",
                 "<b>Relative value comps.</b> Screens on tenor, rating and spread to gauge new issue concession, sent out with the deal terms."])),
           ("The tenor screens", "Where does this print sit against every comparable deal since 2022?",
            P("Ten daily screens: the lowest spreads and lowest coupons printed in the 3, 5, 7, 10 and 30 year, every investment grade deal back to 2022, by week, month and year, with issuer, ratings, size, call, final book, coupon, yield and spread on every row. A check sheet held the prints that looked wrong until I confirmed them.",
              "When a banker asked how a new 5 year compared, the answer was one screen. Concession in practice is one deal against a thousand others, not a formula.")),
           ("The end of day tally", "What priced, where it came from, and how far it moved",
            P("Every afternoon the day's investment grade prints went into one table: issuer, rating, size, tenor, final book, leads, price talk, where it priced, the move from talk to print, and the identifiers. That table is where the morning wire's numbers came from.")),
           ("Volume against the Street", "Did the month come in where the desks said it would?",
            P("Issuance volume against the Street's estimates by day, week and month, with deal counts, tranche size, talk to print, final book, attrition, concession and end of week trading. The daily sheet went back years with holidays, zero days and Fed days marked. It is the table you open when someone says August is dead.")),
           ("Backfilling the database", "Checking 2019 Latin America deals one by one",
            P("The platform's history had gaps. I checked a list of 2019 Latin American deals one by one against what the platform had and sent back the missing, the wrong and the doubtful as a task list. Not glamorous. It is what makes a dataset worth paying for.")),
           ("What I did on my own time", "Treating it like a job, not an internship",
            bul(["Reached out to the syndicate people I was pulling books from, at BBVA, Scotiabank and HSBC, to learn how they read demand and set concession. Three are still regular conversations.",
                 "Taught myself the Bloomberg API in R and built the first market dashboard so I saw the curve, DV01, spreads and new issue comps every morning.",
                 "Flew to New York in July on my own dime to work from the office for a few days and meet the team in person."])),
           ("Since Finsight", "ICE Fixed Income Forum at the NYSE, October 2026",
            P("ICE Fixed Income Forum at the New York Stock Exchange, October 21, 2026.") +
            photos([("nyse-stage", "On stage at the NYSE after the forum, October 21, 2026.", "wide"), ("nyse-podium", "The podium.", "tall"), ("nyse-seated", "The panel chairs, after the panel.", ""), ("nyse-podium-side", "Getting a feel for the room.", "tall")]))], banner=("assets/banners/d-finsight.jpg", "Illustration of an order book from price talk to print. Not a real deal."))
tc_stats = [
    ("$1M", "Virtual starting capital per team. Long only, single name stocks from the WLS index, no ETFs, no leverage."),
    ("WLS", "The benchmark: Bloomberg World Large, Mid and Small Cap Price Return Index. Teams are ranked on relative P&L against it, not raw return, so in a down market not losing can win."),
    ("20%", "Most any one position can be of the book. We cap ours lower so one bad name cannot sink the window."),
    ("2,600+", "Teams in the fall 2025 edition, more than 11,000 students from 50 countries, 72,000 virtual trades. The grand prize team returned more than 400 percent."),
    ("8 weeks", "Roughly the trading cycle. Winners are announced around the end of November, so most of the return has to come from things that happen inside the window."),
    ("Oct 12", "The day our book opened for the fall 2026 round."),
]
tc_stat_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in tc_stats) + "</div>"
case_page("bloomberg.html", "Bloomberg at UMass Lowell", "Bloomberg Terminal Assistant at UMass Lowell since September 2026, and captain of the UML team in the Bloomberg Global Trading Challenge.",
          "Role", "Bloomberg at UMass Lowell", "Terminal Assistant, September 2026 to now. Trading Challenge captain, fall 2026. Investment Analyst, spring 2026 round.",
          "I train business school students on the Bloomberg Terminal, pull data for faculty research, and captain the UML team in the Bloomberg Global Trading Challenge. Same room, same terminals, two different jobs.",
          [("Terminal Assistant", "Training and data pulls",
            bul(["Train business school students across 10 classes, from SRCH and YAS to curves and spreads: bond screens, yield and spread checks, company financials.",
                 "Pull Bloomberg data for faculty research and class assignments. The green bond research on this site started as one of those pulls."])),
           ("One pull in detail", "ESG scores for 2,172 US listed companies",
            P("A professor asked whether the terminal had ESG scores. I screened every US listed company with a Bloomberg ESG score, pulled ten years of history plus the current MSCI, Sustainalytics and S&P scores, and sent a values only file with a field guide tab. I got it wrong twice first: duplicate tickers in a hand built list, and a file with live Bloomberg formulas still in it.")),
           ("The Trading Challenge", "A university competition run entirely inside the terminal", tc_stat_html +
            P("Scoring on relative P&L against the WLS index changes how you play it. Beating a falling index by holding up is worth as much as beating a rising one by running ahead of it.",
              "UMass Lowell's teams are run by Professor Weicker. I was an analyst on the spring 2026 round and I captain the fall 2026 team.")),
           ("How I run the team", "Four lanes and a rule set written down before the first trade",
            bul(["<b>Lanes.</b> I own the book, the final call on every trade and the sizing. Two analysts pitch names with a one liner: what it is, why now, the catalyst and date, what kills it. One keeps the trade log. One owns the earnings calendar.",
                 "<b>Entry rule.</b> Only buy a stock that is above its open and beating the WLS benchmark that morning. No catching falling names.",
                 "<b>Sizing and exits.</b> Caps below the 20 percent limit and a written exit on every name before it goes in. The log carries the reason for every trade.",
                 "<b>The screens.</b> EQS for candidates, EE and ANR for what is priced in, the earnings calendar, N and CN for news, GP for charts, PORT for exposures. My R dashboard points at the book for the daily snapshot."])),
           ("The book so far", "Two energy names and four passes",
            P("October 12: bought Exxon and Chevron after oil bounced. Passed on Goldman Sachs, Nvidia, ASML and General Dynamics the same week. General Dynamics missed the rule by 39 cents on October 15. Stayed out of tech after the hot CPI and PPI prints and the chip selloff, the pass I would defend hardest. Chevron's exit is written down: $225, or earlier if Brent falls below $102.",
              "No running return here. The result goes up when the window closes, good or bad.")),
           ("What past winners did", "Volatility with a thesis, not volatility alone",
            P("The through line in past winners is earnings and catalysts inside the window, not safe long term picks. RIT's 2024 team leaned into volatility and foreign names. USF's 2025 captain ran an earnings volatility book. The fall 2025 grand prize team from the Chinese University of Hong Kong won on discipline and Bloomberg's own data.",
              "The cautionary tale is the team that gambled early, went up 18 percent, parked in cash and was not invited to the finals because the judges decided it was not investing. That is why every name in our book has a written thesis, and a log that survives a judge.")),
           ("What I am learning", "Equities are not my home market",
            P("My work is bonds. A long only equity book scored against an index is a different game, and two weeks of it taught me more about sizing and about passing on a trade than anything I read. The rule that kept us out of tech on CPI week is now my risk management answer.")),
           ("Sources", "Where the competition facts come from",
            '<p class="note">Bloomberg press release on the fall 2025 edition, January 2026. Bloomberg for Education challenge page. TUM School of Management challenge page for the 2026 format. Our rules, trades and passes are from my own trade log.</p>')], banner=("assets/banners/d-bloomberg.jpg", "Ten classes and the Trading Challenge book. Drawn from the numbers on this page."))
wacc = [
    ("4.2%", "Risk free rate, the Treasury yield on the October 31, 2025 valuation date."),
    ("1.16", "Beta. Eleven public engineering and construction companies screened down to the four with clean five year data, median unlevered beta 1.14, relevered for the company's small debt."),
    ("5.0%", "Equity risk premium, the Kroll recommended figure on the valuation date."),
    ("7.06%", "Size premium, Kroll microcap decile. The single biggest judgment in the build. Without it the value would nearly double."),
    ("0%", "Company specific premium. The named risks were priced into the forecast instead, by cutting management's growth. Adding a premium too would count the same risk twice."),
    ("16.8%", "Weighted average cost of capital, 97.7 percent equity at 17.06 percent and 2.3 percent debt at 5.93 percent after tax."),
]
wacc_html = '<div class="stats">' + "".join('<div class="stat"><div class="n">%s</div><p>%s</p></div>' % (n, e(t)) for n, t in wacc) + "</div>"
case_page("valuation.html", "2026 Valuation Challenge", "Valuation Analyst on the UMass Lowell team in the 2026 Business Valuation Challenge: discount rate, DCF, LBO and public comparables.",
          "Competition", "2026 Valuation Challenge", "Valuation Analyst. UMass Lowell team led by Professor Sangphil Kim. September to October 2026.",
          "We valued 100 percent of a $132MM revenue Gulf Coast engineering contractor, an owner operated S corporation, for an ESOP acquisition at fair market value. I owned the discount rate, the DCF, the LBO and the public comparables.",
          [("The competition", "A 25 minute recorded valuation, no questions allowed",
            P("Run out of Georgia State University. Round 1 is a recorded presentation of up to 25 minutes with no live questions; the top five teams go to the in person final. We submitted on October 19, 2026.",
              "With no question period, every judgment has to defend itself inside the video. Each of my four slides answers the question a judge would ask if they could.")),
           ("My four slides", "Risk, value, a buyer's check, and what public peers can and cannot tell you",
            bul(["<b>Discount rate.</b> What return does a buyer need to own this risk? I built the cost of capital in layers and landed at 16.8 percent.",
                 "<b>Discounted cash flow.</b> What are the cash flows worth at that rate? A five year forecast to 2031, tested two ways, growing forever at 2 to 3 percent or selling at 4.5 to 5.5 times EBITDA. The two methods landed within half a million dollars of each other.",
                 "<b>Leveraged buyout.</b> Could a real buyer pay that? I modeled a private equity purchase at 2.5 times EBITDA of debt, kept low because a bonded contractor cannot carry heavy leverage, and solved for the most a fund could pay at its target return. It landed close to the DCF, so the LBO became a floor and a check, with zero weight in the conclusion.",
                 "<b>Guideline public companies.</b> What do public peers tell you? Their risk, not their price. I used the peer set for beta only. Companies worth $4.7 billion to $16.8 billion with hundreds of projects and liquid stock say little about a control sale of a private contractor with two owners, so their multiples carried zero weight."])),
           ("The discount rate build", "Six inputs and one big judgment", wacc_html +
            '<ul class="figs"><li class="full light"><figure><a class="img" href="assets/figures/val_discount_rate.png"><img src="assets/figures/val_discount_rate.png" alt="Discount rate slide: cost of debt 5.93 percent after tax, cost of equity 17.06 percent, WACC 16.80 percent" loading="lazy"></a><figcaption><b>The slide as submitted</b>My discount rate page from the deck. The company, its figures and the conclusion stay off this site.</figcaption></figure></li></ul>' +
            P("The 7.06 percent size premium is worth about five turns of EBITDA. Without it the implied multiple goes from about 5 times to about 10, which is the whole gap between where public peers trade and where private contractors this size sell. That is why the public multiples got zero weight.")),
           ("Where I disagreed with management", "Growth, not margins",
            P("Management grew revenue 6.5 to 7.5 percent a year. The company had missed its own 2025 budget by 14 percent and new orders had been flat for two years. I accepted 2026 because backlog supported it, then faded growth to 2.5 percent by 2031. Every dollar between our value and management's case is that growth call, not margins. The DCF runs on a 6.5 percent mid cycle margin, a normal year rather than a good or bad one.")),
           ("What I would do differently", "Three things the judges could have pushed on",
            bul(["<b>Four betas is thin.</b> Four clean betas beat eleven noisy ones, but every reasonable change to the beta still kept the value inside our range, and I should have shown that range on the slide.",
                 "<b>The 10 year or the 20 year Treasury.</b> Kroll pairs its 5 percent premium with the 20 year yield, which was 4.65 percent. Using it would have raised the WACC to about 17.2 percent and cut the value by about $1.4 million, still inside the range. I used 4.2 percent and should have footnoted the choice.",
                 "<b>Bonding caps leverage harder than I modeled.</b> At 2.5 times EBITDA the contractor's tangible net worth goes negative, which a surety would not accept. A 1.5 times case changes the LBO ceiling by a few million and does not change the conclusion, but it is the more honest number."])),
           ("Process", "Three mock presentations and a content freeze",
            P("Three mocks between September 18 and early October, a content freeze on October 9, recording on October 10 and 11. My segment ran six minutes fifty in the second mock against a target of four and a half, so the last two weeks were cutting words, not adding analysis.",
              "The company and the data room are confidential, so the dollar figures stay off this page. The method and the judgment calls are mine."))], banner=("assets/banners/valuation.jpg", "The cost of capital build, from a 4.2 percent risk free rate to a 16.8 percent WACC. Every input here is already on the public slide."))
open(os.path.join(OUT, "trading.html"), "w", encoding="utf-8").write('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=bloomberg.html"><title>Bloomberg Global Trading Challenge | Anthony Ferriero</title><link rel="canonical" href="bloomberg.html"></head><body><p>Moved to <a href="bloomberg.html">Bloomberg at UMass Lowell</a>.</p></body></html>')
case_page("finance-society.html", "UML Finance Society", "President of the UML Finance Society since April 2026.",
          "Leadership", "UML Finance Society", "President. April 2026 to now.",
          "I lead a nine person executive board for a student finance club of over 500 members.",
          [("What changed", "500 members, a nine person board, and events people show up to",
            '<img class="logo" src="assets/umlfs-logo.svg" alt="UMLFS, UMass Lowell Finance Society" width="520" height="150">' +
            P("I took over in April 2026. Membership is up 200+ to over 500. The e-board is nine people and each of them owns something: events, merch, partnerships, the newsletter. My job is mostly picking the people and getting out of the way.")),
           ("This fall", "Six events in six weeks",
            bul(["<b>September 21.</b> From Gold to Tokens, with Professor Ravi Jain and the Donahue Center for Business Ethics. The history of money from Babylon to AI, Chipotle, open to every major.",
                 "<b>September 22.</b> Boston Fintech Week at the Federal Reserve Bank of Boston. Ten of us on the opening day, with a school shuttle I got the dean's office to pay for.",
                 "<b>September 25.</b> The Fintech That Thinks career summit at the Boston Fed, open to all finance students on a second bus.",
                 "<b>October 1.</b> Develop Your Corporate Financial Acumen with Kim Kinsley of Pratt &amp; Whitney, co-hosted with the DifferenceMaker Institute.",
                 "<b>October 28.</b> Link Up, a LinkedIn workshop in the Bloomberg Terminal room. Free headshots, a talk on how to set up a profile, then live reviews of members' profiles on the screen. Joint with the Real Estate Club.",
                 "<b>Fall.</b> The Bloomberg Global Trading Challenge, with practice time booked in the terminal room."])),
           ("What I am building for after me", "An analyst group the next board runs",
            P("A weekly market newsletter and a case every three weeks, run by the two youngest e-board members, not by me. Four new analysts. The top case team gets shouted out on LinkedIn. The point is to give members who want an e-board seat a way to earn one, and to make sure the club does not depend on whoever is president.")),
           ("Photos", "This fall so far",
            photos([
                ("fintech-rooftop", "The group on the roof of the Federal Reserve Bank of Boston on the opening day of Boston Fintech Week, September 22.", "wide"),
                ("fintech-rooftop-2", "Another rooftop shot from Boston Fintech Week.", "sq"),
                ("fs-group", "The group at a Finance Society event by the water.", "wide"),
                ("fintech-career-summit", "Crack the Fintech Career Code, the student panel at the Boston Fed.", "sq"),
                ("babylon-podium", "Opening the night. Babylon to blockchain in 75 minutes, with Chipotle.", "tall"),
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
            P("Working on getting UMass Lowell into the Mass Fintech Hub so the Boston Fintech Week tickets become a yearly thing. Reaching out to CFA Society Boston to get members into their events. Lining up alumni site visits, starting with a New York trip."))], banner=("assets/banners/d-finance-society.jpg", "The dated events of the fall, then the Trading Challenge running under all of them. Drawn from the list on this page."))
case_page("sales-team.html", "UML Intercollegiate Sales Team", "Captain of the UML Intercollegiate Sales Team since November 2025.",
          "Leadership", "Intercollegiate Sales Team", "Captain. November 2025 to now.",
          "Top four at a national competition. I captain the team and run prep on pitching and objections.",
          [("Results", "Where the team placed",
            bul(["Love's Travel Stops national sales competition, Oklahoma City. The team placed top four.",
                 "March 26, 2026. Fourth in Speed Sell at the Challenger Sales Institute invitational, with two UMass Lowell placings that day."])),
           ("What I run", "Prep and the sponsor list",
            P("I run prep on pitching and objection handling. I also keep the list of competitions and sponsors we bring to our advisors each year.")),
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
            '<div class="logo-row"><img src="assets/ccr-logo.png" alt="Commonwealth Capital Research logo"><p class="note" style="margin:0">Commonwealth Capital Research is a student run research group.</p></div>' +
            bul(["The newsletter. I write the rates and credit section. About 200 people subscribe.",
                 "A SpaceX IPO report, co-written with a friend from the group.",
                 "An oil market piece, in progress. It tracks how the Middle East risk premium faded through 2026."])),
           ("The curve", "What the rates section is about",
            '<figure class="banner"><img src="assets/banners/curve.jpg" alt="The Treasury curve at each year end since 2018 in grey and the latest curve in orange" loading="lazy"><figcaption>The Treasury curve at each year end since 2018, grey, and the latest, orange. FRED data.</figcaption></figure>' +
            P("The newsletter's rates section follows the shape of this curve and the credit spreads on top of it. The inversion from 2022 and the way it unwound is the story I have been writing for two years.")),
           ("Photos", "Fireside chat",
            photos([("ccr-elward", "With Nick Elward of Natixis after the Commonwealth Capital Research fireside chat.", "tall")]))], banner=("assets/banners/d-ccr-news.jpg", "The layout of the newsletter's rates and credit section. An illustration, not an issue."))
case_page("consulting.html", "Mill City Consulting", "Research and due diligence for a UMass Lowell student consulting client.",
          "Project", "Mill City Consulting", "Research and due diligence lead. UMass Lowell student consulting group.",
          "A six lane duckpin bowling alley that has been open since 1931, with new owners and no financial system.",
          [("The client", "Leagues, parties, and 1960s pinsetters",
            P("Two owners had just bought the place. Leagues were about 87 percent of revenue, parties 9, food and drink 4. Strengths: one of the last duckpin houses in the region, owners who do their own repairs, a real Facebook following. Weaknesses: fragile sixty year old machines, no website, no formal books.")),
           ("What we built", "Visibility first",
            bul(["An Excel financial tracker with a live profit and loss, so the owners could see the business for the first time.",
                 "A QR code payment setup, a website, new signage and a brand story.",
                 "An intro to the UML engineering department about the pinsetters."])),
           ("What I owned", "The question bank",
            P("My part was research and due diligence. I wrote the five section client question bank the group uses on new engagements: understanding the business, current operations, customers and market, pain points, and goals. I presented it to the next Mill City cohort in September 2026.")),
           ("Photos", "Presenting the work",
            photos([("class-presenting", "Presenting the research and due diligence template.", ""), ("class-team", "The team after the presentation.", "")]))], banner=("assets/banners/d-consulting.jpg", "Six duckpin lanes. A drawing, not the client's floor plan."))
case_page("education.html", "Education", "Business Administration at UMass Lowell, expected graduation May 2027.",
          "Education", "UMass Lowell", "Bachelor of Science in Business Administration. Expected May 2027.",
          "Concentrations in Finance and Marketing, minor in Quantitative Economics. GPA 3.6 out of 4.0.",
          [("Coursework", "Relevant classes", pills(["Financial Derivatives", "Financial Institutions and Markets", "Financial Statement Analysis"])),
           ("Certifications", "Credentials", pills(["Capital Markets and Securities Analyst, CMSA", "Bloomberg Finance Fundamentals", "Spreadsheet Analysis"]))], banner=("assets/banners/d-education.jpg", "Eight semesters, the seventh under way. Drawn, not a transcript."))
case_page("skills.html", "Skills", "Tools, models and data skills.",
          "Skills", "Tools and certifications", "Terminal, code, models, AI.",
          "What I use to read the bond market and to build and test the work on this site.",
          [("Technical", "Tools and data", pills(["Bloomberg Terminal", "BQL", "SRCH, YAS, DES, GC", "Refinitiv", "R", "Stata", "Excel", "DCF and LBO modeling", "SEC filings"])),
           ("Certifications", "Credentials", pills(["Capital Markets and Securities Analyst, CMSA", "Bloomberg Finance Fundamentals", "Spreadsheet Analysis"])),
           ("AI tools", "How I use them", pills(["Claude", "ChatGPT", "Microsoft Copilot", "Google Gemini"]) +
            P("I use Claude to help write and debug code and to screen first pass matches in the research. I test the results."))], banner=("assets/banners/skills.jpg", "The screens and tools behind the work on this site."))
case_page("contact.html", "Contact", "Contact Anthony Ferriero.", "Contact", "Get in touch", "Lowell, Massachusetts.",
          "The fastest way to reach me is email. I reply to every message about debt capital markets, syndicate, fixed income research or the tools on this site.",
          [("Where to find me", "Email first",
            '<div class="two"><div>' +
            '<div class="hero-cta" style="margin:0 0 18px"><a class="btn primary" href="mailto:%s">Email me <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a><a class="btn outline" href="%s" rel="noopener">LinkedIn</a><a class="btn outline" href="%s" rel="noopener">GitHub</a></div>' % (EMAIL, LINKEDIN, GITHUB) +
            '<p class="note"><a href="mailto:%s">%s</a><br>Lowell, Massachusetts. Boston and New York on short notice.</p>' % (EMAIL, EMAIL) +
            P("I am looking for a 2027 analyst seat in debt capital markets, syndicate or fixed income research, or an internship that leads there. I graduate in May 2027.",
              "If you run a desk and want to see the tender tracker or the dashboard on a real screen, I will bring a laptop.") + '</div>' +
            '<div><figure class="banner" style="aspect-ratio:4/3;margin:0"><img src="assets/photos/careers-stairs.jpg" alt="Anthony Ferriero on campus"><figcaption>On campus.</figcaption></figure></div></div>')], banner=("assets/banners/d-contact.jpg", "Lowell, with Boston and New York as rings. Schematic, not to scale."))
# projects hub page
case_page("projects.html", "Projects", "Research, tools and models, each with its error rates published.", "Projects", "Projects", "Five case files. Public data only.",
          "These are the parts of a syndicate desk's work that I can do with public data: a score for the new issue window, a tender offer tracker, a study of green bond pricing and five DCF models with a credit comparison.",
          [("Case files", "Research, tools and models", card_group(("Project",))),
           ("Competitions", "Where the models got tested", card_group(("Competition",)))], banner=("assets/banners/projects.jpg", "Investment grade spreads since October 2023, the backdrop every one of these tools reads. FRED data."))
# experience and leadership hub pages
case_page("experience.html", "Experience", "Roles, projects and competitions in order.", "Experience", "Experience", "Internship, campus roles, competitions.",
          "Everything in date order, newest first. Each entry opens its case file.",
          [("Timeline", "Roles, projects and competitions", tl)], banner=("assets/banners/d-experience.jpg", "Every role on the site as a bar, January 2024 to now."))
lead = card_group(("Leadership",))
case_page("leadership.html", "Leadership", "Finance Society and Sales Team leadership.", "Leadership", "Leadership", "Two teams at UMass Lowell.",
          "I run the Finance Society and captain the sales team.",
          [("Roles", "Finance Society and Sales Team", lead)], banner=("assets/banners/d-leadership.jpg", "Five hundred members, two hundred of them new, and a rank ladder. One dot is one member."))

open(os.path.join(OUT, "style.css"), "w", encoding="utf-8").write(CSS)
print("built", sorted(os.listdir(OUT)))
