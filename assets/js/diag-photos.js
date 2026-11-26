// 診断の結果のカードに、山ページと同じ写真を出す（2026-11-26〜。運営者の指示「山ページに写真が登録されている山は写真を出して。山ページと完全連携して自動スクロール式で。新たな写真を入れたら自動で反映」）
// 写真の一覧は山ページと同じ data/mountains.json の photos（山ページの mountain-engine.js が読むもの。管理画面の「山画像を管理」が書き換える）を、
// 開くたびに読む。ページを作り直さなくても、山ページに写真を足す・入れ替える・外すと診断にもそのまま出る。
// 複数あれば山ページと同じく4.5秒ごとに切り替え、下に点で枚数を出す。写真クレジットは card-photo-credits.js（開くと見える形）。
(function(){
  var cache = null, loading = null;

  function load(){
    if (cache) return Promise.resolve(cache);
    if (!loading) {
      loading = fetch('/data/mountains.json').then(function(r){ return r.ok ? r.json() : []; }).then(function(all){
        cache = {};
        (all || []).forEach(function(m){ if (m && m.id && m.photos && m.photos.length) cache[m.id] = { photos: m.photos, name: m.name }; });
        return cache;
      }).catch(function(){ cache = {}; return cache; });
    }
    return loading;
  }

  function css(){
    if (document.getElementById('ym-dp-css')) return;
    var st = document.createElement('style');
    st.id = 'ym-dp-css';
    st.textContent = '.ym-dp{position:relative;display:block;width:100%;aspect-ratio:16/9;overflow:hidden;background:#e8e4da;margin:0 0 4px}' +
      '.ym-dp img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transition:opacity .8s ease}' +
      '.ym-dp img.mpc-active{opacity:1}' +
      '.ym-dp .mountain-photo-dots{position:absolute;left:0;right:0;bottom:8px;display:flex;justify-content:center;gap:5px;pointer-events:none}' +
      '.ym-dp .mountain-photo-dot{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.55);box-shadow:0 0 2px rgba(0,0,0,.35)}' +
      '.ym-dp .mountain-photo-dot.mpc-active{background:#fff}' +
      '.result-card .ym-dp{border-radius:10px;margin-bottom:10px}';
    document.head.appendChild(st);
  }

  function idOf(card){
    var a = card.querySelector('a.rc-cta[href^="/mountains/"]');
    var m = a && a.getAttribute('href').match(/^\/mountains\/([^\/?#]+)/);
    return m ? { id: m[1], href: a.getAttribute('href') } : null;
  }

  function build(card, info, data){
    var photos = data.photos;
    var box = document.createElement('a');
    box.className = 'ym-dp mountain-photo-carousel';
    box.href = info.href;
    box.setAttribute('aria-label', (data.name || '') + 'の山ページを見る');
    photos.forEach(function(src, i){
      var img = document.createElement('img');
      img.src = src;
      img.alt = data.name || '';
      img.loading = i === 0 ? 'eager' : 'lazy';
      if (i === 0) img.className = 'mpc-active';
      box.appendChild(img);
    });
    if (photos.length > 1) {
      var dots = document.createElement('div');
      dots.className = 'mountain-photo-dots';
      photos.forEach(function(_, i){
        var d = document.createElement('span');
        d.className = 'mountain-photo-dot' + (i === 0 ? ' mpc-active' : '');
        dots.appendChild(d);
      });
      box.appendChild(dots);
    }
    card.insertBefore(box, card.firstChild);
    if (photos.length > 1 && !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)) {
      var imgs = box.querySelectorAll('img'), ds = box.querySelectorAll('.mountain-photo-dot'), idx = 0;
      var t = setInterval(function(){
        if (!document.body.contains(box)) { clearInterval(t); return; }
        imgs[idx].classList.remove('mpc-active'); if (ds[idx]) ds[idx].classList.remove('mpc-active');
        idx = (idx + 1) % imgs.length;
        imgs[idx].classList.add('mpc-active'); if (ds[idx]) ds[idx].classList.add('mpc-active');
      }, 4500);
    }
  }

  window.YMDiagPhotos = {
    // mountains.json をもう読んでいるページ（通年の山選び診断・登山タイプ診断）は、その中身を渡す（同じファイルを2回読まない）
    use: function(all){
      if (cache || !all || !all.length) return;
      cache = {};
      all.forEach(function(m){ if (m && m.id && m.photos && m.photos.length) cache[m.id] = { photos: m.photos, name: m.name }; });
    },
    // 結果を出したあとに呼ぶ。root の中の結果のカード（.rc / .result-card）に写真を入れる
    render: function(root){
      if (!root) return;
      css();
      load().then(function(map){
        var cards = root.querySelectorAll('.rc, .result-card');
        for (var i = 0; i < cards.length; i++) {
          var card = cards[i];
          if (card.querySelector('.ym-dp')) continue;
          var info = idOf(card);
          if (info && map[info.id]) build(card, info, map[info.id]);
        }
        if (window.YMCardCredits) window.YMCardCredits.scan();
      });
    }
  };
})();
