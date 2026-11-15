/* 記事「サウナシュラン受賞サウナに寄れる山」の地図（2026-11-16）
   [data-smap] の枠に、data-smap の JSON（{s:{n,la,lo}, m:[{n,la,lo,t}]}）を描く。サウナは橙、山の登山口・駐車場は緑、間を点線で結ぶ。
   地図の部品（Leaflet）は、地図が画面に入るまで読み込まない。地図は地理院タイル */
(function () {
  'use strict';
  var CSS = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css';
  var JS = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js';
  var els = document.querySelectorAll('[data-smap]');
  if (!els.length) { return; }
  var loading = null;
  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function load() {
    if (window.L) { return Promise.resolve(); }
    if (loading) { return loading; }
    loading = new Promise(function (ok, ng) {
      var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = CSS; document.head.appendChild(l);
      var s = document.createElement('script'); s.src = JS; s.onload = ok; s.onerror = ng; document.head.appendChild(s);
    });
    return loading;
  }
  function draw(el) {
    if (el.getAttribute('data-done')) { return; }
    el.setAttribute('data-done', '1');
    var d; try { d = JSON.parse(el.getAttribute('data-smap')); } catch (e) { return; }
    var L = window.L, pts = [];
    var map = L.map(el, { scrollWheelZoom: false });
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', {
      minZoom: 5, maxZoom: 18,
      attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル</a>｜サウナの位置：サウナシュラン公式サイトほか'
    }).addTo(map);
    (d.list || [d]).forEach(function (g) {
      var s = g.s;
      L.circleMarker([s.la, s.lo], { radius: 9, color: '#fff', weight: 2, fillColor: '#c8650a', fillOpacity: 1 })
        .bindTooltip(esc(s.n), { permanent: !d.list, direction: 'top', offset: [0, -8], className: 'smap-tip' }).addTo(map);
      pts.push([s.la, s.lo]);
      (g.m || []).forEach(function (m) {
        L.polyline([[m.la, m.lo], [s.la, s.lo]], { color: '#4e6535', weight: 2, dashArray: '5 6', opacity: 0.8 }).addTo(map);
        L.circleMarker([m.la, m.lo], { radius: 7, color: '#fff', weight: 2, fillColor: '#4e6535', fillOpacity: 1 })
          .bindTooltip(esc(m.n) + (m.t ? '（' + esc(m.t) + '）' : ''), { permanent: !d.list, direction: 'bottom', offset: [0, 6], className: 'smap-tip' }).addTo(map);
        pts.push([m.la, m.lo]);
      });
    });
    map.fitBounds(pts, { padding: [36, 36], maxZoom: 13 });
  }
  function go(el) { load().then(function () { draw(el); }).catch(function () {}); }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { io.unobserve(e.target); go(e.target); } });
    }, { rootMargin: '300px' });
    Array.prototype.forEach.call(els, function (el) { io.observe(el); });
  } else {
    Array.prototype.forEach.call(els, go);
  }
})();
