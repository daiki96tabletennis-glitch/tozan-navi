#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""車の所要時間：マイカー規制などで登山口まで車で入れない16山（2026-10-10）。
「車の所要時間」は、車を置く手前の駐車場・乗り換え地点までとする（ユーザー了承済み）。
出典・測り方は drive_times_remeasure_2026_10.py と同じ（Googleマップの経路検索・渋滞を含まない標準の所要時間を5分単位に丸める）。
行き先は場所の名前で検索し、Googleマップが解決した場所を確認した：
  芦安 → 市営芦安第2駐車場（南アルプス市芦安芦倉1570）／戸台パーク（伊那市長谷黒河内396）／立山駅（立山町芦峅寺）
  さわんどバスターミナル（松本市安曇4462-52）／松本市乗鞍観光センター（松本市安曇鈴蘭4306-6）／尾瀬第1駐車場（片品村戸倉766）
  畑薙第一ダム（静岡市葵区田代。夏季臨時駐車場はその手前で、所要時間の差は約3分）／七倉山荘（大町市平高瀬入2118-37）
値は 新宿・大宮・横浜・大船・立川 の順の（分, km）。
"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-10'
HUBS = {
    '芦安駐車場': ([131, 170, 144, 140, 124], 153, ['kitadake', 'ainodake', 'noutori']),
    '戸台パーク': ([193, 233, 208, 203, 187], 225, ['komagatake', 'senjogatake']),
    '立山駅': ([337, 332, 359, 362, 339], 426, ['tateyama', 'tsurugi']),
    '沢渡（さわんどバスターミナル）': ([209, 253, 224, 219, 203], 253, ['yari', 'hotaka', 'chogatake']),
    '乗鞍高原観光センター': ([218, 262, 233, 228, 212], 259, ['norikura']),
    '尾瀬戸倉（尾瀬第1駐車場）': ([172, 166, 194, 196, 174], 175, ['shibutsu']),
    '畑薙第一ダム': ([253, 278, 239, 254, 263], 241, ['arakawadake', 'akaisidake']),
    '七倉': ([218, 247, 232, 227, 212], 268, ['eboshidake_kita', 'noguchigoro']),
}
FIELDS = [('driveTimeShinjuku', 'driveShinjuku'), ('driveTimeOmiya', 'driveOmiya'), ('driveTimeYokohama', 'driveYokohama'),
          ('driveOfuna', 'driveTime'), ('driveTimeTachikawa', 'driveTachikawa')]


def fmt(v):
    h, mi = divmod(v, 60)
    if not h:
        return '%d分' % mi
    return '%d時間%d分' % (h, mi) if mi else '%d時間' % h


TXT = re.compile(r'(新宿から(?:は)?車で約)\d+(?:時間(?:\d+分)?|分)')
n = n_txt = 0
for hub, (mins, km, ids) in HUBS.items():
    for mid in ids:
        m = N[mid]
        assert m.get('driveNeedsVerification') is True, mid
        for k, (a, b) in enumerate(FIELDS):
            new = 5 * round(mins[k] / 5)
            for f in (a, b):
                if f in m:
                    m[f] = new
        m['driveDistance'] = km
        m['driveTarget'] = hub
        m['driveCheckedAt'] = V
        del m['driveNeedsVerification']
        t = fmt(m['driveTimeShinjuku'])
        for f in ('metaDescription', 'ogDescription'):
            if isinstance(m.get(f), str):
                m[f], c = TXT.subn(lambda mm: mm.group(1) + t, m[f]); n_txt += c
        for q in m.get('faq') or []:
            q['answer'], c = TXT.subn(lambda mm: mm.group(1) + t, q['answer']); n_txt += c
        n += 1
assert n == 16 and not any(m.get('driveNeedsVerification') for m in D)
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('更新', n, '山／書き換えた文', n_txt)
