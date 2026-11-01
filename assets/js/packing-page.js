/* 持ち物チェックリストのページ（/packing/。2026-11-01〜）。
   山・登る日・泊まり方（日帰り／山小屋泊／テント泊）を選ぶと、data/packing.json（YMPacking.build）から持ち物のリストを作る。
   - 自分だけで使うとき：チェックは端末の中（localStorage ym_pack_local）
   - 仲間と共有するとき：Firebase Realtime Database の /packLists/<20文字> に、条件・メンバーの名前とチェック・足した持ち物を預ける。
     リンク（/packing/?l=<番号>）を開いた人は同じリストを見られ、変更はすぐ全員に出る（REST の EventSource）。
     登る日の30日後に GitHub の定期実行（scripts/packlists_cleanup.js）が消す。ルールは scripts/firebase_rules.json の packLists
   必要なもの：counts-config.js（YM_COUNTS_DB_URL）、packing.js（YMPacking）。このリストには商品・アフィリエイトのリンクを出さない（運営者の指示・2026-11-01） */
(function () {
  'use strict';
  var root = document.getElementById('pk-app');
  if (!root) return;
  var DB = (window.YM_COUNTS_DB_URL || '').replace(/\/+$/, '');
  var STAY = { day: '日帰り', hut: '山小屋泊', tent: 'テント泊' };
  var SKIP_GROUPS = ['prep'];
  var K_LOCAL = 'ym_pack_local', K_DEV = 'ym_pack_dev', K_NAME = 'ym_pack_name', K_LISTS = 'ym_pack_lists';
  // 自分好みの直し（どの山・日付のリストにも効く）：hidden＝外した持ち物（fkey）、mine＝いつも持っていく自分の持ち物
  var K_CUSTOM = 'ym_pack_custom';
  var MOUNTAINS = [], BY = {}, DATA = null;
  var state = { mid: '', date: '', stay: 'day', edit: false };
  var shared = null;   // { id, data }：共有中のリスト
  var es = null, pollTimer = null, refetchTimer = null;
  var msgTimer = null;

  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function lsGet(k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function rand(n, chars) {
    var out = '', a = new Uint8Array(n);
    (window.crypto || window.msCrypto).getRandomValues(a);
    for (var i = 0; i < n; i++) out += chars.charAt(a[i] % chars.length);
    return out;
  }
  function devId() {
    var d = lsGet(K_DEV, '');
    if (!/^[a-f0-9]{16}$/.test(d)) { d = rand(16, '0123456789abcdef'); lsSet(K_DEV, d); }
    return d;
  }
  // Firebase のキーに「.」は使えないので、持ち物の番号（prep.plan など）を置き換える
  function fkey(id) { return String(id).toLowerCase().replace(/[^a-z0-9_]/g, '_').slice(0, 60); }
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function ymd(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function dateLabel(s) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(s || '')) return '日付未定';
    var p = s.split('-'), d = new Date(+p[0], +p[1] - 1, +p[2]);
    return (+p[1]) + '月' + (+p[2]) + '日（' + '日月火水木金土'.charAt(d.getDay()) + '）';
  }
  function msg(text) {
    var el = root.querySelector('[data-pk-msg]');
    if (!el) return;
    el.textContent = text;
    clearTimeout(msgTimer);
    msgTimer = setTimeout(function () { el.textContent = ''; }, 4000);
  }

  // ---------- Firebase（REST） ----------
  function api(method, path, body) {
    var opt = { method: method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opt.body = JSON.stringify(body);
    return fetch(DB + '/packLists/' + path + '.json', opt).then(function (r) {
      if (!r.ok) throw new Error('http ' + r.status);
      return r.json();
    });
  }
  function watch(id) {
    unwatch();
    var refetch = function () {
      clearTimeout(refetchTimer);
      refetchTimer = setTimeout(function () {
        api('GET', id).then(function (d) { if (shared && shared.id === id && d) { shared.data = d; draw(); } }).catch(function () {});
      }, 250);
    };
    if (window.EventSource) {
      try {
        es = new EventSource(DB + '/packLists/' + id + '.json');
        es.addEventListener('put', refetch);
        es.addEventListener('patch', refetch);
        return;
      } catch (e) { es = null; }
    }
    pollTimer = setInterval(refetch, 15000);
  }
  function unwatch() {
    if (es) { try { es.close(); } catch (e) {} es = null; }
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }

  // ---------- リスト ----------
  function mountain() { return BY[state.mid] || null; }
  function groups() {
    var m = mountain();
    var p = (state.date || '').split('-');
    // このページは「準備のときの忘れ物を防ぐ」ためのもの（運営者の指示）。持ち物ではない「出発前にすること」（予約・計画書など）は出さない
    return window.YMPacking.build({
      mid: m ? m.id : null, elev: m ? m.elev : 0, gear: m ? m.gear : [],
      month: p.length === 3 ? +p[1] : null, day: p.length === 3 ? +p[2] : null, stay: state.stay
    }).filter(function (g) { return SKIP_GROUPS.indexOf(g.key) < 0; });
  }
  function localKey() { return (state.mid || '-') + '|' + (state.date || '-') + '|' + state.stay; }
  function localStore() { var all = lsGet(K_LOCAL, {}); return all[localKey()] || { c: {}, x: {} }; }
  function saveLocal(o) {
    var all = lsGet(K_LOCAL, {});
    all[localKey()] = o;
    // 古い条件の記録はためこまない（新しい順に20件まで）
    var keys = Object.keys(all);
    if (keys.length > 20) keys.slice(0, keys.length - 20).forEach(function (k) { delete all[k]; });
    lsSet(K_LOCAL, all);
  }
  // 自分のチェック・足した持ち物（共有中は Firebase、そうでなければ端末の中）
  function myChecks() {
    if (shared) { var me = (shared.data.members || {})[devId()]; return (me && me.checks) || {}; }
    return localStore().c || {};
  }
  function extras() { return shared ? (shared.data.extra || {}) : {}; }
  function custom() { var c = lsGet(K_CUSTOM, {}); c.hidden = c.hidden || {}; c.mine = c.mine || []; return c; }
  function saveCustom(c) { lsSet(K_CUSTOM, c); }
  function hideItem(k, on) { var c = custom(); if (on) c.hidden[k] = 1; else delete c.hidden[k]; saveCustom(c); draw(); }
  function addMine(label) {
    label = label.trim().slice(0, 40);
    if (!label) return;
    var c = custom();
    c.mine.push({ k: rand(8, 'abcdefghijklmnopqrstuvwxyz0123456789'), label: label, at: Date.now() });
    saveCustom(c); draw();
  }
  function delMine(key) { var c = custom(); c.mine = c.mine.filter(function (x) { return x.k !== key; }); saveCustom(c); draw(); }
  function whoChecked(k) {
    if (!shared) return [];
    var ms = shared.data.members || {}, out = [];
    Object.keys(ms).forEach(function (id) {
      if (ms[id] && ms[id].checks && ms[id].checks[k]) out.push(id === devId() ? 'あなた' : (ms[id].name || '（名前なし）'));
    });
    return out;
  }

  function sourcesHtml(gs) {
    var used = {};
    gs.forEach(function (g) { g.items.forEach(function (it) { (it.src || []).forEach(function (k) { used[k] = 1; }); }); });
    var links = Object.keys(used).map(function (k) {
      var s = DATA.sources && DATA.sources[k];
      if (!s) return '';
      return s.url ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.label) + '</a>' : esc(s.label);
    }).filter(Boolean);
    return '<p class="pk-src">出典：' + (links.length ? links.join('、') + 'をもとに、' : '') + 'Yamatch がまとめました（' + esc(DATA.checkedAt || '') + '）。' +
      '雪の時期の装備は、選んだ山の装備カレンダーから選んでいます。</p>';
  }

  function formHtml() {
    var m = mountain();
    if (shared) {
      var names = Object.keys(shared.data.members || {}).map(function (id) {
        var n = shared.data.members[id] && shared.data.members[id].name;
        return id === devId() ? esc(n || 'あなた') + '（あなた）' : esc(n || '（名前なし）');
      });
      return '<div class="pk-card pk-shared"><div class="pk-tag">仲間と共有中</div>' +
        '<div class="pk-cond"><b>' + esc(m ? m.name : '山は未定') + '</b><span>' + esc(dateLabel(state.date)) + '・' + STAY[state.stay] + '</span></div>' +
        '<div class="pk-members">メンバー：' + (names.length ? names.join('、') : 'まだいません') + '</div>' +
        '<div class="pk-row"><button type="button" class="pk-btn" data-pk-sendlink>リンクを送る</button>' +
        '<button type="button" class="pk-btn pk-sub" data-pk-rename>名前を変える</button>' +
        '<button type="button" class="pk-btn pk-sub" data-pk-leave>このリストを閉じる</button></div>' +
        '<p class="pk-note">リンクを知っている人は誰でも見て編集できます。登る日の30日後に自動で消えます。</p></div>';
    }
    // メインは「泊まり方ごとの自分の持ち物リスト」（運営者の指示）。山と日にちは、雪の時期の装備などを足すためのたたんだ欄
    var stays = ['day', 'hut', 'tent'].map(function (s) {
      return '<button type="button" data-pk-stay="' + s + '"' + (s === state.stay ? ' class="on"' : '') + '>' + STAY[s] + '</button>';
    }).join('');
    var opts = '<option value="">選ばない</option>' + MOUNTAINS.map(function (x) {
      return '<option value="' + esc(x.id) + '"' + (x.id === state.mid ? ' selected' : '') + '>' + esc(x.name) + (x.area ? '（' + esc(x.area) + '）' : '') + '</option>';
    }).join('');
    var tuned = !!(state.mid || state.date);
    var sum = tuned ? '山と日にちに合わせています：' + esc((m ? m.name : '山は選ばない') + '・' + (state.date ? dateLabel(state.date) : '日にちは選ばない')) : '山と日にちに合わせる（雪の時期の装備などを足す）';
    return '<div class="pk-stay pk-stay-main">' + stays + '</div>' +
      '<details class="pk-card pk-tune"' + (tuned || state.tuneOpen ? ' open' : '') + '><summary>' + sum + '</summary><div class="pk-form">' +
      '<label class="pk-f"><span>山</span><select data-pk-mid>' + opts + '</select></label>' +
      '<label class="pk-f"><span>登る日</span><input type="date" data-pk-date value="' + esc(state.date) + '"></label>' +
      (tuned ? '<button type="button" class="pk-btn pk-sub" data-pk-untune>合わせるのをやめる（いつもの持ち物だけ）</button>' : '') +
      (m ? '<a class="pk-mlink" href="/mountains/' + esc(m.id) + '/">' + esc(m.name) + 'の山ページ（天気・装備・アクセス）→</a>' : '') +
      '</div></details>';
  }

  function itemHtml(k, label, note, prods, mine, extraKey, act) {
    var who = whoChecked(k);
    var btn = '';
    if (act && act.hide) btn = '<button type="button" class="pk-mini" data-pk-hide="' + esc(act.hide) + '">外す</button>';
    if (act && act.delMine) btn = '<button type="button" class="pk-mini" data-pk-delmine="' + esc(act.delMine) + '">消す</button>';
    if (act && act.delx) btn = '<button type="button" class="pk-mini" data-pk-delx="' + esc(act.delx) + '">消す</button>';
    var cls = (mine ? 'on' : '') + (btn ? ' pk-act' : '');
    return '<li' + (cls.trim() ? ' class="' + cls.trim() + '"' : '') + '><label><input type="checkbox" data-pk-k="' + esc(k) + '"' + (mine ? ' checked' : '') + '>' +
      '<span>' + esc(label) + (note ? '<small>' + esc(note) + '</small>' : '') +
      (who.length ? '<em class="pk-who">✔ ' + esc(who.join('・')) + '</em>' : '') + '</span></label>' +
      btn +
      '</li>';
  }

  function draw() {
    var gs = groups(), ck = myChecks(), xs = extras();
    var total = 0, done = 0;
    var h = formHtml();
    var m = mountain(), p = (state.date || '').split('-');
    if (m && p.length === 3) {
      var cell = m.gear[+p[1] - 1];
      var kinds = cell && typeof cell === 'object' ? [cell.before, cell.after] : [cell];
      if (kinds.indexOf('closed') >= 0) h += '<p class="pk-warn">' + (+p[1]) + '月は、登山道の閉鎖などで登れない期間があります。山ページの装備カレンダーを確かめてください。</p>';
    }
    var cu = custom(), hiddenList = [];
    h += '<div class="pk-editbar"><button type="button" class="pk-btn pk-sub" data-pk-edit>' + (state.edit ? '編集を終える' : '✎ リストを編集（外す・足す）') + '</button></div>';
    if (state.edit) h += '<p class="pk-edithelp">要らない持ち物は「外す」で消せます。外した物は下の「外した持ち物」から戻せます。外した物と自分の持ち物は、どの山・日付のリストにも効きます。</p>';
    gs.forEach(function (g) {
      var rows = '';
      g.items.forEach(function (it) {
        var k = fkey(it.id);
        if (cu.hidden[k]) { hiddenList.push({ k: k, label: it.label }); return; }
        total++;
        if (ck[k]) done++;
        rows += itemHtml(k, it.label, state.edit ? '' : it.note, null, !!ck[k], null, state.edit ? { hide: k } : null);
      });
      if (!rows) return;
      h += '<div class="pk-g"><h2>' + esc(g.title) + '</h2>' + (g.lead && !state.edit ? '<p class="pk-lead">' + esc(g.lead) + '</p>' : '') + '<ul>' + rows + '</ul></div>';
    });
    // 自分の持ち物（いつも持っていく物。どのリストにも出る）
    h += '<div class="pk-g pk-mine"><h2>自分の持ち物</h2><ul>';
    cu.mine.forEach(function (x) {
      var k = 'm_' + x.k; total++;
      if (ck[k]) done++;
      h += itemHtml(k, x.label, '', null, !!ck[k], null, state.edit ? { delMine: x.k } : null);
    });
    if (!cu.mine.length) h += '<li class="pk-empty">いつも持っていく物を足しておくと、どのリストにも出ます（例：サングラス・常備薬）</li>';
    h += '</ul><div class="pk-row pk-add"><input type="text" maxlength="40" data-pk-newmine placeholder="自分の持ち物を足す"><button type="button" class="pk-btn" data-pk-addmine>足す</button></div></div>';
    if (shared) {
      var xk = Object.keys(xs).sort(function (a, b) { return (xs[a].at || 0) - (xs[b].at || 0); });
      h += '<div class="pk-g"><h2>みんなで足した持ち物</h2><ul>';
      xk.forEach(function (key) {
        var k = 'x_' + key; total++;
        if (ck[k]) done++;
        h += itemHtml(k, xs[key].label, xs[key].by ? xs[key].by + 'が追加' : '', null, !!ck[k], null, state.edit ? { delx: key } : null);
      });
      if (!xk.length) h += '<li class="pk-empty">ここに足した物は、メンバー全員のリストに出ます</li>';
      h += '</ul><div class="pk-row pk-add"><input type="text" maxlength="40" data-pk-newx placeholder="みんなのリストに足す"><button type="button" class="pk-btn" data-pk-addx>足す</button></div></div>';
    }
    if (hiddenList.length) {
      h += '<div class="pk-g pk-hidden"><h2>外した持ち物（' + hiddenList.length + '）</h2><ul>' + hiddenList.map(function (x) {
        return '<li><span class="pk-hl">' + esc(x.label) + '</span><button type="button" class="pk-mini" data-pk-unhide="' + esc(x.k) + '">戻す</button></li>';
      }).join('') + '</ul></div>';
    }
    h += '<div class="pk-foot"><span class="pk-n">あなたの準備：' + done + ' / ' + total + '</span>' +
      (!shared && DB ? '<button type="button" class="pk-btn" data-pk-share>仲間と共有する</button>' : '') +
      '<button type="button" class="pk-btn pk-sub" data-pk-copy>文字でコピー</button>' +
      (!shared ? '<button type="button" class="pk-btn pk-sub" data-pk-reset>チェックを外す</button>' : '') + '</div>' +
      '<p class="pk-msg" data-pk-msg></p>';
    var recent = lsGet(K_LISTS, []).filter(function (x) { return !shared || x.id !== shared.id; });
    if (recent.length) {
      h += '<div class="pk-card pk-recent"><b>共有したリスト</b><ul>' + recent.map(function (x) {
        return '<li><a href="/packing/?l=' + esc(x.id) + '">' + esc((x.name || '山は未定') + '・' + dateLabel(x.date) + '・' + (STAY[x.stay] || '')) + '</a></li>';
      }).join('') + '</ul></div>';
    }
    h += sourcesHtml(gs);
    root.innerHTML = h;
    bind();
  }

  function setCheck(k, on) {
    if (shared) {
      var me = devId();
      if (!(shared.data.members || {})[me]) join(lsGet(K_NAME, '') || autoName(), false);
      shared.data.members[me].checks = shared.data.members[me].checks || {};
      if (on) shared.data.members[me].checks[k] = true; else delete shared.data.members[me].checks[k];
      draw();
      api(on ? 'PUT' : 'DELETE', shared.id + '/members/' + me + '/checks/' + k, on ? true : undefined).catch(function () { msg('保存できませんでした。通信を確かめてください。'); });
      return;
    }
    var o = localStore();
    o.c = o.c || {};
    if (on) o.c[k] = 1; else delete o.c[k];
    saveLocal(o); draw();
  }

  function addExtra(label) {
    label = label.trim().slice(0, 40);
    if (!label) return;
    var key = rand(8, 'abcdefghijklmnopqrstuvwxyz0123456789');
    if (shared) {
      var me = (shared.data.members || {})[devId()];
      var rec = { label: label, by: (me && me.name) || '', at: Date.now() };
      shared.data.extra = shared.data.extra || {};
      shared.data.extra[key] = rec;
      draw();
      api('PUT', shared.id + '/extra/' + key, rec).catch(function () { msg('保存できませんでした。通信を確かめてください。'); });
      return;
    }
  }
  function delExtra(key) {
    if (shared) {
      if (shared.data.extra) delete shared.data.extra[key];
      draw();
      api('DELETE', shared.id + '/extra/' + key).catch(function () {});
      return;
    }
  }

  function listText() {
    var m = mountain(), lines = [(m ? m.name : '登山') + 'の持ち物（' + dateLabel(state.date) + '・' + STAY[state.stay] + '）'];
    var ck = myChecks();
    var cu = custom();
    groups().forEach(function (g) {
      var its = g.items.filter(function (it) { return !cu.hidden[fkey(it.id)]; });
      if (!its.length) return;
      lines.push(''); lines.push('■ ' + g.title);
      its.forEach(function (it) { lines.push((ck[fkey(it.id)] ? '☑ ' : '□ ') + it.label); });
    });
    if (cu.mine.length) {
      lines.push(''); lines.push('■ 自分の持ち物');
      cu.mine.forEach(function (x) { lines.push((ck['m_' + x.k] ? '☑ ' : '□ ') + x.label); });
    }
    var xs = extras(), xk = Object.keys(xs);
    if (xk.length) {
      lines.push(''); lines.push('■ みんなで足した持ち物');
      xk.forEach(function (key) { lines.push((ck['x_' + key] ? '☑ ' : '□ ') + xs[key].label); });
    }
    lines.push(''); lines.push(shared ? location.origin + '/packing/?l=' + shared.id : location.origin + '/packing/');
    return lines.join('\n');
  }
  function copyText(text, done) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { msg(done); }, function () { window.prompt('コピーしてください', text); });
    } else { window.prompt('コピーしてください', text); }
  }
  function sendLink() {
    var m = mountain();
    var url = location.origin + '/packing/?l=' + shared.id;
    var text = (m ? m.name : '登山') + '（' + dateLabel(state.date) + '・' + STAY[state.stay] + '）の持ち物リストです。持っていく物にチェックしてください';
    if (navigator.share) { navigator.share({ title: '持ち物リスト', text: text, url: url }).catch(function () {}); return; }
    copyText(text + '\n' + url, 'リンクをコピーしました。LINE などに貼って送ってください。');
  }
  function remember(id) {
    var m = mountain();
    var list = lsGet(K_LISTS, []).filter(function (x) { return x.id !== id; });
    list.unshift({ id: id, name: m ? m.name : '', date: state.date, stay: state.stay });
    lsSet(K_LISTS, list.slice(0, 10));
  }
  function forget(id) { lsSet(K_LISTS, lsGet(K_LISTS, []).filter(function (x) { return x.id !== id; })); }

  // 名前は聞かない（運営者の指示）。自動で「メンバー1」「メンバー2」…。付けたい人は「名前を変える」で
  function autoName() {
    var used = {};
    Object.keys((shared && shared.data.members) || {}).forEach(function (id) { used[(shared.data.members[id] || {}).name] = 1; });
    var n = 1;
    while (used['メンバー' + n]) n++;
    return 'メンバー' + n;
  }
  function askName() {
    var n = window.prompt('仲間のリストに表示する名前', lsGet(K_NAME, ''));
    if (n === null) return null;
    n = n.trim().slice(0, 20);
    if (!n) return null;
    lsSet(K_NAME, n);
    return n;
  }

  function createShared() {
    var name = lsGet(K_NAME, '') || 'メンバー1';
    var id = rand(20, 'abcdefghijklmnopqrstuvwxyz0123456789');
    var base = /^\d{4}-\d{2}-\d{2}$/.test(state.date) ? new Date(state.date + 'T00:00:00+09:00').getTime() : Date.now();
    var now = Date.now();
    var expire = Math.max(base, now) + 30 * 86400000;
    var local = localStore(), me = devId(), checks = {}, extra = {};
    Object.keys(local.c || {}).forEach(function (k) { checks[k] = true; });
    var members = {};
    members[me] = { name: name, at: now, checks: checks };
    var body = { v: 1, mid: state.mid || '-', date: state.date || '-', stay: state.stay, createdAt: now, expireAt: expire, members: members, extra: extra };
    api('PUT', id, body).then(function () {
      shared = { id: id, data: body };
      remember(id);
      history.replaceState(null, '', '/packing/?l=' + id);
      watch(id);
      draw();
      sendLink();
    }).catch(function () { msg('共有のリストを作れませんでした。時間をおいてもう一度試してください。'); });
  }
  // keep：その名前を、この端末の名前として覚えるか（「名前を変える」で付けたときだけ。自動の「メンバー◯」は覚えない）
  function join(name, keep) {
    name = (name || '').trim().slice(0, 20);
    if (!name) return;
    if (keep) lsSet(K_NAME, name);
    var me = devId(), rec = { name: name, at: Date.now() };
    shared.data.members = shared.data.members || {};
    var old = shared.data.members[me];
    if (old && old.checks) rec.checks = old.checks;
    shared.data.members[me] = rec;
    remember(shared.id);
    draw();
    api('PATCH', shared.id + '/members/' + me, { name: name, at: rec.at }).catch(function () { msg('保存できませんでした。通信を確かめてください。'); });
  }
  function openShared(id) {
    root.innerHTML = '<p class="pk-loading">共有のリストを読み込んでいます…</p>';
    api('GET', id).then(function (d) {
      if (!d || !d.stay) {
        forget(id);
        root.innerHTML = '<div class="pk-card"><b>このリストは見つかりませんでした</b><p>登る日の30日後に消えたか、リンクが間違っている可能性があります。</p><p><a href="/packing/">新しくリストを作る →</a></p></div>';
        return;
      }
      shared = { id: id, data: d };
      state.mid = d.mid === '-' ? '' : d.mid;
      state.date = d.date === '-' ? '' : d.date;
      state.stay = d.stay;
      watch(id);
      // 開いた人は、名前を聞かずにそのまま参加する
      if (!(d.members || {})[devId()]) join(lsGet(K_NAME, '') || autoName(), false);
      else { remember(id); draw(); }
    }).catch(function () {
      root.innerHTML = '<div class="pk-card"><b>リストを読み込めませんでした</b><p>通信を確かめて、もう一度開いてください。</p></div>';
    });
  }

  function bind() {
    var q = function (s) { return root.querySelector(s); };
    var all = function (s, f) { Array.prototype.forEach.call(root.querySelectorAll(s), f); };
    if (q('[data-pk-mid]')) q('[data-pk-mid]').addEventListener('change', function () { state.mid = this.value; state.tuneOpen = true; draw(); });
    if (q('[data-pk-untune]')) q('[data-pk-untune]').addEventListener('click', function () { state.mid = ''; state.date = ''; state.tuneOpen = false; draw(); });
    if (q('.pk-tune')) q('.pk-tune').addEventListener('toggle', function () { state.tuneOpen = this.open; });
    if (q('[data-pk-date]')) q('[data-pk-date]').addEventListener('change', function () { state.date = this.value; state.tuneOpen = true; draw(); });
    all('[data-pk-stay]', function (b) { b.addEventListener('click', function () { state.stay = b.getAttribute('data-pk-stay'); draw(); }); });
    all('[data-pk-k]', function (c) { c.addEventListener('change', function () { setCheck(c.getAttribute('data-pk-k'), c.checked); }); });
    all('[data-pk-delx]', function (b) { b.addEventListener('click', function () { delExtra(b.getAttribute('data-pk-delx')); }); });
    all('[data-pk-hide]', function (b) { b.addEventListener('click', function () { hideItem(b.getAttribute('data-pk-hide'), true); }); });
    all('[data-pk-unhide]', function (b) { b.addEventListener('click', function () { hideItem(b.getAttribute('data-pk-unhide'), false); }); });
    all('[data-pk-delmine]', function (b) { b.addEventListener('click', function () { delMine(b.getAttribute('data-pk-delmine')); }); });
    if (q('[data-pk-edit]')) q('[data-pk-edit]').addEventListener('click', function () { state.edit = !state.edit; draw(); });
    var addm = function () { var i = q('[data-pk-newmine]'); addMine(i.value); };
    if (q('[data-pk-addmine]')) q('[data-pk-addmine]').addEventListener('click', addm);
    if (q('[data-pk-newmine]')) q('[data-pk-newmine]').addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); addm(); } });
    var add = function () { var i = q('[data-pk-newx]'); addExtra(i.value); };
    if (q('[data-pk-addx]')) q('[data-pk-addx]').addEventListener('click', add);
    if (q('[data-pk-newx]')) q('[data-pk-newx]').addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); add(); } });
    if (q('[data-pk-share]')) q('[data-pk-share]').addEventListener('click', createShared);
    if (q('[data-pk-copy]')) q('[data-pk-copy]').addEventListener('click', function () { copyText(listText(), 'コピーしました。LINE やメモに貼り付けられます。'); });
    if (q('[data-pk-reset]')) q('[data-pk-reset]').addEventListener('click', function () { var o = localStore(); o.c = {}; saveLocal(o); draw(); });
    if (q('[data-pk-sendlink]')) q('[data-pk-sendlink]').addEventListener('click', sendLink);
    if (q('[data-pk-rename]')) q('[data-pk-rename]').addEventListener('click', function () { var n = askName(); if (n) join(n, true); });
    if (q('[data-pk-leave]')) q('[data-pk-leave]').addEventListener('click', function () {
      unwatch(); shared = null; history.replaceState(null, '', '/packing/'); draw();
    });
  }

  function start() {
    var qs = new URLSearchParams(location.search);
    Promise.all([
      fetch('/data/packing_mountains.json').then(function (r) { return r.json(); }),
      window.YMPacking.load()
    ]).then(function (a) {
      MOUNTAINS = a[0]; DATA = a[1];
      MOUNTAINS.forEach(function (m) { BY[m.id] = m; });
      var l = qs.get('l');
      if (l && /^[a-z0-9]{20}$/.test(l) && DB) {
        var robots = document.createElement('meta'); robots.name = 'robots'; robots.content = 'noindex';
        document.head.appendChild(robots);
        openShared(l);
        return;
      }
      state.mid = BY[qs.get('m')] ? qs.get('m') : '';
      // マイページの登山計画からは山名で来る（?n=山名）
      if (!state.mid && qs.get('n')) MOUNTAINS.forEach(function (m) { if (m.name === qs.get('n')) state.mid = m.id; });
      state.date = /^\d{4}-\d{2}-\d{2}$/.test(qs.get('d') || '') ? qs.get('d') : '';
      state.stay = STAY[qs.get('s')] ? qs.get('s') : (state.mid && BY[state.mid].elev >= 2500 ? 'hut' : 'day');
      draw();
    }).catch(function () {
      root.innerHTML = '<p class="pk-loading">持ち物リストを読み込めませんでした。通信を確かめてください。</p>';
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
