"""冬の山選び診断の「車（ノーマルタイヤ）」の判定に使う、駐車場の標高と月ごとの目安 data/winter_road.json を作る（2026-11-17〜。運営者の指示
「車のノーマル、スタッドレスの判断は調べたの？」→「おすすめで（駐車場の標高で全山に目安＋高い所・峠道は個別に確認）。調査結果は過程とともに記録しておいて」）。
調べた過程と根拠の全文は .claude/winter_road_research_2026_11.md。

- 駐車場の位置：地図ボタンの行き先（gmapUrl）の座標。座標の無い山は ALT_POINT（国土地理院の地名検索など）か、山頂が低くて駐車場がそれより低いと確かなもの（SUMMIT_LOW）
- 標高：国土地理院の標高API（getelevation.php）。キャッシュは .claude/parking_elev.json（--fetch で取り直す）
- ノーマルタイヤで行ける目安（月ごと）：駐車場の標高が LIMIT 未満。気象庁の平年値（1991〜2020年）の「積雪1cm以上の日数」で決めた
    1・2月 500m（秩父232m・甲府273mは1月3〜6日、飯田516mは7.9日、松本610mは11.3日、河口湖860mは13.0日）
    12・3月 800m（12月は飯田・松本・諏訪・河口湖で2.6〜3.6日、軽井沢999mで7.9日。3月は河口湖5.2日・軽井沢11.3日）
    11月 1,200m（11月は奥日光1,292mで1.3日、軽井沢0.5日、それより下はほぼ0）
- 日本海側の豪雪地帯（新潟県）の山は標高に関係なく冬用タイヤ（みなかみ524mで1月の最深積雪119cm）。2026-11-17 時点で500m未満の駐車場の山はすべて太平洋側
- 個別に確かめた山は NOTES（出典つき）。道の途中に駐車場より高い峠がある山は、駐車場の標高だけでは分からない（記録に書いた）
mountains.json の地図の行き先を変えたら流し直し、そのあと build_winter_find.py。
"""
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'winter_road.json')
CACHE = os.path.join(ROOT, '.claude', 'parking_elev.json')
LIMIT = {'11': 1200, '12': 800, '1': 500, '2': 500, '3': 800}
# 地図の行き先に座標が無い山：位置を別に取った山
ALT_POINT = {
    'myojingatake': (35.263847, 139.048584, '国土地理院の地名検索「箱根町宮城野」（地図の行き先は宮城野支所前のバス停。町の代表点なので目安）'),
    'kogashiyama': (36.6199, 139.7925, '地図ボタンの行き先の文にある座標（宇都宮市森林公園駐車場）'),
}
# 山頂が700m未満で、駐車場がそれより低いと確かな山（座標が無い）
SUMMIT_LOW = {'iwadonoyama', 'hafuzan_chichibu', 'kannokura'}
# 個別に確かめた山（出典つき）。判定は標高の決まりのまま、カードの注意に出す
NOTES = {
    'ohnoyama': '国土交通省 横浜国道事務所「しっかり準備！ウィンタードライブ」：山北町の山間部ではノーマルタイヤで積雪・凍結により動けなくなる事態が起きている',
    'myojingatake': '国土交通省 横浜国道事務所「しっかり準備！ウィンタードライブ」：箱根峠の山間部ではノーマルタイヤで積雪・凍結により動けなくなる事態が起きている',
    'kintoki': '国土交通省 横浜国道事務所「しっかり準備！ウィンタードライブ」：箱根峠の山間部ではノーマルタイヤで積雪・凍結により動けなくなる事態が起きている',
    'dodairasan': '堂平天文台（星と緑の創造センター）の案内：白石峠からの道は冬は積雪・凍結するので冬用タイヤを勧める（予約サイトに載っている施設の案内文で確認。施設の公式ページでは未確認）',
}
SOURCES = [
    {'label': '気象庁 過去の気象データ 平年値（1991〜2020年）積雪1cm以上の日数', 'url': 'https://www.data.jma.go.jp/stats/etrn/index.php'},
    {'label': '国土地理院 標高API', 'url': 'https://maps.gsi.go.jp/development/elevation_s.html'},
    {'label': '国土交通省 横浜国道事務所「しっかり準備！ウィンタードライブ」', 'url': 'https://www.ktr.mlit.go.jp/yokohama/yokokoku_index015.html'},
]


def coords(m):
    u = (m.get('gmapUrl') or '').replace('%2C', ',')
    r = re.search(r'query=(-?\d+\.\d+),(-?\d+\.\d+)', u) or re.search(r'destination=(-?\d+\.\d+),(-?\d+\.\d+)', u)
    return (float(r.group(1)), float(r.group(2))) if r else None


def elev(lat, lng):
    url = 'https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php?lon=%s&lat=%s&outtype=JSON' % (lng, lat)
    req = urllib.request.Request(url, headers={'User-Agent': 'yamatch-site-builder/1.0'})
    d = json.loads(urllib.request.urlopen(req, timeout=20).read())
    time.sleep(0.5)
    return d.get('elevation') if isinstance(d.get('elevation'), (int, float)) else None


def main():
    fetch = '--fetch' in sys.argv
    C = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    M = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    out = {}
    for m in M:
        mid = m['id']
        c = coords(m)
        where = '地図ボタンの行き先（駐車場）'
        if not c and mid in ALT_POINT:
            c = ALT_POINT[mid][:2]
            where = ALT_POINT[mid][2]
        e = None
        if c:
            hit = C.get(mid)
            if hit and hit.get('lat') == c[0] and hit.get('lng') == c[1] and not fetch:
                e = hit.get('elev')
            else:
                e = elev(c[0], c[1])
                C[mid] = {'lat': c[0], 'lng': c[1], 'elev': e}
        item = {'elev': round(e) if isinstance(e, (int, float)) else None, 'where': where}
        snow_region = '新潟県' in (m.get('area') or '')
        nt = {}
        for mo, lim in LIMIT.items():
            if snow_region:
                nt[mo] = False
            elif item['elev'] is not None:
                nt[mo] = item['elev'] < lim
            elif mid in SUMMIT_LOW and (m.get('elevation') or 9999) < 700:
                nt[mo] = (m.get('elevation') or 9999) < lim
                item['where'] = '駐車場の位置は無いが、山頂が%sm（駐車場はそれより低い）' % m.get('elevation')
            else:
                nt[mo] = None  # 分からない（ノーマルタイヤでは出さない）
        item['normal'] = nt
        if snow_region:
            item['snowRegion'] = True
        if mid in NOTES:
            item['note'] = NOTES[mid]
        out[mid] = item
    json.dump(C, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    d = {'_note': 'scripts/build_winter_road.py が作る（手で編集しない）。駐車場の標高と、ノーマルタイヤで行ける目安（月ごと）。根拠は .claude/winter_road_research_2026_11.md',
         'limit': LIMIT, 'sources': SOURCES, 'mountains': out}
    open(OUT, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + '\n')
    unk = [v for v in out.values() if v['elev'] is None and not any(x is not None for x in v['normal'].values())]
    print('書いた：data/winter_road.json（%d山。標高が分からない山 %d）' % (len(out), len(unk)))


if __name__ == '__main__':
    main()
