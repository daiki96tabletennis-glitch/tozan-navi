/* 管理画面の GitHub トークン（2026-11-23。運営者の指示「入れる場所と導線をわかりやすく・切れたときに自分で更新できるように」）
   - 管理画面・山画像・グルメ写真の3画面のヘッダーの下に、状態の帯を出す（開くたびに GitHub に確かめる）
   - 切れたら、その場で開く画面で作り直して保存できる（ページを離れないので、選んだ写真は消えない）
   - トークンは今までと同じ localStorage の ym_gh_token（この端末の中だけ）。送り先は api.github.com だけ
   - GitHub の期限はブラウザから読めないので、保存のときに選んだ日数から目安の日付を ym_gh_token_exp に持つ */
(function () {
  'use strict';
  var KEY = 'ym_gh_token';
  var EXP = 'ym_gh_token_exp';
  var REPO_API = 'https://api.github.com/repos/daiki96tabletennis-glitch/tozan-navi';
  var NEW_URL = 'https://github.com/settings/tokens/new?description=Yamatch%20admin%20images&scopes=public_repo';
  var WARN_DAYS = 14;
  var bar = null;
  var modal = null;
  var afterSave = null;

  function read(k) { try { return localStorage.getItem(k) || ''; } catch (e) { return ''; } }
  function write(k, v) {
    try {
      if (v) localStorage.setItem(k, v); else localStorage.removeItem(k);
      return true;
    } catch (e) { return false; }
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text) n.textContent = text;
    return n;
  }

  // 'ok' / 'expired' / 'noscope' / 'offline'
  function check(token) {
    return fetch(REPO_API, {
      cache: 'no-store',
      headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' }
    }).then(function (res) {
      if (res.status === 401) return 'expired';
      if (!res.ok) return 'noscope';
      var scopes = res.headers.get('X-OAuth-Scopes');
      return res.json().then(function (d) {
        var canPush = !!(d.permissions && d.permissions.push);
        // 従来のトークンは権限の名前も見る（細かい権限のトークンには、この値が無い）
        if (scopes && !/(^|[\s,])(public_repo|repo)($|[\s,])/.test(scopes)) canPush = false;
        return canPush ? 'ok' : 'noscope';
      });
    }).catch(function () { return 'offline'; });
  }

  function daysLeft(iso) {
    if (!iso) return null;
    var t = new Date(iso + 'T23:59:59').getTime();
    if (isNaN(t)) return null;
    return Math.ceil((t - Date.now()) / 86400000);
  }
  function shortDate(iso) {
    var p = iso.split('-');
    return p[0] + '年' + Number(p[1]) + '月' + Number(p[2]) + '日';
  }

  function paint(state) {
    if (!bar) return;
    var exp = read(EXP);
    var left = daysLeft(exp);
    var kind = 'err';
    var msg = '';
    var btn = '更新する';
    if (state === 'checking') { kind = 'wait'; msg = 'GitHub トークンを確認しています…'; btn = ''; }
    else if (state === 'none') { msg = 'GitHub トークンがこの端末に保存されていません。写真の反映に必要です'; btn = '設定する'; }
    else if (state === 'expired') msg = 'GitHub トークンの期限が切れています。写真を反映するには更新してください';
    else if (state === 'noscope') msg = 'この GitHub トークンにはサイトへ書き込む権限がありません。作り直してください';
    else if (state === 'offline') { kind = 'wait'; msg = 'GitHub につながらず、トークンを確認できません'; }
    else if (left !== null && left >= 0 && left <= WARN_DAYS) {
      kind = 'warn';
      msg = 'GitHub トークンはあと' + left + '日ほどで切れます（' + shortDate(exp) + 'ごろ）';
    } else {
      kind = 'ok';
      msg = 'GitHub トークン：使えます' + (left !== null && left > 0 ? '（' + shortDate(exp) + 'ごろまで）' : '');
    }
    bar.className = 'ymt-bar ymt-' + kind;
    bar.textContent = '';
    bar.appendChild(el('span', 'ymt-msg', msg));
    if (btn) {
      var b = el('button', 'ymt-open', btn);
      b.type = 'button';
      b.addEventListener('click', function () { open(); });
      bar.appendChild(b);
    }
  }

  function refresh() {
    var t = read(KEY);
    if (!t) { paint('none'); return Promise.resolve('none'); }
    paint('checking');
    return check(t).then(function (s) { paint(s); return s; });
  }

  function buildModal() {
    var wrap = el('div', 'ymt-overlay');
    wrap.hidden = true;
    var box = el('div', 'ymt-box');
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', 'GitHub トークンを更新');
    box.innerHTML =
      '<button type="button" class="ymt-x" aria-label="閉じる">×</button>' +
      '<h2>GitHub トークンを更新</h2>' +
      '<p class="ymt-reason"></p>' +
      '<ol class="ymt-steps">' +
      '<li><b>GitHub で新しいトークンを作る</b>' +
      '<a class="ymt-new" target="_blank" rel="noopener" href="' + NEW_URL + '">GitHub の作成画面を開く</a>' +
      '<small>名前と権限は入力済みです。Expiration を <b>90 days</b> にして、一番下の緑の <b>Generate token</b> を押します。</small></li>' +
      '<li><b>表示された ghp_ で始まる文字をコピー</b><small>この文字は一度しか表示されません。人やチャットには送らないでください。</small></li>' +
      '<li><b>この画面に戻って貼り付ける</b>' +
      '<div class="ymt-row"><input class="ymt-input" type="password" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="ghp_…" aria-label="GitHub トークン">' +
      '<button type="button" class="ymt-paste">貼り付け</button></div>' +
      '<label class="ymt-days">GitHub で選んだ期限 <select>' +
      '<option value="30">30日</option><option value="60">60日</option><option value="90" selected>90日</option>' +
      '<option value="365">1年</option><option value="0">わからない・期限なし</option></select></label></li>' +
      '</ol>' +
      '<button type="button" class="ymt-save">確かめて保存</button>' +
      '<p class="ymt-result" role="status"></p>' +
      '<p class="ymt-note">保存先はこの端末のブラウザの中だけです。スマホやホーム画面のアプリでは、それぞれ一度保存します。選んだ写真は消えません。</p>';
    wrap.appendChild(box);
    document.body.appendChild(wrap);

    function q(s) { return box.querySelector(s); }
    q('.ymt-x').addEventListener('click', close);
    wrap.addEventListener('click', function (e) { if (e.target === wrap) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !wrap.hidden) close(); });
    if (!(navigator.clipboard && navigator.clipboard.readText)) q('.ymt-paste').hidden = true;
    q('.ymt-paste').addEventListener('click', function () {
      navigator.clipboard.readText().then(function (v) {
        q('.ymt-input').value = (v || '').trim();
        result('', '');
      }).catch(function () {
        result('貼り付けできませんでした。入力欄を長押し（右クリック）して貼り付けてください', 'err');
        q('.ymt-input').focus();
      });
    });
    q('.ymt-save').addEventListener('click', save);
    q('.ymt-input').addEventListener('keydown', function (e) { if (e.key === 'Enter') save(); });

    function result(text, cls) {
      var r = q('.ymt-result');
      r.textContent = text;
      r.className = 'ymt-result' + (cls ? ' ymt-r-' + cls : '');
    }
    modal = { wrap: wrap, q: q, result: result };
  }

  function save() {
    var q = modal.q;
    var token = q('.ymt-input').value.trim();
    if (!/^(ghp_|github_pat_)[A-Za-z0-9_]+$/.test(token)) {
      modal.result('ghp_ で始まる文字をそのまま貼り付けてください', 'err');
      return;
    }
    var btn = q('.ymt-save');
    btn.disabled = true;
    modal.result('GitHub に確かめています…', '');
    check(token).then(function (s) {
      btn.disabled = false;
      if (s === 'expired') { modal.result('このトークンは使えません（期限切れ・取り消し、またはコピーの間違い）。もう一度作り直してください', 'err'); return; }
      if (s === 'noscope') { modal.result('このトークンには書き込む権限がありません。上のボタンから作り直してください', 'err'); return; }
      if (s === 'offline') { modal.result('GitHub につながりません。通信を確かめてもう一度押してください（まだ保存していません）', 'err'); return; }
      var days = Number(q('.ymt-days select').value);
      var exp = '';
      if (days) {
        var d = new Date(Date.now() + days * 86400000);
        exp = d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
      }
      if (!write(KEY, token)) { modal.result('この端末に保存できませんでした（プライベートブラウズなど）', 'err'); return; }
      write(EXP, exp);
      q('.ymt-input').value = '';
      paint('ok');
      var next = afterSave;
      close();
      if (next) next();
    });
  }

  function open(opts) {
    opts = opts || {};
    if (!modal) buildModal();
    afterSave = opts.onSaved || null;
    modal.q('.ymt-reason').textContent = opts.reason || '切れたときは、次の3つで更新できます。';
    modal.result('', '');
    modal.wrap.hidden = false;
    modal.q('.ymt-new').focus();
  }
  function close() {
    if (modal) modal.wrap.hidden = true;
    afterSave = null;
  }

  function style() {
    var s = document.createElement('style');
    s.textContent =
      '.ymt-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 16px;font-size:13px;line-height:1.5;border-bottom:1px solid rgba(0,0,0,.08)}' +
      '.ymt-msg{min-width:0}.ymt-ok{background:#e3f2e5;color:#2f6b3b}.ymt-warn{background:#fff2cc;color:#6f5012}.ymt-err{background:#fde7e5;color:#8f2f25;font-weight:700}.ymt-wait{background:#eeeae2;color:#6d675e}' +
      '.ymt-open{flex:none;min-height:34px;padding:5px 13px;border:1px solid currentColor;border-radius:7px;background:#fff;color:inherit;font-size:13px;font-weight:700;cursor:pointer}' +
      '.ymt-overlay{position:fixed;inset:0;z-index:10000;display:flex;align-items:flex-start;justify-content:center;padding:16px;overflow:auto;background:rgba(30,28,24,.55)}.ymt-overlay[hidden]{display:none}' +
      '.ymt-box{position:relative;width:min(520px,100%);margin:auto;padding:20px;border-radius:12px;background:#fff;color:#302d28;font-size:14px;line-height:1.6}' +
      '.ymt-box h2{margin:0 32px 6px 0;font-size:18px;color:#304326}.ymt-reason{margin:0 0 12px;color:#6d675e}' +
      '.ymt-x{position:absolute;top:8px;right:8px;width:36px;height:36px;border:0;background:none;color:#6d675e;font-size:22px;cursor:pointer}' +
      '.ymt-steps{margin:0 0 14px;padding-left:22px}.ymt-steps li{margin-bottom:13px}.ymt-steps small{display:block;margin-top:4px;color:#6d675e;font-size:12.5px}' +
      '.ymt-new{display:block;margin-top:6px;padding:9px 12px;border-radius:8px;background:#425b32;color:#fff!important;font-weight:700;text-align:center;text-decoration:none}' +
      '.ymt-row{display:flex;gap:6px;margin-top:6px}.ymt-input{flex:1;min-width:0;padding:9px 10px;border:1px solid #b9b2a6;border-radius:8px;font-family:monospace;font-size:16px}' +
      '.ymt-paste{flex:none;padding:0 12px;border:1px solid #425b32;border-radius:8px;background:#fff;color:#425b32;font-size:13px;font-weight:700;cursor:pointer}' +
      '.ymt-days{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:8px;font-size:13px}.ymt-days select{padding:6px;font-size:14px}' +
      '.ymt-save{width:100%;min-height:44px;border:0;border-radius:8px;background:#425b32;color:#fff;font-size:15px;font-weight:700;cursor:pointer}.ymt-save:disabled{opacity:.6}' +
      '.ymt-result{min-height:1em;margin:8px 0 0;font-size:13px}.ymt-r-err{color:#9b382d;font-weight:700}.ymt-note{margin:6px 0 0;color:#6d675e;font-size:12px}';
    document.head.appendChild(s);
  }

  function init() {
    style();
    var header = document.querySelector('header');
    if (!header) return;
    bar = el('div', 'ymt-bar ymt-wait');
    bar.id = 'ym-token-bar';
    header.insertAdjacentElement('afterend', bar);
    refresh();
  }

  window.YmGhToken = { open: open, refresh: refresh, paint: paint };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
