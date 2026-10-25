/* 前泊の宿のページ（/stay/<山ID>/。scripts/gen_stay_pages.py が作る）。
   window.YM_STAY = {mid, name, areas:[{name, kind, lat, lng, r(半径km)}]}
   - 場所ごとの枠（[data-st-hotels="i"]）に、楽天トラベルの施設検索 API（SimpleHotelSearch）で近い宿を5軒まで、距離つきで出す。
     取得した情報は保存しない（楽天ウェブサービス規約）。読めないときは何も出さない（楽天トラベルのページへのリンクは残る）。
   - 宿ごとに：名前（楽天トラベルの宿のページ）、乗り換える場所からの直線距離、宿が楽天トラベルに書いている「アクセス」（駅からの徒歩の分数など。駅の周りの宿だけ）、
     温泉（楽天トラベルの「温泉」の条件で検索し直して、出てきた宿にだけ印を付ける）、最安料金、評価、「楽天トラベルで空室・料金を見る」（宿泊プランの一覧）。
   - 土曜泊の料金：出した宿について、楽天トラベルの空室検索 API（VacantHotelSearch）で、直近4回の土曜泊（大人1人・1室）を調べ、
     空室のある日のうち最安の料金とその日付を出す（宿ごとに安いプランが1つ返る）。4回とも空室が無ければ「空室なし」と出す。宿は15軒まで1回で調べる。
   - 楽天トラベルのページが無い場所（data-api-only）は、宿が見つかったときだけ枠を出す。
   - 上限（1つのアプリ ID につき1秒に1回）に合わせ、場所ごとに1.1秒おきに問い合わせる。
   - 地図（#smap）：場所と、見つかった宿の位置。Leaflet＋地理院タイル（地図が画面に近づくまで読み込まない）。
   - アプリ ID・アクセスキーは assets/js/gear-rakuten.js と同じ（許可するサイトは tozan-navi.com だけ。手元・localhost からは読めない）。
     アプリの「使える API」に楽天トラベルが入っていないと 403 になる。 */
(function () {
  'use strict';
  var S = window.YM_STAY;
  if (!S || !S.areas || !S.areas.length) { return; }
  var APP_ID = '8587e8eb-2e6b-4c5b-a252-bda1d325993e';
  var ACCESS_KEY = 'pk_S4w9CvEjuXKkawN67JPoz8TB39xxAZIXNyoYoLB9EBF';
  var AFF_ID = '57384242.53497bb8.57384243.366083eb';
  var API = 'https://openapi.rakuten.co.jp/engine/api/Travel/SimpleHotelSearch/20260731';
  var VAC = 'https://openapi.rakuten.co.jp/engine/api/Travel/VacantHotelSearch/20170426';
  var SATS = 4;
  var shownNos = [];
  var SHOW = 5;
  var found = []; // 地図に出す宿 [{la, lo, n, u}]
  var map = null, hotelLayer = null;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  // 楽天の宿名・アクセスの文は全角の英数字・空白が多いので、表示のときだけ半角にそろえる（文の中身は変えない）
  function nk(t) {
    t = String(t == null ? '' : t);
    try { t = t.normalize('NFKC'); } catch (e) {}
    return t.replace(/\s+/g, ' ').replace(/^ | $/g, '');
  }
  function km(a, b, c, d) {
    var r = Math.PI / 180, x = Math.sin((c - a) * r / 2), y = Math.sin((d - b) * r / 2);
    var h = x * x + Math.cos(a * r) * Math.cos(c * r) * y * y;
    return 12742 * Math.asin(Math.sqrt(h));
  }
  function info(h) {
    // formatVersion=2 では hotels[i] が [ {hotelBasicInfo}, ... ] の配列
    var arr = Array.isArray(h) ? h : (h && h.hotel) || [];
    for (var i = 0; i < arr.length; i++) { if (arr[i] && arr[i].hotelBasicInfo) { return arr[i].hotelBasicInfo; } }
    return null;
  }

  function query(a, extra) {
    if (!window.fetch) { return Promise.resolve([]); }
    var url = API + '?applicationId=' + encodeURIComponent(APP_ID) + '&accessKey=' + encodeURIComponent(ACCESS_KEY)
      + '&affiliateId=' + encodeURIComponent(AFF_ID) + '&format=json&formatVersion=2&datumType=1'
      + '&latitude=' + a.lat + '&longitude=' + a.lng + '&searchRadius=' + a.r + extra;
    return window.fetch(url, { credentials: 'omit' }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (res) {
        var out = [], hs = (res && res.hotels) || [];
        for (var i = 0; i < hs.length; i++) {
          var b = info(hs[i]);
          if (b && b.hotelName && b.hotelInformationUrl) { out.push(b); }
        }
        return out;
      }, function () { return []; });
  }
  // 近い順の5軒と、同じ範囲の温泉の宿（楽天トラベルの「温泉」の条件。近い順に30軒）。温泉の検索は上限に合わせて1.1秒あける
  function search(a) {
    return query(a, '&hits=' + SHOW).then(function (hs) {
      if (!hs.length) { return hs; }
      return new Promise(function (ok) { setTimeout(ok, 1100); }).then(function () {
        return query(a, '&hits=30&squeezeCondition=onsen');
      }).then(function (on) {
        var set = {};
        for (var i = 0; i < on.length; i++) { set[on[i].hotelNo] = 1; }
        for (var j = 0; j < hs.length; j++) { hs[j].ymOnsen = !!set[hs[j].hotelNo]; }
        return hs;
      });
    });
  }
  // 楽天のアフィリエイトのリンク。API が返したリンクがすでにアフィリエイトのリンクならそのまま
  function aff(u) {
    if (!u) { return ''; }
    if (u.indexOf('hb.afl.rakuten.co.jp') >= 0) { return u; }
    var q = encodeURIComponent(u);
    return 'https://hb.afl.rakuten.co.jp/hgc/' + AFF_ID + '/?pc=' + q + '&m=' + q;
  }

  function item(b, a) {
    var la = Number(b.latitude), lo = Number(b.longitude);
    var d = (la && lo) ? km(a.lat, a.lng, la, lo) : null;
    var dist = d == null ? '' : (d < 1 ? '約' + Math.max(100, Math.round(d * 10) * 100) + 'm' : '約' + (Math.round(d * 10) / 10) + 'km');
    var meta = [];
    if (dist) { meta.push(esc(a.name) + 'から<b>' + dist + '</b>（直線）'); }
    // アクセスの文（駅から徒歩◯分など）は駅の周りの宿だけ。登山口・駐車場の周りでは、最寄り駅からの道順は要らない
    if (b.access && a.kind === 'station') {
      var ac = nk(b.access);
      meta.push('<span class="st-acc">' + esc(ac.length > 70 ? ac.slice(0, 70) + '…' : ac) + '</span>');
    }
    var price = [];
    if (b.hotelMinCharge) { price.push('最安料金 <b>' + Number(b.hotelMinCharge).toLocaleString('ja-JP') + '</b>円〜'); }
    if (b.reviewAverage && b.reviewCount) { price.push('評価 <b>' + esc(b.reviewAverage) + '</b>（' + esc(b.reviewCount) + '件）'); }
    if (price.length) { meta.push(price.join('　')); }
    meta.push('<span class="st-sat" data-st-sat="' + esc(b.hotelNo) + '">土曜泊の料金を調べています…</span>');
    if (shownNos.indexOf(b.hotelNo) < 0) { shownNos.push(b.hotelNo); }
    var infoUrl = aff(b.hotelInformationUrl), planUrl = aff(b.planListUrl || b.hotelInformationUrl);
    if (la && lo) { found.push({ la: la, lo: lo, n: nk(b.hotelName), u: infoUrl }); }
    var ga = function (kind) {
      return "if(window.gtag){gtag('event','lodging_click',{mountain_id:'" + esc(S.mid) + "',area:'" + esc(a.name).replace(/'/g, '') + "',hotel_no:'" + esc(b.hotelNo) + "',link:'" + kind + "'})}";
    };
    var lk = ' target="_blank" rel="nofollow sponsored noopener"';
    var img = b.hotelThumbnailUrl ? '<img src="' + esc(b.hotelThumbnailUrl) + '" alt="" loading="lazy" class="st-img">' : '<span class="st-img"></span>';
    return '<div class="st-item"><a class="st-imgw" href="' + esc(infoUrl) + '"' + lk + ' onclick="' + ga('img') + '" tabindex="-1" aria-hidden="true">' + img + '</a>'
      + '<div class="st-ib"><a class="st-name" href="' + esc(infoUrl) + '"' + lk + ' onclick="' + ga('name') + '">' + esc(nk(b.hotelName)) + '</a>'
      + (b.ymOnsen ? '<span class="st-onsen">温泉</span>' : '')
      + '<span class="st-meta">' + meta.join('<br>') + '</span>'
      + '<a class="st-plan" href="' + esc(planUrl) + '"' + lk + ' onclick="' + ga('plan') + '">楽天トラベルで空室・料金を見る →</a></div></div>';
  }

  function fill(i, a, hs) {
    if (!hs.length) { return; }
    var box = document.querySelector('[data-st-hotels="' + i + '"]');
    var sec = document.querySelector('[data-st-area="' + i + '"]');
    if (!box || !sec) { return; }
    var html = '<p class="st-hh">' + esc(a.name) + 'から近い順（直線' + a.r + 'km以内・楽天トラベル）</p>';
    for (var j = 0; j < hs.length; j++) { html += item(hs[j], a); }
    box.innerHTML = html;
    sec.hidden = false;
    var cr = document.getElementById('st-credit');
    if (cr) { cr.hidden = false; }
    drawHotels();
  }

  // ---- 土曜泊の料金（空室検索） ----
  function ymd(d) {
    var m = d.getMonth() + 1, dd = d.getDate();
    return d.getFullYear() + '-' + (m < 10 ? '0' : '') + m + '-' + (dd < 10 ? '0' : '') + dd;
  }
  function saturdays() {
    var out = [], d = new Date();
    d.setHours(12, 0, 0, 0);
    d.setDate(d.getDate() + 1);
    while (d.getDay() !== 6) { d.setDate(d.getDate() + 1); }
    for (var i = 0; i < SATS; i++) { out.push(new Date(d.getTime())); d.setDate(d.getDate() + 7); }
    return out;
  }
  function vacant(sat) {
    var next = new Date(sat.getTime());
    next.setDate(next.getDate() + 1);
    var url = VAC + '?applicationId=' + encodeURIComponent(APP_ID) + '&accessKey=' + encodeURIComponent(ACCESS_KEY)
      + '&affiliateId=' + encodeURIComponent(AFF_ID) + '&format=json&formatVersion=2&hits=30&adultNum=1&roomNum=1&searchPattern=0'
      + '&hotelNo=' + shownNos.slice(0, 15).join(',') + '&checkinDate=' + ymd(sat) + '&checkoutDate=' + ymd(next);
    return window.fetch(url, { credentials: 'omit' }).then(function (r) { return r.status === 404 ? { hotels: [] } : (r.ok ? r.json() : null); })
      .then(function (res) {
        if (!res) { return null; }
        var out = {}, hs = res.hotels || [];
        for (var i = 0; i < hs.length; i++) {
          var parts = Array.isArray(hs[i]) ? hs[i] : (hs[i].hotel || []), no = null, min = null;
          for (var j = 0; j < parts.length; j++) {
            if (parts[j].hotelBasicInfo) { no = parts[j].hotelBasicInfo.hotelNo; }
            var ri = parts[j].roomInfo || [];
            for (var k = 0; k < ri.length; k++) {
              var dc = ri[k].dailyCharge;
              if (dc && dc.total && (min == null || dc.total < min)) { min = dc.total; }
            }
          }
          if (no != null && min != null) { out[no] = min; }
        }
        return out;
      }, function () { return null; });
  }
  function weekend() {
    if (!shownNos.length) { return; }
    var sats = saturdays(), best = {}, ok = 0, i = 0;
    function step() {
      if (i >= sats.length) { show(); return; }
      var sat = sats[i++];
      vacant(sat).then(function (res) {
        if (res) {
          ok++;
          for (var no in res) {
            if (!best[no] || res[no] < best[no].p) { best[no] = { p: res[no], d: sat }; }
          }
        }
        setTimeout(step, 1100);
      });
    }
    function show() {
      var els = document.querySelectorAll('[data-st-sat]');
      for (var j = 0; j < els.length; j++) {
        var b = best[els[j].getAttribute('data-st-sat')];
        if (!ok) { els[j].parentNode.removeChild(els[j].previousSibling); els[j].parentNode.removeChild(els[j]); continue; }
        els[j].innerHTML = b
          ? '土曜泊（大人1人）<b>' + b.p.toLocaleString('ja-JP') + '</b>円〜（' + (b.d.getMonth() + 1) + '/' + b.d.getDate() + '泊）'
          : '直近' + SATS + '回の土曜泊は、楽天トラベルに大人1人の空室なし';
        els[j].className = 'st-sat' + (b ? '' : ' none');
      }
    }
    step();
  }

  function run() {
    var i = 0;
    function step() {
      if (i >= S.areas.length) { setTimeout(weekend, 1100); return; }
      var k = i++, a = S.areas[k];
      search(a).then(function (hs) { fill(k, a, hs); setTimeout(step, 1100); });
    }
    step();
  }

  // ---- 地図 ----
  var el = document.getElementById('smap');
  function drawHotels() {
    if (!map || !window.L) { return; }
    if (hotelLayer) { map.removeLayer(hotelLayer); }
    hotelLayer = window.L.layerGroup();
    for (var i = 0; i < found.length; i++) {
      var p = found[i];
      var m = window.L.circleMarker([p.la, p.lo], { radius: 6, color: '#fff', weight: 2, fillColor: '#b4532a', fillOpacity: 1 });
      m.bindPopup('<b><a href="' + esc(p.u) + '" target="_blank" rel="nofollow sponsored noopener">' + esc(p.n) + '</a></b>');
      m.addTo(hotelLayer);
    }
    hotelLayer.addTo(map);
  }
  function draw() {
    var L = window.L, pts = [];
    map = L.map(el, { scrollWheelZoom: false });
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', {
      minZoom: 5, maxZoom: 18,
      attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル</a>'
    }).addTo(map);
    for (var i = 0; i < S.areas.length; i++) {
      var a = S.areas[i];
      L.circle([a.lat, a.lng], { radius: a.r * 1000, color: '#4e6535', weight: 1, fillColor: '#4e6535', fillOpacity: 0.06 }).addTo(map);
      L.marker([a.lat, a.lng], {
        icon: L.divIcon({ className: 'stpin', html: '<b>' + esc(a.name) + '</b>', iconSize: [120, 22], iconAnchor: [60, 11] }),
        keyboard: false
      }).addTo(map);
      pts.push([a.lat, a.lng]);
    }
    if (pts.length === 1) { map.setView(pts[0], 13); } else { map.fitBounds(pts, { padding: [36, 36], maxZoom: 13 }); }
    map.on('click', function () { map.scrollWheelZoom.enable(); });
    drawHotels();
  }
  function loadMap() {
    if (map || !el) { return; }
    var css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css';
    document.head.appendChild(css);
    var js = document.createElement('script');
    js.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js';
    js.onload = draw;
    document.head.appendChild(js);
  }
  if (el) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (es) {
        for (var i = 0; i < es.length; i++) { if (es[i].isIntersecting) { io.disconnect(); loadMap(); return; } }
      }, { rootMargin: '300px 0px' });
      io.observe(el);
    } else {
      loadMap();
    }
  }
  run();
})();
