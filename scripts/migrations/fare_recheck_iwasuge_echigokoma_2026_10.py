#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""岩菅山・越後駒ヶ岳の経路と運賃を直す。あわせて「横浜→東京 東海道線18分」を26分に直す（2026-10-08）。
出典：
- 岩菅山：長電バス 奥志賀高原線の停留所一覧（2026年4月7日改正）に「聖平入口」は無い。最寄りは一ノ瀬スキー場
  NAVITIME 湯田中駅→一ノ瀬スキー場 46分・1,450円、Yahoo!路線情報 長野→湯田中 特急44〜45分・1,760円（乗車券1,660＋特急100）
  長野まで 新宿6,820円／大宮6,160円／横浜8,360円（検証済み）
- 越後駒ヶ岳：南越後交通バスの公表路線は「浦佐駅東口〜銀山平〜奥只見ダム」（2026年6月1日改正、6/1〜11/3の土日祝と8/13〜16）で、
  小出駅〜枝折峠の路線は事業者サイトで確認できない。運賃は小出駅までの電車代だけにする
  Yahoo!路線情報 →小出（浦佐乗換）新宿6,820円（大宮乗車）／大宮6,490円／横浜8,800円（東京乗車）
- 横浜→東京：他の18山は24〜29分。18分は誤り（巻機山・岩菅山・飯縄山・苗場山・高妻山）
"""
import json, os, sys, re
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


def leg(station, icon, line, minutes):
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}


def sync(m, fares=None, drop=()):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        if fares:
            m['fare' + K] = fares[dep]
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    keep = [n for n in (m.get('verifyNotes') or []) if not any(k in n for k in drop)]
    m['verifyNotes'] = keep
    m['mountainUpdated'] = V


def faq(m):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    return hit[0]


def times(m):
    return tuple(hm(m['trainTime' + K]) for _, K in DEPS)


# ── 横浜→東京 18分→26分（岩菅山以外の4山。FAQの横浜発の時間も直す）──
for mid in ['makihata', 'iizunasan', 'naeba', 'takatsuma']:
    m = N[mid]
    L = m['trainRoutes']['routes']['yokohama']['legs']
    assert L[0]['station'] == '横浜駅' and L[1]['station'] == '東京駅' and L[0]['durationMin'] == 18, mid
    old = hm(m['trainTimeYokohama'])
    L[0]['durationMin'] = 26
    sync(m)
    q = faq(m)
    q['answer'], c = re.subn(old, hm(m['trainTimeYokohama']), q['answer'])
    assert c == 1, (mid, old, q['answer'])

# ── 岩菅山 ──
m = N['iwasugesan']
R = m['trainRoutes']['routes']
for dep in R:
    L = R[dep]['legs']
    assert L[-3]['station'] == '長野駅' and L[-2]['station'] == '湯田中駅', dep
    L[-3]['method']['line'] = '長野電鉄 特急（特急料金100円）'
    L[-2]['method']['line'] = '長電バス「奥志賀高原線」'
    L[-2]['durationMin'] = 46
    L[-1] = {'station': '一ノ瀬スキー場バス停'}
Y = R['yokohama']['legs']
assert Y[0]['durationMin'] == 18
Y[0]['durationMin'] = 26
m['trainRoutes']['note'] = ('💡 長野駅から長野電鉄の特急で湯田中駅へ行き、長電バス「奥志賀高原線」（奥志賀高原ホテル行き）で一ノ瀬スキー場バス停へ。'
                            'バスは約46分・1,450円。'
                            '長野電鉄は乗車券1,660円に特急料金100円がかかる（普通列車なら特急料金は不要で約1時間10分）。'
                            '季節によってダイヤが変わるため、時刻は長電バスの時刻表で確認を')
m['trainRoutes']['summaryNote'] = '※「一ノ瀬スキー場」バス停から登山口まで徒歩約30分（約2km）。「聖平入口」というバス停は無い'
sync(m, {'shinjuku': 10030, 'omiya': 9370, 'yokohama': 11570})
m['fareCheckedAt'] = V
t = times(m)
faq(m)['answer'] = ('北陸新幹線で長野駅へ行き、長野電鉄の特急で湯田中駅へ、そこから長電バス「奥志賀高原線」で一ノ瀬スキー場バス停まで約46分です。バス停から登山口までは徒歩約30分です。'
                    f'新宿から{t[0]}・{yen(m["fareShinjuku"])}、大宮から{t[1]}・{yen(m["fareOmiya"])}、横浜から{t[2]}・{yen(m["fareYokohama"])}が目安です（新幹線は自由席、乗り換えの待ち時間は別）。'
                    '車の場合は都心から約3時間30分が目安です。')

# ── 越後駒ヶ岳 ──
m = N['echigokoma']
BUS = '南越後交通バス（2026年の運行は未確認）'
END = {'station': '枝折峠登山口'}
m['trainRoutes']['routes'] = {
    'shinjuku': {'legs': [leg('新宿駅', 'train', 'JR埼京線', 26), leg('大宮駅', 'train', '上越新幹線とき', 55), leg('浦佐駅', 'train', 'JR上越線', 10),
                          leg('小出駅', 'bus', BUS, 65), dict(END)]},
    'yokohama': {'legs': [leg('横浜駅', 'train', 'JR東海道線', 26), leg('東京駅', 'train', '上越新幹線とき', 79), leg('浦佐駅', 'train', 'JR上越線', 10),
                          leg('小出駅', 'bus', BUS, 65), dict(END)]},
    'omiya': {'legs': [leg('大宮駅', 'train', '上越新幹線とき', 55), leg('浦佐駅', 'train', 'JR上越線', 10),
                       leg('小出駅', 'bus', BUS, 65), dict(END)]},
}
m['trainRoutes']['badge'] = {'type': None, 'style': 'background:#fde8d8;color:#8a5010;', 'icon': 'warn', 'label': 'バスの運行は未確認'}
m['trainRoutes']['note'] = ('💡 小出駅〜枝折峠のバスは、2026年の運行を事業者の時刻表で確認できていない。'
                            '南越後交通バスが公表しているのは浦佐駅東口〜銀山平〜奥只見ダムの急行バスで、枝折峠は通らない。'
                            'この急行バスは2026年6月1日〜11月3日の土日祝と8月13日〜16日の運行。'
                            '枝折峠へはタクシーを使うか、銀山平や駒の湯温泉での前泊を前提に計画を。'
                            '出かける前に南越後交通バス小出営業所（025-792-8114）で確認を')
m['trainRoutes']['summaryNote'] = '※表示の運賃は小出駅までの電車代。小出駅から先の交通費は別にかかる'
m['annualItems'] = [{'kind': 'transport', 'label': '浦佐駅東口〜銀山平〜奥只見ダムの急行バス（枝折峠は通らない）',
                     'validFrom': '2026-06-01', 'validTo': '2026-11-03', 'seasonYear': 2026,
                     'sourceUrl': 'https://www.minamiechigo.co.jp/pdf/koide/jikoku/holiday/okutadamiR8-4-all-h.pdf',
                     'lastVerified': V, 'note': '土日祝と8月13日〜16日'}]
sync(m, {'shinjuku': 6820, 'omiya': 6490, 'yokohama': 8800}, ['運賃合計が未検算'])
m['verifyNotes'].append('小出駅〜枝折峠のバス（従来「夏季1日1便・680円・65分」と記載）が2026年に運行しているか未確認。事業者サイトの路線一覧に無い。滝雲シャトルバスも未確認')
m['needsVerification'] = True
m['fareCheckedAt'] = V
t = times(m)
faq(m)['answer'] = ('上越新幹線で浦佐駅へ行き、JR上越線で小出駅へ向かいます。小出駅から枝折峠へのバスは2026年の運行を確認できていないため、タクシーの利用か前泊を前提に計画してください。'
                    f'小出駅までの電車代は新宿から{yen(m["fareShinjuku"])}、大宮から{yen(m["fareOmiya"])}、横浜から{yen(m["fareYokohama"])}です（新幹線は自由席。小出駅から先は別）。'
                    '車の場合は都心から約5時間20分が目安です。')
m['trainInfo'] = '新宿→大宮→浦佐（上越新幹線）→小出（上越線）→枝折峠（バスの運行は未確認）'

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ['makihata', 'iizunasan', 'naeba', 'takatsuma', 'iwasugesan', 'echigokoma']:
    m = N[i]
    print(i, m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'])
