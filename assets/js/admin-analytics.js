/* 管理画面（/admin/）の「分析」タブ。
   - Google でログインした運営者だけに、Search Console・GA4・Firebase の数字を出す
   - 数字は Firebase のデータベース /adminDash にある（scripts/admin_dashboard.py が毎週書く）。読めるのは
     scripts/firebase_rules.json で決めた運営者のアカウントだけ。ページや公開のファイルには数字を置かない
   - ログインは30日保つ。30日たったら、もう一度ログインを求める（ym_admin_auth_at）
   - 楽天・Amazon の報酬は API で取れないので、月ごとに手で入れる（/adminDash/revenue/YYYY-MM）
   - FB_WEB.apiKey が空のあいだは、設定待ちの案内だけを出す */
(function () {
  'use strict';
  var FB_WEB = {
    apiKey: '',
    authDomain: 'yamatch-35abd.firebaseapp.com',
    projectId: 'yamatch-35abd',
    appId: '',
    databaseURL: 'https://yamatch-35abd-default-rtdb.asia-southeast1.firebasedatabase.app'
  };
  var SDK = 'https://www.gstatic.com/firebasejs/10.12.2/';
  var KEEP_DAYS = 30;
  var AT_KEY = 'ym_admin_auth_at';
  var root, started = false, fbApp = null;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function num(n) { return (n == null || isNaN(n)) ? '—' : Number(n).toLocaleString('ja-JP'); }
  function pct(n, d) { return (n == null) ? '—' : (Math.round(n * 1000) / 10) + '%'; }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { if (v == null) { localStorage.removeItem(k); } else { localStorage.setItem(k, v); } } catch (e) {} }

  // 前の期間との差（＋◯%）。順位は小さいほど良いので reverse
  function diff(cur, prev, reverse) {
    if (cur == null || prev == null || prev === 0) { return ''; }
    var r = (cur - prev) / prev;
    var good = reverse ? r < 0 : r > 0;
    var s = (r > 0 ? '+' : '') + Math.round(r * 1000) / 10 + '%';
    return '<span class="an-diff ' + (Math.abs(r) < 0.02 ? '' : (good ? 'up' : 'down')) + '">' + s + '</span>';
  }

  function loadScript(src) {
    return new Promise(function (ok, ng) {
      var s = document.createElement('script');
      s.src = src; s.onload = ok; s.onerror = ng;
      document.head.appendChild(s);
    });
  }

  function msg(html) { root.innerHTML = '<div class="an-box">' + html + '</div>'; }

  function start() {
    root = document.getElementById('analytics-root');
    if (!root || started) { return; }
    started = true;
    if (!FB_WEB.apiKey) {
      msg('<b>設定待ち</b><p>Firebase の「ウェブアプリの設定」と「Google でのログイン」を有効にすると、ここに数字が出ます。手順は Claude のアプリで案内しています。</p>');
      return;
    }
    msg('読み込み中...');
    loadScript(SDK + 'firebase-app-compat.js')
      .then(function () { return loadScript(SDK + 'firebase-auth-compat.js'); })
      .then(function () { return loadScript(SDK + 'firebase-database-compat.js'); })
      .then(function () {
        fbApp = window.firebase.initializeApp(FB_WEB, 'ym-admin');
        var auth = fbApp.auth();
        auth.setPersistence(window.firebase.auth.Auth.Persistence.LOCAL);
        auth.onAuthStateChanged(function (user) {
          if (!user) { showLogin(); return; }
          var at = Number(lsGet(AT_KEY) || 0);
          if (!at || Date.now() - at > KEEP_DAYS * 86400000) {   // 30日たった → もう一度ログイン
            lsSet(AT_KEY, null);
            auth.signOut();
            return;
          }
          loadData(user);
        });
      })
      .catch(function () { msg('Firebase の読み込みに失敗しました。通信を確かめて、ページを開き直してください。'); });
  }

  function showLogin() {
    msg('<b>運営者のログイン</b><p>アクセス数・検索語・リンクのクリックなどの数字は、運営者の Google アカウントでログインしたときだけ表示します。ログインは' + KEEP_DAYS + '日間保たれます。</p>' +
      '<button type="button" class="an-btn" id="an-login">Google でログイン</button>');
    document.getElementById('an-login').onclick = function () {
      var auth = fbApp.auth();
      var p = new window.firebase.auth.GoogleAuthProvider();
      auth.signInWithPopup(p).then(function () {
        lsSet(AT_KEY, String(Date.now()));
      }).catch(function (e) {
        if (e && (e.code === 'auth/popup-blocked' || e.code === 'auth/operation-not-supported-in-this-environment')) {
          lsSet(AT_KEY, String(Date.now()));
          auth.signInWithRedirect(p);
          return;
        }
        if (e && e.code === 'auth/popup-closed-by-user') { return; }
        alert('ログインできませんでした：' + (e && e.code ? e.code : e));
      });
    };
  }

  function loadData(user) {
    msg('数字を読み込み中...');
    var db = fbApp.database();
    Promise.all([db.ref('adminDash/latest').once('value'), db.ref('adminDash/revenue').once('value'), db.ref('adminDash/history').once('value')])
      .then(function (r) { render(user, r[0].val(), r[1].val() || {}, r[2].val() || {}); })
      .catch(function (e) {
        // 読む権限が無い＝運営者のアカウントとしてまだ登録されていない（または別のアカウント）
        msg('<b>このアカウントには表示の権限がありません</b><p>運営者のアカウントなら、下の ID を Claude のアプリに伝えてください。データベースのルールに登録します。</p>' +
          '<div class="an-uid">' + esc(user.uid) + '</div><p class="an-sub">' + esc(user.email || '') + '</p>' +
          '<button type="button" class="an-btn an-btn-sub" id="an-out">ログアウト</button>');
        document.getElementById('an-out').onclick = logout;
      });
  }

  function logout() {
    lsSet(AT_KEY, null);
    fbApp.auth().signOut();
  }

  // 小さな折れ線（直近90日）
  function spark(rows, idx, color) {
    if (!rows || rows.length < 2) { return ''; }
    var w = 300, h = 48, max = 0, i;
    for (i = 0; i < rows.length; i++) { if (rows[i][idx] > max) { max = rows[i][idx]; } }
    if (!max) { return ''; }
    var pts = [];
    for (i = 0; i < rows.length; i++) {
      pts.push((i * w / (rows.length - 1)).toFixed(1) + ',' + (h - 2 - rows[i][idx] * (h - 6) / max).toFixed(1));
    }
    return '<svg class="an-spark" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none"><polyline fill="none" stroke="' + color + '" stroke-width="1.6" points="' + pts.join(' ') + '"/></svg>' +
      '<div class="an-spark-cap"><span>' + esc(rows[0][0]) + '</span><span>' + esc(rows[rows.length - 1][0]) + '</span></div>';
  }

  function kpi(label, val, d, note) {
    return '<div class="an-kpi"><div class="an-kpi-l">' + label + '</div><div class="an-kpi-v">' + val + '</div><div class="an-kpi-d">' + (d || '') + (note ? ' <span class="an-sub">' + note + '</span>' : '') + '</div></div>';
  }

  function table(head, rows) {
    if (!rows.length) { return '<p class="an-sub">該当なし</p>'; }
    var h = '<div class="an-tw"><table class="an-t"><thead><tr>';
    for (var i = 0; i < head.length; i++) { h += '<th>' + head[i] + '</th>'; }
    h += '</tr></thead><tbody>';
    for (var j = 0; j < rows.length; j++) {
      h += '<tr>';
      for (var k = 0; k < rows[j].length; k++) { h += '<td>' + rows[j][k] + '</td>'; }
      h += '</tr>';
    }
    return h + '</tbody></table></div>';
  }

  function sec(title, what, body) {
    return '<section class="an-sec"><h3>' + title + '</h3>' + (what ? '<p class="an-what">' + what + '</p>' : '') + body + '</section>';
  }

  function link(path, label) {
    return '<a href="' + esc(path) + '" target="_blank" rel="noopener">' + esc(label || path) + '</a>';
  }

  function render(user, d, revenue, history) {
    var h = '<div class="an-top"><span>更新：' + esc(d ? d.generatedAt : '—') + '（毎週月曜）</span><button type="button" class="an-btn an-btn-sub" id="an-out">ログアウト</button></div>';
    if (!d) {
      root.innerHTML = h + '<div class="an-box">まだ数字がありません。GitHub の Actions で「管理画面の分析の数字を作る」を手動で実行してください。</div>';
      document.getElementById('an-out').onclick = logout;
      return;
    }
    var sc = d.sc || {}, ga = d.ga || {}, fb = d.fb || {};
    var st = sc.total || {}, sp = sc.prevTotal || {}, gt = ga.total || {}, gp = ga.prevTotal || {};
    var ret = 0, allU = 0;
    (ga.newVsReturning || []).forEach(function (x) { allU += x.users; if (x.name === 'returning') { ret = x.users; } });
    var per1000 = gt.screenPageViews ? Math.round(ga.affTotal * 10000 / gt.screenPageViews) / 10 : 0;
    var per1000p = gp.screenPageViews ? Math.round(ga.affPrevTotal * 10000 / gp.screenPageViews) / 10 : 0;

    h += '<p class="an-sub">直近28日（検索 ' + esc((sc.range || []).join('〜')) + '）と、その前の28日との比較</p>';
    h += '<div class="an-kpis">' +
      kpi('検索からのクリック', num(st.clicks), diff(st.clicks, sp.clicks)) +
      kpi('検索での表示', num(st.impressions), diff(st.impressions, sp.impressions)) +
      kpi('平均の掲載順位', st.position || '—', diff(st.position, sp.position, true), '小さいほど上') +
      kpi('訪れた人', num(gt.activeUsers), diff(gt.activeUsers, gp.activeUsers)) +
      kpi('ページの表示', num(gt.screenPageViews), diff(gt.screenPageViews, gp.screenPageViews)) +
      kpi('くり返し来た人', allU ? pct(ret / allU) : '—', '', num(ret) + '人') +
      kpi('楽天・Amazonのクリック', num(ga.affTotal), diff(ga.affTotal, ga.affPrevTotal)) +
      kpi('1,000表示あたりのクリック', per1000, diff(per1000, per1000p)) +
      '</div>';
    h += '<div class="an-two"><div><div class="an-sub">検索からのクリック（90日）</div>' + spark(sc.daily, 1, '#4e6535') + '</div>' +
      '<div><div class="an-sub">訪れた人（90日）</div>' + spark(ga.daily, 1, '#8a6d3b') + '</div></div>';

    // 報酬（手入力）
    h += sec('報酬（手入力）', '楽天・Amazon の管理画面で見た月ごとの報酬を入れます。クリック数と並べて、効いている月が分かるようにします。', revenueHtml(revenue));

    // ページの種類ごと
    var gs = {};
    (sc.groups || []).forEach(function (x) { gs[x.name] = x; });
    h += sec('ページの種類ごと', 'どこで人が来て、どこでリンクが押されているか。「1,000表示あたり」が低い種類は、装備・商品への導線を足す候補です。',
      table(['種類', '表示', '前の28日', '楽天・Amazon', '1,000表示あたり', '検索クリック'],
        (ga.groups || []).map(function (x) {
          var g = gs[x.name] || {};
          return [esc(x.name), num(x.views), diff(x.views, x.prevViews), num(x.aff) + ' ' + diff(x.aff, x.prevAff), x.affPer1000, num(g.clicks)];
        })));

    // リンクのクリック
    var by = ga.affBy || {};
    var byHtml = '';
    if (by.platform && by.platform.missing) {
      byHtml = '<p class="an-note">Amazon と楽天の内訳・商品ごとの内訳は、GA4 の「カスタム定義」に platform・product_name・page_type を登録すると、その日から出ます。</p>';
    } else {
      byHtml = '<div class="an-two"><div>' + table(['Amazon・楽天', 'クリック'], ((by.platform || {}).rows || []).map(function (x) { return [esc(x.name), num(x.clicks)]; })) + '</div>' +
        '<div>' + table(['商品', 'クリック'], ((by.product || {}).rows || []).slice(0, 10).map(function (x) { return [esc(x.name), num(x.clicks)]; })) + '</div></div>';
    }
    h += sec('楽天・Amazon のリンクが押されたページ', 'いまの収入の入口。上位のページは、装備の説明を厚くすると伸ばしやすい。', byHtml +
      table(['ページ', 'クリック', '表示', '1,000表示あたり'], (ga.affPages || []).map(function (x) {
        return [link(x.page, x.label), num(x.clicks), num(x.views), x.per1000 == null ? '—' : x.per1000];
      })));
    h += sec('よく見られているのに、リンクが押されていない山ページ', '表示が100回以上でクリックが0。装備カードの商品・説明の見直し候補。',
      table(['山', '表示'], (ga.mountainsNoAff || []).map(function (x) { return [link(x.page, x.label), num(x.views)]; })));

    // 検索の伸びしろ
    h += sec('あと一歩の検索語', '4〜15位で表示が多い語。見出し・説明文・本文をその語に答える形にすると、クリックが増えやすい（取りこぼしの大きい順）。',
      table(['検索語', '表示', 'クリック', '順位', 'ページ'], (sc.nearMiss || []).slice(0, 15).map(function (x) {
        return [esc(x.query), num(x.impressions), num(x.clicks), x.position, link(x.page)];
      })));
    h += sec('クリック率が低いページ', '表示が多いのに、その順位の目安よりクリック率が低い。検索結果の見出し・説明文の見直し候補。',
      table(['ページ', '表示', 'クリック率', '順位'], (sc.lowCtr || []).map(function (x) {
        return [link(x.page), num(x.impressions), pct(x.ctr), x.position];
      })));
    var qm = sc.queryMovers || {}, pm = sc.pageMovers || {};
    h += sec('伸びた・落ちた（検索からのクリック）', '落ちたものは、順位が下がったか・季節の終わりかを確かめる。',
      '<div class="an-two"><div><div class="an-sub">伸びた検索語</div>' + table(['検索語', '差', '今'], (qm.up || []).slice(0, 8).map(function (x) { return [esc(x.query), '+' + x.diff, num(x.clicks)]; })) + '</div>' +
      '<div><div class="an-sub">落ちた検索語</div>' + table(['検索語', '差', '今'], (qm.down || []).slice(0, 8).map(function (x) { return [esc(x.query), x.diff, num(x.clicks)]; })) + '</div></div>' +
      '<div class="an-two"><div><div class="an-sub">伸びたページ</div>' + table(['ページ', '差', '今'], (pm.up || []).slice(0, 8).map(function (x) { return [link(x.page), '+' + x.diff, num(x.clicks)]; })) + '</div>' +
      '<div><div class="an-sub">落ちたページ</div>' + table(['ページ', '差', '今'], (pm.down || []).slice(0, 8).map(function (x) { return [link(x.page), x.diff, num(x.clicks)]; })) + '</div></div>');

    // 利用者
    h += sec('使っている人', '',
      '<div class="an-two"><div>' + table(['端末', '人'], (ga.device || []).map(function (x) { return [esc(x.name), num(x.users)]; })) + '</div>' +
      '<div>' + table(['来た経路', '訪問'], (ga.channel || []).map(function (x) { return [esc(x.name), num(x.sessions)]; })) + '</div></div>' +
      '<p class="an-sub">1人あたりの利用時間：約' + Math.round((gt.engagementSecPerUser || 0) / 6) / 10 + '分（前の28日 約' + Math.round((gp.engagementSecPerUser || 0) / 6) / 10 + '分）</p>');
    h += sec('よく見られている山', '',
      table(['山', '表示', '前の28日', 'リンクのクリック'], (ga.topMountains || []).map(function (x) { return [link(x.page, x.label), num(x.views), diff(x.views, x.prevViews), num(x.aff)]; })));

    // 機能
    var c = fb.counts || {}, pu = fb.push || {};
    h += sec('機能の利用', '',
      table(['機能', '表示', '前の28日'], (ga.features || []).map(function (x) { return [esc(x.name), num(x.views), diff(x.views, x.prevViews)]; })) +
      '<p class="an-sub">お気に入り 合計 ' + num(c.fav) + '・登頂 合計 ' + num(c.climbed) + '／山小屋の予約開始のプッシュ通知 ' + num(pu.devices) + '台・' + num(pu.alerts) + '件</p>' +
      table(['お気に入りの多い山', 'お気に入り', '登頂'], (c.topFav || []).map(function (x) { return [esc(x.label), num(x.fav), num(x.climbed)]; })));

    // 推移
    var hk = Object.keys(history).sort().slice(-12);
    h += sec('週ごとの推移', '毎週月曜の時点の「直近28日」。',
      table(['日付', '検索クリック', '訪れた人', 'リンクのクリック'], hk.map(function (k) { var x = history[k] || {}; return [esc(k), num(x.scClicks), num(x.users), num(x.aff)]; })));

    root.innerHTML = h;
    document.getElementById('an-out').onclick = logout;
    bindRevenue();
  }

  function revenueHtml(rev) {
    var ks = Object.keys(rev).sort().reverse().slice(0, 12);
    var now = new Date();
    var ym = now.getFullYear() + '-' + ('0' + (now.getMonth() + 1)).slice(-2);
    return table(['月', '楽天', 'Amazon', '合計'], ks.map(function (k) {
      var x = rev[k] || {};
      return [esc(k), num(x.rakuten) + '円', num(x.amazon) + '円', num((x.rakuten || 0) + (x.amazon || 0)) + '円'];
    })) +
      '<div class="an-form"><input type="month" id="an-ym" value="' + ym + '"><input type="number" id="an-rk" placeholder="楽天（円）" min="0"><input type="number" id="an-az" placeholder="Amazon（円）" min="0">' +
      '<button type="button" class="an-btn" id="an-save">記録する</button></div>';
  }

  function bindRevenue() {
    var b = document.getElementById('an-save');
    if (!b) { return; }
    b.onclick = function () {
      var ym = document.getElementById('an-ym').value;
      var rk = document.getElementById('an-rk').value;
      var az = document.getElementById('an-az').value;
      if (!/^\d{4}-\d{2}$/.test(ym) || (rk === '' && az === '')) { alert('月と金額を入れてください'); return; }
      var v = { rakuten: rk === '' ? 0 : Math.round(Number(rk)), amazon: az === '' ? 0 : Math.round(Number(az)), at: Date.now() };
      fbApp.database().ref('adminDash/revenue/' + ym).set(v).then(function () {
        loadData(fbApp.auth().currentUser);
      }).catch(function (e) { alert('記録できませんでした：' + (e && e.code ? e.code : e)); });
    };
  }

  window.ymAdminAnalyticsStart = start;
})();
