#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""妙高山（バスの起点駅の誤り）と甲武信ヶ岳の経路・運賃の検算（2026-10-07）。
出典：Yahoo!路線情報（2026-10-17 発）
  →関山（えちごトキめき鉄道）：新宿9,570円（大宮08:17発はくたか553号→上越妙高09:54、10:13→関山10:39）／大宮8,800円／横浜10,110円（東京07:52発）
  →信濃川上：新宿6,090円（あずさ5号 08:00→小淵沢09:53、小海線10:07→10:50）／大宮5,830円（あさま601号 07:17→佐久平08:13、小海線08:31→09:55）／横浜5,430円（八王子08:33発あずさ5号）
  NAVITIME：関・燕温泉線[妙高市営バス] 関山駅10:49→燕温泉11:23
  妙高市公式：関・燕温泉線は令和8年4月1日〜令和9年3月31日の通年運行、運行は（株）妙高ハブネットに委託
  川上村営バス：信濃川上駅〜梓山 550円・25分（村の時刻表・料金ページ）
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
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
def leg(station, icon=None, line=None, minutes=None):
    if icon is None: return {'station': station}
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}
def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')
def build(m, heads, tail, fares):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        R[dep]['legs'] = heads[dep] + copy.deepcopy(tail)
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
        m['fare' + K] = fares[dep]
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V; m['fareCheckedAt'] = V
def faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text
def T(m): return hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama'])

# 妙高山：燕温泉行きのバスが出るのは妙高高原駅ではなく関山駅。事業者も頸南バスではなく妙高市営バス
m = N['myoko']
m['trainRoutes']['note'] = ('💡 燕温泉へのバスは関山駅から出る（妙高高原駅ではない）。妙高市営バス「関・燕温泉線」で20〜34分、1日7便、通年運行。'
                            '上越妙高駅で北陸新幹線から妙高はねうまラインに乗り換えて関山駅へ。'
                            '大宮からは長野まで新幹線、しなの鉄道と妙高はねうまラインを乗り継ぐ経路もあり、こちらのほうが安い。'
                            '燕温泉には無料の露天風呂「黄金の湯」があり、下山後に立ち寄れる。'
                            '火打山とあわせて登る場合は笹ヶ峰が起点になる')
m['trainRoutes']['summaryNote'] = '※運賃は関山駅までの片道（新幹線は自由席。バス代は別で、金額は未確認）'
m['busScheduleLinks'] = ['https://www.city.myoko.niigata.jp/docs/892.html']
build(m, {'shinjuku': [leg('新宿駅', 'train', 'JR埼京線・湘南新宿ライン', 32), leg('大宮駅', 'train', '北陸新幹線はくたか', 97)],
          'omiya': [leg('大宮駅', 'train', '北陸新幹線はくたか', 97)],
          'yokohama': [leg('横浜駅', 'train', 'JR上野東京ライン', 29), leg('東京駅', 'train', '北陸新幹線はくたか', 122)]},
      [leg('上越妙高駅', 'train', 'えちごトキめき鉄道 妙高はねうまライン', 26), leg('関山駅', 'bus', '妙高市営バス「関・燕温泉線」', 34), leg('燕温泉')],
      {'shinjuku': 9570, 'omiya': 8800, 'yokohama': 10110})
a, b, c = T(m)
faq(m, f'北陸新幹線で上越妙高駅へ行き、えちごトキめき鉄道で関山駅へ、そこから妙高市営バス「関・燕温泉線」で燕温泉まで20〜34分です。バスが出るのは妙高高原駅ではなく関山駅です。'
       f'新宿からは大宮で新幹線に乗り換えて{a}・9,570円、大宮から{b}・8,800円、横浜からは東京で新幹線に乗り換えて{c}・10,110円が目安です（運賃は関山駅まで。バス代と乗り換えの待ち時間は別）。')
m['needsVerification'] = True
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['関山駅〜燕温泉のバス運賃（500円との情報。市の料金表PDFは未確認）']

# 甲武信ヶ岳：大宮・横浜発が新宿経由の同額で載っていた。大宮は佐久平経由、横浜は八王子乗車が速くて安い
m = N['kobushigatake']
tail = [leg('信濃川上駅', 'bus', '川上村営バス「川端下行」', 25), leg('梓山', 'walk', '徒歩', 60), leg('毛木平（登山口）')]
m['trainRoutes']['summaryNote'] = '※運賃はJR＋村営バス550円の合計。大宮は佐久平まで新幹線、横浜は八王子から特急に乗る'
m['trainRoutes']['links'][0]['url'] = 'https://transit.yahoo.co.jp/search/result?from=新宿&to=信濃川上&type=1'
build(m, {'shinjuku': [leg('新宿駅', 'train', 'JR特急あずさ', 113), leg('小淵沢駅', 'train', 'JR小海線', 43)],
          'omiya': [leg('大宮駅', 'train', '北陸新幹線あさま', 56), leg('佐久平駅', 'train', 'JR小海線', 84)],
          'yokohama': [leg('横浜駅', 'train', 'JR横浜線', 60), leg('八王子駅', 'train', 'JR特急あずさ', 80), leg('小淵沢駅', 'train', 'JR小海線', 43)]},
      tail, {'shinjuku': 6640, 'omiya': 6380, 'yokohama': 5980})
a, b, c = T(m)
faq(m, f'小海線の信濃川上駅から川上村営バスで梓山へ行き、毛木平の登山口まで約1時間歩きます。'
       f'新宿からは特急あずさで小淵沢へ出て{a}・6,640円、大宮からは佐久平まで新幹線に乗り{b}・6,380円、横浜からは八王子で特急に乗り{c}・5,980円が目安です（徒歩1時間を含む。乗り換えの待ち時間は別）。'
       '車の場合は都心から約2時間30分が目安です。')
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('myoko', 'kobushigatake'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
