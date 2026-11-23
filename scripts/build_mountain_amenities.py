#!/usr/bin/env python3
"""山ページの「山小屋・下山後の温泉」の要約とトップの絞り込みに使う data/mountain_amenities.json を作る（2026-11-23〜）。
手で編集しない。元：huts.json・huts_stay_mountains.json（コース上の山小屋）、onsen_sauna.json（公式で確かめた施設）、
onsen_near_mountains.json（下山後に寄れそうな温泉の目安）。データに無い料金・時間は足さない。
huts・温泉のデータを直したら実行し、そのあと gen_mountain_pages.py --all"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(name):
    with open(os.path.join(ROOT, 'data', name), encoding='utf-8') as f:
        return json.load(f)

def build():
    ms = load('mountains.json')
    ids = {m['id'] for m in ms}
    huts = load('huts.json')['huts']
    stay = load('huts_stay_mountains.json')['mountains']
    near = load('onsen_near_mountains.json')['mountains']
    plans = load('onsen_sauna.json')['plans']
    out = {}
    for mid in sorted(ids):
        item = {}
        names = set(stay.get(mid) or [])
        hs = [h for h in huts if h['name'] in names and mid in (h.get('mountainIds') or [])]
        if hs:
            hs.sort(key=lambda h: (0 if h.get('bookingStart') else 1, h['name']))
            item['hutCount'] = len(hs)
            item['huts'] = [{'id': h['id'], 'name': h['name'], 'booking': h.get('bookingStart'),
                             'url': h.get('officialUrl')} for h in hs[:3]]
        plan = next((p for p in plans if p['id'] == mid), None)
        if plan and plan.get('facilities'):
            fac = plan['facilities'][0]
            links = fac.get('links') or []
            item['onsen'] = {'name': fac['name'], 'checked': True, 'fee': fac.get('feeShort'),
                             'move': plan.get('moveShort'), 'url': links[0]['url'] if links else None}
        elif mid in near:
            n = near[mid]
            item['onsen'] = {'name': re.sub(r'\s*[；;]\s*', '、', n.get('near') or ''), 'checked': False,
                             'osm': 'osm' in (n.get('why') or [])}
        if item:
            out[mid] = item
    return {'_note': 'scripts/build_mountain_amenities.py が作る（手で編集しない）。checked=false の温泉は下山後に寄れそうな目安で、営業・料金は未確認。osm=true は © OpenStreetMap contributors（ODbL）',
            'mountains': out}

if __name__ == '__main__':
    d = build()
    with open(os.path.join(ROOT, 'data', 'mountain_amenities.json'), 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    v = d['mountains'].values()
    print('山', len(d['mountains']), '山小屋', sum('huts' in x for x in v), '温泉', sum('onsen' in x for x in v),
          '公式確認済みの温泉', sum(x.get('onsen', {}).get('checked', False) for x in v))
