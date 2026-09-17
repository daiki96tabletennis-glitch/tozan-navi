(function(){
  // 数字カウントアップ（標高のみ。動的更新される値には触れない）
  var elevEl = document.querySelector('.stat-card .stat-val');
  if(elevEl){
    var target = parseInt(elevEl.textContent.replace(/,/g,''), 10);
    if(!isNaN(target) && !window.matchMedia('(prefers-reduced-motion: reduce)').matches){
      var statCard = elevEl.closest('.stat-card');
      elevEl.textContent = '0';
      if(statCard) statCard.classList.add('stat-counting');
      setTimeout(function(){
        var start = null;
        var dur = 1400;
        function step(ts){
          if(!start) start = ts;
          var p = Math.min((ts - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          var val = Math.round(target * eased);
          elevEl.textContent = val.toLocaleString('ja-JP');
          if(p < 1) requestAnimationFrame(step);
          else {
            elevEl.textContent = target.toLocaleString('ja-JP');
            if(statCard){
              statCard.classList.remove('stat-counting');
              statCard.classList.add('stat-counted');
              setTimeout(function(){ statCard.classList.remove('stat-counted'); }, 500);
            }
          }
        }
        requestAnimationFrame(step);
      }, 350);
    }
  }

  // スクロールで浮かび上がる演出
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var targets = document.querySelectorAll('.card, .rec-card, .gear-section, .related-links-card, #weather-card');
  if(!('IntersectionObserver' in window) || !targets.length) return;
  targets.forEach(function(el){ el.classList.add('reveal-up'); });
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(entry, i){
      if(entry.isIntersecting){
        var el = entry.target;
        setTimeout(function(){ el.classList.add('in-view'); }, i * 40);
        io.unobserve(el);
      }
    });
  }, {threshold: 0.08, rootMargin: '0px 0px -40px 0px'});
  targets.forEach(function(el){ io.observe(el); });
})();

(function(){
  var tabs = document.querySelectorAll('.bookmark-tab');
  tabs.forEach(function(tab){
    tab.addEventListener('click', function(){
      var id = tab.getAttribute('data-target');
      var el = document.getElementById(id);
      if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
    });
  });
})();

(function(){
  document.querySelectorAll('.faq-item').forEach(function(item,i){
    var q=item.querySelector('.faq-q');
    if(!q) return;
    if(i===0) item.classList.add('open');
    q.setAttribute('role','button');
    q.setAttribute('tabindex','0');
    function t(){ item.classList.toggle('open'); }
    q.addEventListener('click',t);
    q.addEventListener('keydown',function(e){
      if(e.key==='Enter'||e.key===' '){ e.preventDefault(); t(); }
    });
  });
})();

(function(){
  var cards = document.querySelectorAll('.rg .rc');
  if(!cards.length) return;
  var bar = document.getElementById('nearby-sticky-bar');
  var itemsBox = document.getElementById('nearby-sticky-items');

  var picks = [];
  for(var i=0; i<cards.length && picks.length<2; i++){
    var card = cards[i];
    var nameSrc = card.querySelector('.rn');
    if(!nameSrc) continue;
    var diffSrc = card.querySelector('.rbd');
    var coefSrc = card.querySelector('.rbc');
    var href = card.getAttribute('href');
    var idMatch = href.match(/\/mountains\/([a-z0-9_]+)\//);
    picks.push({
      href: href,
      id: idMatch ? idMatch[1] : null,
      name: nameSrc.textContent,
      diff: diffSrc ? diffSrc.textContent : '',
      coef: coefSrc ? coefSrc.textContent : '',
      area: ''
    });
  }
  if(!picks.length) return;

  function render(){
    itemsBox.innerHTML = '';
    picks.forEach(function(p){
      var subParts = [];
      if(p.diff) subParts.push(p.diff);
      if(p.coef) subParts.push(p.coef);
      if(p.area) subParts.push(p.area);

      var a = document.createElement('a');
      a.className = 'nearby-sticky-item';
      a.href = p.href;

      var nameEl = document.createElement('div');
      nameEl.className = 'nearby-sticky-name';
      var nameText = document.createElement('span');
      nameText.style.overflow = 'hidden';
      nameText.style.textOverflow = 'ellipsis';
      nameText.style.whiteSpace = 'nowrap';
      nameText.textContent = p.name;
      var arrowEl = document.createElement('span');
      arrowEl.className = 'arrow';
      arrowEl.textContent = '→';
      nameEl.appendChild(nameText);
      nameEl.appendChild(arrowEl);
      a.appendChild(nameEl);

      if(subParts.length){
        var subEl = document.createElement('div');
        subEl.className = 'nearby-sticky-sub';
        subEl.textContent = subParts.join('・');
        a.appendChild(subEl);
      }
      itemsBox.appendChild(a);
    });
  }
  render();

  // 地域情報をmountains.jsonから取得して追加
  fetch('/data/mountains.json').then(function(r){ return r.json(); }).then(function(list){
    picks.forEach(function(p){
      var mt = list.find(function(m){ return m.id === p.id; });
      if(mt && mt.area) p.area = mt.area;
    });
    render();
  }).catch(function(){});

  var heroSection = document.querySelector('.hero-new');
  var relSection = document.querySelector('.rw');
  var shown = false;
  function checkVisibility(){
    var pastHero = heroSection ? (heroSection.getBoundingClientRect().bottom < 0) : true;
    var pastSection = relSection ? (relSection.getBoundingClientRect().top < window.innerHeight * 0.85) : false;
    var shouldShow = pastHero && !pastSection;
    if(shouldShow && !shown){ bar.style.display='flex'; requestAnimationFrame(function(){bar.classList.add('visible');}); shown = true; }
    else if(!shouldShow && shown){ bar.classList.remove('visible'); shown = false; }
  }
  checkVisibility();
  window.addEventListener('scroll', checkVisibility, {passive:true});
})();

window.GEAR_ICONS = {
  shoe:'img',winter_shoe:'img',rain:'img',down:'img',pole:'img',crampon:'img',axe:'img',
  bottle:'<path d="M9 2h6M10 2v4l-3 3v11a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9l-3-3V2"/>',
  bell:'<path d="M10.268 21a2 2 0 0 0 3.464 0"/><path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"/>',
  warning:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>'
};
window.GEAR_LABEL = {shoe:'登山靴',crampon:'アイゼン',crampon_next:'アイゼン(来月)',axe:'ピッケル',rain:'レインウェア',down:'インナーダウン',pole:'トレッキングポール',bottle:'保温ボトル',bell:'熊鈴',warning:'注意'};
window.GEAR_BADGE_STYLE = {
  '必須':'background:#f5ded9;color:#a0392a',
  '推奨':'background:none;border:1px solid #d4923a;color:#a0672a',
  'あると便利':'background:none;border:1px solid #4e6535;color:#4e6535',
  '条件次第':'background:none;border:1px solid #4e6535;color:#4e6535'
};
window.GEAR_DIRECT_ASIN = {
  'メレル MOAB 3 ミッド GTX':'B09BP11RNG'
};
window.RAKUTEN_ID = '57384242.53497bb8.57384243.366083eb';

function gearAmazonLink(keyword){
  var clean = keyword.replace('(来月分)','');
  if(window.GEAR_DIRECT_ASIN[clean]){
    return 'https://www.amazon.co.jp/dp/' + window.GEAR_DIRECT_ASIN[clean] + '?tag=amazonafdaiki-22';
  }
  return 'https://www.amazon.co.jp/s?k=' + encodeURIComponent(clean) + '&tag=amazonafdaiki-22';
}
function gearRakutenLink(keyword){
  var clean = keyword.replace('(来月分)','');
  var searchUrl = 'https://search.rakuten.co.jp/search/mall/' + encodeURIComponent(clean) + '/';
  var pcValue = encodeURIComponent(searchUrl);
  return 'https://hb.afl.rakuten.co.jp/hgc/' + window.RAKUTEN_ID + '/?pc=' + pcValue + '&m=' + pcValue;
}
function gearRenderIcon(catKey, strokeColor){
  var iconType = window.GEAR_ICONS[catKey];
  if(iconType === 'img'){
    return '<img src="/images/icons/' + catKey + '.webp" width="36" height="36" alt="" loading="lazy">';
  }
  var path = iconType || window.GEAR_ICONS['bottle'];
  return '<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="' + strokeColor + '" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' + path + '</svg>';
}
function gearRenderCard(c, mid, position){
  var catKey = c.c.replace('_next','');
  var iconKey = catKey;
  if(catKey === 'shoe' && c.p && (c.p.indexOf('マンタテック')>=0 || c.p.indexOf('ネパール')>=0)) iconKey = 'winter_shoe';
  var label = window.GEAR_LABEL[c.c] || c.c;
  var badgeStyle = window.GEAR_BADGE_STYLE[c.i] || '';
  var badgeHtml = '<span class="gear-badge" style="' + badgeStyle + ';font-size:9px;padding:1px 5px;border-radius:8px;font-weight:700;white-space:nowrap;flex-shrink:0;display:inline-block;line-height:1.5">' + c.i + '</span>';

  if(!c.p){
    var iconHtmlW = gearRenderIcon(iconKey, '#a0672a');
    return '<div class="gear-card-v2"><div class="gear-card-head"><div class="gear-card-icon">' + iconHtmlW + '</div><div class="gear-card-title">' + label + badgeHtml + '</div></div><p class="gear-card-desc">' + c.r + '</p></div>';
  }
  var amz = gearAmazonLink(c.p);
  var rkt = gearRakutenLink(c.p);
  var gtagAmz = "gtag('event','gear_affiliate_click',{platform:'amazon',product_name:'" + c.p.replace(/'/g,"\\'") + "',mountain_id:'" + mid + "',page_type:'mountain',position:" + position + "})";
  var gtagRkt = "gtag('event','gear_affiliate_click',{platform:'rakuten',product_name:'" + c.p.replace(/'/g,"\\'") + "',mountain_id:'" + mid + "',page_type:'mountain',position:" + position + "})";
  var iconHtml = gearRenderIcon(iconKey, '#4e6535');
  return '<div class="gear-card-v2"><div class="gear-card-head"><div class="gear-card-icon">' + iconHtml + '</div><div class="gear-card-title">' + label + badgeHtml + '</div></div><p class="gear-card-desc">' + c.r + '</p><a href="' + amz + '" target="_blank" rel="nofollow noopener sponsored" class="gear-card-product" onclick="' + gtagAmz + '">' + c.p + '</a><div class="gear-card-sublinks"><a href="' + amz + '" target="_blank" rel="nofollow noopener sponsored" onclick="' + gtagAmz + '">Amazon</a><span>/</span><a href="' + rkt + '" target="_blank" rel="nofollow noopener sponsored" onclick="' + gtagRkt + '">楽天</a></div></div>';
}

(function(){
  document.querySelectorAll('[data-gear-variants]').forEach(function(container){
    var variants;
    try { variants = JSON.parse(container.getAttribute('data-gear-variants')); } catch(e) { return; }
    var mid = container.getAttribute('data-gear-mid');
    var now = new Date();
    var month = now.getMonth() + 1;
    var cards = null;
    for(var key in variants){
      if(variants[key].indexOf(month) !== -1){ cards = JSON.parse(key); break; }
    }
    if(!cards){
      var firstKey = Object.keys(variants)[0];
      cards = JSON.parse(firstKey);
    }
    var html = cards.map(function(c, i){ return gearRenderCard(c, mid, i+1); }).join('');
    container.innerHTML = html;
  });
})();
