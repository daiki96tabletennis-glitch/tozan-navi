// 診断の結果に戻る（2026-11-25〜。運営者の指示「診断から山の個別ページに行った時に、再度診断の結果ページに戻れる様にしたい」）
// 診断（山選び診断・冬の山選び診断・登山タイプ診断）で結果を出したときに、答えと結果に出た山をタブの中（sessionStorage）に預け、
// URL を「?back=1」にする（ブラウザの「戻る」でも結果を出し直せる）。
// 山ページでは、その診断の結果に出た山なら、左下に「◯◯の結果に戻る」のボタンを出す。
(function(){
  var KEY = 'ym_diag_back';
  var MAX_AGE = 24 * 3600 * 1000;
  function get(){
    try { var s = JSON.parse(sessionStorage.getItem(KEY) || 'null'); return (s && Date.now() - s.t < MAX_AGE) ? s : null; } catch (e) { return null; }
  }
  function backUrl(){
    var q = new URLSearchParams(location.search);
    var keep = new URLSearchParams();
    if (q.get('mode')) keep.set('mode', q.get('mode'));
    keep.set('back', '1');
    return location.pathname + '?' + keep.toString();
  }
  window.YMDiagBack = {
    // 結果を出したあとに呼ぶ。root の中の山ページへのリンクから山IDを集める
    save: function(kind, label, answers, root, url){
      var ids = [];
      if (root) {
        var as = root.querySelectorAll('a[href^="/mountains/"]');
        for (var i = 0; i < as.length; i++) {
          var m = as[i].getAttribute('href').match(/^\/mountains\/([^\/?#]+)/);
          if (m && ids.indexOf(m[1]) === -1) ids.push(m[1]);
        }
      }
      // 上位の山（.rc-cta のリンクの順）。2・3位をくじで選ぶ診断でも、出し直したときに同じ山にする
      var top = [];
      if (root) {
        var cs = root.querySelectorAll('.rc-cta[href^="/mountains/"]');
        for (var j = 0; j < cs.length; j++) { var mm = cs[j].getAttribute('href').match(/^\/mountains\/([^\/?#]+)/); if (mm && top.indexOf(mm[1]) === -1) top.push(mm[1]); }
      }
      this.fixedTop = null;
      var u = url || backUrl();
      try { sessionStorage.setItem(KEY, JSON.stringify({ kind: kind, label: label, url: u, ids: ids, top: top, answers: answers || null, t: Date.now() })); } catch (e) {}
      try { if (!url && history.replaceState) history.replaceState(history.state, '', u + location.hash); } catch (e) {}
    },
    // ?back=1 で開いたとき、預けた答えを返す（無ければ null）
    restore: function(kind){
      if (!/[?&]back=1(&|$)/.test(location.search)) return null;
      var s = get();
      if (!s || s.kind !== kind) return null;
      this.fixedTop = (s.top && s.top.length) ? s.top : null;
      return s.answers || {};
    },
    // pickTop3 から呼ぶ：出し直しのときは前と同じ上位の山を返す（そろわなければ null）
    pick: function(list, n){
      var f = this.fixedTop;
      if (!f) return null;
      var by = {};
      list.forEach(function(x){ by[x.m.id] = x; });
      var out = [];
      f.forEach(function(id){ if (by[id]) out.push(by[id]); });
      return out.length === Math.min(n, list.length, f.length) ? out : null;
    },
    // 登頂記録（マイページ・山ページの「登った」。localStorage ym_climbed）の山ID（2026-11-26）
    climbed: function(){
      try {
        var a = JSON.parse(localStorage.getItem('ym_climbed') || '[]');
        return a.map(function(e){ return Array.isArray(e) ? e[0] : (e && e.id); }).filter(Boolean);
      } catch (e) { return []; }
    },
    // 1位に登頂済みの山を出さない：並びのうち、登っていない最初の山を先頭に移す（全部登っていればそのまま）
    notClimbedFirst: function(list, idOf){
      var c = this.climbed();
      if (!c.length || !list.length || c.indexOf(idOf(list[0])) === -1) return list;
      for (var i = 1; i < list.length; i++) {
        if (c.indexOf(idOf(list[i])) === -1) return [list[i]].concat(list.slice(0, i), list.slice(i + 1));
      }
      return list;
    },
    // 診断をやり直すとき：URL から back を外す
    clear: function(){
      try {
        if (/[?&]back=1(&|$)/.test(location.search) && history.replaceState) {
          var q = new URLSearchParams(location.search); q.delete('back');
          var qs = q.toString();
          history.replaceState(history.state, '', location.pathname + (qs ? '?' + qs : ''));
        }
      } catch (e) {}
    }
  };

  // 山ページ：その診断の結果に出た山なら、左下に「結果に戻る」を出す
  var pm = location.pathname.match(/^\/mountains\/([^\/]+)\/?$/);
  if (!pm) return;
  var s = get();
  if (!s || !s.ids || s.ids.indexOf(pm[1]) === -1) return;
  function build(){
    var css = '.ym-diag-back{position:fixed;left:14px;bottom:20px;z-index:900;display:flex;align-items:center;gap:6px;max-width:calc(100% - 90px);' +
      'padding:10px 14px;border-radius:999px;background:#4e6535;color:#fff;font-size:13px;font-weight:700;line-height:1.3;text-decoration:none;' +
      'box-shadow:0 3px 12px rgba(0,0,0,.22);-webkit-tap-highlight-color:transparent}' +
      '.ym-diag-back:active{transform:scale(.97)}@media print{.ym-diag-back{display:none}}';
    var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    var a = document.createElement('a');
    a.className = 'ym-diag-back';
    a.href = s.url;
    a.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>';
    a.appendChild(document.createTextNode(s.label + 'の結果に戻る'));
    a.addEventListener('click', function(){ if (typeof gtag === 'function') gtag('event', 'diag_back_click', { diagnosis_type: s.kind, mountain_id: pm[1] }); });
    document.body.appendChild(a);
    // 画面の下に固定のバーがあれば、その上に出す（to-top.js と同じ考え方）
    function place(){
      var h = window.innerHeight, lift = 0;
      var els = document.body.querySelectorAll('nav, footer, div, header');
      for (var i = 0; i < els.length; i++) {
        var el = els[i];
        var cs = window.getComputedStyle(el);
        if (cs.position !== 'fixed' || cs.display === 'none' || cs.visibility === 'hidden') continue;
        var r = el.getBoundingClientRect();
        if (r.width >= window.innerWidth * 0.5 && r.bottom >= h - 2 && r.height < h * 0.4) lift = Math.max(lift, h - r.top);
      }
      a.style.bottom = (20 + lift) + 'px';
    }
    place();
    window.addEventListener('resize', place);
    setTimeout(place, 1500);
  }
  if (document.body) build(); else document.addEventListener('DOMContentLoaded', build);
})();
