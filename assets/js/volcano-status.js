// 噴火警戒レベルの自動取得（2026-10-10〜）
// 気象庁の噴火警報・予報（https://www.jma.go.jp/bosai/volcano/data/warning.json）を、ページを開くたびに読む。
// このデータには「いま警報が出ている火山」と「最近切り替わった火山」だけが載る。載っていない火山は、警報なし（レベル1相当）として扱う。
// mountains.json の volcanoCodes（気象庁の火山コード）で、山と火山を結び付ける。
(function(){
  var URL = 'https://www.jma.go.jp/bosai/volcano/data/warning.json';
  var INFO_URL = 'https://www.jma.go.jp/bosai/volcano/';
  var CACHE_KEY = 'ym_volcano_v1';
  var CACHE_MS = 30 * 60 * 1000;
  // 気象庁のコード → 深刻さ（0=警報なし、1=火口周辺規制、2=入山規制、3=避難）
  var SEV = { '11': 0, '21': 0, '12': 1, '22': 1, '13': 2, '23': 2, '14': 3, '15': 3 };
  var state = { loaded: false, failed: false, byCode: {} };
  var waiters = [];

  function parse(list){
    var by = {};
    (list || []).forEach(function(e){
      (e.volcanoInfos || []).forEach(function(vi){
        if(vi.type !== '噴火警報・予報（対象火山）') return;
        (vi.items || []).forEach(function(it){
          (it.areas || []).forEach(function(a){
            var cur = by[a.code];
            // 同じ火山が複数回載っていたら、発表の新しいほうを使う
            if(cur && cur.date >= e.reportDatetime) return;
            by[a.code] = { code: it.code, label: it.name, sev: SEV[it.code] === undefined ? 0 : SEV[it.code], date: e.reportDatetime, name: a.name };
          });
        });
      });
    });
    return by;
  }

  function done(){
    state.loaded = true;
    var w = waiters; waiters = [];
    w.forEach(function(f){ try { f(state); } catch(e) {} });
  }

  function start(){
    try {
      var c = JSON.parse(sessionStorage.getItem(CACHE_KEY) || 'null');
      if(c && c.t && (Date.now() - c.t) < CACHE_MS){ state.byCode = c.by || {}; done(); return; }
    } catch(e) {}
    fetch(URL).then(function(r){ if(!r.ok) throw new Error('http'); return r.json(); })
      .then(function(list){
        state.byCode = parse(list);
        try { sessionStorage.setItem(CACHE_KEY, JSON.stringify({ t: Date.now(), by: state.byCode })); } catch(e) {}
      })
      .catch(function(){ state.failed = true; })
      .then(done);
  }

  // 取得が終わったら呼ぶ（終わっていれば、すぐ呼ぶ）
  function load(cb){
    if(state.loaded){ cb(state); return; }
    waiters.push(cb);
  }

  // 取得が終わるか、ms ミリ秒たつまで待つ Promise（ページの表示を長く止めないため）
  function ready(ms){
    return new Promise(function(resolve){
      var fin = false;
      function go(){ if(!fin){ fin = true; resolve(state); } }
      load(go);
      setTimeout(go, ms || 2500);
    });
  }

  // 山の火山コードから、いちばん深刻な警報を返す。火山でない山は null
  function forCodes(codes){
    if(!codes || !codes.length) return null;
    var best = null;
    codes.forEach(function(c){
      var v = state.byCode[String(c)];
      if(v && (!best || v.sev > best.sev)) best = v;
    });
    if(best) return best;
    return { code: null, label: state.failed ? null : '噴火警報なし', sev: 0, date: null, name: null };
  }

  function dateText(iso){
    var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
    return m ? (Number(m[1]) + '年' + Number(m[2]) + '月' + Number(m[3]) + '日') : '';
  }

  // 一覧・診断用：警報が出ている山（火口周辺規制以上）に印を付け、既存の「規制中」と同じ扱いにする
  function apply(mountains){
    if(state.failed) return;
    (mountains || []).forEach(function(m){
      var v = forCodes(m.volcanoCodes);
      if(!v || v.sev < 1) return;
      m.volcanoAlert = v;
      // 火口から離れた山（volcanoScope: nearby）は、警報が出ても登れることが多いので、山ページの表示だけにする
      if(m.volcanoScope === 'nearby' && v.sev < 2) return;
      m.status = { level: 'restricted', summary: '気象庁が' + v.label + 'を発表中（' + dateText(v.date) + '）。登山前に規制の範囲を確認してください。', sourceUrl: INFO_URL, auto: true };
    });
  }

  window.YMVolcano = { load: load, ready: ready, forCodes: forCodes, apply: apply, dateText: dateText, state: state, INFO_URL: INFO_URL };
  start();

  // 山ページ：<div id="volcano-status" data-codes="310"> があれば、そこに現在の状態を出す
  function renderBox(){
    var box = document.getElementById('volcano-status');
    if(!box) return;
    var codes = (box.getAttribute('data-codes') || '').split(',').filter(function(x){ return x; });
    if(!codes.length) return;
    load(function(){
      var v = forCodes(codes);
      var link = '<a href="' + INFO_URL + '" target="_blank" rel="noopener" class="warn-link">気象庁の火山情報を見る →</a>';
      var html;
      if(state.failed || !v){
        html = '<div class="volcano-note">活火山です。噴火警戒レベルを取得できませんでした。登山前に気象庁の火山情報を確認してください。 ' + link + '</div>';
      } else if(v.sev >= 1){
        var cls = v.sev >= 2 ? 'red' : 'yellow';
        html = '<div class="warn-banner warn-banner-' + cls + '"><div class="warn-icon">⚠️</div><div class="warn-body">' +
          '<div class="warn-title warn-title-' + cls + '">気象庁が「' + v.label + '」を発表しています</div>' +
          '<div class="warn-text">' + dateText(v.date) + '発表。火口周辺や登山道に立入規制が出ている可能性があります。登山前に、気象庁と地元自治体の規制情報を必ず確認してください。</div>' +
          link + '</div></div>';
      } else {
        html = '<div class="volcano-note">活火山です。現在、気象庁の噴火警報は出ていません（' + (v.code ? v.label : '警報なし') + '。このページを開いた時点の情報）。 ' + link + '</div>';
      }
      box.innerHTML = html;
    });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderBox);
  else renderBox();
})();
