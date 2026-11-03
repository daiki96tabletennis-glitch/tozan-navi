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
})();
