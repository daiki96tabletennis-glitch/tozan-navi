/* 管理画面｜グルメ記事（/articles/mountain-gourmet/）の写真を Wikimedia Commons から選んで GitHub に書く。
   書くもの：images/articles/mountain-gourmet/<key>-<Commonsのページ番号>.jpg と data/mountain_gourmet.json の image。
   記事は .github/workflows/gourmet-article.yml が作り直す。作業フォルダへは scripts/import_repo_images.py が取り込む（コミットの題に [gourmet] を付ける）。 */
(function () {
  'use strict';

  var OWNER = 'daiki96tabletennis-glitch';
  var REPO = 'tozan-navi';
  var DATA_PATH = 'data/mountain_gourmet.json';
  var IMG_DIR = 'images/articles/mountain-gourmet/';
  var COMMONS_API = 'https://commons.wikimedia.org/w/api.php';
  var MAX_W = 1200;

  var state = { data: null, mountains: {}, cands: {}, lastApi: 0 };

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function clean(html) {
    var d = document.createElement('div');
    d.innerHTML = String(html || '');
    return (d.textContent || '').replace(/\s+/g, ' ').trim();
  }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function itemByKey(d, key) {
    for (var i = 0; i < d.items.length; i++) if (d.items[i].key === key) return d.items[i];
    return null;
  }

  /* ---------- Commons ---------- */
  async function commons(params) {
    var gap = Date.now() - state.lastApi;
    if (gap < 250) await wait(250 - gap);
    state.lastApi = Date.now();
    var q = new URLSearchParams(Object.assign({}, params, { format: 'json', origin: '*' }));
    var res = await fetch(COMMONS_API + '?' + q.toString());
    if (!res.ok) throw new Error('Commons の検索に失敗しました（' + res.status + '）');
    return res.json();
  }

  // 商用で使えるか（CC0・パブリックドメイン・CC BY・CC BY-SA。NC・ND・作者不明・情報不足は使わない）
  function licenseCheck(c) {
    var lic = String(c.license || '').toUpperCase();
    if (!lic) return { ok: false, label: 'ライセンス不明' };
    if (/(^|[-\s])NC($|[-\s\d])|NON.?COMMERCIAL/.test(lic)) return { ok: false, label: '非営利限定（NC）' };
    if (/(^|[-\s])ND($|[-\s\d])|NO.?DERIV/.test(lic)) return { ok: false, label: '改変禁止（ND）' };
    var pd = /PUBLIC DOMAIN|^PD\b|\bPDM\b/.test(lic);
    var cc0 = /\bCC\s*0\b/.test(lic);
    var by = /\bCC\s+BY(-SA)?\b/.test(lic);
    if (!pd && !cc0 && !by) return { ok: false, label: '対象外のライセンス' };
    if (c.restrictions) return { ok: false, label: '利用の制限あり' };
    if (!c.author || /UNKNOWN|作者不明/i.test(c.author)) return { ok: false, label: '作者不明' };
    if (by && !c.licenseUrl) return { ok: false, label: 'ライセンスURLなし' };
    if (!c.pageUrl) return { ok: false, label: '元ページなし' };
    return { ok: true, label: '使える（' + c.license + '）' };
  }

  function queries(it, extra) {
    var qs = [{ q: it.place, kind: 'name' }];
    var parts = it.place.split('・');
    if (parts.length > 1) parts.forEach(function (p) { qs.push({ q: p.trim(), kind: 'name' }); });
    var m = state.mountains[it.mountainId];
    if (m && m.name) qs.push({ q: m.name + (it.group === 'teahouse' ? ' 茶屋' : ' 山小屋'), kind: 'mountain' });
    (it.commonsQueries || []).forEach(function (w) { qs.push({ q: w, kind: 'extra' }); });
    if (extra) qs.push({ q: extra, kind: 'extra' });
    return qs;
  }

  async function findCands(it, extra) {
    var seen = {}, out = [];
    var qs = queries(it, extra);
    for (var i = 0; i < qs.length; i++) {
      var data = await commons({ action: 'query', generator: 'search', gsrnamespace: 6, gsrsearch: qs[i].q, gsrlimit: 30,
        prop: 'imageinfo', iiprop: 'url|size|extmetadata|mime', iiurlwidth: MAX_W });
      var pages = (data.query && data.query.pages) ? Object.keys(data.query.pages).map(function (k) { return data.query.pages[k]; }) : [];
      pages.sort(function (a, b) { return (a.index || 0) - (b.index || 0); });
      pages.forEach(function (p) {
        if (seen[p.title]) return;
        seen[p.title] = 1;
        var ii = (p.imageinfo || [])[0] || {};
        if (['image/jpeg', 'image/png', 'image/webp'].indexOf(ii.mime) < 0) return;
        var md = ii.extmetadata || {};
        function v(k) { return clean((md[k] || {}).value); }
        var c = { title: p.title, pageid: p.pageid, kind: qs[i].kind, query: qs[i].q,
          license: v('LicenseShortName'), licenseUrl: v('LicenseUrl'), author: v('Artist'), restrictions: v('Restrictions'),
          description: v('ImageDescription').slice(0, 140), date: v('DateTimeOriginal').slice(0, 10),
          width: ii.width, height: ii.height, thumb: ii.thumburl || ii.url, pageUrl: ii.descriptionurl };
        c.check = licenseCheck(c);
        out.push(c);
      });
    }
    // 使える写真を先に、その中ではお店の名前で見つかったものを先に
    var rank = { name: 0, mountain: 1, extra: 2 };
    out.sort(function (a, b) {
      if (a.check.ok !== b.check.ok) return a.check.ok ? -1 : 1;
      return rank[a.kind] - rank[b.kind];
    });
    return out;
  }

  /* ---------- GitHub ---------- */
  function token() { try { return localStorage.getItem('ym_gh_token') || ''; } catch (e) { return ''; } }
  function ghHeaders(t) {
    return { Authorization: 'Bearer ' + t, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' };
  }
  function ghUrl(path) {
    return 'https://api.github.com/repos/' + OWNER + '/' + REPO + '/contents/' + path.split('/').map(encodeURIComponent).join('/');
  }
  async function ghGet(path, t, allowMissing) {
    var res = await fetch(ghUrl(path) + '?t=' + Date.now(), { headers: ghHeaders(t) });
    if (allowMissing && res.status === 404) return null;
    if (!res.ok) throw new Error(path + ' の取得に失敗しました（' + res.status + '）');
    return res.json();
  }
  async function ghPut(path, b64, message, t) {
    var cur = await ghGet(path, t, true);
    var body = { message: message, content: b64 };
    if (cur && cur.sha) body.sha = cur.sha;
    var res = await fetch(ghUrl(path), { method: 'PUT', headers: Object.assign({ 'Content-Type': 'application/json' }, ghHeaders(t)), body: JSON.stringify(body) });
    if (!res.ok) {
      var d = await res.json().catch(function () { return {}; });
      throw new Error(path + ' の保存に失敗しました（' + res.status + '）' + (d.message ? '：' + d.message : ''));
    }
    return res.json();
  }
  function bytesB64(bytes) {
    var bin = '';
    for (var i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(bin);
  }
  function textB64(s) { return bytesB64(new TextEncoder().encode(s)); }
  function b64Text(s) {
    var bin = atob(String(s || '').replace(/\n/g, ''));
    var a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return new TextDecoder().decode(a);
  }

  // Commons の縮小版を取り、幅1200px以内の JPEG にする
  async function toJpeg(url) {
    var res = await fetch(url, { referrerPolicy: 'no-referrer' });
    if (!res.ok) throw new Error('写真の取得に失敗しました（' + res.status + '）');
    var blob = await res.blob();
    var src = URL.createObjectURL(blob);
    try {
      var img = await new Promise(function (ok, ng) {
        var im = new Image();
        im.onload = function () { ok(im); };
        im.onerror = function () { ng(new Error('写真を読み込めませんでした')); };
        im.src = src;
      });
      var w = Math.min(MAX_W, img.naturalWidth);
      var h = Math.round(img.naturalHeight * w / img.naturalWidth);
      var cv = document.createElement('canvas');
      cv.width = w; cv.height = h;
      cv.getContext('2d').drawImage(img, 0, 0, w, h);
      var out = await new Promise(function (ok) { cv.toBlob(ok, 'image/jpeg', 0.86); });
      return new Uint8Array(await out.arrayBuffer());
    } finally {
      URL.revokeObjectURL(src);
    }
  }

  async function saveImage(key, image, message, fileBytes, fileName) {
    var t = token();
    if (!t) throw new Error('GitHub のトークンがありません。管理画面のトップで保存してください');
    if (fileBytes) await ghPut(IMG_DIR + fileName, bytesB64(fileBytes), message, t);
    // 書く直前に GitHub の最新を読み、その項目の image だけを替える
    var f = await ghGet(DATA_PATH, t, false);
    var d = JSON.parse(b64Text(f.content));
    var it = itemByKey(d, key);
    if (!it) throw new Error('GitHub のデータに ' + key + ' がありません');
    it.image = image;
    await ghPut(DATA_PATH, textB64(JSON.stringify(d, null, 1)), message, t);
    var local = itemByKey(state.data, key);
    if (local) local.image = image;
  }

  /* ---------- 画面 ---------- */
  function nowHtml(it) {
    var img = it.image || {};
    if (!img.src) return '<div class="gm-now empty">写真なし</div>';
    return '<img class="gm-now" src="' + esc(img.src) + '" alt="' + esc(img.alt) + '">';
  }
  function creditHtml(it) {
    var img = it.image || {};
    if (!img.src) return '';
    return '<p class="small">写真：' + esc(img.credit || '') + (img.license ? '（' + esc(img.license) + '）' : '') +
      (img.pageUrl ? ' ／ <a href="' + esc(img.pageUrl) + '" target="_blank" rel="noopener">Commons</a>' : '') + '</p>';
  }

  function renderItem(it) {
    var el = document.createElement('div');
    el.className = 'gm-item';
    el.id = 'gm-' + it.key;
    var m = state.mountains[it.mountainId];
    el.innerHTML = '<div class="gm-head">' + nowHtml(it) +
      '<div class="gm-info"><h3>' + esc(it.place) + '</h3>' +
      '<p class="small">' + esc(m ? m.name : it.mountainId) + '｜' + esc(it.where) + '</p>' +
      '<p class="small">料理：' + esc(it.food) + '</p>' + creditHtml(it) +
      '<div class="gm-tools"><input type="search" placeholder="追加の検索語（英語名など。任意）" data-extra>' +
      '<button class="compact" type="button" data-find>候補を探す</button>' +
      (it.image && it.image.src ? '<button class="secondary compact" type="button" data-clear>写真を外す</button>' : '') +
      '</div><div class="gm-msg" data-msg></div></div></div><div class="gm-cands" data-cands></div>';
    el.querySelector('[data-find]').addEventListener('click', function () { onFind(it.key); });
    var clr = el.querySelector('[data-clear]');
    if (clr) clr.addEventListener('click', function () { onClear(it.key); });
    return el;
  }

  function rerender(key) {
    var it = itemByKey(state.data, key);
    var old = $('gm-' + key);
    old.parentNode.replaceChild(renderItem(it), old);
  }

  function msg(key, text, ok) {
    var el = $('gm-' + key).querySelector('[data-msg]');
    el.textContent = text;
    el.style.color = ok === false ? '#b33' : (ok ? '#36502a' : '');
  }

  async function onFind(key) {
    var it = itemByKey(state.data, key);
    var box = $('gm-' + key);
    var extra = box.querySelector('[data-extra]').value.trim();
    msg(key, 'Commons を検索しています…');
    try {
      var cands = await findCands(it, extra);
      state.cands[key] = cands;
      var okN = cands.filter(function (c) { return c.check.ok; }).length;
      msg(key, '候補 ' + cands.length + ' 件（使える写真 ' + okN + ' 件）', true);
      var wrap = box.querySelector('[data-cands]');
      wrap.innerHTML = '';
      cands.forEach(function (c, i) { wrap.appendChild(renderCand(it, c, i)); });
      if (!cands.length) wrap.innerHTML = '<p class="small">候補がありません。英語の名前などを足して探してください。</p>';
    } catch (e) {
      msg(key, e.message, false);
    }
  }

  function renderCand(it, c, i) {
    var el = document.createElement('div');
    el.className = 'gm-cand' + (c.check.ok ? '' : ' ng');
    var warn = '';
    if (c.kind === 'mountain') warn = '<div class="gm-warn2">山名で見つかった写真（お店が写っているか確かめる）</div>';
    else if (c.kind === 'extra') warn = '<div class="gm-warn">追加の語で見つかった写真（料理名なら別のお店の可能性が高い）</div>';
    var defAlt = (it.image && it.image.alt) || it.place;
    el.innerHTML = '<img src="' + esc(c.thumb) + '" alt="" loading="lazy" referrerpolicy="no-referrer">' +
      '<div><b>' + esc(c.title.replace(/^File:/, '')) + '</b></div>' + warn +
      '<div class="' + (c.check.ok ? 'gm-ok' : 'gm-warn') + '">' + esc(c.check.label) + '</div>' +
      '<div>' + esc(c.author) + (c.date ? ' ／ ' + esc(c.date) : '') + ' ／ ' + esc(c.width) + '×' + esc(c.height) + '</div>' +
      (c.description ? '<div class="small">' + esc(c.description) + '</div>' : '') +
      '<div><a href="' + esc(c.pageUrl) + '" target="_blank" rel="noopener">Commons のページを開く</a></div>' +
      (c.check.ok ? '<button class="compact" type="button" data-pick style="margin-top:6px">この写真にする</button>' +
        '<div class="gm-apply" data-apply><label class="small">写真の説明（画像の代替テキスト。料理でなく建物なら書き換える）' +
        '<input type="text" value="' + esc(defAlt) + '" data-alt></label>' +
        '<button class="compact" type="button" data-go>GitHubへ反映</button></div>' : '');
    var pick = el.querySelector('[data-pick]');
    if (pick) {
      pick.addEventListener('click', function () {
        el.querySelector('[data-apply]').classList.add('open');
        pick.style.display = 'none';
      });
      el.querySelector('[data-go]').addEventListener('click', function () {
        onApply(it.key, i, el.querySelector('[data-alt]').value.trim(), this);
      });
    }
    return el;
  }

  async function onApply(key, i, alt, btn) {
    var c = state.cands[key][i];
    if (c.kind !== 'name' && !confirm('お店の名前以外で見つかった写真です。そのお店の写真だと確かめましたか？')) return;
    btn.disabled = true;
    msg(key, '写真を GitHub に書いています…');
    try {
      var bytes = await toJpeg(c.thumb);
      var fileName = key + '-' + c.pageid + '.jpg';
      var it = itemByKey(state.data, key);
      var image = { src: '/' + IMG_DIR + fileName, alt: alt || (it.image && it.image.alt) || it.place,
        credit: c.author, license: c.license, licenseUrl: c.licenseUrl || null, pageUrl: c.pageUrl,
        source: 'wikimedia_commons', commonsTitle: c.title, selectedAt: new Date().toISOString().slice(0, 10) };
      await saveImage(key, image, '[gourmet] ' + key + 'の写真を設定（' + c.title + '）', bytes, fileName);
      rerender(key);
      msg(key, '反映しました。数分で記事が作り直されます（GitHub Actions）。', true);
    } catch (e) {
      btn.disabled = false;
      msg(key, e.message, false);
    }
  }

  async function onClear(key) {
    var it = itemByKey(state.data, key);
    if (!confirm(it.place + ' の写真を記事から外しますか？（写真のファイルは残ります）')) return;
    msg(key, 'GitHub に書いています…');
    try {
      await saveImage(key, { src: null, alt: (it.image && it.image.alt) || it.place, credit: null },
        '[gourmet] ' + key + 'の写真を外す', null, null);
      rerender(key);
      msg(key, '外しました。数分で記事が作り直されます。', true);
    } catch (e) {
      msg(key, e.message, false);
    }
  }

  async function init() {
    try {
      var t = token();
      var d;
      if (t) {
        // GitHub の最新（ほかの端末で反映した分も含む）
        var f = await ghGet(DATA_PATH, t, false);
        d = JSON.parse(b64Text(f.content));
      } else {
        d = await (await fetch('/' + DATA_PATH + '?t=' + Date.now())).json();
      }
      var ms = await (await fetch('/data/mountains.json')).json();
      ms.forEach(function (m) { state.mountains[m.id] = m; });
      state.data = d;
      var groups = {};
      d.groups.forEach(function (g) { groups[g.key] = g.title; });
      var box = $('items');
      var cur = null;
      d.items.forEach(function (it) {
        if (it.group !== cur) {
          cur = it.group;
          var h = document.createElement('h2');
          h.textContent = groups[cur] || cur;
          box.appendChild(h);
        }
        box.appendChild(renderItem(it));
      });
      var withPhoto = d.items.filter(function (x) { return x.image && x.image.src; }).length;
      $('load-status').innerHTML = '<p class="small">' + d.items.length + '軒（写真あり ' + withPhoto + '）' +
        (t ? '' : '｜<b class="gm-warn">GitHub のトークンが未保存です。反映するには管理画面のトップで保存してください</b>') + '</p>';
    } catch (e) {
      $('load-status').textContent = '読み込みに失敗しました：' + e.message;
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
