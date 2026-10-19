#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""景信山の「景信茶屋 青木」は、2024年1月28日で景信山での営業を終え、2024年3月に小仏城山の旧春美茶屋の場所へ移って
「山の茶屋 青天狗」として営業している（運営者の指摘・2026-10-19）。景信山の茶屋は「三角点かげ信小屋」の1軒。
出典：高尾山マガジン（2024-01-25）https://mttakaomagazine.com/news/19103 ／ 食べログ（移転先は小仏城山 青天狗）
      https://tabelog.com/tokyo/A1329/A132905/13133144/ ／ 山と溪谷オンラインの山行記録（2024-03-30。景信山の跡地は更地、
      小仏城山の旧茶屋跡に青天狗がオープン）https://www.yamakei-online.com/cl_record/detail.php?id=294086"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
V = '2026-10-19'
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}


def rep(obj, key, old, new):
    assert obj[key].count(old) == 1, (key, old)
    obj[key] = obj[key].replace(old, new)


k = N['kagenobusan']
rep(k['faq'][2], 'answer', '山頂には「景信茶屋 青木」と「三角点かげ信小屋」の2軒があります。',
    '山頂の茶屋は「三角点かげ信小屋」の1軒です（もう1軒の「景信茶屋 青木」は2024年3月に小仏城山へ移り、「山の茶屋 青天狗」になりました）。')
rep(k, 'introHtml', '山頂には2軒の茶屋があり、', '山頂には茶屋（三角点かげ信小屋）があり、')
k['teahouseSources'] = ['https://mttakaomagazine.com/news/19103', 'https://tabelog.com/tokyo/A1329/A132905/13133144/',
                        'https://www.yamakei-online.com/cl_record/detail.php?id=294086']
k['teahouseCheckedAt'] = V
k['mountainUpdated'] = V

s = N['kobotokeshiroyama']
rep(s['faq'][1], 'answer', '城山茶屋・春美茶屋の2軒があります。',
    '城山茶屋と「山の茶屋 青天狗」の2軒があります（青天狗は、景信山の「景信茶屋 青木」が2024年3月に旧春美茶屋の場所へ移ってきたお店です）。')
rep(s, 'description', '2軒の茶屋（城山茶屋・春美茶屋）', '2軒の茶屋（城山茶屋と山の茶屋 青天狗）')
rep(s, 'introHtml', '2軒の茶屋（城山茶屋・春美茶屋）', '2軒の茶屋（城山茶屋と山の茶屋 青天狗）')
s['teahouseSources'] = k['teahouseSources']
s['teahouseCheckedAt'] = V
s['mountainUpdated'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
