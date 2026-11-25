/* Live numbers for the portfolio pages. Three feeds: quotes when the page opens, a daily feed, and the dashboard snapshot.
   Every page is complete without this file. If a feed is down the strip stays hidden and the dated numbers stand.
   Feed text is only ever written with textContent, and only sec.gov links are followed. */
(function () {
  'use strict';
  var local = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
  var API = local ? '/api/quotes' : 'https://anthonyferriero.vercel.app/api/quotes';
  var FEED = local ? '/live.json' : 'https://raw.githubusercontent.com/ferrierotony-cmyk/market_dashboard/live-results/live.json';
  var SNAP = 'https://ferrierotony-cmyk.github.io/market_dashboard/market_snapshot.json';
  var STRIPS = [].slice.call(document.querySelectorAll('[data-live]'));
  if (!STRIPS.length || !window.fetch) return;

  function load(url) {
    var ctl = window.AbortController ? new AbortController() : null, t = setTimeout(function () { if (ctl) ctl.abort(); }, 12000);
    return fetch(url, { signal: ctl ? ctl.signal : undefined }).then(function (r) { clearTimeout(t); if (!r.ok) throw 0; return r.json(); }).catch(function () { clearTimeout(t); return null; });
  }
  function ok(x) { return typeof x === 'number' && isFinite(x); }
  function money(x) { return (x < 0 ? '-$' : '$') + Math.abs(x).toFixed(2); }
  function pct(x, d, sign) { return (sign && x > 0 ? '+' : '') + (x * 100).toFixed(d) + '%'; }
  function el(tag, text, cls) { var e = document.createElement(tag); if (text != null) e.textContent = text; if (cls) e.className = cls; return e; }
  function svg(tag, attrs, cls) { var e = document.createElementNS('http://www.w3.org/2000/svg', tag); Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); }); if (cls) e.setAttribute('class', cls); return e; }
  // a date alone prints as a date. A time prints in New York time.
  function when(iso) {
    if (!iso) return '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) return new Date(iso + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    var d = new Date(iso); if (isNaN(d)) return '';
    return d.toLocaleString('en-US', { timeZone: 'America/New_York', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) + ' ET';
  }
  function long(iso) { return new Date(iso + 'T12:00:00').toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }); }
  function days(iso) { return (Date.now() - new Date(iso.length === 10 ? iso + 'T21:00:00Z' : iso)) / 864e5; }
  function cell(label, value, small, cls) { var li = el('li', label); li.appendChild(el('b', value, cls || '')); li.appendChild(el('small', small || '')); return li; }
  function fill(box, cells, stamp) {
    cells = cells.filter(Boolean); if (!cells.length) return false;
    var ul = box.querySelector('ul'); ul.textContent = ''; cells.forEach(function (c) { ul.appendChild(c); });
    var w = box.querySelector('.live-when'); if (w) w.textContent = stamp || '';
    box.classList.add('on'); return true;
  }

  // ---- the models: same formulas as the workbooks and the calculator
  var M = {}; try { M = JSON.parse(document.getElementById('model-data').textContent); } catch (e) {}
  function priceOf(co, Q) {
    var t = { Skydance: 'SKYD', Netflix: 'NFLX', Disney: 'DIS', Comcast: 'CMCSA' }[co];
    if (t) return Q[t] ? { price: Q[t].price, prev: Q[t].prev, time: Q[t].time } : null;
    if (co === 'Fox' && Q.FOXA && Q.FOX) {
      var a = 349.95, b = 220.25, mix = function (x, y) { return (x * a + y * b) / (a + b); };
      return { price: mix(Q.FOXA.price, Q.FOX.price), prev: Q.FOXA.prev && Q.FOX.prev ? mix(Q.FOXA.prev, Q.FOX.prev) : null, time: Q.FOXA.time };
    }
    return null;
  }
  function value(d, price) {
    var w = d.wacc, pv = 0, i; for (i = 0; i < d.cf.length; i++) pv += d.cf[i] / Math.pow(1 + w, d.per[i]);
    var df = Math.pow(1 + w, d.n);
    function per(ev) { var eq = ev - d.netdebt - d.nci, v = eq / d.shares; if (d.warrants && v > 12) for (var k = 0; k < 3; k++) v = eq / (d.shares + d.warrants * (1 - 12 / v)); return v; }
    var ev = price * d.shares + d.netdebt + d.nci, tv = (ev - pv) * df;
    return { perp: per(pv + d.last * (1 + d.g) / (w - d.g) / df), exit: per(pv + d.mult * d.ebitdaT / df), g: (tv * w - d.last) / (tv + d.last), mult: tv / d.ebitdaT, ev: ev / d.ebitda1, miss: -price * d.shares / ev, ltv: d.netdebt / ev };
  }
  window.liveModel = { value: value, priceOf: priceOf };

  function modelStrip(box, Q) {
    var co = box.getAttribute('data-co'), d = M[co], p = priceOf(co, Q); if (!d || !p || !ok(p.price)) return;
    var v = value(d, p.price), day = p.prev ? pct(p.price / p.prev - 1, 1, true) + ' today' : '';
    fill(box, [cell(co === 'Fox' ? 'Price, both classes' : 'Price', money(p.price), day), cell('Perpetuity value', money(v.perp), pct(v.perp / p.price - 1, 0, true) + ' to the price'), cell('Exit value', money(v.exit), pct(v.exit / p.price - 1, 0, true) + ' to the price'),
      cell('Growth it implies', pct(v.g, 1), 'forever'), cell('EV to EBITDA', v.ev.toFixed(1) + 'x', 'first forecast year'), cell('Miss to zero', pct(v.miss, 0), 'of EBITDA')], when(p.time));
  }
  function fiveStrip(box, Q) {
    var last = '', cells = Object.keys(M).map(function (co) { var p = priceOf(co, Q); if (!p) return null; last = p.time > last ? p.time : last; var v = value(M[co], p.price); return cell(co, money(p.price), pct(v.perp / p.price - 1, 0, true) + ' and ' + pct(v.exit / p.price - 1, 0, true)); });
    fill(box, cells, when(last));
  }
  function explorer(Q) {
    if (!window.xpModels || !window.xpLoad) return;
    Object.keys(window.xpModels).forEach(function (co) { var d = window.xpModels[co], p = priceOf(co, Q); if (!p) return; d.price = p.price; d.mktmult = (p.price * d.shares + d.netdebt + d.nci) / d.ebitda1; });
    window.xpLoad();
  }
  function flags(sec) {
    [].forEach.call(document.querySelectorAll('[data-flag]'), function (n) {
      var m = sec && sec.data && sec.data[n.getAttribute('data-flag')]; if (!m) return;
      var big = m.new.filter(function (f) { return f.big; })[0] || m.new[0];
      var note = days(sec.built) > 4 ? ' Last checked ' + when(sec.built) + '.' : '';
      if (!big) { n.textContent = 'No new filing since the model of ' + long(m.model_date) + '.' + note; return; }
      n.textContent = 'This model is older than a filing. ';
      var a = el('a', big.form + ', ' + big.what + ', filed ' + long(big.filed)); if (/^https:\/\/www\.sec\.gov\//.test(big.url)) { a.href = big.url; a.rel = 'noopener'; }
      n.appendChild(a); n.appendChild(document.createTextNode('.' + note)); n.classList.add('warn');
    });
  }

  // ---- the tape
  function find(o, k) { return o && o[k]; }
  function tape(box, Q, F, S) {
    var c = [], s = S || {}, sf = s.fred || {}, age = s.built_at ? when(String(s.built_at).slice(0, 19).replace(' ', 'T') + 'Z') : '';
    if (s.window) { var w = String(s.window); c.push(cell('New issue window', w, age, /open/i.test(w) ? 'good' : /closed|shut|challeng/i.test(w) ? 'bad' : 'warn')); }
    if (s.health && s.health.score != null) c.push(cell('Market health', s.health.score, s.health.label || ''));
    var t = Q['^TNX'], fr = function (k, sk) { return find(F, k) || (find(sf, sk || k) && find(sf, sk || k).last != null ? { value: find(sf, k).last, w1: find(sf, k).w1, date: find(sf, k).date, snap: true } : null); };
    var d10 = fr('DGS10');
    if (t && t.price > 1 && t.price < 12) c.push(cell('UST 10Y', t.price.toFixed(2) + '%', when(t.time))); else if (d10) c.push(cell('UST 10Y', d10.value.toFixed(2) + '%', when(d10.date)));
    [['IG OAS', 'BAMLC0A0CM'], ['HY OAS', 'BAMLH0A0HYM2']].forEach(function (p) {
      var x = fr(p[1]); if (!x) return; var k = x.snap ? 1 : 100;
      c.push(cell(p[0], (x.value * k).toFixed(0) + ' bp', '1w ' + (x.w1 >= 0 ? '+' : '') + (x.w1 * k).toFixed(0) + ', ' + when(x.date)));
    });
    [['VIX', '^VIX', 1], ['MOVE', '^MOVE', 0]].forEach(function (p) {
      var x = Q[p[1]], y = find(s.yahoo, p[1]);
      if (x) c.push(cell(p[0], x.price.toFixed(p[2]), when(x.time))); else if (y && y.last != null) c.push(cell(p[0], Number(y.last).toFixed(p[2]), age));
    });
    if (c.length > 2) fill(box, c, '');
  }

  // ---- the daily feed
  function tender(box, s) {
    var d = s.data, f = function (x) { return String(x); };
    fill(box, [cell('Offers open', f(d.open), 'of ' + d.offers + ' tracked'), cell('Launches', f(d.launches), 'since ' + when(d.from)), cell('Fast kind', f(d.fast), 'of ' + d.dated + ' dated SEC launches'), cell('Slow kind', f(d.slow), 'with an early deadline'), cell('Changed', f(d.changed), 'extended or amended')], 'through ' + when(d.through));
  }
  // the banner redraws itself from the feed, so the picture is never older than the tracker
  function bars(box, s) {
    var fig = document.querySelector('.page-fig'), img = fig && fig.querySelector('img'), cap = fig && fig.querySelector('figcaption'); if (!img) return;
    var c = s.data.chart, W = 1800, H = 773, floor = H, top = H * .74, side = 54, bw = (W - 2 * side) / c.length, mx = Math.max.apply(null, c.map(function (r) { return r[1] + r[2]; })) || 1;
    var g = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'Filings and releases the tracker read each weekday from ' + long(s.data.from) + ' to ' + long(s.data.through) }, 'spark stage');
    g.appendChild(svg('rect', { x: 0, y: 0, width: W, height: H }, 'back'));
    c.forEach(function (r, i) {
      var a = r[1] / mx * top, b = r[2] / mx * top, x = side + i * bw + bw * .14, w = bw * .72, n = svg('g'), ti = svg('title');
      ti.textContent = when(r[0]) + ': ' + r[1] + ' offer steps, ' + r[2] + ' other'; n.appendChild(ti); n.appendChild(svg('rect', { x: side + i * bw, y: 0, width: bw, height: H }, 'hit'));
      if (b) n.appendChild(svg('rect', { x: x, y: floor - a - b, width: w, height: b }, 'other')); if (a) n.appendChild(svg('rect', { x: x, y: floor - a, width: w, height: a }, 'step')); g.appendChild(n);
    });
    img.parentNode.replaceChild(g, img);
    if (cap) cap.textContent = 'Filings and releases the tracker read, by weekday, ' + long(s.data.from) + ' to ' + long(s.data.through) + '. Orange is a step in a tender or exchange offer, grey is everything else.';
  }
  function line(box, s) {
    var c = s.data.series, W = 1000, H = 260, v = c.map(function (r) { return r[1]; }), lo = Math.min.apply(null, v), hi = Math.max.apply(null, v), pad = 24;
    var X = function (i) { return i / (c.length - 1) * W; }, Y = function (y) { return pad + (hi - y) / (hi - lo || 1) * (H - 2 * pad); };
    var g = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'Net liquidity each week from ' + long(c[0][0]) + ' to ' + long(c[c.length - 1][0]) + ', between ' + Math.round(lo) + ' and ' + Math.round(hi) + ' billion dollars' }, 'spark');
    g.appendChild(svg('polyline', { points: c.map(function (r, i) { return X(i).toFixed(1) + ',' + Y(r[1]).toFixed(1); }).join(' '), 'vector-effect': 'non-scaling-stroke' }, 'trend'));
    g.appendChild(svg('circle', { cx: W - 4, cy: Y(v[v.length - 1]), r: 6 }, 'dot'));
    box.querySelector('.plot').appendChild(g); box.classList.add('on');
  }
  function lab(box, s) {
    var d = s.data, t = function (x) { return '$' + (x / 1000).toFixed(2) + 'tn'; }, b = function (x) { return (x >= 0 ? '+' : '-') + '$' + Math.abs(x).toFixed(0) + 'bn'; };
    var inf = function (n) { return d.inflation.filter(function (x) { return x.name === n; })[0]; }, pce = inf('Core PCE'), tm = inf('Trimmed-mean CPI');
    fill(box, [cell('Net liquidity', t(d.net_liq), when(d.as_of)), cell('Four weeks', b(d.chg_4w), 'change'), cell('One year', b(d.chg_1y), 'change'), cell('Fed assets', t(d.assets), when(d.as_of)), pce && ok(pce.yoy) ? cell('Core PCE', pce.yoy.toFixed(1) + '%', 'over the year') : null, tm && ok(tm.yoy) ? cell('Trimmed mean CPI', tm.yoy.toFixed(1) + '%', 'over the year') : null], s.ok ? '' : 'last good update ' + when(s.built));
  }
  function win(box, s) {
    var d = s.data;
    fill(box, [cell('Tighter after', pct(d.tighter[0], 0), 'other mornings ' + pct(d.tighter[1], 0)), cell('Five day move', d.abs_bp[0].toFixed(1) + ' bp', 'other mornings ' + d.abs_bp[1].toFixed(1)), cell('Wider by 10 bp', pct(d.wider_10[0], 0), 'other mornings ' + pct(d.wider_10[1], 0)), cell('Mornings', d.mornings.toLocaleString('en-US'), d.challenging + ' challenging')], 'data through ' + when(d.end) + ', ' + d.end.slice(0, 4));
  }
  function kit(box, s) {
    var tb = document.querySelector('[data-kit] tbody'), d = s.data; if (!tb || !d.rows.length) return;
    var name = function (r) { return { T: 'AT&T', CCL: 'Carnival', F: 'Ford', AAPL: 'Apple' }[r.ticker] || r.issuer; };
    tb.textContent = '';
    d.rows.forEach(function (r) {
      var tr = el('tr'), why = r.why || (r.gaps[0] ? 'Data gap. ' + r.gaps[0].split(' (')[0] : 'No triggers');
      [name(r), ok(r.leverage) ? r.leverage.toFixed(1) + 'x' : 'not read', ok(r.coverage) ? r.coverage.toFixed(1) + 'x' : 'not tagged', r.route.charAt(0) + r.route.slice(1).toLowerCase(), why.replace(/ \(.*?\)/g, '')].forEach(function (x) { tr.appendChild(el('td', x)); }); tb.appendChild(tr);
    });
    box.textContent = 'Run on ' + long(d.run) + (days(s.built) > 4 ? '. It has not run since.' : '.');
  }

  var by = function (k) { return STRIPS.filter(function (b) { return b.getAttribute('data-live') === k; }); };
  var any = function () { return [].some.call(arguments, function (k) { return by(k).length; }); };
  var pq = any('model', 'five', 'tape') ? load(API) : Promise.resolve(null), ps = any('tape') ? load(SNAP) : Promise.resolve(null);
  var pf = any('model', 'five', 'tender', 'tender-chart', 'lab', 'lab-chart', 'window', 'kit') ? load(FEED) : Promise.resolve(null);
  Promise.all([pq, ps]).then(function (r) {
    var Q = (r[0] && r[0].quotes) || {}, F = {};
    by('model').forEach(function (b) { modelStrip(b, Q); }); by('five').forEach(function (b) { fiveStrip(b, Q); }); by('tape').forEach(function (b) { tape(b, Q, F, r[1]); });
    if (Object.keys(Q).length) explorer(Q);
  });
  pf.then(function (j) {
    var s = (j && j.sections) || {}; if (s.models) flags(s.models);
    [['tender', 'tender', tender], ['tender-chart', 'tender', bars], ['lab', 'lab', lab], ['lab-chart', 'lab', line], ['window', 'window', win], ['kit', 'toolkit', kit]].forEach(function (t) {
      var sec = s[t[1]]; if (!sec || !sec.data) return; by(t[0]).forEach(function (b) { try { t[2](b, sec); } catch (e) {} });
    });
  });
})();
