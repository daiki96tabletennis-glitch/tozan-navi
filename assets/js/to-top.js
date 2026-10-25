// 一番上へ戻るボタン（2026-10-25〜。トップ・山ページ・記事・まとめ）
// 少しでもスクロールしたら、右下に半透明の ⇧ ボタンを出す。押すとページの一番上へ戻る。
// 画面の下に固定のバー（下のメニューなど）があるときは、その上に出す。
(function(){
  if (window.__ymToTop) return;
  window.__ymToTop = true;

  var css = '' +
    '.ym-to-top{position:fixed;right:14px;bottom:20px;z-index:900;width:44px;height:44px;border-radius:50%;' +
    'display:flex;align-items:center;justify-content:center;padding:0;cursor:pointer;' +
    'background:rgba(255,255,255,0.55);border:1px solid rgba(60,70,50,0.18);color:#3a5028;' +
    '-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);box-shadow:0 2px 10px rgba(0,0,0,0.12);' +
    'opacity:0;transform:translateY(8px);pointer-events:none;transition:opacity .2s ease,transform .2s ease;' +
    '-webkit-tap-highlight-color:transparent;}' +
    '.ym-to-top.show{opacity:1;transform:none;pointer-events:auto;}' +
    '.ym-to-top:active{transform:scale(0.92);}' +
    '@media print{.ym-to-top{display:none}}';
  var st = document.createElement('style');
  st.textContent = css;
  document.head.appendChild(st);

  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'ym-to-top';
  btn.setAttribute('aria-label', 'ページの一番上へ戻る');
  btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V6"/><path d="M6 11l6-6 6 6"/></svg>';
  btn.addEventListener('click', function(){
    try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (e) { window.scrollTo(0, 0); }
  });

  // 画面の下に固定されたバー（幅が画面の半分以上）の高さを測って、その上に出す
  function place(){
    var h = window.innerHeight, lift = 0;
    var els = document.body.querySelectorAll('nav, footer, div, header');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el === btn) continue;
      var cs = window.getComputedStyle(el);
      if (cs.position !== 'fixed' || cs.display === 'none' || cs.visibility === 'hidden') continue;
      var r = el.getBoundingClientRect();
      if (r.height <= 0 || r.height > h * 0.4) continue;
      if (r.bottom < h - 2 || r.width < window.innerWidth * 0.5) continue;
      lift = Math.max(lift, h - r.top);
    }
    btn.style.bottom = (lift > 0 ? Math.round(lift + 12) : 20) + 'px';
  }

  var shown = false, lastPlace = 0;
  function onScroll(){
    var y = window.pageYOffset || document.documentElement.scrollTop || 0;
    var want = y > 40;
    var now = Date.now();
    // 下に出たり消えたりするバーがあるので、表示中もときどき位置を測り直す
    if (want && (want !== shown || now - lastPlace > 400)) { lastPlace = now; place(); }
    if (want !== shown) {
      shown = want;
      btn.classList.toggle('show', want);
    }
  }

  function start(){
    document.body.appendChild(btn);
    place();
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', place);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
