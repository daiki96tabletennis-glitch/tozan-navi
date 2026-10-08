#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""光岳：運賃からタクシー代の概算を外し、遠山郷線の時刻表リンクと注記を直す。空木岳：高速バスを窓口運賃に直す（2026-10-08）。
出典：
- 遠山郷線：飯田駅前〜かぐらの湯 700円、平日の朝は和田止まりで和田〜かぐらの湯は徒歩約12分（サイト運営者が確認）
  時刻表 https://www.shinnan.co.jp/sb/time_E1_02.html#link
- 高速バス 新宿〜伊那飯田線の運賃表（京王バス、窓口・車内販売運賃、2025年9月1日現在）
  飯田駅前：月〜木5,000円／金・祝前日・土日祝5,200円／繁忙日5,500円
  駒ヶ根バスターミナル：月〜木4,600円／金・祝前日・土日祝4,800円／繁忙日5,000円（WEB運賃は便ごとに変動）
- 大宮→新宿 528円、横浜→新宿 616円（JR・IC）
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


def sync(m, fares):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['fare' + K] = fares[dep]
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V
    m['fareCheckedAt'] = V


def faq(m):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    return hit[0]


# ── 光岳 ──
m = N['terkari']
URL = 'https://www.shinnan.co.jp/sb/time_E1_02.html#link'
tr = m['trainRoutes']
tr['note'] = ('💡 道の駅遠山郷から易老渡駐車場まで、予約制のタクシー送迎がある（2026年は7月1日〜11月8日）。'
              '行きは道の駅遠山郷を4時30分発、帰りは易老渡を13時発で、約1時間20分。'
              '料金は1台15,000〜20,000円（メーター制または時間制）。'
              '事前にタクシー会社へ直接予約する。'
              '芝沢ゲートでの乗り降りはできない。'
              '始発のバスでは間に合わないので、遠山郷か飯田市内に前泊する。'
              '飯田駅前〜かぐらの湯は信南交通「遠山郷線」で約1時間23分・700円。'
              '平日の朝の便は和田止まりで、和田からかぐらの湯まで歩く（徒歩約12分）。'
              '高速バス（新宿〜飯田駅前）の窓口運賃は月〜木5,000円、金・祝前日・土日祝5,200円、繁忙日5,500円')
tr['summaryNote'] = '※表示の運賃はかぐらの湯まで（高速バスは月〜木の窓口運賃で計算）。易老渡までのタクシー代（1台15,000〜20,000円）は別にかかる'
links = [l for l in tr['links'] if l['type'] == 'yahoo']
assert len(links) == 1
tr['links'] = links + [{'type': 'bus', 'label': 'バス時刻表（信南交通 遠山郷線）', 'url': URL},
                       {'type': 'bus', 'label': '易老渡アクセスタクシー情報（信州遠山郷）', 'url': 'https://tohyamago.com/archives/19377'}]
m['busScheduleLinks'] = [URL]
sync(m, {'shinjuku': 5700, 'omiya': 6228, 'yokohama': 6316})
m['verifyNotes'] = []
m['needsVerification'] = False
faq(m)['answer'] = ('光岳へは新宿から高速バスで飯田駅前まで約4時間10分、信南交通の遠山郷線でかぐらの湯（道の駅遠山郷）まで約1時間23分、そこから予約制タクシーで易老渡まで約1時間20分です。'
                    f'かぐらの湯までの運賃は新宿から{yen(m["fareShinjuku"])}、大宮から{yen(m["fareOmiya"])}、横浜から{yen(m["fareYokohama"])}が目安で、タクシー代は別にかかります（高速バスは月〜木の窓口運賃。大宮・横浜は新宿経由）。'
                    f'所要時間は新宿から{hm(m["trainTimeShinjuku"])}が目安です。'
                    'タクシーは早朝4時30分発の事前予約制（2026年は7月1日〜11月8日）のため前泊が必要です。マイカーは芝沢ゲートまでで、易老渡へは歩いて約1時間30分かかります。')

# ── 空木岳 ──
m = N['utsugi']
m['trainRoutes']['summaryNote'] = '※高速バス（新宿〜駒ヶ根）の窓口運賃は月〜木4,600円、金・祝前日・土日祝4,800円、繁忙日5,000円。表示は月〜木で計算。駒ヶ根駅前〜菅の台バスセンターの路線バスは380円'
sync(m, {'shinjuku': 4980, 'omiya': 5508, 'yokohama': 5596})
m['verifyNotes'] = [n for n in m['verifyNotes'] if '高速バス' not in n]
m['needsVerification'] = bool(m['verifyNotes'])
t = tuple(hm(m['trainTime' + K]) for _, K in DEPS)
faq(m)['answer'] = ('バスタ新宿から高速バスで駒ヶ根へ行き、路線バスで菅の台バスセンターへ向かいます。'
                    f'新宿からは{t[0]}・{yen(m["fareShinjuku"])}、大宮からは新宿乗継で{t[1]}・{yen(m["fareOmiya"])}、横浜からは{t[2]}・{yen(m["fareYokohama"])}が目安です（高速バスは月〜木の窓口運賃。金曜・土日祝や繁忙日は高くなります）。')

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ['terkari', 'utsugi']:
    m = N[i]
    print(i, m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'])
