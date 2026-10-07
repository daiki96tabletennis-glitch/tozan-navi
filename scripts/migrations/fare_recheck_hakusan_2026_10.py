#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""白山の経路と運賃の検算、聖岳の送迎バスの注記、会津駒ヶ岳の要確認の記録（2026-10-07）。
出典：北陸鉄道「2026年 白山登山バスの運行について」（7月4日〜10月13日、金沢駅西口〜市ノ瀬 2,860円、06:00発→08:14着、予約不要・座席定員制）
      Yahoo!路線情報（2026-10-17 発）→金沢：新宿14,390円（大宮07:43発かがやき503号→09:44）／大宮13,950円／横浜14,820円（東京07:20発）
      特種東海フォレスト（2026-04-30更新）：送迎バスは2026年7月11日〜10月12日、約1時間10分、聖岳登山口での乗降は7・8月が対象
      Yahoo!路線情報 →会津田島：新宿5,320円／大宮4,770円／横浜5,690円（リバティきぬ＋AIZUマウントエクスプレス乗継）
"""
import json, os, sys, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-07'
HOKUTETSU = 'https://www.hokutetsu.co.jp/news/news-11388/'
def leg(station, icon=None, line=None, minutes=None):
    if icon is None: return {'station': station}
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}
def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')

# 白山：金沢駅西口発の北鉄・白山登山バスに組み替える。運賃は市ノ瀬まで（シャトルバス代は別）
m = N['hakusan']
tail = [leg('金沢駅', 'bus', '北陸鉄道 白山登山バス', 134), leg('市ノ瀬', 'bus', '市ノ瀬〜別当出合シャトルバス', 20), leg('別当出合')]
heads = {'shinjuku': [leg('新宿駅', 'train', 'JR湘南新宿ライン', 31), leg('大宮駅', 'train', '北陸新幹線かがやき', 121)],
         'omiya': [leg('大宮駅', 'train', '北陸新幹線かがやき', 122)],
         'yokohama': [leg('横浜駅', 'train', 'JR上野東京ライン', 26), leg('東京駅', 'train', '北陸新幹線かがやき', 144)]}
fares = {'shinjuku': 17250, 'omiya': 16810, 'yokohama': 17680}
R = m['trainRoutes']['routes']
for dep, K in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
    R[dep]['legs'] = heads[dep] + copy.deepcopy(tail)
    m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['fare' + K] = fares[dep]
m['trainRoutes']['lineName'] = '北陸新幹線・北陸鉄道 白山登山バス＋市ノ瀬シャトルバス'
m['trainRoutes']['note'] = ('💡 金沢駅西口から北陸鉄道の白山登山バスで市ノ瀬へ（約2時間15分・2,860円）。2026年の運行は7月4日〜10月13日で、運行日は限られる。'
                            '予約は不要だが座席定員制で、満席なら乗れない。'
                            '登山便は朝6時台に金沢駅を出るため、当日の新幹線では間に合わない。金沢に前泊する。'
                            '市ノ瀬〜別当出合はマイカー規制の日にシャトルバスが走る。'
                            '新宿からは大宮で北陸新幹線に乗り換えるのが速くて安い')
m['trainRoutes']['summaryNote'] = '※運賃はJR（かがやき指定席）＋白山登山バス2,860円の合計（市ノ瀬まで）。市ノ瀬〜別当出合のシャトルバス代は別'
m['trainRoutes']['links'] = [{'type': 'yahoo', 'label': '乗換案内で検索', 'url': 'https://transit.yahoo.co.jp/search/result?from=新宿&to=金沢&type=1'},
                             {'type': 'bus', 'label': '白山登山バス（北陸鉄道）', 'url': HOKUTETSU}]
m['busLinks'] = ['https://transit.yahoo.co.jp/search/result?from=新宿&to=金沢&type=1']; m['busScheduleLinks'] = [HOKUTETSU]
m['trainAccess'] = legs_text(R['shinjuku']['legs']); m['trainAccessOmiya'] = legs_text(R['omiya']['legs']); m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
for it in m['annualItems']:
    it.update({'label': '金沢駅〜市ノ瀬の白山登山バス', 'sourceUrl': HOKUTETSU, 'lastVerified': V, 'note': '運行日は限られる・予約不要の座席定員制'})
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = ('白山（別当出合登山口）へは、北陸新幹線で金沢駅へ行き、金沢駅西口から北陸鉄道の白山登山バスで市ノ瀬へ、そこからシャトルバスで別当出合へ向かいます。'
                    f'新宿から{hm(m["trainTimeShinjuku"])}・17,250円、大宮から{hm(m["trainTimeOmiya"])}・16,810円、横浜から{hm(m["trainTimeYokohama"])}・17,680円が目安です（運賃は市ノ瀬まで。シャトルバス代と乗り換えの待ち時間は別）。'
                    'バスは2026年は7月4日〜10月13日の運行で、朝6時台に金沢駅を出るため前泊が必要です。')
m['needsVerification'] = True
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['市ノ瀬〜別当出合のシャトルバスの運賃と2026年の運行日', '松任駅発着便の有無（以前の表記。北陸鉄道の2026年の案内には記載なし）']
m['mountainUpdated'] = V; m['fareCheckedAt'] = V

# 聖岳：聖岳登山口での送迎バスの乗り降りは7・8月が対象
m = N['hijiridade']
a = '聖沢登山口へは、畑薙第一ダムから椹島行き送迎バスの途中で下車（要予約・宿泊者限定、所要時間は概算）。'
assert a in m['trainRoutes']['note']
m['trainRoutes']['note'] = m['trainRoutes']['note'].replace(a, '聖沢登山口へは、畑薙第一ダムから椹島行き送迎バスの途中で下車する（要予約・宿泊者限定）。2026年は聖岳登山口で乗り降りできるのは7・8月だけ。所要時間は概算。')
m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m); m['mountainUpdated'] = V
for mid in ('hijiridade', 'arakawadake', 'akaisidake'):
    for it in N[mid]['annualItems']:
        if '送迎バス' in it['label']: it['lastVerified'] = V
    N[mid]['needsVerification'] = True
    N[mid]['verifyNotes'] = (N[mid].get('verifyNotes') or []) + ['運賃合計が未検算', '静鉄バス「南アルプス登山線」の2026年の期間（7/16〜8/16）は出典ページが開けず再確認できていない']

# 会津駒ヶ岳：鉄道の運賃は確認できたが、経路（乗継便か直通か）とバス運賃が確定せず、合計は据え置き
m = N['aizu_koma']
m['needsVerification'] = True
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['運賃合計が未検算。会津田島まで新宿5,320円／大宮4,770円／横浜5,690円（リバティきぬ＋AIZUマウントエクスプレス乗継。直通のリバティ会津は特急料金が高い）。会津田島〜駒ヶ岳登山口のバスは約2,500円との情報で、正確な額が未確認']
for it in m['annualItems']:
    it['lastVerified'] = V; it['note'] = '2026年の時刻表（5/1〜10/31）で確認'
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
m = N['hakusan']; print(m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'])
