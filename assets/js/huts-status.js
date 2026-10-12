/* 山小屋の「いま営業中か」を、カードの data-season（scripts/huts_season.py が作る）と今日の日付から出す。
   緑＝営業中、黄＝まもなく営業終了（7日以内）・営業の開始や終了の時期、灰＝営業期間外・判定できない */
(function () {
  var now = new Date();
  var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  var DAY = 86400000;

  function md(d) { return (d.getMonth() + 1) + '/' + d.getDate(); }
  function mk(y, m, d) {
    var last = new Date(y, m, 0).getDate();
    return new Date(y, m - 1, Math.min(d, last));
  }

  function judge(s) {
    if (!s) { return null; }
    if (s.closed) { return ['off', '今季は休業', '']; }
    if (s.all) { return ['on', '通年営業', s.caveat ? '休業日・冬季の条件あり。公式サイトで確認' : '']; }
    var y = today.getFullYear(), i, r, a1, b1, a2, b2, left, next = null, recur = !s.y;
    if (s.y && s.y < y) { return ['off', '営業期間は未確認', s.y + '年の情報です']; }
    if (s.y && s.y > y) { return ['off', '営業期間外', s.y + '年の営業を予定']; }
    for (i = 0; i < s.r.length; i++) {
      r = s.r[i];
      a1 = mk(y, r[0], r[1]); b1 = mk(y, r[0], r[2]);
      a2 = mk(y, r[3], r[4]); b2 = mk(y, r[3], r[5]);
      if (today >= b1 && today <= a2) {
        left = Math.round((a2 - today) / DAY);
        if (r[4] === r[5] && left <= 7) {
          return ['soon', left === 0 ? '本日で営業終了' : 'まもなく営業終了', md(a2) + 'まで（あと' + left + '日）'];
        }
        return ['on', '営業中', (r[4] === r[5] ? md(a2) + 'まで' : r[3] + '月' + (r[4] <= 1 ? '上旬' : r[4] <= 11 ? '中旬' : '下旬') + 'ごろまで') + (recur ? '（例年）' : '')];
      }
      if (today >= a1 && today < b1) { return ['soon', '営業開始の時期', '開始日は公式サイトで確認' + (recur ? '（例年' + r[0] + '月）' : '')]; }
      if (today > a2 && today <= b2) { return ['soon', '営業終了の時期', '終了日は公式サイトで確認' + (recur ? '（例年' + r[3] + '月）' : '')]; }
      if (today < a1 && (!next || a1 < next[0])) { next = [a1, r]; }
    }
    if (next) {
      return ['off', '営業期間外', (next[1][1] === next[1][2] ? md(next[0]) + 'から' : next[1][0] + '月から') + (recur ? '（例年）' : '')];
    }
    return ['off', '営業期間外', recur ? '今季の営業は終了（例年）' : '今季の営業は終了'];
  }

  // 12か月の帯：今月に印を付ける
  var cur = document.querySelectorAll('.mbar i[data-m="' + (today.getMonth() + 1) + '"]'), k;
  for (k = 0; k < cur.length; k++) { cur[k].className = 'now'; }

  var els = document.querySelectorAll('[data-season]'), i, s, j, el;
  for (i = 0; i < els.length; i++) {
    el = els[i];
    try { s = JSON.parse(el.getAttribute('data-season')); } catch (e) { s = null; }
    j = judge(s);
    if (!j) { continue; }
    el.className = 'st st-' + j[0];
    el.innerHTML = '<i></i><b></b><small></small>';
    el.querySelector('b').textContent = j[1];
    el.querySelector('small').textContent = j[2];
    el.setAttribute('title', j[1] + (j[2] ? '（' + j[2] + '）' : ''));
  }
})();
