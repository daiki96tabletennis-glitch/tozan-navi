/* 山小屋の予約開始のお知らせ。
   - 山小屋ページの #hut-alert に設定欄を出す（ホーム画面に追加して開いているときだけ使える）
   - どのページでも、開いたときに登録済みのお知らせを確かめ、1週間前・前日・当日に画面上部と端末の通知で知らせる
   - マイページの #ym-hut-alerts に一覧を出す
   登録は端末の中（localStorage の ym_hut_alerts）に保存する。サーバーには送らない。
   予約の型（rule）は scripts/huts_rules.py が作る：rel（何日前・何か月前）/ mon（月ごと）/ fix（一斉）/ phase（期間区切り） */
(function () {
  var KEY = 'ym_hut_alerts';
  var FKEY = 'ym_hut_favs';          // お気に入りの山小屋（小屋IDの配列）
  var DATA = null;                   // /data/huts_rules.json の huts（小屋ID → {n:名前, mts:[山名], s:予約の開始, r:型}）
  var DAY = 86400000;
  var STAGES = [7, 1, 0];
  var now = new Date();
  var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  var standalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || window.navigator.standalone === true;

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function load() {
    try { var v = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(v) ? v : []; } catch (e) { return []; }
  }
  function save(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); return true; } catch (e) { return false; }
  }
  function ymd(d) { return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function parse(s) { var p = String(s).split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function jp(d) { return d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日（' + '日月火水木金土'.charAt(d.getDay()) + '）'; }
  function mk(y, m, d) { var last = new Date(y, m, 0).getDate(); return new Date(y, m - 1, Math.min(d, last)); }
  function addMonths(d, n) { var t = new Date(d.getFullYear(), d.getMonth() + n, 1); return mk(t.getFullYear(), t.getMonth() + 1, d.getDate()); }

  /* 予約の型と泊まりたい日 → {open: 予約開始日, guess: 前の年の日付からの目安か, time, msg}。計算できないときは {err: 理由} */
  function compute(rule, stay) {
    var s = stay ? parse(stay) : null, o, i, p, md, y;
    if (!rule) { return { err: 'この山小屋は通知に対応していません' }; }
    if (rule.t === 'rel') {
      if (!s) { return { err: '泊まりたい日を選んでください' }; }
      o = rule.u === 'm' ? addMonths(s, -rule.n) : new Date(s.getTime() - rule.n * (rule.u === 'w' ? 7 : 1) * DAY);
      o = new Date(o.getFullYear(), o.getMonth(), o.getDate());
      return { open: o, time: rule.time };
    }
    if (rule.t === 'mon') {
      if (!s) { return { err: '泊まりたい日を選んでください' }; }
      o = new Date(s.getFullYear(), s.getMonth() - rule.n, rule.d || 1);
      return { open: o, time: rule.time };
    }
    if (rule.t === 'fix') {
      // 泊まる年が分かればその年、分からなければ次に来る日付。データの年より先の年は、同じ月日を「目安」として出す
      y = s ? s.getFullYear() : today.getFullYear();
      o = mk(y, rule.m, rule.d);
      if (s && o > s) { o = mk(y - 1, rule.m, rule.d); }
      if (!s && o < today) { o = mk(y + 1, rule.m, rule.d); }
      return { open: o, time: rule.time, guess: !!rule.y && o.getFullYear() !== rule.y };
    }
    if (rule.t === 'phase') {
      if (!s) { return { err: '泊まりたい日を選んでください' }; }
      md = ('0' + (s.getMonth() + 1)).slice(-2) + '-' + ('0' + s.getDate()).slice(-2);
      for (i = 0; i < rule.p.length; i++) {
        p = rule.p[i];
        if (md >= p.f && md <= p.e) {
          y = s.getFullYear() + (p.oy || 0);
          o = mk(y, p.m, p.d);
          return { open: o, time: p.time, guess: !!rule.y && y !== rule.y };
        }
      }
      return { err: 'この日の予約開始日はデータにありません。公式サイトで確認してください' };
    }
    return { err: 'この山小屋は通知に対応していません' };
  }

  function typeLabel(rule) {
    if (!rule) { return ''; }
    if (rule.t === 'rel') { return '宿泊日の' + rule.n + (rule.u === 'm' ? 'か月' : rule.u === 'w' ? '週間' : '日') + '前に予約開始'; }
    if (rule.t === 'mon') { return '宿泊月の' + rule.n + 'か月前の' + (rule.d || 1) + '日に予約開始'; }
    if (rule.t === 'fix') { return 'シーズン分をまとめて予約開始（' + rule.m + '月' + rule.d + '日' + (rule.y ? '・' + rule.y + '年' : '・例年') + '）'; }
    if (rule.t === 'phase') { return '宿泊する時期ごとに予約開始日が違う'; }
    return '';
  }

  /* ---------- 開いたときの確認 ---------- */
  function stageOf(open) {
    var left = Math.round((open - today) / DAY);
    if (left <= 0) { return left >= -14 ? 0 : null; }       // 当日〜2週間後までは「予約が始まっています」
    if (left <= 1) { return 1; }
    if (left <= 7) { return 7; }
    return -1;                                                // まだ先
  }

  function notify(title, body, url) {
    if (!standalone || !('Notification' in window) || Notification.permission !== 'granted' || !navigator.serviceWorker) { return; }
    navigator.serviceWorker.register('/sw.js').then(function (reg) {
      return navigator.serviceWorker.ready.then(function () {
        return reg.showNotification(title, { body: body, icon: '/icon-192.png', badge: '/icon-192.png', data: { url: url }, tag: 'ym-hut-' + url });
      });
    }).catch(function () {});
  }

  function banner(items) {
    if (!items.length || document.getElementById('ym-hut-banner')) { return; }
    var el = document.createElement('div'), i, h = '';
    el.id = 'ym-hut-banner';
    el.setAttribute('role', 'status');
    el.style.cssText = 'position:fixed;left:8px;right:8px;top:8px;z-index:9999;max-width:560px;margin:0 auto;background:#fff;border:1px solid #c8d4b8;border-left:5px solid #4e6535;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.18);padding:10px 36px 10px 12px;font-size:13px;line-height:1.55;color:#2f2b26';
    for (i = 0; i < items.length; i++) {
      h += '<div style="margin:2px 0"><b>' + esc(items[i].title) + '</b><br><a href="' + esc(items[i].url) + '" style="color:#4e6535">' + esc(items[i].body) + '</a></div>';
    }
    el.innerHTML = h + '<button type="button" aria-label="閉じる" style="position:absolute;right:6px;top:4px;border:none;background:none;font-size:20px;line-height:1;color:#7a7068;cursor:pointer;padding:6px">×</button>';
    el.querySelector('button').addEventListener('click', function () { el.parentNode.removeChild(el); });
    document.body.appendChild(el);
  }

  /* ---------- 下のバーの「マイページ」に鈴を載せる（知らせることがあるあいだ） ---------- */
  var bellOn = false;
  function bellCss() {
    if (document.getElementById('ym-bell-css')) { return; }
    var st = document.createElement('style');
    st.id = 'ym-bell-css';
    // 4秒に1回、最初の0.6秒だけ小刻みに揺れる
    st.textContent = '.ym-bell{position:absolute;left:50%;top:1px;margin-left:5px;width:18px;height:18px;line-height:0;pointer-events:none;transform-origin:50% 2px;animation:ymBell 4s ease-in-out infinite}'
      + '.ym-bell svg{width:18px;height:18px;fill:#f0c030;stroke:#8a5a10;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 1px 1px rgba(0,0,0,.25))}'
      + '@keyframes ymBell{0%,15%,100%{transform:rotate(0)}2%{transform:rotate(-16deg)}4%{transform:rotate(14deg)}6%{transform:rotate(-12deg)}8%{transform:rotate(10deg)}10%{transform:rotate(-7deg)}12%{transform:rotate(4deg)}}'
      + '@media (prefers-reduced-motion:reduce){.ym-bell{animation:none}}';
    document.head.appendChild(st);
  }
  function putBell() {
    var as = document.querySelectorAll('nav a[href="/mypage/"], a[href="/mypage/"].ym-nav-item'), i, a, b;
    for (i = 0; i < as.length; i++) {
      a = as[i];
      b = a.querySelector('.ym-bell');
      if (bellOn && !b) {
        if (getComputedStyle(a).position === 'static') { a.style.position = 'relative'; }
        b = document.createElement('span');
        b.className = 'ym-bell';
        b.setAttribute('aria-label', '山小屋の予約開始のお知らせがあります');
        b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>';
        a.appendChild(b);
      } else if (!bellOn && b) {
        b.parentNode.removeChild(b);
      }
    }
  }
  function bell(on) {
    bellOn = on;
    if (on) { bellCss(); }
    putBell();
    // トップページの下のバーは後から描かれ、描き直されることがあるので、しばらくのあいだ付け直す
    if (on && !bell.timer) { bell.timer = setInterval(putBell, 1500); }
    if (!on && bell.timer) { clearInterval(bell.timer); bell.timer = null; }
  }
  function activeCount(list, rules) {
    var n = 0, i, c, st;
    for (i = 0; i < list.length; i++) {
      c = compute(rules && rules[list[i].id] ? rules[list[i].id].r : list[i].rule, list[i].stay);
      if (c.err || !c.open) { continue; }
      st = stageOf(c.open);
      if (st === 7 || st === 1 || st === 0) { n++; }
    }
    return n;
  }

  /* ホーム（トップページ）用：上に一瞬だけ出るお知らせ。2秒たつか、画面をスクロールすると消える */
  var isHome = location.pathname === '/' || location.pathname === '/index.html';
  function toast(items) {
    if (!items.length || document.getElementById('ym-hut-toast')) { return; }
    var el = document.createElement('a'), gone = false, born = Date.now();
    el.id = 'ym-hut-toast';
    el.href = '/mypage/';
    el.setAttribute('role', 'status');
    el.style.cssText = 'position:fixed;left:8px;right:8px;top:8px;z-index:9999;max-width:560px;margin:0 auto;display:block;background:#2a3820;color:#fff;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.25);padding:10px 14px;font-size:13px;line-height:1.5;text-decoration:none;opacity:0;transform:translateY(-12px);transition:opacity .25s,transform .25s';
    el.textContent = items[0].title + (items.length > 1 ? '　ほか' + (items.length - 1) + '件' : '');
    document.body.appendChild(el);
    function hide() {
      if (gone) { return; }
      gone = true;
      document.removeEventListener('scroll', onScroll, true);
      document.removeEventListener('touchmove', onScroll, true);
      document.removeEventListener('wheel', onScroll, true);
      el.style.opacity = '0';
      el.style.transform = 'translateY(-12px)';
      setTimeout(function () { if (el.parentNode) { el.parentNode.removeChild(el); } }, 300);
    }
    // ページ全体でも、中の枠でも、スクロール（指でなぞる・ホイール）が始まったら消す。出た直後の0.2秒は無視する
    function onScroll() { if (Date.now() - born > 200) { hide(); } }
    document.addEventListener('scroll', onScroll, true);
    document.addEventListener('touchmove', onScroll, true);
    document.addEventListener('wheel', onScroll, true);
    setTimeout(function () { el.style.opacity = '1'; el.style.transform = 'translateY(0)'; }, 30);
    setTimeout(hide, 2030);
  }
  function checkHome(rules) {
    var list = load(), items = [], i, c, st, left;
    for (i = 0; i < list.length; i++) {
      c = compute(rules && rules[list[i].id] ? rules[list[i].id].r : list[i].rule, list[i].stay);
      if (c.err || !c.open) { continue; }
      st = stageOf(c.open);
      if (st !== 7 && st !== 1 && st !== 0) { continue; }
      left = Math.round((c.open - today) / DAY);
      items.push({ left: left, title: list[i].name + (left > 1 ? '：予約開始まであと' + left + '日' : left === 1 ? '：あした予約開始' : left === 0 ? '：きょう予約開始' : '：予約が始まっています') });
    }
    items.sort(function (a, b) { return a.left - b.left; });
    bell(items.length > 0);
    // 1回の起動につき1度だけ出す（ページを行き来するたびに出さない）
    var seen = false;
    try { seen = sessionStorage.getItem('ym_hut_toast') === ymd(today); sessionStorage.setItem('ym_hut_toast', ymd(today)); } catch (e) {}
    if (!seen) { toast(items); }
  }

  function check(rules) {
    // ホームでは、下のバーの鈴と、上に一瞬出るお知らせだけにする（常に出る枠や端末の通知は出さない。段階の記録も進めない）
    if (isHome) { checkHome(rules); return; }
    var list = load(), changed = false, show = [], i, a, r, c, st, title, body;
    for (i = 0; i < list.length; i++) {
      a = list[i];
      r = rules && rules[a.id] ? rules[a.id].r : a.rule;       // 新しいデータがあればそちらで計算し直す（来季の日付が入ったとき）
      c = compute(r, a.stay);
      if (c.err || !c.open) { continue; }
      if (ymd(c.open) !== a.open || !!c.guess !== !!a.guess) { a.open = ymd(c.open); a.guess = !!c.guess; a.time = c.time || ''; a.shown = []; changed = true; }
      st = stageOf(c.open);
      if (st === null || st === -1) { continue; }
      if ((a.shown || []).indexOf(st) > -1) { continue; }
      title = a.name + (st === 0 ? '：予約が始まります' : st === 1 ? '：あした予約開始' : '：予約開始まであと' + Math.round((c.open - today) / DAY) + '日');
      body = (c.guess ? '昨年の日付からの目安です。' : '') + jp(c.open) + (c.time ? ' ' + c.time : '') + 'から' + (a.stay ? '（' + a.stay.replace(/-/g, '/') + ' 泊の分）' : '') + (c.guess ? '。今年の日付を公式サイトで確認してください' : '');
      show.push({ title: title, body: body, url: '/huts/' + a.id + '/' });
      a.shown = (a.shown || []).concat([st]);
      changed = true;
    }
    if (changed) { save(list); }
    banner(show);
    for (i = 0; i < show.length; i++) { notify(show[i].title, show[i].body, show[i].url); }
    renderMy(list);
    bell(activeCount(list, rules) > 0);
  }

 /* ---------- お気に入りの山小屋 ---------- */
  function favs() {
    try { var v = JSON.parse(localStorage.getItem(FKEY) || '[]'); return Array.isArray(v) ? v : []; } catch (e) { return []; }
  }
  function setFavs(v) { try { localStorage.setItem(FKEY, JSON.stringify(v)); return true; } catch (e) { return false; } }
  function paintFavs() {
    var f = favs(), bs = document.querySelectorAll('[data-fav]'), i, on;
    for (i = 0; i < bs.length; i++) {
      on = f.indexOf(bs[i].getAttribute('data-fav')) > -1;
      bs[i].setAttribute('aria-pressed', on ? 'true' : 'false');
      bs[i].setAttribute('aria-label', on ? 'お気に入りから外す' : 'お気に入りに追加');
    }
  }
  function toggleFav(id) {
    var f = favs(), i = f.indexOf(id);
    if (i > -1) { f.splice(i, 1); } else { f.push(id); }
    setFavs(f);
    paintFavs();
    renderMy(load());
  }
  document.addEventListener('click', function (ev) {
    var t = ev.target, n = 0;
    while (t && t !== document && n < 4) {
      if (t.getAttribute && t.getAttribute('data-fav')) { ev.preventDefault(); toggleFav(t.getAttribute('data-fav')); return; }
      t = t.parentNode; n++;
    }
  });

  function favHtml() {
    var f = favs(), i, d, h;
    if (!f.length) { return ''; }
    h = '<div style="background:#fff;border-radius:16px;padding:14px 16px;margin:14px 0 4px;box-shadow:0 1px 1px rgba(26,22,14,.03),0 2px 5px rgba(26,22,14,.05)">'
      + '<div style="font-size:13px;font-weight:700;color:#2a3820;margin-bottom:8px">お気に入りの山小屋</div>';
    for (i = 0; i < f.length; i++) {
      d = DATA && DATA[f[i]];
      h += '<div style="display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-top:1px solid #f0ede5;font-size:13px;line-height:1.5"><div style="flex:1;min-width:0">'
        + '<a href="/huts/' + esc(f[i]) + '/" style="color:#2a3820;font-weight:700;text-decoration:none">' + esc(d ? d.n : '山小屋のページを開く') + '</a>'
        + (d ? '<br><span style="font-size:12px;color:#5a544a">' + esc((d.mts || []).join('・')) + '</span>'
          + '<br><span style="font-size:12px;color:#7a7068">予約の開始：' + esc(d.s || '公式サイトで確認') + '</span>' : '')
        + '</div><button type="button" data-fav="' + esc(f[i]) + '" aria-pressed="true" style="flex-shrink:0;border:none;background:none;color:#a09888;font-size:11.5px;padding:2px 0;cursor:pointer">外す</button></div>';
    }
    return h + '</div>';
  }

  /* ---------- マイページの一覧 ---------- */
  function renderMy(list) {
    var box = document.getElementById('ym-hut-alerts'), i, a, o, left, h;
    if (!box) { return; }
    if (!list.length) { box.innerHTML = favHtml(); return; }
    h = favHtml() + '<div style="background:#fff;border-radius:16px;padding:14px 16px;margin:14px 0 4px;box-shadow:0 1px 1px rgba(26,22,14,.03),0 2px 5px rgba(26,22,14,.05)">'
      + '<div style="font-size:13px;font-weight:700;color:#2a3820;margin-bottom:8px">山小屋の予約開始のお知らせ</div>';
    for (i = 0; i < list.length; i++) {
      a = list[i];
      o = a.open ? parse(a.open) : null;
      left = o ? Math.round((o - today) / DAY) : null;
      h += '<div style="display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-top:1px solid #f0ede5;font-size:13px;line-height:1.5">'
        + '<div style="flex:1;min-width:0"><a href="/huts/' + esc(a.id) + '/" style="color:#2a3820;font-weight:700;text-decoration:none">' + esc(a.name) + '</a><br>'
        + '<span style="color:#5a544a">' + (o ? esc(jp(o)) + (a.time ? ' ' + esc(a.time) : '') + 'から' + (a.guess ? '（昨年の日付からの目安）' : '') : '日付未定') + '</span>'
        + (a.stay ? '<br><span style="font-size:11.5px;color:#7a7068">' + esc(a.stay.replace(/-/g, '/')) + ' に泊まる分</span>' : '') + '</div>'
        + '<div style="flex-shrink:0;text-align:right"><span style="display:inline-block;font-size:11.5px;border-radius:999px;padding:2px 9px;'
        + (left === null ? 'background:#eeece6;color:#6a6258">—' : left > 0 ? 'background:#e9efe0;color:#2a3820">あと' + left + '日' : 'background:#fbf1cf;color:#7a5a00">受付開始済み') + '</span><br>'
        + '<button type="button" data-del="' + i + '" style="border:none;background:none;color:#a09888;font-size:11.5px;padding:6px 0 0;cursor:pointer">削除</button></div></div>';
    }
    box.innerHTML = h + '</div>';
    var btns = box.querySelectorAll('[data-del]');
    for (i = 0; i < btns.length; i++) {
      btns[i].addEventListener('click', function () {
        var l = load();
        l.splice(+this.getAttribute('data-del'), 1);
        save(l);
        renderMy(l);
        bell(activeCount(l, DATA) > 0);
        if (window.YMHutAlertRefresh) { window.YMHutAlertRefresh(); }
      });
    }
  }

  /* ---------- お知らせの見本：1週間前・前日・当日の3回がどう出るかを、その場で順に見せる ---------- */
  var demoBusy = false;
  function demo(name, open, time, stay, statusEl) {
    if (demoBusy) { return; }
    demoBusy = true;
    var o = open || new Date(today.getTime() + 7 * DAY), steps = [7, 1, 0], k = 0;
    var when = function (d) { return new Date(o.getTime() - d * DAY); };
    function say(t) { if (statusEl) { statusEl.textContent = t; } }
    function step() {
      var old = document.getElementById('ym-hut-banner');
      if (old) { old.parentNode.removeChild(old); }
      if (k >= steps.length) {
        bell(activeCount(load(), DATA) > 0);
        say('見本はここまでです。実際は、それぞれの日に Yamatch を開いたときに出ます（開かなかった日のお知らせは出ません）。');
        demoBusy = false;
        return;
      }
      var d = steps[k], title = '【見本】' + name + (d === 0 ? '：予約が始まります' : d === 1 ? '：あした予約開始' : '：予約開始まであと7日');
      var body = jp(o) + (time ? ' ' + time : '') + 'から' + (stay ? '（' + stay.replace(/-/g, '/') + ' 泊の分）' : '');
      say((k + 1) + '／3　' + (d === 0 ? '当日' : d === 1 ? '前日' : '1週間前') + '（' + jp(when(d)) + '）に開いたときの表示');
      banner([{ title: title, body: body, url: location.pathname }]);
      bell(true);
      if (d === 0) { notify(title, body, location.pathname); }
      k++;
      setTimeout(step, 3200);
    }
    step();
  }
  function demoBlock() {
    return '<div class="ha-demo"><button type="button" id="ha-demo" class="ha-btn ha-btn2">お知らせの見本を見る</button>'
      + '<p id="ha-demo-s" class="ha-p" style="margin:8px 0 0;font-size:12px"></p>'
      + '<p class="ha-p" style="margin:6px 0 0;font-size:12px;color:#7a7068">見本では、1週間前・前日・当日のお知らせを約3秒ずつ順に画面の上に出します。'
      + '下のバーのあるページでは「マイページ」に鈴が付きます。端末の通知を許可している場合は、当日分の通知も1回送ります。</p></div>';
  }
  function bindDemo(name, getCur, getStay) {
    var b = document.getElementById('ha-demo');
    if (!b) { return; }
    b.addEventListener('click', function () {
      var c = getCur ? getCur() : null;
      demo(name, c && c.open ? c.open : null, c ? c.time : '', getStay ? getStay() : '', document.getElementById('ha-demo-s'));
    });
  }

  /* ---------- 山小屋ページの設定欄 ---------- */
  function setup() {
    var box = document.getElementById('hut-alert'), hut;
    if (!box) { return; }
    try { hut = JSON.parse(box.getAttribute('data-hut')); } catch (e) { return; }
    var rule = hut.rule, needDate = rule && rule.t !== 'fix';
    var head = '<div class="ha-t">予約開始のお知らせ</div>';
    if (!rule) {
      box.innerHTML = head + '<p class="ha-p">この山小屋は、予約開始日の決まり方がデータに無いため、お知らせに対応していません。</p>';
      return;
    }
    var kind = '<p class="ha-k">' + esc(typeLabel(rule)) + (rule.note ? '<br><span>' + esc(rule.note) + '</span>' : '') + '</p>';
    if (!standalone) {
      box.innerHTML = head + kind + '<p class="ha-p">Yamatch をホーム画面に追加すると、予約開始の1週間前・前日・当日にお知らせを受け取れます。'
        + 'ホーム画面のアイコンから開いたときに、この欄で泊まりたい日を登録できます。</p>'
        + '<a class="ha-btn ha-btn2" href="/">ホーム画面に追加する方法を見る</a>' + demoBlock();
      bindDemo(hut.name, function () { var c = compute(rule, needDate ? ymd(new Date(today.getTime() + 60 * DAY)) : null); return c.err ? null : c; }, function () { return ''; });
      return;
    }
    function mine() { var l = load(), i, out = []; for (i = 0; i < l.length; i++) { if (l[i].id === hut.id) { out.push(l[i]); } } return out; }
    function draw(msg) {
      var m = mine(), i, h = head + kind;
      if (needDate) {
        h += '<label class="ha-l" for="ha-date">泊まりたい日（連泊は最初の日）</label><input type="date" id="ha-date" class="ha-in" min="' + ymd(today) + '">'
          + '<div id="ha-out" class="ha-out"></div>';
      } else {
        var c = compute(rule, null);
        h += '<div class="ha-out">次の予約開始：<b>' + esc(jp(c.open)) + (c.time ? ' ' + esc(c.time) : '') + '</b>'
          + (c.guess ? '<br><span>' + rule.y + '年の日付からの目安です。今年の日付が発表されたら、この欄とお知らせの日付が切り替わります。</span>' : '') + '</div>';
      }
      h += '<button type="button" id="ha-save" class="ha-btn"' + (needDate ? ' disabled' : '') + '>この予約開始を知らせる</button>';
      if (msg) { h += '<p class="ha-msg">' + esc(msg) + '</p>'; }
      if (m.length) {
        h += '<div class="ha-list"><div class="ha-lt">登録済み</div>';
        for (i = 0; i < m.length; i++) {
          h += '<div>' + (m[i].stay ? esc(m[i].stay.replace(/-/g, '/')) + ' 泊 → ' : '') + esc(jp(parse(m[i].open))) + (m[i].time ? ' ' + esc(m[i].time) : '') + 'から' + (m[i].guess ? '（目安）' : '') + '</div>';
        }
        h += '<a href="/mypage/" class="ha-my">マイページで確認・削除</a></div>';
      }
      box.innerHTML = h + demoBlock();
      var input = document.getElementById('ha-date'), out = document.getElementById('ha-out'), btn = document.getElementById('ha-save'), cur = needDate ? null : compute(rule, null);
      if (input) {
        input.addEventListener('change', function () {
          cur = input.value ? compute(rule, input.value) : null;
          if (!cur) { out.innerHTML = ''; btn.disabled = true; return; }
          if (cur.err) { out.innerHTML = '<span>' + esc(cur.err) + '</span>'; btn.disabled = true; return; }
          var left = Math.round((cur.open - today) / DAY);
          out.innerHTML = '予約開始：<b>' + esc(jp(cur.open)) + (cur.time ? ' ' + esc(cur.time) : '') + '</b>'
            + (cur.guess ? '<br><span>' + rule.y + '年の日付からの目安です。今年の日付は公式サイトで確認してください。</span>' : '')
            + (left <= 0 ? '<br><span>この日の分は、すでに予約できる時期です。</span>' : '');
          btn.disabled = left <= 0;
        });
      }
      bindDemo(hut.name, function () { return cur && !cur.err ? cur : null; }, function () { return input ? input.value : ''; });
      btn.addEventListener('click', function () {
        if (!cur || cur.err) { return; }
        var l = load(), stay = input ? input.value : '', i;
        for (i = 0; i < l.length; i++) { if (l[i].id === hut.id && (l[i].stay || '') === stay) { draw('同じ内容がすでに登録されています。'); return; } }
        l.push({ id: hut.id, name: hut.name, stay: stay, open: ymd(cur.open), time: cur.time || '', guess: !!cur.guess, rule: rule, shown: [], at: ymd(today) });
        if (!save(l)) { draw('この端末に保存できませんでした（プライベートブラウズでは使えません）。'); return; }
        var done = function (p) {
          draw(p === 'granted' ? '登録しました。1週間前・前日・当日に、Yamatch を開いたときにお知らせします。'
            : '登録しました。端末の通知は許可されていないので、Yamatch を開いたときに画面の上にお知らせを出します。');
        };
        if ('Notification' in window && Notification.permission === 'default') {
          try { Notification.requestPermission().then(done, function () { done('denied'); }); } catch (e) { done('denied'); }
        } else {
          done('Notification' in window ? Notification.permission : 'denied');
        }
      });
    }
    window.YMHutAlertRefresh = function () { draw(''); };
    draw('');
  }

  /* ---------- 山小屋まとめの案内バナー → 説明のポップアップ（右上の×で閉じる）。中から見本を試せる ---------- */
  function promo() {
    var modal = document.getElementById('ha-modal'), opens = document.querySelectorAll('[data-ha-open]'), i;
    if (!modal || !opens.length) { return; }
    function open() { modal.style.display = 'flex'; document.body.style.overflow = 'hidden'; var x = modal.querySelector('[data-ha-close]'); if (x) { x.focus(); } }
    function close() { modal.style.display = 'none'; document.body.style.overflow = ''; }
    for (i = 0; i < opens.length; i++) { opens[i].addEventListener('click', open); }
    var xs = modal.querySelectorAll('[data-ha-close]');
    for (i = 0; i < xs.length; i++) { xs[i].addEventListener('click', close); }
    modal.addEventListener('click', function (ev) { if (ev.target === modal) { close(); } });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { close(); } });
    var d = document.getElementById('ha-modal-demo');
    if (d) {
      d.addEventListener('click', function () {
        demo(modal.getAttribute('data-demo-name') || '山小屋', null, modal.getAttribute('data-demo-time') || '', '', document.getElementById('ha-modal-demo-s'));
      });
    }
  }
  promo();

  setup();
  paintFavs();
  var list0 = load();
  renderMy(list0);
  if (!list0.length && !(favs().length && document.getElementById('ym-hut-alerts'))) { return; }
  // 登録があるときだけ、最新の予約開始データを読んで確かめる（読めなければ、登録したときの型で確かめる）
  var done = false;
  function run(rules) { if (done) { return; } done = true; DATA = rules; check(rules); }
  try {
    fetch('/data/huts_rules.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { run(j ? j.huts : null); }, function () { run(null); });
  } catch (e) { run(null); }
})();
