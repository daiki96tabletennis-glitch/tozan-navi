#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋まとめ（β）ページ huts/index.html を data/huts.json から作る。使い方：python3 scripts/gen_huts_page.py
作るページ：一覧 /huts/、山ごと /huts/<山ID>/、山小屋ごと /huts/<小屋ID>/（予約の開始も方法も分からない小屋は noindex）。sitemap.xml の /huts/ 以下も入れ直す。
以前の /huts/?m=山ID は、山ごとのページへ送る。"""
import html, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = lambda s: html.escape(str(s or ''), quote=True)
d = json.load(open(os.path.join(ROOT, 'data', 'huts.json'), encoding='utf-8'))
ML = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
M = {m['id']: m for m in ML}
H = d['huts']
_cp = os.path.join(ROOT, 'data', 'huts_coords.json')
COORDS = json.load(open(_cp, encoding='utf-8'))['huts'] if os.path.exists(_cp) else {}
MAP_VER = '20261020a'
import calendar, math, sys
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import huts_season
import huts_rules
from huts_features import FEATURES
assert set(FEATURES) <= set(h['name'] for h in H), set(FEATURES) - set(h['name'] for h in H)
_sp = os.path.join(ROOT, 'data', 'summit_coords.json')
SUMMITS = json.load(open(_sp, encoding='utf-8'))['mountains'] if os.path.exists(_sp) else {}


def _km(a, b, c, d2):
    p = math.radians
    x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d2 - b) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


def place_text(h):
    """山小屋のだいたいの場所を、位置データから文にする（山頂からの直線距離と、分かれば標高の差）。
    位置の分からない小屋・山は None。距離は直線で、歩く距離ではない"""
    c = COORDS.get(h['name'])
    if not c:
        return None
    best = None
    # ルート上の山（mountainIds）を先に見て、無ければ別ルート・縦走で使う山から、いちばん近い山頂を選ぶ
    for ids in (h['mountainIds'], [o['id'] for o in h.get('otherMountains') or []]):
        for i in ids:
            s = SUMMITS.get(i)
            if s:
                d = _km(c['lat'], c['lng'], s['lat'], s['lng'])
                if best is None or d < best[0]:
                    best = (d, i)
        if best:
            break
    if not best:
        return None
    d, i = best
    m = M[i]
    ele = c.get('ele')
    if ele is None:
        mm = re.search(r'標高\s*([\d,]{3,5})\s*m', h.get('location') or '')
        ele = int(mm.group(1).replace(',', '')) if mm else None
    low = (m['elevation'] - ele) if ele else None
    dist = '%sの山頂から直線で約%s' % (m['name'], ('%dm' % (round(d * 10) * 100)) if d < 1 else ('%.1fkm' % d))
    if d <= 0.3:
        kind = '山頂のすぐそば'
    elif d <= 1.5 and (low is None or low <= 400):
        kind = '山頂の近く'
    else:
        # 登山口の近くかどうか：地図ボタンの行き先（gmapUrl の座標＝登山口・駐車場）から1km以内
        g = re.search(r'query=(-?[\d.]+)%2C(-?[\d.]+)', m.get('gmapUrl') or '')
        if g and _km(c['lat'], c['lng'], float(g.group(1)), float(g.group(2))) <= 1 and d > 1.5:
            kind = '登山口の近く'
        elif d > 1.5 or (low is not None and low > 400):
            kind = '山頂から離れた場所（登山道の途中など）'
        else:
            kind = None
    tail = []
    if ele:
        tail.append('標高約%sm' % format(ele, ','))
    if low is not None and low >= 100:
        tail.append('山頂より約%sm低い' % format(int(round(low, -1)), ','))
    return (kind, dist + ('。' + '、'.join(tail) if tail else ''))


def hut_ele(h):
    """山小屋の標高（OpenStreetMap の値、無ければ出典の「標高◯m」）。分からなければ None"""
    c = COORDS.get(h['name']) or {}
    if c.get('ele'):
        return int(c['ele'])
    mm = re.search(r'標高\s*([\d,]{3,5})\s*m', h.get('location') or '')
    return int(mm.group(1).replace(',', '')) if mm else None


def topo_hero(lat, lng, kicker, title, sub, zoom=15, pin=True):
    """国土地理院の地形図（標準地図）を帯状に敷いたヘッダー。指定の地点が中央に来るようにタイルを並べる。JavaScript は使わない"""
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
    return ('<div class="topo">\n<div class="topo-map" aria-hidden="true" style="margin-left:-%dpx;margin-top:-%dpx">%s</div>\n%s'
            '<div class="topo-cap"><div class="topo-k">%s</div><h1>%s</h1>%s</div>\n'
            '<a class="topo-src" href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル</a>\n</div>\n' % (
                int(round(2 * 256 + px)), int(round(256 + py)) + (23 if pin else 0), ''.join(imgs), '<i class="topo-pin" aria-hidden="true"></i>\n' if pin else '',
                kicker, title, ('<div class="topo-s">%s</div>' % sub) if sub else ''))


def season_bar(sj):
    """営業期間を12か月の帯にする。濃い色＝営業、薄い色＝開始・終了の時期（上旬・下旬など幅のある書き方）。期間として読めない小屋は出さない"""
    if not sj or sj.get('closed'):
        return ''
    days = []                       # 月ごとに、日ごとの 0:なし 1:幅 2:営業
    for mth in range(1, 13):
        nd = calendar.monthrange(2001, mth)[1]
        row = []
        for dd in range(1, nd + 1):
            v = 2 if sj.get('all') else 0
            for r in sj.get('r') or []:
                if (r[0], r[2]) <= (mth, dd) <= (r[3], r[4]):
                    v = 2
                elif (r[0], r[1]) <= (mth, dd) < (r[0], r[2]) or (r[3], r[4]) < (mth, dd) <= (r[3], r[5]):
                    v = max(v, 1)
            row.append(v)
        days.append(row)
    col = {0: 'transparent', 1: '#c3d0b0', 2: '#4e6535'}
    cells = []
    for i, row in enumerate(days):
        stops, start = [], 0
        for k in range(1, len(row) + 1):
            if k == len(row) or row[k] != row[start]:
                stops.append('%s %d%% %d%%' % (col[row[start]], round(start * 100 / len(row)), round(k * 100 / len(row))))
                start = k
        cells.append('<i data-m="%d" style="background:linear-gradient(90deg,%s)"><b>%d</b></i>' % (i + 1, ','.join(stops), i + 1))
    return '<div class="mbar" role="img" aria-label="営業期間を12か月の帯で示した図">%s</div>' % ''.join(cells)


def mt_points(huts):
    """地図に出す山（サイトに載っている山だけ）：その小屋たちが対応している山の山頂"""
    ids = []
    for h in huts:
        for i in h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]:
            if i in SUMMITS and i not in ids:
                ids.append(i)
    return [{'n': M[i]['name'], 'la': SUMMITS[i]['lat'], 'lo': SUMMITS[i]['lng'], 'u': '/mountains/%s/' % i, 'e': M[i]['elevation']} for i in ids]


def map_block(huts, starts, lazy='', mts=True):
    """地図の枠と、ピンのデータ。位置の分かっている小屋だけ出す（分からない小屋は置かない）"""
    pts = []
    for h in huts:
        c = COORDS.get(h['name'])
        if c:
            pts.append({'n': h['name'], 'la': c['lat'], 'lo': c['lng'], 'u': '/huts/%s/' % h['id'], 's': starts.get(h['id']) or ''})
    if not pts:
        return ''
    miss = [h['name'] for h in huts if h['name'] not in COORDS]
    note = ''
    if miss and len(huts) <= 30:
        note = '<p class="mapnote">地図に出ていない小屋（位置を確認できていません）：%s</p>' % E('、'.join(miss))
    elif miss:
        note = '<p class="mapnote">位置を確認できた%d軒を表示しています（%d軒は地図に出ていません）。</p>' % (len(pts), len(miss))
    mp = mt_points(huts) if mts else []
    legend = '<p class="mapnote"><span class="lg lg-h"></span>山小屋　<span class="lg lg-m">▲</span>このサイトで紹介している山（山頂）</p>' if mp else ''
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return ('<div id="hmap" class="hmap"%s role="region" aria-label="山小屋の地図"></div>\n%s%s\n'
            '<script>window.YM_HUT_PTS=%s;window.YM_MT_PTS=%s;</script>\n<script src="/assets/js/huts-map.js?v=%s" defer></script>\n' % (
                (' data-lazy="%s"' % lazy) if lazy else '', legend, note, dump(pts), dump(mp), MAP_VER))
NA = '<span class="na">公式サイトで確認</span>'
# お気に入りの星は、トップページの山の一覧と同じ形
BELL_ICON = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
             'style="vertical-align:-2px;margin-right:4px"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>')
FAV_BTN = ('<button type="button" class="hfav" data-fav="%s" aria-pressed="false" aria-label="お気に入りに追加"><svg width="20" height="20" viewBox="0 0 24 24" '
           'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></button>')
FT_CLS = {'グルメ': 'g', '風呂・温泉': 'b', '設備': 'e', '眺め': 'v', '歴史': 'h'}


def split_note(text):
    """「本文（補足）」→ (本文, 補足)。長い補足を小さい字に回して、要点を読みやすくする"""
    # 文の最後にある括弧だけを補足にする（途中の括弧「夏山（5/25〜11/23泊）は…」で切らない）
    text = text or ''
    if not text.endswith('）'):
        return (text or None, None)
    depth = 0
    for i in range(len(text) - 1, -1, -1):
        if text[i] == '）':
            depth += 1
        elif text[i] == '（':
            depth -= 1
            if depth == 0:
                return (text[:i], text[i + 1:-1]) if i >= 2 else (text, None)
    return (text, None)


def fact(label, main, sub=None, cls=''):
    return '<div class="fact %s"><div class="fl">%s</div><div class="fv">%s</div>%s</div>' % (
        cls, label, main, ('<div class="fs">%s</div>' % sub) if sub else '')


regions = []
for h in H:
    if h['region'] not in regions:
        regions.append(h['region'])
cards = []
count = {}
card_of = {}
info = {}
for h in H:
    au = h.get('auto') or {}
    stale = h.get('bookingStale')
    # 公式サイト・予約サイトから自動で読み取れた値を優先する
    start = (au.get('bookingStart') or {}).get('value') or (None if stale else h.get('bookingStart'))
    # 予約サイトの「予約開始のお知らせ」の日時：手で確認した値が無いとき、または手の値より新しい年のときに使う
    # 公式ページから読めた日付（bookingStartDate）→ 予約サイトのお知らせ（bookingStartWeb）の順に見る
    for web in (au.get('bookingStartDate') or {}, au.get('bookingStartWeb') or {}):
        if web and not (au.get('bookingStart') or {}).get('value'):
            yrs = [int(x) for x in re.findall(r'(20\d\d)年', start or '')]
            if not start or (yrs and max(yrs) < (web.get('year') or 0)):
                start = web['value']
                break
    # 手で確認した値が無い小屋は、予約サイトに登録されている「何日前から予約できるか」を使う
    start = start or (au.get('bookingWindow') or {}).get('value')
    none = None if stale else h.get('bookingNone')
    cap = (au.get('capacity') or {}).get('value') or h.get('capacity')
    methods = None if stale else h.get('bookingMethods')
    ids = h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]
    for i in ids:
        count[i] = count.get(i, 0) + 1
    # 予約の開始
    if none:
        s_html = fact('予約の開始', '予約不要', '予約の受付がない小屋です')
    elif start:
        a, b = split_note(start)
        s_html = fact('予約の開始', E(a), E(b))
        if h.get('officialChanged') and not au.get('bookingStart'):
            s_html = fact('予約の開始', E(a), E((b + '。' if b else '') + '公式サイトの記載に変更あり。最新は公式サイトで確認'))
    elif stale:
        s_html = fact('予約の開始', '<span class="na">確認中</span>', '出典の記載が変わりました')
    elif h.get('bookingStartUnstated'):
        s_html = fact('予約の開始', '<span class="na">記載なし</span>', '公式サイトに、いつから予約できるかの記載がありません。予約先で確認')
    else:
        s_html = fact('予約の開始', NA)
    # 予約方法
    if none:
        m_html = fact('予約方法', '<span class="mt">予約なし</span>', E(none))
    elif methods:
        tags = ''.join('<span class="mt">%s</span>' % E(split_note(x)[0]) for x in methods)
        subs = '／'.join(E(split_note(x)[1]) for x in methods if split_note(x)[1])
        m_html = fact('予約方法', tags, subs or None)
    else:
        m_html = fact('予約方法', NA)
    # 規模
    ref = h.get('capacityRef')
    if cap:
        c_html = fact('規模（定員）', '%s人' % E(cap), ('参考：以前の収容人数は%s人' % ref) if isinstance(ref, int) and ref != cap else None)
    elif isinstance(ref, int):
        c_html = fact('規模（定員）', '約%s人' % ref, '山と溪谷オンラインの記載。現在の定員は公式サイトで確認')
    elif ref:
        c_html = fact('規模（定員）', E(ref), '山と溪谷オンラインの記載')
    else:
        c_html = fact('規模（定員）', '<span class="na">確認中</span>')
    # 営業期間：公式・予約サイトの値があればそれ、無ければ出典の記載
    season = (au.get('season') or {}).get('value')
    raw = h.get('openText') or ''
    season_main = season or re.sub(r'^2026年の営業：', '', raw) or '—'
    season_sub = '公式・予約サイトの記載' if season else None
    if h.get('officialNote'):
        season_sub = '公式サイトの記載：' + h['officialNote']
    mts = ''.join('<a class="mc" href="/mountains/%s/">%s</a>' % (E(i), E(M[i]['name'])) for i in h['mountainIds'])
    oth = ''.join('<a class="mc mc2" href="/mountains/%s/">%s<small>%s</small></a>' % (E(o['id']), E(M[o['id']]['name']), E(o['relation'])) for o in h.get('otherMountains') or [])
    links = []
    if h.get('officialUrl'):
        links.append('<a class="btn" href="%s" target="_blank" rel="noopener">公式サイト</a>' % E(h['officialUrl'].strip()))
    if h.get('bookingSourceUrl') and h['bookingSourceUrl'] != h.get('officialUrl') and 'yamatan.net' in h['bookingSourceUrl']:
        links.append('<a class="btn btn2" href="%s" target="_blank" rel="noopener">予約サイト</a>' % E(h['bookingSourceUrl']))
    detail = []
    sj = huts_season.parse(season or raw)
    st_html = ('<span class="st" data-season="%s"></span>' % E(json.dumps(sj, separators=(',', ':')))) if sj else ''
    pt = place_text(h)
    loc = h.get('location')
    if pt or loc:
        p_main = (('<b class="pk">%s</b>' % E(pt[0])) if pt and pt[0] else '') + (E(pt[1]) if pt else E(loc))
        p_sub = ('<span class="ss">出典の記載：%s</span>' % E(loc)) if (pt and loc) else ''
        place_html = '  <div class="season"><span class="sl">場所</span><span class="sv">%s</span>%s</div>\n' % (p_main, p_sub)
    else:
        place_html = ''
    # 特徴（名物の食事・風呂など）。公式サイトなどで確かめて huts_features.py に書いたものだけ
    ft = FEATURES.get(h['name'])
    if ft:
        feat_html = '  <div class="season"><span class="sl">特徴</span><span class="sv"><ul class="fts">%s</ul></span></div>\n' % ''.join(
            '<li><b class="ftg ftg-%s">%s</b>%s</li>' % (FT_CLS.get(tag, 'o'), E(tag), E(text)) for tag, text in ft['items'])
        if ft.get('src'):
            feat_html = feat_html.replace('</ul></span>', '</ul></span><span class="ss">出典：<a href="%s" target="_blank" rel="noopener" style="color:#4e6535">山岳雑誌の山小屋紹介記事</a>（取材時の内容）</span>' % E(ft['src']))
    else:
        feat_html = ''
    if h.get('tel'):
        detail.append('<div><b>電話</b>%s</div>' % E(h['tel']))
    if raw and season:
        detail.append('<div><b>一覧の出典の記載</b>%s</div>' % E(raw))
    elif raw and raw != season_main:
        detail.append('<div><b>出典の記載</b>%s</div>' % E(raw))
    # 予約の型（お知らせに対応しているか）。対応する小屋のカードには、お知らせの登録欄への入口を出す
    rule = None if none else huts_rules.derive(h['name'], (au.get('bookingStart') or {}).get('value') or (None if stale else h.get('bookingStart')),
                                               (au.get('bookingStartWeb') or {}).get('value'), (au.get('bookingWindow') or {}).get('value'),
                                               autodates=(au.get('bookingStartDate'), au.get('bookingStartWeb'), au.get('bookingStart')))
    if rule:
        links.insert(0, '<a class="btn btn-al" href="/huts/%s/#hut-alert">%s予約開始のお知らせ</a>' % (E(h['id']), BELL_ICON))
    cards.append(
        '<article class="hut" id="%s" data-region="%s" data-m="%s" data-key="%s">\n'
        '  <div class="hh"><h2><a href="/huts/%s/">%s</a></h2>%s<span class="rg">%s</span>%s%s%s</div>\n'
        '  <div class="facts">%s%s%s</div>\n'
        '  <div class="season"><span class="sl">営業期間</span><span class="sv">%s%s</span>%s</div>\n'
        '%s%s'
        '  <div class="mrow"><span class="sl">対応する山</span><span class="mcs">%s%s</span></div>\n'
        '  <div class="foot">%s%s</div>\n'
        '</article>' % (
            E(h['id']), E(h['region']), E(' '.join(ids)), E(h['name'] + ' ' + ' '.join(M[i]['name'] for i in ids)),
            E(h['id']), E(h['name']), ('<span class="el">%s<small>m</small></span>' % format(hut_ele(h), ',')) if hut_ele(h) else '',
            E(h['region']), '<span class="req">予約必須</span>' if h['bookingRequired'] else '', st_html, FAV_BTN % E(h['id']),
            s_html, m_html, c_html, E(season_main), season_bar(sj), ('<span class="ss">%s</span>' % E(season_sub)) if season_sub else '', place_html, feat_html,
            mts, oth, ''.join(links),
            ('<details><summary>くわしく</summary>%s</details>' % ''.join(detail)) if detail else ''))
    card_of[h['id']] = cards[-1]
    info[h['id']] = {'start': None if none else start, 'none': none, 'methods': None if none else methods, 'season': season_main,
                     'cap': cap or (ref if isinstance(ref, int) else None), 'capExact': bool(cap), 'place': pt, 'st': st_html, 'feat': ft,
                     'rule': rule}
# 「山から探す」：小屋のある山を、県・山域の順に並べる
mt_btns = []
for m in ML:
    if m['id'] in count:
        mt_btns.append('<a class="mb" href="/huts/%s/" data-m="%s" data-name="%s">%sの山小屋<span>%d</span></a>' % (E(m['id']), E(m['id']), E(m['name']), E(m['name']), count[m['id']]))
RLABEL = {'その他': '信州のその他（御嶽山・浅間山・美ヶ原ほか）'}
chips = '<button class="chip on" data-r="">すべて</button>' + ''.join('<button class="chip" data-r="%s">%s</button>' % (E(r), E(RLABEL.get(r, r))) for r in regions)
_u = sorted(h['sourceUpdated'] for h in H if h.get('sourceUpdated'))
upd = '%d年%d〜%d月' % (int(_u[0][:4]), int(_u[0][5:7]), int(_u[-1][5:7])) if _u else ''
page = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>山小屋の予約開始日・予約方法まとめ【__YEAR__年】北アルプス・南アルプス・八ヶ岳・富士山ほか__N__軒 | Yamatch</title>
<meta name="description" content="北アルプス・南アルプス・八ヶ岳・富士山・奥秩父・丹沢・尾瀬などの山小屋__N__軒について、__YEAR__年の予約開始日・予約方法（Web・電話）・定員・営業期間を一覧にまとめました。登る山から山小屋を探せます。">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<meta property="og:title" content="山小屋の予約開始日・予約方法まとめ【__YEAR__年】__N__軒 | Yamatch">
<meta property="og:description" content="山小屋__N__軒の予約開始日・予約方法・定員・営業期間の一覧。登る山から探せます。">
<meta property="og:type" content="website">
<meta property="og:url" content="https://tozan-navi.com/huts/">
<link rel="canonical" href="https://tozan-navi.com/huts/">
__HEADCOMMON__
__LD__
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Zen Kaku Gothic New',-apple-system,BlinkMacSystemFont,'Hiragino Sans',sans-serif;background:#f0ede5;color:#2f2b26;line-height:1.6}
header{background:#3a4f28;padding:12px 16px}
.header-inner{max-width:760px;margin:0 auto;display:flex;align-items:center;gap:8px}

.back-btn{background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);color:white;border-radius:8px;padding:4px 9px;font-size:11px;text-decoration:none;white-space:nowrap}
main{max-width:760px;margin:0 auto;padding:16px}
h1{font-size:22px;font-weight:800;color:#2a3820;margin-bottom:4px}
.beta{font-size:11px;background:#c8d4b8;color:#2a3820;border-radius:4px;padding:2px 7px;margin-left:6px;vertical-align:middle}
.sub{font-size:13px;color:#6a6258;margin-bottom:12px}
.about{background:#fff;border:1px solid #e0dbd4;border-radius:10px;padding:10px 14px;margin-bottom:14px;font-size:12.5px;color:#4a4540}
.about summary{cursor:pointer;font-weight:700;color:#4e6535}
.about li{margin:6px 0 0 18px}
.tabs{display:flex;background:#e2ddd2;border-radius:10px;padding:3px;margin-bottom:12px}
.tab{flex:1;border:none;background:none;padding:9px 6px;font-size:14px;font-weight:700;color:#6a6258;border-radius:8px;cursor:pointer}
.tab.on{background:#fff;color:#2a3820;box-shadow:0 1px 3px rgba(0,0,0,.12)}
#q{width:100%;padding:11px 12px;border:1px solid #d0cbc2;border-radius:10px;font-size:15px;margin-bottom:8px;background:#fff}
.chips{display:flex;gap:6px;margin-bottom:10px;overflow-x:auto;padding-bottom:4px}
.chip{flex-shrink:0;border:1px solid #c8c2b8;background:#fff;border-radius:999px;padding:6px 12px;font-size:12.5px;cursor:pointer;color:#3a3530}
.chip.on{background:#4e6535;color:#fff;border-color:#4e6535}
.mgrid{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.mb{text-decoration:none;border:1px solid #c8c2b8;background:#fff;border-radius:8px;padding:7px 10px;font-size:13.5px;cursor:pointer;color:#2f2b26;display:flex;align-items:center;gap:6px}
.mb span{font-size:11px;background:#e9efe0;color:#4e6535;border-radius:999px;padding:0 6px;font-weight:700}
.mb.on{background:#4e6535;color:#fff;border-color:#4e6535}.mb.on span{background:rgba(255,255,255,.25);color:#fff}
#picked{display:none;background:#e9efe0;border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:14px;font-weight:700;color:#2a3820;align-items:center;gap:10px;flex-wrap:wrap}
#picked a{font-size:12px;font-weight:400;color:#4e6535}
#picked button{margin-left:auto;border:none;background:#fff;border-radius:999px;padding:4px 12px;font-size:12px;cursor:pointer;color:#4e6535}
#cnt{font-size:12px;color:#7a7068;margin-bottom:8px}
.hut{background:#fff;border:1px solid #e0dbd4;border-radius:12px;padding:14px;margin-bottom:12px}
.hh{display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;margin-bottom:10px}
.hh h2{font-size:17px;font-weight:800;color:#2a3820}.hh h2 a{color:inherit;text-decoration:none}
.rg{font-size:11px;color:#6a6258;background:#f0ede5;border-radius:4px;padding:1px 7px}
.req{font-size:11px;font-weight:700;background:#fdf0d8;color:#8a5a10;border-radius:4px;padding:1px 7px}
.facts{display:grid;grid-template-columns:1.4fr 1fr .8fr;gap:8px;margin-bottom:10px}
.fact{background:#f7f5ef;border-radius:8px;padding:8px 10px;min-width:0}
.fl{font-size:10.5px;color:#7a7068;font-weight:700;letter-spacing:.03em;margin-bottom:2px}
.fv{font-size:14.5px;font-weight:700;color:#2f2b26;line-height:1.45;word-break:break-word}
.fs{font-size:11px;color:#7a7068;margin-top:3px;line-height:1.5}
.mt{display:inline-block;background:#fff;border:1px solid #d5cfc4;border-radius:5px;padding:0 7px;margin:0 4px 3px 0;font-size:13px;font-weight:700}
.na{color:#a09888;font-size:12.5px;font-weight:400}
.season,.mrow{display:flex;gap:10px;font-size:13.5px;padding:7px 0;border-top:1px solid #f0ede5;align-items:baseline;flex-wrap:wrap}
.sl{flex-shrink:0;width:5.2em;font-size:11px;color:#7a7068;font-weight:700}
.sv{flex:1;min-width:10em}
.ss{flex-basis:100%;padding-left:calc(5.2em + 10px);font-size:11px;color:#7a7068}
.mcs{flex:1;display:flex;flex-wrap:wrap;gap:5px}
.mc{display:inline-block;background:#e9efe0;color:#2a3820;border-radius:6px;padding:2px 9px;font-size:13px;font-weight:700;text-decoration:none}
.mc2{background:#f3f1ea;color:#5a544a;font-weight:400}.mc2 small{display:block;font-size:10.5px;color:#7a7068}
.foot{display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap;padding-top:8px;border-top:1px solid #f0ede5}
.btn{display:inline-block;background:#4e6535;color:#fff;border-radius:8px;padding:6px 14px;font-size:13px;font-weight:700;text-decoration:none}
.btn2{background:#fff;color:#4e6535;border:1px solid #4e6535}
.btn-al{background:#eef3e6;color:#2a3820;border:1px solid #4e6535}
#hut-alert{scroll-margin-top:72px}
.foot details{flex:1;min-width:12em;font-size:12px;color:#5a544a}
.foot summary{cursor:pointer;color:#7a7068;padding:6px 0;text-align:right}
.foot details div{padding:3px 0}.foot details b{display:inline-block;min-width:7.5em;color:#7a7068;font-weight:700;font-size:11px}
.src{font-size:11.5px;color:#7a7068;margin-top:14px;line-height:1.8}.src a{color:#4e6535}
.st{display:inline-flex;align-items:center;gap:5px;font-size:12px;margin-left:auto;padding:2px 9px 2px 7px;border-radius:999px;background:#f3f1ea;color:#5a544a}
.st i{width:9px;height:9px;border-radius:50%;background:#b5b0a8;flex-shrink:0}
.st b{font-weight:700}.st small{font-size:10.5px;color:#7a7068}
.st-on{background:#e6f3e4;color:#22602a}.st-on i{background:#2faa3f;box-shadow:0 0 0 3px rgba(47,170,63,.22)}
.st-soon{background:#fbf1cf;color:#7a5a00}.st-soon i{background:#e0a800;box-shadow:0 0 0 3px rgba(224,168,0,.22)}
.st-off{background:#eeece6;color:#6a6258}
.fts{list-style:none}.fts li{margin:0 0 4px;line-height:1.55}
.ftg{display:inline-block;border-radius:5px;padding:0 7px;margin-right:6px;font-size:11.5px;background:#eeece6;color:#4a4540}
.ftg-g{background:#fde9d2;color:#8a4a10}.ftg-b{background:#dceef5;color:#1f5a70}.ftg-v{background:#e6e4f5;color:#40398a}.ftg-e{background:#e9efe0;color:#2a3820}.ftg-h{background:#efe6da;color:#6a4a20}
.pk{display:inline-block;background:#e9efe0;color:#2a3820;border-radius:5px;padding:0 7px;margin-right:6px;font-size:12.5px}
.lg{display:inline-block;vertical-align:middle;margin-right:3px}.lg-h{width:11px;height:11px;border-radius:50%;background:#4e6535;border:2px solid #fff;box-shadow:0 0 0 1px #c8c2b8}.lg-m{color:#b4532a;font-size:13px}
.mtlb{background:none;border:none;white-space:nowrap;font-size:12px;font-weight:700;color:#8a3d1c;text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff;text-align:center;line-height:1.1}
.mtlb span{display:block;font-size:15px;line-height:1}
.rgh{font-size:16px;font-weight:800;color:#2a3820;margin:20px 0 10px;padding:6px 10px;background:#dfe6d3;border-radius:8px;display:flex;align-items:center}
.rgh small{margin-left:auto;font-size:12px;font-weight:400;color:#4e6535}
.hmap{height:340px;border-radius:12px;border:1px solid #e0dbd4;background:#e8e4dc;margin-bottom:8px;z-index:0}
.mapnote{font-size:11.5px;color:#7a7068;margin-bottom:12px}
.maplink{display:inline-block;font-size:12.5px;color:#4e6535;margin-bottom:14px}
.bc{font-size:11.5px;color:#7a7068;margin-bottom:10px}.bc a{color:#4e6535;text-decoration:none}
.lead{font-size:13.5px;color:#3a3530;margin-bottom:12px}
.upd{font-size:11.5px;color:#7a7068;margin-bottom:12px}
.cmp{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e0dbd4;border-radius:10px;font-size:12.5px;margin-bottom:14px}
.cmp th,.cmp td{padding:7px 9px;border-bottom:1px solid #f0ede5;text-align:left;vertical-align:top}
.cmp th{font-size:11px;color:#7a7068;background:#f7f5ef}.cmp td:first-child{min-width:7em}.cmp td:last-child{min-width:4.5em}.cmp a{color:#2a3820;font-weight:700}
.sec{font-size:17px;font-weight:800;color:#2a3820;margin:22px 0 10px}
.faq{background:#fff;border:1px solid #e0dbd4;border-radius:10px;padding:12px 14px;margin-bottom:8px}
.faq dt{font-size:14px;font-weight:700;color:#2a3820;margin-bottom:4px}.faq dd{font-size:13px;color:#3a3530}
.rel{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
footer{text-align:center;padding:20px 16px;font-size:12px;color:#a09888;border-top:1px solid #e8e4dc;margin-top:8px}footer a{color:#6a8055}
/* ── ガイドブック風の組版：明朝の見出し、細い罫線、数字は Outfit ── */
h1,.hh h2,.sec,.rgh{font-family:'Noto Serif JP','Hiragino Mincho ProN',serif;letter-spacing:.02em}
.hut{border-radius:4px;border:1px solid #d9d3c8;border-top:3px solid #4e6535;padding:16px 16px 12px}
.hh{border-bottom:1px solid #e6e1d8;padding-bottom:10px;margin-bottom:12px}
.hh h2{font-size:19px}
.el{font-family:'Outfit',sans-serif;font-weight:700;font-size:15px;color:#4e6535;letter-spacing:.01em}.el small{font-size:11px;font-weight:500;margin-left:1px}
.rg,.req{border-radius:2px}
.facts{gap:0;border:1px solid #e6e1d8;border-radius:2px}
.fact{background:none;border-radius:0;border-left:1px solid #e6e1d8;padding:9px 11px}.fact:first-child{border-left:none}
.fl,.sl{font-family:'Outfit','Zen Kaku Gothic New',sans-serif;letter-spacing:.08em;color:#8a8072}
.fv{font-size:15px}
.sec{border-bottom:1px solid #2a3820;padding-bottom:6px;font-size:18px}
#ym-packing{background:#fff;border:1px solid #e0dbd4;border-radius:10px;padding:12px 14px}
.pk-ctl{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:6px;font-size:13px;font-weight:700}
.pk-ctl select{font-size:14px;padding:5px 8px;border:1px solid #cfc6b4;border-radius:8px;background:#fff}
.pk-stay{display:flex;gap:4px}.pk-stay button{border:1px solid #4e6535;background:#fff;color:#4e6535;border-radius:999px;padding:5px 12px;font-size:13px;font-weight:700}
.pk-stay button.on{background:#4e6535;color:#fff}
.pk-g h3{font-size:15px;margin:14px 0 4px;color:#2a3820;border-left:3px solid #4e6535;padding-left:7px}
.pk-lead{font-size:12.5px;color:#5a5048;margin:2px 0 4px}
.pk-g ul{list-style:none;margin:0;padding:0}.pk-g li{border-bottom:1px dashed #e6e0d6;padding:7px 0}
.pk-g label{display:flex;gap:8px;align-items:flex-start;font-size:14px;cursor:pointer}
.pk-g input{width:18px;height:18px;margin-top:1px;accent-color:#4e6535;flex:none}
.pk-g small{display:block;font-size:11.5px;color:#8a8070;margin-top:1px}
.pk-g li.on>label>span{color:#a09888;text-decoration:line-through}
.pk-buy{display:block;margin:3px 0 0 26px;font-size:11.5px;color:#4e6535}
.pk-foot{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px}
.pk-foot button{border:0;background:#4e6535;color:#fff;border-radius:8px;padding:8px 12px;font-size:13px;font-weight:700}
.pk-foot .pk-sub{background:#eeeae2;color:#5a5048}.pk-n{font-size:13px;font-weight:700;color:#4e6535;flex:1}
.pk-msg{font-size:12px;color:#4e6535;margin:4px 0 0}.pk-warn{font-size:12.5px;color:#a33;font-weight:700}
.pk-src{font-size:11px;color:#8a8070;margin:10px 0 0;line-height:1.6}.pk-src a{color:#8a8070}
.pk-exp{background:#f6f3ec;border-left:3px solid #c8a060;border-radius:6px;padding:8px 10px;margin:10px 0 4px;font-size:13px}.pk-exp b{display:block;color:#6a4a20}.pk-exp-when{font-size:11.5px;color:#8a8070}.pk-exp p{margin:4px 0 0;line-height:1.6}
.rgh{background:none;border-radius:0;border-bottom:2px solid #2a3820;padding:6px 2px}
.cmp{border-radius:2px}.cmp th{font-family:'Outfit','Zen Kaku Gothic New',sans-serif;letter-spacing:.08em}
.mb,.chip,.btn,.tab,.tabs{border-radius:3px}
.hfav{margin-left:2px;border:none;background:none;padding:4px;cursor:pointer;line-height:0}
.hfav svg{fill:none;stroke:#c0b8a8}.hfav[aria-pressed="true"] svg{fill:#f0c030;stroke:#d4a020}
.st+.hfav{margin-left:2px}
/* 12か月の帯 */
.mbar{display:grid;grid-template-columns:repeat(12,1fr);gap:2px;margin-top:6px;max-width:420px}
.mbar i{display:block;height:9px;background-color:#eceae3;position:relative;margin-bottom:13px}
.mbar b{position:absolute;left:0;right:0;top:11px;text-align:center;font:500 9.5px/1 'Outfit',sans-serif;color:#a09888;font-style:normal}
.mbar i.now b{color:#2a3820;font-weight:700}.mbar i.now{outline:1.5px solid #2a3820;outline-offset:1px}
/* 地形図ヘッダー */
.topo{position:relative;height:190px;overflow:hidden;margin:-16px -16px 16px;background:#e8e4dc}
.topo-map{position:absolute;left:50%;top:50%;width:1280px;height:768px;display:grid;grid-template-columns:repeat(5,256px);filter:saturate(.75) contrast(1.02)}
.topo-map img{display:block;width:256px;height:256px}
.topo:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(34,44,24,0) 12%,rgba(34,44,24,.55) 48%,rgba(34,44,24,.9) 100%);pointer-events:none}
.topo-pin{position:absolute;left:50%;top:38%;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;background:#b4532a;border:2.5px solid #fff;box-shadow:0 0 0 1.5px rgba(0,0,0,.35);z-index:1}
.topo-cap{position:absolute;left:16px;right:16px;bottom:12px;z-index:2;color:#fff}
.topo-cap h1{color:#fff;font-size:23px;line-height:1.3;margin:0;text-shadow:0 1px 6px rgba(0,0,0,.45)}
.topo-k{font:700 11px/1.4 'Outfit','Zen Kaku Gothic New',sans-serif;letter-spacing:.14em;margin-bottom:4px;text-shadow:0 1px 4px rgba(0,0,0,.6)}
.topo-s{font:700 15px/1.3 'Outfit','Zen Kaku Gothic New',sans-serif;margin-top:4px;letter-spacing:.02em}
.topo-src{position:absolute;right:4px;top:4px;z-index:2;font-size:9.5px;color:#4a4540;background:rgba(255,255,255,.72);padding:1px 5px;border-radius:2px;text-decoration:none}
.topo+.bc{margin-top:-6px}
/* 予約開始のお知らせ：案内バナーと説明のポップアップ */
.promo{display:flex;align-items:center;gap:12px;width:100%;text-align:left;background:#c8d4b8;border:1px solid #a9b996;border-left:5px solid #4e6535;border-radius:4px;padding:12px 14px;margin-bottom:14px;cursor:pointer;font-family:inherit;color:#2a3820}
.promo-i{flex-shrink:0;width:38px;height:38px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center}
.promo-i svg{width:22px;height:22px;fill:#f0c030;stroke:#8a5a10;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;transform-origin:50% 2px;animation:promoBell 4s ease-in-out infinite}
@keyframes promoBell{0%,15%,100%{transform:rotate(0)}2%{transform:rotate(-16deg)}4%{transform:rotate(14deg)}6%{transform:rotate(-12deg)}8%{transform:rotate(10deg)}10%{transform:rotate(-7deg)}12%{transform:rotate(4deg)}}
@media (prefers-reduced-motion:reduce){.promo-i svg{animation:none}}
.promo-t{flex:1;min-width:0}.promo-t b{display:block;font-family:'Noto Serif JP',serif;font-size:16px;line-height:1.35}.promo-t small{display:block;font-size:12px;line-height:1.5;color:#3d4a30;margin-top:2px}
.promo-a{flex-shrink:0;font-size:12px;font-weight:700;background:#4e6535;color:#fff;border-radius:3px;padding:6px 10px}
.hamodal{position:fixed;inset:0;z-index:9000;background:rgba(26,22,14,.55);align-items:flex-end;justify-content:center;padding:0}
.hamodal-in{position:relative;width:100%;max-width:560px;max-height:92vh;overflow-y:auto;background:#fff;border-radius:14px 14px 0 0;padding:22px 20px 26px;-webkit-overflow-scrolling:touch}
.hamodal-x{position:absolute;right:8px;top:6px;width:40px;height:40px;border:none;background:none;font-size:26px;line-height:1;color:#6a6258;cursor:pointer}
.hamodal-k{font:700 11px/1 'Outfit',sans-serif;letter-spacing:.16em;color:#4e6535;margin-bottom:6px}
.hamodal h2{font-family:'Noto Serif JP',serif;font-size:20px;color:#2a3820;margin:0 36px 8px 0;line-height:1.4}
.hamodal-lead{font-size:13.5px;color:#3a3530;margin-bottom:14px}
.hamodal-steps{list-style:none;counter-reset:hs;margin:0 0 14px;border-top:1px solid #e6e1d8}
.hamodal-steps li{counter-increment:hs;position:relative;padding:11px 0 11px 40px;border-bottom:1px solid #e6e1d8;font-size:13px;color:#4a4540;line-height:1.6}
.hamodal-steps li:before{content:counter(hs);position:absolute;left:2px;top:11px;width:26px;height:26px;border-radius:50%;background:#4e6535;color:#fff;font:700 14px/26px 'Outfit',sans-serif;text-align:center}
.hamodal-steps b{display:block;font-size:14px;color:#2a3820}
.hamodal-n{display:flex;align-items:baseline;gap:6px;margin-bottom:4px}.hamodal-n b{font:700 34px/1 'Outfit',sans-serif;color:#4e6535}.hamodal-n span{font-size:13px;color:#4a4540}
.hamodal-s{font-size:11.5px;color:#7a7068;line-height:1.6;margin:0 0 12px}
.hamodal-d{font-size:12.5px;color:#22602a;min-height:1.2em;margin:8px 0 4px}
.hamodal-f{border-top:1px solid #e6e1d8;padding-top:12px;margin-top:4px}.hamodal-f p{font-size:12.5px;color:#4a4540;margin-bottom:10px}.hamodal-f p b{display:block;color:#2a3820}
.hamodal-c{display:block;width:100%;margin-top:10px;border:none;background:none;color:#7a7068;font-size:13px;padding:10px;cursor:pointer}
@media(min-width:600px){.hamodal{align-items:center;padding:20px}.hamodal-in{border-radius:10px}}
/* 予約開始のお知らせ */
.ha{background:#fff;border:1px solid #d9d3c8;border-left:4px solid #4e6535;border-radius:4px;padding:14px 16px;margin-bottom:16px}
.ha-t{font-family:'Noto Serif JP',serif;font-weight:700;font-size:16px;color:#2a3820;margin-bottom:6px}
.ha-k{font-size:13px;font-weight:700;color:#2f2b26;margin-bottom:8px}.ha-k span{font-weight:400;font-size:12px;color:#7a7068}
.ha-p{font-size:13px;color:#4a4540;margin-bottom:10px}
.ha-l{display:block;font-size:11.5px;color:#7a7068;font-weight:700;margin-bottom:4px}
.ha-in{width:100%;max-width:240px;padding:9px 10px;border:1px solid #c8c2b8;border-radius:3px;font-size:16px;background:#fff}
.ha-out{font-size:13.5px;margin:8px 0;min-height:1.4em}.ha-out span{font-size:12px;color:#7a7068}
.ha-btn{display:inline-block;background:#4e6535;color:#fff;border:none;border-radius:3px;padding:10px 16px;font-size:14px;font-weight:700;cursor:pointer;text-decoration:none}
.ha-btn:disabled{background:#b5b0a8;cursor:default}.ha-btn2{background:#fff;color:#4e6535;border:1px solid #4e6535}
.ha-demo{margin-top:14px;border-top:1px solid #e6e1d8;padding-top:12px}
.ha-msg{font-size:12.5px;color:#22602a;margin-top:8px}
.ha-list{margin-top:12px;border-top:1px solid #e6e1d8;padding-top:8px;font-size:12.5px;color:#4a4540}.ha-lt{font-size:11px;font-weight:700;color:#7a7068}.ha-my{color:#4e6535;font-size:12px}
@media(max-width:560px){.facts{grid-template-columns:1fr 1fr}.facts .fact:first-child{grid-column:1/-1;border-bottom:1px solid #e6e1d8}.facts .fact:nth-child(2){border-left:none}.topo{height:170px}}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <a href="/" style="display:flex;align-items:center;gap:6px;text-decoration:none;flex:1;min-width:0;"><svg width="24" height="24" viewBox="0 0 36 36" style="flex-shrink:0"><polygon points="18,4 34,30 2,30" fill="#405830"/><polygon points="18,10 30,30 6,30" fill="#789858"/><polygon points="10,30 17,17 24,30" fill="#2c4020"/></svg><div class="header-title" style="color:white;font-size:20px;font-weight:700;font-family:Georgia,serif;line-height:1;">Yamatch</div></a>
    <span style="flex:1"></span>
    <a href="/" class="back-btn">← トップへ</a>
  </div>
</header>
<main>
__HERO__
<nav class="bc" aria-label="パンくず"><a href="/">Yamatch</a> › 山小屋まとめ</nav>
<p class="lead">北アルプス・南アルプス・中央アルプス・八ヶ岳・富士山・奥秩父・丹沢・尾瀬などの山小屋について、「いつから予約できるか」「どうやって予約するか」を山小屋ごとにまとめています。登る山を選ぶと、その山で使える山小屋だけを表示します。</p>
<p class="upd">最終確認：<time datetime="__VERIFIED__">__VERIFIED_JA__</time></p>
__PROMO__
<details class="about"><summary>このページの見方・出典</summary>
<ul>
<li>「対応する山」は、当サイトで紹介しているルートの登山口・途中・山頂にある小屋です。別のルートや縦走で使う小屋は、灰色で関係を添えています。</li>
<li>「予約の開始」「予約方法」は、各山小屋の公式サイト・予約サイト・出典の一覧に書かれているものだけを載せています。見つからなかった小屋は「公式サイトで確認」としています。</li>
<li>「規模」は、公式サイト・予約サイトで確認できた定員です。確認できなかった小屋は、山と溪谷オンラインの山小屋情報の収容人数を「約◯人」として載せています（今は定員を減らしている小屋があります）。</li>
<li>富士山・白山・上信越・尾瀬・東北の山小屋の営業期間は「例年」の値です。</li>
<li>営業期間や予約の受付は変わることがあります。予約の前に、必ず各山小屋の公式サイトで確認してください。</li>
</ul>
</details>
<div class="tabs"><button class="tab on" data-v="mt">山から探す</button><button class="tab" data-v="map">地図から探す</button><button class="tab" data-v="all">山小屋の一覧</button></div>
<div id="v-mt">
<input id="mq" type="search" placeholder="山名でさがす（例：槍ヶ岳）" style="width:100%;padding:11px 12px;border:1px solid #d0cbc2;border-radius:10px;font-size:15px;margin-bottom:8px;background:#fff">
<div class="mgrid" id="mgrid">__MTS__</div>
</div>
<div id="v-map" style="display:none">
__MAP__
</div>
<div id="v-all" style="display:none">
<input id="q" type="search" placeholder="山小屋名・山名でさがす（例：涸沢）">
<div class="chips">__CHIPS__</div>
</div>
<div id="cnt"></div>
<div id="list">
__CARDS__
</div>
<p class="src">出典：<a href="https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/sotaikyo/yamagoya/yamagoya.html" target="_blank" rel="noopener">長野県 山小屋情報ポータルサイト</a>（__UPD__更新分）／山と溪谷オンライン <a href="https://www.yamakei-online.com/yama-ya/detail.php?id=2535" target="_blank" rel="noopener">北アルプス山小屋リスト2026</a>・<a href="https://www.yamakei-online.com/yama-ya/detail.php?id=2556" target="_blank" rel="noopener">中央・南アルプス山小屋リスト2026</a>・山小屋情報の各ページ／予約サイト「やまたん」／各山小屋の公式サイト</p>
<h2 class="sec">山小屋の予約でよくある質問</h2>
<dl>
__FAQ__
</dl>
</main>
__FOOTER__
<script src="/assets/js/huts-status.js?v=__MAPVER__"></script>
<script src="/assets/js/huts-alert.js?v=__MAPVER__" defer></script>
<script>
(function(){
  var view='mt', region='', huts=document.querySelectorAll('.hut');
  var q=document.getElementById('q'), mq=document.getElementById('mq'), cnt=document.getElementById('cnt');
  var list=document.getElementById('list');
  var mbs=document.querySelectorAll('.mb'), i;
  // 以前の形式 /huts/?m=山ID は、山ごとのページへ送る
  var m0=(location.search.match(/[?&]m=([a-z0-9_]+)/)||[])[1];
  if(m0){ for(i=0;i<mbs.length;i++){ if(mbs[i].getAttribute('data-m')===m0){ location.replace('/huts/'+m0+'/'); return; } } }
  var rghs=document.querySelectorAll('.rgh');
  function apply(){
    var k=q.value.replace(/\\s+/g,''), n=0, h, ok, per={}, rg;
    for(i=0;i<huts.length;i++){
      h=huts[i]; rg=h.getAttribute('data-region');
      ok=(!region||rg===region)&&(!k||h.getAttribute('data-key').indexOf(k)>-1);
      h.style.display=ok?'':'none'; if(ok){ n++; per[rg]=(per[rg]||0)+1; }
    }
    // 地域の見出しは、その地域に表示する小屋があるときだけ出す
    for(i=0;i<rghs.length;i++){ rg=rghs[i].getAttribute('data-region'); rghs[i].style.display=per[rg]?'':'none'; rghs[i].querySelector('small').textContent=(per[rg]||0)+'軒'; }
    list.style.display=view==='all'?'':'none';
    cnt.textContent=view==='mt'?'山を選ぶと、その山の山小屋のページを開きます':(view==='map'?'ピンをタップすると、山小屋の名前と予約の開始が出ます':n+'軒を表示');
  }
  mq.addEventListener('input',function(){ var k=mq.value.replace(/\\s+/g,''); for(var j=0;j<mbs.length;j++){ mbs[j].style.display=(!k||mbs[j].getAttribute('data-name').indexOf(k)>-1)?'':'none'; } });
  q.addEventListener('input',apply);
  var chips=document.querySelectorAll('.chip');
  for(i=0;i<chips.length;i++){ chips[i].addEventListener('click',function(){ for(var j=0;j<chips.length;j++)chips[j].className='chip'; this.className='chip on'; region=this.getAttribute('data-r'); apply(); }); }
  var tabs=document.querySelectorAll('.tab');
  for(i=0;i<tabs.length;i++){ tabs[i].addEventListener('click',function(){ for(var j=0;j<tabs.length;j++)tabs[j].className='tab'; this.className='tab on'; view=this.getAttribute('data-v'); document.getElementById('v-mt').style.display=view==='mt'?'':'none'; document.getElementById('v-all').style.display=view==='all'?'':'none'; document.getElementById('v-map').style.display=view==='map'?'':'none'; apply(); if(view==='map'&&window.YMHutsMap){ window.YMHutsMap.show(); } }); }
  // /huts/#hut-xxxx で開いたときは、一覧に切り替えてその小屋を見せる
  if(location.hash==='#map'){ tabs[1].click(); }
  else if(location.hash && document.getElementById(location.hash.slice(1))){ tabs[2].click(); document.getElementById(location.hash.slice(1)).scrollIntoView(); }
  else { apply(); }
})();
</script>
</body>
</html>
'''
# ---------- SEO：共通の部品 ----------
BASE = 'https://tozan-navi.com'
YEAR = d['seasonYear']
VERIFIED = max(h['lastVerified'] for h in H if h.get('lastVerified'))
VERIFIED_JA = '%d年%d月%d日' % tuple(int(x) for x in VERIFIED.split('-'))
HEADCOMMON = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@600;700&family=Outfit:wght@500;700&family=Zen+Kaku+Gothic+New:wght@400;700&display=swap">
<meta property="og:site_name" content="Yamatch">
<meta property="og:locale" content="ja_JP">
<meta property="og:image" content="https://tozan-navi.com/ogp.png">
<meta name="twitter:card" content="summary_large_image">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-TMTVVTEEGF"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-TMTVVTEEGF');
</script>
<link rel="apple-touch-icon" sizes="180x180" href="/icon-180.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon.ico">
<link rel="manifest" href="/manifest.json">"""
FOOTER = """<footer>
<p>Yamatch — 出発地から登る山を探せる登山サーチ</p>
<p style="margin-top:6px"><a href="/">山を検索する</a> <span style="margin:0 8px;opacity:0.4">|</span> <a href="/huts/">山小屋まとめ</a> <span style="margin:0 8px;opacity:0.4">|</span> <a href="/terms/">利用規約</a> <span style="margin:0 8px;opacity:0.4">|</span> <a href="/privacy/">プライバシーポリシー</a> <span style="margin:0 8px;opacity:0.4">|</span> <a href="/about/">運営者</a></p>
<p style="margin-top:8px;opacity:0.6;">© 2026 Yamatch. All rights reserved.</p>
</footer>"""
CSS = re.search(r'<style>(.*?)</style>', page, flags=re.S).group(1)
by_id = {h['id']: h for h in H}


def ld(*objs):
    return '\n'.join('<script type="application/ld+json">%s</script>' % json.dumps(o, ensure_ascii=False) for o in objs)


def crumbs(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': BASE + u} for i, (n, u) in enumerate(items)]}


def lodging(h):
    o = {'@type': 'LodgingBusiness', 'name': h['name'], 'url': BASE + '/huts/%s/' % h['id']}
    if h.get('tel'):
        o['telephone'] = h['tel']
    if h.get('officialUrl'):
        o['sameAs'] = h['officialUrl'].strip()
    c = COORDS.get(h['name'])
    if c:
        o['geo'] = {'@type': 'GeoCoordinates', 'latitude': c['lat'], 'longitude': c['lng']}
    return o


def faq_ld(qa):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in qa]}


def faq_html(qa):
    return '\n'.join('<div class="faq"><dt>%s</dt><dd>%s</dd></div>' % (E(q), E(a)) for q, a in qa)


def methods_text(ms):
    return '・'.join(split_note(x)[0] for x in ms) if ms else None


def huts_of(mid):
    """その山の小屋：ルート上の小屋 → 別ルート・縦走の小屋 の順"""
    a = [h for h in H if mid in h['mountainIds']]
    b = [h for h in H if any(o['id'] == mid for o in h.get('otherMountains') or [])]
    return a, b


def write(path, text):
    assert text.rstrip().endswith('</html>') and text.count('<div') == text.count('</div>'), path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)


SHELL = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="%(robots)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:type" content="article">
<meta property="og:url" content="%(url)s">
<link rel="canonical" href="%(url)s">
%(head)s
%(ld)s
<style>%(css)s</style>
</head>
<body>
<header>
  <div class="header-inner">
    <a href="/" style="display:flex;align-items:center;gap:6px;text-decoration:none;flex:1;min-width:0;"><svg width="24" height="24" viewBox="0 0 36 36" style="flex-shrink:0"><polygon points="18,4 34,30 2,30" fill="#405830"/><polygon points="18,10 30,30 6,30" fill="#789858"/><polygon points="10,30 17,17 24,30" fill="#2c4020"/></svg><div class="header-title" style="color:white;font-size:20px;font-weight:700;font-family:Georgia,serif;line-height:1;">Yamatch</div></a>
    <span style="flex:1"></span>
    <a href="/huts/" class="back-btn">山小屋まとめ</a>
    <a href="/" class="back-btn">← トップへ</a>
  </div>
</header>
<main>
%(body)s
</main>
%(footer)s
<script src="/assets/js/huts-status.js?v=%(ver)s"></script>
<script src="/assets/js/huts-alert.js?v=%(ver)s" defer></script>
</body>
</html>
"""

# ---------- 一覧ページ ----------
# 予約開始のお知らせの案内バナーと、説明のポップアップ
_rc = {}
for _x in info.values():
    if _x.get('rule'):
        _rc[_x['rule']['t']] = _rc.get(_x['rule']['t'], 0) + 1
_rn = sum(_rc.values())
BELL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>'
PROMO = ('''<button type="button" class="promo" data-ha-open aria-haspopup="dialog">
<span class="promo-i">%(bell)s</span>
<span class="promo-t"><b>予約開始をお知らせ</b><small>泊まりたい日を登録すると、予約が始まる1週間前・前日・当日に知らせます（%(n)d軒が対応）</small></span>
<span class="promo-a" aria-hidden="true">くわしく</span>
</button>
<div id="ha-modal" class="hamodal" role="dialog" aria-modal="true" aria-labelledby="ha-modal-t" data-demo-name="槍ヶ岳山荘" data-demo-id="%(demo_id)s" style="display:none">
<div class="hamodal-in">
<button type="button" class="hamodal-x" data-ha-close aria-label="閉じる">×</button>
<div class="hamodal-k">NEW</div>
<h2 id="ha-modal-t">山小屋の予約開始をお知らせ</h2>
<p class="hamodal-lead">人気の山小屋は、予約開始の日にすぐ埋まります。泊まりたい日を登録しておくと、予約が始まる日が近づいたときに Yamatch が知らせます。</p>
<ol class="hamodal-steps">
<li><b>山小屋のページで登録</b>泊まりたい日を選ぶと、その日の予約がいつ始まるかを計算します。まとめて受付が始まる山小屋は、ボタンを押すだけです。</li>
<li><b>1週間前・前日・当日に知らせる</b>Yamatch を開いたときに、画面の上と下のバーの鈴マークで知らせます。通知を許可すると、端末の通知も出ます。</li>
<li><b>マイページで確認</b>登録した山小屋と予約開始日、あと何日かを一覧で見られます。</li>
</ol>
<div class="hamodal-n"><b>%(n)d</b><span>軒が対応（掲載%(all)d軒中）</span></div>
<p class="hamodal-s">内訳：宿泊日の何日前・何か月前に始まる山小屋 %(rel)d軒／シーズン分をまとめて受け付ける山小屋 %(fix)d軒／宿泊する時期ごとに開始日が違う山小屋 %(phase)d軒。予約開始日の決まり方が分からない山小屋は対応していません。</p>
<button type="button" id="ha-modal-demo" class="ha-btn">お知らせの見本を見る</button>
<p id="ha-modal-demo-s" class="hamodal-d"></p>
<button type="button" id="ha-modal-trial" class="ha-btn ha-btn2" style="margin-top:4px">実際の画面でお試しする</button>
<p id="ha-modal-trial-s" class="hamodal-d" style="color:#3a3530"></p>
<p class="hamodal-s">ホームとマイページでどう見えるかを、小さな画面の見本で、1週間前・前日・当日の順に見せます（槍ヶ岳山荘の例）。</p>
<div class="hamodal-f">
<p><b>使うには</b>Yamatch をホーム画面に追加し、ホーム画面のアイコンから開いてください。登録はお使いの端末の中に保存され、Yamatch を開いたときにお知らせします（開いていないときには届きません）。</p>
<a class="ha-btn ha-btn2" href="/">ホーム画面に追加する方法を見る</a>
<button type="button" class="hamodal-c" data-ha-close>閉じる</button>
</div>
</div>
</div>''' % {'bell': BELL, 'n': _rn, 'all': len(H), 'rel': _rc.get('rel', 0) + _rc.get('mon', 0), 'fix': _rc.get('fix', 0), 'phase': _rc.get('phase', 0),
       'demo_id': next((h['id'] for h in H if h['name'] == '槍ヶ岳山荘'), '')})

# 「山小屋の一覧」は地域ごとに見出しで区切る
_g = []
for rg in regions:
    rc = [card_of[h['id']] for h in H if h['region'] == rg]
    _g.append('<div class="rgh" role="heading" aria-level="2" data-region="%s" id="rg-%d">%s<small>%d軒</small></div>' % (E(rg), regions.index(rg), E(RLABEL.get(rg, rg)), len(rc)))
    _g.extend(rc)
grouped = '\n'.join(_g)
n_start = sum(1 for x in info.values() if x['start'])
# 地図の吹き出しに出す短い文（予約の開始の本文だけ）
START_SHORT = {k: ('予約不要' if x['none'] else (split_note(x['start'])[0] if x['start'] else '')) for k, x in info.items()}
n_none = [by_id[k]['name'] for k, x in info.items() if x['none']]
n_web = sum(1 for x in info.values() if x['methods'] and any(re.search(r'Web|LINE|ネット', m) for m in x['methods']))
n_tel_only = sum(1 for x in info.values() if x['methods'] and all('電話' in m for m in x['methods']))
n_req = sum(1 for h in H if h['bookingRequired'])
n_year = sum(1 for h in H if '通年' in (info[h['id']]['season'] or ''))


def example(name):
    h = next((x for x in H if x['name'] == name), None)
    v = info[h['id']]['start'] if h else None
    return '%sは「%s」' % (name, v) if v else None


ex_rel = [e for e in (example('槍ヶ岳山荘'), example('雲取山荘')) if e]
ex_fix = [e for e in (example('燕山荘'), example('白山室堂')) if e]
MAIN_FAQ = [
    ('山小屋の予約はいつから始まりますか？',
     '山小屋によって違い、大きく2つの決め方があります。1つは「宿泊日の◯か月前・◯日前から」という決め方' + ('（例：' + '、'.join(ex_rel) + '）' if ex_rel else '')
     + '、もう1つは「毎年決まった日にシーズン分をまとめて受け付ける」決め方です' + ('（例：' + '、'.join(ex_fix) + '）' if ex_fix else '')
     + '。このページでは%d軒のうち、予約の開始が確認できた%d軒の日付・ルールを載せています。' % (len(H), n_start)),
    ('予約なしで泊まれる山小屋はありますか？',
     '掲載している%d軒のうち、予約の受付がない小屋（避難小屋など）は%d軒です（%s）。一方、出典に「予約必須」「完全予約制」と書かれている小屋は%d軒あります。それ以外の小屋も、定員や食事の準備があるため事前の予約が基本です。'
     % (len(H), len(n_none), '、'.join(n_none), n_req)),
    ('Web（インターネット）で予約できる山小屋はどれくらいありますか？',
     '予約方法が確認できた小屋のうち、Web・予約サイト・LINEなどオンラインで予約できる小屋は%d軒、電話だけで受け付けている小屋は%d軒です。各小屋のカードの「予約方法」で確認できます。' % (n_web, n_tel_only)),
    ('山小屋の営業期間はどこで確認できますか？',
     '各小屋のカードに%d年の営業期間を載せています。通年営業の小屋は%d軒です。営業期間は残雪や天候で変わることがあるので、出発前に各山小屋の公式サイトで確認してください。' % (YEAR, n_year)),
]
main_ld = ld(
    crumbs([('Yamatch', '/'), ('山小屋まとめ', '/huts/')]),
    {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': '山小屋の予約開始日・予約方法まとめ（%d年）' % YEAR, 'url': BASE + '/huts/',
     'dateModified': VERIFIED, 'inLanguage': 'ja',
     'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(H), 'itemListElement': [
         {'@type': 'ListItem', 'position': i + 1, 'url': BASE + '/huts/%s/' % h['id'], 'name': h['name']} for i, h in enumerate(H)]}},
    faq_ld(MAIN_FAQ))
page = (page.replace('__N__', str(len(H))).replace('__YEAR__', str(YEAR)).replace('__UPD__', upd)
        .replace('__HERO__', topo_hero(36.25, 137.75, 'MOUNTAIN HUTS %d' % YEAR, '山小屋の予約開始日・予約方法まとめ<span class="beta">β版</span>', '%d軒｜予約の開始・予約方法・規模・営業期間' % len(H), zoom=10, pin=False)).replace('__PROMO__', PROMO).replace('__MAPVER__', MAP_VER).replace('__HEADCOMMON__', HEADCOMMON).replace('__LD__', main_ld).replace('__FAQ__', faq_html(MAIN_FAQ)).replace('__FOOTER__', FOOTER)
        .replace('__VERIFIED_JA__', VERIFIED_JA).replace('__VERIFIED__', VERIFIED)
        .replace('__MAP__', map_block(H, START_SHORT, 'manual')).replace('__CHIPS__', chips).replace('__MTS__', ''.join(mt_btns)).replace('__CARDS__', grouped))
write(os.path.join(ROOT, 'huts', 'index.html'), page)
print('huts/index.html', len(H), '軒／山', len(mt_btns))

def packing_block(m):
    """持ち物・服装のチェックリスト（assets/js/packing.js が data/packing.json から描く）"""
    return ('<h2 class="sec" id="packing">%sの山小屋泊の持ち物・服装</h2>\n'
            '<p class="lead">行く月と泊まり方を選ぶと、持ち物と服装のチェックリストになります。雪の残る時期・冬山の装備は、%sの装備カレンダーから選んでいます。</p>\n'
            '<div id="ym-packing" data-mid="%s" data-name="%s" data-elev="%s" data-gear="%s">持ち物リストを読み込み中…</div>\n'
            '<script src="/assets/js/gear-common.js?v=%s" defer></script>\n<script src="/assets/js/packing.js?v=%s" defer></script>\n') % (
        E(m['name']), E(m['name']), E(m['id']), E(m['name']), m.get('elevation') or 0,
        E(json.dumps(m.get('gearCalendar') or [], ensure_ascii=False, separators=(',', ':'))), MAP_VER, MAP_VER)


# ---------- 山ごとのページ /huts/<山ID>/ ----------
made = set()
for m in ML:
    mid = m['id']
    if mid not in count:
        continue
    a, b = huts_of(mid)
    hs = a + b
    names = '・'.join(h['name'] for h in hs[:3]) + ('など' if len(hs) > 3 else '')
    title = '%sの山小屋%d軒｜予約開始日・予約方法・営業期間【%d年】| Yamatch' % (m['name'], len(hs), YEAR)
    desc = '%s（標高%sm）の登山で使える山小屋%d軒（%s）の、%d年の予約開始日・予約方法・定員・営業期間を一覧で比較できます。各山小屋の公式サイトへのリンク付き。' % (
        m['name'], '{:,}'.format(m['elevation']), len(hs), names, YEAR)
    rows = []
    for h in hs:
        x = info[h['id']]
        st = '予約不要' if x['none'] else (E(x['start']) if x['start'] else '公式サイトで確認')
        rows.append('<tr><td><a href="#%s">%s</a></td><td>%s</td><td>%s</td></tr>' % (
            E(h['id']), E(h['name']), st, '予約なし' if x['none'] else E(methods_text(x['methods']) or '公式サイトで確認')))
    lead = '%s（%s・標高%sm）で使える山小屋は%d軒です。' % (E(m['name']), E(m.get('area') or ''), '{:,}'.format(m['elevation']), len(hs))
    if a and b:
        lead += '当サイトで紹介しているルートの登山口・途中・山頂にある小屋が%d軒、別のルートや縦走で使う小屋が%d軒あります。' % (len(a), len(b))
    # 関連：同じ小屋を使う山
    rel = []
    for h in hs:
        for i in h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]:
            if i != mid and i not in rel:
                rel.append(i)
    rel_html = ''.join('<a class="mb" href="/huts/%s/">%sの山小屋<span>%d</span></a>' % (E(i), E(M[i]['name']), count[i]) for i in rel[:12])
    body = (
        (topo_hero(SUMMITS[mid]['lat'], SUMMITS[mid]['lng'], E((m.get('area') or '') + '｜MOUNTAIN HUTS'), '%sの山小屋（%d軒）｜予約開始日・予約方法' % (E(m['name']), len(hs)),
                   '%s %sm' % (E(m['name']), format(m['elevation'], ',')), zoom=14, pin=False) if mid in SUMMITS
         else '<h1>%sの山小屋（%d軒）｜予約開始日・予約方法</h1>\n' % (E(m['name']), len(hs)))
        + '<nav class="bc" aria-label="パンくず"><a href="/">Yamatch</a> › <a href="/huts/">山小屋まとめ</a> › %s</nav>\n' % E(m['name'])
        + '<p class="lead">%s予約がいつから始まるか、予約方法、定員、%d年の営業期間をまとめました。</p>\n' % (lead, YEAR)
        + '<p class="upd">最終確認：<time datetime="%s">%s</time>　<a href="/mountains/%s/" style="color:#4e6535">%sの登山情報（アクセス・コース）を見る →</a></p>\n' % (VERIFIED, VERIFIED_JA, E(mid), E(m['name']))
        + '<table class="cmp"><thead><tr><th>山小屋</th><th>予約の開始</th><th>予約方法</th></tr></thead><tbody>%s</tbody></table>\n' % ''.join(rows)
        + (('<h2 class="sec">%sの山小屋マップ</h2>\n' % E(m['name']) + map_block(hs, START_SHORT)) if any(h['name'] in COORDS for h in hs) else '')
        + '<div id="list">\n%s\n</div>\n' % '\n'.join(card_of[h['id']] for h in hs)
        + packing_block(m)
        + ('<h2 class="sec">近くの山・同じ山小屋を使う山</h2>\n<div class="rel">%s</div>\n' % rel_html if rel_html else '')
        + '<p class="src">営業期間や予約の受付は変わることがあります。予約の前に、必ず各山小屋の公式サイトで確認してください。出典は<a href="/huts/">山小屋まとめ</a>のページにまとめています。</p>')
    write(os.path.join(ROOT, 'huts', mid, 'index.html'), SHELL % {
        'title': E(title), 'desc': E(desc), 'robots': 'index,follow,max-snippet:-1,max-image-preview:large', 'url': BASE + '/huts/%s/' % mid,
        'head': HEADCOMMON, 'css': CSS, 'ver': MAP_VER, 'body': body, 'footer': FOOTER,
        'ld': ld(crumbs([('Yamatch', '/'), ('山小屋まとめ', '/huts/'), (m['name'] + 'の山小屋', '/huts/%s/' % mid)]),
                 {'@context': 'https://schema.org', '@type': 'ItemList', 'name': '%sの山小屋' % m['name'], 'numberOfItems': len(hs),
                  'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'item': lodging(h)} for i, h in enumerate(hs)]})})
    made.add(mid)

# ---------- 山小屋ごとのページ /huts/<小屋ID>/ ----------
noindex = 0
for h in H:
    x = info[h['id']]
    name = h['name']
    mts = [M[i]['name'] for i in h['mountainIds']] + [M[o['id']]['name'] for o in h.get('otherMountains') or []]
    mts_txt = '・'.join(mts[:3])
    s_main, s_sub = split_note(x['start']) if x['start'] else (None, None)
    mt_txt = methods_text(x['methods'])
    # タイトル：答え（予約の開始）を先に見せる
    if x['none']:
        title = '%sは予約不要｜営業期間・定員・利用方法【%d年】| Yamatch' % (name, YEAR)
    elif s_main and len(s_main) <= 24:
        title = '%sの予約はいつから？%s【%d年】予約方法・営業期間 | Yamatch' % (name, s_main, YEAR)
    elif s_main:
        title = '%sの予約はいつから？予約開始日・予約方法・営業期間【%d年】| Yamatch' % (name, YEAR)
    else:
        title = '%sの予約方法・営業期間・定員【%d年】| Yamatch' % (name, YEAR)
    if len(title) > 48:
        # 長い名前・長い答えのときは、後ろの決まり文句を落として答えが切れないようにする
        title = title.replace('予約方法・営業期間 | Yamatch', '| Yamatch')
    parts = []
    if x['none']:
        parts.append('%s（%s）は予約の受付がない小屋です。%s' % (name, mts_txt, x['none'].rstrip('。') + '。'))
    else:
        if x['start']:
            parts.append('%s（%s）の予約は、%s。' % (name, mts_txt, x['start']))
        else:
            parts.append('%s（%s）の予約情報。' % (name, mts_txt))
        if mt_txt:
            parts.append('予約方法は%s。' % mt_txt)
    if x['season'] and x['season'] != '—':
        parts.append('営業期間は%s。' % x['season'])
    if x['cap']:
        parts.append('定員は%s%s人。' % ('' if x['capExact'] else '約', x['cap']))
    if x.get('feat'):
        g1 = [t for tag, t in x['feat']['items'] if tag in ('グルメ', '名物', '風呂・温泉')]
        if g1:
            parts.append('%s。' % g1[0])
    desc = ''.join(parts)
    desc = desc if len(desc) <= 150 else desc[:149] + '…'
    qa = []
    if x['none']:
        qa.append(('%sは予約が必要ですか？' % name, '予約は不要です。%s' % x['none']))
    elif x['start']:
        qa.append(('%sの予約はいつからできますか？' % name, '%s。最新の受付状況は公式サイトで確認してください。' % x['start']))
    if mt_txt:
        qa.append(('%sの予約方法は？' % name, '%sで受け付けています。%s' % (mt_txt, '予約は必須です。' if h['bookingRequired'] else '')))
    if x['season'] and x['season'] != '—':
        qa.append(('%sの営業期間は？' % name, '%s（%d年シーズンの情報）。天候や残雪で変わることがあります。' % (x['season'], YEAR)))
    if x.get('feat'):
        gour = [t for tag, t in x['feat']['items'] if tag in ('グルメ', '名物')]
        if gour:
            qa.append(('%sの名物・食事は？' % name, '%s。メニューは時期によって変わることがあります。' % '。'.join(gour)))
        rest = [t for tag, t in x['feat']['items'] if tag not in ('グルメ', '名物')]
        if rest:
            qa.append(('%sの設備・特徴は？' % name, '%s。' % '。'.join(rest)))
    thin = not (x['none'] or x['start'] or mt_txt)
    noindex += thin
    if x['none']:
        ans = '<div class="fv" style="font-size:20px">予約不要</div><div class="fs">%s</div>' % E(x['none'])
    elif s_main:
        ans = '<div class="fv" style="font-size:18px">%s</div>%s' % (E(s_main), ('<div class="fs">%s</div>' % E(s_sub)) if s_sub else '')
    else:
        ans = '<div class="fv"><span class="na">予約の開始時期は確認できていません。公式サイトで確認してください</span></div>'
    sib = []
    for i in h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]:
        for o in sum(huts_of(i), []):
            if o['id'] != h['id'] and o not in sib:
                sib.append(o)
    _t = '%s｜%s（%d年）' % (E(name), '予約不要・利用方法' if x['none'] else '予約開始日・予約方法', YEAR)
    _c = COORDS.get(name)
    _fm = h['mountainIds'][0] if h['mountainIds'] else None
    _sub = ('標高 %sm' % format(hut_ele(h), ',')) if hut_ele(h) else ''
    if _c:
        _hero = topo_hero(_c['lat'], _c['lng'], E(h['region'] + '｜' + mts_txt), _t, _sub)
    elif _fm in SUMMITS:
        _hero = topo_hero(SUMMITS[_fm]['lat'], SUMMITS[_fm]['lng'], E(h['region'] + '｜' + mts_txt), _t, '地図は%sの山頂付近' % E(M[_fm]['name']), zoom=14, pin=False)
    else:
        _hero = '<h1>%s</h1>\n' % _t
    if x['none']:
        alert_html = ''
    else:
        alert_html = '<div id="hut-alert" class="ha" data-hut="%s"></div>\n' % E(json.dumps({'id': h['id'], 'name': name, 'rule': x.get('rule')}, ensure_ascii=False, separators=(',', ':')))
    own = card_of[h['id']].replace('<h2><a href="/huts/%s/">%s</a></h2>' % (E(h['id']), E(name)), '<h2>%s</h2>' % E(name))
    body = (
        _hero + '<nav class="bc" aria-label="パンくず"><a href="/">Yamatch</a> › <a href="/huts/">山小屋まとめ</a>%s › %s</nav>\n' % (
            (' › <a href="/huts/%s/">%sの山小屋</a>' % (E(h['mountainIds'][0]), E(M[h['mountainIds'][0]]['name']))) if h['mountainIds'] else '', E(name))
        + '<div class="fact" style="background:#e9efe0;margin-bottom:12px"><div class="fl">%s</div>%s</div>\n' % ('予約' if x['none'] else '予約はいつから？', ans)
        + '<p class="upd">最終確認：<time datetime="%s">%s</time></p>\n' % (h.get('lastVerified') or VERIFIED, VERIFIED_JA)
        + (('<p class="lead">%sは、%s%s</p>\n' % (E(name), ('「%s」にあります。' % E(x['place'][0])) if x['place'][0] else '', E(x['place'][1]) + '。')) if x.get('place') else '')
        + '<div id="list">\n%s\n</div>\n' % own
        + alert_html
        + (('<p class="upd"><a href="/huts/%s/#packing" style="color:#4e6535">%sの山小屋泊の持ち物・服装のチェックリスト →</a></p>\n' % (E(_fm), E(M[_fm]['name']))) if _fm in made else '')
        + (('<h2 class="sec">%sの場所</h2>\n' % E(name) + map_block([h], START_SHORT)
            + '<a class="maplink" href="https://www.google.com/maps/search/?api=1&amp;query=%s,%s" target="_blank" rel="noopener">Googleマップで開く →</a>\n' % (
                COORDS[name]['lat'], COORDS[name]['lng'])) if name in COORDS else '')
        + '<h2 class="sec">この山小屋を使う山</h2>\n<div class="rel">%s</div>\n' % ''.join(
            '<a class="mb" href="/huts/%s/">%sの山小屋<span>%d</span></a>' % (E(i), E(M[i]['name']), count[i])
            for i in h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []])
        + ('<h2 class="sec">同じ山のほかの山小屋</h2>\n<div class="rel">%s</div>\n' % ''.join(
            '<a class="mb" href="/huts/%s/">%s</a>' % (E(o['id']), E(o['name'])) for o in sib[:16]) if sib else '')
        + ('<h2 class="sec">よくある質問</h2>\n<dl>\n%s\n</dl>\n' % faq_html(qa) if qa else '')
        + '<p class="src">営業期間や予約の受付は変わることがあります。予約の前に、必ず公式サイトで確認してください。出典は<a href="/huts/">山小屋まとめ</a>のページにまとめています。</p>')
    lds = [crumbs([('Yamatch', '/'), ('山小屋まとめ', '/huts/')]
                  + ([(M[h['mountainIds'][0]]['name'] + 'の山小屋', '/huts/%s/' % h['mountainIds'][0])] if h['mountainIds'] else [])
                  + [(name, '/huts/%s/' % h['id'])]),
           dict({'@context': 'https://schema.org'}, **lodging(h))]
    if qa:
        lds.append(faq_ld(qa))
    write(os.path.join(ROOT, 'huts', h['id'], 'index.html'), SHELL % {
        'title': E(title), 'desc': E(desc), 'robots': 'noindex,follow' if thin else 'index,follow,max-snippet:-1,max-image-preview:large',
        'url': BASE + '/huts/%s/' % h['id'], 'head': HEADCOMMON, 'css': CSS, 'ver': MAP_VER, 'body': body, 'footer': FOOTER, 'ld': ld(*lds)})
    if not thin:
        made.add(h['id'])
    else:
        made.add('!' + h['id'])
# 通知とお気に入り（assets/js/huts-alert.js）が読むデータ：小屋ID → 名前・山名・予約の開始の文・予約の型
_rules = {}
for h in H:
    x = info[h['id']]
    _rules[h['id']] = {'n': h['name'], 'mts': [M[i]['name'] for i in h['mountainIds']] or [M[o['id']]['name'] for o in h.get('otherMountains') or []][:2],
                       's': '予約不要' if x['none'] else (split_note(x['start'])[0] if x['start'] else ''), 'r': x.get('rule')}
json.dump({'note': '山小屋の予約開始のお知らせ・お気に入り用。scripts/gen_huts_page.py が作る（手で編集しない）', 'huts': _rules},
          open(os.path.join(ROOT, 'data', 'huts_rules.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('通知に対応 %d 軒／%d 軒' % (sum(1 for v in _rules.values() if v['r']), len(_rules)))
# 無くなった山・小屋のページを消す（このスクリプトが作った huts/<ID>/index.html だけ）
keep = set(x.lstrip('!') for x in made)
for name in os.listdir(os.path.join(ROOT, 'huts')):
    dp = os.path.join(ROOT, 'huts', name)
    if os.path.isdir(dp) and name not in keep and os.listdir(dp) == ['index.html']:
        os.remove(os.path.join(dp, 'index.html'))
        os.rmdir(dp)
# サイトマップ：/huts/ 以下を入れ直す（検索に出さないページは入れない）
sp = os.path.join(ROOT, 'sitemap.xml')
sm = open(sp, encoding='utf-8').read()
sm, n_old = re.subn(r'<url><loc>https://tozan-navi\.com/huts/[^<]*</loc>.*?</url>\n?', '', sm, flags=re.S)
urls = ['<url><loc>%s/huts/</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>' % (BASE, VERIFIED)]
urls += ['<url><loc>%s/huts/%s/</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>%s</priority></url>' % (
    BASE, k, VERIFIED, '0.7' if k in M else '0.6') for k in sorted(x for x in made if not x.startswith('!'))]
assert sm.count('</urlset>') == 1
open(sp, 'w', encoding='utf-8').write(sm.replace('</urlset>', '\n'.join(urls) + '\n</urlset>'))
print('山ごと %d ページ／山小屋ごと %d ページ（うち検索に出さない %d）／sitemap %d 件' % (len(count), len(H), noindex, len(urls)))
