// 管理画面の「お気に入り・登頂」タブ（2026-10-25〜）
// 山ごとのお気に入り数・登頂数を、管理者端末の分を引いて一覧にする。
// 数は Firebase の /counts（山ページと同じ集計）。管理者端末の分は /countsAdmin/<端末の番号>
// （管理者表示をオンにした端末が assets/js/ym-counts.js から預ける）と、いま開いている端末が管理者端末ならその端末の分。
(function(){
  var DB = String(window.YM_COUNTS_DB_URL || '').replace(/\/+$/, '');
  var root = null, loaded = false, state = { rows: [], sort: 'fav', showZero: false, info: null };

  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){ return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function num(v){ return (typeof v === 'number' && v > 0) ? Math.floor(v) : 0; }
  function getJSON(url){ return fetch(url, { cache: 'no-store' }).then(function(r){ if(!r.ok) throw new Error('http ' + r.status); return r.json(); }); }
  function readLocal(key, def){ try { var v = JSON.parse(localStorage.getItem(key) || 'null'); return v === null ? def : v; } catch(e) { return def; } }

  function load(){
    root = document.getElementById('counts-root');
    if(!root) return;
    if(!DB){ root.innerHTML = '<div class="ac-note">集計先（counts-config.js）が設定されていません。</div>'; return; }
    root.innerHTML = '<div class="ac-note">読み込み中…</div>';
    var adminReq = getJSON(DB + '/countsAdmin.json').catch(function(){ return null; });
    Promise.all([getJSON(DB + '/counts.json'), adminReq, getJSON('/data/mountains.json')]).then(function(res){
      var counts = res[0] || {}, admins = res[1], mountains = res[2] || [];
      // 管理者端末の分（端末ごとに、集計に加えた山）
      var devs = {}, adminOk = admins !== null;
      if(admins){ Object.keys(admins).forEach(function(k){ devs[k] = admins[k] || {}; }); }
      var myDev = null;
      try { myDev = localStorage.getItem('ym_counts_dev'); } catch(e) {}
      var iAmAdmin = false;
      try { iAmAdmin = localStorage.getItem('ym_admin') === '1'; } catch(e) {}
      if(iAmAdmin && (!myDev || !devs[myDev])){
        // まだ預けていない（または預けられない）とき：この端末の分をその場で引く
        var done = readLocal('ym_counts_synced', { fav: [], climbed: [] }) || { fav: [], climbed: [] };
        var mine = { fav: {}, climbed: {} };
        (done.fav || []).forEach(function(id){ mine.fav[id] = true; });
        (done.climbed || []).forEach(function(id){ mine.climbed[id] = true; });
        devs['this-device'] = mine;
      }
      var subFav = {}, subClm = {};
      Object.keys(devs).forEach(function(k){
        var d = devs[k];
        Object.keys(d.fav || {}).forEach(function(id){ subFav[id] = (subFav[id] || 0) + 1; });
        Object.keys(d.climbed || {}).forEach(function(id){ subClm[id] = (subClm[id] || 0) + 1; });
      });
      var byId = {};
      mountains.forEach(function(m){ byId[m.id] = m; });
      var ids = {};
      Object.keys(counts).forEach(function(id){ ids[id] = 1; });
      mountains.forEach(function(m){ ids[m.id] = 1; });
      var rows = [], totFav = 0, totClm = 0, rawFav = 0, rawClm = 0;
      Object.keys(ids).forEach(function(id){
        var c = counts[id] || {};
        var f0 = num(c.fav), c0 = num(c.climbed);
        var f = Math.max(0, f0 - (subFav[id] || 0)), cl = Math.max(0, c0 - (subClm[id] || 0));
        rawFav += f0; rawClm += c0; totFav += f; totClm += cl;
        var m = byId[id] || {};
        rows.push({ id: id, name: m.name || id, area: m.area || '', category: m.category || '', fav: f, climbed: cl, onSite: !!byId[id] });
      });
      state.rows = rows;
      state.info = {
        devices: Object.keys(devs).length, adminOk: adminOk, iAmAdmin: iAmAdmin,
        totFav: totFav, totClm: totClm, rawFav: rawFav, rawClm: rawClm,
        withAny: rows.filter(function(r){ return r.fav > 0 || r.climbed > 0; }).length
      };
      loaded = true;
      render();
    }).catch(function(e){
      root.innerHTML = '<div class="ac-note">読み込めませんでした（' + esc(e && e.message) + '）。通信を確かめて、もう一度開いてください。</div>';
    });
  }

  function sorted(){
    var list = state.rows.slice();
    if(!state.showZero) list = list.filter(function(r){ return r.fav > 0 || r.climbed > 0; });
    var key = state.sort;
    list.sort(function(a, b){
      if(key === 'name') return a.name < b.name ? -1 : (a.name > b.name ? 1 : 0);
      var va = key === 'sum' ? a.fav + a.climbed : a[key], vb = key === 'sum' ? b.fav + b.climbed : b[key];
      if(vb !== va) return vb - va;
      var sa = a.fav + a.climbed, sb = b.fav + b.climbed;
      if(sb !== sa) return sb - sa;
      return a.name < b.name ? -1 : 1;
    });
    return list;
  }

  function render(){
    if(!root || !loaded) return;
    var i = state.info, list = sorted();
    var html = '';
    html += '<div class="ac-head">';
    html += '<div class="ac-sum"><div class="ac-sum-item"><div class="ac-sum-num">' + i.totFav + '</div><div class="ac-sum-label">お気に入りの合計</div></div>';
    html += '<div class="ac-sum-item"><div class="ac-sum-num">' + i.totClm + '</div><div class="ac-sum-label">登頂記録の合計</div></div>';
    html += '<div class="ac-sum-item"><div class="ac-sum-num">' + i.withAny + '</div><div class="ac-sum-label">登録のある山</div></div></div>';
    var note = '管理者端末 ' + i.devices + '台の分を引いています（引く前：お気に入り ' + i.rawFav + '・登頂 ' + i.rawClm + '）。';
    if(!i.adminOk) note += '管理者端末の預け先が読めませんでした（Firebase のルールに countsAdmin が未登録の可能性）。';
    if(i.devices === 0) note += 'いまは管理者端末の記録がありません。管理者表示をオンにした端末で、サイトを一度開くと預けられます。';
    html += '<div class="ac-note">' + esc(note) + '</div>';
    html += '<div class="ac-ctrl"><label>並び順 <select id="ac-sort">' +
      opt('fav', 'お気に入りの多い順') + opt('climbed', '登頂の多い順') + opt('sum', '合計の多い順') + opt('name', '山名順') +
      '</select></label><label class="ac-zero"><input type="checkbox" id="ac-zero"' + (state.showZero ? ' checked' : '') + '> 0件の山も出す</label>' +
      '<button type="button" id="ac-reload" class="ac-btn">読み込み直す</button></div>';
    html += '</div>';
    if(!list.length){
      html += '<div class="ac-note">まだ登録のある山はありません。</div>';
    } else {
      html += '<table class="ac-table"><thead><tr><th>#</th><th>山</th><th>★ お気に入り</th><th>⚑ 登頂</th></tr></thead><tbody>';
      list.forEach(function(r, n){
        var nm = r.onSite ? '<a href="/mountains/' + esc(r.id) + '/">' + esc(r.name) + '</a>' : esc(r.name) + '<span class="ac-off">（掲載なし）</span>';
        html += '<tr><td class="ac-rank">' + (n + 1) + '</td><td>' + nm + '<div class="ac-sub">' + esc(r.area) + (r.category ? '・' + esc(r.category) : '') + '</div></td>' +
          '<td class="ac-num">' + r.fav + '</td><td class="ac-num">' + r.climbed + '</td></tr>';
      });
      html += '</tbody></table>';
    }
    root.innerHTML = html;
    var s = document.getElementById('ac-sort');
    if(s) s.onchange = function(){ state.sort = s.value; render(); };
    var z = document.getElementById('ac-zero');
    if(z) z.onchange = function(){ state.showZero = z.checked; render(); };
    var b = document.getElementById('ac-reload');
    if(b) b.onclick = function(){ loaded = false; load(); };
  }
  function opt(v, label){ return '<option value="' + v + '"' + (state.sort === v ? ' selected' : '') + '>' + label + '</option>'; }

  window.ymAdminCountsStart = function(){ if(!loaded) load(); else render(); };
})();
