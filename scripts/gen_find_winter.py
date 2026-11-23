"""冬の山選び診断（/find/winter/index.html）を作る（2026-11-17〜。運営者の指示「冬登山に特化した山選び診断を、既存の山選び診断を改造して」）。
手で編集しない。見た目（CSS）は /find/index.html から読み、冬の分を足す。山のデータは data/winter_find.json（scripts/build_winter_find.py）。
データを直したら build_winter_find.py → このスクリプトの順に流す（見た目は /find/ と同じ。記事のような説明・よくある質問は置かない＝運営者の指示 2026-11-17）。
--check は書かずに同じかを見る（check_pages.py セクション26）。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import ym_icons as I  # noqa: E402

OUT = os.path.join(ROOT, 'find', 'winter', 'index.html')
URL = 'https://tozan-navi.com/find/winter/'
TITLE = '冬の山選び診断｜12月・1月・2月に登れる関東の山を9問で【雪なし〜雪山入門】'
DESC = ('雪の無い山からチェーンスパイクの山、雪山入門まで。行く月・装備・交通手段を選ぶと、装備カレンダーと冬の運休・通行止めを見て、'
        '関東から日帰りで行ける冬の山を提案します。富士山・雪景色・山頂からの大展望・下山後の温泉でも選べます。')
OG_IMAGE = 'https://tozan-navi.com/articles/images/hero_winter_views.jpg?v=20261115'
CAR_SVG = ('<svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><path d="M4 13l1.5-4A2 2 0 0 1 7.3 8h9.4a2 2 0 0 1 1.8 1.2L20 13z" fill="currentColor"/>'
           '<rect x="2.5" y="13" width="19" height="4.5" rx="2" fill="currentColor"/><rect x="6.5" y="9.2" width="4" height="2.8" rx="0.5" fill="white"/>'
           '<rect x="11.5" y="9.2" width="6" height="2.8" rx="0.5" fill="white"/><circle cx="6.5" cy="17.5" r="1.6" fill="#3a3530"/><circle cx="17.5" cy="17.5" r="1.6" fill="#3a3530"/></svg>')
ICON_NAMES = ['snowflake', 'sprout', 'sun', 'footprints', 'mountain-snow', 'pickaxe', 'compass', 'users', 'handshake', 'train-front',
              'leaf', 'dumbbell', 'mountain', 'sunrise', 'sparkles', 'droplets', 'utensils', 'bell', 'check', 'zap', 'clock', 'map',
              'map-pin', 'triangle-alert', 'backpack', 'timer', 'route', 'binoculars', 'clipboard-list', 'search', 'trophy', 'flame', 'wind',
              'smartphone', 'shirt', 'lightbulb']
LOGO = ('<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M2 20 L8 9 L14 20 Z" fill="#405830"/>'
        '<path d="M8 20 L14 6 L20 20 Z" fill="#789858"/><path d="M13 20 L18 12 L23 20 Z" fill="#2c4020"/></svg>')


def esc(s):
    return (str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))


def icons_js():
    out = {}
    for n in ICON_NAMES:
        if n in I.LUCIDE or n in I.CUSTOM:
            out[n] = I.svg(n, size='1em', style=I.ICON_STYLE)
    out['car'] = CAR_SVG
    return json.dumps(out, ensure_ascii=False)


def base_css():
    s = open(os.path.join(ROOT, 'find', 'index.html'), encoding='utf-8').read()
    # いちばん長い style（本体の見た目）。12〜2月の入れ替え用の短い style（ym-winter-swap）は使わない
    css = max(re.findall(r'<style>(.*?)</style>', s, re.S), key=len)
    if 'ym-winter-swap' in css:
        raise SystemExit('/find/ の見た目に入れ替え用の指定が混ざっている')
    # 見た目は /find/ と同じ（上の写真・ヘッダー・選択肢・結果の見出し。2026-11-17 運営者の指示「UIは以前の山選び診断に揃えて」）
    return css


WINTER_CSS = """
.intro-hero h1{margin:0 0 8px;}
.intro-tag .ym-ic{margin-right:3px;}
.choice-icon .ym-ic{width:28px;height:28px;color:#4e6535;}
.rb-gear{background:#eef4e8;color:#4a6838;border:0.5px solid #b0cc90;}
.rb-warn{background:#fdf0e4;color:#8a5010;border:0.5px solid #e2b583;}
.rb-dia{background:#fff4e0;color:#8a5820;border:0.5px solid #d4a860;}
.rc-course{padding:9px 14px;border-top:1px solid #f0ede5;font-size:12px;color:#3a3530;line-height:1.6;}
.rc-course b{font-weight:700;color:#2a3820;}
.rc-course .ym-ic{color:#4e6535;margin-right:3px;}
.rc-note{margin:0 14px 10px;padding:9px 11px;border-radius:10px;background:#fdf6ec;border:1px solid #ecd2ab;font-size:11.5px;color:#6a4a20;line-height:1.6;}
.rc-note ul{margin:4px 0 0;padding-left:18px;}
.rc-note .ym-ic{color:#b06a10;margin-right:3px;}
.rc-sub{display:block;margin:-4px 14px 14px;text-align:center;font-size:12px;color:#4e6535;font-weight:700;text-decoration:none;}
.more-list{background:white;border:1px solid #e0dbd4;border-radius:12px;padding:12px 14px;margin-bottom:20px;}
.more-title{font-size:11px;font-weight:700;color:#8a7a6a;letter-spacing:0.06em;margin-bottom:6px;}
.more-list a{display:flex;justify-content:space-between;gap:8px;padding:7px 0;border-bottom:1px solid #f4f1ea;color:#2a2520;text-decoration:none;font-size:13px;font-weight:700;}
.more-list a:last-child{border-bottom:none;}
.more-list a span{font-size:11px;color:#8a7a6a;font-weight:400;white-space:nowrap;}
.fw-guide{background:white;border:1px solid #e0dbd4;border-radius:12px;padding:14px;margin-bottom:20px;}
.fw-guide h2{margin:0 0 3px;font-size:16px;color:#2a3820;line-height:1.4;}
.fw-guide-lead{margin:0 0 10px;font-size:12px;color:#6a6258;line-height:1.6;}
.fw-tabs{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;}
.fw-tab{min-height:42px;padding:6px;border:1px solid #c8d4b8;border-radius:8px;background:#f6f8f1;color:#4e6535;font:700 13px 'Zen Kaku Gothic New',sans-serif;cursor:pointer;}
.fw-tab[aria-selected="true"]{background:#4e6535;border-color:#4e6535;color:#fff;}
.fw-tab:focus-visible,.fw-img-link:focus-visible{outline:3px solid #2a3820;outline-offset:2px;}
.fw-img-link{display:block;border-radius:8px;overflow:hidden;border:1px solid #e8e4dc;}
.fw-img-link img{display:block;width:100%;height:auto;}
.fw-zoom{display:block;margin-top:7px;text-align:center;font-size:12px;font-weight:700;color:#4e6535;text-decoration:none;}
.fw-guide-note{margin:10px 0 0;padding:9px 11px;border-radius:10px;background:#fdf6ec;border:1px solid #ecd2ab;font-size:12px;color:#6a4a20;line-height:1.6;}
"""


def jsonld():
    graph = [
        {'@type': 'WebPage', '@id': URL, 'url': URL, 'name': TITLE, 'description': DESC, 'inLanguage': 'ja',
         'isPartOf': {'@type': 'WebSite', 'name': 'Yamatch', 'url': 'https://tozan-navi.com/'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Yamatch', 'item': 'https://tozan-navi.com/'},
            {'@type': 'ListItem', 'position': 2, 'name': '山選び診断', 'item': 'https://tozan-navi.com/find/'},
            {'@type': 'ListItem', 'position': 3, 'name': '冬の山選び診断', 'item': URL}]},
    ]
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)


def page():
    html = TEMPLATE
    rep = {
        '@@TITLE@@': esc(TITLE + ' - Yamatch'), '@@OGTITLE@@': esc('冬の山選び診断 - Yamatch'), '@@DESC@@': esc(DESC), '@@URL@@': URL,
        '@@OGIMG@@': OG_IMAGE, '@@CSS@@': base_css() + WINTER_CSS, '@@JSONLD@@': jsonld(), 
        '@@ICONS@@': icons_js(),
        '@@TRAIN@@': I.svg('train-front', size='12px', style=I.ICON_STYLE), '@@TIMER@@': I.svg('timer', size='12px', style=I.ICON_STYLE),
        '@@FREE@@': I.svg('sparkles', size='12px', style=I.ICON_STYLE),
        '@@SNOW@@': I.svg('snowflake', size='12px', style=I.ICON_STYLE),
        
    }
    for k, v in rep.items():
        if k not in html:
            raise SystemExit('テンプレートに無い：' + k)
        html = html.replace(k, v)
    if '@@' in html:
        raise SystemExit('置き換え残り：' + re.search(r'@@\w+@@', html).group(0))
    return html


TEMPLATE = r"""<!DOCTYPE html>
<!-- generated: scripts/gen_find_winter.py（手で編集しない） -->
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Yamatch">
<meta property="og:title" content="@@OGTITLE@@">
<meta property="og:description" content="@@DESC@@">
<meta property="og:url" content="@@URL@@">
<meta property="og:image" content="@@OGIMG@@">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="@@URL@@">
<link rel="apple-touch-icon" sizes="180x180" href="/icon-180.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="manifest" href="/manifest.json">
<link href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@700;900&display=swap" rel="stylesheet">
<script type="application/ld+json">@@JSONLD@@</script>
<style>@@CSS@@</style>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-TMTVVTEEGF"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-TMTVVTEEGF');
</script>
<script defer src="/assets/js/ym-track.js?v=20261103b"></script>
</head>
<body>
<header class="ym-header">
  <div class="ym-header-inner">
    <a href="/"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>戻る</a>
    <div class="ym-header-title">冬の山選び診断</div>
  </div>
</header>
<main>
<div id="find-loading">
  <div class="fl-bars"><div class="fl-bar"></div><div class="fl-bar"></div><div class="fl-bar"></div><div class="fl-bar"></div><div class="fl-bar"></div></div>
  <div class="fl-txt">冬に行ける山を探しています...</div>
</div>
<div id="step-intro" class="step active">
  <div class="intro-hero">
    <h1 class="intro-hero-title">冬の山選び診断<br>11月〜3月に登れる山</h1>
    <div class="intro-hero-sub">9問に答えるだけ。雪の無い山からチェーンスパイクの山、雪山入門まで、行く月の装備と冬の運休・通行止めを見て提案します</div>
    <div class="intro-tags">
      <span class="intro-tag">@@SNOW@@雪なし〜雪山入門</span>
      <span class="intro-tag">@@TRAIN@@電車・車どちらも</span>
      <span class="intro-tag">@@TIMER@@約2分</span>
      <span class="intro-tag">@@FREE@@無料</span>
    </div>
    <button class="start-btn" onclick="startQuiz()">診断スタート →</button>
    <div class="intro-note">※関東（新宿・大宮・横浜）から日帰りで行ける山から選びます</div>
  </div>
</div>
<div id="step-q" class="step">
  <div class="q-wrap">
    <div class="back-row">
      <button class="back-btn-q" onclick="goBack()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>戻る</button>
    </div>
    <div class="progress-bar"><div class="progress-fill" id="prog-fill" style="width:0%"></div></div>
    <div class="q-num" id="q-num"></div>
    <div class="q-text" id="q-text"></div>
    <div class="q-sub" id="q-sub"></div>
    <div class="choices" id="choices"></div>
  </div>
</div>
<div id="step-result" class="step">
  <div class="result-wrap">
    <div class="result-header">
      <div class="result-header-title">あなたにおすすめの冬の山</div>
      <div class="result-header-main" id="result-headline"></div>
      <div class="result-count" id="result-count"></div>
    </div>
    <div class="result-cards" id="result-cards"></div>
    <div id="more-list"></div>
    <section class="fw-guide" aria-labelledby="fw-guide-title">
      <h2 id="fw-guide-title">はじめて登山をする人へ</h2>
      <p class="fw-guide-lead">出発前にやることと、冬の服装をまとめました。</p>
      <div class="fw-tabs" role="tablist" aria-label="はじめての登山のガイド">
        <button class="fw-tab" id="fw-tab-0" type="button" role="tab" aria-selected="true" aria-controls="fw-panel-0" onclick="fwGuideTab(0)">登山の基本</button>
        <button class="fw-tab" id="fw-tab-1" type="button" role="tab" aria-selected="false" aria-controls="fw-panel-1" onclick="fwGuideTab(1)">冬の服装</button>
      </div>
      <div id="fw-panel-0" role="tabpanel" aria-labelledby="fw-tab-0">
        <a class="fw-img-link" href="/images/find/winter-hiking-basics.webp" target="_blank" rel="noopener" onclick="fwGuideOpen('basics')"><img src="/images/find/winter-hiking-basics.webp" width="1216" height="1294" loading="lazy" decoding="async" alt="登山の基本。登山前は、体力に合うコースを選び、登山計画を作り、地図をスマホに保存し、天気・日没時刻・通行止めを確認して家族に行程を伝え、登山届を出す。当日は、こまめに地図を見て、ルートから外れたら立ち止まり、遅れたら山頂にこだわらず引き返す。持ち物は靴、雨具・防寒着、飲料と行動食、充電済みスマホとモバイルバッテリー、ヘッドライト。"></a>
        <a class="fw-zoom" href="/images/find/winter-hiking-basics.webp" target="_blank" rel="noopener" onclick="fwGuideOpen('basics')">画像を大きく見る</a>
      </div>
      <div id="fw-panel-1" role="tabpanel" aria-labelledby="fw-tab-1" hidden>
        <a class="fw-img-link" href="/images/find/winter-clothing-basics.webp" target="_blank" rel="noopener" onclick="fwGuideOpen('clothing')"><img src="/images/find/winter-clothing-basics.webp" width="1055" height="1491" loading="lazy" decoding="async" alt="冬の低山での服装の基本。肌着は化繊かウール、中間着はフリースや薄手ダウン、上着は防風のシェルの3層で重ね着する。長ズボン、登山用ソックスと滑りにくい靴、手袋、帽子、ネックウォーマーをそろえる。歩いて暑くなったら脱ぎ、休憩中はすぐ防寒着を着る。綿のTシャツだけ、厚着のしすぎ、休憩中に上着を着ないのは避ける。"></a>
        <a class="fw-zoom" href="/images/find/winter-clothing-basics.webp" target="_blank" rel="noopener" onclick="fwGuideOpen('clothing')">画像を大きく見る</a>
      </div>
      <p class="fw-guide-note" id="fw-guide-note"></p>
    </section>
    <div id="gear-section" class="info-section"></div>
    <div id="tips-section" class="info-section"></div>
    <button class="retry-btn" onclick="resetQuiz()">↺ もう一度診断する</button>
    <a class="type-nudge" href="/find/?mode=all">
      <div class="type-nudge-text">
        <div class="type-nudge-label">冬以外の季節は</div>
        <div class="type-nudge-title">山選び診断（通年）で探す</div>
      </div>
      <div class="type-nudge-arrow">›</div>
    </a>
  </div>
</div>
</main>
<script src="/assets/js/volcano-status.js?v=20261010a"></script>
<script>
var IC = @@ICONS@@;
function ic(n){ return IC[n] || ''; }
var MONTH_LABEL = { '11': '11月', '12': '12月', '1': '1月', '2': '2月', '3': '3月' };
var QUESTIONS = [
  { id: 'when', text: 'いつごろ行く予定ですか？', sub: 'その月の雪や凍結、バス・ロープウェイの運行に合わせて選びます',
    choices: [
      { value: '11', icon: 'leaf',      label: '11月', sub: '高い山から雪が降り始める' },
      { value: '12', icon: 'snowflake', label: '12月', sub: '年末年始を含む' },
      { value: '1',  icon: 'snowflake', label: '1月', sub: '寒さがいちばん厳しい時期' },
      { value: '2',  icon: 'snowflake', label: '2月', sub: '雪が多い時期' },
      { value: '3',  icon: 'sprout',    label: '3月', sub: '雪が残る山も多い' }
    ] },
  { id: 'gear', text: 'どのくらいの雪の山まで行きたいですか？', sub: '持っている装備と、雪山の経験で選んでください',
    choices: [
      { value: 'none',   icon: 'sun',           label: '雪の無い山がいい', sub: 'アイゼンは持っていない' },
      { value: 'light',  icon: 'footprints',    label: 'うっすら雪・凍結くらいまで', sub: 'チェーンスパイク・軽アイゼンなら使える' },
      { value: 'entry',  icon: 'mountain-snow', label: '雪山に行きたい（入門）', sub: '12本爪アイゼン・ピッケルを数回使った' },
      { value: 'expert', icon: 'pickaxe',       label: '本格的な雪山に慣れている', sub: '冬山の経験が何度もある' }
    ] },
  { id: 'who', text: '誰と行きますか？', sub: '一緒に行く人に合う山を選びます',
    choices: [
      { value: 'solo',    icon: 'compass',   label: 'ひとりで', sub: '人の多い定番の山を優先します' },
      { value: 'friends', icon: 'users',     label: '友人・パートナーと', sub: '茶屋や寄り道も楽しめる山を優先します' },
      { value: 'family',  icon: 'handshake', label: '子ども・家族と', sub: '雪の無い、やさしい山だけにします' }
    ] },
  { id: 'transport', text: '山へはどうやって行きますか？', sub: '冬に運休するバス・ロープウェイの山は、電車・バスでは出しません',
    choices: [
      { value: 'train', icon: 'train-front', label: '電車・バスだけで行きたい', sub: '車を持っていない、または運転しない' },
      { value: 'car',       icon: 'car', label: '車（冬用タイヤ・チェーンあり）', sub: '雪や凍結の道も走れる' },
      { value: 'carnormal', icon: 'car', label: '車（ノーマルタイヤ）', sub: '駐車場が低く、雪の日が少ない山だけにします' }
    ] },
  { id: 'fitness', text: '普段の運動量はどのくらいですか？', sub: '冬は日が短いので、歩く時間の上限にも使います',
    choices: [
      { value: 'low',  icon: 'leaf',       label: 'ほとんど運動しない', sub: '歩くのは3時間くらいまで' },
      { value: 'mid',  icon: 'footprints', label: '軽く歩くことはある', sub: '歩くのは5時間くらいまで' },
      { value: 'high', icon: 'dumbbell',   label: '体を動かすのは好き', sub: '6時間半くらいまで歩ける' }
    ] },
  { id: 'see', text: '冬の山で何を見たいですか？', sub: '一番ピンとくるものを選んでください',
    choices: [
      { value: 'fuji',    icon: 'mountain',  label: '空気の澄んだ冬の富士山', sub: '山頂や稜線から富士山が見える山' },
      { value: 'ice',     icon: 'snowflake', label: '雪景色・霧氷', sub: '雪の上を歩く、冬にしか見られない景色' },
      { value: 'pano',    icon: 'binoculars', label: '山頂からの大展望', sub: '360度の眺め・名峰や海まで見渡せる山' },
      { value: 'easy',    icon: 'sparkles',  label: 'とにかく気軽に', sub: '寒い時期は短く楽しみたい' }
    ] },
  { id: 'after', text: '下山したあと、何をしたいですか？', sub: '冷えた体を温める楽しみに合う山を上げます',
    choices: [
      { value: 'onsen',  icon: 'droplets', label: '温泉・サウナで温まりたい', sub: '登山口の近くや帰り道に温泉・サウナがある山' },
      { value: 'food',   icon: 'utensils', label: '茶屋や山小屋で温かいものを', sub: '山頂や途中でひと休み' },
      { value: 'shrine', icon: 'bell',     label: '初詣・神社やお寺に寄りたい', sub: '信仰の山・古い道・史跡' },
      { value: 'none',   icon: 'check',    label: '特にない', sub: 'おまかせで選んでほしい' }
    ] },
  { id: 'time', text: '自宅から登山口まで何時間かけられますか？', sub: '冬は早く下山するので、近い山ほど上げます',
    choices: [
      { value: 'near',   icon: 'zap',   label: '1〜2時間以内', sub: 'できるだけ近場がいい' },
      { value: 'middle', icon: 'clock', label: '2〜3時間くらいなら', sub: '少し遠くても行きたい山があれば' },
      { value: 'far',    icon: 'map',   label: '時間はあまり気にしない', sub: '4時間以上でもOK' }
    ] },
  { id: 'depart', text: '出発地はどのあたりですか？', sub: '一番近い拠点を選んでください',
    choices: [
      { value: 'ofuna',    icon: 'map-pin', label: '横浜・大船・湘南方面', sub: '神奈川中心' },
      { value: 'shinjuku', icon: 'map-pin', label: '新宿・渋谷・都内方面', sub: '東京中心' },
      { value: 'omiya',    icon: 'map-pin', label: '大宮・浦和・埼玉方面', sub: '埼玉中心' }
    ] }
];

var answers = {};
var currentQ = 0;
var mountainsData = [];
var loaded = false;

fetch('/data/winter_find.json')
  .then(function(r){ return r.json(); })
  .then(function(data){
    mountainsData = data.mountains || [];
    loaded = true;
    // 噴火警報が出ている山は「規制中」として外す（気象庁のデータ。山選び診断と同じ）
    if(window.YMVolcano) window.YMVolcano.load(function(){ window.YMVolcano.apply(mountainsData); });
  })
  .catch(function(){ loaded = true; });

function startQuiz(){
  answers = {}; currentQ = 0; _transitioning = false;
  show('step-q'); renderQ();
  if(typeof gtag === 'function') gtag('event', 'diagnosis_start', { diagnosis_type: 'find_winter' });
}
function goBack(){
  if(currentQ === 0){ show('step-intro'); return; }
  currentQ--;
  var stepQ = document.getElementById('step-q');
  stepQ.classList.remove('animating','animating-back'); void stepQ.offsetWidth; stepQ.classList.add('animating-back');
  renderQ();
}
function renderQ(){
  var q = QUESTIONS[currentQ];
  document.getElementById('prog-fill').style.width = Math.round((currentQ / QUESTIONS.length) * 100) + '%';
  document.getElementById('q-num').textContent = (currentQ + 1) + ' / ' + QUESTIONS.length;
  document.getElementById('q-text').textContent = q.text;
  document.getElementById('q-sub').textContent = q.sub;
  var html = '';
  q.choices.forEach(function(c){
    var sel = answers[q.id] === c.value ? ' selected' : '';
    html += '<button class="choice' + sel + '" data-val="' + c.value + '" onclick="selectChoice(\'' + q.id + '\',\'' + c.value + '\',this)">';
    html += '<div class="choice-icon">' + ic(c.icon) + '</div>';
    html += '<div><div class="choice-label">' + c.label + '</div><div class="choice-sub">' + c.sub + '</div></div></button>';
  });
  document.getElementById('choices').innerHTML = html;
  window.scrollTo(0, 0);
}
var _transitioning = false;
function selectChoice(qid, val, el){
  if(_transitioning) return;
  _transitioning = true;
  answers[qid] = val;
  if(el){
    var rpl = document.createElement('span'); rpl.className = 'ripple';
    var rc = el.getBoundingClientRect(); var sz = Math.max(rc.width, rc.height);
    rpl.style.width = rpl.style.height = sz + 'px';
    rpl.style.left = (rc.width/2 - sz/2) + 'px'; rpl.style.top = (rc.height/2 - sz/2) + 'px';
    el.appendChild(rpl); setTimeout(function(){ if(rpl.parentNode) rpl.parentNode.removeChild(rpl); }, 600);
  }
  document.querySelectorAll('#choices .choice').forEach(function(b){ b.classList.toggle('selected', b.getAttribute('data-val') === val); });
  setTimeout(function(){
    _transitioning = false;
    if(currentQ < QUESTIONS.length - 1){
      currentQ++;
      var stepQ = document.getElementById('step-q');
      stepQ.classList.remove('animating','animating-back'); void stepQ.offsetWidth; stepQ.classList.add('animating');
      renderQ();
    } else if(!loaded){
      document.getElementById('choices').innerHTML = '<div style="text-align:center;padding:24px;color:#8a7a6a;">データを読み込み中...</div>';
      var check = setInterval(function(){ if(loaded){ clearInterval(check); showResult(); } }, 100);
    } else {
      showResult();
    }
  }, 220);
}

// ===== 判定 =====
var RANK = { no_crampons: 0, light_crampons: 1, winter_gear: 2 };
var GEAR_LABEL = { no_crampons: 'アイゼン不要', light_crampons: '軽アイゼン等（チェーンスパイク・6本爪アイゼンなど）', winter_gear: '冬山装備（12本爪アイゼン・ピッケル等）', closed: '入山不可' };
var GEAR_SHORT = { no_crampons: 'アイゼン不要', light_crampons: '軽アイゼン等', winter_gear: '冬山装備', closed: '入山不可' };
var ALLOW = { none: 0, light: 1, entry: 2, expert: 2 };
var WALK_CAP = { low: 180, mid: 300, high: 390 };
var WALK_FIT = { low: [90, 180], mid: [150, 300], high: [240, 390] };
var ICE_RE = /霧氷|樹氷|雪景色|雪原|銀世界|雪山|スノーシュー/;

// その月の装備。月の途中で変わる月は、厳しいほうと切り替わる日
function gearOf(m){
  var e = m.g[answers.when];
  if(!e) return { worst: null };
  if(typeof e === 'string') return { worst: e };
  var order = ['no_crampons','light_crampons','winter_gear','closed'];
  var worst = order.indexOf(e.b) > order.indexOf(e.a) ? e.b : e.a;
  return { worst: worst, split: e };
}
function gearText(g){
  var mo = MONTH_LABEL[answers.when];
  if(g.split){
    return mo + 'は' + g.split.d + '日ごろまで' + GEAR_SHORT[g.split.b] + '、' + g.split.d + '日ごろから' + GEAR_SHORT[g.split.a];
  }
  return mo + 'は' + GEAR_LABEL[g.worst];
}
function hasTag(m, t){ return (m.tags || []).indexOf(t) > -1; }
function fpText(m){ return (m.fp || []).map(function(p){ return (p.l || '') + ' ' + (p.x || ''); }).join(' '); }
function isRestricted(m){ return m.rest || (m.status && m.status.level === 'restricted'); }

// 歩くコース：泊まらないコースのうち、条件に合うもののいちばん短いもの
// その月（15日）にコースが冬に使えないか（routes[].winter。closed は誰も、car_only は電車・バスの人だけ使えない。2026-11-19〜）
function winterBlocked(r){
  var w = r.w;
  if(!w || !w.f || !w.t) return false;
  if(w.st !== 'closed' && !(w.st === 'car_only' && answers.transport === 'train')) return false;
  var md = ('0' + answers.when).slice(-2) + '-15';
  return w.f <= w.t ? (md >= w.f && md <= w.t) : (md >= w.f || md <= w.t);
}

function pickRoute(m, winterGear){
  var cap = WALK_CAP[answers.fitness] || 300;
  var list = (m.routes || []).filter(function(r){
    if(r.min > cap) return false;
    if(winterBlocked(r)) return false;
    if(answers.who === 'family' && (r.chain || r.rock)) return false;
    if(winterGear){
      if(r.tech === 'D' || r.tech === 'E') return false;
      if(answers.gear === 'entry' && (r.chain || r.tech === 'C')) return false;
    }
    return true;
  });
  if(answers.transport === 'train'){
    var tr = list.filter(function(r){ return r.train; });
    if(tr.length) list = tr;
  }
  // 冬の行き方を確かめられていないコースは、ほかに使えるコースがあれば選ばない
  var known = list.filter(function(r){ return !(r.w && r.w.st === 'unknown'); });
  if(known.length) list = known;
  list.sort(function(a, b){ return a.min - b.min; });
  return list[0] || null;
}

function travelMin(m){
  var dep = answers.depart || 'ofuna';
  if(answers.transport === 'train'){
    var k = dep === 'ofuna' ? 'yokohama' : dep;
    var v = m.tt ? m.tt[k] : null;
    return (typeof v === 'number' && v > 0) ? v : null;
  }
  var d = m.dt ? m.dt[dep] : null;
  return (typeof d === 'number' && d > 0) ? d : null;
}

function scoreMount(m){
  if(!m.day || isRestricted(m)) return null;
  var mo = answers.when;
  var g = gearOf(m);
  if(!g.worst || g.worst === 'closed') return null;
  var rank = RANK[g.worst];
  var allow = ALLOW[answers.gear];
  if(answers.who === 'family') allow = 0;
  if(rank > allow) return null;
  var wg = rank === 2;
  // 冬山装備の山：上級は出さない。入門は中級まで
  if(wg){
    if(m.diff === '上級') return null;
    if(answers.gear === 'entry' && m.diff === '中〜上級') return null;
  }
  if(answers.who === 'family' && m.diff !== '初級' && m.diff !== '初〜中級') return null;
  // 行けるか（季節運行・冬期閉鎖）
  var acc = (m.acc || {})[mo] || {};
  var st = answers.transport === 'train' ? acc.train : acc.car;
  if(answers.transport === 'train' && !m.train) return null;
  if(st === 'no') return null;
  // ノーマルタイヤ：駐車場の標高が月ごとの目安より低い山だけ（気象庁の平年値の積雪日数から。1・2月500m・12・3月800m・11月1,200m未満。
  // scripts/build_winter_road.py。標高が分からない山は出さない）
  if(answers.transport === 'carnormal' && !(m.road && m.road.nt && m.road.nt[mo] === true)) return null;
  var route = pickRoute(m, wg);
  if(!route) return null;

  var score = 0, notes = [];
  if(st === 'part'){ score -= 10; }

  // 体力：歩く時間が合うほど高い（最大40）
  var fit = WALK_FIT[answers.fitness] || WALK_FIT.mid;
  if(route.min >= fit[0] && route.min <= fit[1]) score += 40;
  else if(route.min < fit[0]) score += Math.max(0, 40 - (fit[0] - route.min) / 6);
  // 難易度
  var dm = { low: { '初級': 30, '初〜中級': 14 }, mid: { '初〜中級': 30, '中級': 22, '初級': 12 }, high: { '中級': 30, '中〜上級': 22, '初〜中級': 18, '初級': 6 } };
  var ds = (dm[answers.fitness] || dm.mid)[m.diff];
  if(ds === undefined){
    if(!wg) return null;
    ds = 0;
  }
  score += ds;

  // 雪の好み：選んだ雪の段階の山を上げる
  // 雪山（入門・経験者）を選んだ人には冬山装備の山を、チェーンスパイクの人には軽アイゼン等の山を上にする
  if(answers.who !== 'family'){
    if(answers.gear === 'entry' || answers.gear === 'expert') score += [-30, 10, 45][rank];
    else if(answers.gear === 'light') score += [5, 25][rank];
  }

  // 冬山装備の山の重み付け（2026-11-17。運営者の指示「冬山装備の山を重み付けして、冬の絶景の5山以外も出したい」）
  if(wg){
    // 冬の絶景の記事の区分は、記事の山だけが上に来すぎないよう小さくする（2026-11-17 運営者の指示）
    if(m.view && m.view.cat === 'entry') score += 15;
    if(m.view && m.view.cat === 'expert' && answers.gear === 'expert') score += 5;
    if(m.lift) score += 15;
    var axe = (m.axe || {})[mo];
    if(axe !== '推奨') score += 10;
    if(m.diff === '初級' || m.diff === '初〜中級') score += 15;
    if(m.diff === '中〜上級') score -= 15;
    if(route.chain) score -= 15;
    if((m.ele || 0) >= 2800) score -= 10;
    if(!m.winterOk) score -= 10;
  }

  // 誰と
  if(answers.who === 'family'){
    if(hasTag(m, 'easy') || hasTag(m, 'casual')) score += 10;
  } else if(answers.who === 'solo'){
    if(hasTag(m, 'quiet')) score -= 10;
    if(hasTag(m, 'casual') || hasTag(m, 'accessible')) score += 8;
  } else if(answers.who === 'friends'){
    if(hasTag(m, 'casual')) score += 10;
  }

  // 見たいもの
  var dia = (m.dia || {})[mo];
  if(answers.see === 'fuji'){
    score += m.fuji ? 30 : -10;
  } else if(answers.see === 'ice'){
    // 雪景色：その月の雪の段階で全部の山を同じ基準で見る。霧氷・樹氷が書いてある山（記事・特徴の文・紹介文）は少し足す
    score += [-10, 15, 25][rank];
    if(m.view || m.iceText || ICE_RE.test(fpText(m))) score += 10;
  } else if(answers.see === 'pano'){
    // 大展望：ホームの絞り込みの「絶景」と同じ山（360度・大パノラマなどが出典に書いてある山）
    score += m.pano ? 30 : -10;
  } else if(answers.see === 'easy'){
    if(hasTag(m, 'accessible') || hasTag(m, 'easy') || hasTag(m, 'casual')) score += 20;
    if(m.lift) score += 8;
    score += Math.max(0, (240 - route.min) / 12);
  }

  // 下山後
  if(answers.after === 'onsen'){
    // 記事の山か、特徴の文・紹介文に書いてある山かで差を付けない
    if(m.onsen || m.sauna || m.onsenText || m.onsenNear) score += 25;
  } else if(answers.after === 'food'){
    if(m.food) score += 20;
  } else if(answers.after === 'shrine'){
    score += hasTag(m, 'historic') ? 25 : -5;
  }

  // 移動時間
  var limit = { near: 120, middle: 180 }[answers.time] || 999;
  var tm = travelMin(m);
  if(tm === null){
    if(answers.transport === 'train'){
      var d0 = m.dt ? m.dt[answers.depart || 'ofuna'] : null;
      if(!d0) return null;
      tm = Math.round(d0 * 1.4);
    } else {
      return null;
    }
  }
  var lim = answers.transport === 'train' && limit < 999 ? limit + 30 : limit;
  if(tm > lim) return null;
  score += Math.max(0, 210 - tm) / 10.5;

  return { m: m, score: score, route: route, gear: g, acc: acc, st: st, dia: dia, wg: wg };
}

// 冬の歩き始めの目安：15:30 に下山を終えるとして、歩く時間と休憩・遅れの余裕（1時間。2026-11-18）を引き、10分単位で切り下げ
function startBy(min){
  var t = 15 * 60 + 30 - min - 60;
  t = Math.floor(t / 10) * 10;
  var h = Math.floor(t / 60), mi = t % 60;
  return h + ':' + (mi < 10 ? '0' : '') + mi;
}
function fmtMin(v){
  var h = Math.floor(v / 60), mi = v % 60;
  if(!h) return mi + '分';
  return mi ? h + '時間' + mi + '分' : h + '時間';
}

function buildReasons(x){
  var m = x.m, out = [];
  if(x.dia){
    out.push({ l: 'ダイヤモンド富士', t: x.dia.join('／') + '（計算の目安。天気・見る場所で変わります）' });
  }
  if(m.view && (answers.see === 'ice' || x.wg)){
    var vcat = { sight: '樹氷を見る山（登山なし）', entry: '雪山入門の候補', expert: '冬山の経験者向け' }[m.view.cat] || '';
    out.push({ l: m.view.what, t: '「冬の絶景が見られる山6選」で' + vcat + 'として紹介した山です' + (m.view.season && m.view.season !== '冬' ? '（見ごろ：' + m.view.season + '）' : '') });
  }
  if(answers.after === 'onsen' && (m.onsen || m.sauna)){
    var fac = (m.onsen || []).concat(m.sauna || []);
    out.push({ l: '下山後に寄れる温泉・サウナ', t: fac.slice(0, 3).join('・') + '（温泉・サウナの記事で紹介）' });
  } else if(answers.after === 'onsen' && typeof m.onsenNear === 'string'){
    out.push({ l: '近くの温泉・サウナ', t: m.onsenNear + 'など（地図のデータからの目安。冬の営業日・時間は公式で確かめてください）' });
  }
  var want = { fuji: ['view'], ice: ['alpine', 'view'], pano: ['view'], easy: ['easy', 'casual'] }[answers.see] || [];
  var add = { food: ['casual', 'hut'], shrine: ['historic'] }[answers.after] || [];
  want = want.concat(add);
  var pts = (m.fp || []).map(function(p, i){
    var hit = want.indexOf(p.t) > -1 ? 1 : 0;
    if(answers.see === 'fuji' && /富士山/.test((p.l || '') + (p.x || ''))) hit = 2;
    if(answers.see === 'ice' && ICE_RE.test((p.l || '') + (p.x || ''))) hit = 2;
    if(answers.after === 'onsen' && /温泉|サウナ/.test((p.l || '') + (p.x || ''))) hit = 2;
    return { p: p, i: i, hit: hit };
  });
  pts.sort(function(a, b){ return (b.hit - a.hit) || (a.i - b.i); });
  var seen = out.map(function(o){ return o.l; });
  pts.forEach(function(c){ if(out.length < 3 && seen.indexOf(c.p.l) === -1){ seen.push(c.p.l); out.push({ l: c.p.l, t: c.p.x }); } });
  return out;
}

function cardHtml(x, i){
  var m = x.m;
  var rankClass = ['r1','r2','r3'][i];
  var h = '<div class="rc result-card">';
  h += '<div class="rc-top"><div class="rc-rank ' + rankClass + '">' + (i + 1) + '</div>';
  h += '<div><div class="rc-name">' + esc(m.name) + '</div><div class="rc-area">' + esc(m.area) + ' ' + (m.ele || '').toLocaleString() + 'm</div></div></div>';
  h += '<div class="rc-badges">';
  h += '<span class="rb rb-diff">' + esc(m.diff || '') + '</span>';
  h += '<span class="rb rb-gear">' + MONTH_LABEL[answers.when] + '：' + esc(GEAR_SHORT[x.gear.worst]) + '</span>';
  if(answers.transport === 'train') h += '<span class="rb rb-train">電車・バスOK</span>';
  var tm = travelMin(m);
  if(answers.transport !== 'train' && tm) h += '<span class="rb rb-drive">' + ic('car') + tm + '分</span>';
  if(x.dia) h += '<span class="rb rb-dia">ダイヤモンド富士</span>';
  if(m.cat === '百名山') h += '<span class="rb rb-100">百名山</span>';
  if(x.wg && !m.winterOk) h += '<span class="rb rb-warn">冬の登山口は未確認</span>';
  h += '</div>';
  // コース
  h += '<div class="rc-course">' + ic('route') + '<b>コース：</b>' + esc(x.route.n) + '（歩く時間 ' + fmtMin(x.route.min) + '）<br>';
  h += ic('timer') + '<b>冬の歩き始めの目安：</b>' + startBy(x.route.min) + 'まで（15:30に下山を終えるとして。休憩と遅れの余裕を1時間みた目安）<br>';
  h += ic('snowflake') + esc(gearText(x.gear)) + '</div>';
  // 理由
  var rs = buildReasons(x);
  if(rs.length){
    h += '<div class="rc-reason"><div class="rc-reason-title">この山をおすすめする理由</div><div class="rc-reason-text">';
    rs.forEach(function(r){ h += '<div class="rc-reason-item">' + (r.l ? '<strong>' + esc(r.l) + '</strong>' : '') + '<span>' + esc(r.t) + '</span></div>'; });
    h += '</div></div>';
  }
  // 注意
  var notes = [];
  if(x.st === 'part' && x.acc.why && x.acc.why.length){
    notes.push(MONTH_LABEL[answers.when] + 'は一部の日だけ行けます：' + x.acc.why.join('、'));
  }
  if(answers.transport === 'carnormal'){
    var lim = { '11': '1,200', '12': '800', '1': '500', '2': '500', '3': '800' }[answers.when];
    notes.push('駐車場の標高は約' + (m.road && m.road.e !== null ? Number(m.road.e).toLocaleString() + 'm' : '（不明・山頂より低い）') + '。' + MONTH_LABEL[answers.when] + 'に雪が積もる日が少ない標高（' + lim + 'm未満）の目安でノーマルタイヤでも出しています。雪が降った翌日や冷え込んだ朝は道が凍ることがあるので、出発前に道路の情報を確かめてください。');
    if(m.road && m.road.note) notes.push(m.road.note);
  }
  if(x.wg){
    notes.push('コースの時間・難易度は雪の無い時期の値です。冬はラッセルや凍結で長くかかります。');
    if(m.winterOk) notes.push('冬の行き方：' + m.winterOk);
    else notes.push('冬に登山口まで道路・バスで行けるかは、Yamatch では確かめられていません。出発前に自治体・観光協会の案内で確かめてください。');
  }
  if(notes.length){
    h += '<div class="rc-note">' + ic('triangle-alert') + '<b>冬の注意</b><ul>';
    notes.forEach(function(n){ h += '<li>' + esc(n) + '</li>'; });
    h += '</ul></div>';
  }
  var accQ = '?access=' + (answers.transport !== 'train' ? 'car' : 'train');
  h += '<a class="rc-cta" href="/mountains/' + esc(m.id) + '/' + accQ + '">詳しく見る →</a>';
  h += '<a class="rc-sub" href="/packing/?m=' + esc(m.id) + '&amp;s=day">この山の冬の持ち物リストを作る →</a>';
  h += '</div>';
  return h;
}

function pickTop3(list){
  if(list.length <= 3) return list;
  var top1 = list[0], best = top1.score;
  var pool = list.slice(1).filter(function(x){ return x.score >= best - 30; });
  if(pool.length < 4) pool = list.slice(1).filter(function(x){ return x.score >= best - 45; });
  if(pool.length < 2) pool = list.slice(1, 3);
  var arr = pool.slice();
  for(var i = arr.length - 1; i > 0; i--){
    var j = Math.floor(Math.random() * (i + 1)); var t = arr[i]; arr[i] = arr[j]; arr[j] = t;
  }
  var picks = arr.slice(0, 2);
  picks.sort(function(a, b){ return b.score - a.score; });
  return [top1].concat(picks);
}

function showResult(){
  var ov = document.getElementById('find-loading');
  if(ov){ ov.classList.add('active'); document.body.style.overflow = 'hidden'; }
  setTimeout(_doShowResult, 1100);
}
function _doShowResult(){
  var ov = document.getElementById('find-loading');
  if(ov){ ov.classList.remove('active'); document.body.style.overflow = ''; }
  var scored = [];
  mountainsData.forEach(function(m){ var x = scoreMount(m); if(x && x.score > 0) scored.push(x); });
  scored.sort(function(a, b){ return b.score - a.score; });
  var dep = answers.depart || 'ofuna';
  var depLabel = dep === 'shinjuku' ? '新宿・都内' : dep === 'omiya' ? '大宮・埼玉' : '横浜・大船';
  var gearLabel = { none: '雪の無い', light: 'チェーンスパイクで行ける', entry: '雪山入門の', expert: '雪山の' }[answers.gear] || '';
  if(answers.who === 'family') gearLabel = '雪の無い';
  document.getElementById('result-headline').textContent = MONTH_LABEL[answers.when] + '・' + depLabel + '発・' + gearLabel + '日帰りの山';
  document.getElementById('result-count').textContent = scored.length ? '条件に合う山：' + scored.length + '件中、上位3件を表示' : '';
  var top3 = pickTop3(scored);
  if(!top3.length){
    document.getElementById('result-cards').innerHTML = '<div class="empty-result"><div class="empty-result-text">条件に合う山が見つかりませんでした。<br>移動時間や雪の段階を変えてお試しください。</div></div>';
    document.getElementById('result-headline').textContent = '条件に合う山が見つかりませんでした';
    document.getElementById('more-list').innerHTML = '';
    if(typeof gtag === 'function') gtag('event', 'diagnosis_complete', { diagnosis_type: 'find_winter', top_mountain_id: 'none' });
  } else {
    document.getElementById('result-cards').innerHTML = top3.map(cardHtml).join('');
    var used = top3.map(function(x){ return x.m.id; });
    var more = scored.filter(function(x){ return used.indexOf(x.m.id) === -1; }).slice(0, 6);
    var mh = '';
    if(more.length){
      mh = '<div class="more-list"><div class="more-title">ほかの候補</div>';
      more.forEach(function(x){
        mh += '<a href="/mountains/' + esc(x.m.id) + '/?access=' + (answers.transport !== 'train' ? 'car' : 'train') + '">' + esc(x.m.name) + '<span>' + esc(x.m.diff || '') + '・' + GEAR_SHORT[x.gear.worst] + '・歩く' + fmtMin(x.route.min) + '</span></a>';
      });
      mh += '</div>';
    }
    document.getElementById('more-list').innerHTML = mh;
    if(typeof gtag === 'function') gtag('event', 'diagnosis_complete', { diagnosis_type: 'find_winter', top_mountain_id: top3[0].m.id });
  }
  show('step-result');
  fwGuideTab(0);
  document.getElementById('fw-guide-note').textContent = fwGuideNote();
  document.getElementById('gear-section').innerHTML = buildGearSection();
  document.getElementById('tips-section').innerHTML = buildTipsSection();
  window.scrollTo(0, 0);
}

// ===== はじめて登山をする人へ（2026-11-23。運営者の絵）=====
function fwGuideTab(n){
  [0, 1].forEach(function(i){
    document.getElementById('fw-tab-' + i).setAttribute('aria-selected', i === n ? 'true' : 'false');
    document.getElementById('fw-panel-' + i).hidden = i !== n;
  });
}
function fwGuideOpen(name){
  if(typeof gtag === 'function') gtag('event', 'winter_guide_open', { guide: name });
}
// 絵は雪の無い低山の目安なので、選んだ雪の段階に合わせて足元の注意を添える
function fwGuideNote(){
  if(answers.who !== 'family' && (answers.gear === 'entry' || answers.gear === 'expert')){
    return '雪山はスポーツシューズでは登れません。絵の服装は低山の目安で、雪山はさらに防寒と冬靴・アイゼンが要ります。登山がはじめての人は、まず雪の無い山か、ガイド付きのツアーがおすすめです。';
  }
  if(answers.who !== 'family' && answers.gear === 'light'){
    return '雪や凍結のある道は、スポーツシューズではなく、登山靴にチェーンスパイクや軽アイゼンを付けて歩きます。';
  }
  return '冬は日陰の道が凍ることがあるので、足元は登山靴が安心です。雪が降ったあとは、出かける前に山の状況を確かめてください。';
}

// ===== 冬の持ち物・注意 =====
function item(icon, name, note, must){ return { icon: icon, name: name, note: note, must: must }; }
function buildGearSection(){
  var g = [];
  g.push({ title: '冬はかならず持っていくもの', items: [
    item('shirt', '防寒着（フリース・薄手のダウンなど）', '休憩や山頂で体が冷えるので、歩くとき脱いだ分を着られるように。綿の服は汗で冷えるので避ける', true),
    item('backpack', '手袋・帽子・ネックウォーマー', '指先・耳から冷える。手袋は濡れたときの替えもあると安心', true),
    item('flame', '温かい飲み物（保温ボトル）', '冬は冷たい水が飲みにくく、水分が足りなくなりやすい', true),
    item('lightbulb', 'ヘッドライト', '冬は日が短い。予定より遅れても暗くなる前に下りられるとは限らない', true),
    item('smartphone', 'スマホと予備の電池', '寒さで電池の減りが早い。地図アプリは電波が無くても使えるように', true)
  ] });
  var snow = [];
  if(answers.gear === 'light' || answers.gear === 'entry' || answers.gear === 'expert'){
    snow.push(item('footprints', 'チェーンスパイク・軽アイゼン', '凍った道・踏み固められた雪の道で滑らないように。出発前に靴に合うか試しておく', true));
  }
  if(answers.gear === 'entry' || answers.gear === 'expert'){
    snow.push(item('pickaxe', '12本爪アイゼン・ピッケル・冬用の登山靴', '冬山装備が要る山の基本の装備。使い方に慣れてから', true));
    snow.push(item('wind', 'ゴーグル・目出し帽', '稜線の強い風と雪から顔を守る', false));
  }
  if(snow.length) g.push({ title: '雪・凍結に備えるもの', items: snow });
  if(answers.transport === 'car') g.push({ title: '車で行く人', items: [ item('car', '冬用タイヤ・タイヤチェーン', '山の道路は朝晩に凍る。駐車場が雪で使えないこともある', true) ] });
  if(answers.transport === 'carnormal') g.push({ title: 'ノーマルタイヤで行く人', items: [ item('car', '出発前に道路の情報と天気を確かめる', '雪が降った翌日や冷え込んだ朝は、低い山の道でも凍ることがある。雪の予報が出たら行き先を変えるか、電車・バスで', true) ] });
  var html = '<button class="info-toggle" onclick="toggleInfo(this)"><span><span class="info-toggle-icon">' + ic('backpack') + '</span>冬の持ち物チェックリスト</span><span class="info-toggle-arrow">›</span></button><div class="info-body">';
  g.forEach(function(gr){
    html += '<div class="gear-group"><div class="gear-group-title">' + gr.title + '</div><div class="gear-items">';
    gr.items.forEach(function(it){
      html += '<div class="gear-item-row"><div class="gear-item-emoji">' + ic(it.icon) + '</div><div class="gear-item-body"><div class="gear-item-name">' + it.name;
      html += it.must ? '<span class="gear-tag gear-tag-must">必須</span>' : '<span class="gear-tag gear-tag-easy">あると安心</span>';
      html += '</div><div class="gear-item-note">' + it.note + '</div></div></div>';
    });
    html += '</div></div>';
  });
  html += '<div style="margin-top:12px;font-size:12px;"><a href="/packing/" style="color:#4e6535;font-weight:700;">持ち物チェックリスト（日帰り・山小屋泊・テント泊）を開く →</a></div></div>';
  return html;
}
function buildTipsSection(){
  var tips = [
    ['timer', '15時30分には下山を終える計画に', '冬は日の入りが早い（12月上旬の東京で16時28分。国立天文台）。山の中は日が陰るともっと早く暗くなる', true],
    ['triangle-alert', '下りの凍結に気をつける', '朝は凍っていて、昼に溶けてぬかるみ、夕方にまた凍る。登りで平気でも下りで滑りやすい', true],
    ['wind', '休憩は短く、着るものでこまめに調整', '汗で濡れると一気に冷える。登りは薄着で、止まったらすぐに羽織る', false],
    ['clipboard-list', '登山計画書を出す・行き先を伝える', '冬は人が少なく、何かあったときに見つけてもらいにくい', false]
  ];
  if(answers.transport === 'train') tips.push(['train-front', '帰りのバスの最終を確かめる', '冬はダイヤが変わり、本数が減るバスがある', true]);
  if(answers.gear === 'entry' || answers.gear === 'expert') tips.push(['mountain-snow', '雪崩・天気の急変に備える', '冬山は天気が崩れると引き返す判断が大事。初めての山は経験者と一緒に', true]);
  var html = '<button class="info-toggle" onclick="toggleInfo(this)"><span><span class="info-toggle-icon">' + ic('triangle-alert') + '</span>冬の山で気をつけること</span><span class="info-toggle-arrow">›</span></button><div class="info-body"><div class="tip-list">';
  tips.forEach(function(t){
    html += '<div class="tip-item' + (t[3] ? ' warn' : '') + '"><div class="tip-item-icon">' + ic(t[0]) + '</div><div class="tip-item-body"><div class="tip-item-title">' + t[1] + '</div><div class="tip-item-text">' + t[2] + '</div></div></div>';
  });
  html += '</div></div>';
  return html;
}
function toggleInfo(btn){ btn.classList.toggle('open'); btn.nextElementSibling.classList.toggle('open'); }
function resetQuiz(){ answers = {}; currentQ = 0; show('step-intro'); window.scrollTo(0, 0); }
function show(id){
  document.querySelectorAll('.step').forEach(function(el){ el.classList.remove('active'); });
  document.getElementById(id).classList.add('active');
}
function esc(s){
  if(s === null || s === undefined) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
<script defer src="/assets/js/to-top.js?v=20261025a"></script>
</body>
</html>
"""


def main():
    html = page()
    if '--check' in sys.argv:
        cur = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if cur != html:
            print('find/winter/index.html が古い：python3 scripts/gen_find_winter.py を流す')
            sys.exit(1)
        print('find/winter/index.html は最新')
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(html)
    print('書いた：find/winter/index.html')


if __name__ == '__main__':
    main()
