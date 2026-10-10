#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""車の所要時間を全山で測り直す（2026-10-10）。

出典：Googleマップの経路検索（車）。出発地は新宿駅・大宮駅・横浜駅・大船駅・立川駅、行き先は各山の地図ボタンの座標（gmapUrl。無い山は lat/lng）。
使う値：渋滞を含まない標準の所要時間（drive_times_gmaps_2026_10.json の base）を5分単位に丸める。
        取得時点の渋滞込みの値（traffic）は土曜の渋滞で大きくぶれるため使わない（記録だけ残す）。
対象外（値を変えず driveNeedsVerification を付ける）：マイカー規制・一般車が入れない場所が行き先になっている16山。
        どこまでを「車の所要時間」とするか（手前の駐車場まで、など）を決めてから測る。
あわせて、meta / og の説明文とFAQにある「新宿から車で約◯時間◯分」を新しい値にそろえる。
"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
G = json.load(open(os.path.join(HERE, 'drive_times_gmaps_2026_10.json'), encoding='utf-8'))['data']
V = '2026-10-10'
EXCLUDE = {'kitadake', 'ainodake', 'noutori', 'komagatake', 'senjogatake', 'tateyama', 'tsurugi', 'yari', 'hotaka', 'chogatake',
           'norikura', 'shibutsu', 'arakawadake', 'akaisidake', 'eboshidake_kita', 'noguchigoro'}
# 出発地の順（新宿・大宮・横浜・大船・立川）→ 書き込むフィールド（2系統）
FIELDS = [('driveTimeShinjuku', 'driveShinjuku'), ('driveTimeOmiya', 'driveOmiya'), ('driveTimeYokohama', 'driveYokohama'),
          ('driveOfuna', 'driveTime'), ('driveTimeTachikawa', 'driveTachikawa')]


def fmt(v):
    h, mi = divmod(v, 60)
    if not h:
        return '%d分' % mi
    return '%d時間%d分' % (h, mi) if mi else '%d時間' % h


TXT = re.compile(r'(新宿から(?:は)?車で約)\d+(?:時間(?:\d+分)?|分)')
n_m = n_v = n_txt = 0
for m in D:
    mid = m['id']
    if mid in EXCLUDE:
        m['driveNeedsVerification'] = True
        continue
    g = G[mid]
    for k, (a, b) in enumerate(FIELDS):
        new = 5 * round(g['base'][k] / 5)
        for f in (a, b):
            if f in m and m[f] != new:
                n_v += 1
            if f in m:
                m[f] = new
    m['driveDistance'] = g['km'][0]
    m['driveCheckedAt'] = V
    m.pop('driveNeedsVerification', None)
    new_txt = fmt(m['driveTimeShinjuku'])
    for f in ('metaDescription', 'ogDescription'):
        if isinstance(m.get(f), str):
            m[f], c = TXT.subn(lambda mm: mm.group(1) + new_txt, m[f])
            n_txt += c
    for q in m.get('faq') or []:
        q['answer'], c = TXT.subn(lambda mm: mm.group(1) + new_txt, q['answer'])
        n_txt += c
    n_m += 1
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('更新した山', n_m, '／変わった値', n_v, '／書き換えた文', n_txt, '／対象外', len(EXCLUDE))
