#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：10月の初冬・南アルプスの6月・厳しすぎる低山を見直す（2026-10-09）。
■ 10月（標高2,800m以上で、10月が軽アイゼン等・11月が冬山装備の山）
  長野県山岳遭難防止対策協会「山岳通信」：2023年は10月2週末に北アルプスで約30cmの積雪があり「冬山の装備が必須」（第319号・10/20）、
  3週も「冬山と同等の防寒装備やアイゼン・ピッケルを携行」（第320号・10/26）。2020年10月4週も「凍結して滑りやすく、アイゼン等の冬山装備が必要」（第205号）。
  → 10月を「10/10まで軽アイゼン等／10/11〜冬山装備」の切替にする。切替日は「中旬以降」の初日（安全側）
■ 南アルプスの6月（仙丈ヶ岳・甲斐駒ヶ岳・塩見岳）
  伊那市「【残雪注意】6月に南アルプスを登山される皆様へ」（2026年5月1日更新）：
  「6月の仙丈ヶ岳・甲斐駒ヶ岳・塩見岳には雪が残っており、アイゼンなどの滑り止め装備が必要となる場合があります」。
  冬季〜5月は「ピッケル、アイゼンなどの冬山装備が必須」と書き分けている → 6月は軽アイゼン等に戻す
  間ノ岳・農鳥岳・赤石岳・荒川岳・聖岳・黒部五郎岳・野口五郎岳は6月の情報が取れず、冬山装備（安全側）のまま
■ 厳しすぎた低山
  高水三山（793m）：2月に積雪約20cmで軽アイゼンを使った記録。3〜4月の根拠はなく、同じ奥多摩の本仁田山・大岳山に合わせ 12〜2月だけ軽アイゼン等に
  金時山（1,212m）：3月上旬に凍結した雪道の記録、神奈川県の積雪情報は3月下旬まで。4月はアイゼン不要に
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
OLD = json.load(open(sys.argv[1], encoding='utf-8'))   # 6月を一括変更する前の gear-data.json
N = {m['id']: m for m in D}
V = '2026-10-09'
SPLIT = {'split': True, 'before': 'light_crampons', 'after': 'winter_gear', 'changeDate': 11}


def sync_old(m):
    assert not G.validate(m['gearCalendar'])
    keys = []
    for e in m['gearCalendar']:
        for k in ([e] if isinstance(e, str) else [e['before'], e['after']]):
            if k not in keys:
                keys.append(k)
    m['calLegend'] = [G.LABEL[k] for k in G.KEYS if k in keys]
    m['seasonNoGear'] = ranges([i + 1 for i in range(12) if m['gearCalendar'][i] == 'no_crampons'])
    m['mountainUpdated'] = V


# ── 10月の切替 ──
oct_done = []
for m in D:
    cal = m['gearCalendar']
    if (m.get('elevation') or 0) < 2800 or cal[9] != 'light_crampons' or cal[10] != 'winter_gear':
        continue
    if m.get('dataModel') == 'ssot-v1':
        m['conditions']['gearSplits'] = {'10': {'before': 'light_crampons', 'after': 'winter_gear', 'changeDate': 11}}
        m['mountainUpdated'] = V
    else:
        cal[9] = dict(SPLIT)
        sync_old(m)
    oct_done.append(m['name'])
assert len(oct_done) == 29, len(oct_done)

# ── 南アルプスの6月 ──
for mid in ('senjogatake', 'komagatake', 'shiomidake'):
    m = N[mid]
    assert m['gearCalendar'][5] == 'winter_gear', mid
    if m.get('dataModel') == 'ssot-v1':
        m['conditions']['gearMonthly'][5] = 'snow_caution'
        m['conditions']['gearSource'] = '6月は伊那市の案内（アイゼンなどの滑り止めが必要な場合あり）に合わせ軽アイゼン等（2026-10-09）'
    else:
        m['gearCalendar'][5] = 'light_crampons'
        m['seasonCalendar'][5] = 's-gear'
        sync_old(m)
    GD[mid]['6'] = OLD[mid]['6']
    m['mountainUpdated'] = V
hit = [q for q in N['shiomidake']['faq'] if 'シーズン' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = ('塩見岳の登山シーズンは7月〜9月が目安です。6月は雪が残り、アイゼンなどの滑り止めが必要になることがあります（伊那市の案内）。'
                    '5月までは冬山装備が必須で、10月中旬以降も積雪・凍結で冬山装備が必要になる年があります。直前の最新情報を確認してください。')

# ── 厳しすぎた低山 ──
for mid, back, six, months in (('takamizusanzan', [3, 4], '12月〜2月', '12月〜2月'), ('kintoki', [4], '12月〜3月', '12月〜3月')):
    m = N[mid]
    for mo in back:
        assert m['gearCalendar'][mo - 1] == 'light_crampons', (mid, mo)
        m['gearCalendar'][mo - 1] = 'no_crampons'
        m['seasonCalendar'][mo - 1] = 's-ok'
        GD[mid][str(mo)] = [c for c in GD[mid][str(mo)] if c['c'] != 'crampon']
    sync_old(m)
    m['season6Crampons'] = six
    hit = [q for q in m['faq'] if 'シーズン' in q['question']]
    assert len(hit) == 1
    hit[0]['answer'] = (f'{m["name"]}は通年登れます。{months}は積雪や凍結があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が必要になることがあります。'
                        '積雪・凍結の状況は年によって変わるため、直前の最新情報を確認してください。')

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(GD, open(GP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(oct_done), '・'.join(oct_done))
