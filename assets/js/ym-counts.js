// お気に入り数・登頂数の集計と表示（2026-10-10〜）
// 端末に保存されているお気に入り（ym_favorites）と登頂記録（ym_climbed）を、全端末ぶん合計して表示する。
// 送るのは「どの山に +1 / -1 か」だけ。誰の記録か・日付・メモは送らない。
// 仕組み：この端末が集計に加えた山の一覧（ym_counts_synced）を端末に持ち、いまの記録との差だけを送る。
//   ・初めて動いたとき：保存済みの記録がすべて +1 される（過去の分も数える）
//   ・お気に入りや登頂記録を外したとき：-1 される
// 集計先のアドレス（counts-config.js の YM_COUNTS_DB_URL）が空なら、何もしない。
(function(){
  var DB = String(window.YM_COUNTS_DB_URL || '').replace(/\/+$/, '');
  var SYNC_KEY = 'ym_counts_synced';
  var CACHE_KEY = 'ym_counts_cache_v1';
  var CACHE_MS = 5 * 60 * 1000;
  var ID_RE = /^[a-z0-9_]{1,40}$/;
  var STAR = '<svg width="13" height="13" viewBox="0 0 24 24" fill="#f0c030" stroke="#d4a020" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>';
  var FLAG = '<svg width="13" height="13" viewBox="0 0 24 24"><path d="M6 3v18M6 4h12l-3 4 3 4H6" fill="#c05030" stroke="#c05030" stroke-width="1" stroke-linejoin="round"/></svg>';
  var counts = null, waiters = [], syncing = false, pending = false;

  function read(key, def){
    try { var v = JSON.parse(localStorage.getItem(key) || 'null'); return v === null ? def : v; } catch(e) { return def; }
  }
  function uniq(list){
    var out = [];
    list.forEach(function(x){ if(typeof x === 'string' && ID_RE.test(x) && out.indexOf(x) === -1) out.push(x); });
    return out;
  }
  // いま端末にある記録：お気に入りは山IDの配列、登頂記録は [山ID, 日付, メモ] の配列
  function localSets(){
    var fav = uniq(read('ym_favorites', []) || []);
    var clm = uniq((read('ym_climbed', []) || []).map(function(e){ return Array.isArray(e) ? e[0] : (e && e.id); }));
    return { fav: fav, climbed: clm };
  }

  function bump(id, kind, delta){
    // Firebase の「サーバー側で加算」を使う（同時に押されても数がずれない）
    return fetch(DB + '/counts/' + id + '/' + kind + '.json', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ '.sv': { increment: delta } })
    }).then(function(r){ if(!r.ok) throw new Error('http ' + r.status); });
  }

  // 端末の記録と、集計に加えた一覧の差を送る
  function sync(){
    if(!DB) return;
    if(syncing){ pending = true; return; }
    syncing = true;
    var now = localSets();
    var done = read(SYNC_KEY, { fav: [], climbed: [] }) || { fav: [], climbed: [] };
    var jobs = [];
    ['fav', 'climbed'].forEach(function(kind){
      var cur = now[kind], old = uniq(done[kind] || []);
      cur.forEach(function(id){ if(old.indexOf(id) === -1) jobs.push({ id: id, kind: kind, d: 1 }); });
      old.forEach(function(id){ if(cur.indexOf(id) === -1) jobs.push({ id: id, kind: kind, d: -1 }); });
      done[kind] = old;
    });
    // 1件ずつ送り、成功したものだけ「加えた一覧」に反映する（途中で失敗しても、次回に続きから送れる）
    function next(){
      var j = jobs.shift();
      if(!j){
        syncing = false;
        if(pending){ pending = false; sync(); }
        return;
      }
      bump(j.id, j.kind, j.d).then(function(){
        var list = done[j.kind];
        var i = list.indexOf(j.id);
        if(j.d > 0 && i === -1) list.push(j.id);
        if(j.d < 0 && i > -1) list.splice(i, 1);
        try { localStorage.setItem(SYNC_KEY, JSON.stringify(done)); } catch(e) {}
        if(counts){
          counts[j.id] = counts[j.id] || {};
          counts[j.id][j.kind] = Math.max(0, (counts[j.id][j.kind] || 0) + j.d);
          try { sessionStorage.setItem(CACHE_KEY, JSON.stringify({ t: Date.now(), c: counts })); } catch(e) {}
          render();
        }
        next();
      }).catch(function(){ syncing = false; pending = false; });
    }
    next();
  }

  function load(cb){
    if(!DB) return;
    if(counts){ cb(counts); return; }
    waiters.push(cb);
    if(waiters.length > 1) return;
    function fin(c){
      counts = c || {};
      var w = waiters; waiters = [];
      w.forEach(function(f){ try { f(counts); } catch(e) {} });
    }
    try {
      var c = JSON.parse(sessionStorage.getItem(CACHE_KEY) || 'null');
      if(c && (Date.now() - c.t) < CACHE_MS){ fin(c.c); return; }
    } catch(e) {}
    fetch(DB + '/counts.json').then(function(r){ if(!r.ok) throw new Error('http'); return r.json(); })
      .then(function(c){
        try { sessionStorage.setItem(CACHE_KEY, JSON.stringify({ t: Date.now(), c: c || {} })); } catch(e) {}
        fin(c);
      })
      .catch(function(){ waiters = []; });
  }

  function num(v){ return (typeof v === 'number' && v > 0) ? Math.floor(v) : 0; }

  // 山ページ：<div id="hero-counts" data-id="takao"> に「★5 ⚑6」を出す
  function render(){
    var box = document.getElementById('hero-counts');
    if(!box || !counts) return;
    var c = counts[box.getAttribute('data-id')] || {};
    box.innerHTML =
      '<span class="hc-item" title="お気に入りに入れている人の数">' + STAR + '<b>' + num(c.fav) + '</b></span>' +
      '<span class="hc-item" title="登頂記録を付けた人の数">' + FLAG + '<b>' + num(c.climbed) + '</b></span>';
    box.style.display = 'flex';
  }

  window.YMCounts = { load: load, sync: sync, enabled: !!DB };
  if(!DB) return;

  // お気に入り・登頂記録が書き換えられたら、少し待ってから差を送る
  try {
    var origSet = Storage.prototype.setItem;
    var timer = null;
    Storage.prototype.setItem = function(k, v){
      origSet.call(this, k, v);
      if(this === localStorage && (k === 'ym_favorites' || k === 'ym_climbed')){
        clearTimeout(timer);
        timer = setTimeout(sync, 1500);
      }
    };
  } catch(e) {}

  function start(){ load(function(){ render(); }); setTimeout(sync, 800); }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
