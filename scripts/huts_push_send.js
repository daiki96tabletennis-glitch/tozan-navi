// 山小屋の予約開始のお知らせを、アプリの外に届く通知（プッシュ通知）で送る。
// .github/workflows/huts-push.yml が毎朝実行する。AIは使わない。
//
//   node scripts/huts_push_send.js                       本番（Firebase から登録を読み、送り、送った記録を残す）
//   node scripts/huts_push_send.js --test                管理者の端末（admin: true の登録）だけにテスト通知を送る
//   node scripts/huts_push_send.js --dry-run --subs f.json [--today 2027-03-01]
//                                                        送らずに、何を送るかだけ出す（手元の確認用。通信しない）
//
// 環境変数（本番・テスト）：
//   FIREBASE_DB_URL            登録を預かる Realtime Database のアドレス
//   FIREBASE_SERVICE_ACCOUNT   サービスアカウントの鍵（JSON の中身そのまま）
//   VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY / VAPID_SUBJECT
//
// 預かっているもの（/hutPush/<宛先から作った文字列>）：{endpoint, keys, alerts:[{id: 小屋ID, stay: 泊まりたい日}], at, admin}
// 送った記録（/hutPushSent/<同じ文字列>/<小屋ID|泊まりたい日|予約開始日|段階>）：同じお知らせを2回送らないため
//
// 予約開始日の計算は、アプリと同じもの（assets/js/huts-alert.js の @core-start〜@core-end）をそのまま読み込んで使う。
// 予約の型は data/huts_rules.json（自動取得で来季の日付が入れば、ここも新しい日付で判定する）。

const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const flag = (n) => args.indexOf(n) > -1;
const opt = (n) => (args.indexOf(n) > -1 ? args[args.indexOf(n) + 1] : null);
const DRY = flag('--dry-run');
const TEST = flag('--test');
const DAY = 86400000;

// 日本時間の「今日」（0時）。Actions は UTC で動くので、時差を足してから年月日を取り出す
function jstToday() {
  const o = opt('--today');
  if (o) { const p = o.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  const j = new Date(Date.now() + 9 * 3600 * 1000);
  return new Date(j.getUTCFullYear(), j.getUTCMonth(), j.getUTCDate());
}
const today = jstToday();

// アプリと同じ計算を読み込む
function loadCore() {
  const src = fs.readFileSync(path.join(ROOT, 'assets', 'js', 'huts-alert.js'), 'utf-8');
  const m = /\/\* @core-start[^*]*\*\/([\s\S]*?)\/\* @core-end \*\//.exec(src);
  if (!m) { throw new Error('huts-alert.js に @core-start〜@core-end が見つかりません'); }
  return new Function('today', 'DAY', m[1] + '\nreturn { compute: compute, ymd: ymd, jp: jp };')(today, DAY);
}
const core = loadCore();
const rules = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'huts_rules.json'), 'utf-8')).huts;

// きょう送る段階。7日前〜2日前は「1週間前」、1日前は「前日」、当日は「当日」。それ以外は送らない。
// 1週間前の分は、その日に実行できなかったときのために、2日前までは遅れて送る
function stageFor(open) {
  const left = Math.round((open - today) / DAY);
  if (left === 0) { return 0; }
  if (left === 1) { return 1; }
  if (left >= 2 && left <= 7) { return 7; }
  return null;
}

function messages(sub, sent) {
  const out = [];
  (sub.alerts || []).forEach(function (a) {
    const hut = rules[a.id];
    if (!hut || !hut.r) { return; }
    const c = core.compute(hut.r, a.stay || null);
    if (c.err || !c.open) { return; }
    const st = stageFor(c.open);
    if (st === null) { return; }
    const key = [a.id, a.stay || '-', core.ymd(c.open), st].join('|').replace(/[.#$\[\]\/]/g, '_');
    if (sent && sent[key]) { return; }
    const left = Math.round((c.open - today) / DAY);
    const title = hut.n + (st === 0 ? '：きょう予約開始' : st === 1 ? '：あした予約開始' : '：予約開始まであと' + left + '日');
    const body = (c.guess ? '昨年の日付からの目安です。' : '') + core.jp(c.open) + (c.time ? ' ' + c.time : '') + 'から'
      + (a.stay ? '（' + a.stay.replace(/-/g, '/') + ' 泊の分）' : '');
    out.push({ key: key, payload: { title: title, body: body, url: '/huts/' + a.id + '/', tag: 'ym-hut-' + a.id + '-' + (a.stay || 'x') } });
  });
  return out;
}

async function main() {
  // 手元の確認：通信しない
  if (DRY) {
    const subs = JSON.parse(fs.readFileSync(opt('--subs'), 'utf-8'));
    let n = 0;
    Object.keys(subs).forEach(function (id) {
      messages(subs[id], null).forEach(function (m) { n++; console.log(id.slice(0, 8), '|', m.payload.title, '|', m.payload.body, '|', m.payload.url, '|', m.key); });
    });
    console.log('きょう（' + core.ymd(today) + '）送る通知：' + n + '件／登録 ' + Object.keys(subs).length + '台');
    return;
  }

  const need = ['FIREBASE_DB_URL', 'FIREBASE_SERVICE_ACCOUNT', 'VAPID_PUBLIC_KEY', 'VAPID_PRIVATE_KEY'].filter(function (k) { return !process.env[k]; });
  if (need.length) { console.log('未設定のため何もしません：' + need.join('、')); return; }
  const webpush = require('web-push');
  const { JWT } = require('google-auth-library');
  const DB = process.env.FIREBASE_DB_URL.replace(/\/+$/, '');
  const sa = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
  const auth = new JWT({ email: sa.client_email, key: sa.private_key,
    scopes: ['https://www.googleapis.com/auth/firebase.database', 'https://www.googleapis.com/auth/userinfo.email'] });
  const token = (await auth.authorize()).access_token;
  const db = async function (method, p, body) {
    const res = await fetch(DB + p + '.json', { method: method, headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body) });
    if (!res.ok) { throw new Error('Firebase ' + method + ' ' + p + ' → ' + res.status); }
    return res.json();
  };
  webpush.setVapidDetails(process.env.VAPID_SUBJECT || 'mailto:admin@tozan-navi.com', process.env.VAPID_PUBLIC_KEY, process.env.VAPID_PRIVATE_KEY);

  const subs = (await db('GET', '/hutPush')) || {};
  const sentAll = (await db('GET', '/hutPushSent')) || {};
  const stat = { devices: Object.keys(subs).length, sent: 0, expired: 0, failed: 0 };
  const errors = [];
  for (const id of Object.keys(subs)) {
    const sub = subs[id];
    if (!sub || !sub.endpoint || !sub.keys) { continue; }
    let list;
    if (TEST) {
      if (!sub.admin) { continue; }
      list = [{ key: null, payload: { title: 'Yamatch：テスト通知', body: '山小屋の予約開始のお知らせは、この形で届きます。', url: '/mypage/', tag: 'ym-hut-test' } }];
    } else {
      list = messages(sub, sentAll[id] || {});
    }
    let gone = false;
    for (const m of list) {
      if (gone) { break; }
      try {
        await webpush.sendNotification({ endpoint: sub.endpoint, keys: sub.keys }, JSON.stringify(m.payload), { TTL: 12 * 3600 });
        stat.sent++;
        if (m.key) { await db('PUT', '/hutPushSent/' + id + '/' + encodeURIComponent(m.key), core.ymd(today)); }
      } catch (e) {
        if (e.statusCode === 404 || e.statusCode === 410) {            // 宛先が無効（アプリを消した・通知を切った）→ 預かった分を消す
          gone = true; stat.expired++;
          await db('DELETE', '/hutPush/' + id);
          await db('DELETE', '/hutPushSent/' + id);
        } else {
          stat.failed++;
          errors.push('- 送信に失敗：' + (e.statusCode || '') + ' ' + String(e.body || e.message || '').slice(0, 80));
        }
      }
    }
  }
  // 登録が消えた端末の「送った記録」を片づける
  for (const id of Object.keys(sentAll)) { if (!subs[id]) { await db('DELETE', '/hutPushSent/' + id); } }

  const head = '# 山小屋の予約開始の通知（' + core.ymd(today) + (TEST ? '・テスト' : '') + '）';
  const lines = ['- 登録している端末：' + stat.devices + '台／送った通知：' + stat.sent + '件／無効になっていた宛先：' + stat.expired + '台／失敗：' + stat.failed + '件'].concat(errors.slice(0, 20));
  console.log(head + '\n\n' + lines.join('\n'));
  if (opt('--out')) { fs.writeFileSync(opt('--out'), head + '\n\n## 送信の失敗\n\n' + (errors.length ? errors.slice(0, 20).join('\n') : '- なし') + '\n'); }
  if (stat.failed) { process.exitCode = 1; }
}

main().catch(function (e) { console.error(e && e.message ? e.message : e); process.exit(1); });
