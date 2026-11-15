/* 記事「登山のあとの温泉・サウナ」：楽天トラベルに載っている宿の写真（2026-11-15）
   - 枠 [data-rk-hotel="施設番号"] に、楽天トラベルの施設検索 API（SimpleHotelSearch）の画像（hotelImageUrl）を、
     楽天トラベルの宿のページ（アフィリエイトのリンク）へのリンクつきで出す。取得した情報は保存しない
   - 画像を出したら、楽天の決まりのクレジット（Supported by Rakuten Developers）を写真の下に出す
   - 読めないとき（API の制限・手元の確認など）は、枠を出さないまま */
(function () {
  'use strict';
  var APP_ID = '8587e8eb-2e6b-4c5b-a252-bda1d325993e';
  var ACCESS_KEY = 'pk_S4w9CvEjuXKkawN67JPoz8TB39xxAZIXNyoYoLB9EBF';
  var AFF_ID = '57384242.53497bb8.57384243.366083eb';
  var API = 'https://openapi.rakuten.co.jp/engine/api/Travel/SimpleHotelSearch/20260731';
  var boxes = document.querySelectorAll('[data-rk-hotel]');
  if (!boxes.length || !window.fetch) { return; }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function info(h) {
    var arr = Array.isArray(h) ? h : (h && h.hotel) || [];
    for (var i = 0; i < arr.length; i++) { if (arr[i] && arr[i].hotelBasicInfo) { return arr[i].hotelBasicInfo; } }
    return null;
  }
  Array.prototype.forEach.call(boxes, function (box, k) {
    var no = box.getAttribute('data-rk-hotel');
    var url = API + '?applicationId=' + encodeURIComponent(APP_ID) + '&accessKey=' + encodeURIComponent(ACCESS_KEY)
      + '&affiliateId=' + encodeURIComponent(AFF_ID) + '&format=json&formatVersion=2&hotelNo=' + encodeURIComponent(no);
    setTimeout(function () {
      window.fetch(url, { credentials: 'omit' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (res) {
        var b = res && res.hotels && res.hotels.length ? info(res.hotels[0]) : null;
        if (!b || !b.hotelImageUrl) { return; }
        var link = b.hotelInformationUrl || ('https://travel.rakuten.co.jp/HOTEL/' + no + '/');
        box.innerHTML = '<a href="' + esc(link) + '" target="_blank" rel="sponsored noopener"><img src="' + esc(b.hotelImageUrl) + '" alt="' + esc(box.getAttribute('data-rk-name')) + '（楽天トラベル）" loading="lazy"></a>'
          + '<div class="os-rk-cap">写真：<a href="' + esc(link) + '" target="_blank" rel="sponsored noopener">楽天トラベル</a>（宿の写真）　'
          + '<a href="https://developers.rakuten.com/" target="_blank" rel="noopener">Supported by Rakuten Developers</a></div>';
        box.hidden = false;
      }).catch(function () {});
    }, k * 1100);
  });
})();
