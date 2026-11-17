"""季節ダイヤ（夏ダイヤ・冬ダイヤ。transitSeasons）を、冬にも運行のある山に入れる（2026-11-17。運営者の指示
「冬ダイヤがある山は夏の期間が終了したら冬ダイヤの表示に切り替わる様に。夏ダイヤ終了後・冬ダイヤ開始前は冬ダイヤは何日からかの表示に。
リンクも冬ダイヤの案内や時刻表に」）。入笠山は fix_nyukasa_winter_access_2026_11.py。

公式で確かめた冬の運行（2026-11-17）：
- 赤城山：関越交通 前橋駅〜赤城山（富士見温泉線・前橋赤城山線・富士見赤城山線）。冬季 12/1〜3/31（2026年12月1日改正）。
  急行バス（直通）は土日祝だけ、平日は富士見温泉で乗り換え（山頂方面へ1日4本）。http://kan-etsu.net/pages/42/ ・ /pages/24/
- 西吾妻山：天元台高原 2026-27年の冬 11/28〜2027/5/5。ロープウェイ 8:00〜17:00（平日8:20〜）、リフト 8:10〜16:00（平日8:30〜）・
  北望台への最終15:00。12/9・1/6・2/3・3/10・4/14 は点検で運休。https://www.winter.tengendai.jp/
- 谷川岳：谷川岳ヨッホ ウィンターシーズン 2026/12/5〜2027/4/4、ロープウェイ 8:30〜16:30（上りの最終16:00）。https://tanigawadake-joch.com/
  関越交通 水上線は冬季 11/16〜4/4（2026年11月16日改正）。上毛高原駅7:58発の急行便は 12/5〜4/4 の運行日だけ（2,000円）。
  http://kan-etsu.net/pages/20/
入れなかった山（冬の運行の日付が公式に出ていない）：那須岳（大丸温泉〜那須ロープウェイのバスは冬季運休、ロープウェイは12/13まで）・
唐松岳（八方は12/1から営業予定。登山者の冬のゴンドラの案内なし）・五竜岳（テレキャビンの冬は例年12月中旬から）・
日光白根山（丸沼高原は12/4オープン予定。冬のロープウェイの運行開始日の記載なし）
何度流しても同じ結果。このあと build_derived.py → build_access_tier.py --write → gen_mountain_pages.py --id … → check_pages.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

DAY = '2026-11-17'
KE42 = 'http://kan-etsu.net/pages/42/'

SEASONS = {
    'akagi': [
        {'key': 'summer', 'label': '夏ダイヤ', 'from': '2026-04-01', 'to': '2026-11-30',
         'lines': ['前橋駅から赤城山（あかぎ広場前・スノーピークLS赤城）への直通バスは土日祝だけ',
                   '平日は富士見温泉で乗り換え'],
         'links': [{'label': '夏ダイヤの時刻表（9/19〜11/30）', 'url': 'https://kan-etsu.net/files/libs/14532/202608311118548109.pdf'},
                   {'label': '関越交通 赤城山へのバス', 'url': KE42}],
         'timetable': {'label': '赤城山へのバス 夏ダイヤの時刻表', 'url': 'https://kan-etsu.net/files/libs/14532/202608311118548109.pdf'},
         'lastVerified': DAY},
        {'key': 'winter', 'label': '冬ダイヤ', 'from': '2026-12-01', 'to': '2027-03-31',
         'lines': ['前橋駅から赤城山への急行バス（直通）は土日祝だけ',
                   '平日は富士見温泉で乗り換え（富士見温泉から山頂方面は1日4本）'],
         'links': [{'label': '冬ダイヤの時刻表（土日祝）', 'url': 'https://kan-etsu.net/files/libs/14686/202611131729401095.pdf'},
                   {'label': '冬ダイヤの時刻表（平日）', 'url': 'https://kan-etsu.net/files/libs/14685/202611131729328577.pdf'},
                   {'label': '関越交通 赤城山へのバス', 'url': KE42}],
         'timetable': {'label': '赤城山へのバス 冬ダイヤの時刻表（土日祝）', 'url': 'https://kan-etsu.net/files/libs/14686/202611131729401095.pdf'},
         'lastVerified': DAY},
    ],
    'azuma': [
        {'key': 'summer', 'label': 'グリーンシーズン', 'from': '2026-06-13', 'to': '2026-11-03',
         'lines': ['天元台ロープウェイ：6月13日〜11月3日',
                   '北望台までの夏山リフト：6月13日〜10月25日（運休日あり）'],
         'links': [{'label': '天元台高原 グリーンシーズン', 'url': 'https://www.green.tengendai.jp/'}],
         'lastVerified': DAY},
        {'key': 'winter', 'label': 'ウィンターシーズン', 'from': '2026-11-28', 'to': '2027-05-05',
         'lines': ['ロープウェイ：8:00〜17:00（平日は8:20から）',
                   'リフト：8:10〜16:00（平日は8:30から）。北望台へ上がる最終は15:00',
                   '12/9・1/6・2/3・3/10・4/14 は点検でロープウェイ・リフトとも運休'],
         'links': [{'label': '天元台高原 ウィンターシーズン', 'url': 'https://www.winter.tengendai.jp/'},
                   {'label': '冬のトレッキング', 'url': 'https://www.winter.tengendai.jp/トレッキング'}],
         'lastVerified': DAY},
    ],
    'tanigawa': [
        {'key': 'summer', 'label': 'グリーンシーズン', 'from': '2026-04-18', 'to': '2026-11-15',
         'lines': ['谷川岳ヨッホ（ロープウェイ）：4月18日〜11月15日',
                   '上毛高原駅・水上駅からのバス（関越交通 水上線）：夏の時刻（2026年4月1日改正）'],
         'links': [{'label': '谷川岳ヨッホ', 'url': 'https://tanigawadake-joch.com/'},
                   {'label': '水上線 谷川岳ヨッホ方面の時刻表（4/1改正）', 'url': 'https://kan-etsu.net/files/libs/14053/202603051656145737.pdf'}],
         'timetable': {'label': '水上線 谷川岳ヨッホ方面の時刻表（夏）', 'url': 'https://kan-etsu.net/files/libs/14053/202603051656145737.pdf'},
         'lastVerified': DAY},
        {'key': 'winter', 'label': 'ウィンターシーズン', 'from': '2026-12-05', 'to': '2027-04-04',
         'lines': ['谷川岳ヨッホ（ロープウェイ）：8:30〜16:30（上りの最終16:00）',
                   'バス（関越交通 水上線）は11月16日から冬の時刻（4月4日まで）',
                   '上毛高原駅7:58発の急行便は12月5日〜4月4日の運行日だけ（大人2,000円）'],
         'links': [{'label': '谷川岳ヨッホ', 'url': 'https://tanigawadake-joch.com/'},
                   {'label': '水上線 谷川岳ヨッホ方面の時刻表（冬）', 'url': 'https://kan-etsu.net/files/libs/14622/202610271608236341.pdf'},
                   {'label': '水上線 上毛高原駅方面の時刻表（冬）', 'url': 'https://kan-etsu.net/files/libs/14623/202610271608272093.pdf'}],
         'timetable': {'label': '水上線 谷川岳ヨッホ方面の時刻表（冬）', 'url': 'https://kan-etsu.net/files/libs/14622/202610271608236341.pdf'},
         'lastVerified': DAY},
    ],
}
# 期限の見張り（check_annual_updates.py）のための冬の項目
ANNUAL = {
    'akagi': [{'kind': 'transport', 'label': '前橋駅〜赤城山のバス（冬ダイヤ）', 'validFrom': '2026-12-01', 'validTo': '2027-03-31',
               'seasonYear': '2026〜27', 'sourceUrl': 'http://kan-etsu.net/pages/24/', 'lastVerified': DAY,
               'note': '急行バス（直通）は土日祝だけ、平日は富士見温泉で乗り換え'}],
    'azuma': [{'kind': 'transport', 'label': '天元台ロープウェイ・リフト（ウィンターシーズン）', 'validFrom': '2026-11-28', 'validTo': '2027-05-05',
               'seasonYear': '2026〜27', 'sourceUrl': 'https://www.winter.tengendai.jp/', 'lastVerified': DAY,
               'note': 'ロープウェイ8:00〜17:00（平日8:20〜）、北望台へのリフトの最終15:00'}],
    'tanigawa': [{'kind': 'transport', 'label': '谷川岳ヨッホ（ウィンターシーズン）', 'validFrom': '2026-12-05', 'validTo': '2027-04-04',
                  'seasonYear': '2026〜27', 'sourceUrl': 'https://tanigawadake-joch.com/', 'lastVerified': DAY,
                  'note': 'ロープウェイ8:30〜16:30（上りの最終16:00）'}],
}
# 季節運行の名前（冬の山選び診断の「一部の日だけ行けます」などに出る。transitSeasonsName）
NAME = {'azuma': '天元台ロープウェイ・リフト', 'tanigawa': '谷川岳ヨッホ（ロープウェイ）'}
NOTE = {
    'akagi': '直通バスは土日祝だけ（平日は富士見温泉で乗り換え）。あかぎ大沼白樺マラソン・まえばし赤城山ヒルクライムの日は、午前中に山頂へ行けない',
    'azuma': '',
}

path = os.path.join(ROOT, 'data', 'mountains.json')
M = json.load(open(path, encoding='utf-8'))
for mid, ss in SEASONS.items():
    m = next(x for x in M if x['id'] == mid)
    m['transitSeasons'] = ss
    if mid in NAME:
        m['transitSeasonsName'] = NAME[mid]
    labels = {a['label'] for a in ANNUAL[mid]}
    m['annualItems'] = [a for a in m.get('annualItems') or [] if a.get('label') not in labels] + [dict(a) for a in ANNUAL[mid]]
    if mid in NOTE and m.get('dataModel') != 'ssot-v1':
        m['trainRoutes']['note'] = NOTE[mid]
        m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = DAY
json.dump(M, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', list(SEASONS))
