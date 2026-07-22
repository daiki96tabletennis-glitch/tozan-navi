// Yamatch 毎日のプッシュ通知送信スクリプト
// GitHub Actionsから node scripts/send_push_notification.js で実行する想定
// 環境変数 VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY / VAPID_SUBJECT が必要

const fs = require('fs');
const path = require('path');
const webpush = require('web-push');

const ROOT = path.resolve(__dirname, '..');
const SUB_PATH = path.join(ROOT, 'data', 'push_subscription.json');
const DRAFT_PATH = path.join(ROOT, 'data', 'post_draft.json');

const VAPID_PUBLIC_KEY = process.env.VAPID_PUBLIC_KEY;
const VAPID_PRIVATE_KEY = process.env.VAPID_PRIVATE_KEY;
const VAPID_SUBJECT = process.env.VAPID_SUBJECT || 'mailto:admin@tozan-navi.com';

if (!VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) {
  console.error('VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY が設定されていません');
  process.exit(1);
}

webpush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

function loadJson(p) {
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf-8'));
}

async function main() {
  const subscription = loadJson(SUB_PATH);
  if (!subscription || !subscription.endpoint) {
    console.error('購読情報がありません。/admin/notify-setup.html で設定してください。');
    process.exit(1);
  }

  const draft = loadJson(DRAFT_PATH);
  if (!draft) {
    console.error('下書きがありません。先に generate_post_draft.js を実行してください。');
    process.exit(1);
  }

  const payload = JSON.stringify({
    title: '📝 今日のX投稿案ができました',
    body: draft.text.length > 80 ? draft.text.slice(0, 80) + '...' : draft.text,
    url: '/admin/post-draft.html',
  });

  try {
    await webpush.sendNotification(subscription, payload);
    console.log('プッシュ通知を送信しました');
  } catch (err) {
    console.error('送信失敗:', err.statusCode, err.body || err.message);
    if (err.statusCode === 404 || err.statusCode === 410) {
      console.error('購読が失効しています。/admin/notify-setup.html で再設定してください。');
    }
    process.exit(1);
  }
}

main();
