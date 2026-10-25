/* 山ページの「前泊の宿」欄（#sec-lodging data-mid="山ID"）。
   - 宿を探す場所（登山口へのバスが出る駅・登山口側・車を置く場所）は data/lodging_areas.json（scripts/build_lodging_areas.py が作る）。
   - 宿は、欄が画面に近づいたときに楽天トラベルの施設検索 API（SimpleHotelSearch）で、その場所から近い順に探す。
     取得した情報は保存しない（楽天ウェブサービス規約）。宿が1軒も無い場所はタブを出さず、どの場所にも無ければ欄ごと出さない。
   - リンクは楽天アフィリエイトのリンク（affiliateId を付けて API が返す hotelInformationUrl）。画像は API が返すものを加工せずに出す。
   - 上限（1つのアプリ ID につき1秒に1回）に合わせ、場所ごとに1.1秒おきに問い合わせる。
   - アプリ ID・アクセスキーは assets/js/gear-rakuten.js と同じ（許可するサイトは tozan-navi.com だけ。手元・localhost からは読めない）。 */
(function () {
  'use strict';
  var box = document.getElementById('sec-lodging');
  if (!box || !window.fetch) { return; }
  var MID = box.getAttribute('data-mid');
  var APP_ID = '8587e8eb-2e6b-4c5b-a252-bda1d325993e';
  var ACCESS_KEY = 'pk_S4w9CvEjuXKkawN67JPoz8TB39xxAZIXNyoYoLB9EBF';
  var AFF_ID = '57384242.53497bb8.57384243.366083eb';
  var API = 'https://openapi.rakuten.co.jp/engine/api/Travel/SimpleHotelSearch/20260731';
  var SHOW = 5;
  var KIND = { station: '駅の近く', trailhead: '登山口側', parking: '車を置く場所の近く' };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
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

  function search(area) {
    var url = API + '?applicationId=' + encodeURIComponent(APP_ID) + '&accessKey=' + encodeURIComponent(ACCESS_KEY)
      + '&affiliateId=' + encodeURIComponent(AFF_ID) + '&format=json&formatVersion=2&datumType=1'
      + '&latitude=' + area.lat + '&longitude=' + area.lng + '&searchRadius=' + area.radiusKm + '&hits=' + SHOW;
    return window.fetch(url, { credentials: 'omit' }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (res) {
        var out = [];
        var hs = (res && res.hotels) || [];
        for (var i = 0; i < hs.length; i++) {
          var b = info(hs[i]);
          if (b && b.hotelName && b.hotelInformationUrl) { out.push(b); }
        }
        return out;
      }, function () { return []; });
  }

  function card(b, area) {
    var d = (b.latitude && b.longitude) ? km(area.lat, area.lng, Number(b.latitude), Number(b.longitude)) : null;
    var dist = d == null ? '' : (d < 1 ? '約' + Math.max(100, Math.round(d * 10) * 100) + 'm' : '約' + (Math.round(d * 10) / 10) + 'km');
    var meta = [];
    if (dist) { meta.push(esc(area.name) + 'から' + dist + '（直線）'); }
    if (b.hotelMinCharge) { meta.push('最安料金 ' + Number(b.hotelMinCharge).toLocaleString('ja-JP') + '円〜'); }
    if (b.reviewAverage && b.reviewCount) { meta.push('評価 ' + esc(b.reviewAverage) + '（' + esc(b.reviewCount) + '件）'); }
    var ga = "if(window.gtag){gtag('event','lodging_click',{mountain_id:'" + MID + "',area:'" + esc(area.name).replace(/'/g, '') + "',hotel_no:'" + esc(b.hotelNo) + "'})}";
    var img = b.hotelThumbnailUrl ? '<img src="' + esc(b.hotelThumbnailUrl) + '" alt="" loading="lazy" class="ld-img">' : '<span class="ld-img"></span>';
    return '<a class="ld-item" href="' + esc(b.hotelInformationUrl) + '" target="_blank" rel="nofollow sponsored noopener" onclick="' + ga + '">'
      + img + '<span class="ld-body"><span class="ld-name">' + esc(b.hotelName) + '</span>'
      + '<span class="ld-meta">' + meta.join('<br>') + '</span></span></a>';
  }

  function render(found) {
    if (!found.length) { return; }
    var tabs = '', panes = '';
    for (var i = 0; i < found.length; i++) {
      var f = found[i], a = f.area;
      tabs += '<button type="button" class="ld-tab' + (i ? '' : ' on') + '" data-i="' + i + '">' + esc(a.name) + '<small>' + KIND[a.kind] + '</small></button>';
      var list = '';
      for (var j = 0; j < f.hotels.length; j++) { list += card(f.hotels[j], a); }
      panes += '<div class="ld-pane"' + (i ? ' hidden' : '') + ' data-i="' + i + '">'
        + '<p class="ld-why">' + esc(a.name) + '：' + esc(a.via) + '。直線' + a.radiusKm + 'km以内の宿を近い順に出しています。</p>' + list + '</div>';
    }
    var body = box.querySelector('.ld-content');
    body.innerHTML = (found.length > 1 ? '<div class="ld-tabs">' + tabs + '</div>' : '') + panes
      + '<p class="ld-note">宿は楽天トラベルに載っているものです。空室・料金・送迎や朝食の時間は、楽天トラベルと宿の案内で確かめてください。当サイトは楽天アフィリエイトを利用しています。</p>'
      + '<p class="ld-credit"><a href="https://developers.rakuten.com/" target="_blank">Supported by Rakuten Developers</a></p>';
    var bs = body.querySelectorAll('.ld-tab');
    for (var k = 0; k < bs.length; k++) {
      bs[k].addEventListener('click', function () {
        var n = this.getAttribute('data-i');
        for (var x = 0; x < bs.length; x++) { bs[x].className = 'ld-tab' + (bs[x] === this ? ' on' : ''); }
        var ps = body.querySelectorAll('.ld-pane');
        for (var y = 0; y < ps.length; y++) { ps[y].hidden = ps[y].getAttribute('data-i') !== n; }
      });
    }
    box.hidden = false;
  }

  function start() {
    window.fetch('/data/lodging_areas.json', { credentials: 'omit' }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        var m = d && d.mountains && d.mountains[MID];
        if (!m) { return; }
        var areas = [];
        for (var i = 0; i < m.areas.length; i++) { if (m.areas[i].lat != null && !m.areas[i].needsVerification) { areas.push(m.areas[i]); } }
        var found = [], idx = 0;
        function step() {
          if (idx >= areas.length) { render(found); return; }
          var a = areas[idx++];
          search(a).then(function (hs) {
            if (hs.length) { found.push({ area: a, hotels: hs }); }
            setTimeout(step, 1100);
          });
        }
        step();
      }, function () {});
  }

  // 欄（隠してある）の位置は、すぐ前の「登山口・駐車場」の欄で見る
  var target = document.getElementById('sec-parking') || box;
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      for (var i = 0; i < es.length; i++) { if (es[i].isIntersecting) { io.disconnect(); start(); return; } }
    }, { rootMargin: '600px 0px' });
    io.observe(target);
  } else {
    start();
  }
})();
