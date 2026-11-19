# -*- coding: utf-8 -*-
"""冬に使えないコースの印の試作：金峰山（2026-11-19。運営者の指示「特定のコースが冬に利用不可能だったり、そこまでの道のりが冬季に
通行止めのコースは分かる様にしたい」→「1つ山を決めて試作品をつくって見せて」）

routes[].winter（gen_mountain_pages.py の winter_tag・winter_line。コースの欄とコースを比べる表に出す）
- 大弛峠からの往復：山梨県の林道情報（林道川上牧丘線 柳平ゲート〜大弛峠 R8.12.1〜R9.5.31 予定。凍結と落石のため）。
  塩山駅からの予約制バス（栄和交通）も2026年は11月8日まで（accesses.json の odarumi）
- 瑞牆山荘からの往復：韮崎駅からの路線バス（韮崎瑞牆線）は2026年は4月4日〜11月23日（瑞牆山の annualItems）。
  冬も車では行ける（瑞牆山荘の現地情報：冬は「車は冬タイヤ必須」「四駆で冬タイヤ推奨」。山と溪谷オンラインの過去ログ id=1015）
- 廻り目平からの往復：長野県川上村側の道の冬の通行を、公式の案内で確かめられていない
何度流しても同じ結果。このあと gen_mountain_pages.py --id kinpusan
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
DAY = '2026-11-19'
WINTER = {
    'odarumi-roundtrip': {
        'state': 'closed', 'label': '冬は通行止め', 'from': '12-01', 'to': '05-31',
        'text': '山梨県が大弛峠への林道（川上牧丘線の柳平ゲート〜大弛峠）を凍結と落石のため通行止めにする予定で、車でも登山口へ行けません。'
                '塩山駅からの予約制バスも2026年は11月8日で終わりました',
        'sources': [
            {'label': '山梨県 林道の通行規制', 'url': 'https://www.pref.yamanashi.jp/rindoujyouhou/kisei.php?id=61'},
        ],
        'lastVerified': DAY,
    },
    'mawarimedaira-roundtrip': {
        'state': 'unknown', 'label': '冬の道路は未確認',
        'text': '長野県川上村の廻り目平へ行く道が冬に通れるかは、公式の案内で確かめられていません。出かける前に川上村・金峰山荘に確かめてください',
        'lastVerified': DAY,
    },
    'mizugaki-sanso-roundtrip': {
        'state': 'car_only', 'label': '冬は車だけ', 'from': '11-24', 'to': '04-03',
        'text': '韮崎駅からの路線バス（韮崎瑞牆線）は2026年は11月23日までで、冬は電車・バスでは行けません。'
                '車では行けますが、瑞牆山荘は冬は冬用タイヤが要ると案内しています',
        'sources': [
            {'label': '韮崎瑞牆線の時刻表', 'url': 'http://cus4.kyohoku.jp/routebus/kayagatakemizugakidenen-bus/schedule-mizugakiline/'},
            {'label': '瑞牆山荘の現地情報', 'url': 'https://www.yamakei-online.com/mt_info/past.php?id=1015&yy=2024'},
        ],
        'lastVerified': DAY,
    },
}
raw = open(P, encoding='utf-8').read()
M = json.loads(raw)
m = next(x for x in M if x['id'] == 'kinpusan')
ids = {r['id'] for r in m['routes']}
assert set(WINTER) <= ids, ids
changed = False
for r in m['routes']:
    w = WINTER.get(r['id'])
    if w and r.get('winter') != w:
        r['winter'] = w
        changed = True
if changed:
    m['mountainUpdated'] = max(m.get('mountainUpdated') or '', DAY)
open(P, 'w', encoding='utf-8').write(json.dumps(M, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
print('ok', changed)
