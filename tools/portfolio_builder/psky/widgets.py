# Interactive widgets: DCF explorer, credit cushion, research power slider, day on the desk.
# Markup and behaviour only. Styling lives in styles/site.css.
import json as _json, os as _os
EXPLORER = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "explorer.json")))



def explorer_html():
    data = _json.dumps(EXPLORER)
    return f"""<div class="xp" id="xp">
  <div class="panel">
    <div class="seg" id="xp-seg" role="group" aria-label="Company"></div>
    <div class="ctl"><label>Cost of capital, WACC <b id="xp-w-v"></b></label><input type="range" id="xp-w" min="5" max="14" step="0.0001"><p class="hint" id="xp-w-h"></p></div>
    <div class="ctl"><label>Long term growth <b id="xp-g-v"></b></label><input type="range" id="xp-g" min="-3" max="5" step="0.1"><p class="hint" id="xp-g-h"></p></div>
    <div class="ctl"><label>Exit multiple, EV to EBITDA <b id="xp-m-v"></b></label><input type="range" id="xp-m" min="3" max="20" step="0.5"><p class="hint" id="xp-m-h"></p></div>
    <div class="ctl"><label>EBITDA against the base case <b id="xp-e-v"></b></label><input type="range" id="xp-e" min="-50" max="20" step="1"><p class="hint">Scales every year of cash flow and the terminal value. The credit view below uses the same miss.</p></div>
    <p class="hint"><button type="button" class="btn outline small" id="xp-reset">Reset to my base case</button></p>
  </div>
  <div class="panel">
    <div class="outs">
      <div class="out"><div class="n" id="xp-perp"></div><p>Value per share, perpetuity method</p></div>
      <div class="out"><div class="n" id="xp-exit"></div><p>Value per share, exit multiple method</p></div>
      <div class="out"><div class="n" id="xp-up"></div><p id="xp-up-p">Perpetuity value against the market price</p></div>
      <div class="out"><div class="n" id="xp-tv"></div><p>Share of value past the forecast</p></div>
      <div class="out"><div class="n" id="xp-lev"></div><p>Net debt to first year EBITDA</p></div>
      <div class="out"><div class="n" id="xp-cush"></div><p id="xp-cush-p">Equity left at today's multiple after the EBITDA change</p></div>
    </div>
    <div class="vbar"><div class="fill" id="xp-fill"></div><div class="mk" id="xp-mk"></div></div>
    <div class="vbar-lab"><span>$0</span><span id="xp-mkt"></span><span id="xp-max"></span></div>
    <p class="note">Same formulas as the Excel models: mid year discounting, a stub for the first year, the equity bridge off net debt and other claims. Skydance includes the warrant dilution above $12. The bear and bull scenarios in the models also change revenue and margins, which this slider does not.</p>
  </div>
</div>
<script>
(function(){{var D={data};var names=Object.keys(D);var cur=names[0];
var seg=document.getElementById('xp-seg');names.forEach(function(n){{var b=document.createElement('button');b.type='button';b.textContent=n;b.setAttribute('aria-pressed',n===cur);b.onclick=function(){{cur=n;load();}};seg.appendChild(b);}});
var W=document.getElementById('xp-w'),G=document.getElementById('xp-g'),M=document.getElementById('xp-m'),E=document.getElementById('xp-e');
function $(i){{return document.getElementById(i);}}
function money(x){{return (x<0?'-$':'$')+Math.abs(x).toFixed(2);}}
function load(){{var d=D[cur];W.value=(d.wacc*100).toFixed(4);G.value=(d.g*100).toFixed(1);M.value=d.mult;E.value=0;
seg.querySelectorAll('button').forEach(function(b){{b.setAttribute('aria-pressed',b.textContent===cur);}});
$('xp-w-h').textContent='My base case: '+(d.wacc*100).toFixed(1)+'%';$('xp-g-h').textContent='My base case: '+(d.g*100).toFixed(1)+'%';$('xp-m-h').textContent='My base case: '+d.mult.toFixed(1)+'x. Market pays '+d.mktmult.toFixed(1)+'x today';calc();}}
function calc(){{var d=D[cur];var w=W.value/100,g=G.value/100,m=parseFloat(M.value),e=1+E.value/100;
$('xp-w-v').textContent=(w*100).toFixed(1)+'%';$('xp-g-v').textContent=(g*100).toFixed(1)+'%';$('xp-m-v').textContent=m.toFixed(1)+'x';$('xp-e-v').textContent=(E.value>0?'+':'')+E.value+'%';
var pv=0;for(var i=0;i<d.cf.length;i++){{pv+=d.cf[i]*e/Math.pow(1+w,d.per[i]);}}
var df=Math.pow(1+w,d.n);var tvp=(w>g)?d.last*e*(1+g)/(w-g)/df:NaN;var tve=m*d.ebitdaT*e/df;
function px(ev){{var eq=ev-d.netdebt-d.nci;var sh=d.shares;var v=eq/sh;if(d.warrants&&v>12){{for(var k=0;k<3;k++){{var dil=d.warrants*(1-12/v);v=eq/(sh+dil);}}}}return v;}}
var vp=isNaN(tvp)?NaN:px(pv+tvp),ve=px(pv+tve);
var P=$('xp-perp'),X=$('xp-exit');P.textContent=isNaN(vp)?'growth above WACC':money(vp);P.className='n'+(vp<0?' neg':'');X.textContent=money(ve);X.className='n'+(ve<0?' neg':'');
var up=isNaN(vp)?NaN:(vp/d.price-1);$('xp-up').textContent=isNaN(up)?'n/a':((up>=0?'+':'')+(up*100).toFixed(0)+'%');$('xp-up').className='n'+(up<0?' neg':'');$('xp-up-p').textContent='Perpetuity value against the $'+d.price.toFixed(2)+' market price';
$('xp-tv').textContent=isNaN(tvp)?'n/a':(tvp/(pv+tvp)*100).toFixed(0)+'%';
var lev=d.netdebt/(d.ebitda1*e);$('xp-lev').textContent=lev.toFixed(1)+'x';$('xp-lev').className='n'+(lev>4?' neg':'');
var eqm=Math.max(0,d.ebitda1*e*d.mktmult-d.netdebt-d.nci),eq0=d.ebitda1*d.mktmult-d.netdebt-d.nci;var c=eq0>0?eqm/eq0:0;$('xp-cush').textContent=(c*100).toFixed(0)+'%';$('xp-cush').className='n'+(c<0.5?' neg':'');
var mx=Math.max(d.price*2.2,(isNaN(vp)?0:vp)*1.1,ve*1.1);$('xp-fill').style.width=Math.max(0,Math.min(100,(isNaN(vp)?ve:vp)/mx*100))+'%';$('xp-mk').style.left=(d.price/mx*100)+'%';$('xp-mkt').textContent='market $'+d.price.toFixed(2);$('xp-max').textContent='$'+mx.toFixed(0);}}
[W,G,M,E].forEach(function(r){{r.addEventListener('input',calc);}});$('xp-reset').onclick=load;load();}})();
</script>"""


POWER_HTML = """<div class="xp">
  <div class="panel">
    <div class="ctl"><label>Matched pairs in the sample <b id="pw-n-v"></b></label><input type="range" id="pw-n" min="33" max="1203" step="10" value="153"><p class="hint">I have 153. Each new pair is a terminal session and a twin search.</p></div>
    <div class="ctl"><label>Gap you want to be able to detect <b id="pw-t-v"></b></label><input type="range" id="pw-t" min="1" max="15" step="0.5" value="5"><p class="hint">My point estimate is 2.4 bps tighter.</p></div>
  </div>
  <div class="panel">
    <div class="outs">
      <div class="out"><div class="n" id="pw-mde"></div><p>Smallest gap this many pairs can detect at 80 percent power</p></div>
      <div class="out"><div class="n" id="pw-need"></div><p id="pw-need-p">Pairs needed to detect the gap you picked</p></div>
    </div>
    <p class="note" id="pw-note"></p>
  </div>
</div>
<script>
(function(){var N=document.getElementById('pw-n'),T=document.getElementById('pw-t');function $(i){return document.getElementById(i);}
function calc(){var n=+N.value,t=+T.value;var mde=6.6*Math.sqrt(153/n);var need=Math.ceil(153*Math.pow(6.6/t,2)/10)*10;
$('pw-n-v').textContent=n;$('pw-t-v').textContent=t.toFixed(1)+' bps';$('pw-mde').textContent=mde.toFixed(1)+' bps';$('pw-need').textContent=need.toLocaleString();
$('pw-note').textContent=(mde<=2.4?'At '+n+' pairs a 2.4 bps result would be detectable. ':'At '+n+' pairs a 2.4 bps gap is inside the noise, which is where the paper sits today. ')+'The scaling is the standard error falling with the square root of the sample size, anchored on the 6.6 bps minimum detectable effect at 153 pairs.';}
[N,T].forEach(function(r){r.addEventListener('input',calc);});calc();})();
</script>"""


DAY = [
    ("7:00", "The wire", "Read what printed overnight and where the futures and spreads sit. Update the volume tally against the Street's estimate for the week and the month so the morning wire has its headline number.", "Tools: the daily tally, the window score."),
    ("8:30", "Announcements", "Deals are announced with initial price talk. I log the issuer, size, tenor, leads and starting talk for each one before the first book update, because the rest of the day is measured from that talk.", "Tools: the deal log, the tenor screens for a first comp."),
    ("10:00", "The book chase", "Call and message desks at 30 plus banks for book sizes. There are fifteen to twenty deals, each with three or four updates a day. Clean what comes back and publish it before the next revision.", "This is the relationship work. No desk has to share the number."),
    ("12:00", "Guidance", "Talk tightens into guidance. Track the move in basis points on every tranche and the book against the deal size. This is where concession starts to show."),
    ("14:00", "Launch", "Final terms and final book sizes. Publish, then compare the print against every comparable deal since 2022 on the tenor screens. Flag anything that looks wrong to the check sheet."),
    ("16:30", "Pricing and the tally", "The day's investment grade prints go into one table with issuer, rating, size, tenor, final book, leads, talk, print, the move from talk to print and identifiers. The headline is the day's volume.", "Feeds tomorrow's 7:00 wire."),
    ("17:30", "Liability management", "Tenders, exchanges and consents arrive after the close. Write the headline and log the terms and caps. I covered twenty five plus of these over nine months.", "This is where the Tender Tracker came from."),
]


def day_html():
    items = "".join('<li><button type="button" role="tab" aria-selected="%s" data-i="%d">%s &nbsp;%s</button></li>' % ("true" if i == 0 else "false", i, t, h) for i, (t, h, *_) in enumerate(DAY))
    data = _json.dumps([{"t": t, "h": h, "p": p, "s": (s[0] if s else "")} for t, h, p, *s in DAY])
    return f"""<div class="day" id="day"><ol role="tablist">{items}</ol><div class="panel" role="tabpanel"><h3 id="day-h"></h3><p id="day-p"></p><small id="day-s"></small></div></div>
<script>(function(){{var D={data};var bs=document.querySelectorAll('#day button'),P=document.querySelector('#day .panel');function show(i){{bs.forEach(function(b,j){{b.setAttribute('aria-selected',i===j);}});document.getElementById('day-h').textContent=D[i].t+' '+D[i].h;document.getElementById('day-p').textContent=D[i].p;document.getElementById('day-s').textContent=D[i].s;P.classList.remove('swap');void P.offsetWidth;P.classList.add('swap');}}
bs.forEach(function(b){{b.addEventListener('click',function(){{show(+b.dataset.i);}});}});show(0);}})();</script>"""
