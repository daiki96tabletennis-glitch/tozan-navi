/* 持ち物・服装のチェックリスト（data/packing.json）。
   山小屋の山ごとのページ（#ym-packing。data-mid / data-name / data-elev / data-gear）と、マイページの登山計画（YMPacking.build）から使う。
   気温の数字は出さない。装備の時期は gearCalendar で決める。商品は Amazon の検索リンク（gear-common.js の YMGear があればそれを使う）。
   チェックは端末の中（localStorage ym_packing）だけに保存する。 */
window.YMPacking = (function () {
  'use strict';
  var DATA = null, GEAR = null, loading = null;
  var KEY = 'ym_packing';
  var STAY_LABEL = { day: '日帰り', hut: '山小屋泊', tent: 'テント泊' };
  var TAG = 'amazonafdaiki-22';

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function load() {
    if (loading) return loading;
    loading = Promise.all([
      fetch('/data/packing.json').then(function (r) { return r.json(); }),
      fetch('/data/gear-data.json').then(function (r) { return r.json(); }).catch(function () { return {}; })
    ]).then(function (a) { DATA = a[0]; GEAR = a[1]; return DATA; });
    return loading;
  }
  // 商品のリンクは Amazon（運営者の指示・2026-10-20）。gear-common.js の YMGear があればそれを使う（商品ごとの ASIN 指定も効く）
  function buyUrl(name) {
    if (window.YMGear && window.YMGear.getAffiliate) return window.YMGear.getAffiliate(name).amazonUrl;
    return 'https://www.amazon.co.jp/s?k=' + encodeURIComponent(name) + '&tag=' + TAG;
  }
  // その月の装備の区分（月の途中で変わる月は両方）
  function gearKinds(cal, month) {
    var v = cal && cal[month - 1];
    if (!v) return [];
    if (typeof v === 'object') return [v.before, v.after];
    return [v];
  }
  function gearProduct(mid, month, cat) {
    var arr = GEAR && GEAR[mid] && GEAR[mid][String(month)];
    if (!arr) return null;
    for (var i = 0; i < arr.length; i++) if (arr[i].c === cat) return arr[i].p;
    return null;
  }

  /* opts: { mid, elev, gear(12か月), month(1〜12 または null), day(日。分かるときだけ), stay('day'|'hut'|'tent') }
     返り値：[{ key, title, lead, items:[{ id, label, note, product, src }] }] */
  function build(opts) {
    var kinds = opts.month ? gearKinds(opts.gear, opts.month) : [];
    var cell = opts.month && opts.gear ? opts.gear[opts.month - 1] : null;
    var split = cell && typeof cell === 'object' && cell.changeDate ? cell : null;
    // 日付が分かるとき（登山計画）は、その日の区分だけにする
    if (split && opts.day) {
      kinds = [opts.day >= split.changeDate ? split.after : split.before];
      split = null;
    }
    var out = [];
    DATA.groups.forEach(function (g) {
      if (g.stay && g.stay.indexOf(opts.stay) < 0) return;
      if (g.gear && !g.gear.some(function (k) { return kinds.indexOf(k) >= 0; })) return;
      var items = [];
      g.items.forEach(function (it) {
        if (it.stay && it.stay.indexOf(opts.stay) < 0) return;
        if (it.minElev && (opts.elev || 0) < it.minElev) return;
        var prod = (it.gearCat && opts.mid && opts.month && gearProduct(opts.mid, opts.month, it.gearCat)) || it.product || null;
        if (prod) prod = prod.replace(/\(来月分\)$/, '');
        var prods = it.products ? it.products.slice() : (prod ? [prod] : []);
        var note = it.note || '';
        if (it.noteHigh && (opts.elev || 0) >= 2500) note = note ? note + '。' + it.noteHigh : it.noteHigh;
        items.push({ id: g.key + '.' + it.id, label: it.label, note: note, product: prods[0] || null, products: prods, src: it.src ? [].concat(it.src) : [], unless: it.unless || null });
      });
      var title = g.title;
      // 月の途中で装備が変わる月は、どちらの時期の分かを添える
      if (split && g.gear) {
        if (g.gear.indexOf(split.before) >= 0) title += '（' + opts.month + '月' + (split.changeDate - 1) + '日ごろまで）';
        else if (g.gear.indexOf(split.after) >= 0) title += '（' + opts.month + '月' + split.changeDate + '日ごろから）';
      }
      if (items.length) out.push({ key: g.key, title: title, lead: g.lead || '', items: items });
    });
    // 同じものが二重に出ないように（unless の項目が入っていれば外す）
    var have = {};
    out.forEach(function (g) { g.items.forEach(function (it) { have[it.id] = 1; }); });
    out.forEach(function (g) { g.items = g.items.filter(function (it) { return !(it.unless && have[it.unless]); }); });
    return out.filter(function (g) { return g.items.length; });
  }

  function readChecks() { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } }
  function writeChecks(o) { try { localStorage.setItem(KEY, JSON.stringify(o)); } catch (e) {} }

  function shareText(name, month, stay, groups) {
    var lines = [name + 'の持ち物（' + (month ? month + '月・' : '') + STAY_LABEL[stay] + '）'];
    groups.forEach(function (g) {
      lines.push('');
      lines.push('■ ' + g.title);
      g.items.forEach(function (it) { lines.push('□ ' + it.label); });
    });
    lines.push('');
    lines.push(location.origin + location.pathname + '#packing');
    return lines.join('\n');
  }

  function srcHtml(groups) {
    var used = {};
    groups.forEach(function (g) { g.items.forEach(function (it) { (it.src || []).forEach(function (k) { used[k] = 1; }); }); });
    var links = Object.keys(used).map(function (k) {
      var s = DATA.sources[k];
      if (!s) return '';
      return s.url ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.label) + '</a>' : esc(s.label);
    }).filter(Boolean);
    return '<p class="pk-src">出典：' + links.join('、') + 'をもとに、Yamatch がまとめました（' + esc(DATA.checkedAt) + '）。' +
      '装備の時期は、この山の装備カレンダーから選んでいます。商品のリンクは Amazon の検索結果です（広告。当サイトは Amazon アソシエイトを利用しています）。</p>';
  }

  // 泊まった人の服装の例（data/packing.json の experiences）
  function expHtml(mid, elev) {
    var out = '';
    var list = (DATA.experiences || []).filter(function (x) { return x.mid === mid; });
    // 標高の高い山（2,500m以上）では、ほかの山の例も参考に出す
    if (elev >= 2500) list = list.concat((DATA.experiences || []).filter(function (x) { return x.mid !== mid; }));
    list.forEach(function (x) {
      // 日付が分かるものは日付、分からないものは聞いたとおりの時期（when）
      var when = x.when || '';
      if (x.date) {
        var d = x.date.split('-');
        when = d[0] + '年' + parseInt(d[1], 10) + '月' + parseInt(d[2], 10) + '日';
      }
      var body = x.text ? x.text : '上は' + x.top.join('＋') + '、下は' + x.bottom.join('＋') + 'で、' + x.feel;
      out += '<div class="pk-exp"><b>泊まった人の服装の例' + (x.mid !== mid ? '（ほかの山）' : '') + '</b>' +
        '<span class="pk-exp-when">' + esc(when + '・' + x.place + '（' + x.who + '）') + '</span>' +
        '<p>' + esc(x.scene) + '：' + esc(body) + '。</p></div>';
    });
    return out;
  }

  function mount(el) {
    var mid = el.getAttribute('data-mid');
    var name = el.getAttribute('data-name') || '';
    var elev = parseInt(el.getAttribute('data-elev') || '0', 10);
    var gear = [];
    try { gear = JSON.parse(el.getAttribute('data-gear') || '[]'); } catch (e) {}
    var state = { month: new Date().getMonth() + 1, stay: 'hut' };

    function draw() {
      var groups = build({ mid: mid, elev: elev, gear: gear, month: state.month, stay: state.stay });
      var ck = readChecks();
      var pre = mid + ':' + state.stay + ':' + state.month + ':';
      var total = 0, done = 0;
      var h = '<div class="pk-ctl"><label>行く月 <select data-pk-month>';
      for (var m = 1; m <= 12; m++) h += '<option value="' + m + '"' + (m === state.month ? ' selected' : '') + '>' + m + '月</option>';
      h += '</select></label><div class="pk-stay">';
      ['hut', 'tent'].forEach(function (s) {
        h += '<button type="button" data-pk-stay="' + s + '"' + (s === state.stay ? ' class="on"' : '') + '>' + STAY_LABEL[s] + '</button>';
      });
      h += '</div></div>';
      var kinds = gearKinds(gear, state.month);
      if (kinds.indexOf('closed') >= 0) h += '<p class="pk-warn">' + state.month + '月は、登山道の閉鎖などで登れない期間があります。山ページの装備カレンダーを確かめてください。</p>';
      h += expHtml(mid, elev);
      groups.forEach(function (g) {
        h += '<div class="pk-g"><h3>' + esc(g.title) + '</h3>' + (g.lead ? '<p class="pk-lead">' + esc(g.lead) + '</p>' : '') + '<ul>';
        g.items.forEach(function (it) {
          total++;
          var on = !!ck[pre + it.id];
          if (on) done++;
          h += '<li' + (on ? ' class="on"' : '') + '><label><input type="checkbox" data-pk-id="' + esc(it.id) + '"' + (on ? ' checked' : '') + '><span>' + esc(it.label) +
            (it.note ? '<small>' + esc(it.note) + '</small>' : '') + '</span></label>' +
            it.products.map(function (p) { return '<a class="pk-buy" href="' + esc(buyUrl(p)) + '" target="_blank" rel="sponsored noopener">Amazonで見る：' + esc(p) + '</a>'; }).join('') + '</li>';
        });
        h += '</ul></div>';
      });
      h += '<div class="pk-foot"><span class="pk-n">' + done + ' / ' + total + ' 準備済み</span>' +
        '<button type="button" data-pk-share>リストを送る・コピー</button><button type="button" data-pk-reset class="pk-sub">チェックを外す</button></div>' +
        '<p class="pk-msg" data-pk-msg></p>' + srcHtml(groups);
      el.innerHTML = h;

      el.querySelector('[data-pk-month]').addEventListener('change', function () { state.month = parseInt(this.value, 10); draw(); });
      Array.prototype.forEach.call(el.querySelectorAll('[data-pk-stay]'), function (b) {
        b.addEventListener('click', function () { state.stay = b.getAttribute('data-pk-stay'); draw(); });
      });
      Array.prototype.forEach.call(el.querySelectorAll('[data-pk-id]'), function (c) {
        c.addEventListener('change', function () {
          var o = readChecks();
          if (c.checked) o[pre + c.getAttribute('data-pk-id')] = 1; else delete o[pre + c.getAttribute('data-pk-id')];
          writeChecks(o);
          draw();
        });
      });
      el.querySelector('[data-pk-reset]').addEventListener('click', function () {
        var o = readChecks();
        Object.keys(o).forEach(function (k) { if (k.indexOf(pre) === 0) delete o[k]; });
        writeChecks(o);
        draw();
      });
      el.querySelector('[data-pk-share]').addEventListener('click', function () {
        var text = shareText(name, state.month, state.stay, groups);
        var msg = el.querySelector('[data-pk-msg]');
        if (navigator.share) {
          navigator.share({ text: text }).catch(function () {});
        } else if (navigator.clipboard) {
          navigator.clipboard.writeText(text).then(function () { msg.textContent = 'コピーしました。LINE やメモに貼り付けられます。'; });
        }
      });
    }
    draw();
  }

  function init() {
    var els = document.querySelectorAll('#ym-packing');
    if (!els.length) return;
    load().then(function () { Array.prototype.forEach.call(els, mount); }).catch(function () {
      Array.prototype.forEach.call(els, function (el) { el.textContent = '持ち物リストを読み込めませんでした。'; });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();

  return { load: load, build: build, buyUrl: buyUrl, STAY_LABEL: STAY_LABEL };
})();
