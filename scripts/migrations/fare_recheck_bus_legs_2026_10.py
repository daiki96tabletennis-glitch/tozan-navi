#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""バス区間の運賃が未確認だった7山を、事業者の資料で確定する（2026-10-07）。
出典：
- 焼岳：アルピコ交通「上高地線（予約優先）」運賃表 2026年4月17日改定 … 新島々営業所〜中の湯 2,400円
        鉄道は検証済みの上高地アクセス（新島々まで 7,440／7,130／7,130円）に揃える
- 飯縄山：アルピコ交通 70系統 戸隠線（2026年4月1日〜12月4日ダイヤ）長野駅〜飯綱登山口 47分・950円（NAVITIME、運賃表は2023年4月1日改定のまま）
- 高妻山：2026年の70系統は戸隠中社止まり。戸隠キャンプ場へ直通するのは予約制「観光特急戸隠線」
        （2026年4月1日〜12月4日予定、長野駅6:50→戸隠キャンプ場7:55、2,500円）
- 美ヶ原：信州美ヶ原高原直行バス 松本駅8:15→美ヶ原自然保護センター9:35、1,500円（松本市観光サイト・公式サイト）
        松本まで 新宿6,730円（Yahoo!路線情報）／大宮・横浜6,420円（新島々までの検証額 7,130円 − 上高地線710円）
- 石割山：富士急バス「ふじっ湖号」運賃表（2026年）河口湖駅〜山中湖平野 1,050円、約55分（NAVITIME）
        鉄道は十二ヶ岳と同じ検証済みの経路（河口湖まで 2,569／2,756／2,756円）
- 三ツ峠山：天下茶屋線 河口湖駅〜三ッ峠登山口 25分・840円（NAVITIME）。富士回遊は新宿から4,189円、
        大宮・横浜は乗車券の差額だけ変わり4,376円（特急料金1,620円は同じ）
- 苗場山：タクシー代の概算を運賃から外し、越後湯沢駅までの電車代だけにする（6,160／5,830／7,030円）
"""
import json, os, sys, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
AC = json.load(open(os.path.join(ROOT, 'data', 'accesses.json'), encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-07'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))


def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')


def yen(n):
    return format(n, ',') + '円'


def leg(station, icon, line, minutes):
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}


def sync(m, fares, drop_notes):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['fare' + K] = fares[dep]
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    keep = [n for n in (m.get('verifyNotes') or []) if not any(k in n for k in drop_notes)]
    m['verifyNotes'] = keep
    m['needsVerification'] = bool(keep)
    m['mountainUpdated'] = V
    m['fareCheckedAt'] = V


def set_faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text


def times(m):
    return tuple(hm(m['trainTime' + K]) for _, K in DEPS)


# ── 焼岳 ──
m = N['yakedake']
R = copy.deepcopy(AC['kamikochi']['trainRoutes']['routes'])
for dep in R:
    assert R[dep]['legs'][-2]['station'] == '新島々駅'
    R[dep]['legs'][-2]['durationMin'] = 55
    R[dep]['legs'][-1] = {'station': '中の湯バス停'}
m['trainRoutes']['routes'] = R
m['trainRoutes']['lineName'] = 'JR特急あずさ・松本電鉄上高地線・アルピコ交通バス'
m['trainRoutes']['summaryNote'] = '※バスは新島々〜中の湯が2,400円（2026年4月17日改定）。運行は2026年4月17日〜11月15日'
sync(m, {'shinjuku': 9840, 'omiya': 9530, 'yokohama': 9530}, ['運賃合計が未検算'])
t = times(m)
set_faq(m, '特急あずさで松本駅へ行き、松本電鉄上高地線で新島々駅へ、そこから上高地行きのアルピコ交通バスで中の湯バス停まで約55分です。'
        f'新宿から{t[0]}・{yen(m["fareShinjuku"])}、大宮からは立川で特急に乗り{t[1]}・{yen(m["fareOmiya"])}、横浜からは八王子で特急に乗り{t[2]}・{yen(m["fareYokohama"])}が目安です（乗り換えの待ち時間は別）。'
        'バスは2026年は予約優先制で、冬は運休します。車の場合は都心から約4時間40分が目安です。')

# ── 飯縄山 ──
m = N['iizunasan']
sync(m, {'shinjuku': 7770, 'omiya': 7110, 'yokohama': 9310}, ['運賃合計が未検算'])
t = times(m)
set_faq(m, '北陸新幹線で長野駅へ行き、アルピコ交通バス「戸隠線」（ループ橋経由）で飯綱登山口バス停まで約47分です。'
        f'新宿から{t[0]}・{yen(m["fareShinjuku"])}、大宮から{t[1]}・{yen(m["fareOmiya"])}、横浜から{t[2]}・{yen(m["fareYokohama"])}が目安です（新幹線は自由席、乗り換えの待ち時間は別）。'
        'バスは1日5本ほどです。車の場合は都心から約3時間50分が目安です。')
m['trainInfo'] = '新宿→東京→長野駅（北陸新幹線）→戸隠線バス約47分→飯綱登山口'

# ── 高妻山 ──
m = N['takatsuma']
R = m['trainRoutes']['routes']
for dep in R:
    b = R[dep]['legs'][-2]
    assert b['station'] == '長野駅'
    b['method']['line'] = 'アルピコ交通「観光特急戸隠線」（予約制）'
    b['durationMin'] = 65
m['trainRoutes']['lineName'] = 'JR北陸新幹線・アルピコ交通「観光特急戸隠線」'
m['trainRoutes']['badge'] = {'type': None, 'style': 'background:#fde8d8;color:#8a5010;', 'icon': 'warn', 'label': '季節運行（予約制）'}
m['trainRoutes']['note'] = ('💡 高妻山の登山口は戸隠キャンプ場。'
                            '長野駅から戸隠キャンプ場へ直通するのは予約制の「観光特急戸隠線」で、約65分・片道2,500円。'
                            '2026年は4月1日〜12月4日（予定）の運行。'
                            '予約は乗車日の1か月前からインターネットで受け付け、空席があれば予約なしでも乗れる。'
                            '交通系ICカードは使えない。'
                            '路線バスの戸隠線（70系統）は戸隠中社止まりで、その先は観光連絡バス（2026年の時刻表では土休日運転）に乗り換える。'
                            '同じ沿線の「飯綱登山口」は飯縄山の登山口で別の山')
m['trainRoutes']['summaryNote'] = '※冬（12月上旬〜3月）は観光特急が運休し、戸隠キャンプ場までのバスはない'
m['annualItems'] = [{'kind': 'transport', 'label': '長野駅〜戸隠キャンプ場の観光特急戸隠線（予約制）',
                     'validFrom': '2026-04-01', 'validTo': '2026-12-04', 'seasonYear': 2026,
                     'sourceUrl': 'https://www.alpico.co.jp/traffic/express/express_togakushi/',
                     'lastVerified': V, 'note': '終了日は予定'}]
sync(m, {'shinjuku': 9320, 'omiya': 8660, 'yokohama': 10860}, ['運賃合計が未検算'])
t = times(m)
set_faq(m, '北陸新幹線で長野駅へ行き、予約制のアルピコ交通「観光特急戸隠線」で戸隠キャンプ場まで約65分です。'
        f'新宿から{t[0]}・{yen(m["fareShinjuku"])}、大宮から{t[1]}・{yen(m["fareOmiya"])}、横浜から{t[2]}・{yen(m["fareYokohama"])}が目安です（新幹線は自由席、乗り換えの待ち時間は別）。'
        '観光特急は2026年は4月1日〜12月4日（予定）の運行です。車の場合は都心から約4時間25分が目安です。')

# ── 美ヶ原 ──
m = N['utsukushigahara']
R = m['trainRoutes']['routes']
for dep in R:
    b = R[dep]['legs'][-2]
    assert b['station'] == '松本駅'
    b['method']['line'] = '信州美ヶ原高原直行バス（完全予約制）'
    b['durationMin'] = 80
    R[dep]['legs'][-1] = {'station': '美ヶ原自然保護センター'}
m['trainRoutes']['note'] = ('💡 「信州美ヶ原高原直行バス」は松本駅アルプス口8:15発・13:15発の1日2便で、美ヶ原自然保護センターまで約1時間20分。'
                            '片道1,500円（乗車2日前までの予約は1,200円・席数限定）。'
                            '完全予約制で、空席があれば出発15分前まで予約できる。'
                            '支払いはクレジットカードの事前決済のみ。'
                            '2026年は6月6日〜10月12日の土日祝と、7月13日〜8月31日の毎日')
m['trainRoutes']['summaryNote'] = '※直行バスは季節運行で1日2便。山本小屋・美術館側へは行かない'
sync(m, {'shinjuku': 8230, 'omiya': 7920, 'yokohama': 7920}, ['運賃'])
t = times(m)
set_faq(m, 'JR松本駅から予約制の「信州美ヶ原高原直行バス」で美ヶ原自然保護センターへ向かいます（約1時間20分）。'
        f'新宿からは特急あずさで{t[0]}・{yen(m["fareShinjuku"])}、大宮からは立川で特急あずさに乗り{t[1]}・{yen(m["fareOmiya"])}、横浜からは八王子で特急あずさに乗り{t[2]}・{yen(m["fareYokohama"])}が目安です（乗り換えの待ち時間は別）。'
        '直行バスは2026年は6月6日〜10月12日の土日祝と、7月13日〜8月31日の毎日の運行です。')

# ── 石割山 ──
m = N['ishiwariyama']
BUS = '富士急バス「ふじっ湖号」'
m['trainRoutes']['routes'] = {
    'shinjuku': {'legs': [leg('新宿駅', 'train', 'JR中央線（高尾乗換）', 104), leg('大月駅', 'train', '富士急行線', 59),
                          leg('河口湖駅', 'bus', BUS, 55), {'station': '山中湖平野バス停'}]},
    'yokohama': {'legs': [leg('横浜駅', 'train', 'JR横浜線・中央線（八王子乗換）', 112), leg('大月駅', 'train', '富士急行線', 59),
                          leg('河口湖駅', 'bus', BUS, 55), {'station': '山中湖平野バス停'}]},
    'omiya': {'legs': [leg('大宮駅', 'train', 'JR埼京線・武蔵野線・中央線（西国分寺・高尾乗換）', 120), leg('大月駅', 'train', '富士急行線', 59),
                       leg('河口湖駅', 'bus', BUS, 55), {'station': '山中湖平野バス停'}]},
}
m['trainRoutes']['lineName'] = 'JR中央線・富士急行線・富士急バス「ふじっ湖号」'
m['trainRoutes']['summaryNote'] = '※ふじっ湖号は河口湖駅〜山中湖平野が約55分・1,050円。富士山駅からも乗れる'
sync(m, {'shinjuku': 3619, 'omiya': 3806, 'yokohama': 3806}, ['バス運賃'])
t = times(m)
set_faq(m, 'JR中央線で大月駅へ行き、富士急行線で河口湖駅へ、そこから富士急バス「ふじっ湖号」で山中湖平野バス停まで約55分です。'
        f'新宿から{t[0]}・{yen(m["fareShinjuku"])}、大宮から{t[1]}・{yen(m["fareOmiya"])}、横浜からは八王子経由で{t[2]}・{yen(m["fareYokohama"])}が目安です（特急を使わない場合。乗り換えの待ち時間は別）。')
m['trainInfo'] = '新宿→大月→河口湖駅（富士急行線）→ふじっ湖号 約55分→山中湖平野'

# ── 三ツ峠山 ──
m = N['mitsutoge']
m['trainRoutes']['summaryNote'] = '※天下茶屋線は本数がごく少ない（河口湖駅9:50発）。2026年10月1日のダイヤ改正後の時刻は富士急バスで確認を'
sync(m, {'shinjuku': 5029, 'omiya': 5216, 'yokohama': 5216}, ['バス運賃'])
m['verifyNotes'].append('天下茶屋線の2026年10月1日ダイヤ改正後の時刻・運行日が未確認（運賃840円はNAVITIME、富士急の古いモデルコースのページは730円表記）')
m['needsVerification'] = True
t = times(m)
set_faq(m, '新宿駅からJR中央線・富士急行線直通特急「富士回遊」で河口湖駅へ（約1時間55分）、河口湖駅から富士急バス「天下茶屋線」で三つ峠登山口バス停へ（約25分）。'
        f'新宿から{t[0]}・{yen(m["fareShinjuku"])}、大宮から{t[1]}・{yen(m["fareOmiya"])}、横浜から{t[2]}・{yen(m["fareYokohama"])}が目安です（乗り換えの待ち時間は別）。'
        '天下茶屋線は本数がごく少ないため、時刻を確認してから出かけてください。')

# ── 苗場山 ──
m = N['naeba']
m['trainRoutes']['summaryNote'] = '※表示の運賃は越後湯沢駅までの電車代。タクシー代（片道約4,000円/台）は別にかかる。和田小屋・祓川への定期路線バスはない'
sync(m, {'shinjuku': 6160, 'omiya': 5830, 'yokohama': 7030}, ['運賃'])
t = times(m)
set_faq(m, '上越新幹線で越後湯沢駅へ行き、タクシーで祓川登山口駐車場へ向かいます（約25分、路線バスはありません）。'
        f'越後湯沢駅までの電車代は新宿から{yen(m["fareShinjuku"])}、大宮から{yen(m["fareOmiya"])}、横浜から{yen(m["fareYokohama"])}で、タクシー代は別にかかります（新幹線は自由席）。'
        f'所要時間は新宿から{t[0]}、大宮から{t[1]}、横浜から{t[2]}が目安です（乗り換えの待ち時間は別）。車の場合は都心から約3時間40分が目安です。')
m['trainInfo'] = '新宿→東京→越後湯沢（上越新幹線）→タクシー約25分→祓川登山口駐車場'

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ['yakedake', 'iizunasan', 'takatsuma', 'utsukushigahara', 'ishiwariyama', 'mitsutoge', 'naeba']:
    m = N[i]
    print(i, m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['needsVerification'], m['verifyNotes'])
