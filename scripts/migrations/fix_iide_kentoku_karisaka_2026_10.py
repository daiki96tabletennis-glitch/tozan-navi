#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飯豊山（バスの運行主体）、乾徳山・雁坂嶺（山梨市民バスは毎日運行）の表記修正（2026-10-06）。
出典：山梨市公式「西沢渓谷線」（2025-08-01更新：毎日運行、1月1日・2日は運休、運行は笛吹観光自動車）、
      飯豊町がまとめた「飯豊山登山情報（市町村別一覧）」（喜多方市の飯豊山登山アクセスバス：山都タクシー運行、金〜月曜、1日2便、大人1,000円）
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
DEPS = ('shinjuku', 'omiya', 'yokohama')
KITAKATA = 'https://www.city.kitakata.fukushima.jp/soshiki/sangyo-y/36163.html'
YAMANASHI = 'https://www.city.yamanashi.yamanashi.jp/site/city-bus/9090.html'

def resync(m):
    R = m['trainRoutes']['routes']
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = '2026-10-06'

# ── 飯豊山：バスは会津バスではなく、喜多方市の「飯豊山登山アクセスバス」（山都タクシー運行） ──
m = N['iide']
for dep in DEPS:
    hit = [l for l in m['trainRoutes']['routes'][dep]['legs'] if l['station'] == '山都駅']
    assert len(hit) == 1 and '会津バス' in hit[0]['method']['line'], dep
    hit[0]['method']['line'] = '飯豊山登山アクセスバス（喜多方市・夏の金〜月曜のみ）'
m['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ 季節運行'}
m['trainRoutes']['note'] = ('💡 山都駅〜川入は、喜多方市の「飯豊山登山アクセスバス」（山都タクシーが運行）。'
                            '過去の実績では7月中旬〜9月中旬の金〜月曜だけ、1日2便、大人1,000円。'
                            '2026年の運行日は確認できていない。'
                            '出発前に喜多方市の山都総合支所か山都タクシーへ確認する。'
                            '運行のない日は山都駅からタクシーで入る')
m['trainRoutes']['links'] = [l for l in m['trainRoutes']['links'] if l.get('type') == 'yahoo'] + \
    [{'type': 'other', 'label': '喜多方市の登山口情報', 'url': KITAKATA}]
for it in m['annualItems']:
    if 'アクセスバス' in it['label']:
        it['label'] = '山都駅〜川入の飯豊山登山アクセスバス（喜多方市）'; it['sourceUrl'] = KITAKATA
m['busScheduleLinks'] = [KITAKATA]
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['飯豊山登山アクセスバスの2026年の運行日・運賃（運賃合計にバス代が含まれているかも未確認）']
m['needsVerification'] = True
resync(m)

# ── 乾徳山：山梨市駅からのバスは山梨市民バスで、毎日運行（季節運行ではない） ──
m = N['kentoku']
for dep in DEPS:
    legs = m['trainRoutes']['routes'][dep]['legs']
    hit = [l for l in legs if l['station'] == '山梨市駅']
    assert len(hit) == 1 and hit[0]['method']['line'] == '山梨交通「西沢渓谷線」', dep
    hit[0]['method']['line'] = '山梨市民バス「西沢渓谷線」'
    assert legs[-1]['station'] == '乾徳山登山口（季節）'
    legs[-1] = {'station': '乾徳山登山口'}
m['trainRoutes']['note'] = ('💡 山梨市駅〜乾徳山登山口は山梨市民バス「西沢渓谷線」。毎日運行（1月1日・2日は運休）で、平日も土日祝も同じ時刻。'
                            '本数が少ないので、下山時の最終便を必ず確認する。'
                            '塩山駅発の山梨交通「西沢渓谷線」でも乾徳山登山口へ行けるが、こちらは運行日が限られる')
m['trainRoutes']['summaryNote'] = '※冬に途中止まりになるとの情報があり、冬期は事前に確認する'
hit = [q for q in m['faq'] if 'バスは季節運行のため事前確認が必要です' in q['answer']]
assert len(hit) == 1
hit[0]['answer'] = hit[0]['answer'].replace('バスは季節運行のため事前確認が必要です', 'バスは毎日運行ですが本数が少ないため、時刻の事前確認が必要です')
for it in m['annualItems']:
    it['label'] = '山梨市駅〜乾徳山登山口の山梨市民バス（冬期の運行区間）'; it['kind'] = 'info'
m['annualNotApplicable'] = True
resync(m)

# ── 雁坂嶺：塩山駅発の山梨交通は運行日が限られる。山梨市駅発の市民バスは毎日運行と追記 ──
m = N['karisaka']
m['trainRoutes']['note'] = m['trainRoutes']['note'].rstrip('。') + '。山梨市駅からは山梨市民バス「西沢渓谷線」が毎日運行している（1月1日・2日は運休）'
m['annualItems'].append({'kind': 'info', 'label': '山梨市駅〜西沢渓谷入口の山梨市民バス', 'validFrom': None, 'validTo': None, 'seasonYear': None,
                         'sourceUrl': YAMANASHI, 'lastVerified': '2026-10-06'})
for it in m['annualItems']:
    if it['kind'] == 'transport':
        it['label'] = '塩山駅〜西沢渓谷入口の山梨交通バス'; it['sourceUrl'] = 'https://ykbus.jp/'
resync(m)
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
