/* 記事・まとめのカードに出す山の写真に、作者とライセンスを添える。
   写真はページのスクリプトが mountains.json の photos から後で入れるので、
   data/image-credits.json の localPath と img の src を照らし、見つけた写真の下に1行ずつ出す。
   Wikimedia Commons の CC BY / BY-SA は表示が必須。 */
(function(){
  var byPath = null;
  var timer = null;

  function cleanPath(src){
    if(!src) return '';
    try { return new URL(src, location.href).pathname; } catch(e){ return src.split('?')[0]; }
  }

  function esc(s){
    return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){
      return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;' }[c];
    });
  }

  function creditHtml(p){
    if(p.source !== 'wikimedia_commons'){
      return '撮影：' + esc(p.author || 'Yamatch');
    }
    var lic = p.license || 'ライセンス不明';
    var licUrl = p.licenseUrl || p.commonsPageUrl;
    var out = esc(p.author || '作者不明') + '（';
    out += licUrl ? '<a href="' + esc(licUrl) + '" target="_blank" rel="noopener">' + esc(lic) + '</a>' : esc(lic);
    if(p.commonsPageUrl){
      out += '、<a href="' + esc(p.commonsPageUrl) + '" target="_blank" rel="noopener">Wikimedia Commons</a>';
    }
    return out + '）';
  }

  function addLine(after, credits){
    var seen = {};
    var parts = [];
    credits.forEach(function(p){
      var h = creditHtml(p);
      if(seen[h]) return;
      seen[h] = 1;
      parts.push(h);
    });
    if(!parts.length) return;
    var d = document.createElement('div');
    d.className = 'ym-photo-credit';
    d.style.cssText = 'order:-1;font-size:11px;line-height:1.5;color:#7a776e;margin:4px 2px 6px;word-break:break-word';
    d.innerHTML = '写真：' + parts.join('／');
    after.insertAdjacentElement('afterend', d);
  }

  function hasLine(el){
    var n = el.nextElementSibling;
    return !!(n && n.className === 'ym-photo-credit');
  }

  function scan(){
    if(!byPath) return;
    // いくつも写真を切り替える枠：枠の下にまとめて1行
    document.querySelectorAll('.mc-photo-carousel').forEach(function(wrap){
      if(hasLine(wrap)) return;
      var list = [];
      wrap.querySelectorAll('img').forEach(function(img){
        var p = byPath[cleanPath(img.getAttribute('src'))];
        if(p) list.push(p);
      });
      addLine(wrap, list);
    });
    // 1枚の写真
    document.querySelectorAll('img').forEach(function(img){
      if(img.closest('.mc-photo-carousel')) return;
      var p = byPath[cleanPath(img.getAttribute('src'))];
      if(!p) return;
      var n = img.nextElementSibling;
      if(n && n.className === 'ym-photo-credit'){
        // 写真が差し替わったときは書き直す
        if(n.getAttribute('data-src') === img.getAttribute('src')) return;
        n.parentNode.removeChild(n);
      }
      addLine(img, [p]);
      var line = img.nextElementSibling;
      if(line) line.setAttribute('data-src', img.getAttribute('src'));
    });
  }

  function later(){
    if(timer) clearTimeout(timer);
    timer = setTimeout(scan, 150);
  }

  fetch('/data/image-credits.json', { cache: 'no-cache' }).then(function(r){ return r.ok ? r.json() : {}; }).then(function(all){
    byPath = {};
    Object.keys(all || {}).forEach(function(id){
      (all[id] || []).forEach(function(p){
        if(p && p.localPath) byPath[cleanPath(p.localPath)] = p;
      });
    });
    scan();
    if(window.MutationObserver){
      var mo = new MutationObserver(later);
      mo.observe(document.body, { childList: true, subtree: true });
      setTimeout(function(){ mo.disconnect(); }, 15000);
    }
  }).catch(function(){});
})();
