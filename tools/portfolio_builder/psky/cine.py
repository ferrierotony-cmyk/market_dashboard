"""Cinematic layer: full bleed hero and page heads with slow camera moves, parallax photo bands,
word by word title reveals, film grain, a cursor light, a marquee and page transitions.
Everything switches off under prefers-reduced-motion."""
import html as _html


def _e(s):
    return _html.escape(s, quote=True)


def split(text, dot=True):
    """Wrap each word of a title so it can rise into view one at a time. The orange dot rides the last word."""
    words = text.split()
    out = []
    for i, w in enumerate(words):
        inner = _e(w) + ("<i>.</i>" if dot and i == len(words) - 1 else "")
        out.append('<span class="w"><span style="animation-delay:%dms">%s</span></span>' % (120 + i * 90, inner))
    return " ".join(out)


def band(photo, big, cap, pos="center 35%"):
    """A full bleed photo band with one big line over it. Parallax on scroll."""
    return ('<section class="band" aria-label="%s"><div class="band-bg" data-px><img src="%s" alt="" style="object-position:%s"></div>'
            '<div class="wrap band-in"><p class="big">%s</p><p class="band-cap">%s</p></div></section>' % (_e(cap), photo if "/" in photo else "assets/photos/%s.jpg" % photo, pos, _e(big), _e(cap)))


def marquee(items):
    inner = "".join('<span><b>%s</b> %s</span>' % (_e(n), _e(t)) for n, t in items)
    return '<div class="marq" aria-hidden="true"><div class="marq-in">%s%s</div></div>' % (inner, inner)


AI_DIR = None  # set by the build: folder that may hold assets/ai/<slug>.jpg
TINTS = {"Role": "#DCEBFA", "Project": "#FFE8D6", "Leadership": "#FFF1C9", "Education": "#E3EFE4", "Competition": "#FFE8D6", "Skills": "#E3EFE4"}


def tint_for(kind):
    return TINTS.get(kind, "#FFF1C9")


def ai_image(img_src):
    """Path of an AI generated image for this page, if one was dropped into assets/ai. Slug comes from the old banner name."""
    import os
    if not AI_DIR:
        return None
    slug = os.path.basename(img_src).replace(".jpg", "").replace("d-", "", 1).replace("-m", "")
    rel = "assets/ai/%s.jpg" % slug
    return rel if os.path.exists(os.path.join(AI_DIR, rel)) else None


def cine_head(crumb_html, kind, h1, meta, img_src, cap, pos="center 30%"):
    """Case page head: a calm tinted block with the title. A chart or real photo sits under it as a framed figure.
    The drawn banners are retired. An AI generated image shows only if one exists, and says so in its caption."""
    fig = ""
    if "/d-" in img_src:
        ai = ai_image(img_src)
        if ai:
            fig = (f'<figure class="chead-fig wrap"><img src="{ai}" alt="" fetchpriority="high" style="object-position:{pos}">'
                   f'<figcaption>AI generated image, not a photo of the real place.</figcaption></figure>')
    else:
        fig = (f'<figure class="chead-fig wrap"><img src="{img_src}" alt="" fetchpriority="high" style="object-position:{pos}">'
               f'<figcaption>{_e(cap)}</figcaption></figure>')
    return (f'<div class="chead" style="--tint:{tint_for(kind)}">'
            f'<div class="wrap chead-in">{crumb_html}<p class="eyebrow">{_e(kind)}</p><h1>{split(h1)}</h1><p class="meta">{_e(meta)}</p></div>'
            f'{fig}</div>')


CINE_CSS = r"""
/* ---------- cinematic layer ---------- */
.js body { animation: pagein .7s ease both; }
body.leaving { opacity: 0; transition: opacity .22s ease; }
@keyframes pagein { from { opacity: 0; } to { opacity: 1; } }
.grain { position: fixed; inset: -50%; width: 200%; height: 200%; pointer-events: none; z-index: 40; opacity: .055;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .6 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  animation: grain 1.2s steps(6) infinite; }
@keyframes grain { 0% { transform: translate(0,0);} 20% { transform: translate(-4%,3%);} 40% { transform: translate(3%,-5%);} 60% { transform: translate(-6%,-2%);} 80% { transform: translate(5%,6%);} 100% { transform: translate(-2%,4%);} }
.glow { position: fixed; left: 0; top: 0; width: 720px; height: 720px; margin: -360px 0 0 -360px; pointer-events: none; z-index: 0; border-radius: 50%;
  background: radial-gradient(circle, rgba(242,106,27,.09), rgba(242,106,27,.03) 40%, transparent 70%); opacity: 0; transition: opacity .6s; will-change: transform; }
.glow.on { opacity: 1; }
@media (hover: none), (pointer: coarse) { .glow { display: none; } }

/* header goes clear over the hero, then solidifies */
body.home .site-head, body.hashead .site-head { background: transparent; border-bottom-color: transparent; transition: background .35s, border-color .35s; }
html.scrolled body.home .site-head, html.scrolled body.hashead .site-head { background: rgba(11,11,12,.88); border-bottom-color: var(--line); }
body.home .nav.open, body.hashead .nav.open { background: var(--bg2); }

/* word by word title reveal */
.w { display: inline-block; overflow: hidden; vertical-align: bottom; padding-bottom: .14em; margin-bottom: -.14em; }
.w > span { display: inline-block; transform: translateY(112%); animation: wup 1s cubic-bezier(.2,.75,.15,1) forwards; will-change: transform; }
@keyframes wup { to { transform: none; } }

/* home hero */
.cine { position: relative; min-height: calc(100svh - 62px); margin-top: -62px; padding-top: 62px; display: flex; align-items: center; overflow: hidden; isolation: isolate; }
.cine-bg { position: absolute; inset: -6% 0; z-index: -1; }
.cine-bg img { width: 135%; height: 100%; object-fit: cover; object-position: 0 45%; display: block; filter: saturate(.75) brightness(.8); transform-origin: 60% 45%; animation: kb 26s ease-in-out infinite alternate; }
.cine-bg::after { content: ""; position: absolute; inset: 0;
  background: linear-gradient(90deg, rgba(11,11,12,.97) 0%, rgba(11,11,12,.9) 34%, rgba(11,11,12,.5) 66%, rgba(11,11,12,.3) 100%), linear-gradient(180deg, rgba(11,11,12,.35) 0%, transparent 30%, transparent 60%, var(--bg) 100%); }
@keyframes kb { from { transform: scale(1.04) translate(0,0); } to { transform: scale(1.16) translate(-1.5%, 1.5%); } }
.cine-in { width: 100%; padding-top: 48px; padding-bottom: 96px; }
.cine-in > * { max-width: 620px; }
.byline { display: flex; align-items: center; gap: 12px; margin: 0 0 22px; }
.byline .pic { width: 46px; height: 46px; border-radius: 50%; border: 2px solid var(--amber); object-fit: cover; object-position: center top; background: #fff; box-shadow: 0 0 0 4px rgba(242,106,27,.18); }
.byline .badge { margin: 0; }
.cine h1 { font-size: clamp(3.1rem, 8vw, 6.4rem); line-height: .95; letter-spacing: -0.045em; font-weight: 800; text-shadow: 0 10px 40px rgba(0,0,0,.6); }
.kick { font-family: var(--display); font-weight: 700; font-size: clamp(1.25rem, 2.3vw, 1.75rem); line-height: 1.2; letter-spacing: -0.02em; margin: 22px 0 0; color: var(--ink); opacity: 0; animation: fadeup 1s .55s cubic-bezier(.2,.75,.15,1) forwards; }
.cine .tag { opacity: 0; animation: fadeup 1s .7s cubic-bezier(.2,.75,.15,1) forwards; margin-top: 14px; }
.cine .hero-cta { opacity: 0; animation: fadeup 1s .85s cubic-bezier(.2,.75,.15,1) forwards; }
.cine .contact-row { opacity: 0; animation: fadeup 1s 1s cubic-bezier(.2,.75,.15,1) forwards; }
@keyframes fadeup { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
.cine-cap { position: absolute; right: max(22px, env(safe-area-inset-right, 0px)); bottom: 18px; margin: 0; font-family: var(--mono); font-size: 12px; color: var(--muted); max-width: 46ch; text-align: right; opacity: 0; animation: fadeup 1s 1.3s forwards; }
.cue { position: absolute; left: max(22px, env(safe-area-inset-left, 0px)); bottom: 18px; display: flex; align-items: center; gap: 10px; font-family: var(--mono); font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); text-decoration: none; opacity: 0; animation: fadeup 1s 1.4s forwards; }
.cue::before { content: ""; width: 44px; height: 1px; background: var(--amber); transform-origin: left; animation: cue 1.8s ease-in-out infinite; }
@keyframes cue { 0%, 100% { transform: scaleX(.3); opacity: .5; } 50% { transform: scaleX(1); opacity: 1; } }
@media (max-width: 760px) {
  .cine { min-height: 100svh; align-items: flex-end; }
  .cine-bg img { width: 100%; height: 150%; position: absolute; top: -45%; object-position: 60% 0; transform-origin: 60% 30%; }
  .cine-bg::after { background: linear-gradient(180deg, rgba(11,11,12,.5) 0%, rgba(11,11,12,.15) 25%, rgba(11,11,12,.75) 48%, rgba(11,11,12,.97) 68%, var(--bg) 100%); }
  .cine-in { padding-top: 46svh; padding-bottom: 86px; }
  .cine h1 { text-shadow: 0 6px 30px rgba(0,0,0,.8); }
  .cine-cap { display: none; }
  .cue { bottom: 16px; }
}

/* marquee */
.marq { overflow: hidden; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); background: #0e0e10; font-family: var(--mono); font-size: 13.5px; color: var(--muted); white-space: nowrap; position: relative; z-index: 1; }
.marq-in { display: inline-block; padding: 12px 0; animation: marq 46s linear infinite; }
.marq:hover .marq-in { animation-play-state: paused; }
.marq-in span { display: inline-block; margin: 0 26px; }
.marq-in span::after { content: "\25C6"; margin-left: 52px; color: var(--amber); font-size: 8px; vertical-align: middle; opacity: .8; }
.marq-in b { color: var(--amber); font-weight: 500; }
@keyframes marq { to { transform: translateX(-50%); } }

/* photo bands */
.band { position: relative; min-height: 66vh; display: flex; align-items: flex-end; overflow: hidden; isolation: isolate; margin: 40px 0 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.band-bg { position: absolute; left: 0; right: 0; top: -14%; bottom: -14%; z-index: -1; will-change: transform; }
.band-bg img { width: 100%; height: 100%; object-fit: cover; display: block; }
.band-bg::after { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, var(--bg) 0%, rgba(11,11,12,.15) 22%, rgba(11,11,12,.3) 55%, rgba(11,11,12,.9) 85%, var(--bg) 100%); }
.band-in { padding-top: 120px; padding-bottom: 48px; }
.big { font-family: var(--display); font-weight: 800; font-size: clamp(1.9rem, 4.6vw, 3.6rem); line-height: 1.02; letter-spacing: -0.035em; max-width: 18ch; margin: 0; text-shadow: 0 10px 40px rgba(0,0,0,.7); }
.big.rv { transform: translateY(28px); } .big.rv.in { transform: none; }
.band-cap { font-family: var(--mono); font-size: 12.5px; color: var(--muted); margin: 18px 0 0; }
@media (max-width: 760px) { .band { min-height: 52vh; } }

/* case page heads */
.chead { position: relative; min-height: min(64vh, 660px); display: flex; align-items: flex-end; overflow: hidden; isolation: isolate; margin-top: -62px; padding-top: 62px; border-bottom: 1px solid var(--line); }
.chead-bg { position: absolute; left: 0; right: 0; top: -12%; bottom: -12%; z-index: -1; will-change: transform; }
.chead-bg picture { display: block; width: 100%; height: 100%; }
.chead-bg img { width: 100%; height: 100%; object-fit: cover; display: block; filter: saturate(.8) brightness(.78); transform-origin: 50% 40%; animation: kb 28s ease-in-out infinite alternate; }
.chead-bg::after { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(11,11,12,.55) 0%, rgba(11,11,12,.15) 30%, rgba(11,11,12,.55) 60%, rgba(11,11,12,.96) 92%, var(--bg) 100%); }
.chead-in { width: 100%; padding-top: 110px; padding-bottom: 34px; }
.chead .crumb { margin-bottom: 14px; }
.chead .eyebrow { opacity: 0; animation: fadeup .9s .25s forwards; }
.chead h1 { font-size: clamp(2.4rem, 6vw, 4.6rem); line-height: .98; letter-spacing: -0.04em; text-shadow: 0 10px 40px rgba(0,0,0,.7); max-width: 20ch; }
.chead .meta { opacity: 0; animation: fadeup .9s .7s forwards; }
.chead-cap { position: absolute; right: max(22px, env(safe-area-inset-right, 0px)); bottom: 12px; margin: 0; font-family: var(--mono); font-size: 11.5px; color: var(--muted); max-width: 44ch; text-align: right; opacity: 0; animation: fadeup 1s 1.1s forwards; }
.lede-wrap { padding-top: 30px; padding-bottom: 8px; }
@media (max-width: 760px) { .chead { min-height: 78svh; flex-direction: column; justify-content: flex-end; } .chead-in { padding-top: 140px; padding-bottom: 46px; } .chead-cap { position: static; text-align: left; padding: 0 22px 14px; max-width: none; } }
.phead { position: relative; overflow: hidden; }
.phead::before { content: ""; position: absolute; inset: 0; z-index: -1; background: radial-gradient(700px 320px at 20% 0%, rgba(242,106,27,.13), transparent 70%); }
.phead h1 { font-size: clamp(2.4rem, 6vw, 4.6rem); line-height: .98; letter-spacing: -0.04em; }
.phead .eyebrow { opacity: 0; animation: fadeup .9s .25s forwards; }
.phead .meta, .phead .lede { opacity: 0; animation: fadeup .9s .7s forwards; }

/* chapters */
body { counter-reset: sec; }
.section { counter-increment: sec; }
.label { display: flex; align-items: center; gap: 12px; }
.label::before { content: counter(sec, decimal-leading-zero); color: var(--muted); font-size: 12.5px; letter-spacing: .08em; opacity: .75; }
.label::after { content: ""; display: block; width: 0; height: 1px; background: var(--amber); transition: width .9s cubic-bezier(.2,.75,.15,1) .15s; }
.label.in::after, .label.rv.in::after { width: 48px; }
h2.rv { transform: translateY(22px); filter: blur(6px); transition: opacity .9s ease, transform .9s cubic-bezier(.2,.75,.15,1), filter .9s ease; }
h2.rv.in { filter: blur(0); }
.rv { transform: translateY(22px); transition: opacity .85s ease, transform .85s cubic-bezier(.2,.75,.15,1); }
.mosaic li.rv { clip-path: inset(0 100% 0 0); transform: none; transition: clip-path .9s cubic-bezier(.2,.75,.15,1), opacity .6s; }
.mosaic li.rv.in { clip-path: inset(0 0 0 0); }
.photos li.rv, .figs li.rv { transform: translateY(26px) scale(.985); }
.photos li.rv.in, .figs li.rv.in { transform: none; }

/* cards: light sweep and tilt */
.card { overflow: hidden; transform-style: preserve-3d; }
.card::before { content: ""; position: absolute; inset: 0; z-index: 2; pointer-events: none; background: linear-gradient(115deg, transparent 35%, rgba(255,255,255,.07) 48%, transparent 62%); transform: translateX(-110%); transition: transform .8s cubic-bezier(.2,.75,.15,1); }
.card:hover::before { transform: translateX(110%); }
.card .thumb { position: relative; }
.card .thumb::after { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, transparent 50%, rgba(11,11,12,.7)); }
.stat { transform-style: preserve-3d; }

/* timeline draws itself */
.tl { position: relative; }
.tl::before { content: ""; position: absolute; left: -2px; top: 0; width: 2px; height: var(--fill, 0%); background: var(--amber); transition: height .2s linear; }

/* reduced motion switches the whole layer off */
@media (prefers-reduced-motion: reduce) {
  .grain, .glow, .cue { display: none; }
  .js body { animation: none; }
  .w > span, .kick, .cine .tag, .cine .hero-cta, .cine .contact-row, .cine-cap, .chead .eyebrow, .chead .meta, .chead-cap, .phead .eyebrow, .phead .meta, .phead .lede { animation: none; opacity: 1; transform: none; }
  .cine-bg img, .chead-bg img { animation: none; }
  .marq-in { animation: none; }
  .band-bg, .chead-bg { transform: none !important; }
  h2.rv { filter: none; }
  .mosaic li.rv { clip-path: none; }
  .label::after { width: 48px; }
}
"""

CINE_JS = r"""
(function(){var H=document.documentElement;if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
var g=document.createElement('div');g.className='grain';g.setAttribute('aria-hidden','true');document.body.appendChild(g);
if(window.matchMedia('(hover: hover) and (pointer: fine)').matches){var gl=document.createElement('div');gl.className='glow';gl.setAttribute('aria-hidden','true');document.body.appendChild(gl);var gx=0,gy=0,gr=false;
window.addEventListener('pointermove',function(ev){gx=ev.clientX;gy=ev.clientY;gl.classList.add('on');if(!gr){gr=true;requestAnimationFrame(function(){gl.style.transform='translate('+gx+'px,'+gy+'px)';gr=false;});}},{passive:true});
document.addEventListener('pointerleave',function(){gl.classList.remove('on');});
document.querySelectorAll('.card, .stat').forEach(function(c){c.addEventListener('pointermove',function(ev){var r=c.getBoundingClientRect();var dx=(ev.clientX-r.left)/r.width-.5,dy=(ev.clientY-r.top)/r.height-.5;c.style.transform='perspective(900px) rotateX('+(-dy*7).toFixed(2)+'deg) rotateY('+(dx*7).toFixed(2)+'deg) translateY(-3px)';});
c.addEventListener('pointerleave',function(){c.style.transform='';});});}
var px=[].slice.call(document.querySelectorAll('[data-px]')),tl=document.querySelector('.tl'),tick=false;
function run(){tick=false;var y=window.scrollY||window.pageYOffset,vh=window.innerHeight;if(y>40)H.classList.add('scrolled');else H.classList.remove('scrolled');
px.forEach(function(el){var p=el.parentNode,r=p.getBoundingClientRect();if(r.bottom<0||r.top>vh)return;var k=(r.top+r.height/2-vh/2)/vh;el.style.transform='translateY('+(k*-9).toFixed(2)+'%)';});
if(tl){var r=tl.getBoundingClientRect();var f=Math.max(0,Math.min(100,(vh*0.75-r.top)/r.height*100));tl.style.setProperty('--fill',f+'%');}}
window.addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(run);}},{passive:true});window.addEventListener('resize',run);run();
document.addEventListener('click',function(ev){var a=ev.target.closest&&ev.target.closest('a[href]');if(!a||ev.defaultPrevented||ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey||ev.button!==0)return;
var h=a.getAttribute('href');if(!h||h.charAt(0)==='#'||/^(https?:|mailto:|tel:)/i.test(h)||a.target||a.hasAttribute('download')||!/\.html(#.*)?$/.test(h)||h.indexOf('#')>=0)return;
ev.preventDefault();document.body.classList.add('leaving');setTimeout(function(){location.href=h;},200);});
window.addEventListener('pageshow',function(ev){if(ev.persisted)document.body.classList.remove('leaving');});})();
"""
