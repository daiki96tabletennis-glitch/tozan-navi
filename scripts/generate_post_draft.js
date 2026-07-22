// Yamatch 毎日のX投稿案 自動生成スクリプト
// GitHub Actionsから node scripts/generate_post_draft.js で実行する想定
// 生成した下書きを data/post_draft.json に保存し、投稿履歴を post_history.json に記録する

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const MOUNTAINS_PATH = path.join(ROOT, 'data', 'mountains.json');
const HISTORY_PATH = path.join(ROOT, 'data', 'post_history.json');
const DRAFT_PATH = path.join(ROOT, 'data', 'post_draft.json');

const SITE_URL = 'https://tozan-navi.com';

function loadJson(p, fallback) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf-8'));
  } catch (e) {
    return fallback;
  }
}

function saveJson(p, data) {
  fs.writeFileSync(p, JSON.stringify(data, null, 2), 'utf-8');
}

function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function todayStr() {
  const now = new Date();
  // JSTに変換
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10);
}

const mountains = loadJson(MOUNTAINS_PATH, []);
const history = loadJson(HISTORY_PATH, { posts: [] });

// ==== テンプレート群 ====
// 直近14日で使ったテンプレート種別・山idはなるべく避ける
const recentTemplates = history.posts.slice(-14).map(p => p.templateType);
const recentMountainIds = new Set(history.posts.slice(-14).map(p => p.mountainId).filter(Boolean));

const TEMPLATE_TYPES = [
  'featured_mountain',   // 今日のおすすめ山
  'beginner_pick',       // 初心者向けピックアップ
  'weather_good',        // 天気の良い山
  'season_tip',          // シーズン豆知識
  'type_diagnosis',      // タイプ診断への誘導
  'train_access',        // 電車で行ける山特集
];

function chooseTemplateType() {
  // 直近使っていないものを優先
  const unused = TEMPLATE_TYPES.filter(t => !recentTemplates.slice(-2).includes(t));
  const pool = unused.length ? unused : TEMPLATE_TYPES;
  return pickRandom(pool);
}

function pickMountain(filterFn) {
  const candidates = mountains.filter(m => (!filterFn || filterFn(m)) && !recentMountainIds.has(m.id));
  const pool = candidates.length ? candidates : mountains.filter(filterFn || (() => true));
  return pickRandom(pool);
}

function mountainUrl(id) {
  return `${SITE_URL}/mountains/${id}/`;
}

function genFeaturedMountain() {
  const m = pickMountain(x => x.description && x.elevation);
  if (!m) return null;
  const body = `【今日の一座】${m.name}（${m.elevation}m・${m.area}）\n\n${(m.description || '').slice(0, 60)}...\n\n▼ルート・アクセス時間はこちら\n${mountainUrl(m.id)}\n\n#登山 #${m.name.replace(/[（）\s]/g, '')} #Yamatch`;
  return { text: body, mountainId: m.id };
}

function genBeginnerPick() {
  const m = pickMountain(x => x.difficulty === '初級' || x.difficulty === '初〜中級');
  if (!m) return null;
  const body = `【登山ギアなしでも行ける】\n${m.name}（${m.area}）は初心者でも楽しめる${m.difficulty}レベル。\n日帰りで気軽に登山デビューしてみませんか？\n\n${mountainUrl(m.id)}\n\n#初心者登山 #日帰り登山 #Yamatch`;
  return { text: body, mountainId: m.id };
}

function genWeatherGood() {
  const weatherMountains = mountains.filter(m => m.weatherLat);
  const m = pickMountain(x => weatherMountains.some(w => w.id === x.id));
  if (!m) return null;
  const body = `【天気情報つき】\n${m.name}の10日間天気をYamatchでチェック！\n登山コンディション（良好/注意/非推奨）もひと目で分かります。\n\n${mountainUrl(m.id)}\n\n#登山天気 #Yamatch`;
  return { text: body, mountainId: m.id };
}

function genSeasonTip() {
  const month = new Date().getMonth() + 1;
  const tips = {
    winter: 'この時期の高山は積雪・凍結の可能性あり。アイゼンの要否は各山のページでチェックできます。',
    spring: '残雪が残る山もまだ多い季節。事前に最新の登山道情報を確認してから出発しましょう。',
    summer: '熱中症・水分補給に要注意な季節。標高の高い山なら涼しく歩けます。',
    autumn: '紅葉シーズン到来。混雑する山も多いので、早朝出発がおすすめです。',
  };
  let key = 'summer';
  if ([12, 1, 2].includes(month)) key = 'winter';
  else if ([3, 4, 5].includes(month)) key = 'spring';
  else if ([9, 10, 11].includes(month)) key = 'autumn';
  const body = `【${month}月の登山豆知識】\n${tips[key]}\n\nYamatchで山ごとのシーズンカレンダーをチェック👇\n${SITE_URL}\n\n#登山 #Yamatch`;
  return { text: body, mountainId: null };
}

function genTypeDiagnosis() {
  const body = `【あなたの登山タイプは？】\nYamatchの登山タイプ診断で、自分にぴったりの山が見つかります。\n性格診断感覚で楽しめる登山版タイプ診断、試してみませんか？\n\n${SITE_URL}/recommend/\n\n#登山タイプ診断 #Yamatch`;
  return { text: body, mountainId: null };
}

function genTrainAccess() {
  const m = pickMountain(x => x.trainAccess);
  if (!m) return null;
  const body = `【電車で行ける山】\n${m.name}（${m.area}）は電車＋徒歩でアクセス可能。\n車を持っていなくても本格登山が楽しめます。\n\n${mountainUrl(m.id)}\n\n#電車登山 #Yamatch`;
  return { text: body, mountainId: m.id };
}

const GENERATORS = {
  featured_mountain: genFeaturedMountain,
  beginner_pick: genBeginnerPick,
  weather_good: genWeatherGood,
  season_tip: genSeasonTip,
  type_diagnosis: genTypeDiagnosis,
  train_access: genTrainAccess,
};

function generateDraft() {
  let templateType = chooseTemplateType();
  let result = GENERATORS[templateType] ? GENERATORS[templateType]() : null;

  // データ不足等でnullなら他のテンプレートにフォールバック
  let attempts = 0;
  while (!result && attempts < TEMPLATE_TYPES.length) {
    templateType = pickRandom(TEMPLATE_TYPES);
    result = GENERATORS[templateType]();
    attempts++;
  }
  if (!result) {
    templateType = 'type_diagnosis';
    result = genTypeDiagnosis();
  }
  return { templateType, ...result };
}

const draft = generateDraft();
const date = todayStr();

const draftRecord = {
  date,
  templateType: draft.templateType,
  mountainId: draft.mountainId,
  text: draft.text,
  charCount: draft.text.length,
  posted: false,
};

saveJson(DRAFT_PATH, draftRecord);

history.posts.push({
  date,
  templateType: draft.templateType,
  mountainId: draft.mountainId,
});
// 履歴は直近180件だけ保持
history.posts = history.posts.slice(-180);
saveJson(HISTORY_PATH, history);

console.log('=== 生成された下書き ===');
console.log(draft.text);
console.log('========================');
console.log('文字数:', draft.text.length);
