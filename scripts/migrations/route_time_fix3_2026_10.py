#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""難易度の理由（第3回）を調べる中で見つかった食い違いを、出典のページを読んで直す（2026-10-12）。
- 鍋割山：大倉〜後沢乗越〜鍋割山の往復は「4時間〜4時間30分・9.4km」ではなく、
  片道が8.1km・登り約3時間50分（秦野市観光協会）、往復のコースタイムは6時間15分（YAMA HACK）
- 黒姫山：大橋〜新道の往復は「5時間30分・10.0km」ではなく、標準6時間15分・約13.5km（山と溪谷オンラインの記録。YAMA HACK は6時間45分・13.41km）
- 武尊山：川場スキー場のリフトを使う登山は、スキー場の営業期間中の雪山登山（川場スキー場）。無雪期のリフト運行は確認できていない → コースに注記と印
- 鋸山：関東ふれあいの道は林道の土砂崩落で保田方面へ通り抜けできない（富津市）→ 出典の見張りに登録（代表の車力道コースは通行可なので、注意表示は出さない）
標高差は出典で確かめた値が無いので変えていない。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
V = '2026-10-12'
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}


def route(mid, key):
    rs = [r for r in N[mid]['routes'] if key in r['name']]
    assert len(rs) == 1, (mid, key)
    return rs[0]


def swap(mid, old, new, want):
    n = 0
    for q in N[mid]['faq']:
        n += q['answer'].count(old)
        q['answer'] = q['answer'].replace(old, new)
    assert n == want, (mid, old, n)


r = route('nabewari', '後沢乗越')
assert r['time'] == '4時間〜4時間30分' and r['distance'] == '9.4km'
r.update({'time': '6時間15分', 'distance': '16.2km', 'timeSource': '往復のコースタイムは YAMA HACK（6時間15分・16.63km）。距離は秦野市観光協会の片道8.1km（登り3時間50分）の2倍',
          'timeSourceUrl': 'https://www.kankou-hadano.org/climbing/selectmountain/letsclimbingnabewari.html', 'timeCheckedAt': V})
N['nabewari']['dlReasonsSources'] = ['https://www.kankou-hadano.org/climbing/course02.html', 'https://www.kankou-hadano.org/climbing/selectmountain/letsclimbingnabewari.html', 'https://yamahack.com/169', 'https://yamahack.com/6623']

r = route('kurohimesan', '大橋林道')
assert r['time'] == '5時間30分' and r['distance'] == '10.0km'
r.update({'time': '6時間15分', 'distance': '13.5km', 'timeSource': '山と溪谷オンラインの山行記録に出ている標準コースタイム（6時間15分・約13.5km）。YAMA HACK は6時間45分・13.41km',
          'timeSourceUrl': 'https://www.yamakei-online.com/cl_record/detail.php?id=334057', 'timeCheckedAt': V})
swap('kurohimesan', '5時間30分・10.0km・標高差+1000m', '6時間15分・13.5km・標高差+1000m', 1)
N['kurohimesan']['dlReasonsSources'] = ['https://yamahack.com/2037', 'https://www.yamakei-online.com/cl_record/detail.php?id=334057']
old = '<li class="minus">山頂付近から岩場が増える。時期によっては雪が残る</li>'
assert N['kurohimesan']['dlReasonsHtml'].count(old) == 1
N['kurohimesan']['dlReasonsHtml'] = N['kurohimesan']['dlReasonsHtml'].replace(old, '<li class="minus">大橋からの往復は約13.5km・標準6時間15分〜6時間45分と距離が長い</li>\n    ' + old)

r = route('takeson', '川場スキー場')
assert not r.get('status')
r['status'] = {'state': 'caution', 'label': '積雪期のルート'}
r['note'] = '川場スキー場のリフトを使う登山は、スキー場の営業期間中（例年12月〜4月）の雪山登山です。登山届の提出とココヘリの携帯が必須で、天候や積雪で受け入れのない日があります（川場スキー場）。雪のない時期のリフト運行は確認できていません。'
r['needsVerification'] = True
r['sourceUrl'] = 'https://www.kawaba.co.jp/faq/'

m = N['nokogiriyama_chiba']
m.setdefault('annualItems', [])
assert not any(a.get('kind') == 'closure' for a in m['annualItems'])
m['annualItems'].append({'kind': 'closure', 'label': '関東ふれあいの道（林道金谷元名線）の通行止め', 'validFrom': None, 'validTo': None, 'seasonYear': 2026,
                         'sourceUrl': 'https://www.city.futtsu.lg.jp/0000000317.html', 'lastVerified': V,
                         'note': '土砂崩落のため当面の間、保田方面へ通り抜け不可。浜金谷駅〜山頂・林道口は通行可（富津市。ページの更新日は2025-06-04）'})

for mid in ('nabewari', 'kurohimesan', 'takeson', 'nokogiriyama_chiba'):
    N[mid]['mountainUpdated'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
