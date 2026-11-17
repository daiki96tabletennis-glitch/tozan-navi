"""入笠山の冬の運行（ゴンドラ・富士見駅からの無料送迎バス）を入れる（2026-11-17。運営者の指示「入笠山はバスもゴンドラも冬もやっているはず。記載が間違っている」）

前は夏（グリーンシーズン）の運行期間しか持っておらず、注記・よくある質問に「ゴンドラは2026年は4月25日〜11月15日」とだけ出ていた。
公式（富士見パノラマリゾート）で確かめた冬の運行：
- 営業期間 2026年12月12日（土）〜2027年4月4日（日）。ゴンドラ 8:30〜16:00（下り最終16:30）
  https://www.fujimipanorama.com/snow/ticket/
- 冬山登山のゴンドラ 大人往復2,400円。ゴンドラ山頂駅から入笠山の山頂までスノーシューで往復約3時間（スノートレッキング）
  https://www.fujimipanorama.com/snow/trekking/
- 無料送迎バス：冬季オープン中毎日運行・予約不要。富士見駅 9:15発・10:00発、帰りは 15:00発・17:00発
  https://www.fujimipanorama.com/snow/access/
何度流しても同じ結果。このあと build_access_tier.py --write → gen_mountain_pages.py --id nyukasayama → gen_winter_specials.py → check_pages.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

DAY = '2026-11-17'
WINTER = [
    {'kind': 'transport', 'label': '富士見パノラマリゾートのゴンドラ（ウインターシーズン）', 'validFrom': '2026-12-12', 'validTo': '2027-04-04',
     'seasonYear': '2026〜27', 'sourceUrl': 'https://www.fujimipanorama.com/snow/ticket/', 'lastVerified': DAY,
     'note': '8時30分〜16時（下りの最終16時30分）。冬山登山は往復2,400円'},
    {'kind': 'transport', 'label': '富士見駅〜富士見パノラマリゾートの無料送迎バス（冬）', 'validFrom': '2026-12-12', 'validTo': '2027-04-04',
     'seasonYear': '2026〜27', 'sourceUrl': 'https://www.fujimipanorama.com/snow/access/', 'lastVerified': DAY,
     'note': '毎日運行・予約不要。富士見駅9時15分・10時発、帰りは15時・17時発'},
]
NOTE = ('無料シャトルバスは夏（2026年4/25〜11/24）は富士見駅10時発、冬（12/12〜2027年4/4）は9:15・10:00発。'
        'ゴンドラは夏（2026年4/25〜11/15）と冬（12/12〜2027年4/4）に運行')
SUMMARY = 'ゴンドラ代（片道2,000円。冬の登山は往復2,400円）は別'
FAQ_SEASON = ('入笠山のゴンドラは、春〜秋（2026年は4月25日〜11月15日）と冬（2026年12月12日〜2027年4月4日）に動きます。'
              '6月は入笠湿原のスズランが見ごろです。冬はゴンドラ山頂駅から山頂まで、スノーシューで往復約3時間のスノートレッキングが定番で、'
              '雪が積もるので滑り止めかスノーシューが要ります。11月中旬〜12月上旬はゴンドラが動きません。')

path = os.path.join(ROOT, 'data', 'mountains.json')
M = json.load(open(path, encoding='utf-8'))
m = next(x for x in M if x['id'] == 'nyukasayama')
labels = {w['label'] for w in WINTER}
m['annualItems'] = [a for a in m.get('annualItems') or [] if a.get('label') not in labels] + [dict(w) for w in WINTER]
tr = m['trainRoutes']
tr['note'] = NOTE
tr['summaryNote'] = SUMMARY
m['trainAccessHtml'] = render_ts_section(tr, m)
for f in m.get('faq') or []:
    q = f.get('question') or ''
    if 'シーズン' in q:
        f['answer'] = FAQ_SEASON
    if '帰りのゴンドラの最終便（4〜10月は下り16時30分）' in (f.get('answer') or ''):
        f['answer'] = f['answer'].replace('帰りのゴンドラの最終便（4〜10月は下り16時30分）', '帰りのゴンドラの最終便（下り16時30分。冬も同じ）')
m['mountainUpdated'] = DAY
json.dump(M, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

wp = os.path.join(ROOT, 'data', 'winter_specials.json')
raw = open(wp, encoding='utf-8').read()
W = json.loads(raw)
for it in W['views']['mountains']:
    if it['id'] == 'nyukasayama':
        it['winterAccess'] = ('冬はウインターシーズン（2026年12月12日〜2027年4月4日）のゴンドラで山頂エリアへ。ゴンドラは8:30〜16:00（下りの最終16:30）、'
                              '冬山登山は往復2,400円。富士見駅からの無料送迎バスも冬は毎日（9:15・10:00発、予約不要）')
        it['winterShort'] = 'ゴンドラ・無料送迎バス（冬は12/12〜4/4）'
        links = [l for l in it.get('winterLinks') or [] if 'snow/access' not in l['url']]
        links.append({'label': '富士見パノラマリゾート（冬のアクセス・送迎バス）', 'url': 'https://www.fujimipanorama.com/snow/access/'})
        it['winterLinks'] = links
open(wp, 'w', encoding='utf-8').write(json.dumps(W, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
print('ok', tr['note'])
