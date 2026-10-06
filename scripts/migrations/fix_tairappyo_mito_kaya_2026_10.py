#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""平標山・三頭山・茅ヶ岳：運行形態の表記修正と2026年の期間登録（2026-10-06）。
出典：南越後交通バス 2026年4月1日改正時刻表（湯沢駅前〜平標登山口は通年・1日8便・約34分・660円）、
      檜原都民の森の公式案内（急行バス・連絡バスは4〜11月の開園日と3月の土日祝。12〜2月は運行なし）、
      山梨峡北交通の告知（茅ヶ岳みずがき田園バス 韮崎深田公園線：2026年4月4日〜11月23日の土日祝、4/29〜5/5は毎日、700円）
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-06'
def item(kind, label, url, vf=None, vt=None, note=None):
    d = {'kind': kind, 'label': label, 'validFrom': vf, 'validTo': vt, 'seasonYear': int(vt[:4]) if vt else None, 'sourceUrl': url, 'lastVerified': V}
    if note: d['note'] = note
    return d
def done(m):
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m); m['mountainUpdated'] = V

m = N['tairappyo']
m['trainRoutes']['badge'] = {'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'}
a = '南越後交通バスで平標登山口へ約35分・約640円'
assert a in m['trainRoutes']['note']
m['trainRoutes']['note'] = m['trainRoutes']['note'].replace(a, '南越後交通バス（湯沢駅〜浅貝〜西武クリスタル線）で平標登山口へ約35分・660円。通年運行で1日8便（2026年4月改正）')
m['annualItems'] = [item('info', '越後湯沢駅〜平標登山口の路線バスのダイヤ', 'https://www.minamiechigo.co.jp/')]
m['annualNotApplicable'] = True
m['needsVerification'] = True
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['運賃合計が旧バス運賃（約640円）で計算されている可能性。現行は660円']
done(m)

m = N['mitosaan']
m['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ 12〜2月は運休'}
a = '3月中旬〜11月の土日祝は、武蔵五日市駅から都民の森まで直通の急行バスも運行（所要時間短縮、運賃は同額程度）。冬季（12〜2月頃）は数馬〜都民の森間の連絡バスが運休。'
assert a in m['trainRoutes']['note']
m['trainRoutes']['note'] = m['trainRoutes']['note'].replace(a,
    '数馬〜都民の森の連絡バスと、武蔵五日市駅から直通の急行バスは、4〜11月の開園日は毎日、3月は土日祝だけ走る。'
    '12〜2月は都民の森までのバスがなく、数馬から歩くことになる。'
    '都民の森は月曜休園（祝日は翌日）で、休園日はバスも運休。')
m['annualItems'] = [item('info', '武蔵五日市駅〜都民の森のバスの運行期間', 'https://www.hinohara-mori.jp/access_bus/')]
m['annualNotApplicable'] = True
done(m)

m = N['kayagatake']
m['trainRoutes']['summaryNote'] = '※バスは季節運行。2026年は4月4日〜11月23日の土日祝（4月29日〜5月5日は毎日）で、1日2往復・700円。運行のない日は韮崎駅からタクシーを使う'
m['annualItems'] = [item('transport', '韮崎駅〜深田記念公園のバス（韮崎深田公園線）', 'http://cus4.kyohoku.jp/routebus/kayagatakemizugakidenen-bus/schedule-fukadakoenline/',
                         '2026-04-04', '2026-11-23', '土日祝のみ。4月29日〜5月5日は毎日')]
done(m)
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
