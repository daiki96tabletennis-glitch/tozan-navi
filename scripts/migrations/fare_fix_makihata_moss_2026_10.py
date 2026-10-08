#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巻機山：MOSSの運賃500円を合計に入れ、バスのリンクを南魚沼市のMOSSのページに統一する（2026-10-08）。
出典：南魚沼市「AIオンデマンド交通MOSS」https://www.city.minamiuonuma.niigata.jp/docs/ondemand-koutsu.html
  距離別運賃 13〜17km未満 500円。六日町駅〜清水は車で約15km（サイト運営者が確認）
  六日町駅まで（Yahoo!路線情報、浦佐経由）新宿7,080円／大宮6,420円／横浜8,620円
MOSSの所要時間は出発地によって30分／40分とばらついていたので30分に揃える（15kmの道のり）。
"""
import json, os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'makihata'][0]
V = '2026-10-08'
URL = 'https://www.city.minamiuonuma.niigata.jp/docs/ondemand-koutsu.html'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))


def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')


tr = m['trainRoutes']
assert (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama']) == (7080, 6420, 8620)
F = {'shinjuku': 7580, 'omiya': 6920, 'yokohama': 9120}
for dep, K in DEPS:
    L = tr['routes'][dep]['legs']
    assert L[-2]['station'] == '六日町駅'
    L[-2]['durationMin'] = 30
    L[-2]['method']['line'] = 'オンデマンド交通「MOSS」（平日のみ・要予約）'
    m['fare' + K] = F[dep]
    m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in L)
note, c = re.subn(re.escape('運賃は距離別で300〜1,000円（13km未満300円、13〜17km未満500円、17〜20km未満700円、20km以上1,000円）。'),
                  '運賃は距離別で、六日町駅〜清水（約15km）は500円。', tr['note'])
assert c == 1
tr['note'] = note
tr['summaryNote'] = '※表示の運賃はMOSS（500円）を使う場合。土日祝や早朝はMOSSが無く、タクシー代が別にかかる。六日町駅〜清水の路線バスは2026年3月31日で廃止された'
bus = [l for l in tr['links'] if l['type'] == 'bus']
assert len(bus) == 1 and bus[0]['url'] == URL
m['busScheduleLinks'] = [URL]
m['trainAccess'] = legs_text(tr['routes']['shinjuku']['legs'])
m['trainAccessOmiya'] = legs_text(tr['routes']['omiya']['legs'])
m['trainAccessYokohama'] = legs_text(tr['routes']['yokohama']['legs'])
m['trainAccessHtml'] = render_ts_section(tr, m)
m['verifyNotes'] = [n for n in (m.get('verifyNotes') or []) if 'MOSS' not in n]
m['needsVerification'] = bool(m['verifyNotes'])
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
t = tuple(hm(m['trainTime' + K]) for _, K in DEPS)
hit[0]['answer'] = ('上越新幹線で浦佐駅へ行き、JR上越線で六日町駅へ。六日町駅からは予約制のオンデマンド交通「MOSS」（月〜金のみ）で清水（桜坂駐車場）へ向かいます。'
                    f'新宿から{t[0]}・{format(F["shinjuku"], ",")}円、大宮から{t[1]}・{format(F["omiya"], ",")}円、横浜から{t[2]}・{format(F["yokohama"], ",")}円が目安です（新幹線は自由席、乗り換えの待ち時間は別）。'
                    '土日祝はMOSSが運休のため、六日町駅からタクシーを使います。車の場合は都心から約4時間5分が目安です。')
m['trainInfo'] = '新宿→大宮→浦佐（上越新幹線）→六日町（上越線）→MOSS約30分（平日のみ）→清水'
m['mountainUpdated'] = V
m['fareCheckedAt'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(F, m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['verifyNotes'])
