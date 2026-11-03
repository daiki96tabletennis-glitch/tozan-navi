/* サイト共通の計測（GA4。2026-11-03〜）
 * - pwa_launch：ホーム画面に追加したアプリとして開いたとき、訪問（セッション）ごとに1回
 *   （ホーム追加率の目安＝この計測のある人 ÷ 訪れた人）
 * - pwa_installed：Android の Chrome などで「アプリをインストール」したとき（iPhone は通知が無いので数えられない）
 * どのページでも GA4 のタグ（gtag）の後に読む。個人を特定する情報は送らない。
 */
(function () {
  if (typeof window.gtag !== 'function') return;
  var ua = navigator.userAgent || '';
  var platform = /iPad|iPhone|iPod/.test(ua) ? 'ios' : (/Android/.test(ua) ? 'android' : 'other');
  var standalone = false;
  try {
    standalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || window.navigator.standalone === true;
  } catch (e) {}
  if (standalone) {
    var done = false;
    try { done = sessionStorage.getItem('ym_pwa_launch') === '1'; } catch (e) {}
    if (!done) {
      try { sessionStorage.setItem('ym_pwa_launch', '1'); } catch (e) {}
      window.gtag('event', 'pwa_launch', { platform: platform });
    }
  }
  window.addEventListener('appinstalled', function () {
    window.gtag('event', 'pwa_installed', { platform: platform });
  });

  // 「登山口の近く（PR）」の掲載枠（山ページ。data/listings.json）
  // - 期限（data-valid-to）を過ぎた掲載は、ページを作り直す前でも隠す
  // - listing_view：枠が画面に半分以上入ったとき（ページごとに1回）／listing_click：公式サイトへのリンクを押したとき
  function setupListings() {
    var els = document.querySelectorAll('.ym-listing[data-listing-id]');
    if (!els.length) return;
    var d = new Date();
    var today = d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
    var live = [];
    Array.prototype.forEach.call(els, function (el) {
      var to = el.getAttribute('data-valid-to');
      if (to && to < today) { el.style.display = 'none'; return; }
      live.push(el);
      var a = el.querySelector('a.ym-listing-link');
      if (a) a.addEventListener('click', function () {
        window.gtag('event', 'listing_click', {
          listing_id: el.getAttribute('data-listing-id'), mountain_id: el.getAttribute('data-mountain-id'), transport_type: 'beacon'
        });
      });
    });
    if (!live.length || !('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) {
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        window.gtag('event', 'listing_view', {
          listing_id: en.target.getAttribute('data-listing-id'), mountain_id: en.target.getAttribute('data-mountain-id')
        });
      });
    }, { threshold: 0.5 });
    live.forEach(function (el) { io.observe(el); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setupListings);
  else setupListings();
})();
