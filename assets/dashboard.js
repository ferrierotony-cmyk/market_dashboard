/* Morning Market Dashboard - client side.
   No external libraries: charts are drawn as SVG, layout and preferences are
   kept in this browser's localStorage. Everything degrades to the server-built
   tables if a chart cannot render. */
(function () {
  'use strict';
  var D = JSON.parse(document.getElementById('dash-data').textContent);
  // candles come from market_data.js (written next to the page by the build)
  D.candles = window.MMD_CANDLES || D.candles || {};
  var haveCandles = Object.keys(D.candles).length > 0;
  var LS_LAYOUT = 'mmd.layout.v3', LS_STATE = 'mmd.state.v2';
  function lsGet(k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* storage blocked */ } }

  var state = Object.assign({
    tab: 'morning', sym: null, tf: '6M', corrWin: '90', theme: 'system',
    ind: { sma20: false, sma50: true, sma200: true, bb: true, vwap: true, vol: true, rsi: true, macd: true }
  }, lsGet(LS_STATE, {}));
  function saveState() { lsSet(LS_STATE, state); }

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function cssv(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }

  // ------------------------------------------------------------------ formatting
  var NF = {};
  function num(v, d) {
    if (v == null || !isFinite(v)) return '–';
    if (!NF[d]) NF[d] = new Intl.NumberFormat('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
    return NF[d].format(v);
  }
  function signed(v, d, suf) { if (v == null || !isFinite(v)) return '–'; return (v > 0 ? '+' : v < 0 ? '−' : '') + num(Math.abs(v), d) + (suf || ''); }
  function compact(v) {
    var a = Math.abs(v);
    if (a >= 1e9) return num(v / 1e9, 1) + 'B';
    if (a >= 1e6) return num(v / 1e6, 1) + 'M';
    if (a >= 1e3) return num(v / 1e3, 0) + 'K';
    return num(v, 0);
  }
  function pxDec(v) { var a = Math.abs(v); return a < 10 ? 4 : a < 1000 ? 2 : 1; }
  var FMT = {
    pct2: function (v) { return num(v, 2) + '%'; }, pct1: function (v) { return num(v, 1) + '%'; },
    bp0: function (v) { return num(v, 0) + ' bp'; }, idx: function (v) { return num(v, 1); },
    num2: function (v) { return num(v, 2); }, corr: function (v) { return num(v, 2); },
    money0: function (v) { return '$' + num(v, 0); }, px: function (v) { return num(v, pxDec(v)); }
  };
  var SHORT = {
    pct2: function (v) { return num(v, 2); }, pct1: function (v) { return num(v, 1); }, bp0: function (v) { return num(v, 0); },
    idx: function (v) { return num(v, 1); }, num2: function (v) { return num(v, 2); }, corr: function (v) { return num(v, 2); },
    money0: function (v) { return '$' + compact(v); }, px: function (v) { return num(v, pxDec(v)); }
  };
  function stepDecimals(step) {
    if (step >= 1) return 0;
    var mant = step / Math.pow(10, Math.floor(Math.log10(step)));
    return Math.min(6, Math.ceil(-Math.log10(step) - 1e-9) + (Math.abs(mant - 2.5) < 1e-6 ? 1 : 0));
  }
  function tickFmt(fmt, step) {
    var d = stepDecimals(step);
    if (fmt === 'pct2' || fmt === 'pct1') return function (v) { return num(v, d) + '%'; };
    if (fmt === 'bp0') return function (v) { return num(v, d) + 'bp'; };
    if (fmt === 'money0') return function (v) { return '$' + compact(v); };
    return function (v) { return num(v, d); };
  }
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  function pd(s) { return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)); }
  function fmtDay(ms, yr) { var d = new Date(ms); return d.getUTCDate() + ' ' + MON[d.getUTCMonth()] + (yr === false ? '' : ' ' + d.getUTCFullYear()); }
  function niceTicks(lo, hi, count) {
    if (!(hi > lo)) { hi = lo + 1; lo = lo - 1; }
    var raw = (hi - lo) / Math.max(1, count), p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
    var st = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
    var a = Math.floor(lo / st) * st, b = Math.ceil(hi / st) * st, out = [];
    for (var v = a; v <= b + st * 1e-9; v += st) out.push(+v.toFixed(10));
    return out;
  }
  function dateTicks(t0, t1, maxN) {
    var DAY = 864e5, span = (t1 - t0) / DAY, out = [], t;
    if (span <= 14) { for (t = Math.ceil(t0 / DAY) * DAY; t <= t1; t += DAY) out.push({ t: t, l: fmtDay(t, false) }); }
    else if (span <= 75) {
      t = Math.ceil(t0 / DAY) * DAY; while (new Date(t).getUTCDay() !== 1) t += DAY;
      for (; t <= t1; t += 7 * DAY) out.push({ t: t, l: fmtDay(t, false) });
    } else {
      var stepM = span <= 450 ? 1 : span <= 1100 ? 3 : span <= 2200 ? 6 : 12;
      var s = new Date(t0), m = s.getUTCFullYear() * 12 + s.getUTCMonth() + 1;
      m = Math.ceil(m / stepM) * stepM;
      for (; ; m += stepM) {
        var yy = Math.floor(m / 12), mm = m % 12; t = Date.UTC(yy, mm, 1);
        if (t > t1) break;
        out.push({ t: t, l: mm === 0 ? String(yy) : MON[mm] });
      }
    }
    if (out.length > maxN) { var k = Math.ceil(out.length / maxN); out = out.filter(function (_, i) { return i % k === 0; }); }
    return out;
  }
  function nearest(xs, x) {
    var lo = 0, hi = xs.length - 1;
    if (x <= xs[0]) return 0; if (x >= xs[hi]) return hi;
    while (hi - lo > 1) { var mid = (lo + hi) >> 1; if (xs[mid] <= x) lo = mid; else hi = mid; }
    return (x - xs[lo] <= xs[hi] - x) ? lo : hi;
  }
  function estW(s, size) { return String(s).length * size * 0.56; }
  function hexRgb(h) { h = h.replace('#', ''); if (h.length === 3) h = h.replace(/./g, '$&$&'); var n = parseInt(h, 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function mixHex(a, b, t) { var A = hexRgb(a), B = hexRgb(b); return 'rgb(' + A.map(function (v, i) { return Math.round(v + (B[i] - v) * t); }).join(',') + ')'; }
  function lum(rgbStr) { var m = rgbStr.match(/\d+/g).map(Number); return (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255; }

  // ------------------------------------------------------------------ svg + tooltip
  var NS = 'http://www.w3.org/2000/svg';
  function S(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function T(parent, x, y, str, attrs) { var t = S('text', Object.assign({ x: x, y: y }, attrs || {}), parent); t.textContent = str; return t; }
  function msg(host, text) { host.textContent = ''; var d = document.createElement('div'); d.className = 'chartmsg'; d.textContent = text; host.appendChild(d); }

  var tip = document.createElement('div'); tip.className = 'tip'; tip.hidden = true; tip.setAttribute('role', 'tooltip');
  document.body.appendChild(tip);
  function showTip(cx, cy, head, rows) {
    tip.textContent = '';
    var h = document.createElement('div'); h.className = 'th'; h.textContent = head; tip.appendChild(h);
    rows.forEach(function (r) {
      var tr = document.createElement('div'); tr.className = 'tr';
      var k = document.createElement('i'); k.className = 'key'; k.style.background = r.color || 'transparent';
      var b = document.createElement('b'); b.textContent = r.value;
      var s = document.createElement('span'); s.textContent = r.label;
      tr.appendChild(k); tr.appendChild(b); tr.appendChild(s); tip.appendChild(tr);
    });
    tip.hidden = false;
    var w = tip.offsetWidth, hh = tip.offsetHeight, x = cx + 14, y = cy + 14;
    if (x + w > innerWidth - 6) x = cx - w - 14;
    if (y + hh > innerHeight - 6) y = cy - hh - 14;
    tip.style.left = Math.max(4, x) + 'px'; tip.style.top = Math.max(4, y) + 'px';
  }
  function hideTip() { tip.hidden = true; }

  // ------------------------------------------------------------------ chart registry
  var registry = new Map(), pending = new Set(), raf = 0;
  function schedule(host) {
    pending.add(host);
    if (raf) return;
    var run = function () {
      raf = 0; var hs = Array.from(pending); pending.clear();
      hs.forEach(function (h) { var fn = registry.get(h); if (fn && h.offsetParent !== null) { try { fn(); } catch (e) { msg(h, 'Chart error: ' + e.message); } } });
    };
    // animation frames pause while the page is hidden (background tab, covered window): use a timer then
    raf = document.hidden ? setTimeout(run, 0) : requestAnimationFrame(run);
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden) rerenderAll(); });
  var ro = new ResizeObserver(function (es) { es.forEach(function (e) { if (registry.has(e.target)) schedule(e.target); }); });
  function mount(host, fn) { registry.set(host, fn); ro.observe(host); schedule(host); }
  function rerenderAll() { registry.forEach(function (_, h) { schedule(h); }); }

  function legendLayout(names, x0, maxX, size) {
    var pos = [], x = x0, row = 0;
    names.forEach(function (n) {
      var w = 16 + estW(n, size) + 12;
      if (x + w > maxX && x > x0) { x = x0; row++; }
      pos.push({ x: x, row: row }); x += w;
    });
    return { pos: pos, rows: row + 1 };
  }
  function seriesColor(s, i) { return cssv(s.color || ('--s' + ((i % 8) + 1))); }

  // ------------------------------------------------------------------ line chart
  function lineChart(host, spec) {
    host.textContent = '';
    var W = host.clientWidth, H = host.clientHeight;
    if (W < 60 || H < 50) return;
    var ser = (spec.series || []).filter(function (s) { return s && s.values && s.values.length; });
    if (!ser.length) { msg(host, 'No data'); return; }
    var isCat = spec.x === 'cat', fmt = FMT[spec.fmt] || FMT.num2, short = SHORT[spec.fmt] || SHORT.num2;
    var nCat = isCat ? ser[0].values.length : 0;
    ser.forEach(function (s, i) { s._x = isCat ? s.values.map(function (_, j) { return j; }) : s.dates.map(pd); s._c = seriesColor(s, i); });
    var lo = Infinity, hi = -Infinity;
    ser.forEach(function (s) { s.values.forEach(function (v) { if (v != null && isFinite(v)) { if (v < lo) lo = v; if (v > hi) hi = v; } }); });
    if (!isFinite(lo)) { msg(host, 'No data'); return; }
    if (spec.zero) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
    if (spec.ymin != null) { lo = Math.min(lo, spec.ymin); hi = Math.max(hi, spec.ymax); }
    else { var pv = (hi - lo) * 0.06 || Math.abs(hi) * 0.05 || 1; lo -= pv; hi += pv; }
    var ticks = niceTicks(lo, hi, Math.max(3, Math.min(7, Math.floor(H / 42))));
    if (spec.ymin != null) ticks = ticks.filter(function (t) { return t >= spec.ymin - 1e-9 && t <= spec.ymax + 1e-9; });
    var y0 = ticks[0], y1 = ticks[ticks.length - 1], tfm = tickFmt(spec.fmt, ticks[1] - ticks[0]);
    var labels = ticks.map(tfm);
    var ml = Math.max.apply(null, labels.map(function (l) { return estW(l, 10); })) + 10;
    var mr = spec.endLabels && !isCat ? 44 : 12, mb = 18;
    var leg = ser.length > 1 ? legendLayout(ser.map(function (s) { return s.name; }), ml, W - 4, 10.5) : null;
    var top = leg ? leg.rows * 14 + 6 : (spec.title ? 18 : 8);
    var pw = W - ml - mr, ph = H - top - mb - 4;
    if (pw < 30 || ph < 20) return;
    var x0, x1;
    if (isCat) { x0 = 0; x1 = Math.max(1, nCat - 1); }
    else {
      x0 = Math.min.apply(null, ser.map(function (s) { return s._x[0]; }));
      x1 = Math.max.apply(null, ser.map(function (s) { return s._x[s._x.length - 1]; }));
      if (x1 === x0) x1 = x0 + 864e5;
    }
    var inset = isCat ? 10 : 0;
    var X = function (v) { return ml + inset + (v - x0) / (x1 - x0) * (pw - 2 * inset); };
    var Y = function (v) { return top + 4 + (y1 - v) / (y1 - y0) * ph; };
    var title = spec.title || (host.closest('.w') ? host.closest('.w').dataset.title : 'Chart');
    var svg = S('svg', { width: W, height: H, role: 'img', 'aria-label': title + ' (line chart; use the Table button for values)' }, host);
    var g = S('g', {}, svg), grid = cssv('--grid'), muted = cssv('--muted'), ink2 = cssv('--ink2'), surf = cssv('--surface');
    ticks.forEach(function (t, i) {
      var y = Math.round(Y(t)) + 0.5;
      S('line', { x1: ml, x2: ml + pw, y1: y, y2: y, stroke: grid, 'stroke-width': 1 }, g);
      T(g, ml - 6, y + 3.5, labels[i], { 'text-anchor': 'end', fill: muted, 'font-size': 10 });
    });
    if (spec.zero && y0 < 0 && y1 > 0) S('line', { x1: ml, x2: ml + pw, y1: Y(0), y2: Y(0), stroke: cssv('--axis'), 'stroke-width': 1 }, g);
    if (isCat) {
      var every = Math.ceil(nCat / Math.max(2, Math.floor(pw / 30)));
      spec.cats.forEach(function (c, i) { if (i % every === 0) T(g, X(i), H - 5, c, { 'text-anchor': 'middle', fill: muted, 'font-size': 10 }); });
    } else {
      dateTicks(x0, x1, Math.max(2, Math.floor(pw / 62))).forEach(function (tk) {
        var x = X(tk.t); if (x > ml + 10 && x < ml + pw - 10) T(g, x, H - 5, tk.l, { 'text-anchor': 'middle', fill: muted, 'font-size': 10 });
      });
    }
    ser.forEach(function (s) {
      var d = '', pen = false;
      s.values.forEach(function (v, j) {
        if (v == null || !isFinite(v)) { pen = false; return; }
        d += (pen ? 'L' : 'M') + X(s._x[j]).toFixed(1) + ' ' + Y(v).toFixed(1); pen = true;
      });
      S('path', { d: d, fill: 'none', stroke: s._c, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
      if (isCat) s.values.forEach(function (v, j) { if (v != null) S('circle', { cx: X(j), cy: Y(v), r: 3, fill: s._c, stroke: surf, 'stroke-width': 1.5 }, svg); });
    });
    if (spec.endLabels && !isCat) {
      var placed = [];
      ser.forEach(function (s) {
        var j = s.values.length - 1; while (j >= 0 && s.values[j] == null) j--;
        if (j < 0) return;
        var x = X(s._x[j]), y = Y(s.values[j]);
        S('circle', { cx: x, cy: y, r: 4, fill: s._c, stroke: surf, 'stroke-width': 2 }, svg);
        if (placed.some(function (p) { return Math.abs(p - y) < 11; })) return;
        placed.push(y);
        T(svg, x + 7, y + 3.5, short(s.values[j]), { fill: ink2, 'font-size': 10.5 });
      });
    }
    if (leg) {
      ser.forEach(function (s, i) {
        var p = leg.pos[i], ly = 9 + p.row * 14;
        S('line', { x1: p.x, x2: p.x + 12, y1: ly, y2: ly, stroke: s._c, 'stroke-width': 2, 'stroke-linecap': 'round' }, svg);
        T(svg, p.x + 16, ly + 3.5, s.name, { fill: ink2, 'font-size': 10.5 });
      });
    } else if (spec.title) T(svg, ml, 12, spec.title, { fill: ink2, 'font-size': 10.5, 'font-weight': 600 });

    var cross = S('line', { y1: top, y2: top + ph + 4, stroke: cssv('--axis'), 'stroke-width': 1, visibility: 'hidden' }, svg);
    var dots = ser.map(function (s) { return S('circle', { r: 4, fill: s._c, stroke: surf, 'stroke-width': 2, visibility: 'hidden' }, svg); });
    var ov = S('rect', { x: ml, y: top, width: pw, height: ph + 4, fill: 'transparent', tabindex: 0, 'aria-label': title + ': arrow keys step through values' }, svg);
    function at(xv, cx, cy) {
      var rows = [], refX = null;
      ser.forEach(function (s, i) {
        var j = nearest(s._x, xv), v = s.values[j];
        if (v == null || !isFinite(v) || (!isCat && Math.abs(s._x[j] - xv) > 20 * 864e5)) { dots[i].setAttribute('visibility', 'hidden'); return; }
        if (refX == null) refX = s._x[j];
        dots[i].setAttribute('cx', X(s._x[j])); dots[i].setAttribute('cy', Y(v)); dots[i].setAttribute('visibility', 'visible');
        rows.push({ color: s._c, value: fmt(v), label: s.name });
      });
      if (refX == null) return;
      cross.setAttribute('x1', X(refX)); cross.setAttribute('x2', X(refX)); cross.setAttribute('visibility', 'visible');
      showTip(cx, cy, isCat ? spec.cats[Math.round(refX)] : fmtDay(refX), rows);
    }
    function clear() { hideTip(); cross.setAttribute('visibility', 'hidden'); dots.forEach(function (d) { d.setAttribute('visibility', 'hidden'); }); }
    function toData(px) { return x0 + (px - ml - inset) / (pw - 2 * inset) * (x1 - x0); }
    ov.addEventListener('pointermove', function (e) { var r = svg.getBoundingClientRect(); at(toData(e.clientX - r.left), e.clientX, e.clientY); });
    ov.addEventListener('pointerleave', clear);
    var kIdx = null;
    ov.addEventListener('focus', function () { kIdx = ser[0]._x.length - 1; key(); });
    ov.addEventListener('blur', clear);
    ov.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      e.preventDefault(); kIdx = Math.max(0, Math.min(ser[0]._x.length - 1, kIdx + (e.key === 'ArrowLeft' ? -1 : 1))); key();
    });
    function key() { var r = svg.getBoundingClientRect(), xv = ser[0]._x[kIdx]; at(xv, r.left + X(xv), r.top + top + 10); }

    host._table = function () {
      var headers = [isCat ? 'Tenor' : 'Date'].concat(ser.map(function (s) { return s.name; })), rows = [];
      if (isCat) spec.cats.forEach(function (c, j) { rows.push([c].concat(ser.map(function (s) { return s.values[j] == null ? '–' : fmt(s.values[j]); }))); });
      else {
        var maps = ser.map(function (s) { var m = new Map(); s._x.forEach(function (x, j) { m.set(x, s.values[j]); }); return m; });
        var all = Array.from(new Set([].concat.apply([], ser.map(function (s) { return s._x; })))).sort(function (a, b) { return b - a; });
        all.slice(0, 500).forEach(function (x) { rows.push([fmtDay(x)].concat(maps.map(function (m) { var v = m.get(x); return v == null ? '–' : fmt(v); }))); });
      }
      return { headers: headers, rows: rows };
    };
  }

  // ------------------------------------------------------------------ bar chart
  function barChart(host, spec) {
    host.textContent = '';
    var W = host.clientWidth, H = host.clientHeight;
    if (W < 80 || H < 40) return;
    var labels = spec.labels || [], vals = spec.values || [], n = labels.length;
    if (!n) { msg(host, 'No data'); return; }
    var fmt = FMT[spec.fmt] || FMT.num2;
    var ml = Math.min(W * 0.45, Math.max.apply(null, labels.map(function (l) { return estW(l, 10.5); })) + 12), mr = 58;
    var rowH = (H - 6) / n, bh = Math.min(18, rowH * 0.64), mx = Math.max.apply(null, vals.concat([0])) || 1;
    var pw = W - ml - mr, col = cssv(spec.color || '--s1'), ink2 = cssv('--ink2'), surf = cssv('--surface');
    var svg = S('svg', { width: W, height: H, role: 'img', 'aria-label': (host.closest('.w') || {}).dataset ? host.closest('.w').dataset.title + ' (bar chart)' : 'Bar chart' }, host);
    labels.forEach(function (lab, i) {
      var v = Math.max(0, vals[i] || 0), y = 3 + i * rowH + (rowH - bh) / 2, x0 = ml, x1 = ml + Math.max(1, v / mx * pw), r = Math.min(4, bh / 2, x1 - x0);
      var shown = estW(lab, 10.5) > ml - 8 ? lab.slice(0, Math.max(3, Math.floor((ml - 14) / 5.9))) + '…' : lab;
      T(svg, ml - 6, y + bh / 2 + 3.5, shown, { 'text-anchor': 'end', fill: ink2, 'font-size': 10.5 });
      var bar = S('path', { d: 'M' + x0 + ' ' + y + 'H' + (x1 - r) + 'Q' + x1 + ' ' + y + ' ' + x1 + ' ' + (y + r) + 'V' + (y + bh - r) + 'Q' + x1 + ' ' + (y + bh) + ' ' + (x1 - r) + ' ' + (y + bh) + 'H' + x0 + 'Z', fill: col }, svg);
      T(svg, x1 + 5, y + bh / 2 + 3.5, fmt(vals[i]), { fill: ink2, 'font-size': 10.5 });
      var hit = S('rect', { x: 0, y: 3 + i * rowH, width: W, height: rowH, fill: 'transparent', tabindex: 0, 'aria-label': lab + ': ' + fmt(vals[i]) }, svg);
      function on(e) { bar.setAttribute('fill-opacity', 0.75); var r2 = hit.getBoundingClientRect(); showTip(e.clientX || r2.left + ml, e.clientY || r2.top, lab, [{ color: col, value: fmt(vals[i]), label: '' }]); }
      function off() { bar.removeAttribute('fill-opacity'); hideTip(); }
      hit.addEventListener('pointermove', on); hit.addEventListener('pointerleave', off);
      hit.addEventListener('focus', on); hit.addEventListener('blur', off);
    });
    S('line', { x1: ml, x2: ml, y1: 2, y2: H - 2, stroke: cssv('--axis'), 'stroke-width': 1 }, svg);
    host._table = function () { return { headers: ['Category', 'Value'], rows: labels.map(function (l, i) { return [l, fmt(vals[i])]; }) }; };
    void surf;
  }

  // ------------------------------------------------------------------ indicators
  function smaArr(c, n) { var out = new Array(c.length).fill(null), s = 0; for (var i = 0; i < c.length; i++) { s += c[i]; if (i >= n) s -= c[i - n]; if (i >= n - 1) out[i] = s / n; } return out; }
  function emaArr(c, n) {
    var out = new Array(c.length).fill(null), k = 2 / (n + 1), e = null, first = c.findIndex(function (v) { return v != null; });
    if (first < 0) return out;
    for (var i = first; i < c.length; i++) {
      if (i < first + n - 1) continue;
      if (e == null) { var s = 0; for (var j = i - n + 1; j <= i; j++) s += c[j]; e = s / n; } else e = c[i] * k + e * (1 - k);
      out[i] = e;
    }
    return out;
  }
  function bbArr(c, n, m) {
    var mid = smaArr(c, n), up = new Array(c.length).fill(null), lo = new Array(c.length).fill(null);
    for (var i = n - 1; i < c.length; i++) { var s = 0; for (var j = i - n + 1; j <= i; j++) s += Math.pow(c[j] - mid[i], 2); var sd = Math.sqrt(s / n); up[i] = mid[i] + m * sd; lo[i] = mid[i] - m * sd; }
    return { mid: mid, up: up, lo: lo };
  }
  function rsiArr(c, n) {
    var out = new Array(c.length).fill(null); if (c.length <= n) return out;
    var ag = 0, al = 0, i;
    for (i = 1; i <= n; i++) { var d = c[i] - c[i - 1]; if (d > 0) ag += d; else al -= d; }
    ag /= n; al /= n; out[n] = al === 0 ? 100 : 100 - 100 / (1 + ag / al);
    for (i = n + 1; i < c.length; i++) { var d2 = c[i] - c[i - 1]; ag = (ag * (n - 1) + Math.max(d2, 0)) / n; al = (al * (n - 1) + Math.max(-d2, 0)) / n; out[i] = al === 0 ? 100 : 100 - 100 / (1 + ag / al); }
    return out;
  }
  function macdArr(c) {
    var e12 = emaArr(c, 12), e26 = emaArr(c, 26), m = c.map(function (_, i) { return e12[i] != null && e26[i] != null ? e12[i] - e26[i] : null; });
    var sig = emaArr(m, 9), hist = m.map(function (v, i) { return v != null && sig[i] != null ? v - sig[i] : null; });
    return { macd: m, signal: sig, hist: hist };
  }
  function vwapArr(t, h, l, c, v, gmt) {
    var out = new Array(c.length).fill(null), key = null, pv = 0, vv = 0;
    for (var i = 0; i < c.length; i++) {
      var k = Math.floor((t[i] + gmt) / 86400);
      if (k !== key) { key = k; pv = 0; vv = 0; }
      pv += (h[i] + l[i] + c[i]) / 3 * v[i]; vv += v[i];
      out[i] = vv > 0 ? pv / vv : null;
    }
    return out;
  }

  // ------------------------------------------------------------------ candlestick chart
  function candleChart(host) {
    host.textContent = '';
    var W = host.clientWidth, H = host.clientHeight;
    if (W < 120 || H < 120) return;
    var C = D.candles && D.candles[state.sym];
    if (!C) { msg(host, haveCandles ? 'No chart data for this symbol' : 'Chart data file market_data.js was not found next to this page'); return; }
    var F = C.tf[state.tf];
    if (F && F.ref && C.tf[F.ref]) F = Object.assign({}, C.tf[F.ref], { show: F.show });
    var srcEl = $('#csrc'); if (srcEl) srcEl.textContent = 'Yahoo · ' + C.delay + ' · last ' + C.time;
    if (!F) { msg(host, 'Timeframe ' + state.tf + ' not available for ' + C.label); return; }
    var intraday = F.interval !== '1d' && F.interval !== '1wk';
    var t = F.t, o = F.o, h = F.h, l = F.l, c = F.c, v = F.v, N = c.length, ind = state.ind, gmt = C.gmtoffset || 0;
    var start = F.show ? Math.max(0, N - F.show) : 0, n = N - start;
    if (n < 2) { msg(host, 'Not enough bars'); return; }
    var ov = [];
    if (ind.sma20) ov.push({ name: 'SMA 20', a: smaArr(c, 20), col: cssv('--s5') });
    if (ind.sma50) ov.push({ name: 'SMA 50', a: smaArr(c, 50), col: cssv('--s2') });
    if (ind.sma200) ov.push({ name: 'SMA 200', a: smaArr(c, 200), col: cssv('--s7') });
    var bb = ind.bb ? bbArr(c, 20, 2) : null;
    if (ind.vwap && intraday && v.some(function (x) { return x > 0; })) ov.push({ name: 'VWAP', a: vwapArr(t, h, l, c, v, gmt), col: cssv('--s1') });
    var rsi = ind.rsi ? rsiArr(c, 14) : null, mac = ind.macd ? macdArr(c) : null;
    var hasVol = ind.vol && v.slice(start).some(function (x) { return x > 0; });
    var top = 20, mb = 18, mr = 60, ml = 6, gp = 8, plotH = H - top - mb;
    var subs = []; if (hasVol) subs.push(['vol', 0.14]); if (rsi) subs.push(['rsi', 0.16]); if (mac) subs.push(['macd', 0.18]);
    var frac = subs.reduce(function (a, b) { return a + b[1]; }, 0);
    var main = { y: top, h: plotH * (1 - frac) - gp * subs.length }, panes = {}, yy = main.y + main.h;
    subs.forEach(function (s) { yy += gp; panes[s[0]] = { y: yy, h: plotH * s[1] }; yy += plotH * s[1]; });
    var pw = W - ml - mr, bw = pw / n;
    var X = function (i) { return ml + (i - start + 0.5) * bw; };
    var lo = Infinity, hi = -Infinity, i;
    for (i = start; i < N; i++) { if (l[i] < lo) lo = l[i]; if (h[i] > hi) hi = h[i]; }
    ov.forEach(function (s) { for (var j = start; j < N; j++) if (s.a[j] != null) { lo = Math.min(lo, s.a[j]); hi = Math.max(hi, s.a[j]); } });
    if (bb) for (i = start; i < N; i++) if (bb.up[i] != null) { lo = Math.min(lo, bb.lo[i]); hi = Math.max(hi, bb.up[i]); }
    var padv = (hi - lo) * 0.04 || 1; lo -= padv; hi += padv;
    var Ym = function (p) { return main.y + (hi - p) / (hi - lo) * main.h; };
    var grid = cssv('--grid'), muted = cssv('--muted'), ink2 = cssv('--ink2'), surf = cssv('--surface'), axis = cssv('--axis');
    var upC = cssv('--up'), dnC = cssv('--down');
    var svg = S('svg', { width: W, height: H, role: 'img', 'aria-label': C.label + ' ' + state.tf + ' candlestick chart; use the Table button for values' }, host);
    var mt = niceTicks(lo, hi, Math.max(3, Math.floor(main.h / 46))).filter(function (x) { return x >= lo && x <= hi; });
    var mtf = tickFmt('px', mt.length > 1 ? mt[1] - mt[0] : 1);
    mt.forEach(function (p) { var y = Math.round(Ym(p)) + 0.5; S('line', { x1: ml, x2: ml + pw, y1: y, y2: y, stroke: grid }, svg); T(svg, ml + pw + 6, y + 3.5, mtf(p), { fill: muted, 'font-size': 10 }); });
    // time axis
    function lt(i2) { return new Date((t[i2] + gmt) * 1000); }
    function xlab(i2) {
      var d = lt(i2), hm = String(d.getUTCHours()).padStart(2, '0') + ':' + String(d.getUTCMinutes()).padStart(2, '0');
      if (state.tf === '1D') return hm;
      if (state.tf === '5D') return DOW[d.getUTCDay()] + ' ' + hm;
      if (state.tf === '1M' || state.tf === '6M') return d.getUTCDate() + ' ' + MON[d.getUTCMonth()];
      return MON[d.getUTCMonth()] + " '" + String(d.getUTCFullYear()).slice(2);
    }
    var nl = Math.max(2, Math.floor(pw / 90)), stepI = Math.max(1, Math.round(n / nl));
    for (i = start + Math.floor(stepI / 2); i < N; i += stepI) T(svg, X(i), H - 5, xlab(i), { 'text-anchor': 'middle', fill: muted, 'font-size': 10 });
    // bollinger
    if (bb) {
      var up = '', dn = '', first = true;
      for (i = start; i < N; i++) if (bb.up[i] != null) { up += (first ? 'M' : 'L') + X(i).toFixed(1) + ' ' + Ym(bb.up[i]).toFixed(1); first = false; }
      for (i = N - 1; i >= start; i--) if (bb.lo[i] != null) dn += 'L' + X(i).toFixed(1) + ' ' + Ym(bb.lo[i]).toFixed(1);
      if (up) {
        var bcol = cssv('--s3');
        S('path', { d: up + dn + 'Z', fill: bcol, 'fill-opacity': 0.1, stroke: 'none' }, svg);
        line(bb.up, bcol, 1, Ym); line(bb.lo, bcol, 1, Ym); line(bb.mid, bcol, 1, Ym, 0.6);
      }
    }
    function line(a, col, wdt, Yf, op) {
      var d = '', pen = false;
      for (var j = start; j < N; j++) { if (a[j] == null) { pen = false; continue; } d += (pen ? 'L' : 'M') + X(j).toFixed(1) + ' ' + Yf(a[j]).toFixed(1); pen = true; }
      if (d) S('path', { d: d, fill: 'none', stroke: col, 'stroke-width': wdt, 'stroke-opacity': op || 1, 'stroke-linejoin': 'round' }, svg);
    }
    // candles
    var cw = Math.max(1, Math.min(12, bw * 0.68));
    for (i = start; i < N; i++) {
      var isUp = c[i] >= o[i], col = isUp ? upC : dnC, x = X(i);
      S('line', { x1: x, x2: x, y1: Ym(h[i]), y2: Ym(l[i]), stroke: col, 'stroke-width': 1 }, svg);
      var yt = Ym(Math.max(o[i], c[i])), yb = Ym(Math.min(o[i], c[i]));
      S('rect', { x: x - cw / 2, y: yt, width: cw, height: Math.max(1, yb - yt), fill: isUp ? surf : col, stroke: col, 'stroke-width': cw > 2 ? 1 : 0 }, svg);
    }
    ov.forEach(function (s) { line(s.a, s.col, 1.6, Ym); });
    // last price tag
    var lastY = Ym(c[N - 1]), lastCol = c[N - 1] >= (C.prev || o[N - 1]) ? upC : dnC;
    S('line', { x1: ml, x2: ml + pw, y1: lastY, y2: lastY, stroke: lastCol, 'stroke-width': 1, 'stroke-opacity': 0.6 }, svg);
    S('rect', { x: ml + pw + 2, y: lastY - 8, width: mr - 4, height: 16, rx: 3, fill: lastCol }, svg);
    T(svg, ml + pw + 6, lastY + 3.5, num(c[N - 1], pxDec(c[N - 1])), { fill: '#fff', 'font-size': 10, 'font-weight': 600 });
    // legend
    var lx = ml + 2, legItems = ov.slice(); if (bb) legItems.unshift({ name: 'BB 20,2', col: cssv('--s3') });
    T(svg, lx, 13, C.label + ' · ' + state.tf, { fill: cssv('--ink'), 'font-size': 11, 'font-weight': 600 });
    lx += estW(C.label + ' · ' + state.tf, 11) + 14;
    legItems.forEach(function (s) { S('line', { x1: lx, x2: lx + 12, y1: 9, y2: 9, stroke: s.col, 'stroke-width': 2 }, svg); T(svg, lx + 16, 12.5, s.name, { fill: ink2, 'font-size': 10.5 }); lx += 16 + estW(s.name, 10.5) + 12; });
    // sub panes
    function paneLabel(p, txt) { T(svg, ml + 2, p.y + 10, txt, { fill: ink2, 'font-size': 10, 'font-weight': 600 }); }
    if (panes.vol) {
      var P = panes.vol, vmax = Math.max.apply(null, v.slice(start)) || 1;
      S('line', { x1: ml, x2: ml + pw, y1: P.y + P.h, y2: P.y + P.h, stroke: axis }, svg);
      for (i = start; i < N; i++) { var vh = v[i] / vmax * (P.h - 2); S('rect', { x: X(i) - cw / 2, y: P.y + P.h - vh, width: cw, height: Math.max(0, vh), fill: c[i] >= o[i] ? upC : dnC, 'fill-opacity': 0.45 }, svg); }
      T(svg, ml + pw + 6, P.y + 10, compact(vmax), { fill: muted, 'font-size': 10 }); paneLabel(P, 'Volume');
    }
    if (panes.rsi) {
      var R = panes.rsi, Yr = function (x2) { return R.y + (100 - x2) / 100 * R.h; };
      [30, 50, 70].forEach(function (lv) { S('line', { x1: ml, x2: ml + pw, y1: Yr(lv), y2: Yr(lv), stroke: lv === 50 ? grid : axis, 'stroke-width': 1 }, svg); T(svg, ml + pw + 6, Yr(lv) + 3.5, String(lv), { fill: muted, 'font-size': 10 }); });
      line(rsi, cssv('--s1'), 1.6, Yr); paneLabel(R, 'RSI 14  ' + num(rsi[N - 1], 1));
    }
    if (panes.macd) {
      var M = panes.macd, mlo = 0, mhi = 0;
      for (i = start; i < N; i++) [mac.macd[i], mac.signal[i], mac.hist[i]].forEach(function (x2) { if (x2 != null) { mlo = Math.min(mlo, x2); mhi = Math.max(mhi, x2); } });
      if (mhi === mlo) mhi = mlo + 1;
      var Ymc = function (x2) { return M.y + (mhi - x2) / (mhi - mlo) * M.h; };
      S('line', { x1: ml, x2: ml + pw, y1: Ymc(0), y2: Ymc(0), stroke: axis }, svg);
      for (i = start; i < N; i++) if (mac.hist[i] != null) { var y1h = Ymc(Math.max(0, mac.hist[i])), y2h = Ymc(Math.min(0, mac.hist[i])); S('rect', { x: X(i) - cw / 2, y: y1h, width: cw, height: Math.max(0.5, y2h - y1h), fill: mac.hist[i] >= 0 ? cssv('--s3') : cssv('--s8'), 'fill-opacity': 0.55 }, svg); }
      line(mac.macd, cssv('--s1'), 1.5, Ymc); line(mac.signal, cssv('--s2'), 1.5, Ymc);
      paneLabel(M, 'MACD 12,26,9  ' + num(mac.macd[N - 1], 3) + ' / ' + num(mac.signal[N - 1], 3));
    }
    // crosshair
    var cross = S('line', { y1: top, y2: H - mb, stroke: axis, visibility: 'hidden' }, svg);
    var hl = S('line', { x1: ml, x2: ml + pw, stroke: axis, visibility: 'hidden' }, svg);
    var cover = S('rect', { x: ml, y: top, width: pw, height: H - top - mb, fill: 'transparent', tabindex: 0, 'aria-label': 'Candles: arrow keys step through bars' }, svg);
    function head(i2) { var d = lt(i2); return intraday ? DOW[d.getUTCDay()] + ' ' + d.getUTCDate() + ' ' + MON[d.getUTCMonth()] + ' ' + String(d.getUTCHours()).padStart(2, '0') + ':' + String(d.getUTCMinutes()).padStart(2, '0') : fmtDay(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate())); }
    function show(i2, cx, cy, py) {
      var dec = pxDec(c[i2]), prevC = i2 > 0 ? c[i2 - 1] : o[i2];
      var rows = [{ value: num(o[i2], dec), label: 'Open' }, { value: num(h[i2], dec), label: 'High' }, { value: num(l[i2], dec), label: 'Low' },
        { value: num(c[i2], dec), label: 'Close', color: c[i2] >= o[i2] ? upC : dnC }, { value: signed((c[i2] / prevC - 1) * 100, 2, '%'), label: 'Change' }];
      if (hasVol) rows.push({ value: compact(v[i2]), label: 'Volume' });
      if (bb && bb.up[i2] != null) rows.push({ value: num(bb.lo[i2], dec) + ' – ' + num(bb.up[i2], dec), label: 'Bollinger', color: cssv('--s3') });
      ov.forEach(function (s) { if (s.a[i2] != null) rows.push({ value: num(s.a[i2], dec), label: s.name, color: s.col }); });
      if (rsi && rsi[i2] != null) rows.push({ value: num(rsi[i2], 1), label: 'RSI 14', color: cssv('--s1') });
      if (mac && mac.macd[i2] != null) rows.push({ value: num(mac.macd[i2], 3) + ' / ' + num(mac.signal[i2], 3), label: 'MACD / signal', color: cssv('--s1') });
      cross.setAttribute('x1', X(i2)); cross.setAttribute('x2', X(i2)); cross.setAttribute('visibility', 'visible');
      if (py != null && py >= main.y && py <= main.y + main.h) { hl.setAttribute('y1', py); hl.setAttribute('y2', py); hl.setAttribute('visibility', 'visible'); } else hl.setAttribute('visibility', 'hidden');
      showTip(cx, cy, head(i2), rows);
    }
    function clear() { hideTip(); cross.setAttribute('visibility', 'hidden'); hl.setAttribute('visibility', 'hidden'); }
    cover.addEventListener('pointermove', function (e) { var r = svg.getBoundingClientRect(), px = e.clientX - r.left; var i2 = Math.max(start, Math.min(N - 1, start + Math.floor((px - ml) / bw))); show(i2, e.clientX, e.clientY, e.clientY - r.top); });
    cover.addEventListener('pointerleave', clear);
    var k = N - 1;
    cover.addEventListener('focus', function () { k = N - 1; var r = svg.getBoundingClientRect(); show(k, r.left + X(k), r.top + top + 20); });
    cover.addEventListener('blur', clear);
    cover.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return; e.preventDefault();
      k = Math.max(start, Math.min(N - 1, k + (e.key === 'ArrowLeft' ? -1 : 1))); var r = svg.getBoundingClientRect(); show(k, r.left + X(k), r.top + top + 20);
    });
    host._table = function () {
      var rows = [];
      for (var j = N - 1; j >= start && rows.length < 400; j--) rows.push([head(j), num(o[j], pxDec(o[j])), num(h[j], pxDec(h[j])), num(l[j], pxDec(l[j])), num(c[j], pxDec(c[j])), compact(v[j]),
        rsi && rsi[j] != null ? num(rsi[j], 1) : '–', mac && mac.macd[j] != null ? num(mac.macd[j], 3) : '–']);
      return { headers: ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'RSI 14', 'MACD'], rows: rows };
    };
  }

  // ------------------------------------------------------------------ correlation heatmap
  function heatChart(host) {
    host.textContent = '';
    var Cr = D.corr; if (!Cr) { msg(host, 'No correlation data'); return; }
    var W = host.clientWidth, H = host.clientHeight; if (W < 120 || H < 120) return;
    var lab = Cr.labels, n = lab.length, win = state.corrWin;
    var get = function (i, j) {
      var a = Cr.m90[i][j], b = Cr.m1y[i][j];
      if (win === '90') return a; if (win === '1y') return b;
      return a == null || b == null ? null : a - b;
    };
    var ml = Math.max.apply(null, lab.map(function (s) { return estW(s, 10.5); })) + 10, mt = 54, legH = 26;
    var cell = Math.floor(Math.min((W - ml - 6) / n, (H - mt - legH) / n));
    if (cell < 8) { msg(host, 'Widget too small'); return; }
    var neg = cssv('--div-neg'), pos = cssv('--div-pos'), mid = cssv('--div-mid'), ink = '#0b0b0b', ink2 = cssv('--ink2');
    function colr(v) { if (v == null) return cssv('--surface2'); var x = Math.max(-1, Math.min(1, v)); return x < 0 ? mixHex(mid, neg, -x) : mixHex(mid, pos, x); }
    var svg = S('svg', { width: W, height: H, role: 'img', 'aria-label': 'Correlation heatmap, ' + (win === '90' ? '90 days' : win === '1y' ? '1 year' : '90 days minus 1 year') }, host);
    lab.forEach(function (s, j) {
      var x = ml + j * cell + cell / 2;
      T(svg, x, mt - 6, s, { 'text-anchor': 'start', fill: ink2, 'font-size': 10, transform: 'rotate(-40 ' + x + ' ' + (mt - 6) + ')' });
      T(svg, ml - 6, mt + j * cell + cell / 2 + 3.5, s, { 'text-anchor': 'end', fill: ink2, 'font-size': 10.5 });
    });
    var hover = S('rect', { width: cell, height: cell, fill: 'none', stroke: cssv('--ink'), 'stroke-width': 2, visibility: 'hidden' }, null);
    for (var i = 0; i < n; i++) for (var j = 0; j < n; j++) {
      (function (i, j) {
        var x = ml + j * cell, y = mt + i * cell, v = i === j ? null : get(i, j), fill = i === j ? cssv('--surface2') : colr(v);
        var r = S('rect', { x: x + 1, y: y + 1, width: cell - 2, height: cell - 2, rx: 2, fill: fill, tabindex: 0, 'aria-label': lab[i] + ' vs ' + lab[j] + ': ' + (v == null ? 'n/a' : num(v, 2)) }, svg);
        if (v != null && cell >= 26) T(svg, x + cell / 2, y + cell / 2 + 3.5, num(v, 2).replace(/^0\./, '.').replace(/^-0\./, '−.'), { 'text-anchor': 'middle', 'font-size': Math.min(11, cell / 3.2), fill: lum(fill) > 0.55 ? ink : '#ffffff', 'pointer-events': 'none' });
        if (i === j) return;
        function on(e) {
          hover.setAttribute('x', x); hover.setAttribute('y', y); hover.setAttribute('visibility', 'visible'); svg.appendChild(hover);
          var rr = r.getBoundingClientRect(), a = Cr.m90[i][j], b = Cr.m1y[i][j];
          showTip(e.clientX || rr.right, e.clientY || rr.top, lab[i] + ' × ' + lab[j], [
            { value: a == null ? 'n/a' : num(a, 2), label: '90 days', color: colr(a) },
            { value: b == null ? 'n/a' : num(b, 2), label: '1 year', color: colr(b) },
            { value: a == null || b == null ? 'n/a' : signed(a - b, 2), label: 'Change (90D − 1Y)' }]);
        }
        function off() { hover.setAttribute('visibility', 'hidden'); hideTip(); }
        r.addEventListener('pointermove', on); r.addEventListener('pointerleave', off); r.addEventListener('focus', on); r.addEventListener('blur', off);
      })(i, j);
    }
    // diverging legend
    var lw = Math.min(220, n * cell), lx = ml, ly = mt + n * cell + 10, steps = 40;
    for (var s2 = 0; s2 < steps; s2++) { var vv = -1 + 2 * s2 / (steps - 1); S('rect', { x: lx + s2 * lw / steps, y: ly, width: lw / steps + 0.5, height: 8, fill: colr(vv) }, svg); }
    T(svg, lx, ly + 19, '−1', { fill: ink2, 'font-size': 10 }); T(svg, lx + lw / 2, ly + 19, '0', { fill: ink2, 'font-size': 10, 'text-anchor': 'middle' });
    T(svg, lx + lw, ly + 19, '+1', { fill: ink2, 'font-size': 10, 'text-anchor': 'end' });
    T(svg, lx + lw + 10, ly + 8, win === 'chg' ? 'change in correlation' : 'correlation', { fill: ink2, 'font-size': 10 });
    host._table = function () {
      return { headers: [''].concat(lab), rows: lab.map(function (a, i2) { return [a].concat(lab.map(function (_, j2) { var v2 = i2 === j2 ? 1 : get(i2, j2); return v2 == null ? '–' : num(v2, 2); })); }) };
    };
  }

  // ------------------------------------------------------------------ tables from charts
  function buildTable(t) {
    var tb = document.createElement('table'); tb.className = 'tbl';
    var hr = tb.createTHead().insertRow();
    t.headers.forEach(function (h, i) { var th = document.createElement('th'); th.textContent = h; th.className = i ? 'ar' : 'al'; hr.appendChild(th); });
    var body = tb.createTBody();
    t.rows.forEach(function (r) { var tr = body.insertRow(); r.forEach(function (cv, i) { var td = tr.insertCell(); td.textContent = cv; td.className = i ? 'ar' : 'al'; }); });
    return tb;
  }

  // ------------------------------------------------------------------ layout engine
  // Every visible widget owns a cell [x, y, w, h] on a 12-column grid. Dragging a
  // widget drops it at the pointer's cell; whatever it lands on is pushed down and
  // everything then floats up to close gaps. Layouts are {view: {pos: {id: [x,y,w,h]},
  // hidden: [id]}} per name; the same JSON is exported for inputs/layouts.json.
  var COLS = 12, MAX_ROWS = 400, LS_LAYOUT_OLD = 'mmd.layout.v2';
  var BUILTIN = {
    'Default': {},
    'Syndicate desk': { morning: {
      order: ['m-kpis', 'm-window', 'm-curve', 'm-oas', 'm-credit', 'm-risk', 'm-pipe', 'm-comps', 'm-rates', 'm-hist', 'm-slope', 'm-port'],
      size: { 'm-kpis': [12, 2], 'm-window': [4, 4], 'm-curve': [4, 4], 'm-oas': [4, 4], 'm-credit': [4, 5], 'm-risk': [4, 5], 'm-pipe': [4, 5], 'm-comps': [6, 3], 'm-rates': [6, 3] },
      hidden: ['m-hist', 'm-slope', 'm-port'] } },
    'Rates & credit': { morning: {
      order: ['m-kpis', 'm-curve', 'm-hist', 'm-slope', 'm-rates', 'm-credit', 'm-oas', 'm-risk', 'm-port', 'm-window', 'm-pipe', 'm-comps'],
      size: { 'm-kpis': [12, 2], 'm-curve': [4, 4], 'm-hist': [4, 4], 'm-slope': [4, 4], 'm-rates': [4, 5], 'm-credit': [4, 5], 'm-oas': [4, 5], 'm-risk': [4, 3], 'm-port': [4, 3], 'm-window': [4, 3] },
      hidden: ['m-pipe', 'm-comps'] } }
  };
  // presets baked from inputs/layouts.json (shared across machines)
  if (D.layouts) Object.keys(D.layouts).forEach(function (n) { if (D.layouts[n] && typeof D.layouts[n] === 'object') BUILTIN[n] = D.layouts[n]; });
  var MOBILE_H = { 'm-kpis': 5, 'x-ribbon': 9, 'p-summary': 6, 'c-candle': 10, 'c-side': 9, 'h-domains': 10, 'c-heat': 8 };
  var LAY = lsGet(LS_LAYOUT, null);
  if (!LAY) { var old = lsGet(LS_LAYOUT_OLD, null); LAY = old && old.custom ? old : { current: 'Default', custom: {} }; }
  if (!LAY.custom) LAY.custom = {};
  if (!BUILTIN[LAY.current] && !LAY.custom[LAY.current]) LAY.current = 'Default';
  function saveLayouts() { lsSet(LS_LAYOUT, LAY); }
  function layoutObj(name) { return LAY.custom[name] || BUILTIN[name] || {}; }
  function widgetsOf(view) { return Array.prototype.filter.call(view.children, function (e) { return e.classList.contains('w'); }); }
  function byDefault(a, b) { return (+a.dataset.def) - (+b.dataset.def); }
  function overlap(a, b) { return a[0] < b[0] + b[2] && b[0] < a[0] + a[2] && a[1] < b[1] + b[3] && b[1] < a[1] + a[3]; }
  function fits(pos, cell, skip) { for (var id in pos) if (id !== skip && overlap(pos[id], cell)) return false; return true; }
  function clampW(w) { return Math.max(1, Math.min(COLS, w | 0)); }
  function clampH(h) { return Math.max(1, Math.min(40, h | 0)); }
  // first free cell, row-major: what CSS auto-placement did before positions existed
  function flowPlace(pos, id, w, h) {
    w = clampW(w); h = clampH(h);
    for (var y = 0; y < MAX_ROWS; y++) for (var x = 0; x + w <= COLS; x++) {
      var c = [x, y, w, h]; if (fits(pos, c, id)) { pos[id] = c; return c; }
    }
    pos[id] = [0, MAX_ROWS, w, h]; return pos[id];
  }
  // push overlaps down (the pinned widget stays where it was dropped), then float up
  function compactGrid(pos, pinned) {
    var ids = Object.keys(pos).sort(function (a, b) {
      if (a === pinned) return -1; if (b === pinned) return 1;
      return pos[a][1] - pos[b][1] || pos[a][0] - pos[b][0];
    });
    var out = {};
    ids.forEach(function (id) { var c = pos[id].slice(); c[0] = Math.max(0, Math.min(COLS - c[2], c[0])); while (!fits(out, c)) c[1]++; out[id] = c; });
    ids = Object.keys(out).sort(function (a, b) { return out[a][1] - out[b][1] || out[a][0] - out[b][0]; });
    ids.forEach(function (id) { var c = out[id]; while (c[1] > 0 && fits(out, [c[0], c[1] - 1, c[2], c[3]], id)) c[1]--; });
    return out;
  }
  // {order, size, hidden} from the old engine -> {pos, hidden}
  function fromLegacy(conf, view) {
    var ws = widgetsOf(view).slice().sort(byDefault), pos = {}, hidden = conf.hidden || [];
    var rank = function (w) { var k = conf.order ? conf.order.indexOf(w.dataset.id) : -1; return k >= 0 ? k : 1000 + (+w.dataset.def); };
    ws.sort(function (a, b) { return rank(a) - rank(b); }).forEach(function (w) {
      if (hidden.indexOf(w.dataset.id) >= 0) return;
      var sz = (conf.size && conf.size[w.dataset.id]) || [+w.dataset.w, +w.dataset.h];
      flowPlace(pos, w.dataset.id, sz[0], sz[1]);
    });
    return { pos: pos, hidden: hidden.slice() };
  }
  function viewConf(name, view) {
    var L = layoutObj(name), c = L[view.dataset.view];
    if (!c) return null;
    if (!c.pos && (c.order || c.size || c.hidden)) { c = fromLegacy(c, view); L[view.dataset.view] = c; }
    return c;
  }
  function setCell(w, c) {
    w.style.gridColumn = (c[0] + 1) + ' / span ' + c[2]; w.style.gridRow = (c[1] + 1) + ' / span ' + c[3];
    w.dataset.cx = c[0]; w.dataset.cy = c[1]; w.dataset.cw = c[2]; w.dataset.ch = c[3];
    w.style.setProperty('--hm', MOBILE_H[w.dataset.id] || Math.max(c[3], 4));
  }
  function paintView(view, reorder) {
    var pos = view._pos, ws = widgetsOf(view);
    ws.forEach(function (w) { if (!w.hidden && pos[w.dataset.id]) setCell(w, pos[w.dataset.id]); });
    if (reorder === false) return;   // re-appending a node mid-drag would drop its pointer capture
    // DOM order follows the grid so a phone (single column) reads top to bottom
    ws.filter(function (w) { return !w.hidden; }).sort(function (a, b) { var p = pos[a.dataset.id], q = pos[b.dataset.id]; return p[1] - q[1] || p[0] - q[0]; })
      .concat(ws.filter(function (w) { return w.hidden; })).forEach(function (w) { view.appendChild(w); });
  }
  function applyLayout() {
    $$('.view').forEach(function (view) {
      var conf = viewConf(LAY.current, view), ws = widgetsOf(view).slice().sort(byDefault), pos = {};
      ws.forEach(function (w) {
        var id = w.dataset.id;
        w.hidden = conf && conf.hidden ? conf.hidden.indexOf(id) >= 0 : w.dataset.defHidden === '1';
        if (!w.hidden && conf && conf.pos && conf.pos[id]) pos[id] = conf.pos[id].slice();
      });
      pos = compactGrid(pos);
      // widgets the layout does not know (added since it was saved) flow in after the rest
      ws.forEach(function (w) { if (!w.hidden && !pos[w.dataset.id]) flowPlace(pos, w.dataset.id, +w.dataset.w, +w.dataset.h); });
      view._pos = pos; paintView(view);
    });
    fillLayoutSel(); renderTray(); rerenderAll();
  }
  function editableLayout() {
    if (!LAY.custom[LAY.current]) {
      var base = JSON.parse(JSON.stringify(layoutObj(LAY.current)));
      var name = LAY.current === 'Default' ? 'My layout' : LAY.current + ' (mine)';
      LAY.custom[name] = base; LAY.current = name;
    }
    return LAY.custom[LAY.current];
  }
  function commitView(view) {
    var L = editableLayout(), pos = {};
    widgetsOf(view).forEach(function (w) { if (!w.hidden && view._pos[w.dataset.id]) pos[w.dataset.id] = view._pos[w.dataset.id].slice(); });
    L[view.dataset.view] = { pos: pos, hidden: widgetsOf(view).filter(function (w) { return w.hidden; }).map(function (w) { return w.dataset.id; }) };
    saveLayouts(); fillLayoutSel(); renderTray();
  }
  function placeWidget(view, id, cell, save) {
    var pos = view._pos; pos[id] = [Math.max(0, Math.min(COLS - cell[2], cell[0])), Math.max(0, cell[1]), clampW(cell[2]), clampH(cell[3])];
    view._pos = compactGrid(pos, id); paintView(view, save !== false);
    if (save !== false) { commitView(view); rerenderAll(); }
  }
  function showWidget(view, w) {
    w.hidden = false; flowPlace(view._pos, w.dataset.id, +w.dataset.w, +w.dataset.h); view._pos = compactGrid(view._pos);
    paintView(view); commitView(view); rerenderAll();
  }
  function hideWidget(view, w) { w.hidden = true; delete view._pos[w.dataset.id]; view._pos = compactGrid(view._pos); paintView(view); commitView(view); rerenderAll(); }
  function gridMetrics(view) {
    var r = view.getBoundingClientRect(), cs = getComputedStyle(view), gap = parseFloat(cs.gap || cs.rowGap) || 7;
    var rowH = parseFloat(cs.gridAutoRows) || 62;
    return { left: r.left, top: r.top, colW: (r.width + gap) / COLS, rowH: rowH + gap };
  }
  var layoutSel = $('#layoutSel');
  function fillLayoutSel() {
    layoutSel.textContent = '';
    var names = Object.keys(BUILTIN).filter(function (n) { return !LAY.custom[n]; }).concat(Object.keys(LAY.custom));
    names.forEach(function (n) { var o = document.createElement('option'); o.value = n; o.textContent = 'Layout: ' + n; layoutSel.appendChild(o); });
    layoutSel.value = LAY.current;
    var del = $('#delLayoutBtn'); if (del) del.disabled = !LAY.custom[LAY.current];
  }
  layoutSel.addEventListener('change', function () { LAY.current = layoutSel.value; saveLayouts(); applyLayout(); });
  function currentView() { return $('.view[data-view="' + state.tab + '"]'); }
  function renderTray() {
    var items = $('#trayItems'); if (!items) return; items.textContent = '';
    var view = currentView(); if (!view) return;
    var hidden = widgetsOf(view).filter(function (w) { return w.hidden; });
    if (!hidden.length) { var s = document.createElement('span'); s.textContent = 'none'; items.appendChild(s); }
    hidden.forEach(function (w) {
      var b = document.createElement('button'); b.type = 'button'; b.textContent = '+ ' + w.dataset.title;
      b.addEventListener('click', function () { showWidget(view, w); });
      items.appendChild(b);
    });
  }
  function isEditing() { return document.body.classList.contains('editing'); }
  // widget controls
  function ctlBtn(text, label, cls, fn) {
    var b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.title = label; b.setAttribute('aria-label', label);
    if (cls) b.className = cls; b.addEventListener('click', fn); return b;
  }
  $$('.view').forEach(function (view) {
    widgetsOf(view).forEach(function (w, idx) {
      w.dataset.def = idx;
      var id = w.dataset.id, ctl = $('.wctl', w), charts = $$('.chart', w);
      if (charts.length) {
        var tb = ctlBtn('Table', 'Show the data as a table', 'tbtn', function () {
          var on = tb.getAttribute('aria-pressed') !== 'true'; tb.setAttribute('aria-pressed', on);
          var wb = $('.wb', w), old = $('.ctable', w); if (old) old.remove();
          var vis = $$('.chart, .stack', wb);
          if (on) {
            vis.forEach(function (c) { c.style.display = 'none'; });
            var box = document.createElement('div'); box.className = 'ctable';
            charts.forEach(function (c) { if (c._table) box.appendChild(buildTable(c._table())); });
            wb.appendChild(box);
          } else { vis.forEach(function (c) { c.style.display = ''; }); rerenderAll(); }
        });
        tb.setAttribute('aria-pressed', 'false'); ctl.appendChild(tb);
      }
      function cell() { return view._pos[id].slice(); }
      function nudge(dx, dy, dw, dh) { var c = cell(); placeWidget(view, id, [c[0] + dx, c[1] + dy, c[2] + dw, c[3] + dh]); }
      var edits = [
        ['◂', 'Narrower (Shift+Left)', function () { nudge(0, 0, -1, 0); }],
        ['▸', 'Wider (Shift+Right)', function () { nudge(0, 0, 1, 0); }],
        ['▴', 'Shorter (Shift+Up)', function () { nudge(0, 0, 0, -1); }],
        ['▾', 'Taller (Shift+Down)', function () { nudge(0, 0, 0, 1); }],
        ['✕', 'Hide widget', function () { hideWidget(view, w); }]
      ];
      edits.forEach(function (e) { var b = ctlBtn(e[0], e[1], 'edit', e[2]); b.hidden = true; ctl.appendChild(b); });
      // drag the header to any cell
      var head = $('.wh', w);
      head.addEventListener('pointerdown', function (e) {
        if (!isEditing() || e.button !== 0 || e.target.closest('button')) return;
        e.preventDefault(); head.setPointerCapture(e.pointerId);
        var r = w.getBoundingClientRect(), offX = e.clientX - r.left, offY = e.clientY - r.top, moved = false;
        w.classList.add('dragging');
        function mv(ev) {
          var m = gridMetrics(view), c = cell();
          var x = Math.round((ev.clientX - offX - m.left) / m.colW), y = Math.round((ev.clientY - offY - m.top) / m.rowH);
          x = Math.max(0, Math.min(COLS - c[2], x)); y = Math.max(0, y);
          if (x !== c[0] || y !== c[1]) { moved = true; placeWidget(view, id, [x, y, c[2], c[3]], false); }
        }
        function up() {
          head.removeEventListener('pointermove', mv); head.removeEventListener('pointerup', up); head.removeEventListener('pointercancel', up);
          w.classList.remove('dragging'); if (moved) { paintView(view); commitView(view); rerenderAll(); }
        }
        head.addEventListener('pointermove', mv); head.addEventListener('pointerup', up); head.addEventListener('pointercancel', up);
      });
      // keyboard: arrows move, shift+arrows resize
      head.addEventListener('keydown', function (e) {
        if (!isEditing()) return;
        var k = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key]; if (!k) return;
        e.preventDefault();
        if (e.shiftKey) nudge(0, 0, k[0], k[1]); else nudge(k[0], k[1], 0, 0);
      });
      // drag the corner to resize
      var rz = $('.rz', w);
      rz.addEventListener('pointerdown', function (e) {
        e.preventDefault(); rz.setPointerCapture(e.pointerId);
        var c0 = cell(), m = gridMetrics(view), sx = e.clientX, sy = e.clientY;
        function mv(ev) {
          var nw = clampW(Math.round(c0[2] + (ev.clientX - sx) / m.colW)), nh = clampH(Math.round(c0[3] + (ev.clientY - sy) / m.rowH));
          nw = Math.min(nw, COLS - c0[0]);
          var c = cell(); if (nw !== c[2] || nh !== c[3]) placeWidget(view, id, [c0[0], c0[1], nw, nh], false);
        }
        function up() { rz.removeEventListener('pointermove', mv); rz.removeEventListener('pointerup', up); paintView(view); commitView(view); rerenderAll(); }
        rz.addEventListener('pointermove', mv); rz.addEventListener('pointerup', up);
      });
    });
  });
  function setEditing(on) {
    document.body.classList.toggle('editing', on);
    $('#editBtn').setAttribute('aria-pressed', on); $('#tray').hidden = !on;
    $$('.wctl .edit').forEach(function (b) { b.hidden = !on; });
    $$('.wh').forEach(function (h) { if (on) h.tabIndex = 0; else h.removeAttribute('tabindex'); });
    renderTray(); setTopVar();
  }
  $('#editBtn').addEventListener('click', function () { setEditing(!isEditing()); });
  $('#doneBtn').addEventListener('click', function () { setEditing(false); });
  $('#saveAsBtn').addEventListener('click', function () {
    var name = (window.prompt('Name this layout (it is saved in this browser; use Export to share it):', '') || '').trim();
    if (!name) return;
    $$('.view').forEach(function (v) { commitView(v); });
    LAY.custom[name] = JSON.parse(JSON.stringify(layoutObj(LAY.current))); LAY.current = name; saveLayouts(); fillLayoutSel();
  });
  $('#delLayoutBtn').addEventListener('click', function () {
    if (!LAY.custom[LAY.current]) return;
    if (!window.confirm('Delete the layout "' + LAY.current + '"?')) return;
    delete LAY.custom[LAY.current]; LAY.current = 'Default'; saveLayouts(); applyLayout();
  });
  $('#resetBtn').addEventListener('click', function () {
    var view = currentView(); if (!view) return;
    if (LAY.custom[LAY.current]) { delete LAY.custom[LAY.current][view.dataset.view]; saveLayouts(); }
    applyLayout();
  });
  // export / import: the file is exactly what inputs/layouts.json takes, so a layout
  // exported here can be made a shared preset for every machine that runs the build
  function download(name, text) {
    var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'application/json' })); a.download = name;
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 0);
  }
  var exportBtn = $('#exportBtn'), importFile = $('#importFile');
  if (exportBtn) exportBtn.addEventListener('click', function () {
    $$('.view').forEach(function (v) { if (LAY.custom[LAY.current]) commitView(v); });
    var out = {};
    Object.keys(LAY.custom).forEach(function (n) { out[n] = LAY.custom[n]; });
    if (!Object.keys(out).length) { window.alert('No custom layouts yet. Click Customize, move something, then export.'); return; }
    download('layouts.json', JSON.stringify(out, null, 1));
  });
  if (importFile) importFile.addEventListener('change', function () {
    var f = importFile.files[0]; if (!f) return;
    var rd = new FileReader();
    rd.onload = function () {
      try {
        var obj = JSON.parse(rd.result), n = 0;
        Object.keys(obj).forEach(function (name) { if (obj[name] && typeof obj[name] === 'object') { LAY.custom[name] = obj[name]; n++; LAY.current = name; } });
        if (!n) throw new Error('no layouts in file');
        saveLayouts(); applyLayout();
      } catch (e) { window.alert('Could not import: ' + e.message); }
      importFile.value = '';
    };
    rd.readAsText(f);
  });

  // ------------------------------------------------------------------ tabs, theme, refresh
  function setTopVar() {
    var h = $('#top').offsetHeight + ($('#tray').hidden ? 0 : $('#tray').offsetHeight);
    document.documentElement.style.setProperty('--top', h + 'px');
  }
  function showTab(v) {
    if (!$('.view[data-view="' + v + '"]')) v = 'morning';
    state.tab = v; saveState();
    $$('.view').forEach(function (x) { x.hidden = x.dataset.view !== v; });
    $$('.tabs button').forEach(function (b) { b.setAttribute('aria-selected', b.dataset.view === v); });
    renderTray(); setTopVar(); rerenderAll(); hideTip();
  }
  $$('.tabs button').forEach(function (b) { b.addEventListener('click', function () { showTab(b.dataset.view); }); });
  $$('[data-goto]').forEach(function (b) { b.addEventListener('click', function () { showTab(b.dataset.goto); }); });
  var feedsDlg = $('#feedsDlg'), feedsBtn = $('#feedsBtn');
  if (feedsDlg && feedsBtn) {
    feedsBtn.addEventListener('click', function () { if (feedsDlg.showModal) feedsDlg.showModal(); else feedsDlg.setAttribute('open', ''); });
    $('#feedsClose').addEventListener('click', function () { feedsDlg.close ? feedsDlg.close() : feedsDlg.removeAttribute('open'); });
    feedsDlg.addEventListener('click', function (e) { if (e.target === feedsDlg) feedsDlg.close(); });
  }

  var themeBtn = $('#themeBtn');
  function applyTheme() {
    var r = document.documentElement;
    if (state.theme === 'system') r.removeAttribute('data-theme'); else r.setAttribute('data-theme', state.theme);
    themeBtn.textContent = 'Theme: ' + ({ system: 'Auto', light: 'Light', dark: 'Dark' })[state.theme];
  }
  themeBtn.addEventListener('click', function () {
    state.theme = ({ system: 'light', light: 'dark', dark: 'system' })[state.theme] || 'system';
    saveState(); applyTheme(); rerenderAll();
  });
  if (window.matchMedia) window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', rerenderAll);

  var cd = $('#countdown'), reloadAt = Date.now() + (D.meta.refresh_s || 900) * 1000;
  setInterval(function () {
    var left = reloadAt - Date.now();
    if (left <= 0) {
      if (document.body.classList.contains('editing')) { reloadAt = Date.now() + 60000; return; }
      location.reload(); return;
    }
    cd.textContent = 'reload in ' + Math.floor(left / 60000) + ':' + String(Math.floor(left % 60000 / 1000)).padStart(2, '0');
  }, 1000);
  $$('.news li.hassum').forEach(function (li) {
    function tog(e) { if (e.target.closest('a')) return; li.classList.toggle('open'); }
    li.addEventListener('click', tog);
    li.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); tog(e); } });
  });
  $$('time[data-iso]').forEach(function (t) {
    var d = new Date(t.dataset.iso);
    if (!isNaN(d)) t.textContent = d.toLocaleString([], { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  });

  // ------------------------------------------------------------------ charts view controls
  var csym = $('#csym'), syms = D.candles ? Object.keys(D.candles) : [];
  if (!state.sym || syms.indexOf(state.sym) < 0) state.sym = syms[0] || null;
  function updateSide() { $$('.symside').forEach(function (s) { s.hidden = s.dataset.sym !== state.sym; }); }
  function updateTfButtons() {
    var C = D.candles && D.candles[state.sym];
    if (C && !C.tf[state.tf]) state.tf = Object.keys(C.tf).indexOf('6M') >= 0 ? '6M' : Object.keys(C.tf)[0];
    $$('#ctf button').forEach(function (b) { b.disabled = !(C && C.tf[b.dataset.tf]); b.setAttribute('aria-pressed', b.dataset.tf === state.tf); });
  }
  var candleHost = $('#candle');
  function redrawCandle() { saveState(); updateTfButtons(); updateSide(); if (candleHost) schedule(candleHost); }
  if (csym) {
    csym.value = state.sym || '';
    csym.addEventListener('change', function () { state.sym = csym.value; redrawCandle(); });
    $$('#ctf button').forEach(function (b) { b.addEventListener('click', function () { state.tf = b.dataset.tf; redrawCandle(); }); });
    $$('.inds input').forEach(function (cb) {
      cb.checked = !!state.ind[cb.dataset.ind];
      cb.addEventListener('change', function () { state.ind[cb.dataset.ind] = cb.checked; redrawCandle(); });
    });
  }
  $$('tr.rowlink').forEach(function (tr) {
    function go() { if (!D.candles[tr.dataset.sym]) return; state.sym = tr.dataset.sym; if (csym) csym.value = state.sym; showTab('charts'); redrawCandle(); }
    tr.addEventListener('click', go);
    tr.addEventListener('keydown', function (e) { if (e.key === 'Enter') go(); });
  });
  $$('#cwin button').forEach(function (b) {
    b.setAttribute('aria-pressed', b.dataset.win === state.corrWin);
    b.addEventListener('click', function () {
      state.corrWin = b.dataset.win; saveState();
      $$('#cwin button').forEach(function (x) { x.setAttribute('aria-pressed', x.dataset.win === state.corrWin); });
      var hh = $('#heat'); if (hh) schedule(hh);
    });
  });

  // ------------------------------------------------------------------ sortable tables + watchlist filter
  function cellVal(td) {
    var t = td.textContent.trim().replace(/−/g, '-').replace(/[,%$x]/g, '');
    if (!t || t === '–') return null;
    var n = parseFloat(t); return isNaN(n) ? null : n;
  }
  $$('table.sort').forEach(function (tb) {
    var ths = $$('thead th', tb);
    ths.forEach(function (th, ci) {
      th.classList.add('sortable'); th.tabIndex = 0; th.setAttribute('aria-sort', 'none');
      function sort() {
        var dir = th.dataset.dir === 'desc' ? 'asc' : 'desc';
        ths.forEach(function (x) { delete x.dataset.dir; x.setAttribute('aria-sort', 'none'); });
        th.dataset.dir = dir; th.setAttribute('aria-sort', dir === 'desc' ? 'descending' : 'ascending');
        var body = tb.tBodies[0], rows = Array.prototype.slice.call(body.rows);
        rows.sort(function (a, b) {
          var ta = a.cells[ci], tb2 = b.cells[ci]; if (!ta || !tb2) return 0;
          var na = cellVal(ta), nb = cellVal(tb2), r;
          if (na != null && nb != null) r = na - nb;
          else if (na != null) r = 1; else if (nb != null) r = -1;
          else r = ta.textContent.trim().localeCompare(tb2.textContent.trim());
          return dir === 'desc' ? -r : r;
        });
        rows.forEach(function (r) { body.appendChild(r); });
      }
      th.addEventListener('click', sort);
      th.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sort(); } });
    });
  });
  var wf = $('#wfilter'), ws = $('#wsector');
  function applyWatchFilter() {
    var q = (wf.value || '').trim().toLowerCase(), sec = ws.value, n = 0, tot = 0;
    $$('#w-w-table tbody tr').forEach(function (tr) {
      tot++;
      var hay = ((tr.dataset.name || '') + ' ' + (tr.dataset.sym || '') + ' ' + (tr.dataset.sector || '')).toLowerCase();
      var show = (!q || hay.indexOf(q) >= 0) && (!sec || tr.dataset.sector === sec);
      tr.hidden = !show; if (show) n++;
    });
    $('#wcount').textContent = n + ' of ' + tot + ' names';
  }
  if (wf && ws) { wf.addEventListener('input', applyWatchFilter); ws.addEventListener('change', applyWatchFilter); applyWatchFilter(); }

  // ------------------------------------------------------------------ market screener
  // ~6,000 rows from market_universe.js: filtered and sorted in memory, only the
  // visible slice is in the DOM (two spacer rows keep the scrollbar honest).
  var U = window.MMD_UNIVERSE, scr = $('#screener');
  if (U && U.rows && scr) {
    var CI = {}; U.cols.forEach(function (c, i) { CI[c] = i; });
    var ROWH = 22, SCOLS = [
      { k: 'symbol', l: 'Symbol', w: 72, f: function (v) { return v; }, al: true },
      { k: 'name', l: 'Name', w: 230, f: function (v) { return v; }, al: true },
      { k: 'sector', l: 'Sector', w: 150, f: function (v) { return v; }, al: true },
      { k: 'last', l: 'Last', w: 70, f: function (v) { return v == null ? '–' : num(v, pxDec(v)); } },
      { k: 'chg_pct', l: '1D', w: 70, f: function (v) { return signed(v, 2, '%'); }, sign: true },
      { k: 'volume', l: 'Volume', w: 74, f: function (v) { return v == null ? '–' : compact(v); } },
      { k: 'vol_x', l: 'Vol/3M', w: 62, f: function (v) { return v == null ? '–' : num(v, 1) + 'x'; } },
      { k: 'dollar_vol', l: '$ traded', w: 78, f: function (v) { return v == null ? '–' : '$' + compact(v); } },
      { k: 'mcap', l: 'Mkt cap', w: 78, f: function (v) { return v == null ? '–' : '$' + compact(v); } },
      { k: 'pos52', l: '52w pos', w: 64, f: function (v) { return v == null ? '–' : num(v, 0) + '%'; } },
      { k: 'vs50', l: 'vs 50D', w: 66, f: function (v) { return signed(v, 1, '%'); }, sign: true },
      { k: 'vs200', l: 'vs 200D', w: 66, f: function (v) { return signed(v, 1, '%'); }, sign: true },
      { k: 'exchange', l: 'Exchange', w: 90, f: function (v) { return v || ''; }, al: true }
    ];
    var sst = { q: '', sector: '', bucket: '', min: 1e7, watch: false, key: 'dollar_vol', dir: 'desc' }, srows = [];
    var sf = $('#sfilter'), ss = $('#ssector'), sb = $('#sbucket'), smin = $('#smin'), sw = $('#swatch'), scount = $('#scount');
    var tbl = document.createElement('table'), thead = tbl.createTHead(), hr = thead.insertRow(), body = tbl.createTBody();
    SCOLS.forEach(function (c) {
      var th = document.createElement('th'); th.textContent = c.l; th.style.width = c.w + 'px'; th.className = c.al ? 'al' : 'ar'; th.tabIndex = 0;
      th.setAttribute('aria-sort', 'none');
      function sortBy() { if (sst.key === c.k) sst.dir = sst.dir === 'desc' ? 'asc' : 'desc'; else { sst.key = c.k; sst.dir = c.al ? 'asc' : 'desc'; } recompute(); }
      th.addEventListener('click', sortBy); th.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sortBy(); } });
      hr.appendChild(th);
    });
    scr.appendChild(tbl);
    function recompute() {
      var q = sst.q.toLowerCase(), ki = CI[sst.key], isText = SCOLS.some(function (c) { return c.k === sst.key && c.al; });
      srows = U.rows.filter(function (r) {
        if (sst.sector && r[CI.sector] !== sst.sector) return false;
        if (sst.bucket && r[CI.bucket] !== sst.bucket) return false;
        if (sst.min && !(r[CI.dollar_vol] >= sst.min)) return false;
        if (sst.watch && !r[CI.in_watch]) return false;
        if (q && (String(r[CI.symbol]).toLowerCase().indexOf(q) < 0 && String(r[CI.name]).toLowerCase().indexOf(q) < 0)) return false;
        return true;
      });
      var dir = sst.dir === 'desc' ? -1 : 1;
      srows.sort(function (a, b) {
        var x = a[ki], y = b[ki];
        if (isText) return dir * String(x || '').localeCompare(String(y || ''));
        if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1;
        return dir * (x - y);
      });
      $$('th', thead).forEach(function (th, i) { th.setAttribute('aria-sort', SCOLS[i].k === sst.key ? (sst.dir === 'desc' ? 'descending' : 'ascending') : 'none'); });
      scount.textContent = srows.length.toLocaleString() + ' of ' + U.rows.length.toLocaleString() + ' names';
      scr.scrollTop = 0; paint();
    }
    function paint() {
      var n = srows.length, h = scr.clientHeight || 400, first = Math.max(0, Math.floor(scr.scrollTop / ROWH) - 5), vis = Math.ceil(h / ROWH) + 10, last = Math.min(n, first + vis);
      body.textContent = '';
      var sp1 = body.insertRow(); sp1.className = 'spacer'; var c1 = sp1.insertCell(); c1.colSpan = SCOLS.length; c1.style.height = (first * ROWH) + 'px';
      for (var i = first; i < last; i++) {
        var r = srows[i], tr = body.insertRow(); tr.className = 'srow'; tr.title = r[CI.industry] || '';
        SCOLS.forEach(function (c) {
          var td = tr.insertCell(), v = r[CI[c.k]]; td.className = c.al ? 'al' : 'ar'; td.textContent = c.f(v);
          if (c.sign && v != null) td.classList.add(v > 0 ? 'up' : v < 0 ? 'dn' : 'flat');
          if (c.k === 'symbol' && r[CI.in_watch]) { var ch = document.createElement('span'); ch.className = 'chipw'; ch.textContent = 'WL'; td.appendChild(ch); }
          if (c.k === 'pos52' && v != null) { if (r[CI.new_high]) td.classList.add('up'); if (r[CI.new_low]) td.classList.add('dn'); }
        });
      }
      var sp2 = body.insertRow(); sp2.className = 'spacer'; var c2 = sp2.insertCell(); c2.colSpan = SCOLS.length; c2.style.height = (Math.max(0, n - last) * ROWH) + 'px';
      if (!n) { var e = body.insertRow().insertCell(); e.colSpan = SCOLS.length; e.className = 'muted al'; e.textContent = 'No names match'; }
    }
    var lastFirst = -1;
    scr.addEventListener('scroll', function () { var f = Math.floor(scr.scrollTop / ROWH); if (f !== lastFirst) { lastFirst = f; paint(); } });
    new ResizeObserver(function () { paint(); }).observe(scr);
    if (sf) sf.addEventListener('input', function () { sst.q = sf.value.trim(); recompute(); });
    if (ss) ss.addEventListener('change', function () { sst.sector = ss.value; recompute(); });
    if (sb) sb.addEventListener('change', function () { sst.bucket = sb.value; recompute(); });
    if (smin) smin.addEventListener('change', function () { sst.min = +smin.value; recompute(); });
    if (sw) sw.addEventListener('change', function () { sst.watch = sw.checked; recompute(); });
    recompute();
    // movers tables: clicking a name that is on the watchlist opens its chart; otherwise filter the screener to it
    $$('tr.mrow').forEach(function (tr) {
      tr.addEventListener('click', function () {
        var s = tr.dataset.sym;
        if (D.candles && D.candles[s]) { state.sym = s; if (csym) csym.value = s; showTab('charts'); redrawCandle(); return; }
        if (sf) { sf.value = s; sst.q = s; sst.min = 0; if (smin) smin.value = '0'; recompute(); scr.scrollIntoView({ block: 'nearest' }); }
      });
    });
  }

  // ------------------------------------------------------------------ alert rules editor
  // Edits are previewed instantly against the numbers baked into this page and kept
  // in this browser; "Download alerts.csv" writes the file the build reads.
  var RULES_LS = 'mmd.rules.v1', rulesPanel = $('#rulesPanel'), rulesBtn = $('#rulesBtn');
  if (rulesPanel && rulesBtn && D.alert_rules) {
    var fileRules = D.alert_rules.map(function (r) { return Object.assign({}, r); });
    var rules = lsGet(RULES_LS, null) || JSON.parse(JSON.stringify(fileRules));
    var OPS = ['>', '<', '>=', '<=', 'abs>', 'abs<', 'crosses_above', 'crosses_below'];
    var SEVS = ['critical', 'serious', 'warning', 'info'];
    var SUFFIX = { d1: '1-day change', w1: '1-week change', m1: '1-month change', ytd: 'YTD change' };
    var SYMM = (D.metric_labels && D.metric_labels.symbol) || {}, PORTM = (D.metric_labels && D.metric_labels.portfolio) || {};
    function marketMetricOptions() {
      var out = [];
      Object.keys(D.metrics || {}).forEach(function (k) {
        var m = D.metrics[k]; out.push([k, m.label]);
        Object.keys(SUFFIX).forEach(function (s) { out.push([k + '.' + s, m.label + ' - ' + SUFFIX[s]]); });
      });
      return out;
    }
    var METRIC_OPTS = { market: marketMetricOptions(), symbol: Object.keys(SYMM).map(function (k) { return [k, SYMM[k]]; }),
      portfolio: Object.keys(PORTM).map(function (k) { return [k, PORTM[k]]; }) };
    function cmp(op, v, x) {
      if (v == null || !isFinite(v) || !isFinite(x)) return false;
      switch (op) { case '>': return v > x; case '<': return v < x; case '>=': return v >= x; case '<=': return v <= x; case 'abs>': return Math.abs(v) > x; case 'abs<': return Math.abs(v) < x; }
      return false;
    }
    function targets(tg) {
      var S = D.symmetrics || {}, ids = Object.keys(S); tg = (tg || '*').trim();
      if (tg === '*') return ids;
      if (tg.toLowerCase() === 'detail') return ids.filter(function (s) { return S[s].detail; });
      if (/^sector:/i.test(tg)) { var sc = tg.replace(/^sector:/i, '').trim().toLowerCase(); return ids.filter(function (s) { return (S[s].sector || '').toLowerCase() === sc; }); }
      var want = tg.toUpperCase().split(',').map(function (s) { return s.trim(); }); return ids.filter(function (s) { return want.indexOf(s) >= 0; });
    }
    // mirrors alerts_compute() in alerts.R
    function evalRule(r) {
      var x = parseFloat(r.value), v;
      if (r.scope === 'market') {
        var parts = String(r.metric).split('.'), m = (D.metrics || {})[parts[0]]; if (!m) return { ok: false, text: 'unknown metric' };
        v = parts[1] ? m[parts[1]] : m.v; var hit = cmp(r.op, v, x);
        return { ok: true, fires: hit, text: (v == null ? 'n/a' : num(v, 2)) + (hit ? ' ✓ fires' : '') };
      }
      if (r.scope === 'portfolio') {
        v = (D.portmetrics || {})[r.metric]; if (v === undefined) return { ok: false, text: 'unknown metric' };
        var h2 = cmp(r.op, v, x); return { ok: true, fires: h2, text: (v == null ? 'n/a' : num(v, 2)) + (h2 ? ' ✓ fires' : '') };
      }
      var S = D.symmetrics || {}, hits = [], tg = targets(r.target);
      tg.forEach(function (s) {
        var sm = S[s], f = false;
        if (r.op === 'crosses_above' || r.op === 'crosses_below') {
          var up = r.op === 'crosses_above', val = String(r.value || '').trim().toLowerCase();
          if (val === 'sma50' || val === 'sma200') f = sm[val === 'sma50' ? 'cross50' : 'cross200'] === (up ? 1 : -1);
          else if (isFinite(x) && sm.prev != null && sm.last != null) f = up ? (sm.prev < x && sm.last >= x) : (sm.prev > x && sm.last <= x);
        } else f = cmp(r.op, sm[r.metric], x);
        if (f) hits.push(s);
      });
      return { ok: true, fires: hits.length > 0, text: hits.length ? hits.length + ' of ' + tg.length + ' fire: ' + hits.slice(0, 6).join(', ') + (hits.length > 6 ? '…' : '') : '0 of ' + tg.length };
    }
    function csvCell(s) { s = String(s == null ? '' : s); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }
    function toCSV() {
      var cols = ['id', 'enabled', 'scope', 'target', 'metric', 'op', 'value', 'severity', 'note'];
      return cols.join(',') + '\n' + rules.map(function (r) { return cols.map(function (c) { return csvCell(c === 'enabled' ? (r.enabled ? 'Y' : 'N') : r[c]); }).join(','); }).join('\n') + '\n';
    }
    function sel(opts, val, onchange) {
      var s = document.createElement('select');
      opts.forEach(function (o) { var op = document.createElement('option'); op.value = o[0]; op.textContent = o[1] || o[0]; s.appendChild(op); });
      if (opts.every(function (o) { return o[0] !== val; }) && val) { var ex = document.createElement('option'); ex.value = val; ex.textContent = val; s.appendChild(ex); }
      s.value = val || opts[0][0]; s.addEventListener('change', function () { onchange(s.value); }); return s;
    }
    function inp(val, cls, onchange) { var i = document.createElement('input'); i.type = 'text'; i.value = val == null ? '' : val; if (cls) i.className = cls; i.addEventListener('change', function () { onchange(i.value); }); return i; }
    function save() { lsSet(RULES_LS, rules); }
    function renderRules() {
      rulesPanel.textContent = '';
      var tool = document.createElement('div'); tool.className = 'rtool';
      var add = ctlBtn('+ Add rule', 'Add a rule', '', function () { rules.push({ id: 'rule' + (rules.length + 1), enabled: true, scope: 'symbol', target: '*', metric: 'd1', op: 'abs>', value: '5', severity: 'warning', note: '' }); save(); renderRules(); });
      var dl = ctlBtn('Download alerts.csv', 'Save these rules as inputs/alerts.csv so the build uses them', '', function () { download('alerts.csv', toCSV()); });
      var rs = ctlBtn('Reset to file', 'Discard browser edits and reload the rules the build used', '', function () { rules = JSON.parse(JSON.stringify(fileRules)); try { localStorage.removeItem(RULES_LS); } catch (e) { } renderRules(); });
      var edited = JSON.stringify(rules) !== JSON.stringify(fileRules);
      var note = document.createElement('span'); note.className = 'muted';
      note.textContent = (edited ? 'Edited in this browser, not yet in the build. ' : '') + 'Preview shows what each rule would fire on right now. Save the download as inputs/alerts.csv and rebuild to make it live.';
      tool.appendChild(add); tool.appendChild(dl); tool.appendChild(rs); tool.appendChild(note); rulesPanel.appendChild(tool);
      var tb = document.createElement('table'), hr = tb.createTHead().insertRow();
      ['On', 'Id', 'Scope', 'Target', 'Metric', 'Op', 'Value', 'Severity', 'Note', 'Preview', ''].forEach(function (h) { var th = document.createElement('th'); th.textContent = h; hr.appendChild(th); });
      var body = tb.createTBody();
      rules.forEach(function (r, i) {
        var tr = body.insertRow(); if (!r.enabled) tr.className = 'off';
        var on = document.createElement('input'); on.type = 'checkbox'; on.checked = !!r.enabled; on.addEventListener('change', function () { r.enabled = on.checked; save(); renderRules(); });
        tr.insertCell().appendChild(on);
        tr.insertCell().appendChild(inp(r.id, '', function (v) { r.id = v; save(); }));
        tr.insertCell().appendChild(sel([['symbol'], ['market'], ['portfolio']], r.scope, function (v) { r.scope = v; r.metric = (METRIC_OPTS[v][0] || [''])[0]; if (v !== 'symbol') r.target = ''; save(); renderRules(); }));
        var tgc = tr.insertCell(); if (r.scope === 'symbol') tgc.appendChild(inp(r.target, '', function (v) { r.target = v; save(); renderRules(); }));
        tr.insertCell().appendChild(sel(METRIC_OPTS[r.scope] || [[r.metric]], r.metric, function (v) { r.metric = v; save(); renderRules(); }));
        tr.insertCell().appendChild(sel(OPS.map(function (o) { return [o]; }), r.op, function (v) { r.op = v; save(); renderRules(); }));
        tr.insertCell().appendChild(inp(r.value, 'num', function (v) { r.value = v; save(); renderRules(); }));
        tr.insertCell().appendChild(sel(SEVS.map(function (o) { return [o]; }), r.severity, function (v) { r.severity = v; save(); renderRules(); }));
        tr.insertCell().appendChild(inp(r.note, '', function (v) { r.note = v; save(); }));
        var ev = evalRule(r), fc = tr.insertCell(); fc.className = 'fire'; fc.textContent = ev.text; if (ev.fires) fc.classList.add('dn'); if (!ev.ok) fc.classList.add('muted');
        tr.insertCell().appendChild(ctlBtn('✕', 'Delete rule', '', function () { rules.splice(i, 1); save(); renderRules(); }));
      });
      rulesPanel.appendChild(tb);
    }
    rulesBtn.addEventListener('click', function () {
      var open = rulesPanel.hidden; rulesPanel.hidden = !open; rulesBtn.setAttribute('aria-expanded', open);
      if (open) renderRules();
    });
  }

  // ------------------------------------------------------------------ mount
  $$('.chart[data-chart]').forEach(function (h) {
    var spec = D.charts[h.dataset.chart];
    if (!spec) { msg(h, 'No data'); return; }
    mount(h, function () { if (spec.type === 'bar') barChart(h, spec); else lineChart(h, spec); });
  });
  if (candleHost) mount(candleHost, function () { candleChart(candleHost); });
  var heatHost = $('#heat'); if (heatHost) mount(heatHost, function () { heatChart(heatHost); });

  applyTheme(); applyLayout(); updateTfButtons(); updateSide();
  showTab(state.tab);
  window.addEventListener('resize', setTopVar);
})();
