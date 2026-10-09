#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：御岳山・日の出山・棒ノ折山は「通年アイゼン不要」ではなかった（2026-10-09）。
- 棒ノ折山：2月の記録で「7割ほど凍結、軽アイゼンまたはチェーンスパイク必須」、白谷沢も凍結して「下りは必携」。1月にひざ下の積雪の記録。2月の平年最深積雪17cm
- 御岳山：御岳山駅〜神社は雪が降ってもすぐ除雪されるが、それ以外の山道はチェーンスパイクか軽アイゼンが必要。
  1月下旬に参道が雪道になった記録。御岳ビジターセンターは、冬（12〜2月）のロックガーデンは凍結するとして別コースを案内
- 日の出山：2月の平年最深積雪18cm・最低気温−6.5℃。御岳山〜日の出山でチェーンスパイクを使った記録
→ 記録で確認できた1〜2月を軽アイゼン等にする（降雪・凍結のあとに必要になる時期、という意味）。12月と3月は根拠が無いので変えない
旧フィールド・FAQ・装備カードも揃える。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gear_calendar as G
from build_derived import ranges
P = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
D = json.load(open(P, encoding='utf-8'))
GD = json.load(open(GP, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-09'
LIGHT = {'c': 'crampon', 'i': '推奨', 'p': 'エバニュー 6本爪アイゼン',
         'r': '凍結・残雪が見られる時期です。チェーンスパイクや6本爪アイゼンなどの軽アイゼン等があると滑りにくく安心です。事前に最新の積雪・凍結情報を確認してください。'}
for mid in ('bonori', 'hinodesaan', 'mitakesan'):
    m = N[mid]
    assert all(e == 'no_crampons' for e in m['gearCalendar']), mid
    for mo in (1, 2):
        m['gearCalendar'][mo - 1] = 'light_crampons'
        m['seasonCalendar'][mo - 1] = 's-gear'
        cards = GD[mid][str(mo)]
        if not any(c['c'] == 'crampon' for c in cards):
            idx = max(i for i, c in enumerate(cards) if c['c'] in ('shoe', 'rain')) + 1
            cards.insert(idx, dict(LIGHT))
    assert not G.validate(m['gearCalendar'])
    m['calLegend'] = [G.LABEL['no_crampons'], G.LABEL['light_crampons']]
    m['seasonNoGear'] = ranges([i + 1 for i in range(12) if m['gearCalendar'][i] == 'no_crampons'])
    m['season6Crampons'] = '1月〜2月'
    m['season'] = '通年（冬は積雪・凍結に注意）'
    hit = [q for q in m['faq'] if 'シーズン' in q['question']]
    assert len(hit) == 1, mid
    hit[0]['answer'] = (f'{m["name"]}は通年登れます。1月〜2月は雪が降ったあとに登山道が凍結することがあり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が必要になる場合があります。'
                        '積雪・凍結の状況は年によって変わるため、直前の最新情報を確認してください。')
    m['mountainUpdated'] = V
    print(mid, m['seasonNoGear'])
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(GD, open(GP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
