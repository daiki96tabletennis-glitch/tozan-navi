#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""甲府駅・韮崎駅を起点にする5山の運賃検算（2026-10-06）。
出典：Yahoo!路線情報（2026-10-17 発）
  →甲府：新宿4,000円（あずさ1号 07:00→08:27）／大宮4,000円（新宿乗換）／横浜3,440円（横浜線で八王子、あずさ5号 08:33→09:28）
  →韮崎：新宿4,330円（あずさ1号 07:00→08:36）／大宮4,330円／横浜3,770円（八王子・甲府乗換、09:50着）
大宮・横浜発が「新宿発＋770円」で揃っていたのは誤り。大宮は新宿発と同額、横浜は八王子乗車で安くなる。
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
def yokohama_via_hachioji(m, to_nirasaki):
    """横浜発を、横浜線で八王子に出て特急あずさに乗る経路にする"""
    legs = m['trainRoutes']['routes']['yokohama']['legs']
    gw = '韮崎駅' if to_nirasaki else '甲府駅'
    idx = [i for i, l in enumerate(legs) if l['station'] == gw]
    assert len(idx) == 1, m['id']
    head = [leg('横浜駅', 'train', 'JR横浜線', 60), leg('八王子駅', 'train', 'JR特急あずさ', 55)]
    if to_nirasaki:
        head.append(leg('甲府駅', 'train', 'JR中央本線（普通）', 13))
    m['trainRoutes']['routes']['yokohama']['legs'] = head + legs[idx[0]:]

# 北岳（運賃には利用者協力金300円を含める従来の扱いを維持）
m = N['kitadake']
yokohama_via_hachioji(m, False)
m['trainRoutes']['summaryNote'] = '※運賃はJR＋バス1,990円＋利用者協力金300円の合計。大宮は新宿で、横浜は八王子で特急に乗る'
F = {'shinjuku': 6290, 'omiya': 6290, 'yokohama': 5730}
sync(m, F)
faq(m, '新宿駅から特急あずさ・かいじで甲府駅へ（約1時間45分）、甲府駅から山梨交通の南アルプス登山バスで広河原へ（乗換不要、約1時間50分）。'
       'バスは別途、利用者協力金が必要で、マイカー規制期間（2026年は6月26日〜11月3日）以外は冬期閉鎖されます。'
       f'新宿から片道6,290円・{hm(m["trainTimeShinjuku"])}、大宮から6,290円・{hm(m["trainTimeOmiya"])}、横浜からは八王子で特急に乗り5,730円・{hm(m["trainTimeYokohama"])}が目安です（協力金込み。乗り換えの待ち時間は別）。')

# 農鳥岳・間ノ岳は北岳と同じバス。経路と運賃を北岳に揃える
for mid, extra in (('noutori', None), ('ainodake', None)):
    x = N[mid]; k = N['kitadake']
    note_tail = ''
    if mid == 'noutori':
        note_tail = ('。農鳥岳は広河原から北岳・間ノ岳を経て歩き、奈良田（大門沢）へ下るのが一般的。'
                     '下山後は奈良田温泉から、はやかわ乗合バスで身延駅へ出る（予約の要否は早川町に確認）')
    x['trainRoutes'] = copy.deepcopy(k['trainRoutes'])
    x['trainRoutes']['note'] = k['trainRoutes']['note'].rstrip('。') + note_tail
    sync(x, F)
    for key in ('busLinks', 'busScheduleLinks'):
        x[key] = copy.deepcopy(k.get(key))
faq(N['noutori'], '農鳥岳は広河原から北岳・間ノ岳を経て縦走し、奈良田へ下山するのが一般的です。行きは新宿から特急あずさ・かいじで甲府駅へ、山梨交通の南アルプス登山バスで広河原まで約1時間50分です。'
    f'新宿から{hm(N["noutori"]["trainTimeShinjuku"])}・6,290円、大宮から{hm(N["noutori"]["trainTimeOmiya"])}・6,290円、横浜から{hm(N["noutori"]["trainTimeYokohama"])}・5,730円が目安です（利用者協力金込み）。'
    '下山後は奈良田温泉から、はやかわ乗合バスで身延駅へ出ます。')
faq(N['ainodake'], '間ノ岳へは広河原から北岳を経て登ります。新宿から特急あずさ・かいじで甲府駅へ、山梨交通の南アルプス登山バスで広河原まで約1時間50分です。'
    f'新宿から{hm(N["ainodake"]["trainTimeShinjuku"])}・6,290円、大宮から{hm(N["ainodake"]["trainTimeOmiya"])}・6,290円、横浜から{hm(N["ainodake"]["trainTimeYokohama"])}・5,730円が目安です（利用者協力金込み）。'
    '車の場合は都心から約3時間10分が目安です。')

# 茅ヶ岳（バス700円）
m = N['kayagatake']
yokohama_via_hachioji(m, True)
sync(m, {'shinjuku': 5030, 'omiya': 5030, 'yokohama': 4470})
faq(m, '新宿駅から特急あずさで韮崎駅へ（約1時間45分）、山梨峡北交通バス「韮崎深田公園線」で約25分、深田記念公園バス停から登山口まで徒歩すぐです。'
       '運賃は新宿発5,030円、大宮発5,030円、横浜発は八王子で特急に乗り4,470円が目安です。車の場合は都心から約2時間10分が目安です。')

# 瑞牆山（バス2,100円）。新宿発は韮崎までの運賃ではなく甲府までの運賃で計算されていた
m = N['mizugaki']
yokohama_via_hachioji(m, True)
sync(m, {'shinjuku': 6430, 'omiya': 6430, 'yokohama': 5870})
faq(m, f'新宿駅から特急あずさで韮崎駅へ行き、山梨峡北交通「韮崎瑞牆線」でみずがき山荘まで約1時間20分です。'
       f'新宿から{hm(m["trainTimeShinjuku"])}・6,430円、大宮から{hm(m["trainTimeOmiya"])}・6,430円、横浜からは八王子で特急に乗り{hm(m["trainTimeYokohama"])}・5,870円が目安です。'
       '韮崎駅〜みずがき山荘のバスは2026年は4月4日〜11月23日の運行のため、時期に注意してください。')
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('kitadake', 'noutori', 'ainodake', 'kayagatake', 'mizugaki'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
