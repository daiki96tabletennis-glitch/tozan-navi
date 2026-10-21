/* 海外登山ギアのページ（/gear/）：楽天市場の商品画像を、楽天ウェブサービスの商品検索 API から、ページを開いたときに読み込んで出す。
   - 画像の枠 data-rk-code="ショップ:商品番号"（/gear/ の商品カード .item-visual）に、128×128 の画像（mediumImageUrls）を
     楽天アフィリエイトのリンク（affiliateUrl）付きで入れる。画像は加工しない・サイズを変えない（楽天のルール）。
   - 取得した情報は保存しない（楽天ウェブサービス規約 第10条）。読めなかったときは今のアイコンのまま。
   - 同じ商品が楽天市場に無いときは、似た商品を出す（data-rk-similar="1"。画像の下に「楽天市場で買える似た商品」と楽天の商品名を出し、同じ商品に見せない）。
   - 画像の枠が無かったカードには、隠した枠（hidden）を置いてあり、画像が出たときだけ見せる。
   - 楽天の決まりのクレジット表示（Supported by Rakuten Developers）を、画像を出したページの下に1回だけ出す。
   - アプリ ID・アクセスキーは楽天ウェブサービスで「許可するサイト」を tozan-navi.com に限ったもの（ほかのサイトからは使えない）。
   - API は送り元（Origin ヘッダー）でサイトを確かめる。script タグ（JSONP）では Origin が送られず 403 になるので fetch で読む。 */
(function () {
  'use strict';
  var APP_ID = '8587e8eb-2e6b-4c5b-a252-bda1d325993e';
  var ACCESS_KEY = 'pk_S4w9CvEjuXKkawN67JPoz8TB39xxAZIXNyoYoLB9EBF'; // 楽天ウェブサービスのアクセスキー（空にすると何もしない）
  var AFF_ID = '57384242.53497bb8.57384243.366083eb';
  var API = 'https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701';
  if (!ACCESS_KEY) { return; }

  var shown = 0;

  function credit() {
    if (!shown || document.getElementById('rk-credit')) { return; }
    var p = document.createElement('p');
    p.id = 'rk-credit';
    p.style.cssText = 'text-align:center;font-size:11px;margin:18px 0 8px';
    // 楽天ウェブサービスのクレジット表示（提供された HTML をそのまま使う）
    p.innerHTML = '<a href="https://developers.rakuten.com/" target="_blank">Supported by Rakuten Developers</a>';
    // 横に並ぶ枠（.gear-cards-scroll）の中で出したときは、その枠のすぐ下に出す。ほかはページの下
    var first = document.querySelector('.item-visual-rakuten');
    var row = first && first.closest ? first.closest('.gear-cards-scroll') : null;
    if (row && row.parentNode) {
      p.style.cssText = 'text-align:right;font-size:10.5px;margin:4px 4px 0';
      row.parentNode.insertBefore(p, row.nextSibling);
      return;
    }
    var main = document.querySelector('main') || document.body;
    main.appendChild(p);
  }

  // 楽天ウェブサービスの上限（1つのアプリ ID につき1秒に1回）に合わせ、画面に近づいた枠から順に1件ずつ、1.1秒おきに問い合わせる。
  // 混み合って断られた（429 など）枠は、1回だけ少しあとに問い合わせ直し、それでも読めなければアイコンのまま
  var queue = [], busy = false;
  function next() {
    if (busy || !queue.length) { return; }
    busy = true;
    load(queue.shift());
  }
  function done() {
    credit();
    setTimeout(function () { busy = false; next(); }, 1100);
  }
  function want(box) {
    if (box.getAttribute('data-rk-q')) { return; }
    box.setAttribute('data-rk-q', '1');
    queue.push(box);
    next();
  }

  function load(box) {
    var code = box.getAttribute('data-rk-code');
    var url = API + '?applicationId=' + encodeURIComponent(APP_ID) + '&accessKey=' + encodeURIComponent(ACCESS_KEY)
      + '&affiliateId=' + encodeURIComponent(AFF_ID) + '&itemCode=' + encodeURIComponent(code)
      + '&format=json&formatVersion=2&hits=1&imageFlag=1&elements=itemName,itemUrl,affiliateUrl,mediumImageUrls';
    if (!window.fetch) { done(); return; }
    window.fetch(url, { credentials: 'omit' }).then(function (r) {
      if (r.status === 429 && !box.getAttribute('data-rk-retry')) { box.setAttribute('data-rk-retry', '1'); setTimeout(function () { queue.push(box); next(); }, 3000); return null; }
      return r.ok ? r.json() : null;
    }).then(function (res) {
      try {
        var it = res && res.Items && res.Items[0] && (res.Items[0].Item || res.Items[0]);
        var img = it && it.mediumImageUrls && it.mediumImageUrls[0];
        var src = img && (img.imageUrl || img);
        var href = it && (it.affiliateUrl || it.itemUrl);
        if (src && href) {
          var a = document.createElement('a');
          a.href = href;
          a.target = '_blank';
          a.rel = 'nofollow sponsored noopener';
          var im = document.createElement('img');
          im.src = src;
          im.width = 128;
          im.height = 128;
          im.alt = it.itemName ? String(it.itemName).slice(0, 60) : '';
          im.loading = 'lazy';
          a.appendChild(im);
          box.innerHTML = '';
          box.className = box.className + ' item-visual-rakuten';
          box.appendChild(a);
          if (box.getAttribute('data-rk-similar') === '1') {
            var cap = document.createElement('div');
            cap.className = 'item-visual-rk-cap';
            cap.textContent = '楽天市場で買える似た商品：' + (it.itemName ? String(it.itemName).slice(0, 40) : '');
            box.appendChild(cap);
          }
          box.hidden = false;
          shown++;
        }
      } catch (e) {}
      done();
    }, function () { done(); });
  }

  var io = ('IntersectionObserver' in window) ? new IntersectionObserver(function (es) {
    for (var k = 0; k < es.length; k++) {
      if (es[k].isIntersecting) { io.unobserve(es[k].target); want(es[k].target.__rkBox || es[k].target); }
    }
  }, { rootMargin: '400px 400px' }) : null;

  // 枠を探して見張る。あとから描いた枠は、描いたあとに window.ymRakutenScan() を呼ぶと読み込む
  function scan() {
    var boxes = document.querySelectorAll('[data-rk-code]');
    for (var i = 0; i < boxes.length; i++) {
      var b = boxes[i];
      if (b.getAttribute('data-rk-seen')) { continue; }
      b.setAttribute('data-rk-seen', '1');
      if (!io) { want(b); continue; }
      // 隠した枠（hidden）は大きさが無く画面に入ったか分からないので、親のカードで見る
      var t = b.hidden ? (b.parentNode || b) : b;
      t.__rkBox = b;
      io.observe(t);
    }
  }
  window.ymRakutenScan = scan;
  scan();
})();
