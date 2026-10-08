#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""越後駒ヶ岳：滝雲シャトルバスの記載を協会の最新情報（2026.10.8更新）に合わせる（2026-10-08）。
出典：魚沼市観光協会 https://www.iine-uonuma.jp/31055/ と https://www.iine-uonuma.jp/31684/
- 大湯公園発は災害復旧のため1日2便（4:30発→枝折峠5:30着、5:00発→6:00着、シルバーライン経由）だったが、
  国道352号の規制解除（2026年10月9日15時）に伴い「昨年同様の運行」（随時運行・始発3:30〜最終7:00）に戻る
- 登山者向け臨時便（枝折峠15時発）は白銀の湯駐車場を経由して大湯公園へ。所要約70分（サイト運営者が確認）
- 小出駅前〜大湯公園の路線バス（栃尾又線）は平日・土日祝とも時刻表があり通年運行。季節運行なのはシャトルバスだけ
"""
import json, os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'echigokoma'][0]
tr = m['trainRoutes']
for dep in tr['routes']:
    L = tr['routes'][dep]['legs']
    assert L[-3]['station'] == '小出駅'
    L[-3]['method']['line'] = '南越後交通バス「栃尾又線」（通年運行）'
tr['badge'] = {'type': None, 'style': 'background:#fde8d8;color:#8a5010;', 'icon': 'warn', 'label': 'シャトルバスは秋の土日祝のみ・前泊が必要'}
tr['note'] = ('💡 小出駅から枝折峠へ行く路線バスは無い。'
              '公共交通で枝折峠へ入れるのは「うおぬま滝雲シャトルバス」だけで、2026年は9月19日〜11月3日の土日祝に運行する。'
              '大湯公園駐車場発は始発3時30分〜最終7時（予定）。'
              '白銀の湯の駐車場からも4時〜6時40分に約20分間隔で出ている。'
              '片道1,000円で、魚沼市内に泊まった人は宿泊証明券を見せると500円になる。'
              '予約は不要だが、乗れる人数に限りがある。'
              '帰りは登山者向けの臨時便が枝折峠を15時に出る（土日祝・1便のみ）。'
              'この臨時便は白銀の湯駐車場を経由するため、大湯公園まで約70分かかる。'
              '乗り遅れると歩いて下りることになるので、時間に余裕のある計画にする。'
              '早朝発のため、大湯温泉などに前泊する。'
              '小出駅前〜大湯公園の南越後交通バスは通年運行で、約25分・400円。'
              '土日祝は小出駅前6時40分・7時55分・15時20分・17時20分発')
m['trainAccess'] = legs_text(tr['routes']['shinjuku']['legs'])
m['trainAccessOmiya'] = legs_text(tr['routes']['omiya']['legs'])
m['trainAccessYokohama'] = legs_text(tr['routes']['yokohama']['legs'])
m['trainAccessHtml'] = render_ts_section(tr, m)
m['annualItems'][0]['note'] = '土日祝のみ。帰りの登山者向け臨時便は枝折峠15時発'
m['verifyNotes'] = [n for n in m['verifyNotes'] if 'シャトルバス大湯公園' not in n] + [
    'シャトルバス大湯公園→枝折峠（国道352号経由）の所要時間。協会ページに記載が無い（規制解除前のシルバーライン経由は60分。現在の表示は約40分）']
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
