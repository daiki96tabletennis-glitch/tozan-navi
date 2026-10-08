#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""七面山・笊ヶ岳・空木岳の運賃を検算する（2026-10-08）。
出典：
- 身延まで（Yahoo!路線情報）：新宿5,100円（あずさ＋身延線普通、3,520＋1,580）
  大宮4,540円（武蔵野線経由・立川で特急、乗車券3,520＋特急1,020）、横浜5,430円（新宿経由、3,850＋1,580）
- 早川町乗合バス 運賃表（早川町サイト）：身延駅〜七面山登山口・赤沢入口 600円、身延駅〜大島 600円。登山ザックは手回り品200円が別
- 笊ヶ岳：大島〜老平の乗合タクシーの運賃は確認できず、合計に含めない
- 空木岳：中央アルプス観光 路線バス運賃表 駒ヶ根駅前〜菅の台バスセンター 380円。
  高速バス（新宿〜駒ヶ根）は乗車日・便で変動（事業者サイトに固定額なし）。表示は最安の4,200円（比較サイトの掲載額）で、要確認のまま
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-08'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))


def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')


def yen(n):
    return format(n, ',') + '円'


def sync(m, fares, drop):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['fare' + K] = fares[dep]
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['verifyNotes'] = [n for n in (m.get('verifyNotes') or []) if not any(k in n for k in drop)]
    m['needsVerification'] = bool(m['verifyNotes'])
    m['mountainUpdated'] = V
    m['fareCheckedAt'] = V


def faq(m):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    return hit[0]


def times(m):
    return tuple(hm(m['trainTime' + K]) for _, K in DEPS)


F = {'shinjuku': 5700, 'omiya': 5140, 'yokohama': 6030}

m = N['nanaitsurasan']
sync(m, F, ['運賃合計が未検算'])
t = times(m)
faq(m)['answer'] = ('特急で甲府駅へ行き、JR身延線で身延駅へ、そこから早川町の「はやかわ乗合バス」で七面山登山口・赤沢入口バス停へ向かいます。バス停から表参道の登山口（羽衣）まではタクシーを使います。'
                    f'バス停までは新宿から{t[0]}・{yen(m["fareShinjuku"])}、大宮からは立川で特急に乗り{t[1]}・{yen(m["fareOmiya"])}、横浜からは新宿経由で{t[2]}・{yen(m["fareYokohama"])}が目安です（身延線は普通列車。タクシー代は別）。'
                    'バスは1日4本です。車の場合は都心から約2時間35分が目安です。')

m = N['yarigatake2']
m['trainRoutes']['summaryNote'] = '※表示の運賃は大島バス停まで（バスは身延駅〜大島600円）。大島〜老平の乗合タクシー代は別にかかる。早川町乗合バスは1日4往復で、乗合タクシーは前日19時までの予約制（角瀬タクシー運行）'
sync(m, F, ['運賃合計が未検算'])
m['verifyNotes'].append('大島〜老平（馬場）の乗合タクシーの運賃・時刻が未確認（町のPDFが読み取れない）')
m['needsVerification'] = True
t = times(m)
faq(m)['answer'] = ('特急で甲府駅へ行き、JR身延線（普通）で身延駅へ、身延駅から早川町乗合バスで大島バス停へ（約40分）、大島から予約制の乗合タクシー（前日19時までに要予約）で老平登山口（馬場停留所）へ向かいます（約20分）。'
                    f'新宿から{t[0]}、大宮から{t[1]}、横浜から{t[2]}が目安です。大島バス停までの運賃は新宿から{yen(m["fareShinjuku"])}、大宮から{yen(m["fareOmiya"])}、横浜から{yen(m["fareYokohama"])}で、乗合タクシー代は別にかかります。'
                    'バスは1日4往復のみのため事前の計画が必須です。')

m = N['utsugi']
m['trainRoutes']['summaryNote'] = '※高速バスの運賃は乗車日・便で変わる。表示は最も安い場合（4,200円〜）で計算。駒ヶ根駅前〜菅の台バスセンターの路線バスは380円'
sync(m, {'shinjuku': 4580, 'omiya': 5108, 'yokohama': 5196}, ['運賃合計が未検算'])
m['verifyNotes'].append('高速バス（新宿〜駒ヶ根）の運賃は変動制。最安4,200円は比較サイトの掲載額で、事業者サイトでは固定額を確認できない')
m['needsVerification'] = True
t = times(m)
faq(m)['answer'] = ('バスタ新宿から高速バスで駒ヶ根へ行き、路線バスで菅の台バスセンターへ向かいます。'
                    f'新宿からは{t[0]}・{yen(m["fareShinjuku"])}、大宮からは新宿乗継で{t[1]}・{yen(m["fareOmiya"])}、横浜からは{t[2]}・{yen(m["fareYokohama"])}が目安です（高速バスが最も安い日の場合。乗車日や便で変わります）。')

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ['nanaitsurasan', 'yarigatake2', 'utsugi']:
    m = N[i]
    print(i, m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['verifyNotes'])
