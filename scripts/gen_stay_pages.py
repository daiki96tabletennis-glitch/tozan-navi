#!/usr/bin/env python3
"""前泊の宿のページ /stay/<山ID>/ を作る（手で編集しない。生成物）。

  python3 scripts/gen_stay_pages.py            # data/lodging_areas.json にある山を全部
  python3 scripts/gen_stay_pages.py kitadake   # 指定した山だけ

- 宿を探す場所は data/lodging_areas.json（scripts/build_lodging_areas.py が作る）。
- 場所ごとの説明は mountains.json の値だけで作る：駅＝そこから終点までの乗り物と時間、
  車を置く場所＝新宿からの車の時間と、駐車場からのバス（carShuttle）の運賃・期間・出典。
- 近い宿（距離つき）は、ページを開いたときに assets/js/lodging.js が楽天トラベルの施設検索 API で読む（保存しない）。
  読めないときも、楽天トラベルの「周辺のホテル・旅館」のページへのリンクは出る。
- 見た目は山小屋のページ（/huts/<山ID>/）と同じ。CSS は生成済みの huts/index.html から読む。
- いまは検索に出さない（noindex）。宿の一覧は楽天から読むもので、ページの文章としては残らないため（中身が育ったら見直す）。
"""
import html
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = lambda s: html.escape(str(s if s is not None else ''), quote=True)  # noqa: E731
BASE = 'https://tozan-navi.com'
VER = '20261025f'
AFF_ID = '57384242.53497bb8.57384243.366083eb'

ML = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
M = {m['id']: m for m in ML}
LA = json.load(open(os.path.join(ROOT, 'data', 'lodging_areas.json'), encoding='utf-8'))['mountains']
_hp = open(os.path.join(ROOT, 'huts', 'index.html'), encoding='utf-8').read()
CSS = re.search(r'<style>(.*?)</style>', _hp, flags=re.S).group(1)
HEADCOMMON = re.search(r'(<link rel="preconnect" href="https://fonts.googleapis.com">.*?<link rel="manifest" href="/manifest.json">)', _hp, flags=re.S).group(1)
FOOTER = re.search(r'(<footer>.*?</footer>)', _hp, flags=re.S).group(1)

STAY_CSS = '''
.st-pr{font:700 10px/1.4 'Outfit',sans-serif;color:#7a7068;border:1px solid #c9c2b6;border-radius:4px;padding:0 4px;margin-left:6px;vertical-align:3px}
.st-area{background:#fff;border:1px solid #e0dbd4;border-radius:12px;padding:14px 14px 12px;margin-bottom:14px}
.st-area h2{font-family:'Noto Serif JP','Hiragino Mincho ProN',serif;font-size:17px;color:#2a3820;margin:0 0 6px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.st-who{font:700 11px/1.5 'Zen Kaku Gothic New',sans-serif;color:#fff;background:#4e6535;border-radius:20px;padding:1px 9px}
.st-who.car{background:#8a6a3a}.st-who.th{background:#6a8a9a}
.st-why{font-size:13px;color:#3a3530;margin:0 0 4px}
.st-fact{font-size:12.5px;color:#5a5248;margin:0;line-height:1.7}
.st-fact a{color:#4e6535}
.st-hotels{margin-top:10px}
.st-hotels:empty{display:none}
.st-hh{font-size:12px;color:#7a7068;margin:0 0 2px}
.st-item{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-top:1px solid #ece8e1;color:#2f2b26}
.st-ib{flex:1;min-width:0}
.st-onsen{display:inline-block;font-size:10.5px;font-weight:700;color:#9a4a22;background:#fbeee5;border:1px solid #efc9b2;border-radius:4px;padding:0 5px;margin-left:6px;vertical-align:1px}
.st-acc{color:#3a3530}
.st-sat{color:#2a3820}.st-sat.none{color:#8a8278}
.st-plan{display:inline-block;margin-top:6px;padding:5px 10px;font-size:12px;font-weight:700;color:#bf0000;background:#fff;border:1px solid #e3b5b5;border-radius:6px;text-decoration:none}
.st-imgw{flex:0 0 64px}
.st-img{display:block;width:64px;height:64px;object-fit:cover;border-radius:8px;background:#ece8e1}
.st-name{font-size:14px;font-weight:700;color:#2a3820;line-height:1.4;text-decoration:none}
.st-meta{display:block;font-size:12px;color:#6a6258;line-height:1.6;margin-top:1px}
.st-meta b{font-family:'Outfit',sans-serif;color:#2a3820}
.st-rk{display:block;margin-top:10px;padding:11px 14px;background:#eef4e8;border:1px solid #c8d4b8;border-radius:10px;color:#2a3820;font-size:13.5px;font-weight:700;text-decoration:none}
.st-rk small{display:block;font-size:11.5px;font-weight:400;color:#5a6a4a;margin-top:1px}
.st-links{display:flex;flex-direction:column;gap:8px;margin:18px 0 6px}
.st-links a{display:block;padding:11px 14px;background:#fff;border:1px solid #e0dbd4;border-radius:10px;color:#2a3820;font-size:13.5px;font-weight:700;text-decoration:none}
.st-credit{text-align:right;font-size:10.5px;margin:6px 0 0}
.mtlb{background:none;border:none}.mtlb span{color:#b4532a}
.stpin{background:none;border:none}.stpin b{display:inline-block;white-space:nowrap;background:#2a3820;color:#fff;font:700 11px/1.5 'Zen Kaku Gothic New',sans-serif;padding:1px 7px;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.3)}
'''

SHELL = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="noindex,follow">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:type" content="article">
<meta property="og:url" content="%(url)s">
<link rel="canonical" href="%(url)s">
%(head)s
<style>%(css)s%(stay_css)s</style>
</head>
<body>
<!-- generated: scripts/gen_stay_pages.py -->
<header>
  <div class="header-inner">
    <a href="/" style="display:flex;align-items:center;gap:6px;text-decoration:none;flex:1;min-width:0;"><svg width="24" height="24" viewBox="0 0 36 36" style="flex-shrink:0"><polygon points="18,4 34,30 2,30" fill="#405830"/><polygon points="18,10 30,30 6,30" fill="#789858"/><polygon points="10,30 17,17 24,30" fill="#2c4020"/></svg><div class="header-title" style="color:white;font-size:20px;font-weight:700;font-family:Georgia,serif;line-height:1;">Yamatch</div></a>
    <span style="flex:1"></span>
    <a href="/mountains/%(mid)s/" class="back-btn">← %(name)sの登山情報</a>
  </div>
</header>
<main>
%(body)s
</main>
%(footer)s
<script>window.YM_STAY=%(data)s;</script>
<script src="/assets/js/lodging.js?v=%(ver)s" defer></script>
<script src="/assets/js/to-top.js?v=20261025a" defer></script>
</body>
</html>
"""


def topo_hero(lat, lng, kicker, title, sub, zoom):
    """国土地理院の地形図を帯状に敷いたヘッダー（山小屋のページと同じ作り）"""
    n = 2 ** zoom
    xf = (lng + 180.0) / 360.0 * n
    yf = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    tx, ty = int(xf), int(yf)
    px, py = (xf - tx) * 256, (yf - ty) * 256
    imgs = []
    for r in (-1, 0, 1):
        for c in (-2, -1, 0, 1, 2):
            imgs.append('<img src="https://cyberjapandata.gsi.go.jp/xyz/std/%d/%d/%d.png" alt="" width="256" height="256"%s>' % (
                zoom, tx + c, ty + r, '' if abs(c) <= 1 and r >= 0 else ' loading="lazy"'))
    return ('<div class="topo">\n<div class="topo-map" aria-hidden="true" style="margin-left:-%dpx;margin-top:-%dpx">%s</div>\n'
            '<div class="topo-cap"><div class="topo-k">%s</div><h1>%s</h1><div class="topo-s">%s</div></div>\n'
            '<a class="topo-src" href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル</a>\n</div>\n' % (
                int(round(2 * 256 + px)), int(round(256 + py)), ''.join(imgs), kicker, title, sub))


def clean(name):
    return re.sub(r'[（(].*?[）)]', '', name or '').strip()


def hm(minutes):
    h, mm = divmod(int(minutes), 60)
    if not h:
        return '%d分' % mm
    return '%d時間%s' % (h, ('%d分' % mm) if mm else '')


def aff(url):
    from urllib.parse import quote
    q = quote(url, safe='')
    return 'https://hb.afl.rakuten.co.jp/hgc/%s/?pc=%s&m=%s' % (AFF_ID, q, q)


def legs_from(m, station):
    """新宿からの経路で、その駅から終点までの乗り物と時間。分からなければ None"""
    legs = (((m.get('trainRoutes') or {}).get('routes') or {}).get('shinjuku') or {}).get('legs') or []
    for i, leg in enumerate(legs):
        if clean(leg.get('station')) == station:
            rest = legs[i:-1]
            if not rest or any(x.get('durationMin') is None for x in rest):
                return None
            lines = [((x.get('method') or {}).get('line') or '').strip() for x in rest]
            return '・'.join(l for l in lines if l), sum(x['durationMin'] for x in rest), clean(legs[-1].get('station'))
    return None


def facts(m, a):
    """場所ごとの説明（データにある値だけ）"""
    out = []
    if a['kind'] == 'station':
        lf = legs_from(m, a['name'])
        if lf:
            out.append('%sで%sまで約%s（%sの登山情報の電車・バスの欄より）' % (E(lf[0]), E(lf[2]), hm(lf[1]), E(m['name'])))
    if a['kind'] == 'parking':
        if m.get('driveTarget') and clean(m['driveTarget']) == a['name'] and m.get('driveTimeShinjuku'):
            out.append('新宿から車で約%s（渋滞を含まない目安）' % hm(m['driveTimeShinjuku']))
        cs = m.get('carShuttle')
        if cs and (a['name'] in (cs.get('route') or '') or clean(m.get('driveTarget')) == a['name']):
            t = '%s：%s' % (E(cs.get('route')), E(cs.get('fare')))
            if cs.get('period'):
                t += '。運行は%s' % E(cs['period'])
            if cs.get('url'):
                t += '（<a href="%s" target="_blank" rel="noopener">%s</a>）' % (E(cs['url']), E(cs.get('linkText') or '出典'))
            out.append(t)
    return out


WHO = {'station': ('電車・バスで行く人', ''), 'parking': ('車で行く人', ' car'), 'trailhead': ('登山口のそば', ' th')}


def page(mid):
    m = M[mid]
    areas = [a for a in LA[mid]['areas'] if a.get('lat') is not None and not a.get('needsVerification')]
    if not areas:
        return None
    name = m['name']
    shown = [a for a in areas if a.get('rakuten')]
    names = '・'.join(a['name'] for a in shown) or '・'.join(a['name'] for a in areas)
    blocks = []
    for i, a in enumerate(areas):
        who, cls = WHO[a['kind']]
        fs = facts(m, a)
        rk = a.get('rakuten')
        # 楽天トラベルのページが無い場所は、近くの宿が API で見つかったときだけ出す
        hidden = '' if rk else ' hidden data-api-only="1"'
        blocks.append(
            '<section class="st-area" data-st-area="%d"%s>\n<h2>%sの周り<span class="st-who%s">%s</span></h2>\n'
            '<p class="st-why">%s。</p>\n%s<div class="st-hotels" data-st-hotels="%d"></div>\n%s</section>' % (
                i, hidden, E(a['name']), cls, who, E(a['via']),
                ''.join('<p class="st-fact">%s</p>\n' % f for f in fs), i,
                ('<a class="st-rk" href="%s" target="_blank" rel="nofollow sponsored noopener" '
                 'onclick="if(window.gtag){gtag(\'event\',\'lodging_click\',{mountain_id:\'%s\',area:\'%s\',hotel_no:\'list\'})}">'
                 '楽天トラベルで「%s 周辺のホテル・旅館」を見る →<small>日付・人数を入れて空室と料金を探せます</small></a>\n' % (
                     E(aff(rk['url'])), E(mid), E(a['name']), E(rk['label']))) if rk else ''))
    lat = sum(a['lat'] for a in areas) / len(areas)
    lng = sum(a['lng'] for a in areas) / len(areas)
    title = '%sの前泊の宿｜%sの周りの宿' % (name, names)
    desc = '%sに登る前の晩に泊まる宿を、電車・バスで行く人と車で行く人に分けてまとめました（%s）。楽天トラベルの宿を、乗り換える場所から近い順に出します。' % (name, names)
    links = ['<a href="/mountains/%s/">%sの登山情報（アクセス・コース・装備）→</a>' % (E(mid), E(name))]
    if os.path.exists(os.path.join(ROOT, 'huts', mid, 'index.html')):
        links.append('<a href="/huts/%s/">%sの山小屋（予約開始日・予約方法）→</a>' % (E(mid), E(name)))
    body = (
        topo_hero(lat, lng, E(m.get('area') or ''), '%sの前泊の宿<span class="st-pr">PR</span>' % E(name), E(names), zoom=11)
        + '<nav class="bc" aria-label="パンくず"><a href="/">Yamatch</a> › <a href="/mountains/%s/">%s</a> › 前泊の宿</nav>\n' % (E(mid), E(name))
        + '<p class="lead">%sに登る前の晩に泊まる場所を、電車・バスで行く人と車で行く人に分けてまとめました。'
          '場所は、%sの登山情報の電車・バスと車のデータから選んでいます。宿は楽天トラベルに載っているものです。</p>\n' % (E(name), E(name))
        + '\n'.join(blocks) + '\n'
        + '<h2 class="sec">地図</h2>\n<div id="smap" class="hmap" role="region" aria-label="前泊の宿を探す場所の地図"></div>\n'
        + '<div class="st-links">%s</div>\n' % ''.join(links)
        + '<p class="src">宿の一覧は楽天トラベルのものです。空室・料金・チェックインの時間や朝食の時間は、楽天トラベルと各宿の案内で確かめてください。'
          '土曜泊の料金は、直近4回の土曜の中で大人1人・1室の空室がある日の、楽天トラベルでいちばん安いプランの料金です（ページを開いたときの値。食事の有無はプランによります）。距離は乗り換える場所からの直線の距離で、歩く距離ではありません。バスの時刻・運行期間は年によって変わります。当サイトは楽天アフィリエイトを利用しています。</p>\n'
        + '<p class="st-credit" id="st-credit" hidden><a href="https://developers.rakuten.com/" target="_blank">Supported by Rakuten Developers</a></p>')
    data = {'mid': mid, 'name': name, 'areas': [
        {'name': a['name'], 'kind': a['kind'], 'lat': a['lat'], 'lng': a['lng'], 'r': a['radiusKm']} for a in areas]}
    text = SHELL % {'title': E(title), 'desc': E(desc), 'url': BASE + '/stay/%s/' % mid, 'head': HEADCOMMON, 'css': CSS,
                    'stay_css': STAY_CSS, 'mid': E(mid), 'name': E(name), 'body': body, 'footer': FOOTER,
                    'data': json.dumps(data, ensure_ascii=False).replace('</', '<\\/'), 'ver': VER}
    assert text.rstrip().endswith('</html>') and text.count('<div') == text.count('</div>'), mid
    out = os.path.join(ROOT, 'stay', mid, 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(text)
    return out


def main():
    ids = sys.argv[1:] or list(LA.keys())
    for mid in ids:
        if mid not in LA:
            sys.exit('%s: data/lodging_areas.json にありません' % mid)
        print(page(mid) or '%s: 出せる場所が無い' % mid)


if __name__ == '__main__':
    main()
