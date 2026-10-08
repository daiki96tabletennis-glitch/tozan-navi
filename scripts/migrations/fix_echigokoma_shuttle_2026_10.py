#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""越後駒ヶ岳：小出駅〜枝折峠の路線バスは無い（サイト運営者が確認）。大湯公園発の「うおぬま滝雲シャトルバス」に直す（2026-10-08）。
出典：
- 魚沼市観光協会「2026年度 うおぬま滝雲シャトルバス」（2026.10.3更新）https://www.iine-uonuma.jp/31055/
  2026年9月19日〜11月3日の土日祝。大湯公園駐車場発は3時30分〜7時の1日2便（10月中旬まで）、白銀の湯発は4時〜6時40分。
  片道1,000円（魚沼市内の宿泊者は宿泊証明券で500円）。予約不要。登山者向け臨時便が枝折峠15時発（土日祝）
- 南越後交通バス 小出駅前〜折立〜栃尾又線 運賃表：小出駅前〜大湯公園 400円
  休日時刻表（2025年4月1日改正）：小出駅前 6:40／7:55／15:20／17:20 発、大湯公園まで25分
- 小出駅まで（Yahoo!路線情報、浦佐乗換）新宿6,820円／大宮6,490円／横浜8,800円
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'echigokoma'][0]
V = '2026-10-08'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
SRC = 'https://www.iine-uonuma.jp/31055/'


def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')


def yen(n):
    return format(n, ',') + '円'


tr = m['trainRoutes']
for dep in tr['routes']:
    L = tr['routes'][dep]['legs']
    assert L[-2]['station'] == '小出駅' and L[-1]['station'] == '枝折峠登山口', dep
    L[-2] = {'station': '小出駅', 'method': {'icon': 'bus', 'line': '南越後交通バス「栃尾又線」'}, 'durationMin': 25, 'fareYen': None}
    L[-1:] = [{'station': '大湯公園（前泊）', 'method': {'icon': 'bus', 'line': 'うおぬま滝雲シャトルバス（土日祝・早朝）'}, 'durationMin': 40, 'fareYen': None},
              {'station': '枝折峠登山口'}]
tr['lineName'] = '上越新幹線・JR上越線・南越後交通バス・うおぬま滝雲シャトルバス'
tr['badge'] = {'type': None, 'style': 'background:#fde8d8;color:#8a5010;', 'icon': 'warn', 'label': '秋の土日祝のみ・前泊が必要'}
tr['note'] = ('💡 小出駅から枝折峠へ行く路線バスは無い。'
              '公共交通で枝折峠へ入れるのは「うおぬま滝雲シャトルバス」だけで、2026年は9月19日〜11月3日の土日祝に運行する。'
              '大湯公園駐車場発は3時30分〜7時の1日2便で、10月中旬まで。'
              '白銀の湯の駐車場からも4時〜6時40分に出ている。'
              '片道1,000円で、魚沼市内に泊まった人は宿泊証明券を見せると500円になる。'
              '予約は不要だが、乗れる人数に限りがある。'
              '帰りは登山者向けの臨時便が枝折峠を15時に出る（土日祝）。'
              '早朝発のため、大湯温泉などに前泊する。'
              '小出駅前〜大湯公園は南越後交通バスで約25分・400円、土日祝は小出駅前6時40分・7時55分・15時20分・17時20分発')
tr['summaryNote'] = '※シャトルバスの無い時期・平日は、小出駅や大湯温泉からタクシーを使う。表示の所要時間に前泊の時間は含まない'
tr['links'] = [l for l in (tr.get('links') or []) if l.get('type') == 'yahoo'] + [
    {'type': 'bus', 'label': 'うおぬま滝雲シャトルバス（魚沼市観光協会）', 'url': SRC},
    {'type': 'bus', 'label': 'バス時刻表（南越後交通バス）', 'url': 'https://www.minamiechigo.co.jp/'}]
m['busScheduleLinks'] = [SRC]
m['annualItems'] = [{'kind': 'transport', 'label': '大湯公園・白銀の湯〜枝折峠の「うおぬま滝雲シャトルバス」',
                     'validFrom': '2026-09-19', 'validTo': '2026-11-03', 'seasonYear': 2026,
                     'sourceUrl': SRC, 'lastVerified': V, 'note': '土日祝のみ。大湯公園発は10月中旬まで'}]
F = {'shinjuku': 8220, 'omiya': 7890, 'yokohama': 10200}
for dep, K in DEPS:
    m['fare' + K] = F[dep]
    m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in tr['routes'][dep]['legs'])
m['trainAccess'] = legs_text(tr['routes']['shinjuku']['legs'])
m['trainAccessOmiya'] = legs_text(tr['routes']['omiya']['legs'])
m['trainAccessYokohama'] = legs_text(tr['routes']['yokohama']['legs'])
m['trainAccessHtml'] = render_ts_section(tr, m)
m['verifyNotes'] = [n for n in (m.get('verifyNotes') or []) if '小出駅〜枝折峠のバス' not in n] + [
    'シャトルバス大湯公園〜枝折峠の所要時間（約40分）と、大湯公園発の最終運行日（「10月中旬まで」）の正確な値が未確認']
m['needsVerification'] = True
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
t = tuple(hm(m['trainTime' + K]) for _, K in DEPS)
hit[0]['answer'] = ('上越新幹線で浦佐駅へ行き、JR上越線で小出駅へ、南越後交通バスで大湯公園へ向かいます。小出駅から枝折峠への路線バスは無く、大湯公園から「うおぬま滝雲シャトルバス」（2026年は9月19日〜11月3日の土日祝、早朝発）で枝折峠へ入ります。'
                    f'新宿から{t[0]}・{yen(F["shinjuku"])}、大宮から{t[1]}・{yen(F["omiya"])}、横浜から{t[2]}・{yen(F["yokohama"])}が目安です（新幹線は自由席。乗り換えの待ち時間と前泊は別）。'
                    'シャトルバスの無い時期はタクシーを使います。車の場合は都心から約5時間20分が目安です。')
m['trainInfo'] = '新宿→大宮→浦佐（上越新幹線）→小出（上越線）→大湯公園（バス25分・前泊）→滝雲シャトルバス→枝折峠'
m['mountainUpdated'] = V
m['fareCheckedAt'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(F, m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'])
