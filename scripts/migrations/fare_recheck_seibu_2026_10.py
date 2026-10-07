#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""西武池袋線・西武秩父線の組の運賃検算（方針B：池袋で西武線に乗り換える今の経路のまま）。2026-10-07
出典：Yahoo!路線情報（2026-10-17 発、IC運賃）
  池袋まで（JR）：新宿199円／大宮440円／横浜715円
  池袋から（西武）：飯能557円（急行49分）／高麗627円／正丸735円／芦ヶ久保758円／西武秩父800円＋特急ちちぶ900円（約1時間20分）
  国際興業バス：飯能駅〜河又名栗湖入口 690円・約40分
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-07'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
JR = {'shinjuku': 199, 'omiya': 440, 'yokohama': 715}
def leg(station, icon, line, minutes):
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}
def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')
def resync(m, after_ikebukuro):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
        m['fare' + K] = JR[dep] + after_ikebukuro
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V; m['fareCheckedAt'] = V
def faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text
def F(m): return f'{m["fareShinjuku"]:,}円', f'{m["fareOmiya"]:,}円', f'{m["fareYokohama"]:,}円'
def T(m): return hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama'])
def set_line(m, dep, station, line, minutes):
    hit = [l for l in m['trainRoutes']['routes'][dep]['legs'] if l['station'] == station]
    assert len(hit) == 1, (m['id'], dep, station)
    hit[0]['method']['line'] = line; hit[0]['durationMin'] = minutes

# 天覧山・多峯主山（飯能、徒歩）：大宮発だけ特急の経路になっていた
m = N['tenzandake']
for dep, _ in DEPS: set_line(m, dep, '池袋駅', '西武池袋線', 49)
m['trainRoutes']['summaryNote'] = '※運賃はJR（池袋まで）＋西武池袋線557円の合計'
resync(m, 557); a, b, c = T(m); x, y, z = F(m)
faq(m, f'池袋で西武池袋線に乗り換えて飯能駅へ行き、駅から歩いて約20分で登山口です。新宿から{a}・{x}、大宮から{b}・{y}、横浜から{c}・{z}が目安です（徒歩を含む）。車の場合は都心から約1時間40分が目安です。')

# 棒ノ折山（飯能からバス690円・約40分）
m = N['bonori']
for dep, _ in DEPS:
    set_line(m, dep, '池袋駅', '西武池袋線', 49)
    set_line(m, dep, '飯能駅', '国際興業バス', 40)
m['trainRoutes']['summaryNote'] = '※運賃はJR＋西武池袋線557円＋バス690円の合計。バスは1時間に1本程度で、本数が少ない'
resync(m, 557 + 690); a, b, c = T(m); x, y, z = F(m)
faq(m, f'池袋で西武池袋線に乗り換えて飯能駅へ行き、国際興業バスで河又名栗湖入口まで約40分です。新宿から{a}・{x}、大宮から{b}・{y}、横浜から{c}・{z}が目安です。車の場合は都心から約1時間40分が目安です。')

# 丸山・二子山（芦ヶ久保、徒歩）：大宮・横浜発の額が他の西武線の山と揃っていなかった
for mid, walk, goal in (('maruyama_okubusuma', 30, '丸山登山口'), ('futagoyama_okumusa', 15, '二子山登山口')):
    m = N[mid]
    m['trainRoutes']['summaryNote'] = '※運賃はJR（池袋まで）＋西武線758円の合計'
    resync(m, 758); a, b, c = T(m); x, y, z = F(m)
    faq(m, f'池袋で西武池袋線に乗り換え、飯能で西武秩父線に乗り継いで芦ヶ久保駅へ。駅から歩いて約{walk}分で{goal}です。新宿から{a}・{x}、大宮から{b}・{y}、横浜から{c}・{z}が目安です（徒歩を含む）。')

# 武甲山・両神山（西武秩父まで特急ちちぶ）：大宮発を他と同じ池袋経由に揃え、タクシー代・バス代を運賃に含めない
for mid in ('bukosan', 'ryokami'):
    m = N[mid]
    legs = m['trainRoutes']['routes']['omiya']['legs']
    idx = [i for i, l in enumerate(legs) if l['station'] == '西武秩父駅']; assert len(idx) == 1
    m['trainRoutes']['routes']['omiya']['legs'] = [leg('大宮駅', 'train', 'JR埼京線', 30), leg('池袋駅', 'train', '西武池袋線特急ちちぶ', 80)] + legs[idx[0]:]
    for dep in ('shinjuku', 'yokohama'):
        set_line(m, dep, '池袋駅', '西武池袋線特急ちちぶ', 80)
m = N['bukosan']
m['trainRoutes']['summaryNote'] = '※運賃は西武秩父駅までの片道（特急料金900円を含む。タクシー代は別で、横瀬駅から約2,000円が目安）'
resync(m, 1700); a, b, c = T(m); x, y, z = F(m)
faq(m, f'西武秩父駅からタクシーで約20分の一ノ鳥居登山口が一般的です（バス路線なし）。池袋から特急ちちぶで約80分。新宿から{a}・{x}、大宮から{b}・{y}、横浜から{c}・{z}が目安です（運賃は西武秩父駅まで。タクシー代は別）。')
m['needsVerification'] = True
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['西武秩父駅・横瀬駅〜一ノ鳥居のタクシー料金']
m = N['ryokami']
for dep, _ in DEPS:
    legs = m['trainRoutes']['routes'][dep]['legs']; legs[-1] = {'station': '日向大谷口'}
m['trainRoutes']['summaryNote'] = '※運賃は西武秩父駅までの片道（特急料金900円を含む。小鹿野町営バス代は別）。町営バスは薬師の湯で乗り継ぎ、本数が少ないため事前に時刻を確認する'
resync(m, 1700); a, b, c = T(m); x, y, z = F(m)
faq(m, f'池袋から特急ちちぶで西武秩父駅へ行き、小鹿野町営バスを薬師の湯で乗り継いで日向大谷口へ向かいます。新宿から{a}・{x}、大宮から{b}・{y}、横浜から{c}・{z}が目安です（運賃は西武秩父駅まで。バス代は別）。車の場合は都心から約2時間30分が目安です。')
m['needsVerification'] = True
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['西武秩父駅〜日向大谷口の小鹿野町営バスの運賃・所要時間（60分）']
for name in ('日和田山', '伊豆ヶ岳'):
    x = [y for y in D if y['name'] == name][0]; x['fareCheckedAt'] = V
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('tenzandake', 'bonori', 'maruyama_okubusuma', 'futagoyama_okumusa', 'bukosan', 'ryokami'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
