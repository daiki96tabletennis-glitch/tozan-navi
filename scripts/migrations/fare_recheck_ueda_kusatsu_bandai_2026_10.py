#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四阿山・草津白根山・磐梯山の運賃と経路の検算、飯縄山のバス所要時間の修正（2026-10-07）。
出典：Yahoo!路線情報（2026-10-17 発、新幹線は自由席）
  →上田：新宿6,160円（大宮乗換）／大宮5,390円（08:17→09:18）／横浜6,700円（東京乗換、はくたか553号）
  →長野原草津口：新宿5,060円（大宮・高崎乗換）／大宮4,620円（08:17→高崎08:42、08:53→10:19）／横浜6,360円（東京・高崎乗換）
  →猪苗代：新宿7,700円（大宮08:05→郡山08:56、郡山09:15→猪苗代09:58）／大宮6,820円／横浜9,130円
  NAVITIME：上田駅前→菅平高原ダボス 600円・58分、長野原草津口駅→草津温泉 780円・25分、長野駅→飯綱登山口 47〜52分
新宿発が東京駅経由の高い経路で計算されていたのを、大宮で新幹線に乗る経路に改めた。
"""
import json, os, sys, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
def leg(station, icon=None, line=None, minutes=None):
    if icon is None: return {'station': station}
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}
def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')
def sync(m, fares=None):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
        if fares: m['fare' + K] = fares[dep]
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = '2026-10-07'
def faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text
def T(m): return hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama'])

# 四阿山
m = N['azumayasan']
tail = [leg('上田駅', 'bus', '上田バス(菅平線)', 58), leg('菅平高原(ダボス)')]
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR埼京線・湘南新宿ライン', 30), leg('大宮駅', 'train', '北陸新幹線', 61)] + copy.deepcopy(tail)
R['omiya']['legs'] = [leg('大宮駅', 'train', '北陸新幹線', 61)] + copy.deepcopy(tail)
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR上野東京ライン', 26), leg('東京駅', 'train', '北陸新幹線', 86)] + copy.deepcopy(tail)
m['trainRoutes']['summaryNote'] = '※運賃はJR（新幹線は自由席）＋バス600円の合計'
sync(m, {'shinjuku': 6760, 'omiya': 5990, 'yokohama': 7300})
a, b, c = T(m)
faq(m, f'四阿山（菅平高原登山口）へは、北陸新幹線で上田駅へ行き、上田バス菅平線で菅平高原ダボスまで約58分です。'
       f'新宿からは大宮で新幹線に乗り換えて{a}・6,760円、大宮から{b}・5,990円、横浜からは東京で新幹線に乗り換えて{c}・7,300円が目安です（乗り換えの待ち時間は別）。')

# 草津白根山
m = N['shirane_gunma']
tail = [leg('高崎駅', 'train', 'JR吾妻線', 86), leg('長野原草津口駅', 'bus', 'JRバス関東', 25), leg('草津温泉バスターミナル')]
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR埼京線・湘南新宿ライン', 30), leg('大宮駅', 'train', '上越・北陸新幹線', 25)] + copy.deepcopy(tail)
R['omiya']['legs'] = [leg('大宮駅', 'train', '上越・北陸新幹線', 25)] + copy.deepcopy(tail)
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR上野東京ライン', 26), leg('東京駅', 'train', '上越・北陸新幹線', 50)] + copy.deepcopy(tail)
m['trainRoutes']['note'] = ('💡 高崎駅まで新幹線で行き、吾妻線に乗り換えて長野原草津口駅へ。新宿からは大宮で新幹線に乗るのが安い。'
                            '上野・大宮からは特急「草津・四万」が長野原草津口駅まで乗り換えなしで走る（本数は少ない）。'
                            '長野原草津口駅からJRバス関東で草津温泉バスターミナルへ約25分・780円。'
                            '草津温泉〜白根火山のバスは、道路の状況により当面の間、全便運休している')
m['trainRoutes']['summaryNote'] = '※運賃はJR（新幹線は自由席）＋バス780円の合計'
sync(m, {'shinjuku': 5840, 'omiya': 5400, 'yokohama': 7140})
a, b, c = T(m)
faq(m, f'新幹線で高崎駅へ行き、吾妻線で長野原草津口駅へ、そこからJRバス関東で草津温泉まで約25分です。'
       f'新宿からは大宮で新幹線に乗り換えて{a}・5,840円、大宮から{b}・5,400円、横浜からは東京で新幹線に乗り換えて{c}・7,140円が目安です（乗り換えの待ち時間は別）。'
       '上野・大宮からは乗り換えなしの特急「草津・四万」もあります。車の場合は都心から約3時間45分が目安です。')

# 磐梯山（猪苗代駅からはタクシー。運賃は猪苗代駅まで）
m = N['bandai']
tail = [leg('郡山駅', 'train', 'JR磐越西線', 43), leg('猪苗代駅', 'taxi', 'タクシー', 25), leg('八方台登山口（バス路線なし、タクシー利用）')]
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR埼京線・湘南新宿ライン', 30), leg('大宮駅', 'train', '東北新幹線やまびこ', 51)] + copy.deepcopy(tail)
R['omiya']['legs'] = [leg('大宮駅', 'train', '東北新幹線やまびこ', 51)] + copy.deepcopy(tail)
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR上野東京ライン', 26), leg('東京駅', 'train', '東北新幹線やまびこ', 76)] + copy.deepcopy(tail)
m['trainRoutes']['summaryNote'] = '※運賃は猪苗代駅までの片道（新幹線は自由席。タクシー代は別）'
sync(m, {'shinjuku': 7700, 'omiya': 6820, 'yokohama': 9130})
a, b, c = T(m)
faq(m, f'東北新幹線で郡山駅へ行き、磐越西線で猪苗代駅へ。八方台登山口へのバス路線はなく、猪苗代駅からタクシーで約25分です。'
       f'新宿からは大宮で新幹線に乗り換えて{a}・7,700円、大宮から{b}・6,820円、横浜からは東京で新幹線に乗り換えて{c}・9,130円が目安です（運賃は猪苗代駅まで。タクシー代と乗り換えの待ち時間は別）。'
       '車の場合は都心から約4時間25分が目安です。')

# 飯縄山：長野駅〜飯綱登山口のバスは30分ではなく約47分。運賃はバス運賃が未確認のため据え置き
m = N['iizunasan']
old = (m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'])
for dep, _ in DEPS:
    hit = [l for l in m['trainRoutes']['routes'][dep]['legs'] if l['station'] == '長野駅']
    assert len(hit) == 1 and hit[0]['durationMin'] == 30, dep
    hit[0]['durationMin'] = 47
sync(m)
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']][0]
for o, k in zip(old, ('Shinjuku', 'Omiya', 'Yokohama')):
    assert hm(o) in hit['answer'], (o, hit['answer'])
    hit['answer'] = hit['answer'].replace(hm(o), hm(m['trainTime' + k]))
m['needsVerification'] = True
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['運賃合計が未検算。JRは長野まで新宿6,820円／大宮6,160円／横浜8,360円（自由席）。長野駅〜飯綱登山口のバス運賃が未確認']
N['takatsuma']['needsVerification'] = True
N['takatsuma']['verifyNotes'] = (N['takatsuma'].get('verifyNotes') or []) + ['運賃合計が未検算。JRは長野まで新宿6,820円／大宮6,160円／横浜8,360円（自由席）。長野駅〜戸隠キャンプ場のバス運賃（1,450円との情報）が未確認']
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('azumayasan', 'shirane_gunma', 'bandai', 'iizunasan'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
