/* 運営者向けのお知らせ（マイページ・管理画面）。
   - マイページ：/mypage/?admin=<合言葉> を一度開いた端末、または管理画面の「お知らせ」で表示をオンにした端末だけに出す
     （localStorage ym_admin）。合言葉は下のハッシュと照合する
   - 管理画面（/admin/ の「お知らせ」。data-always="1"）：いつも出す。機能の説明と、マイページに出すかどうかの設定もここに出す
   - 中身は /data/admin_notices.json（scripts/admin_notice.py が GitHub Actions の定期実行から作る）
   - 「確認済みにする」は端末の中だけの記録（localStorage ym_admin_seen）。同じお知らせは畳んで出す
   - 表示を隠すだけで、データのファイル自体は公開されている。保守の情報以外を入れない */
(function () {
  'use strict';
  var KEY_HASH = '192fcc9a44c0deceea178e0f09d9ce1c440763958a252c3fa311cf30d1f0010a';
  var box = document.getElementById('ym-admin-notices');
  if (!box) return;
  var ALWAYS = box.getAttribute('data-always') === '1';   // 管理画面

  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function del(k) { try { localStorage.removeItem(k); } catch (e) {} }
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function seen() {
    try { return JSON.parse(get('ym_admin_seen') || '[]'); } catch (e) { return []; }
  }

  function hex(buf) {
    var b = new Uint8Array(buf), s = '', i;
    for (i = 0; i < b.length; i++) s += ('0' + b[i].toString(16)).slice(-2);
    return s;
  }

  // 合言葉つきのURLで開いたとき：照合して、合えばこの端末を運営者の端末として覚える。URLからは合言葉を消す
  function checkKey(done) {
    var m = /[?&]admin=([^&#]+)/.exec(location.search);
    if (!m) { done(); return; }
    var key = decodeURIComponent(m[1]);
    try { history.replaceState(null, '', location.pathname); } catch (e) {}
    if (key === 'off') { del('ym_admin'); done(); return; }
    if (!(window.crypto && crypto.subtle && window.TextEncoder)) { done(); return; }
    crypto.subtle.digest('SHA-256', new TextEncoder().encode(key)).then(function (h) {
      if (hex(h) === KEY_HASH) set('ym_admin', '1');
      done();
    }, function () { done(); });
  }

  function card(it, isSeen) {
    var dot = it.needsAction ? '#c9a227' : '#5f8a3a';
    var state = it.needsAction ? '対応が必要' : '異常なし';
    var n = 0, i, j, body = '';
    for (i = 0; i < it.sections.length; i++) n += it.sections[i].lines.length;
    for (i = 0; i < it.sections.length; i++) {
      var s = it.sections[i];
      body += '<div style="font-weight:700;font-size:12px;color:#2a3820;margin:10px 0 3px">' + esc(s.heading || '概要') + '</div><ul style="margin:0;padding-left:18px">';
      for (j = 0; j < s.lines.length; j++) {
        body += '<li style="margin:2px 0;word-break:break-all">' + esc(s.lines[j]) + '</li>';
      }
      body += '</ul>';
    }
    if (it.next) body += '<div style="margin-top:10px;padding:8px 10px;background:#f0ede5;border-radius:8px;font-size:12px"><b>次にやること</b>：' + esc(it.next) + '</div>';
    if (it.url) body += '<div style="margin-top:8px"><a href="' + esc(it.url) + '" target="_blank" rel="noopener" style="color:#4e6535;font-size:12px">実行結果の全文を見る（GitHub）</a></div>';
    if (it.needsAction && !isSeen) body += '<button type="button" data-seen="' + esc(it.id) + '" style="margin-top:10px;border:1px solid #4e6535;background:#fff;color:#4e6535;border-radius:999px;padding:6px 14px;font-size:12px;font-family:inherit">確認済みにする</button>';
    var open = it.needsAction && !isSeen;
    return '<details' + (open ? ' open' : '') + ' style="border-top:1px solid #eeece6;padding:10px 0">'
      + '<summary style="list-style:none;display:flex;align-items:center;gap:8px;cursor:pointer">'
      + '<span style="width:9px;height:9px;border-radius:50%;flex-shrink:0;background:' + (isSeen ? '#b9b2a6' : dot) + '"></span>'
      + '<span style="flex:1;min-width:0"><b style="color:#2a3820;font-size:13.5px">' + esc(it.title) + '</b>'
      + '<span style="display:block;font-size:11px;color:#93897c">' + esc(it.date) + '・' + state + (n ? '（' + n + '項目）' : '') + (isSeen ? '・確認済み' : '') + '</span></span>'
      + '<span style="font-size:11px;color:#93897c">開く</span></summary>'
      + (body ? '<div style="font-size:12.5px;line-height:1.6;color:#2f2b26">' + body + '</div>' : '')
      + '</details>';
  }

  function settings() {
    var on = get('ym_admin') === '1', sn = seen();
    return '<div style="border-top:1px solid #eeece6;padding:12px 0 6px;font-size:12.5px;line-height:1.65;color:#2f2b26">'
      + '<b style="font-size:13px;color:#2a3820">マイページでの設定</b>'
      + '<label style="display:flex;align-items:center;gap:10px;margin:8px 0 4px;cursor:pointer">'
      + '<input type="checkbox" id="ym-admin-toggle"' + (on ? ' checked' : '') + ' style="width:20px;height:20px;accent-color:#4e6535">'
      + '<span>この端末のマイページにも、このお知らせを出す<span style="display:block;font-size:11px;color:#93897c">いまは' + (on ? '出す設定です' : '出さない設定です') + '（端末ごとの設定。ほかの端末・ほかの人には出ません）</span></span></label>'
      + '<div style="font-size:11.5px;color:#6a6258;margin:2px 0 8px">ホーム画面に追加したアプリは、ブラウザと設定が別です。アプリのマイページに出すには、アプリの中でこの管理画面（/admin/）を開いてオンにしてください。</div>'
      + '<button type="button" id="ym-admin-unseen" style="border:1px solid #cfc8ba;background:#fff;color:#6a6258;border-radius:999px;padding:5px 12px;font-size:11.5px;font-family:inherit"' + (sn.length ? '' : ' disabled') + '>「確認済み」を取り消す（' + sn.length + '件）</button>'
      + '</div>'
      + '<details style="border-top:1px solid #eeece6;padding:10px 0;font-size:12.5px;line-height:1.65;color:#2f2b26">'
      + '<summary style="cursor:pointer;font-weight:700;color:#2a3820;font-size:13px">このお知らせについて</summary>'
      + '<ul style="margin:8px 0 0;padding-left:18px">'
      + '<li><b>毎月の年次データ確認</b>：毎月1日。運行期間・規制期間の期限切れ、30日以内に期限、出典ページの変更、リンク切れ、噴火警報の出ている山</li>'
      + '<li><b>山小屋の定期更新</b>：変化や候補があったとき。記載が変わった小屋、予約開始日の候補、読み取れなくなった小屋</li>'
      + '<li><b>サイトの検証</b>：プッシュのたびと毎週月曜。結果が変わったときに、異常のある項目</li>'
      + '<li>種類ごとに最新の1件が出ます。黄色の印＝対応が必要、緑＝異常なし、灰色＝確認済み</li>'
      + '<li>「確認済みにする」は、この端末の中だけの記録です。データを直して次の実行で内容が変わると、新しいお知らせとして出ます</li>'
      + '<li>GitHub の定期実行が自動で作ります（AIは使いません）。山のデータやページは書き換えません</li>'
      + '<li>お知らせのデータ（/data/admin_notices.json）は公開されています。入るのは保守の情報だけです</li>'
      + '</ul></details>';
  }

  function render(data) {
    var items = (data && data.items) || [], sn = seen(), todo = 0, i, h;
    for (i = 0; i < items.length; i++) if (items[i].needsAction && sn.indexOf(items[i].id) < 0) todo++;
    h = '<div style="background:#fff;border-radius:16px;padding:14px 16px 6px;margin:14px 0 4px;box-shadow:0 1px 1px rgba(26,22,14,.03),0 2px 5px rgba(26,22,14,.05);border-left:4px solid #4e6535">'
      + '<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:8px"><b style="font-size:14px;color:#2a3820">運営者向けのお知らせ</b>'
      + '<span style="font-size:11.5px;border-radius:999px;padding:1px 9px;background:' + (todo ? '#f6ecc4' : '#e9efe0') + ';color:#2a3820">' + (todo ? '未確認 ' + todo + '件' : '未確認なし') + '</span></div>';
    if (!items.length) {
      h += '<div style="font-size:12.5px;color:#6a6258;padding:4px 0 10px">まだお知らせはありません（GitHub の定期実行が動くと、ここに出ます）。</div>';
    }
    for (i = 0; i < items.length; i++) h += card(items[i], sn.indexOf(items[i].id) >= 0);
    if (ALWAYS) {
      h += settings() + '</div>';
    } else {
      h += '<div style="font-size:10.5px;color:#93897c;padding:8px 0 8px;border-top:1px solid #eeece6">この欄は、この端末にだけ出ています。'
        + '<a href="/admin/#notices" style="color:#93897c;margin-left:6px">説明と設定（管理画面）</a></div></div>';
    }
    box.innerHTML = h;
  }

  function load() {
    if (!ALWAYS && get('ym_admin') !== '1') { box.innerHTML = ''; return; }
    var x = new XMLHttpRequest();
    x.open('GET', '/data/admin_notices.json?t=' + Math.floor(Date.now() / 600000));
    x.onload = function () {
      var d = null;
      if (x.status === 200) { try { d = JSON.parse(x.responseText); } catch (e) {} }
      render(d);
    };
    x.onerror = function () { render(null); };
    x.send();
  }

  box.addEventListener('click', function (e) {
    var t = e.target;
    if (t && t.id === 'ym-admin-unseen') { del('ym_admin_seen'); load(); return; }
    if (!t || !t.getAttribute || !t.getAttribute('data-seen')) return;
    var sn = seen(), id = t.getAttribute('data-seen');
    if (sn.indexOf(id) < 0) sn.push(id);
    set('ym_admin_seen', JSON.stringify(sn.slice(-30)));
    load();
  });

  box.addEventListener('change', function (e) {
    var t = e.target;
    if (!t || t.id !== 'ym-admin-toggle') return;
    if (t.checked) set('ym_admin', '1'); else del('ym_admin');
    load();
  });

  // ホーム画面に追加したアプリにはアドレス欄が無いので、マイページの見出し「マイページ」を続けて5回押すと合言葉を聞く。
  // 合っていればこの端末で表示をオンにする。すでにオンなら管理画面の「お知らせ」を開く
  function secretEntry() {
    if (ALWAYS) return;
    var head = document.querySelector('header.ym-header'), taps = [];
    if (!head) return;
    head.addEventListener('click', function (e) {
      if (e.target && e.target.closest && e.target.closest('a,button')) return;
      var now = Date.now();
      taps.push(now);
      while (taps.length && now - taps[0] > 3000) taps.shift();
      if (taps.length < 5) return;
      taps = [];
      if (get('ym_admin') === '1') { location.href = '/admin/#notices'; return; }
      var key = window.prompt('合言葉');
      if (!key || !(window.crypto && crypto.subtle && window.TextEncoder)) return;
      crypto.subtle.digest('SHA-256', new TextEncoder().encode(key.replace(/\s/g, ''))).then(function (h) {
        if (hex(h) === KEY_HASH) { set('ym_admin', '1'); load(); box.scrollIntoView({ block: 'start' }); }
      });
    });
  }
  secretEntry();

  window.ymAdminNoticesReload = load;
  checkKey(load);
})();
