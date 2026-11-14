#!/usr/bin/env python3
"""冬の特集記事の写真の候補に、Flickr の写真を足す（2026-11-13。運営者の指示「残りは flickr でいい写真ないか確かめて」）

  python3 scripts/winter_photos_flickr.py [<記事>_<山ID> ...]
      Flickr の検索ページで、商用で使えて加工してよいライセンス（CC BY 2.0/4.0・CC BY-SA 2.0/4.0・CC0・パブリックドメイン）の写真を探し、
      写真のページで撮影地・説明・撮影日・作者・ライセンスを確かめて、関係があり記事に合う写真（日の出・富士山・雪）だけを .claude/winter_photos/<記事>_<山ID>.json の flickr に入れる。
      そのあと python3 scripts/winter_photos.py all でページを作り直すと、F番号で出る
Flickr の API の鍵は使っていない（無い）。機械でまとめて読まないよう、1山あたり検索4回・写真のページ25枚まで、3秒おきにする。
決まり（山の近くで撮ったか・名前と地名・記事に合う語）は winter_photos.py の候補の決まりと同じ。
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import winter_photos as WP  # noqa: E402

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh) YamatchPhotoCheck'}
LIC_OK = {4: 'CC BY 2.0', 5: 'CC BY-SA 2.0', 9: 'CC0 1.0', 10: 'Public Domain Mark', 11: 'CC BY 4.0', 12: 'CC BY-SA 4.0'}
LIC_URL = {4: 'https://creativecommons.org/licenses/by/2.0/', 5: 'https://creativecommons.org/licenses/by-sa/2.0/',
           9: 'https://creativecommons.org/publicdomain/zero/1.0/', 10: 'https://creativecommons.org/publicdomain/mark/1.0/',
           11: 'https://creativecommons.org/licenses/by/4.0/', 12: 'https://creativecommons.org/licenses/by-sa/4.0/'}
DEFAULT = ['hatsuhinode_mitakesan', 'hatsuhinode_hinodesaan', 'hatsuhinode_tsukuba', 'hatsuhinode_oyama', 'hatsuhinode_ryugatake',
           'diamond_ryugatake', 'diamond_nanaitsurasan', 'diamond_nokogiriyama_chiba',
           'views_nyukasayama', 'views_okutama', 'views_akagi']
TOPIC2 = {'hatsuhinode': '初日の出', 'diamond': 'ダイヤモンド富士', 'views': '霧氷'}
TOPIC_Q = {'hatsuhinode': ['日の出', 'sunrise'], 'diamond': ['富士山', 'Fuji'], 'views': ['雪', 'snow']}
NAME_Q = {'mitakesan': '御岳山', 'hinodesaan': '日の出山', 'tsukuba': '筑波山', 'oyama': '大山 阿夫利', 'ryugatake': '竜ヶ岳',
          'nanaitsurasan': '七面山', 'nokogiriyama_chiba': '鋸山', 'nyukasayama': '入笠山', 'okutama': '大菩薩', 'akagi': '赤城山'}
last = [0.0]


def get(url):
    wait = 3 - (time.time() - last[0])
    if wait > 0:
        time.sleep(wait)
    last[0] = time.time()
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode('utf-8', 'replace')


def export(html):
    i = html.find('modelExport:')
    if i < 0:
        return None
    j = html.find('\n', i)
    return json.loads(html[i + len('modelExport:'):j].strip().rstrip(','))['main']


def search(text, center=None, km=None):
    q = {'text': text, 'license': '4,5,9,10,11,12', 'per_page': 50}
    if center:
        q.update({'has_geo': 1, 'lat': '%.5f' % center[0], 'lon': '%.5f' % center[1], 'radius': km, 'radius_units': 'km'})
    m = export(get('https://www.flickr.com/search/?' + urllib.parse.urlencode(q)))
    data = m['search-photos-lite-models'][0]['data']['photos']['data']['_data'] if m else []
    out = []
    for p in data:
        if p:
            p = p.get('data', p)
            out.append((p['id'], p.get('ownerNsid') or p.get('pathAlias'), p.get('title') or ''))
    return out


def photo(pid, owner):
    url = 'https://www.flickr.com/photos/%s/%s/' % (owner, pid)
    html = get(url)
    m = export(html)
    pm = m['photo-models'][0]['data']
    lic = int(pm.get('license'))
    if lic not in LIC_OK:
        return None
    ow = (pm.get('owner') or {}).get('data') or {}
    geo = (m.get('photo-geo-models') or [{}])[0].get('data') or {}
    head = (m.get('photo-head-meta-models') or [{}])[0].get('data') or {}
    sizes = pm['sizes']['data']
    big = next((sizes[k]['data'] for k in ('k', 'h', 'b', 'c', 'z') if k in sizes), None)
    if not big or max(big.get('width') or 0, big.get('height') or 0) < 800:
        return None
    small = next((sizes[k]['data'] for k in ('z', 'c', 'w', 'n') if k in sizes), big)
    dt = re.search(r'"dateTaken":"([^"]+)"', html)
    tags = re.findall(r'"tagRaw":"([^"]+)"', html) or re.findall(r'/photos/tags/([^/"]+)/', html)
    return {'title': pm.get('title') or '', 'description': (head.get('og:description') or '')[:200], 'tags': tags[:30],
            'license': LIC_OK[lic], 'licenseUrl': LIC_URL[lic], 'author': ow.get('realname') or ow.get('username') or '作者不明',
            'date': (dt.group(1)[:10] if dt else ''), 'coord': (geo['latitude'], geo['longitude']) if geo.get('hasGeo') else None,
            'thumb': 'https:' + small['url'], 'full': 'https:' + big['url'], 'width': big.get('width'), 'height': big.get('height'),
            'pageUrl': 'https://www.flickr.com/photos/%s/%s/' % (owner, pid)}


def judge(art, mid, center, x, via_topic):
    """winter_photos.commons と同じ決まり。via_topic＝Flickr が記事の語で見つけた（タグに入っていることがある）"""
    names = [n.lower() for n in WP.NAMES.get(mid, [])]
    text = ' '.join([x['title'], x['description']] + x['tags']).lower()
    if any(w in text for w in WP.NOT_SUBJECT):
        return None
    name_hit = next((n for n in names if n in text), None)
    near = WP.NEAR_KM[art]
    if x['coord']:
        d = WP.dist_km(center, x['coord'])
        if not (d <= near or (name_hit and d <= 15)):
            return None
        where = '撮影地は山頂から%.1fkm' % d if d <= near else '題・説明に「%s」・撮影地は山頂から%.0fkm' % (name_hit, d)
    else:
        if not name_hit or any(n.lower() in text for n in WP.NOT.get(mid, [])):
            return None
        if mid in WP.REGION and not any(r in text for r in WP.REGION[mid]):
            return None
        d = None
        where = '題・説明・タグに「%s」' % name_hit
    ttext = re.sub(r'日の出(山|町|村|屋|乃)', '', text)
    hit = next((t for t in (w.lower() for w in WP.TOPIC[art]) if t in ttext), None)
    why = '%s：「%s」' % (WP.TOPIC_NAME[art], hit) if hit else None
    if not why and via_topic and d is not None and d <= near:
        why = '%s：Flickr の検索語「%s」に合う' % (WP.TOPIC_NAME[art], via_topic)
    if not why and art == 'views':
        mm = re.match(r'(\d{4})-(\d{2})', x['date'])
        if mm and int(mm.group(2)) in (12, 1, 2, 3) and d is not None and d <= near:
            why = '冬・雪：%s月に撮影' % int(mm.group(2))
    return dict(x, why=why, where=where, dist=d, title='Flickr:' + x['title'], query='')


def run(key):
    art, mid = key.split('_', 1)
    M = WP.mountains()
    SC = json.load(open(os.path.join(ROOT, 'data', 'summit_coords.json'), encoding='utf-8'))['mountains']
    sc = SC.get(mid) or {}
    center = (sc.get('lat') or M[mid]['lat'], sc.get('lng') or M[mid]['lng'])
    found = []   # (id, owner, title, 記事の語で見つけたか)
    seen = set()
    for t in TOPIC_Q[art]:
        for pid, ow, title in search(t, center, max(WP.NEAR_KM[art], 2)):
            if pid not in seen:
                seen.add(pid)
                found.append((pid, ow, title, t))
    # 名前だけで広く探す（語を並べるとほとんど見つからない）。記事に合うかは写真のページの題・説明・撮影日で見る
    for t in [NAME_Q[mid], WP.EN[mid]]:
        for pid, ow, title in search(t):
            if pid not in seen:
                seen.add(pid)
                found.append((pid, ow, title, None))
    out = []
    for pid, ow, title, via in found[:25]:
        try:
            x = photo(pid, ow)
        except Exception as e:  # 読めない写真は飛ばす
            print('  読めない', pid, e)
            continue
        if x:
            j = judge(art, mid, center, x, via)
            # Flickr からは記事に合う写真だけ（山の近くの夏の写真などは Commons の候補で足りている）
            if j and j['why']:
                out.append(j)
    out.sort(key=lambda c: (c['why'] is None, c['dist'] if c['dist'] is not None else 99))
    f = os.path.join(WP.WORK, key + '.json')
    d = json.load(open(f, encoding='utf-8'))
    d['flickr'] = out
    json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%-32s 見つかった %d 枚のうち %d 枚を確かめ、候補 %d 枚（記事に合う %d）' % (
        key, len(found), min(25, len(found)), len(out), len([c for c in out if c['why']])))


if __name__ == '__main__':
    for k in sys.argv[1:] or DEFAULT:
        run(k)
