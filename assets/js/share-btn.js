/* 記事・まとめの共有ボタン（2026-11-16。運営者の指示「簡易的なもので iOS 共有ボタンのみ・ヘッダーとフッターに」）
   - ヘッダー（.ym-site-header）の右と、ページの下（footer の前。footer が無いページは main の後ろ）に、
     iOS の共有の形のアイコン（Lucide「share」。ISC License）のボタンを出す
   - 押すと端末の共有（navigator.share。題名と URL）。使えない端末では URL をコピーして「リンクをコピーしました」と出す
   - 計測：GA4 の share_click（place＝header／footer、method＝native／copy） */
(function () {
  'use strict';
  if (document.querySelector('.ym-share')) { return; }
  var ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    + '<path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" x2="12" y1="2" y2="15"/></svg>';
  function title() {
    var t = document.querySelector('meta[property="og:title"]');
    return (t && t.getAttribute('content')) || document.title;
  }
  function url() {
    var c = document.querySelector('link[rel="canonical"]');
    return (c && c.getAttribute('href')) || location.href.split('#')[0];
  }
  function toast(msg) {
    var d = document.createElement('div');
    d.textContent = msg;
    d.setAttribute('role', 'status');
    d.style.cssText = 'position:fixed;left:50%;bottom:90px;transform:translateX(-50%);background:rgba(40,48,32,.92);color:#fff;font-size:13px;font-weight:700;padding:9px 16px;border-radius:20px;z-index:9999;pointer-events:none';
    document.body.appendChild(d);
    setTimeout(function () { d.parentNode && d.parentNode.removeChild(d); }, 1800);
  }
  function track(place, method) {
    try { if (window.gtag) { window.gtag('event', 'share_click', { place: place, method: method, page_path: location.pathname }); } } catch (e) {}
  }
  function share(place) {
    var data = { title: title(), url: url() };
    if (navigator.share) {
      navigator.share(data).then(function () { track(place, 'native'); }).catch(function () {});
      return;
    }
    var done = function () { toast('リンクをコピーしました'); track(place, 'copy'); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(data.url).then(done, function () { window.prompt('このページのURL', data.url); });
    } else {
      window.prompt('このページのURL', data.url);
    }
  }
  // ヘッダー：右端に丸いアイコンのボタン
  var inner = document.querySelector('.ym-site-header > div') || document.querySelector('.ym-site-header');
  if (inner) {
    var hb = document.createElement('button');
    hb.type = 'button';
    hb.className = 'ym-share ym-share-h';
    hb.setAttribute('aria-label', 'このページを共有');
    hb.innerHTML = ICON;
    hb.style.cssText = 'flex-shrink:0;display:inline-flex;align-items:center;justify-content:center;width:34px;height:30px;padding:0;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);color:#fff;border-radius:8px;cursor:pointer';
    hb.addEventListener('click', function () { share('header'); });
    inner.appendChild(hb);
    // 幅の狭い端末（400px 未満。iPhone の多くの機種）では、ロゴとボタンが重ならないよう、ヘッダーのボタンの文字を短くする（山を検索する→検索、記事一覧へ→記事一覧）
    if (window.innerWidth < 400) {
      inner.style.gap = '5px';
      var SHORT = { '山を検索する': '検索', '記事一覧へ': '記事一覧' };
      Array.prototype.forEach.call(inner.querySelectorAll('a'), function (a, i) {
        if (i === 0) { a.style.flexShrink = '0'; return; }   // 1つ目はロゴ（縮めない）
        var t = (a.textContent || '').trim();
        if (SHORT[t]) { a.textContent = SHORT[t]; }
        a.style.padding = '5px 8px';
      });
      hb.style.width = '30px';
    }
  }
  // ページの下：文字つきのボタン
  var box = document.createElement('div');
  box.className = 'ym-share ym-share-f';
  box.style.cssText = 'text-align:center;margin:24px 16px 8px';
  var fb = document.createElement('button');
  fb.type = 'button';
  fb.innerHTML = ICON + '<span>このページを共有する</span>';
  fb.style.cssText = 'display:inline-flex;align-items:center;gap:8px;background:#4e6535;color:#fff;border:0;border-radius:24px;padding:11px 22px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit';
  fb.addEventListener('click', function () { share('footer'); });
  box.appendChild(fb);
  var foot = document.querySelector('body > footer') || document.querySelector('footer');
  var main = document.querySelector('main');
  if (foot) { foot.parentNode.insertBefore(box, foot); }
  else if (main) { main.parentNode.insertBefore(box, main.nextSibling); }
  else { document.body.appendChild(box); }
})();
