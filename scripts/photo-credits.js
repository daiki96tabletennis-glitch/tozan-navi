(function(){
  var match=location.pathname.match(/^\/mountains\/([^/]+)/); if(!match) return;
  fetch('/data/image-credits.json').then(function(r){return r.ok?r.json():{};}).then(function(all){
    var photos=all[match[1]]; if(!photos||!photos.length) return;
    var box=document.createElement('details'); box.className='photo-credits';
    box.innerHTML='<summary>写真クレジット</summary>';
    var list=document.createElement('ul');
    photos.forEach(function(p){var item=document.createElement('li'); var author=document.createElement('span'); author.textContent=p.author||'作者不明'; item.appendChild(author); item.appendChild(document.createTextNode(' / ')); var license=document.createElement('a'); license.textContent=p.license||'ライセンス不明'; license.href=p.licenseUrl||p.commonsPageUrl; license.target='_blank'; license.rel='noopener'; item.appendChild(license); item.appendChild(document.createTextNode(' / ')); var source=document.createElement('a'); source.textContent='Wikimedia Commons'; source.href=p.commonsPageUrl; source.target='_blank'; source.rel='noopener'; item.appendChild(source); list.appendChild(item);});
    box.appendChild(list); (document.querySelector('.hero-new')||document.querySelector('main')||document.body).after(box);
  }).catch(function(){});
})();