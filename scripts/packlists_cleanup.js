// 持ち物チェックリストの共有のリスト（Firebase の /packLists）のうち、期限（expireAt＝登る日の30日後）を過ぎたものを消す。
// .github/workflows/huts-push.yml が毎朝、プッシュ通知を送ったあとに実行する（失敗しても通知の結果には影響させない）。AIは使わない。
//
//   node scripts/packlists_cleanup.js            本番（期限切れを消す）
//   node scripts/packlists_cleanup.js --dry-run  消さずに件数だけ出す
//
// 環境変数：FIREBASE_DB_URL / FIREBASE_SERVICE_ACCOUNT（huts_push_send.js と同じ）

async function main() {
  const DRY = process.argv.indexOf('--dry-run') > -1;
  if (!process.env.FIREBASE_DB_URL || !process.env.FIREBASE_SERVICE_ACCOUNT) { console.log('未設定のため何もしません'); return; }
  const { JWT } = require('google-auth-library');
  const DB = process.env.FIREBASE_DB_URL.replace(/\/+$/, '');
  const sa = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
  const auth = new JWT({ email: sa.client_email, key: sa.private_key,
    scopes: ['https://www.googleapis.com/auth/firebase.database', 'https://www.googleapis.com/auth/userinfo.email'] });
  const token = (await auth.authorize()).access_token;
  const db = async function (method, p) {
    const res = await fetch(DB + p, { method: method, headers: { Authorization: 'Bearer ' + token } });
    if (!res.ok) throw new Error('Firebase ' + method + ' ' + p + ' → ' + res.status);
    return res.json();
  };
  // 期限だけを並べて読む（中身は読まない）
  const lists = (await db('GET', '/packLists.json?shallow=true')) || {};
  const now = Date.now();
  let gone = 0, kept = 0;
  for (const id of Object.keys(lists)) {
    const exp = await db('GET', '/packLists/' + id + '/expireAt.json');
    if (typeof exp === 'number' && exp > now) { kept++; continue; }
    gone++;
    if (!DRY) await db('DELETE', '/packLists/' + id + '.json');
  }
  console.log('持ち物リスト：残す ' + kept + ' 件／' + (DRY ? '消す予定 ' : '消した ') + gone + ' 件');
}
main().catch(function (e) { console.error(e && e.message ? e.message : e); process.exit(1); });
