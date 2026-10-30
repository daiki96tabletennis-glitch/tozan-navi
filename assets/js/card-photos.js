/* 記事のカードの写真を、山ページの写真と合わせる。
   <div data-photo-id="山ID"> の中の1枚目を、data/image-credits.json（山ページの写真と同じ順。
   管理画面の「山画像を管理」が写真と一緒に書き換える）の1枚目にそろえる。
   ページを作り直さなくても、山ページに写真を足す・入れ替えると記事にも出る。
   作者・ライセンスの1行は card-photo-credits.js が足す。 */
(function(){
  function path(src){
    try { return new URL(src, location.href).pathname; } catch(e){ return String(src || '').split('?')[0]; }
  }
  fetch('/data/image-credits.json', { cache: 'no-cache' }).then(function(r){ return r.ok ? r.json() : null; }).then(function(all){
    if(!all) return;
    document.querySelectorAll('[data-photo-id]').forEach(function(box){
      var list = all[box.getAttribute('data-photo-id')] || [];
      var first = list[0] && list[0].localPath;
      var img = box.querySelector('img');
      if(!first){
        // 山ページから写真が外れたときは記事からも外す
        if(img && box.getAttribute('data-photo-keep') !== '1') box.parentNode.removeChild(box);
        return;
      }
      if(img){
        if(path(img.getAttribute('src')) !== path(first)){
          img.setAttribute('src', first);
          var old = img.nextElementSibling;
          if(old && old.className === 'ym-photo-credit') old.parentNode.removeChild(old);
        }
        return;
      }
      img = document.createElement('img');
      img.src = first;
      img.alt = box.getAttribute('data-photo-alt') || '';
      img.loading = 'lazy';
      img.className = box.getAttribute('data-photo-class') || '';
      box.appendChild(img);
      box.style.display = '';
    });
  }).catch(function(){});
})();
