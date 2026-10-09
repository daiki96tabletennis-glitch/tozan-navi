#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：「雪が降ったあとの数日だけ滑り止めが要る」低山を、アイゼン不要に戻す（運営者の方針・2026-10-09）。
方針：都内でも雪は降り、その後の数日に滑り止めが要るのは当たり前。そういう例外では「軽アイゼン等」を付けない。
      冬のあいだ雪や凍結が続くのが普通の山だけ「軽アイゼン等」にする。
関東の低山は標高1,200mを目安に線を引く。
  戻す（通年アイゼン不要）：御岳山 929m・日の出山 902m・棒ノ折山 969m・高水三山 793m・百蔵山 1,003m・扇山 1,138m・明神ヶ岳 1,169m
    （根拠にした記録が、降雪直後のもの／「雪は数日で解ける」という内容だった）
  そのまま（冬は軽アイゼン等）：大山 1,252m・大岳山 1,266m・金時山 1,212m・笹子雁ヶ腹摺山 1,357m・天城山 1,406m など1,200m以上の山
旧フィールド・FAQ・装備カードも元に戻す（FAQ などは改修前のバックアップの値を使う）。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gear_calendar as G
P = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
D = json.load(open(P, encoding='utf-8'))
GD = json.load(open(GP, encoding='utf-8'))
ORIG = {m['id']: m for m in json.load(open(sys.argv[1], encoding='utf-8'))}   # 装備カレンダー改修前の mountains.json
N = {m['id']: m for m in D}
V = '2026-10-09'
for mid in ('mitakesan', 'hinodesaan', 'bonori', 'takamizusanzan', 'momakurasan', 'ogiyama', 'myojingatake'):
    m = N[mid]
    assert (m.get('elevation') or 0) < 1200, mid
    m['gearCalendar'] = ['no_crampons'] * 12
    m['seasonCalendar'] = ['s-ok'] * 12
    m['calLegend'] = [G.LABEL['no_crampons']]
    o = ORIG[mid]
    for k in ('seasonNoGear', 'season6Crampons', 'season'):
        m[k] = o.get(k)
    if mid == 'takamizusanzan':
        m['season6Crampons'] = 'なし'
    oq = [q for q in o['faq'] if 'シーズン' in q['question']]
    nq = [q for q in m['faq'] if 'シーズン' in q['question']]
    assert len(oq) == len(nq) <= 1, mid
    if nq:
        nq[0]['answer'] = oq[0]['answer']
    for mo in GD[mid]:
        GD[mid][mo] = [c for c in GD[mid][mo] if c['c'] not in ('crampon', 'crampon_next')]
    m['mountainUpdated'] = V
    print(mid, m['name'], m.get('elevation'), m['seasonNoGear'], '|', m['season6Crampons'], '|', m['season'])
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(GD, open(GP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
