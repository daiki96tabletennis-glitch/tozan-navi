#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：通年「アイゼン不要」だった標高1,100m以上の6山に、冬の「軽アイゼン等」の月を入れる（2026-10-08）。
同じ山域・同じ標高帯の山（三ノ塔・本仁田山・御前山・石割山など）は冬が軽アイゼン等なのに、この6山だけ通年アイゼン不要になっていた。
根拠（冬に積雪・凍結があること）：
- 大山（丹沢）：神奈川県「丹沢・大山の積雪情報」（1〜2月に山頂で数cm〜約30cmの積雪）。同じ山塊の三ノ塔に合わせ 12〜3月
- 大岳山：2026年2月の登山記録（芥場峠付近はチェーンスパイク必須）。同じ奥多摩の本仁田山に合わせ 12〜2月
- 天城山：積雪時期は1月〜3月中旬（静岡県警の登山案内ほか）。1〜3月
- 扇山：冬（12〜2月）は登山道の凍結に注意との案内。12〜2月
- 明神ヶ岳：箱根は1〜2月にまとまった積雪がある。1〜2月
- 笹子雁ヶ腹摺山：冬は残雪がアイスバーンになり軽アイゼンが役立つとの記録。同じ標高帯の石割山に合わせ 12〜2月
百蔵山（1,003m）は根拠が弱いので変えない（要確認）。
旧フィールド（seasonCalendar など）・FAQ・装備カード（gear-data.json）も同じ内容に揃える。
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
V = '2026-10-08'
PLAN = {'oyama': [12, 1, 2, 3], 'otake': [12, 1, 2], 'amagi': [1, 2, 3], 'ogiyama': [12, 1, 2],
        'myojingatake': [1, 2], 'sasakogarigaburiyama': [12, 1, 2]}
CARD = {'c': 'crampon', 'i': '推奨', 'p': 'エバニュー 6本爪アイゼン',
        'r': '凍結・残雪が見られる時期です。チェーンスパイクや6本爪アイゼンなどの軽アイゼン等があると滑りにくく安心です。事前に最新の積雪・凍結情報を確認してください。'}


def span(months):
    """[12,1,2] → 12月〜2月"""
    return f'{months[0]}月〜{months[-1]}月'


for mid, months in PLAN.items():
    m = N[mid]
    assert m.get('dataModel') != 'ssot-v1' and all(e == 'no_crampons' for e in m['gearCalendar']), mid
    for mo in months:
        m['gearCalendar'][mo - 1] = 'light_crampons'
        m['seasonCalendar'][mo - 1] = 's-gear'
    assert not G.validate(m['gearCalendar'])
    m['calLegend'] = [G.LABEL['no_crampons'], G.LABEL['light_crampons']]
    m['seasonNoGear'] = ranges([i + 1 for i in range(12) if m['gearCalendar'][i] == 'no_crampons'])
    m['season6Crampons'] = span(months)
    m['season'] = '通年（冬は積雪・凍結に注意）'
    hit = [q for q in m['faq'] if 'シーズン' in q['question']]
    assert len(hit) <= 1, mid
    if hit:
        hit[0]['answer'] = (f'{m["name"]}は通年登れます。{span(months)}は積雪や凍結があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が必要になることがあります。'
                            '積雪・凍結の状況は年によって変わるため、直前の最新情報を確認してください。')
    m['mountainUpdated'] = V
    for mo in months:
        cards = GD[mid][str(mo)]
        if any(c['c'] == 'crampon' for c in cards):
            continue
        idx = max(i for i, c in enumerate(cards) if c['c'] in ('shoe', 'rain')) + 1
        cards.insert(idx, dict(CARD))
    print(mid, m['name'], m['seasonNoGear'], '/', m['season6Crampons'])
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(GD, open(GP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
