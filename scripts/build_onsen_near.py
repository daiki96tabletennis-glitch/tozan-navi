"""下山後に寄れそうな温泉・サウナがある山の一覧 data/onsen_near_mountains.json を作る（2026-11-17〜。運営者の指示
「温泉サウナはざっくり調べて該当しそうな山をピックアップして。温泉地近くの山や温泉記事に記載されている山と近い山は当てはまる」）。
冬の山選び診断（/find/winter/。scripts/build_winter_find.py）の「温泉・サウナで温まりたい」に使う。ざっくりの目安で、営業期間・料金は確かめていない。

山ごとに、次のどれかに当たれば載せる（理由 why と、近い施設 near を残す）：
  - article：温泉・サウナの記事（onsen_sauna.json）・サウナシュランの記事（saunachelin_hiking.json）の山
  - name：電車・バスの経路・登山口・駐車場の名前に温泉地の名前がある（鶴巻温泉・中房温泉など。コース名は使わない＝登山道の途中の山小屋の温泉が入るため）。
          ほかの決まりに当たらず名前だけで当たる山は、日帰り入浴を確かめた NAME_CHECKED の山だけ
  - osm：地図ボタンの行き先（駐車場）から 3km 以内に、OpenStreetMap の温泉・日帰り入浴・サウナがある
        （amenity=public_bath は bath:type が onsen か、名前に温泉・鉱泉・の湯などがあるものだけ。足湯・手湯・閉館・関係者のみは除く）
  - nearArticle：記事の山の駐車場、またはサウナシュランの施設から 5km 以内
OpenStreetMap は Overpass API で一度だけ読み、--fetch のときだけ取り直す（キャッシュは .claude/osm_baths.json。コミットしない）。
出典の表記：© OpenStreetMap contributors（ODbL）。
"""
import json
import math
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'onsen_near_mountains.json')
CACHE = os.path.join(ROOT, '.claude', 'osm_baths.json')
QUERY = """[out:json][timeout:180];
(
  nwr["amenity"="public_bath"](34.6,136.4,38.6,141.2);
  nwr["leisure"="sauna"](34.6,136.4,38.6,141.2);
  nwr["amenity"="sauna"](34.6,136.4,38.6,141.2);
);
out center tags;"""
OSM_KM = 3.0
# 温泉地の名前だけで当たる山：日帰り入浴があるかを確かめた結果（2026-11-17。各施設の案内・温泉の紹介サイトの掲載）。ここに無い山は入れない
#  花敷温泉（白砂山）は宿泊の宿だけで日帰り入浴が見つからず、同じ道沿いの応徳温泉「くつろぎの湯」（道の駅六合の隣）・尻焼温泉 星ヶ岡山荘にある
NAME_CHECKED = {
    'nikko_shirane': '日光湯元温泉（奥日光高原ホテル・休暇村日光湯元など）',
    'yakedake': '中の湯温泉旅館',
    'azuma': '白布温泉 東屋',
    'zaosan': '蔵王温泉の共同浴場（上湯・下湯など）',
    'shirasunayama': '応徳温泉 くつろぎの湯（道の駅六合の隣）',
}
ARTICLE_KM = 5.0
ONSEN_NAME = re.compile(r'([^\s→（）()、・「」>\-\[\]〜～：:]{1,8}温泉)')


def fetch():
    r = subprocess.run(['curl', '-s', '-A', 'yamatch-site-builder/1.0', '--data-urlencode', 'data=' + QUERY,
                        'https://overpass-api.de/api/interpreter'], capture_output=True)
    d = json.loads(r.stdout.decode('utf-8'))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(d, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    return d


def facilities(d):
    out = []
    for e in d['elements']:
        t = e.get('tags') or {}
        lat = e.get('lat') or (e.get('center') or {}).get('lat')
        lng = e.get('lon') or (e.get('center') or {}).get('lon')
        name = t.get('name') or ''
        if lat is None or not name or re.search(r'足湯|手湯|閉館|休業|廃業|[Gg]uest ?[Hh]ouse|ゲストハウス', name):
            continue
        if t.get('access') in ('private', 'no', 'customers'):
            continue
        ok = (t.get('bath:type') in ('onsen', 'hot_spring') or re.search(r'温泉|鉱泉|の湯|ゆ〜|の郷', name)
              or t.get('leisure') == 'sauna' or t.get('amenity') == 'sauna')
        if ok:
            out.append((lat, lng, name.split(';')[-1].strip()))
    return out


def coords(m):
    u = (m.get('gmapUrl') or '').replace('%2C', ',')
    r = re.search(r'query=(-?\d+\.\d+),(-?\d+\.\d+)', u) or re.search(r'destination=(-?\d+\.\d+),(-?\d+\.\d+)', u)
    return (float(r.group(1)), float(r.group(2))) if r else None


def dist(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def name_hits(m):
    names = []
    for r in ((m.get('trainRoutes') or {}).get('routes') or {}).values():
        for l in (r or {}).get('legs') or []:
            for k in ('from', 'to', 'station', 'name'):
                if isinstance(l.get(k), str):
                    names.append(l[k])
            meth = l.get('method') or {}
            for k in ('line', 'to', 'from'):
                if isinstance(meth.get(k), str):
                    names.append(meth[k])
    for k in ('trailhead', 'parking', 'driveTarget'):
        if isinstance(m.get(k), str):
            names.append(m[k])
    # コース名は使わない（白馬鑓温泉・赤湯温泉など、登山道の途中の山小屋の温泉が入るため。2026-11-17）
    found = []
    for x in ONSEN_NAME.findall(' '.join(names)):
        x = re.sub(r'^.*[「『]', '', x)
        x = re.sub(r'^.*バス', '', x)
        if len(x) >= 3 and x not in found:
            found.append(x)
    return found


def build(osm):
    M = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    ON = json.load(open(os.path.join(ROOT, 'data', 'onsen_sauna.json'), encoding='utf-8'))
    SA = json.load(open(os.path.join(ROOT, 'data', 'saunachelin_hiking.json'), encoding='utf-8'))
    by = {m['id']: m for m in M}
    art = {}
    for p in ON['plans']:
        art.setdefault(p['id'], []).extend(f['name'] for f in p.get('facilities') or [])
    for s in SA['saunas']:
        for mm in s.get('mountains') or []:
            art.setdefault(mm['id'], []).append(s['name'])
    anchors = []  # 記事の山の駐車場・サウナの位置
    for mid, names in art.items():
        c = coords(by[mid]) if mid in by else None
        if c:
            anchors.append((c, by[mid]['name'], names[0]))
    for s in SA['saunas']:
        if s.get('lat') and s.get('lng'):
            anchors.append(((s['lat'], s['lng']), None, s['name']))
    F = facilities(osm)
    out = {}
    for m in M:
        why, near = [], None
        if m['id'] in art:
            why.append('article')
            near = art[m['id']][0]
        c = coords(m)
        if c:
            best = min(((dist(c, (f[0], f[1])), f[2]) for f in F), default=None)
            if best and best[0] <= OSM_KM:
                why.append('osm')
                near = near or best[1]
            if m['id'] not in art:
                a = min(((dist(c, x[0]), x) for x in anchors), default=None)
                if a and a[0] <= ARTICLE_KM:
                    why.append('nearArticle')
                    near = near or a[1][2]
        nh = name_hits(m)
        if nh:
            if why:
                why.append('name')
            elif m['id'] in NAME_CHECKED:
                # 温泉地の名前だけで当たる山は、日帰り入浴があると確かめた山だけ（花敷温泉のように宿泊の宿だけの温泉地があるため）
                why.append('name')
                near = NAME_CHECKED[m['id']]
        if why:
            out[m['id']] = {'name': m['name'], 'why': why, 'near': near}
    return {'_note': 'scripts/build_onsen_near.py が作る（手で編集しない）。下山後に寄れそうな温泉・サウナがある山（ざっくりの目安。営業期間・料金は未確認）。'
                     '近い施設の一部は © OpenStreetMap contributors（ODbL）',
            'mountains': out}


def main():
    if '--fetch' in sys.argv or not os.path.exists(CACHE):
        osm = fetch()
    else:
        osm = json.load(open(CACHE, encoding='utf-8'))
    d = build(osm)
    s = json.dumps(d, ensure_ascii=False, indent=1) + '\n'
    open(OUT, 'w', encoding='utf-8').write(s)
    cnt = {}
    for v in d['mountains'].values():
        for w in v['why']:
            cnt[w] = cnt.get(w, 0) + 1
    print('書いた：data/onsen_near_mountains.json（%d山）' % len(d['mountains']), cnt)


if __name__ == '__main__':
    main()
