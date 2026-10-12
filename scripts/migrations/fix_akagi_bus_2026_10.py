#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""赤城山：関越交通バスの2026年9月19日改正を反映する（2026-10-12）。
出典（関越交通 公式・赤城山直通バスのページ https://kan-etsu.net/publics/index/42/ ）：
- 「赤城ビジターセンターの完成に伴い、2026年9月19日から『スノーピークランドステーション赤城』が終点となります」
- 時刻表 48 前橋赤城山線 夏季（4/1〜11/30）2026年9月19日改正・土日祝：
    直通（48C）前橋駅 8:45・12:10・15:15 発 → 赤城山大洞 9:48 → あかぎ広場前 9:50 → スノーピークLS赤城 9:56
    （前橋駅〜あかぎ広場前は65分）
- 運賃表 2026年9月19日改定：前橋駅〜あかぎ広場前 1,850円（赤城山大洞・スノーピークLS赤城は1,800円）
変更前：バス75分・運賃1,500円で計算（合計 5,460／3,100／4,250円）、終点は「あかぎ広場前（建替え工事のため終点）」
鉄道（前橋まで 3,960／1,600／2,750円）は 2026-10-07 の検算のまま。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'akagi'][0]
V = '2026-10-12'
SRC = 'https://kan-etsu.net/publics/index/42/'
OLD_BUS, NEW_BUS = 1500, 1850
assert (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama']) == (5460, 3100, 4250), '運賃が想定と違う（適用済み？）'
R = m['trainRoutes']['routes']
for dep, K in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
    legs = R[dep]['legs']
    assert legs[-2]['station'] == '前橋駅' and legs[-2]['durationMin'] == 75, dep
    legs[-2]['method']['line'] = '関越交通バス（スノーピークランドステーション赤城行き）'
    legs[-2]['durationMin'] = 65
    legs[-1] = {'station': 'あかぎ広場前'}
    m['fare' + K] = m['fare' + K] - OLD_BUS + NEW_BUS
    m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in legs)
m['trainRoutes']['summaryNote'] = '※運賃はJR＋バス1,850円（前橋駅〜あかぎ広場前。2026年9月19日改定）の合計。直通バスは土日祝だけで、前橋駅発は8:45・12:10・15:15の3本（2026年11月30日までの夏ダイヤ）'
m['trainRoutes']['note'] = ('💡 2026年9月19日から、バスの終点は「スノーピークランドステーション赤城」（新しい赤城ビジターセンター）になった。'
                            '黒檜山登山口へは「あかぎ広場前」で降りる。'
                            '平日は直通がなく、富士見温泉で乗り換える。'
                            '12月以降は冬ダイヤに変わるので、関越交通の時刻表で確認する。'
                            'あかぎ大沼白樺マラソン・まえばし赤城山ヒルクライムの開催日は、交通規制のため午前中は山頂・大沼周辺へ行けない')
m['trainAccess'] = legs_text(R['shinjuku']['legs'])
m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
m['trainInfo'] = '新宿→高崎（新幹線約50分）→前橋（両毛線約15分）→バス約65分（土日祝直通）'
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = '前橋駅から関越交通バスで「あかぎ広場前」まで約65分（土日祝は直通、平日は富士見温泉で乗換）。新宿からは上越新幹線で高崎→JR両毛線で前橋まで約70分です。'
items = [a for a in (m.get('annualItems') or []) if a.get('label') != '前橋駅〜赤城山の直通バス（夏ダイヤ）']
items.append({'kind': 'transport', 'label': '前橋駅〜赤城山の直通バス（夏ダイヤ）', 'validFrom': '2026-09-19', 'validTo': '2026-11-30', 'seasonYear': 2026,
              'sourceUrl': SRC, 'lastVerified': V, 'note': '土日祝のみ。12月以降は冬ダイヤ'})
m['annualItems'] = items
m['mountainUpdated'] = V
m['fareCheckedAt'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('akagi', m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'])
print(m['trainAccess'])
