#!/usr/bin/env python3
"""猿倉駐車場の閉鎖を白馬岳に入れる（2026-11-23。運営者の指示）。
出典：白馬村「猿倉駐車場の閉鎖及び白馬岳方面への進入方法についてのお知らせ」（2026-04-28 更新。令和8〜9年度の路面復旧工事）。
県道白馬岳線の冬期通行止めの開始の変更（11/27→11/19 17時。長野県大町建設事務所）は add_route_winter_2026_11.py。何度流しても同じ結果"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL = 'https://www.vill.hakuba.lg.jp/gyosei/soshikikarasagasu/kankoka/osirase_ibennto_kouhoumusenntou/10949.html'
TITLE = '猿倉駐車場は工事で閉鎖中'
ALERT = {'title': TITLE,
         'text': '令和8〜9年度の路面復旧工事で、猿倉駐車場は使えません。車は八方第3・第5駐車場か八方ローソン東側駐車場（無料）に停め、八方バスターミナルからタクシーか路線バスで猿倉へ向かいます。猿倉までの路上駐車は禁止です。猿倉への県道は2026年11月19日17時から冬期通行止めです（解除は2027年4月23日10時の予定）。',
         'level': 'red', 'statusType': 'temporary', 'validFrom': '2026-04-17', 'validTo': None,
         'sourceUrl': URL, 'linkText': '白馬村のお知らせ', 'lastVerified': '2026-11-23'}
PARKING = '猿倉駐車場は令和8〜9年度の工事で閉鎖中。八方第3・第5駐車場・八方ローソン東側駐車場（無料）に停め、八方バスターミナルからタクシーか路線バスで猿倉へ'

p = os.path.join(ROOT, 'data', 'mountains.json')
with open(p, encoding='utf-8') as f:
    ms = json.load(f)
m = next(x for x in ms if x['id'] == 'shirouma')
al = [a for a in (m.get('alerts') or []) if a.get('title') != TITLE]
m['alerts'] = al + [ALERT]
m['mountainUpdated'] = '2026-11-23'
next(x for x in ms if x['id'] == 'karamatsu')['mountainUpdated'] = '2026-11-23'
with open(p, 'w', encoding='utf-8') as f:
    json.dump(ms, f, ensure_ascii=False, indent=2)
p = os.path.join(ROOT, 'data', 'accesses.json')
with open(p, encoding='utf-8') as f:
    raw = f.read()
ac = json.loads(raw)
ac['sarukura']['car']['parking'] = PARKING
ac['sarukura']['lastVerified'] = '2026-11-23'
with open(p, 'w', encoding='utf-8') as f:
    json.dump(ac, f, ensure_ascii=False, indent=2)
    if raw.endswith('\n'):
        f.write('\n')
print('ok')
