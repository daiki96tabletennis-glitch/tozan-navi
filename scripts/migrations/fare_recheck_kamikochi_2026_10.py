#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""蝶ヶ岳を、検証済みの「上高地へのアクセス」（槍ヶ岳・奥穂高岳と同じ）に揃える。焼岳は注記の更新と要確認の記録。
あわせて、運賃を検算した山に fareCheckedAt を付ける（2026-10-07）。
出典：Yahoo!路線情報（2026-10-17 発）→新島々 7,440円／7,440円（立川乗車なら7,130円）／7,130円、アルピコ交通 新島々〜上高地 3,100円（2026年）
"""
import json, os, sys, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
D = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
AC = json.load(open(os.path.join(ROOT, 'data', 'accesses.json'), encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-07'
def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')

a = AC['kamikochi']
m = N['chogatake']
m['trainRoutes'] = copy.deepcopy(a['trainRoutes'])
R = m['trainRoutes']['routes']
for dep, K in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
    m['fare' + K] = a['fares'][dep]
    m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
m['trainAccess'] = legs_text(R['shinjuku']['legs'])
m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
m['trainAccessLabel'] = '上高地バスターミナル（長塀尾根ルート）'
m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = ('特急あずさで松本駅へ行き、松本電鉄上高地線で新島々駅へ、そこからアルピコ交通バスで上高地まで約1時間です。'
                    f'新宿から{hm(m["trainTimeShinjuku"])}・10,540円、大宮からは立川で特急に乗り{hm(m["trainTimeOmiya"])}・10,230円、横浜からは八王子で特急に乗り{hm(m["trainTimeYokohama"])}・10,230円が目安です（乗り換えの待ち時間は別）。'
                    'バスは2026年は予約優先制です。三股から登る場合は、穂高駅から路線バス「三股線」があります。車の場合は都心から約5時間が目安です。')
m['mountainUpdated'] = V

y = N['yakedake']
y['trainRoutes']['note'] = (a['trainRoutes']['note'].rstrip('。') + '。焼岳の中の湯バス停は、この上高地行きのバスの途中（上高地の手前）にある')
y['trainRoutes']['summaryNote'] = '※新島々〜中の湯のバス運賃は未確認。表示の運賃は古い額の可能性がある'
y['trainAccessHtml'] = render_ts_section(y['trainRoutes'], y)
y['needsVerification'] = True
y['verifyNotes'] = (y.get('verifyNotes') or []) + ['運賃合計が未検算。新島々まで新宿7,440円／大宮7,130〜7,440円／横浜7,130円。新島々〜中の湯のバス運賃が未確認（上高地までは3,100円）']
y['mountainUpdated'] = V

CHECKED = ['tairappyo', 'ontakesan', 'iide', 'kitadake', 'noutori', 'ainodake', 'kayagatake', 'mizugaki', 'harinokidake', 'kashimayari',
           'eboshidake_kita', 'noguchigoro', 'arikayama', 'otenshoudake', 'azumayasan', 'shirane_gunma', 'bandai',
           'keirisan', 'kirigamine', 'nokogiriyama', 'akagi', 'chogatake', 'hinata', 'minamikomagatake', 'azuma', 'kurohimesan',
           'juunigadake']
for mid in CHECKED:
    N[mid]['fareCheckedAt'] = V
json.dump(D, open(os.path.join(ROOT, 'data', 'mountains.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], len(CHECKED))
