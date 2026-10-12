#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋のある山の「山頂の位置」を OpenStreetMap から取り、data/summit_coords.json に書く。
（mountains.json の lat / lng は登山口の位置なので、山小屋の地図に山を出すには山頂の位置が別に要る）
使い方：python3 scripts/build_summit_coords.py            （Overpass API から取得）
        python3 scripts/build_summit_coords.py --cache F  （取得済みの JSON を使う）

山名が OpenStreetMap の山頂（natural=peak / volcano）の名前と一致し、サイトの山の位置（mountains.json の lat / lng）から15km以内にあるものだけ書く。
同じ名前が複数あるときは、標高（ele）がサイトの標高に最も近いものを選ぶ。標高差が150mを超えるものは採らない。
名前の書き方が違う山は PEAK_NAME に、OpenStreetMap 上の山頂名を書く。一致しない山は地図に出さない（推測で置かない）。
© OpenStreetMap contributors（ODbL）
"""
import json, math, os, re, subprocess, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BBOX = '34.9,136.3,38.3,140.6'
QUERY = '[out:json][timeout:150];node["natural"~"^(peak|volcano)$"]["name"](%s);out;' % BBOX
# サイトの山名 → OpenStreetMap の山頂名（最高点や、ふつう山頂とされる峰）
PEAK_NAME = {
    '八ヶ岳（赤岳）': '赤岳', '丹沢山': '丹沢山', '立山': '大汝山', '白馬岳': '白馬岳', '穂高岳': '奥穂高岳', '奥穂高岳': '奥穂高岳',
    '乗鞍岳': '剣ヶ峰', '富士山': '剣ヶ峰', '白山': '御前峰', '浅間山': '前掛山', '霧ヶ峰': '車山', '美ヶ原': '王ヶ頭',
    '木曽駒ヶ岳': '木曽駒ヶ岳', '甲斐駒ヶ岳': '甲斐駒ヶ岳', '荒川岳': '悪沢岳', '大菩薩嶺': '大菩薩嶺', '鳳凰山': '観音ヶ岳', '谷川岳': '谷川岳 オキノ耳', '越後駒ヶ岳': '駒ヶ岳', '塩見岳': '塩見岳 東峰',
    '苗場山': '苗場山', '妙高山': '妙高山', '燧ヶ岳': '柴安嵓', '八ヶ岳（天狗岳）': '西天狗岳', '塔ノ岳': '塔ノ岳',
}


def norm(s):
    s = unicodedata.normalize('NFKC', s or '')
    s = re.sub(r'[（(].*?[）)]', '', s)
    s = re.sub(r'\s', '', s)
    for a, b in (('ヶ', 'ケ'), ('が', 'ケ'), ('ガ', 'ケ'), ('ノ', 'の'), ('之', 'の'), ('嶽', '岳'), ('劔', '剱'), ('剣', '剱'), ('槍', '鑓')):
        s = s.replace(a, b)
    return s


def dist(a, b, c, d):
    p = math.radians
    x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


def ele(tags):
    m = re.match(r'\s*([\d.]+)', str(tags.get('ele') or ''))
    return float(m.group(1)) if m else None


def main():
    if '--cache' in sys.argv:
        raw = open(sys.argv[sys.argv.index('--cache') + 1], encoding='utf-8').read()
    else:
        raw = subprocess.run(['curl', '-s', '-m', '180', '-A', 'yamatch-huts/1.0 (tozan-navi.com)', '--data-urlencode', 'data=' + QUERY,
                              'https://overpass-api.de/api/interpreter'], capture_output=True).stdout.decode('utf-8', 'replace')
    try:
        els = json.loads(raw)['elements']
    except ValueError:
        sys.exit('OpenStreetMap（Overpass API）から取得できませんでした。data/summit_coords.json は変えていません')
    assert len(els) > 1000
    huts = json.load(open(os.path.join(ROOT, 'data', 'huts.json'), encoding='utf-8'))['huts']
    need = set(i for h in huts for i in h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []])
    ML = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    out, miss = {}, []
    for m in ML:
        if m['id'] not in need:
            continue
        key = norm(PEAK_NAME.get(m['name'], m['name']))
        cand = []
        for e in els:
            names = set(norm(p) for k in ('name', 'name:ja', 'alt_name') for p in re.split(r'[;/]', e['tags'].get(k) or '') if p.strip())
            if key in names and dist(e['lat'], e['lon'], m['lat'], m['lng']) <= 15:
                el = ele(e['tags'])
                cand.append((abs(el - m['elevation']) if el is not None else 9999, dist(e['lat'], e['lon'], m['lat'], m['lng']), e))
        cand.sort(key=lambda x: (x[0], x[1]))
        ok = [c for c in cand if c[0] <= 150] or ([cand[0]] if len(cand) == 1 else [])
        if not ok:
            miss.append(m['name'])
            continue
        e = ok[0][2]
        out[m['id']] = {'lat': round(e['lat'], 5), 'lng': round(e['lon'], 5), 'osm': 'node/%d' % e['id'], 'osmName': e['tags'].get('name'), 'ele': ele(e['tags'])}
    json.dump({'note': '山頂の位置。OpenStreetMap から scripts/build_summit_coords.py が作る（手で編集しない）。© OpenStreetMap contributors（ODbL）', 'mountains': out},
              open(os.path.join(ROOT, 'data', 'summit_coords.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    print('山頂の位置あり %d 山／%d 山' % (len(out), len(need)))
    print('見つからない：', miss)
    for k, v in out.items():
        mm = [x for x in ML if x['id'] == k][0]
        if v['osmName'] != mm['name'] or v['ele'] is None or abs(v['ele'] - mm['elevation']) > 30:
            print('  要目視', mm['name'], mm['elevation'], '←', v['osmName'], v['ele'])


if __name__ == '__main__':
    main()
