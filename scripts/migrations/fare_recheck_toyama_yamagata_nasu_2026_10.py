#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""薬師岳・黒部五郎岳・立山・剱岳・蔵王山・那須岳の運賃と経路の検算（2026-10-07）。
出典：Yahoo!路線情報（2026-10-17 発）
  →富山：新宿12,970円（大宮07:43発かがやき503号→09:24）／大宮12,640円（06:41→08:23）／横浜13,730円（東京07:20発→09:24）
  →山形：新宿11,460円（大宮08:25発つばさ75号→10:44）／大宮11,130円／横浜12,330円（東京08:00発）
  →那須塩原：新宿5,390円／大宮5,060円／横浜6,370円（自由席）
  電鉄富山→立山 1,280円・73分、立山駅→室堂 4,670円（アルペンルート公式の運賃）
  富山地鉄 夏山バス有峰線（高速バスドットコム）：富山駅前〜折立 6,000円・100分。2026年は7/11〜8/23毎日、8/29〜9/27土日祝
  NAVITIME：山形駅前→蔵王温泉バスターミナル 1,200円・37分
"""
import json, os, sys, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-07'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
def leg(station, icon=None, line=None, minutes=None):
    if icon is None: return {'station': station}
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}
def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')
def build(m, heads, tail, fares):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        R[dep]['legs'] = heads[dep] + copy.deepcopy(tail)
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
        m['fare' + K] = fares[dep]
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['mountainUpdated'] = V; m['fareCheckedAt'] = V
def faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text
def T(m): return hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama'])
def html(m): m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)

TOYAMA = {'shinjuku': [leg('新宿駅', 'train', 'JR湘南新宿ライン', 31), leg('大宮駅', 'train', '北陸新幹線かがやき', 101)],
          'omiya': [leg('大宮駅', 'train', '北陸新幹線かがやき', 102)],
          'yokohama': [leg('横浜駅', 'train', 'JR上野東京ライン', 26), leg('東京駅', 'train', '北陸新幹線かがやき', 124)]}
# 薬師岳・黒部五郎岳（折立）
for mid in ('yakushidake', 'kurobegorodam'):
    m = N[mid]
    build(m, copy.deepcopy(TOYAMA), [leg('富山駅', 'bus', '富山地鉄バス 夏山バス(有峰線)直通便', 100), leg('折立')],
          {'shinjuku': 18970, 'omiya': 18640, 'yokohama': 19730})
    m['trainRoutes']['note'] = ('💡 富山駅前〜折立の直通バスは完全予約制で、約1時間40分・6,000円。'
                                '2026年は7月11日〜8月23日が毎日、8月29日〜9月27日は土日祝だけの運行。'
                                '朝の便は富山駅前を6時10分に出るため、当日の新幹線では間に合わない。富山に前泊する。'
                                '新宿からは大宮で北陸新幹線に乗り換えるのが速くて安い')
    m['trainRoutes']['summaryNote'] = '※運賃はJR（かがやき指定席）＋バス6,000円の合計'
    for it in m['annualItems']:
        if '折立' in it['label']:
            it.update({'validFrom': '2026-07-11', 'validTo': '2026-09-27', 'note': '8月23日までは毎日、8月29日以降は土日祝のみ・完全予約制',
                       'sourceUrl': 'https://www.kosokubus.com/?dir=sp&page=_arimine', 'lastVerified': V})
    html(m); a, b, c = T(m)
    faq(m, f'{m["name"]}（折立登山口）へは、北陸新幹線で富山駅へ行き、富山地鉄の夏山バスで折立まで約1時間40分です。'
           f'新宿から{a}・18,970円、大宮から{b}・18,640円、横浜から{c}・19,730円が目安です（乗り換えの待ち時間は別）。'
           'バスは完全予約制で、2026年は7月11日〜9月27日の運行でした。朝の便は早朝発のため、富山での前泊が必要です。')

# 立山・剱岳（室堂）：JR＋地鉄1,280円＋立山駅〜室堂4,670円
for mid in ('tateyama', 'tsurugi'):
    m = N[mid]
    cable = [l for l in m['trainRoutes']['routes']['shinjuku']['legs'] if l['station'] == '立山駅'][0]['durationMin']
    build(m, copy.deepcopy(TOYAMA), [leg('富山駅', 'train', '富山地方鉄道', 73), leg('立山駅', 'cable', 'ケーブルカー・高原バス', cable), leg('室堂（季節運行）')],
          {'shinjuku': 18920, 'omiya': 18590, 'yokohama': 19680})
    m['trainRoutes']['summaryNote'] = '※運賃はJR（かがやき指定席）＋富山地方鉄道1,280円＋立山駅〜室堂4,670円の合計'
    n0 = m['trainRoutes']['note']
    for a_, b_ in (('例年4月中旬〜11月下旬の営業', '2026年は4月15日〜11月30日の営業'), ('新宿からの運賃は片道約18,000円と高額なため', '運賃が高額なため')):
        n0 = n0.replace(a_, b_)
    m['trainRoutes']['note'] = n0
    html(m); a, b, c = T(m)
    faq(m, f'北陸新幹線で富山駅へ行き、富山地方鉄道で立山駅へ、ケーブルカーと高原バスを乗り継いで室堂へ上がります。'
           f'新宿からは大宮で新幹線に乗り換えて{a}・18,920円、大宮から{b}・18,590円、横浜から{c}・19,680円が目安です（乗り換えの待ち時間は別）。'
           + ('剱岳へは室堂から剱沢を経て登ります。' if mid == 'tsurugi' else '') + '車の場合は都心から約6時間が目安です。')

# 蔵王山：JR＋バス1,200円
m = N['zaosan']
build(m, {'shinjuku': [leg('新宿駅', 'train', 'JR湘南新宿ライン', 30), leg('大宮駅', 'train', '山形新幹線つばさ', 139)],
          'omiya': [leg('大宮駅', 'train', '山形新幹線つばさ', 139)],
          'yokohama': [leg('横浜駅', 'train', 'JR上野東京ライン', 27), leg('東京駅', 'train', '山形新幹線つばさ', 164)]},
      [leg('山形駅', 'bus', '山交バス蔵王温泉行き', 37), leg('蔵王温泉バスターミナル')],
      {'shinjuku': 12660, 'omiya': 12330, 'yokohama': 13530})
m['trainRoutes']['summaryNote'] = '※運賃はJR（つばさは全車指定席）＋バス1,200円の合計。新宿からは大宮で新幹線に乗り換える'
html(m); a, b, c = T(m)
faq(m, f'山形新幹線で山形駅へ行き、山交バスで蔵王温泉バスターミナルまで約37分です。'
       f'新宿からは大宮で新幹線に乗り換えて{a}・12,660円、大宮から{b}・12,330円、横浜から{c}・13,530円が目安です（乗り換えの待ち時間は別）。'
       '車の場合は都心から約6時間が目安です。')

# 那須岳：大宮発が110円安く載っていた。終点の表記を揃える
m = N['nasu']
for dep, _ in DEPS:
    legs = m['trainRoutes']['routes'][dep]['legs']
    legs[-1] = {'station': '峠の茶屋登山口'}
m['fareOmiya'] = 6700
m['trainAccess'] = legs_text(m['trainRoutes']['routes']['shinjuku']['legs'])
m['trainAccessOmiya'] = legs_text(m['trainRoutes']['routes']['omiya']['legs'])
m['trainAccessYokohama'] = legs_text(m['trainRoutes']['routes']['yokohama']['legs'])
m['trainRoutes']['note'] = m['trainRoutes']['note'].replace('バスは季節運行（例年4月〜11月）で、冬期は運休', 'バスは季節運行（2026年は4月1日〜11月30日）で、冬ダイヤの間は大丸温泉までで折り返す')
html(m); m['mountainUpdated'] = V; m['fareCheckedAt'] = V
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']][0]
hit['answer'] = hit['answer'].replace('横浜からは', '大宮からは' + hm(m['trainTimeOmiya']) + '（運賃約6,700円）、横浜からは')
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('yakushidake', 'kurobegorodam', 'tateyama', 'tsurugi', 'zaosan', 'nasu'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
