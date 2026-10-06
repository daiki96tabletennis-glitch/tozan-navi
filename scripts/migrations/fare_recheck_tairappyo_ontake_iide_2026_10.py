#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""平標山・御嶽山・飯豊山の運賃と所要時間の検算（2026-10-06）。
出典：Yahoo!路線情報（2026-10-17 発）
  →越後湯沢：新宿6,160円（大宮で新幹線に乗換）／大宮5,830円／横浜7,030円。バス660円（南越後交通バス 2026年4月改正）
  →木曽福島：新宿8,160円／大宮7,850円／横浜7,850円。バス1,500円（王滝村公式 令和8年）
  →山都：新宿9,460円／大宮8,030円／横浜10,010円（東京06:40発やまびこ203号→郡山08:20、郡山08:29→会津若松09:41、会津若松09:48→山都10:22）
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
def sync(m, fares):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
        m['fare' + K] = fares[dep]
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = '2026-10-06'
def faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text
def drop_note(m, key):
    m['verifyNotes'] = [x for x in (m.get('verifyNotes') or []) if key not in x]

# 平標山
m = N['tairappyo']
tail = [leg('越後湯沢駅', 'bus', '南越後交通バス', 35), leg('平標登山口バス停')]
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR埼京線・湘南新宿ライン', 32), leg('大宮駅', 'train', '上越新幹線とき', 57)] + copy.deepcopy(tail)
R['omiya']['legs'] = [leg('大宮駅', 'train', '上越新幹線とき', 57)] + copy.deepcopy(tail)
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR上野東京ライン', 26), leg('東京駅', 'train', '上越新幹線', 73)] + copy.deepcopy(tail)
a = '上越新幹線は新宿発着がないため東京駅での乗り換えが必要。'
assert a in m['trainRoutes']['note']
m['trainRoutes']['note'] = m['trainRoutes']['note'].replace(a, '新宿からは大宮で上越新幹線に乗り換えるのが速くて安い。')
sync(m, {'shinjuku': 6820, 'omiya': 6490, 'yokohama': 7690})
faq(m, '新宿からは大宮で上越新幹線に乗り換えて越後湯沢駅へ行き、南越後交通バスで平標登山口まで約35分です。'
       f'新宿から{hm(m["trainTimeShinjuku"])}・6,820円、大宮から{hm(m["trainTimeOmiya"])}・6,490円、横浜から{hm(m["trainTimeYokohama"])}・7,690円が目安です（乗り換えの待ち時間は別）。'
       'バスは通年運行で1日8便です。')
drop_note(m, '旧バス運賃')

# 御嶽山
m = N['ontakesan']
sync(m, {'shinjuku': 9660, 'omiya': 9350, 'yokohama': 9350})
faq(m, '新宿から特急あずさ・特急しなの（塩尻乗換）で木曽福島駅へ行き、田の原線のバスで田の原へ向かいます。'
       f'新宿からは{hm(m["trainTimeShinjuku"])}・9,660円、大宮からは立川で特急あずさに乗り{hm(m["trainTimeOmiya"])}・9,350円、横浜からは八王子で特急あずさに乗り{hm(m["trainTimeYokohama"])}・9,350円が目安です。'
       'バスは2026年は7月4日〜10月18日の土日祝が中心で、1日2便と少ないため事前の時刻確認が必須です。')

# 飯豊山：新幹線・磐越西線の所要時間も実際の時刻に合わせる。運賃は山都駅まで（バス代は別）
m = N['iide']
tail = [leg('郡山駅', 'train', 'JR磐越西線快速', 72), leg('会津若松駅', 'train', 'JR磐越西線', 34),
        leg('山都駅', 'bus', '飯豊山登山アクセスバス（喜多方市・夏の金〜月曜のみ）', 45), leg('川入バス停', 'walk', '徒歩', 30), leg('御沢野営場（登山口）')]
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR中央線快速', 15), leg('東京駅', 'train', '東北新幹線やまびこ', 100)] + copy.deepcopy(tail)
R['omiya']['legs'] = [leg('大宮駅', 'train', '東北新幹線やまびこ', 75)] + copy.deepcopy(tail)
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR上野東京ライン', 26), leg('東京駅', 'train', '東北新幹線やまびこ', 100)] + copy.deepcopy(tail)
m['trainRoutes']['summaryNote'] = '※運賃は山都駅までの片道（バス代は別）。磐越西線は本数が少なく、乗り継ぎの待ち時間が長くなることがある'
sync(m, {'shinjuku': 9460, 'omiya': 8030, 'yokohama': 10010})
faq(m, '東北新幹線で郡山駅へ行き、磐越西線を会津若松で乗り継いで山都駅へ。山都駅からは喜多方市の飯豊山登山アクセスバス（夏の金〜月曜のみ）で川入へ向かいます。'
       f'新宿から{hm(m["trainTimeShinjuku"])}・9,460円、大宮から{hm(m["trainTimeOmiya"])}・8,030円、横浜から{hm(m["trainTimeYokohama"])}・10,010円が目安です（運賃は山都駅まで。乗り換えの待ち時間とバス代は別）。'
       '車の場合は都心から約5時間10分が目安です。')
drop_note(m, '運賃合計にバス代')
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['飯豊山登山アクセスバスの2026年の運行日・運賃']
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('tairappyo', 'ontakesan', 'iide'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
