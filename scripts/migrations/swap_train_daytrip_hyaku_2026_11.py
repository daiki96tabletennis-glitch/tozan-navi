# -*- coding: utf-8 -*-
"""電車で行ける日帰り登山20選（/search/train-daytrip/）の「電車で行く百名山の日帰り」から、
立山・唐松岳を外して赤城山・天城山を入れる（2026-11-18。運営者の指示「他の山に入れ替えて」）。

理由：2026-11-18 に日帰りの決まりを変え（新宿からの電車・車の往復＋いちばん短いコースが14時間以内）、
立山（電車 4時間15分×2＋6時間23分）・唐松岳（電車 3時間55分×2＋6時間48分）が日帰り不可になった。
入れる山：日帰り可・電車とバスで通年行ける百名山。
- 赤城山：前橋駅から関越交通のバス（冬ダイヤ 12/1〜3/31。土日祝は直通の急行、平日は富士見温泉で乗り換え）。
  コースはバスの着くあかぎ広場前から歩く周回（routes の4本目）。
  帰りの最終：あかぎ広場前 17:17（平日・土日祝とも）→ 前橋駅 18:10。関越交通「通過時刻予定表」（2026年12月1日改正）の土日祝・平日の表
- 天城山：伊東駅から東海バス「伊豆天城リゾートシャトルバス」（毎日3往復＋土曜などの増発便）。
  帰りの最終：天城縦走登山口 16:45 → 伊東駅 17:40（毎日）。東海バスの時刻表（2026年3月1日改正）
何度流しても同じ結果。このあと gen_train_daytrip.py → check_pages.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'train_daytrip.json')
raw = open(P, encoding='utf-8').read()
d = json.loads(raw)
g = next(x for x in d['groups'] if x['key'] == 'hyaku')
ids = [i for i in g['ids'] if i not in ('tateyama', 'karamatsu')]
for i in ('akagi', 'amagi'):
    if i not in ids:
        ids.append(i)
g['ids'] = ids
for i in ('tateyama', 'karamatsu'):
    d['lastBus'].pop(i, None)
    d['courses'].pop(i, None)
d['courses']['akagi'] = {
    'route': 3,
    'note': '直通のバスは土日祝だけで、平日は富士見温泉で乗り換えます。12月〜3月は冬ダイヤです。',
}
d['lastBus']['akagi'] = {
    'status': 'ok',
    'operator': '関越交通',
    'rows': [{'from': 'あかぎ広場前', 'to': '前橋駅', 'weekday': '17:17', 'holiday': '17:17'}],
    'note': '2026年12月1日〜2027年3月31日の冬ダイヤ。平日は富士見温泉で乗り換え（前橋駅着18:10）',
    'revised': '2026-12-01',
    'checkedAt': '2026-11-18',
    'sourceUrl': 'https://kan-etsu.net/files/libs/14686/202611131729401095.pdf',
    'sources': [
        {'label': '関越交通 冬ダイヤ（土日祝）', 'url': 'https://kan-etsu.net/files/libs/14686/202611131729401095.pdf',
         'revised': '2026年12月1日改正', 'checkedAt': '2026-11-18'},
        {'label': '関越交通 冬ダイヤ（平日）', 'url': 'https://kan-etsu.net/files/libs/14685/202611131729328577.pdf',
         'revised': '2026年12月1日改正', 'checkedAt': '2026-11-18'},
    ],
}
d['lastBus']['amagi'] = {
    'status': 'ok',
    'operator': '東海バス',
    'rows': [{'from': '天城縦走登山口', 'to': '伊東駅', 'weekday': '16:45', 'holiday': '16:45'}],
    'note': '伊東駅着17:40。バスは1日3往復（土曜などは増発便あり）',
    'revised': '2026-03-01',
    'checkedAt': '2026-11-18',
    'sourceUrl': 'https://www.tokaibus.jp/images/6589.pdf',
}
s = json.dumps(d, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else '')
open(P, 'w', encoding='utf-8').write(s)
print('ok', ids)
