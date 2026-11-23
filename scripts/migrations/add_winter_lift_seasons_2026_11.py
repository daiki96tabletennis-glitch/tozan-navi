"""唐松岳・五竜岳に冬の営業（季節ダイヤ transitSeasons）を入れる（2026-11-23。運営者の指示「他の山でも類似事例があれば対応」「続けて」）

公式で確かめたこと（2026-11-23）：
- 白馬八方尾根：2026-27シーズンは11/21から。いま動くのはゴンドラ（8:00〜16:00・上りの最終14:00）・パノラマペア・国際第3ペアだけで、
  コースの歩き始めの八方池山荘へ上がるアルペンクワッド・グラートクワッドは動いていない（https://www.happo-one.jp/news/39854/）。
  料金表の期間は2027/5/5まで。アルペンラインの通し券は登山・バックカントリーのみ・片道大人4,200円、登山届が必要（https://www.happo-one.jp/ticket）
- エイブル白馬五竜：11/21からゴンドラ（テレキャビン）運行。11/23は8:30〜15:00・下りの最終16:00（https://www.hakubagoryu.jp/information/news/12199/）。
  運行は「例年12月中旬からゴールデンウィークまで（積雪状況による）」「シーズン終了（GWの予定）」で終了日の発表は無い（rangeText で「GW（予定）」と出す。
  日付の判定には、料金の案内に営業日として出てくる5/5を使う）。登山装備や滑走装備なしではリフトに乗れない
入れていない：日光白根山（丸沼高原は12/4オープン予定だが、冬のロープウェイの運行開始日の記載が無い）
何度流しても同じ結果。このあと build_derived.py → build_access_tier.py --write → build_winter_find.py → gen_find_winter.py → gen_mountain_pages.py --all → check_pages.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DAY = '2026-11-23'
H_STATUS = 'https://www.happo-one.jp/gelande/lift'
G_STATUS = 'https://www.hakubagoryu.jp/ski/gelande/lift-and-gondola-status/'
SEASONS = {
    'karamatsu': [
        {'key': 'summer', 'label': 'グリーンシーズン', 'from': '2026-06-06', 'to': '2026-11-03',
         'lines': ['八方アルペンライン（ゴンドラ＋リフト2本）で八方池山荘へ：6月6日〜11月3日'],
         'links': [{'label': '八方アルペンラインの案内', 'url': 'https://www.happo-one.jp/news/38573/'}], 'lastVerified': DAY},
        {'key': 'winter', 'label': 'スキーシーズン', 'from': '2026-11-21', 'to': '2027-05-05',
         'lines': ['ゴンドラは11月21日から。八方池山荘へ上がるアルペンクワッド・グラートクワッドは積雪しだいで、11月23日時点は動いていません',
                   'アルペンラインの通し券は登山・バックカントリー用で片道大人4,200円、登山届が必要',
                   '運行するリフトと時間は日で変わるので、当日の運行状況で確かめてください'],
         'links': [{'label': 'リフト運行状況', 'url': H_STATUS}, {'label': 'リフト料金', 'url': 'https://www.happo-one.jp/ticket'}],
         'lastVerified': DAY},
    ],
    'goryudake': [
        {'key': 'summer', 'label': 'グリーンシーズン', 'from': '2026-06-20', 'to': '2026-10-18',
         'lines': ['テレキャビンでアルプス平へ：6月20日〜10月18日（6/6・7・13・14は先行営業）'],
         'links': [{'label': 'ゴンドラ運行カレンダー・料金', 'url': 'https://www.hakubagoryu.jp/garden/gondolas-and-lifts/schedule-and-fares/'}],
         'lastVerified': DAY},
        {'key': 'winter', 'label': 'スキーシーズン', 'from': '2026-11-21', 'to': '2027-05-05',
         'rangeText': '2026年11月21日〜ゴールデンウィーク（予定・積雪による）',
         'lines': ['テレキャビンは11月21日から（11月23日は8:30〜15:00、下りの最終16:00）',
                   '登山装備や滑走装備なしではリフトに乗れません',
                   '運行するリフトと時間は日で変わるので、当日の運行状況で確かめてください'],
         'links': [{'label': 'リフト・ゴンドラ運行状況', 'url': G_STATUS},
                   {'label': 'リフト料金（観光・登山リフト券）', 'url': 'https://www.hakubagoryu.jp/ski/pricing/lift-tickets/'}],
         'lastVerified': DAY},
    ],
}
NAME = {'karamatsu': '八方アルペンライン', 'goryudake': '白馬五竜テレキャビン'}
SRC = {'karamatsu': 'https://www.happo-one.jp/news/39854/', 'goryudake': 'https://www.hakubagoryu.jp/information/news/12199/'}
LABEL = {'karamatsu': '八方尾根のゴンドラ・リフト（スキーシーズン）', 'goryudake': '五竜テレキャビン（スキーシーズン）'}

ap = os.path.join(ROOT, 'data', 'accesses.json')
araw = open(ap, encoding='utf-8').read()
A = json.loads(araw)
g = A['goryu-telecabin']
if g['trainRoutes'].get('note') == 'テレキャビンは6月上旬〜10月末':
    g['trainRoutes']['note'] = ''
for l in g['trainRoutes'].get('links') or []:
    if 'テレキャビン運行カレンダー' in (l.get('label') or '') or l.get('label') == 'テレキャビンの運行状況':
        l['label'] = 'テレキャビンの運行状況'
        l['url'] = G_STATUS
# 経路の札は夏の期間だけを書いていて、冬の営業中に「終わった」ように読めるので、期間は季節ダイヤの枠に任せる
A['happo']['trainRoutes']['badge']['label'] = '⚠️ ゴンドラ・リフトは季節営業（期間は上の案内）'
g['trainRoutes']['badge']['label'] = '⚠️ テレキャビンは季節営業（期間は上の案内）'
open(ap, 'w', encoding='utf-8').write(json.dumps(A, ensure_ascii=False, indent=2) + ('\n' if araw.endswith('\n') else ''))

mp = os.path.join(ROOT, 'data', 'mountains.json')
M = json.load(open(mp, encoding='utf-8'))
for mid, ss in SEASONS.items():
    m = next(x for x in M if x['id'] == mid)
    m['transitSeasons'] = ss
    m['transitSeasonsName'] = NAME[mid]
    item = {'kind': 'transport', 'label': LABEL[mid], 'validFrom': '2026-11-21', 'validTo': '2027-05-05', 'seasonYear': '2026〜27',
            'sourceUrl': SRC[mid], 'lastVerified': DAY, 'note': ss[1]['lines'][0]}
    m['annualItems'] = [a for a in m.get('annualItems') or [] if a.get('label') != item['label']] + [item]
    m['mountainUpdated'] = max(m.get('mountainUpdated') or '', DAY)
json.dump(M, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
