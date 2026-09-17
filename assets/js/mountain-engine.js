// YAMATCH 山ページ共通エンジン（Phase3）
// 各山のHTMLは window.YM_MOUNTAIN_INIT = {id, name, heroMinMap, nearbyIds} を
// このscriptタグの前に定義してから読み込むこと。
// 旧版で山ごとに直書きされていた timeMap は ymFormatHeroTime() に渡した後の
// 出力が heroMinMap 経由の値と常に同一になるため、Phase3で廃止（死んでいたコードではなく
// 使われていたが、常にheroMinMapと同じ結果になる冗長な二重管理だったため統一）。

function shareNative(){
  var name = (window.YM_MOUNTAIN_INIT && YM_MOUNTAIN_INIT.name) || '';
  gtag('event','share_click',{method:'native'});
  if(navigator.share){ navigator.share({title:name + 'の登山情報',url:location.href}); }
  else { document.getElementById('share-fallback').style.display='flex'; }
}
function copyUrl(){gtag('event','share_click',{method:'copy_url'});
  navigator.clipboard.writeText(location.href).then(()=>alert('URLをコピーしました'));
}
function ymFormatHeroTime(raw){var totalMin;if(typeof raw==='number'){totalMin=raw;}else{var s=String(raw);var hMatch=s.match(/(\d+)\s*時間/);var mMatch=s.match(/(\d+)\s*分/);if(hMatch||mMatch){var h=hMatch?parseInt(hMatch[1],10):0;var m=mMatch?parseInt(mMatch[1],10):0;totalMin=h*60+m;}else{var n=s.match(/\d+/);totalMin=n?parseInt(n[0],10):0;}}if(totalMin<60){return {v:String(totalMin),u:'分〜'};}var hrs=totalMin/60;var hrsStr=hrs.toFixed(1);if(hrsStr.slice(-2)==='.0'){hrsStr=hrsStr.slice(0,-2);}return {v:hrsStr,u:'時間〜'};}
function changeDep(dep){
  sessionStorage.setItem('ym_departure', dep);
  updateDepButtons(dep);
  applyDep();
}
function updateDepButtons(dep){
  document.querySelectorAll('.dep-btn-m').forEach(function(b){
    b.classList.toggle('active', b.textContent === dep + '駅');
  });
}
function changeDepTrain(key){
  sessionStorage.setItem('ym_departure_train', key);
  document.querySelectorAll('.ts-dep-btn').forEach(function(b){
    b.classList.toggle('active', b.dataset.key === key);
  });
  document.querySelectorAll('.ts-time-val').forEach(function(el){
    if(el.dataset[key]) el.textContent = el.dataset[key];
  });
  document.querySelectorAll('.ts-fare-val').forEach(function(el){
    if(el.dataset[key]) el.textContent = el.dataset[key];
  });
  ['shinjuku','omiya','yokohama'].forEach(function(k){
    document.querySelectorAll('.ts-route-'+k).forEach(function(el){
      el.style.display = (key === k) ? '' : 'none';
    });
  });
}
function applyDepTrain(){
  var key = sessionStorage.getItem('ym_departure_train') || 'shinjuku';
  changeDepTrain(key);
}

function applyDep(){
  var init = window.YM_MOUNTAIN_INIT || {};
  var heroMinMap = init.heroMinMap || {};
  var nearbyIds = init.nearbyIds || [];
  var raw = sessionStorage.getItem('ym_departure'); var dep = raw ? (raw.startsWith('"') ? JSON.parse(raw) : raw) : '大船';
  var depMap = {'大船':'ofuna','新宿':'shinjuku','横浜':'yokohama','大宮':'omiya','立川':'tachikawa'};
  var key = depMap[dep] || 'ofuna';
  var label = dep + 'から';
  var heroTime = document.getElementById('hero-time');
  var heroUnit = document.getElementById('hero-unit');
  var heroLabel = document.getElementById('hero-dep-label');
  var __hf = ymFormatHeroTime(parseInt(heroMinMap[key],10) || 0);
  if(heroTime) heroTime.textContent = __hf.v;
  if(heroUnit) heroUnit.textContent = __hf.u;
  if(heroLabel) heroLabel.textContent = label;
  document.querySelectorAll('#access-grid .ai-a').forEach(function(el){
    var sel = el.dataset.dep === dep + '駅';
    el.querySelector('.ai-a-dep').style.fontWeight = sel ? '700' : '400';
    el.querySelector('.ai-a-dep').style.color = sel ? '#3a5a28' : '#5a5248';
    var bar = el.querySelector('.ai-a-bar');
    if(bar) bar.style.background = sel ? 'linear-gradient(90deg,#4e6535,#607848)' : 'linear-gradient(90deg,#607848,#c8d4b8)';
    el.querySelector('.ai-a-val').style.color = sel ? '#3a5a28' : '#3a3530';
    el.querySelector('.ai-a-val').style.fontWeight = sel ? '700' : '600';
  });
  nearbyIds.forEach(function(id){
    var timeEl = document.getElementById('nearby-time-'+id);
    var labelEl = document.getElementById('nearby-label-'+id);
    if(timeEl && labelEl){
      var t = timeEl.dataset[key];
      if(t){ timeEl.childNodes[0].textContent = t; labelEl.textContent = label; }
    }
  });
}
(function(){
  var initDep = sessionStorage.getItem('ym_departure') || '大船';
  updateDepButtons(initDep);
  applyDep();
  applyDepTrain();
})();


// === JSONから動的データを反映 ===
(function(){
  var MID = (window.YM_MOUNTAIN_INIT && YM_MOUNTAIN_INIT.id) || '';
  fetch('/data/mountains.json')
    .then(function(r){ return r.json(); })
    .then(function(data){
      var mt = data.find(function(m){ return m.id === MID; });
      if(!mt) return;
      applyMountainData(mt);
    })
    .catch(function(){ });

  function fmtMin(m){
    if(!m) return '—';
    var h=Math.floor(m/60), mn=m%60;
    if(h===0) return mn+'分';
    if(mn===0) return h+'時間';
    return h+'時間'+mn+'分';
  }

  function renderHeroPhotos(mt){
    if(!mt.photos || !mt.photos.length) return;
    var heroNew = document.querySelector('.hero-new');
    var heroTop = document.querySelector('.hero-top');
    var statsRow = document.querySelector('.stats-row');
    if(!heroNew || !heroTop || heroNew.querySelector('.hero-bg-img')) return;
    heroNew.classList.add('hp-mode');

    var imgBox = document.createElement('div');
    imgBox.className = 'hero-bg-img';
    mt.photos.forEach(function(src, i){
      var img = document.createElement('img');
      img.src = src;
      img.alt = mt.name || '';
      if(i === 0){ img.loading = 'eager'; img.fetchPriority = 'high'; img.className = 'hp-active'; }
      else { img.loading = 'lazy'; }
      imgBox.appendChild(img);
    });
    var scrim = document.createElement('div');
    scrim.className = 'hero-bg-scrim';
    imgBox.appendChild(scrim);
    heroNew.insertBefore(imgBox, heroNew.firstChild);

    var expandBtn = document.createElement('button');
    expandBtn.type = 'button';
    expandBtn.className = 'hero-bg-expand';
    expandBtn.setAttribute('aria-label', '写真を拡大表示');
    expandBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>';
    imgBox.appendChild(expandBtn);

    var dots = null;
    if(mt.photos.length > 1){
      dots = document.createElement('div');
      dots.className = 'hero-bg-dots';
      mt.photos.forEach(function(_, i){
        var d = document.createElement('div');
        d.className = 'hero-bg-dot' + (i === 0 ? ' hp-active' : '');
        dots.appendChild(d);
      });
      imgBox.appendChild(dots);
    }

    var idx = 0;
    var timerId = null;
    if(mt.photos.length > 1){
      var imgs = imgBox.querySelectorAll('img');
      var dotEls = imgBox.querySelectorAll('.hero-bg-dot');
      timerId = setInterval(advance, 4500);
      function advance(){
        imgs[idx].classList.remove('hp-active');
        if(dotEls[idx]) dotEls[idx].classList.remove('hp-active');
        idx = (idx + 1) % imgs.length;
        imgs[idx].classList.add('hp-active');
        if(dotEls[idx]) dotEls[idx].classList.add('hp-active');
      }
    }

    function openLightbox(startIdx){
      if(timerId) clearInterval(timerId);
      var lb = document.createElement('div');
      lb.className = 'hero-lightbox';
      var lbImg = document.createElement('img');
      lb.appendChild(lbImg);
      var closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.className = 'hero-lightbox-close';
      closeBtn.setAttribute('aria-label', '閉じる');
      closeBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>';
      lb.appendChild(closeBtn);
      var lbIdx = startIdx || 0;
      function render(){ lbImg.src = mt.photos[lbIdx]; lbImg.alt = mt.name || ''; }
      if(mt.photos.length > 1){
        var prevBtn = document.createElement('button');
        prevBtn.type = 'button';
        prevBtn.className = 'hero-lightbox-nav hero-lightbox-prev';
        prevBtn.setAttribute('aria-label', '前の写真');
        prevBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>';
        var nextBtn = document.createElement('button');
        nextBtn.type = 'button';
        nextBtn.className = 'hero-lightbox-nav hero-lightbox-next';
        nextBtn.setAttribute('aria-label', '次の写真');
        nextBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>';
        var lbDots = document.createElement('div');
        lbDots.className = 'hero-lightbox-dots';
        mt.photos.forEach(function(_, i){
          var d = document.createElement('div');
          d.className = 'hero-lightbox-dot' + (i === lbIdx ? ' hp-active' : '');
          lbDots.appendChild(d);
        });
        function updateDots(){
          lbDots.querySelectorAll('.hero-lightbox-dot').forEach(function(d, i){
            d.classList.toggle('hp-active', i === lbIdx);
          });
        }
        prevBtn.addEventListener('click', function(e){ e.stopPropagation(); lbIdx = (lbIdx - 1 + mt.photos.length) % mt.photos.length; render(); updateDots(); });
        nextBtn.addEventListener('click', function(e){ e.stopPropagation(); lbIdx = (lbIdx + 1) % mt.photos.length; render(); updateDots(); });
        lb.appendChild(prevBtn);
        lb.appendChild(nextBtn);
        lb.appendChild(lbDots);
      }
      render();
      document.body.appendChild(lb);
      requestAnimationFrame(function(){ lb.classList.add('hp-open'); });
      function close(){
        lb.classList.remove('hp-open');
        setTimeout(function(){ lb.remove(); }, 200);
        document.removeEventListener('keydown', onKey);
      }
      function onKey(e){ if(e.key === 'Escape') close(); }
      document.addEventListener('keydown', onKey);
      closeBtn.addEventListener('click', close);
      lb.addEventListener('click', function(e){ if(e.target === lb) close(); });
    }

    imgBox.addEventListener('click', function(){ openLightbox(idx); });
  }
  function applyMountainData(mt){
    // 0. 写真カルーセル
    renderHeroPhotos(mt);

    // 1. コース定数（ヒーローカード）
    var statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(function(card){
      var unit = card.querySelector('.stat-unit');
      if(unit && unit.textContent === 'コース定数'){
        var val = card.querySelector('.stat-val');
        if(val) val.textContent = mt.coeffMin + '〜' + mt.coeffMax;
      }
    });

    // 2. 車アクセス時間バー（値だけ更新・表示はapplyDepに任せる）
    var depMap = {'大船駅':'driveOfuna','横浜駅':'driveYokohama','新宿駅':'driveShinjuku','大宮駅':'driveOmiya','立川駅':'driveTachikawa'};
    document.querySelectorAll('#access-grid .ai-a').forEach(function(el){
      var dep = el.dataset.dep;
      var key = depMap[dep];
      if(!key || !mt[key]) return;
      var mins = mt[key];
      el.dataset.min = mins;
      var valEl = el.querySelector('.ai-a-val');
      if(valEl) valEl.textContent = fmtMin(mins);
      var barEl = el.querySelector('.ai-a-bar');
      if(barEl) barEl.style.width = Math.min(Math.round(mins/360*100),100) + '%';
    });

    // 3. ヒーロー時間を直接更新
    var raw = sessionStorage.getItem('ym_departure');
    var dep = raw ? (raw.startsWith('"') ? JSON.parse(raw) : raw) : '大船';
    var dk = {'大船':'driveOfuna','新宿':'driveShinjuku','横浜':'driveYokohama','大宮':'driveOmiya','立川':'driveTachikawa'};
    var heroTime = document.getElementById('hero-time');
    var heroUnit = document.getElementById('hero-unit');
    var heroLabel = document.getElementById('hero-dep-label');
    if(heroTime && mt[dk[dep]]){
      var __mthf = ymFormatHeroTime(mt[dk[dep]]);
      heroTime.textContent = __mthf.v;
      if(heroUnit) heroUnit.textContent = __mthf.u;
    }
    if(heroLabel) heroLabel.textContent = dep + 'から';

    // 4. YAMAPリンク
    if(mt.yamapUrl){
      document.querySelectorAll('a.yamap-btn').forEach(function(a){
        a.href = mt.yamapUrl;
      });
    }

    // 5. 登山口・駐車場・住所
    document.querySelectorAll('.info-row').forEach(function(row){
      var label = row.querySelector('.info-label');
      var val = row.querySelector('.info-val');
      if(!label || !val) return;
      if(label.textContent === '登山口' && mt.trailhead) val.textContent = mt.trailhead;
      if(label.textContent === '駐車場' && mt.parking) val.textContent = mt.parking;
      if(label.textContent === '住所' && mt.address) val.textContent = mt.address;
    });

    // 6. 地図リンク
    document.querySelectorAll('.map-btn-link').forEach(function(a){
      if(a.textContent.includes('Google') && mt.gmapUrl) a.href = mt.gmapUrl;
      if(a.textContent.includes('Apple') && mt.amapUrl) a.href = mt.amapUrl;
    });

    // 7. シーズンカレンダー
    if(mt.seasonCalendar && mt.seasonCalendar.length === 12){
      var calBars = document.querySelectorAll('.cal-b');
      calBars.forEach(function(bar, i){
        if(i < 12) bar.className = 'cal-b ' + mt.seasonCalendar[i];
      });
    }

    // 8. 凡例テキスト
    if(mt.calLegend && mt.calLegend.length > 0){
      var legEls = document.querySelectorAll('.cal-legend .leg');
      legEls.forEach(function(el, i){
        if(mt.calLegend[i]){
          var dotEl = el.querySelector('.leg-dot');
          if(dotEl) {
            el.innerHTML = '';
            el.appendChild(dotEl);
            el.appendChild(document.createTextNode(' ' + mt.calLegend[i]));
          }
        }
      });
    }

    // 9. バス時刻表リンク（JSONから更新）
    if(mt.busScheduleLinks && mt.busScheduleLinks.length > 0){
      var busLinkEls = document.querySelectorAll('a.ts-link-bus');
      busLinkEls.forEach(function(a, i){
        if(mt.busScheduleLinks[i]) a.href = mt.busScheduleLinks[i];
      });
    }
    // 10. 乗換案内リンク（JSONから更新）
    if(mt.busLinks && mt.busLinks.length > 0){
      var yahooLinkEls = document.querySelectorAll('a.ts-link-yahoo');
      yahooLinkEls.forEach(function(a, i){
        if(mt.busLinks[i]) a.href = mt.busLinks[i];
      });
    }

    // 11. 電車バスルート（trainRoutes）を動的反映
    if(mt.trainRoutes && mt.trainRoutes.length > 0){
      var tsSection = document.querySelector('.ts-section');
      if(tsSection){
        var lineNameEl = tsSection.querySelector('.ts-line-name');
        if(lineNameEl && mt.trainRoutes[0].lineName) lineNameEl.textContent = mt.trainRoutes[0].lineName;
        var noteEl = tsSection.querySelector('.ts-note');
        if(noteEl && mt.trainRoutes[0].note) noteEl.textContent = '💡 ' + mt.trainRoutes[0].note;
        var badgeEl = tsSection.querySelector('.ts-badge');
        if(badgeEl && mt.trainRoutes[0].season) badgeEl.textContent = mt.trainRoutes[0].season;
        var durationEls = tsSection.querySelectorAll('.ts-duration');
        var fareEls = tsSection.querySelectorAll('.ts-fare');
        if(mt.trainRoutes[0].steps){
          mt.trainRoutes[0].steps.forEach(function(step, i){
            var stations = tsSection.querySelectorAll('.ts-station');
            if(stations[i] && step.station) stations[i].textContent = step.station;
            if(durationEls[i] && step.duration) durationEls[i].textContent = step.duration;
            if(fareEls[i] && step.fare) fareEls[i].textContent = step.fare;
          });
        }
        if(mt.trainRoutes[0].yahooUrl){
          var yahooLink = tsSection.querySelector('a.ts-link-yahoo');
          if(yahooLink) yahooLink.href = mt.trainRoutes[0].yahooUrl;
        }
        if(mt.trainRoutes[0].busUrl){
          var busLink = tsSection.querySelector('a.ts-link-bus');
          if(busLink) busLink.href = mt.trainRoutes[0].busUrl;
        }
      }
    }
  }
})();
