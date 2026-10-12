#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋の位置（緯度・経度）を OpenStreetMap から取り、data/huts_coords.json に書く。
使い方：python3 scripts/build_huts_coords.py            （Overpass API から取得）
        python3 scripts/build_huts_coords.py --cache F  （取得済みの JSON を使う）

位置は推測で置かない。次のどちらかに当てはまる小屋だけ書く。
  1. OpenStreetMap 上の名前（name / alt_name / old_name など）が小屋名と一致し、対応する山（mountains.json の lat / lng）から20km以内に1か所だけある
  2. 名前の書き方が違うだけで同じ小屋だと確かめたもの（ALIAS。OpenStreetMap の要素を番号で指定）
当てはまらない小屋は地図に出さない（ページでは一覧にだけ出る）。
データは © OpenStreetMap contributors（ODbL）。地図を出すページに出典を表記する。
"""
import json, math, os, re, subprocess, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BBOX = '34.9,136.3,38.3,140.6'
QUERY = ('[out:json][timeout:150];(nwr["tourism"~"^(alpine_hut|wilderness_hut|hotel|guest_house|hostel|chalet|camp_site)$"]["name"](%s);'
         'nwr["amenity"="shelter"]["name"](%s););out center tags;' % (BBOX, BBOX))
# 名前の書き方が違うが同じ小屋と確かめたもの：小屋名 → OpenStreetMap の要素
ALIAS = {
    '殺生小屋': 'node/1845028386',                 # 殺生ヒュッテ
    '徳沢ロッヂ': 'way/720922476',                 # 徳沢ロッジ
    '有明荘': 'way/184870438',                     # 安曇野市営有明荘
    '村営白馬岳頂上宿舎': 'way/234581430',         # 白馬岳頂上宿舎
    '村営天狗山荘': 'way/810456769',               # 天狗山荘
    '村営八方池山荘': 'way/312064753',             # 八方池山荘
    '駒ヶ岳頂上山荘': 'way/187898280',             # 頂上山荘（木曽駒ヶ岳）
    '空木駒峰ヒュッテ': 'way/886111863',           # 駒峰ヒュッテ
    '苗場山頂ヒュッテ－自然体験交流センター': 'way/549930007',  # 苗場山頂ヒュッテ
    '石室山荘': 'way/305226519',                   # 山荘石室（御嶽山）
    '甲斐駒ヶ岳七丈小屋': 'way/1386017340',        # 七丈第一小屋（受付のある棟）
    '雷鳥荘': 'way/199362781',                     # らいちょう温泉雷鳥荘
    '里見平★星観荘': 'node/2429748893',            # 星見平 星観荘
    '本八合目 富士山ホテル': 'way/300186485',      # 本八合目 富士山ホテル 第1
    '飯豊切合小屋': 'node/4359745025',             # 切合小屋
    'LUCY尾瀬鳩待（旧 鳩待山荘）': 'way/388245395',  # LUCY尾瀬鳩待 by 星野リゾート
    '尾瀬御池ロッジ': 'way/27423455',              # 御池ロッジ
    '吉田口七合目 日の出館': 'way/837513081',      # 日の出館（吉田ルート側。御殿場側の「日ノ出館」と区別）
}


def norm(s):
    s = unicodedata.normalize('NFKC', s or '')
    s = re.sub(r'[（(].*?[）)]', '', s)
    s = re.sub(r'[\s　・★\-－ー―]', '', s)
    for a, b in (('ヶ', 'ケ'), ('が', 'ケ'), ('ガ', 'ケ'), ('ノ', 'の'), ('之', 'の'), ('乃', 'の'), ('ッ', 'ツ'), ('澤', '沢'), ('嶽', '岳'), ('劔', '剱'), ('剣', '剱'), ('ひゅって', 'ヒュツテ')):
        s = s.replace(a, b)
    return s


def dist(a, b, c, d):
    p = math.radians
    x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


def ele(e):
    m = re.match(r'\s*([\d.]+)', str(e['tags'].get('ele') or ''))
    return round(float(m.group(1))) if m else None


def main():
    if '--cache' in sys.argv:
        raw = open(sys.argv[sys.argv.index('--cache') + 1], encoding='utf-8').read()
    else:
        raw = subprocess.run(['curl', '-s', '-m', '180', '-A', 'yamatch-huts/1.0 (tozan-navi.com)', '--data-urlencode', 'data=' + QUERY,
                              'https://overpass-api.de/api/interpreter'], capture_output=True).stdout.decode('utf-8', 'replace')
    try:
        els = json.loads(raw)['elements']
    except ValueError:
        sys.exit('OpenStreetMap（Overpass API）から取得できませんでした。時間をおいて再実行してください。data/huts_coords.json は変えていません')
    assert len(els) > 1000, '取得件数が少なすぎる（%d件）' % len(els)
    huts = json.load(open(os.path.join(ROOT, 'data', 'huts.json'), encoding='utf-8'))['huts']
    M = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
    assert set(ALIAS) <= set(h['name'] for h in huts), set(ALIAS) - set(h['name'] for h in huts)
    osm, by_ref = [], {}
    for e in els:
        la = e.get('lat') or (e.get('center') or {}).get('lat')
        lo = e.get('lon') or (e.get('center') or {}).get('lon')
        if la is None:
            continue
        ns = set()
        for k in ('name', 'name:ja', 'alt_name', 'official_name', 'old_name', 'short_name'):
            for part in re.split(r'[;/]', e['tags'].get(k) or ''):
                if part.strip():
                    ns.add(norm(part))
        osm.append((ns, la, lo, e))
        by_ref['%s/%d' % (e['type'], e['id'])] = (la, lo, e)
    out, multi, none = {}, [], []
    for h in huts:
        name = h['name']
        if name in ALIAS:
            if ALIAS[name] not in by_ref:
                none.append(name + '（ALIAS の要素が見つからない）')
                continue
            la, lo, e = by_ref[ALIAS[name]]
            out[name] = {'lat': round(la, 5), 'lng': round(lo, 5), 'osm': ALIAS[name], 'osmName': e['tags'].get('name'), 'match': 'alias', 'ele': ele(e)}
            continue
        mids = h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]
        pts = [(M[i]['lat'], M[i]['lng']) for i in mids if M[i].get('lat')]
        keys = {norm(name)}
        m = re.search(r'[（(](.+?)[）)]', name)
        if m and '小屋' in m.group(1):
            keys.add(norm(m.group(1)))
        sp = name.split(' ')
        if len(sp) > 1:                      # 「富士宮口八合目 池田館」→「池田館」
            keys.add(norm(sp[-1]))
            keys.add(norm(''.join(sp)))
        cand = []
        for ns, la, lo, e in osm:
            if keys & ns and pts and min(dist(la, lo, a, b) for a, b in pts) <= 20:
                if all(dist(la, lo, c[0], c[1]) > 0.3 for c in cand):     # 同じ建物の node と way は1つに数える
                    cand.append((la, lo, e))
        if len(cand) == 1:
            la, lo, e = cand[0]
            out[name] = {'lat': round(la, 5), 'lng': round(lo, 5), 'osm': '%s/%d' % (e['type'], e['id']), 'osmName': e['tags'].get('name'), 'match': 'name', 'ele': ele(e)}
        elif cand:
            multi.append(name)
        else:
            none.append(name)
    json.dump({'note': '山小屋の位置。OpenStreetMap から scripts/build_huts_coords.py が作る（手で編集しない）。© OpenStreetMap contributors（ODbL）',
               'source': 'https://www.openstreetmap.org/copyright', 'huts': out},
              open(os.path.join(ROOT, 'data', 'huts_coords.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    print('位置あり %d 軒／%d 軒' % (len(out), len(huts)))
    print('候補が複数あって決められない：', multi)
    print('見つからない：', none)


if __name__ == '__main__':
    main()
