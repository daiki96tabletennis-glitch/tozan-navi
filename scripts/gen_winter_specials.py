#!/usr/bin/env python3
"""冬の特集記事を作る（2026-11-12。運営者の指示「冬でも検索から来てもらえる人を増やす」）

- /articles/hatsuhinode-hiking/  初日の出登山（山頂の日の出の時刻と、元日の始発で間に合うか）
- /articles/diamond-fuji/        ダイヤモンド富士が見える山（山頂から太陽が富士山頂に重なる日と時刻）
- /articles/winter-views/        冬にしか見られない景色の山（樹氷・霧氷・雪原。出典で確かめた山だけ）

中身：data/winter_specials.json（手で書く。元日の運行・神社・注記）と mountains.json。
日の出・ダイヤモンド富士の日付と時刻は scripts/sun_calc.py・diamond_fuji.py で計算する。
見た目は「冬でも登れる関東の山7選」（articles/winter-no-crampons）の CSS を読み込んで使う。手で編集しない。
  python3 scripts/gen_winter_specials.py          書く
  python3 scripts/gen_winter_specials.py --check  書かずに、いまのファイルと同じかを見る（違えば終了コード1）
"""
import datetime
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import sun_calc  # noqa: E402
import diamond_fuji  # noqa: E402
import gear_calendar  # noqa: E402

GEN = '<!-- generated: scripts/gen_winter_specials.py -->'
SITE = 'https://tozan-navi.com'
UPDATED = '2026-11-14'


def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def load():
    M = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    SC = json.load(open(os.path.join(ROOT, 'data', 'summit_coords.json'), encoding='utf-8'))['mountains']
    W = json.load(open(os.path.join(ROOT, 'data', 'winter_specials.json'), encoding='utf-8'))
    return {m['id']: m for m in M}, SC, W


def summit(m, SC):
    c = SC.get(m['id']) or {}
    return c.get('lat') or m['lat'], c.get('lng') or m['lng'], c.get('ele') or m['elevation']


def css():
    s = open(os.path.join(ROOT, 'articles', 'winter-no-crampons', 'index.html'), encoding='utf-8').read()
    m = re.search(r'<style>.*?</style>', s, re.S)
    if not m:
        raise SystemExit('winter-no-crampons の CSS が見つからない')
    extra = ('.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch;margin-bottom:8px}'
             '.tbl table{border-collapse:collapse;width:100%;min-width:560px;font-size:13px;background:#fff}'
             '.tbl th,.tbl td{padding:7px 8px;border-bottom:1px solid #e6e1d6;vertical-align:top;text-align:left}'
             '.tbl th{background:#f3f0e8;color:#4a5e3a;font-weight:700;white-space:nowrap}'
             '.big-time{font-family:Outfit,sans-serif;font-size:20px;font-weight:700;color:#2a3e2a}'
             '.ws-links a{color:#4a6038;font-weight:700}'
             '.ws-src{font-size:12px;color:#777;margin-top:6px}'
             '.ws-note{background:#f7f6f2;border-radius:10px;padding:10px 14px;font-size:13px;line-height:1.7;margin-top:10px}')
    return m.group(0).replace('</style>', extra + '</style>')


HEADER = ('<header class="ym-site-header" style="background:#3a4f28;padding:12px 16px;margin:0"><div style="max-width:760px;margin:0 auto;display:flex;align-items:center;gap:8px">'
          '<a href="/" style="display:flex;align-items:center;gap:6px;text-decoration:none;min-width:0;margin-right:auto"><svg width="24" height="24" viewBox="0 0 36 36" style="flex-shrink:0" aria-hidden="true"><polygon points="18,4 34,30 2,30" fill="#405830"/><polygon points="18,10 30,30 6,30" fill="#789858"/><polygon points="10,30 17,17 24,30" fill="#2c4020"/></svg><span style="color:#fff;font-size:20px;font-weight:700;font-family:Georgia,serif;line-height:1">Yamatch</span></a>'
          '<a href="/" style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);color:#fff;border-radius:8px;padding:6px 10px;font-size:12px;font-weight:600;line-height:1.2;text-decoration:none;white-space:nowrap">山を検索する</a>'
          '<a href="/articles/" style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);color:#fff;border-radius:8px;padding:6px 10px;font-size:12px;font-weight:600;line-height:1.2;text-decoration:none;white-space:nowrap">記事一覧へ</a></div></header>')

FOOTER = ('<footer>\n  <p>Yamatch（やまっち） — 出発地から登る山を探せる登山サーチ</p>\n'
          '  <p style="margin-top:6px"><a href="/" style="color:#7a9a7a">← トップページに戻る</a></p>\n'
          '  <p style="margin-top:6px"><a href="/terms/" style="color:#7a9a7a">利用規約</a> | <a href="/privacy/" style="color:#7a9a7a">プライバシーポリシー</a> | <a href="/listing/" style="color:#7a9a7a">お店の掲載</a></p>\n</footer>')

CAL_ICON = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            'style="vertical-align:-2px;margin-right:3px;display:inline-block"><path d="M8 2v3"/><path d="M16 2v3"/><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/></svg>')


def page(slug, title, desc, h1, label, pills, body, faq, crumb, photos):
    url = '%s/articles/%s/' % (SITE, slug)
    ld = [
        {'@context': 'https://schema.org', '@type': 'Article', 'headline': title, 'description': desc,
         'author': {'@type': 'Person', 'name': 'Yamatch編集部'},
         'publisher': {'@type': 'Organization', 'name': 'Yamatch', 'url': SITE}, 'dateModified': UPDATED, 'url': url,
         'image': '%s/articles/images/%s' % (SITE, photos)},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Yamatch', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': '登山ガイド記事', 'item': SITE + '/articles/'},
            {'@type': 'ListItem', 'position': 3, 'name': crumb, 'item': url}]},
    ]
    og_img = '<meta property="og:image" content="%s/articles/images/%s">\n' % (SITE, esc(photos))
    faq_html = '<h2 id="faq">よくある質問</h2>' + ''.join(
        '<div class="tips-card" style="padding:14px 18px;margin-bottom:12px"><div style="font-weight:700;color:#2a3e2a;margin-bottom:4px">Q. %s</div><div>%s</div></div>' % (esc(q), esc(a))
        for q, a in faq)
    out = ['<!DOCTYPE html>\n<html lang="ja">\n<head>\n' + GEN,
           '<!-- Google tag (gtag.js) -->\n<script async src="https://www.googletagmanager.com/gtag/js?id=G-TMTVVTEEGF"></script>\n'
           "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-TMTVVTEEGF');</script>\n"
           '<script defer src="/assets/js/ym-track.js?v=20261103b"></script>',
           '<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">',
           '<title>%s | Yamatch</title>' % esc(title),
           '<meta name="description" content="%s">' % esc(desc),
           '<meta property="og:title" content="%s | Yamatch">' % esc(title),
           '<meta property="og:description" content="%s">' % esc(desc),
           '<meta property="og:type" content="article">\n<meta property="og:url" content="%s">\n<meta property="og:site_name" content="Yamatch">' % url,
           og_img.rstrip('\n'),
           '<meta property="article:modified_time" content="%s">' % UPDATED,
           ''.join('<script type="application/ld+json">%s</script>\n' % json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in ld).rstrip('\n'),
           '<link rel="canonical" href="%s">' % url,
           css(), '</head>\n<body>', HEADER,
           '<a id="top"></a><div class="article-hero">\n  <div class="hero-inner">\n    <div class="article-label">%s</div>\n    <h1 class="article-title">%s</h1>\n    <p class="article-desc">%s</p>\n'
           '    <div class="article-meta"><span class="meta-pill updated-pill">%s 最終更新: %s</span>%s</div>\n  </div>\n</div>' % (
               esc(label), h1, esc(desc), CAL_ICON, UPDATED, ''.join('\n      <span class="meta-pill">%s</span>' % esc(p) for p in pills)),
           '<main>', body, faq_html, '</main>', FOOTER,
           '<script src="/assets/js/to-top.js?v=20261025a" defer></script>',
           '<script src="/assets/js/card-photo-credits.js?v=20261105b" defer></script>',
           '</body></html>\n']
    return '\n'.join(x for x in out if x != '')


def direction(az):
    names = ['北', '北北東', '北東', '東北東', '東', '東南東', '南東', '南南東', '南', '南南西', '南西', '西南西', '西', '西北西', '北西', '北北西']
    return names[int((az % 360) / 22.5 + 0.5) % 16]


def dur(v):
    if v is None:
        return None
    h, mi = divmod(int(v), 60)
    return ('%d時間%d分' % (h, mi) if mi else '%d時間' % h) if h else '%d分' % mi


def closed(m):
    """規制中の山（status.level が restricted）は、カードに閉鎖の注意を出す（check_pages.py セクション13）"""
    st = m.get('status') or {}
    if st.get('level') != 'restricted':
        return ''
    link = (' <a href="%s" target="_blank" rel="noopener" style="color:#7a1f14;">案内</a>' % esc(st['sourceUrl'])) if st.get('sourceUrl') else ''
    return ('<div class="mc-closed" data-closed="%s" style="margin:10px 14px 0;padding:8px 10px;background:#fdecea;border-left:3px solid #c0392b;border-radius:6px;'
            'font-size:12.5px;line-height:1.6;color:#7a1f14;"><b>閉鎖中</b>：%s%s</div>' % (esc(m['id']), esc(st.get('summary') or ''), link))


ONLY_PICKED = ('diamond', 'views')


def hatsu_li(W):
    """初日の出の記事へのリンク。公開するまで（publish が false のあいだ）は出さない"""
    if not W['hatsuhinode'].get('publish', True):
        return ''
    return '<li><a href="/articles/hatsuhinode-hiking/" style="color:#4a6038;font-weight:700">初日の出登山 関東（山頂の日の出の時刻と元日の始発）</a></li>'


def photo(m, W=None, art=None):
    """カードの写真。記事に合わせて選んだ写真（winter_specials.json の photos。scripts/winter_photos.py で選ぶ）があればそれ、無ければ山の1枚目。
    記事のために取り込んだ Commons の写真は image-credits.json に無いので、作者・ライセンスの1行をここで書く（card-photo-credits.js と同じ形）"""
    rec = ((W or {}).get('photos') or {}).get(art, {}).get(m['id']) if art else None
    if rec:
        img = '<img src="%s" class="mountain-photo" alt="%s" loading="lazy">' % (esc(rec['src']), esc(m['name']))
        if rec.get('source') == 'pakutaso':   # 表示は不要だが、ぱくたその推奨に合わせて出す
            return img + ('<div class="ym-photo-credit" style="font-size:11px;line-height:1.5;color:#7a776e;margin:4px 0 6px;padding:0 2px">'
                          '写真：<a href="https://www.pakutaso.com" target="_blank" rel="noopener">フリー素材ぱくたそ</a></div>')
        if not rec.get('credit'):
            return img
        lic = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(rec['licenseUrl']), esc(rec['license'])) if rec.get('licenseUrl') else esc(rec['license'])
        return img + ('<div class="ym-photo-credit" style="font-size:11px;line-height:1.5;color:#7a776e;margin:4px 0 6px;padding:0 2px;word-break:break-word">'
                      '写真：%s（%s、<a href="%s" target="_blank" rel="noopener">%s</a>）</div>' % (
                          esc(rec['credit']), lic, esc(rec['pageUrl']), 'Flickr' if rec.get('source') == 'flickr' else 'Wikimedia Commons'))
    # ダイヤモンド富士・冬の絶景は、記事に合う写真を選んだ山だけ写真を出す（山ページの写真は使わない。運営者の指示・2026-11-14）
    if art in ONLY_PICKED:
        return ''
    ph = m.get('photos') or []
    if not ph:
        return ''
    return '<img src="%s" class="mountain-photo" alt="%s" loading="lazy">' % (esc(ph[0]), esc(m['name']))


def row(label, val):
    return '<div class="info-row"><span class="info-label">%s</span><span class="info-val">%s</span></div>' % (esc(label), val)


def table(head, rows):
    return ('<div class="tbl"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
        ''.join('<th>%s</th>' % esc(h) for h in head),
        ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % c for c in r) for r in rows)))


NUM = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'


def md(d):
    return '%d月%d日' % (d.month, d.day)


# ---------------------------------------------------------------- 初日の出
def ranges(M, SC):
    """文に入れる計算の値（{ryugatake_range} など）"""
    out = {}
    for k in ('ryugatake', 'takao'):
        lat, lng, ele = summit(M[k], SC)
        e = diamond_fuji.events(lat, lng, ele)[0]
        out[k + '_range'] = md(e['from']) + ('〜' + md(e['to']) if e['to'] != e['from'] else '')
    return out


def fill(s, M, SC):
    for k, v in ranges(M, SC).items():
        s = s.replace('{' + k + '}', v)
    if '{' in s:
        raise SystemExit('置き換えていない値：' + s)
    return s


def hatsuhinode(M, SC, W):
    H = W['hatsuhinode']
    y = H['year']
    day = datetime.date(y, 1, 1)
    cards, comp, toc = [], [], []
    rows = []
    for i, it in enumerate(H['mountains']):
        m = M[it['id']]
        lat, lng, ele = summit(m, SC)
        rise, _ = sun_calc.sunrise_sunset(lat, lng, day, ele)
        flat, _ = sun_calc.sunrise_sunset(lat, lng, day)
        az = sun_calc.sun_position(lat, lng, rise)[0]
        fa = datetime.datetime.strptime('%s %s' % (day, it['firstArrive']), '%Y-%m-%d %H:%M').replace(tzinfo=sun_calc.JST)
        gap = int((rise - fa).total_seconds() // 60)
        gap_txt = ('日の出の約%d分前' % gap) if gap > 0 else '日の出のあと'
        rows.append((it, m, rise, az, gap_txt))
        n = NUM[i]
        toc.append('<li style="margin:3px 0"><a href="#m-%s" style="color:#4a6038">%s %s</a></li>' % (m['id'], n, esc(m['name'])))
        sh = it.get('shrine')
        shrine = ('<a href="%s" target="_blank" rel="noopener" style="color:#4a6038">%s</a>（%s）' % (esc(sh['url']), esc(sh['name']), esc(sh['where']))) if sh else 'なし'
        r0 = (m.get('routes') or [{}])[0]
        drive = m.get('driveTimeShinjuku') or m.get('driveShinjuku')
        links = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (esc(l['url']), esc(l['label'])) for l in it.get('links') or [])
        extra = ''
        if it.get('diamondLink'):
            extra = '<p style="margin-top:8px">→ <a href="/articles/diamond-fuji/#m-%s" style="color:#4a6038;font-weight:700">ダイヤモンド富士が見える山（日付と時刻）</a></p>' % m['id']
        body = ''.join([
            row('山頂の日の出', '<span class="big-time">%s</span> ごろ（%s・方位%d°）' % (sun_calc.hm(rise), direction(az), round(az))),
            row('見る場所', esc(it['place'])),
            row('元日の始発', '新宿から%s着 %s（%s）' % (esc(it['station']), esc(it['firstArrive']), gap_txt)),
            row('初詣', shrine),
            row('代表コース', '%s（%s・難易度 %s）' % (esc(r0.get('name') or ''), esc(r0.get('time') or ''), esc(m.get('difficulty') or ''))),
            row('車', '新宿から約%s' % dur(drive) if drive else '—'),
        ])
        cards.append(
            '<div class="mountain-card" id="m-%s">\n  <div class="mountain-card-header" data-mountain-id="%s">\n'
            '    <h2 class="mountain-card-title" style="margin:0;padding:0;border:none;font-size:18px;line-height:1.4">%s %s</h2>\n'
            '    <div class="mountain-card-sub">%s・標高%sm</div>\n  </div>\n  %s\n  <div class="mountain-card-body">\n    %s\n'
            '    <div class="ws-note"><strong>日の出に間に合わせるには</strong><br>%s%s</div>\n'
            '    <p style="margin-top:10px"><a href="/mountains/%s/" style="color:#4a6038;font-weight:700">%sの登山ガイドを見る →</a></p>\n  </div>\n</div>' % (
                m['id'], m['id'], n, esc(m['name']), esc(m.get('prefecture') or m.get('area') or ''), '{:,}'.format(int(m['elevation'])), photo(m, W, 'hatsuhinode') + closed(m), body,
                esc(fill(it['howto'], M, SC)), ('<ul class="ws-links" style="margin:6px 0 0 18px">%s</ul>' % links if links else '') + extra,
                m['id'], esc(m['name'])))
        comp.append(['<a href="#m-%s" style="color:#4a6038;font-weight:700">%s %s</a>' % (m['id'], n, esc(m['name'])),
                     '%sm' % '{:,}'.format(int(m['elevation'])), sun_calc.hm(rise), '%s %s' % (esc(it['station']), esc(it['firstArrive'])), esc(r0.get('time') or ''),
                     'あり' if sh else '—'])
    first = rows[0][2]
    earliest = min(rows, key=lambda r: r[2])
    latest = max(rows, key=lambda r: r[2])
    toc_html = ('<nav class="tips-card" id="toc" aria-label="目次" style="padding:16px 20px"><div style="font-weight:700;color:#2a3e2a;margin-bottom:6px">目次</div>'
                '<ul style="margin:0;padding:0;list-style:none;font-size:14px;line-height:1.7"><li style="margin:3px 0"><a href="#first-train" style="color:#4a6038">元日の始発では山頂の日の出に間に合わない</a></li>%s'
                '<li style="margin:3px 0"><a href="#compare" style="color:#4a6038">%d山の比較表</a></li><li style="margin:3px 0"><a href="#tips" style="color:#4a6038">暗いうちに登るときに気をつけること</a></li>'
                '<li style="margin:3px 0"><a href="#faq" style="color:#4a6038">よくある質問</a></li></ul></nav>') % (''.join(toc), len(rows))
    ft = table(['山', '最寄り駅', '始発の着', '山頂の日の出', ''],
               [[esc(m['name']), esc(it['station']), esc(it['firstArrive']), sun_calc.hm(rise), gap] for it, m, rise, az, gap in rows])
    body = '\n'.join([
        '<div class="info-note">⚠️ <strong>%d年元日の電車・バス・ケーブルカー</strong><br>終夜運転・臨時列車・ケーブルカーの早朝の運転は、%s時点でどの会社もまだ発表していません。発表されたら、この記事に書き足します。</div>' % (y, '2026年11月12日'),
        '<div class="lead-box">山頂で迎える初日の出の時刻を、山ごとに計算しました。国立天文台の暦と同じ計算に、山頂の高さで地平線が下がるぶんを入れています（手前に山があると数分遅くなります）。<br><br>'
        '%d年の元日、ここで選んだ山の山頂の日の出は<strong>%s（%s）〜%s（%s）</strong>ごろです。<br><br>'
        'あわせて、<strong>新宿からの元日の始発で、山頂の日の出に間に合うか</strong>を山ごとに確かめました。</div>' % (
            y, sun_calc.hm(earliest[2]), esc(earliest[1]['name']), sun_calc.hm(latest[2]), esc(latest[1]['name'])),
        toc_html,
        '<h2 id="first-train">元日の始発では山頂の日の出に間に合わない</h2>',
        '<p style="margin-bottom:12px">新宿駅を元日の始発で出ると、どの山も最寄り駅に着くのは6時台以降です。駅からさらにバス・ケーブルカーに乗るか、歩いて登る時間が要るので、ふだんのダイヤでは山頂の日の出に間に合いません。山頂で日の出を見るには、元日の臨時列車・ケーブルカーの早朝の運転を使う、前の日に山の上の宿に泊まる、車で行く、のどれかになります。</p>',
        ft,
        '<p class="ws-src">%s。山頂の日の出は計算の目安。</p>' % esc(H['firstTrainNote']),
        '<h2>初日の出の山%d選</h2>' % len(rows),
        '\n'.join(cards),
        '<h2 id="compare">%d山の比較表</h2>' % len(rows),
        table(['山', '標高', '山頂の日の出', '元日の始発（新宿から）', '代表コース', '初詣'], comp),
        '<h2 id="tips">暗いうちに登るときに気をつけること</h2>',
        '<div class="tips-card" style="padding:16px 20px"><ul style="margin:0 0 0 18px;line-height:1.9">'
        '<li>日の出の前は登山道が真っ暗です。ヘッドランプと予備の電池を持っていきましょう</li>'
        '<li>日の出を待つあいだは動かないので、体が冷えます。ダウンなどの防寒着と手袋・帽子を持っていきましょう</li>'
        '<li>雪や凍結がある日は、暗い中では足もとが見えにくくなります。冬の装備は各山のページの装備カレンダーで確かめてください</li>'
        '<li>元日は人が多い山があります。駐車場・ケーブルカーの混み具合は、各社の案内を確かめてください</li></ul></div>',
        '<h2>あわせて読みたい</h2>',
        '<div class="tips-card" style="padding:16px 20px"><ul style="margin:0 0 0 18px;line-height:1.9">'
        '<li><a href="/articles/diamond-fuji/" style="color:#4a6038;font-weight:700">ダイヤモンド富士が見える山（日付と時刻）</a></li>'
        '<li><a href="/articles/winter-no-crampons/" style="color:#4a6038;font-weight:700">冬でも登れる関東の山7選｜雪なし・アイゼン不要</a></li>'
        '<li><a href="/search/train-daytrip/" style="color:#4a6038;font-weight:700">電車で行ける日帰り登山</a></li></ul></div>',
    ])
    faq = [
        ('%d年の元日、山頂の日の出は何時ですか？' % y,
         'この記事の計算では、高尾山%s・御岳山%s・筑波山%s・大山%sごろです。平地より山頂のほうが数分早く日が昇ります。手前に山があるとその分遅くなります。' % tuple(
             sun_calc.hm(next(r[2] for r in rows if r[1]['id'] == k)) for k in ('takao', 'mitakesan', 'tsukuba', 'oyama'))),
        ('元日の始発の電車で山頂の初日の出に間に合いますか？',
         'ふだんのダイヤでは間に合いません。新宿からの元日の始発で、高尾山口駅は%s、御嶽駅は%s、つくば駅は%s、伊勢原駅は%sに着き、そこから山頂まで登る時間が要ります。元日の臨時列車やケーブルカーの早朝の運転を使うか、前の日に泊まる計画が要ります。' % tuple(
             next(it['firstArrive'] for it in H['mountains'] if it['id'] == k) for k in ('takao', 'mitakesan', 'tsukuba', 'oyama'))),
        ('初日の出と初詣を一緒にできる山はどこですか？',
         '山頂や登山道の途中に神社・寺がある山です。この記事では、高尾山（高尾山薬王院）、御岳山（武蔵御嶽神社）、筑波山（筑波山神社）、大山（大山阿夫利神社）、鋸山（日本寺）を紹介しています。'),
    ]
    photos = 'hero_hatsuhinode.jpg'
    title = '初日の出登山 関東【%d年】山頂の日の出の時刻と、元日の始発で間に合うか' % y
    desc = '%d年元日に関東の山頂で初日の出を見るなら。高尾山・御岳山・日の出山・筑波山・大山・鋸山・竜ヶ岳の山頂の日の出の時刻（計算）、新宿からの元日の始発で間に合うか、初詣ができる神社・寺をまとめました。' % y
    return page('hatsuhinode-hiking', title, desc, '初日の出登山 関東【%d年】<br>山頂の日の出の時刻と元日の始発' % y, '冬の特集',
                ['初日の出', '📍 関東', '元日'], body, faq, '初日の出登山 関東（%d年）' % y, photos)


# ---------------------------------------------------------------- ダイヤモンド富士
def diamond_list(M, SC, W):
    D = W['diamond']
    out = []
    # 載せる山は手で選ぶ（include。2026-11-12 運営者の指示「もっと厳選したい」）：
    # ダイヤモンド富士の名所として知られる山（関東の富士見百景・山の特徴の文）と、冬に見られて無理なく行ける山
    for it in D['include']:
        m = M[it['id']]
        fp = [f for f in m.get('featurePoints') or [] if '富士' in json.dumps(f, ensure_ascii=False)]
        ex = D['extra'].get(m['id'])
        if not fp and not ex:
            raise SystemExit('富士山が見える根拠が無い：' + m['id'])
        lat, lng, ele = summit(m, SC)
        ev = diamond_fuji.events(lat, lng, ele)
        if not ev:
            raise SystemExit('計算でダイヤモンド富士の日が無い：' + m['id'])
        dkm, az, alt = diamond_fuji.fuji_view(lat, lng, ele)
        out.append({'m': m, 'ev': ev, 'dkm': dkm, 'az': az, 'alt': alt, 'fp': fp, 'ex': ex, 'why': it['why']})
    out.sort(key=lambda x: x['ev'][0]['date'])
    return out


def ev_text(e):
    side = '日の出' if e['morning'] else '日没'
    if e['kind'] == 'near':
        return '%s（%s）ごろ %s：太陽が富士山頂のすぐ上をかすめる' % (md(e['date']), side, sun_calc.hm(e['time']))
    if e['from'] != e['to']:
        return '%s〜%s（%s）。いちばん重なるのは%s %sごろ' % (md(e['from']), md(e['to']), side, md(e['date']), sun_calc.hm(e['time']))
    return '%s（%s）%sごろ' % (md(e['date']), side, sun_calc.hm(e['time']))


def parking_ok(m):
    v = m.get('parking') or ''
    return bool(v) and '確認できていない' not in v


def pref_of(m):
    return re.split(r'[・、]', m.get('area') or '')[0]


def ev_short(evs):
    out = []
    for e in evs:
        d = md(e['from']) + ('〜' + md(e['to']) if e['to'] != e['from'] else '')
        out.append('%s（%s）%sごろ%s' % (d, '日の出' if e['morning'] else '日没', sun_calc.hm(e['time']), '・かすめる' if e['kind'] == 'near' else ''))
    return '・'.join(out)


def best_text(evs):
    e = evs[0]
    return '%s %sごろです' % (md(e['date']), sun_calc.hm(e['time']))


def get_ev(L, mid):
    return next(x['ev'] for x in L if x['m']['id'] == mid)


def pref_answer(by_pref, pf):
    xs = by_pref.get(pf, [])
    return '、'.join('%s（%s）' % (x['m']['name'], ev_short(x['ev'])) for x in xs) + 'です（この記事の計算）。'


def tanzawa_more(M, SC):
    out = []
    for mid in ('tanzawa', 'hirugata'):
        m = M[mid]
        lat, lng, ele = summit(m, SC)
        out.append('%sでも%s' % (m['name'], ev_short(diamond_fuji.events(lat, lng, ele))))
    return '、'.join(out) + 'に見られます（計算）'


def diamond(M, SC, W):
    D = W['diamond']
    L = diamond_list(M, SC, W)
    cards, toc, comp = [], [], []
    for i, x in enumerate(L):
        m = x['m']
        n = NUM[i] if i < len(NUM) else '%d.' % (i + 1)
        toc.append('<li style="margin:3px 0"><a href="#m-%s" style="color:#4a6038">%s %s</a></li>' % (m['id'], n, esc(m['name'])))
        r0 = (m.get('routes') or [{}])[0]
        drive = m.get('driveTimeShinjuku') or m.get('driveShinjuku')
        train = m.get('trainTimeShinjuku')
        view = esc(x['fp'][0].get('text') or x['fp'][0].get('label')) if x['fp'] else (
            '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(x['ex']['viewUrl']), esc(x['ex']['viewSource'])))
        evs = '<br>'.join('<span class="big-time" style="font-size:16px">%s</span>' % esc(ev_text(e)) for e in x['ev'])
        note = D['note'].get(m['id'])
        side = '日の出' if x['ev'][0]['morning'] else '日没'
        tip = ('日没のころのダイヤモンド富士は、そのあと暗い道を下ることになります。ヘッドランプを持ち、下りの時間を見て計画しましょう。' if side == '日没'
               else '日の出のころのダイヤモンド富士は、暗いうちに登ることになります。ヘッドランプを持ちましょう。')
        body = ''.join([
            row('選んだ理由', esc(x['why'])),
            row('ダイヤモンド富士', evs),
            row('富士山の方角', '%s（方位%d°）・山頂から約%dkm' % (direction(x['az']), round(x['az']), round(x['dkm']))),
            row('富士山の眺め', view),
            row('代表コース', '%s（%s・難易度 %s）' % (esc(r0.get('name') or ''), esc(r0.get('time') or ''), esc(m.get('difficulty') or ''))),
            row('新宿から', '電車 約%s・車 約%s' % (dur(train) or '—', dur(drive) or '—') if train else '車 約%s' % (dur(drive) or '—')),
            row('駐車場', esc(m['parking'])) if parking_ok(m) else '',
        ])
        cards.append(
            '<div class="mountain-card" id="m-%s">\n  <div class="mountain-card-header" data-mountain-id="%s">\n'
            '    <h2 class="mountain-card-title" style="margin:0;padding:0;border:none;font-size:18px;line-height:1.4">%s %s</h2>\n'
            '    <div class="mountain-card-sub">%s・標高%sm・%s</div>\n  </div>\n  %s\n  <div class="mountain-card-body">\n    %s\n'
            '    <div class="ws-note">%s%s</div>\n'
            '    <p style="margin-top:10px"><a href="/mountains/%s/" style="color:#4a6038;font-weight:700">%sの登山ガイドを見る →</a></p>\n  </div>\n</div>' % (
                m['id'], m['id'], n, esc(m['name']), esc(m.get('prefecture') or m.get('area') or ''), '{:,}'.format(int(m['elevation'])), side,
                photo(m, W, 'diamond') + closed(m), body, (esc(note) + '<br>') if note else '', esc(tip), m['id'], esc(m['name'])))
        for e in x['ev']:
            comp.append((e['date'], ['<a href="#m-%s" style="color:#4a6038;font-weight:700">%s</a>' % (m['id'], esc(m['name'])),
                                     md(e['from']) + ('〜' + md(e['to']) if e['to'] != e['from'] else ''), '日の出' if e['morning'] else '日没',
                                     sun_calc.hm(e['time']), 'かすめる' if e['kind'] == 'near' else '重なる']))
    comp.sort(key=lambda r: ((r[0].month - 12) % 12, r[0].day))
    winter = [r for r in comp if r[0].month in (12, 1, 2)]
    by_pref = {}
    for x in L:
        by_pref.setdefault(pref_of(x['m']), []).append(x)
    pref_rows = []
    for pf in ('東京都', '神奈川県', '山梨県', '千葉県'):
        for x in by_pref.get(pf, []):
            pref_rows.append([esc(pf), '<a href="#m-%s" style="color:#4a6038;font-weight:700">%s</a>' % (x['m']['id'], esc(x['m']['name'])), esc(ev_short(x['ev']))])
    ktr_rows = []
    for c in D['ktr']['compare']:
        x = next(v for v in L if v['m']['id'] == c['id'])
        ktr_rows.append([esc(x['m']['name']), ' / '.join(esc(md(e['from']) + ('〜' + md(e['to']) if e['to'] != e['from'] else '')) for e in x['ev']), esc(c['ktr'])])
    toc_html = ('<nav class="tips-card" id="toc" aria-label="目次" style="padding:16px 20px"><div style="font-weight:700;color:#2a3e2a;margin-bottom:6px">目次</div>'
                '<ul style="margin:0;padding:0;list-style:none;font-size:14px;line-height:1.7"><li style="margin:3px 0"><a href="#about" style="color:#4a6038">ダイヤモンド富士とは</a></li>'
                '<li style="margin:3px 0"><a href="#pref" style="color:#4a6038">見える場所（東京・神奈川・山梨・千葉）</a></li>'
                '<li style="margin:3px 0"><a href="#winter" style="color:#4a6038">冬（12〜2月）に見える山と時間</a></li>'
                '<li style="margin:3px 0"><a href="#calendar" style="color:#4a6038">ダイヤモンド富士カレンダー2026-2027</a></li>%s'
                '<li style="margin:3px 0"><a href="#method" style="color:#4a6038">日付の計算のしかた</a></li><li style="margin:3px 0"><a href="#faq" style="color:#4a6038">よくある質問</a></li></ul></nav>') % ''.join(toc)
    body = '\n'.join([
        '<div class="info-note">⚠️ 日付と時刻は計算の目安です。前後2〜3日の幅を見て計画し、当日の天気（富士山が見えるか）を確かめてください。</div>',
        '<div class="lead-box">山頂から見て、太陽が富士山の頂上にちょうど重なる「ダイヤモンド富士」。ダイヤモンド富士の名所として知られる山と、冬に見られて無理なく行ける山の%d山を選び、その日付と時刻を計算しました。<br><br>'
        '富士山の東側の山（丹沢・高尾・房総など）では夕方の日没に、西側の山（竜ヶ岳・七面山）では朝の日の出に見られます。</div>' % len(L),
        toc_html,
        '<h2 id="about">ダイヤモンド富士とは</h2>',
        '<div class="tips-card" style="padding:16px 20px;line-height:1.9">富士山の山頂に太陽が重なり、ダイヤモンドのように輝いて見える景色のことです。'
        '太陽が富士山の真上に来るのは、見る場所ごとに決まった日だけで、多くの場所では1年に2回（冬至のころの1回だけの場所もあります）。'
        '富士山より東の場所（東京・神奈川・千葉や、山梨の山中湖のあたり）では夕日が沈むとき、西の場所（本栖湖や身延のあたり）では朝日が昇るときに見られます。'
        'ここでは、登山で山頂から見られる日付と時間を計算しました。</div>',
        '<h2 id="pref">ダイヤモンド富士が見える場所（東京・神奈川・山梨・千葉の山）</h2>',
        table(['都県', '山', '見える日（計算）'], pref_rows),
        '<h2 id="winter">冬（12〜2月）にダイヤモンド富士が見える山と時間</h2>',
        table(['山', '日付', '時間帯', '時刻', ''], [r[1] for r in winter]),
        '<h2 id="calendar">ダイヤモンド富士カレンダー2026-2027（日付と時間・12月から）</h2>',
        table(['山', '日付', '時間帯', '時刻', ''], [r[1] for r in comp]),
        '<h2>ダイヤモンド富士が見える山%d選（12月から日付の順）</h2>' % len(L),
        '\n'.join(cards),
        '<h2 id="method">日付の計算のしかた</h2>',
        '<div class="tips-card" style="padding:16px 20px;line-height:1.9">山頂の位置と標高から、富士山の剣ヶ峰（3,776m）が見える方角と高さ（地球の丸みと大気による浮き上がりを入れる）を出し、'
        '毎日、太陽がその方角に来た時刻に、太陽の中心が富士山頂からどれだけ離れているかを計算しました。太陽の半径（約0.27°）より近ければ「重なる」、少し外れる日は「かすめる」としています。'
        '地形で富士山が隠れるかどうかは計算していないので、山のデータで富士山が見えると確かめた山だけを載せています。<br><br>'
        '国土交通省 関東地方整備局「<a href="%s" target="_blank" rel="noopener" style="color:#4a6038">関東の富士見百景</a>」のダイヤモンド富士の一覧と、同じ場所で比べると次のとおりです（一覧は見る人の標高を考えない計算で、1〜3日ほどずれます）。</div>' % esc(D['ktr']['url']),
        table(['山', 'この記事の計算', '関東地方整備局の一覧'], ktr_rows),
        '<h2>あわせて読みたい</h2>',
        '<div class="tips-card" style="padding:16px 20px"><ul style="margin:0 0 0 18px;line-height:1.9">'
        '' + hatsu_li(W) + ''
        '<li><a href="/articles/winter-no-crampons/" style="color:#4a6038;font-weight:700">冬でも登れる関東の山7選｜雪なし・アイゼン不要</a></li></ul></div>',
    ])
    wn = [r for r in winter]
    faq = [
        ('冬にダイヤモンド富士が見える山はどこですか？',
         '12〜2月に見られるのは、' + '、'.join(sorted(set(re.sub(r'<[^>]+>', '', r[1][0]) for r in wn), key=lambda s: s)) + 'です（この記事の計算）。'),
        ('ダイヤモンド富士とは何ですか？',
         '富士山の山頂に太陽が重なり、ダイヤモンドのように輝いて見える景色のことです。見える日は場所ごとに決まっていて、富士山より東では日没、西では日の出のときに見られます。'),
        ('高尾山のダイヤモンド富士はいつ・何時ですか？',
         '冬至のころ（12月下旬）の日没です。この記事の計算では%s。関東地方整備局は12月17〜26日としています。' % ev_short(get_ev(L, 'takao'))),
        ('竜ヶ岳のダイヤモンド富士はいつ・何時ですか？',
         '冬の朝の日の出です。この記事の計算では、山頂から太陽が富士山頂に重なるのは%sごろで、いちばん重なるのは%s。登山道の途中の低い場所ほど重なる日が遅くなります。%s' % (
             ranges(M, SC)['ryugatake_range'], best_text(get_ev(L, 'ryugatake')), ('駐車場は' + M['ryugatake']['parking'] + '。') if parking_ok(M['ryugatake']) else '')),
        ('東京でダイヤモンド富士が見える山はどこですか？',
         pref_answer(by_pref, '東京都')),
        ('神奈川でダイヤモンド富士が見える山はどこですか？',
         pref_answer(by_pref, '神奈川県')),
        ('丹沢でダイヤモンド富士が見える山はどこですか？',
         '塔ノ岳で%s（この記事の計算）。山頂に尊仏山荘（通年営業）があります。同じ丹沢の%s。' % (ev_short(get_ev(L, 'tonosaki')), tanzawa_more(M, SC))),
        ('山梨でダイヤモンド富士が見える山はどこですか？',
         pref_answer(by_pref, '山梨県')),
        ('千葉でダイヤモンド富士が見える山はどこですか？',
         pref_answer(by_pref, '千葉県')),
        ('初日の出とダイヤモンド富士を一緒に見られる山はありますか？',
         '竜ヶ岳です。計算では、山頂から太陽が富士山頂に重なるのは%sごろで、元日は山頂からだと少し外れます。登山道の途中の低い場所ほど重なる日が遅くなり、元日に石仏の見晴台で富士山頂の真ん中から昇ったという登山記録があります。' % ranges(M, SC)['ryugatake_range']),
    ]
    photos = 'hero_diamond_fuji.jpg'
    title = 'ダイヤモンド富士が見える場所・山【2026-2027】いつ何時？カレンダー｜高尾山・竜ヶ岳・丹沢'
    desc = 'ダイヤモンド富士はいつ・どこで見える？東京・神奈川・山梨・千葉の山頂から見られる日付と時間を、高尾山・竜ヶ岳・丹沢（塔ノ岳）・石割山・七面山・大野山・鋸山など厳選%d山で計算。冬（12〜2月）の見える山、2026-2027年のカレンダー、登山コース・駐車場つき。' % len(L)
    return page('diamond-fuji', title, desc, 'ダイヤモンド富士が見える場所・山<br>2026-2027年の日付と時間（カレンダー）', '冬の特集',
                ['ダイヤモンド富士', '📍 関東', '計算'], body, faq, 'ダイヤモンド富士が見える山', photos)


# ---------------------------------------------------------------- 冬にしか見られない景色
def winter_gear(m):
    cal = m.get('gearCalendar') or []
    parts = []
    for mo in (12, 1, 2):
        v = cal[mo - 1] if len(cal) >= mo else None
        if isinstance(v, dict):
            txt = '%s→%d日から%s' % (gear_calendar.LABEL[v['before']], v['changeDate'], gear_calendar.LABEL[v['after']])
        else:
            txt = gear_calendar.LABEL.get(v, '—')
        parts.append((mo, txt))
    if len(set(p[1] for p in parts)) == 1:
        return '12〜2月：' + parts[0][1]
    return '・'.join('%d月：%s' % p for p in parts)


def views(M, SC, W):
    V = W['views']
    cards, toc, comp, easy = [], [], [], []
    for i, it in enumerate(V['mountains']):
        m = M[it['id']]
        n = NUM[i]
        toc.append('<li style="margin:3px 0"><a href="#m-%s" style="color:#4a6038">%s %s（%s）</a></li>' % (m['id'], n, esc(m['name']), esc(it['what'])))
        r0 = (m.get('routes') or [{}])[0]
        drive = m.get('driveTimeShinjuku') or m.get('driveShinjuku')
        train = m.get('trainTimeShinjuku')
        src = it['url']
        src_a = ('<a href="%s" style="color:#4a6038">%s</a>' % (esc(src), esc(it['source'])) if src.startswith('/') else
                 '<a href="%s" target="_blank" rel="noopener" style="color:#4a6038">%s</a>' % (esc(src), esc(it['source'])))
        body = ''.join([
            row('冬の見どころ', '<strong>%s</strong>' % esc(it['what'])),
            row('見られる場所', esc(it['where'])),
            row('時期', esc(it['season'])),
            row('冬の装備', esc(winter_gear(m))),
            row('代表コース', '%s（%s・難易度 %s）' % (esc(r0.get('name') or ''), esc(r0.get('time') or ''), esc(m.get('difficulty') or ''))),
            row('行き方', esc(it['access'])) if it.get('access') else
            row('新宿から', '電車 約%s・車 約%s' % (dur(train) or '—', dur(drive) or '—') if train else '車 約%s' % (dur(drive) or '—')),
        ])
        cards.append(
            '<div class="mountain-card" id="m-%s">\n  <div class="mountain-card-header" data-mountain-id="%s">\n'
            '    <h2 class="mountain-card-title" style="margin:0;padding:0;border:none;font-size:18px;line-height:1.4">%s %s（%s）</h2>\n'
            '    <div class="mountain-card-sub">%s・標高%sm</div>\n  </div>\n  %s\n  <div class="mountain-card-body">\n'
            '    <p style="margin-bottom:10px">%s</p>\n    %s\n'
            '    <p class="ws-src">出典：%s</p>%s\n'
            '    <p style="margin-top:10px"><a href="/mountains/%s/" style="color:#4a6038;font-weight:700">%sの登山ガイド（装備カレンダー）を見る →</a></p>\n  </div>\n</div>' % (
                m['id'], m['id'], n, esc(m['name']), esc(it['what']), esc(m.get('prefecture') or m.get('area') or ''), '{:,}'.format(int(m['elevation'])),
                photo(m, W, 'views') + closed(m), esc(it['text']), body, src_a,
                ('<div class="ws-note">%s</div>' % esc(it['note'])) if it.get('note') else '', m['id'], esc(m['name'])))
        lifts = it.get('lift') or '・'.join(l['method']['line'] for l in (((m.get('trainRoutes') or {}).get('routes') or {}).get('shinjuku') or {}).get('legs') or []
                                            if (l.get('method') or {}).get('icon') == 'ropeway')
        easy.append((0 if m.get('difficulty') == '初級' else 1, ['<a href="#m-%s" style="color:#4a6038;font-weight:700">%s</a>' % (m['id'], esc(m['name'])),
                     esc(m.get('difficulty') or ''), esc(winter_gear(m)), esc(lifts or '—'),
                     # 蔵王は樹氷を見る場所（山形県側のロープウェイ）と山のページの代表コース（宮城県側）が別なので、コースの時間を出さない
                     '樹氷の場所へはロープウェイで（登山のコースとは別）' if it.get('lift') else
                     esc('日帰り可（代表コース%s）' % (r0.get('time') or '')) if m.get('daytrip') else '山小屋泊']))
        comp.append(['<a href="#m-%s" style="color:#4a6038;font-weight:700">%s %s</a>' % (m['id'], n, esc(m['name'])), esc(it['what']),
                     esc(winter_gear(m)), esc(m.get('difficulty') or ''), ('約' + dur(train)) if (train and not it.get('access')) else '—'])
    toc_html = ('<nav class="tips-card" id="toc" aria-label="目次" style="padding:16px 20px"><div style="font-weight:700;color:#2a3e2a;margin-bottom:6px">目次</div>'
                '<ul style="margin:0;padding:0;list-style:none;font-size:14px;line-height:1.7"><li style="margin:3px 0"><a href="#beginner" style="color:#4a6038">雪山初心者・日帰りで行ける冬の絶景の山</a></li>%s<li style="margin:3px 0"><a href="#compare" style="color:#4a6038">%d山の比較表</a></li>'
                '<li style="margin:3px 0"><a href="#tips" style="color:#4a6038">雪と氷の山に行く前に</a></li><li style="margin:3px 0"><a href="#faq" style="color:#4a6038">よくある質問</a></li></ul></nav>') % (''.join(toc), len(cards))
    body = '\n'.join([
        '<div class="info-note">⚠️ 雪と氷の山です。冬の装備（軽アイゼン等・冬山装備）は、山ごとの装備カレンダーで確かめてください。<a href="/articles/winter-no-crampons/" style="color:#5a4a10;font-weight:700">雪のない冬の山はこちら</a></div>',
        '<div class="lead-box">樹氷、霧氷、銀世界の湿原、凍った湖。冬にしか見られない景色に会える山を、Yamatch に載っている山から選びました。'
        'ロープウェイやゴンドラで高いところまで上がれる山もあり、雪山を始める人にも向いています。</div>',
        toc_html,
        '<h2 id="beginner">雪山初心者・日帰りで行ける冬の絶景の山</h2>',
        '<p style="margin:0 0 10px">ロープウェイやゴンドラで高いところまで上がれる山は、雪山を始める人に向いています。難易度の低い順です。'
        '装備の「軽アイゼン等」はチェーンスパイク・6本爪アイゼンなど、「冬山装備」は12本爪アイゼン・ピッケルなどのことです。</p>',
        table(['山', '難易度', '冬の装備（12〜2月）', '上がれる乗り物', '日帰り'], [r for _, r in sorted(easy, key=lambda t: t[0])]),
        '<h2>関東近郊で冬の絶景が見られる山%d選（樹氷・霧氷・雪原・氷）</h2>' % len(cards),
        '\n'.join(cards),
        '<h2 id="compare">%d山の比較表</h2>' % len(cards),
        table(['山', '冬の見どころ', '冬の装備', '難易度', '新宿から電車'], comp),
        '<h2 id="tips">雪と氷の山に行く前に</h2>',
        '<div class="tips-card" style="padding:16px 20px"><ul style="margin:0 0 0 18px;line-height:1.9">'
        '<li>装備は山ごとの装備カレンダーで確かめましょう。「軽アイゼン等」の月はチェーンスパイク・6本爪アイゼンなど、「冬山装備」の月は12本爪アイゼン・ピッケル・冬用の登山靴などが要ります</li>'
        '<li>ロープウェイ・ゴンドラは、冬の運行期間・点検の運休・強風の運休があります。出かける前に運行会社の案内を確かめましょう</li>'
        '<li>冬至のころ、東京の日の入りは' + sun_calc.hm(sun_calc.sunrise_sunset(35.6581, 139.7414, datetime.date(2026, 12, 22))[1]) + 'ごろです（計算）。早めに歩き始め、ヘッドランプを持っていきましょう</li>'
        '<li>樹氷・霧氷は気象条件で見られない日があります</li></ul></div>',
        '<h2>あわせて読みたい</h2>',
        '<div class="tips-card" style="padding:16px 20px"><ul style="margin:0 0 0 18px;line-height:1.9">'
        '<li><a href="/articles/winter-no-crampons/" style="color:#4a6038;font-weight:700">冬でも登れる関東の山7選｜雪なし・アイゼン不要</a></li>'
        '<li><a href="/articles/diamond-fuji/" style="color:#4a6038;font-weight:700">ダイヤモンド富士が見える山（日付と時刻）</a></li>'
        '' + hatsu_li(W) + '</ul></div>',
    ])
    vz = {it['id']: it for it in V['mountains']}
    faq = [
        ('樹氷と霧氷の違いは何ですか？',
         '気象の用語では、霧氷は、空気中の冷たい水滴などが木の枝に凍りついてできる氷をまとめた呼び方で、樹氷はその一つです。蔵王の「スノーモンスター」は、樹氷に雪が積もって大きく育ったものです。'),
        ('雪山初心者におすすめの関東近郊の山はどこですか？',
         'この記事では、難易度が初級の%sです。ロープウェイやゴンドラで高いところまで上がれます。冬の装備は、%s。' % (
             '・'.join(M[i]['name'] for i in vz if M[i].get('difficulty') == '初級'),
             '、'.join('%sは%s' % (M[i]['name'], winter_gear(M[i]).replace('12〜2月：', '12〜2月は')) for i in vz if M[i].get('difficulty') == '初級'))),
        ('日帰りで行ける雪山・冬の絶景の山はありますか？',
         '%sは日帰りで歩けるコースがあります（代表コース：%s）。蔵王山の樹氷は、山形県側の蔵王ロープウェイで見に行けます。冬は日が短いので、早めに歩き始めましょう。' % (
             '・'.join(M[i]['name'] for i in vz if M[i].get('daytrip') and not vz[i].get('lift')),
             '、'.join('%s %s' % (M[i]['name'], (M[i].get('routes') or [{}])[0].get('time') or '') for i in vz if M[i].get('daytrip') and not vz[i].get('lift')))),
        ('蔵王の樹氷の見頃・時期はいつですか？',
         '%s。%s' % (vz['zaosan']['season'], vz['zaosan']['text'].split('。')[0] + '。')),
        ('蔵王の樹氷への行き方は？',
         vz['zaosan']['access'] + '。'),
        ('北横岳・入笠山・赤城山の冬の装備は？チェーンスパイクで行けますか？',
         '装備カレンダーでは、%s。「軽アイゼン等」はチェーンスパイク・6本爪アイゼンなど、「冬山装備」は12本爪アイゼン・ピッケルなどです。' % (
             '、'.join('%sは%s' % (M[i]['name'], winter_gear(M[i]).replace('12〜2月：', '12〜2月が')) for i in ('kitayokodake', 'nyukasayama', 'akagi')))),
        ('スノーシューで歩ける関東近郊の山はありますか？',
         '入笠山です。ゴンドラで山頂エリアまで上がり、スノーシューで雪原を歩けます（富士見パノラマリゾートの発表）。'),
        ('関東から行ける樹氷の山はどこですか？',
         'この記事では、蔵王山（蔵王ロープウェイ地蔵山頂駅のあたり。例年12月下旬〜2月中旬ごろ）と、西吾妻山（天元台から続く稜線の樹氷原）を紹介しています。'),
        ('雪山が初めてでも行ける冬の絶景の山はありますか？',
         'ロープウェイやゴンドラで高いところまで上がれる入笠山・北横岳などがあります。装備は山ごとの装備カレンダーで確かめ、冬山装備の月は経験者と一緒に行きましょう。'),
        ('霧氷が見られる関東の山はどこですか？',
         'この記事では大菩薩嶺（冬は霧氷）を紹介しています。霧氷は気象条件で見られない日があります。'),
    ]
    photos = 'hero_winter_views.jpg'
    names = '・'.join(M[it['id']]['name'] for it in V['mountains'])
    title = '冬の絶景が見られる山%d選【関東近郊】樹氷・霧氷・雪山へ日帰りで｜初心者向けロープウェイの山も' % len(cards)
    desc = '関東近郊で樹氷・霧氷・雪原・凍った湖など、冬にしか見られない絶景の山%d選（%s）。雪山初心者向けのロープウェイ・ゴンドラの山、日帰りのコース、冬の装備（チェーンスパイク・アイゼン）、蔵王の樹氷の見頃と行き方つき。' % (len(cards), names)
    return page('winter-views', title, desc, '冬の絶景が見られる山%d選【関東近郊】<br>樹氷・霧氷・雪山へ日帰りで' % len(cards), '冬の特集',
                ['冬季', '📍 関東近郊', '樹氷・霧氷'], body, faq, '冬にしか見られない絶景の山', photos)


def main():
    M, SC, W = load()
    pages = {'hatsuhinode-hiking': hatsuhinode(M, SC, W), 'diamond-fuji': diamond(M, SC, W), 'winter-views': views(M, SC, W)}
    check = '--check' in sys.argv
    bad = 0
    for slug, s in pages.items():
        p = os.path.join(ROOT, 'articles', slug, 'index.html')
        old = open(p, encoding='utf-8').read() if os.path.exists(p) else None
        if check:
            if old != s:
                print('違う：', p)
                bad += 1
            continue
        if old != s:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'w', encoding='utf-8').write(s)
            print('書きました', os.path.relpath(p, ROOT))
        else:
            print('変わらない', os.path.relpath(p, ROOT))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
