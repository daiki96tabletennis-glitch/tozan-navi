#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巻機山：運賃を六日町駅までの電車代だけにする（2026-10-07）。
MOSSの運賃は距離別（13km未満300円／13〜17km未満500円／17〜20km未満700円／20〜30km未満1,000円）で、
六日町駅〜清水がどの区分かを市の資料で確認できなかったため、合計に含めない。
出典：南魚沼市「AIオンデマンド交通MOSS」、Yahoo!路線情報（浦佐経由）新宿7,080円（大宮乗車、4,440＋2,640）／大宮6,420円（3,780＋2,640）／横浜8,620円（東京乗車、4,880＋3,740）
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'makihata'][0]
V = '2026-10-07'


def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')


tr = m['trainRoutes']
tr['note'] = ('💡 六日町駅から清水（桜坂駐車場）へはAIオンデマンド交通「MOSS」を予約して乗る。'
              'MOSSは月〜金の8時30分〜17時30分だけの運行で、土日祝は運休。'
              '運賃は距離別で300〜1,000円（13km未満300円、13〜17km未満500円、17〜20km未満700円、20km以上1,000円）。'
              '予約は乗車の1週間前から30分前まで、アプリか電話（025-775-7778）で受け付ける。'
              '8時30分〜9時に乗る場合は前日までの予約が必要。'
              '土日祝や早朝はタクシー利用となる（約25分・6,000〜7,000円）。'
              '越後湯沢駅でほくほく線に乗り換える行き方もある。'
              '桜坂駐車場から巻機山山頂（御機屋経由）までは約4時間30分で、井戸尾根は標高差1,200m超の登りが続くため早発が必須')
tr['summaryNote'] = '※表示の運賃は六日町駅までの電車代。MOSSまたはタクシーの料金は別にかかる。六日町駅〜清水の路線バスは2026年3月31日で廃止された'
R = tr['routes']
F = {'shinjuku': 7080, 'omiya': 6420, 'yokohama': 8620}
for dep, K in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
    m['fare' + K] = F[dep]
    m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
m['trainAccess'] = legs_text(R['shinjuku']['legs'])
m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
m['trainAccessHtml'] = render_ts_section(tr, m)
m['verifyNotes'] = [n for n in (m.get('verifyNotes') or []) if '運賃合計が未検算' not in n] + [
    'MOSSで六日町駅〜清水（桜坂駐車場）に乗れるか（乗降場所の一覧）と、その距離区分の運賃・所要時間（30分／40分の表記ゆれ）が未確認']
m['needsVerification'] = True
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = ('上越新幹線で浦佐駅へ行き、JR上越線で六日町駅へ。六日町駅からは予約制のオンデマンド交通「MOSS」（月〜金のみ）かタクシーで清水（桜坂駐車場）へ向かいます。'
                    f'六日町駅までの電車代は新宿から{format(F["shinjuku"], ",")}円、大宮から{format(F["omiya"], ",")}円、横浜から{format(F["yokohama"], ",")}円で、MOSSやタクシーの料金は別にかかります（新幹線は自由席）。'
                    f'所要時間は新宿から{hm(m["trainTimeShinjuku"])}、大宮から{hm(m["trainTimeOmiya"])}、横浜から{hm(m["trainTimeYokohama"])}が目安です（乗り換えの待ち時間は別）。'
                    '土日祝はMOSSが運休です。車の場合は都心から約4時間5分が目安です。')
m['trainInfo'] = '新宿→大宮→浦佐（上越新幹線）→六日町（上越線）→MOSSまたはタクシー→清水'
m['mountainUpdated'] = V
m['fareCheckedAt'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'])
