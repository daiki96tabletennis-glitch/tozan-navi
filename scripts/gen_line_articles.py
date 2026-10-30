#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""路線別の登山記事（search/<slug>/）を data/line_articles.json と data/mountains.json から作る（2026-10-30〜）。

- 時間・距離・累積標高差・コース定数・難易度・新宿からの電車とバスの時間・運賃・閉鎖は mountains.json から読む
  （前は手書きで、山のデータを直しても記事が古いままだった）
- 分け方・山ごとの「選ぶ理由」・使うコース・よくある質問は line_articles.json に書く
- 装備欄（アフィリエイト）は前の記事と同じ形のまま（gear-data.json の月ごとの中身を data-gear-variants に入れる）
- 写真は前の記事と同じく、ページの中のスクリプトが mountains.json の photos から入れる
- <head> の CSS・解析タグと、ページ下の装備・写真のスクリプトは、いまのページから引き継ぐ（その部分は手で直してよい）

  python3 scripts/gen_line_articles.py odakyu-hiking
  python3 scripts/gen_line_articles.py --all
"""
import argparse
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = '<!-- generated: scripts/gen_line_articles.py（手で編集しない。data/line_articles.json を直して作り直す） -->'
TODAY = None

E = html.escape


def load(p):
    return json.load(open(os.path.join(ROOT, p), encoding='utf-8'))


def hm(minutes):
    h, m = divmod(int(minutes), 60)
    if not h:
        return '%d分' % m
    return '%d時間%d分' % (h, m) if m else '%d時間' % h


def yen(v):
    return '{:,}円'.format(int(v))


def legs_until(legs, until):
    if not until:
        return legs
    out = []
    for x in legs:
        out.append(x)
        if x['station'] == until:
            out[-1] = {'station': x['station']}
            return out
    raise SystemExit('accessUntil の駅が経路にありません：' + until)


def only_walk_dropped(full, cut):
    """accessUntil で切った先が徒歩だけなら、運賃は全体と同じ"""
    dropped = full[len(cut) - 1:]
    return all('徒歩' in ((x.get('method') or {}).get('line') or '') for x in dropped if x.get('method'))


def access_html(m, item):
    full = m['trainRoutes']['routes']['shinjuku']['legs']
    legs = legs_until(full, item.get('accessUntil'))
    parts = []
    total = 0
    for x in legs:
        parts.append('<span class="la-st">%s</span>' % E(x['station']))
        meth = x.get('method')
        if meth:
            d = x.get('durationMin') or 0
            total += d
            parts.append('<span class="la-mv">%s %s</span>' % (E(meth.get('line') or ''), hm(d)))
    line = '<span class="la-ar">→</span>'.join(parts)
    fare = m.get('fareShinjuku')
    head = '新宿から約%s' % hm(total)
    whole = not item.get('accessUntil') or only_walk_dropped(full, legs)
    if fare and whole:
        head += '・%s' % yen(fare)
    note = ''
    sn = (m['trainRoutes'].get('summaryNote') or '').strip()
    if sn and whole:
        note += '<p class="la-anote">%s</p>' % E(sn.lstrip('※ '))
    if item.get('accessNote'):
        note += '<p class="la-anote">%s</p>' % E(item['accessNote'])
    return ('<div class="la-access"><div class="la-h">行き方<span class="la-sum">%s（乗り換えの待ち時間を除く）</span></div>'
            '<div class="la-legs">%s</div>%s</div>%s') % (head, line, note, alt_access_html(item.get('altAccess')))


def alt_access_html(alt):
    """山のデータに無い別の行き方（記事のために公式の経路検索などで確かめたもの。出典・確認日つき）"""
    if not alt:
        return ''
    parts, total = [], 0
    for x in alt['legs']:
        parts.append('<span class="la-st">%s</span>' % E(x['station']))
        if x.get('line'):
            total += x['min']
            parts.append('<span class="la-mv">%s %s</span>' % (E(x['line']), hm(x['min'])))
    src = '・'.join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(u), E(t)) for t, u in alt.get('sources') or [])
    return ('<div class="la-access la-alt-access"><div class="la-h">%s<span class="la-sum">新宿から約%s・%s（%s）</span></div>'
            '<div class="la-legs">%s</div><p class="la-anote">%s</p><p class="la-src">出典：%s（%s 確認）</p></div>'
            % (E(alt['title']), hm(total), yen(alt['fare']), E(alt.get('fareNote') or ''),
               '<span class="la-ar">→</span>'.join(parts), E(alt.get('note') or ''), src, E(alt.get('checked') or '')))


def route_row(r, cls=''):
    cells = [r.get('time') or '—', r.get('distance') or '—',
             ('+' + str(r['elevation']).lstrip('+').replace('m', '') + 'm') if r.get('elevation') else '—']
    return ('<tr%s><th>%s</th><td>%s</td><td>%s</td><td>%s</td></tr>'
            % (cls, E(r.get('name') or ''), E(cells[0]), E(cells[1]), E(cells[2])))


def course_html(m, item):
    routes = m.get('routes') or []
    r = routes[item.get('route', 0)]
    rows = [route_row(r)]
    for i in item.get('alt') or []:
        rows.append(route_row(routes[i], ' class="la-alt"'))
    src = r.get('source')
    return ('<div class="la-course"><div class="la-h">コース</div><table><thead><tr><th>コース</th><th>歩く時間</th><th>距離</th><th>登り</th></tr></thead>'
            '<tbody>%s</tbody></table>%s</div>') % (''.join(rows), '<p class="la-src">時間・距離・登り（累積標高差）の出典：%s</p>' % E(src) if src else '')


def cautions(m, n=2):
    lis = re.findall(r'<li class="minus">(.*?)</li>', m.get('dlReasonsHtml') or '', re.S)
    out = [re.sub(r'<[^>]+>', '', x).strip() for x in lis][:n]
    if not out:
        return ''
    return '<div class="la-caut"><div class="la-h">気をつけたいこと</div><ul>%s</ul></div>' % ''.join('<li>%s</li>' % E(x) for x in out)


def gear_block(m, gear):
    md = gear.get(m['id'])
    if not md:
        return ''
    groups, order = {}, []
    for month in sorted(md.keys(), key=int):
        key = json.dumps(md[month], ensure_ascii=False)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(int(month))
    attr = json.dumps({k: groups[k] for k in order}, ensure_ascii=False).replace('"', '&quot;')
    return ('<div class="gear-section-label"><img src="/images/icons/backpack.webp" width="18" height="18" alt="" '
            'style="vertical-align:-4px;margin-right:2px">%sの装備</div><div class="gear-cards-scroll" data-gear-mid="%s" '
            'data-gear-variants="%s"></div>') % (E(m['name']), m['id'], attr)


def closed_html(m):
    st = m.get('status') or {}
    if st.get('level') == 'caution':
        link = (' <a href="%s" target="_blank" rel="noopener">出典</a>' % E(st['sourceUrl'])) if st.get('sourceUrl') else ''
        return '<div class="mc-caution"><b>注意</b>：%s%s</div>' % (E(st.get('summary') or ''), link)
    if st.get('level') != 'restricted':
        return ''
    return ('<div class="mc-closed" data-closed="%s"><b>規制中</b>：%s <a href="%s" target="_blank" rel="noopener">出典</a></div>'
            % (m['id'], E(st.get('summary') or ''), E(st.get('sourceUrl') or '')))


def card(m, item, cfg, gear):
    badges = ['<span class="sb sb-diff">%s</span>' % E(m.get('difficulty') or '')]
    if m.get('category') and m['category'] != '人気の山':
        badges.append('<span class="sb sb-cat">%s</span>' % E(m['category']))
    badges.append('<span class="sb sb-day">%s</span>' % ('日帰り可' if m.get('daytrip') else '山小屋泊が基本'))
    r = (m.get('routes') or [])[item.get('route', 0)]
    if r.get('coeff'):
        badges.append('<span class="sb sb-co">このコースの定数 %s</span>' % r['coeff'])
    return (
        '<div class="mountain-card" data-mountain-id="%(id)s">\n  <div class="mc-body">\n'
        '    <div class="mc-head"><h3 class="mc-name"><a href="/mountains/%(id)s/">%(name)s</a></h3>'
        '<div class="mc-area">%(area)s · 標高%(elev)sm</div></div>\n'
        '    %(closed)s<div class="mc-badges">%(badges)s</div>\n'
        '    <p class="la-why">%(why)s</p>\n    %(course)s\n    %(access)s\n    %(caut)s\n'
        '    <a href="/mountains/%(id)s/" class="mc-link" style="background:%(color)s;">%(name)sのページで詳しく見る →</a>%(gear)s\n'
        '  </div>\n</div>\n'
    ) % {'id': m['id'], 'name': E(m['name']), 'area': E(m.get('area') or ''), 'elev': '{:,}'.format(m['elevation']),
         'closed': closed_html(m), 'badges': ''.join(badges), 'why': E(item['why']),
         'course': course_html(m, item), 'access': access_html(m, item), 'caut': cautions(m),
         'color': cfg['color'], 'gear': gear_block(m, gear)}


def fill(text, by):
    """よくある質問の {time:山ID} などを山のデータの値にする"""
    def rep(mm):
        kind, mid = mm.group(1), mm.group(2)
        m = by[mid]
        r = (m.get('routes') or [{}])[0]
        if kind == 'time':
            return r.get('time') or ''
        if kind == 'dist':
            return r.get('distance') or ''
        if kind == 'up':
            return '+%sm' % str(r.get('elevation')).lstrip('+').replace('m', '')
        if kind == 'train':
            return hm(m['trainTimeShinjuku'])
        if kind == 'fare':
            return yen(m['fareShinjuku'])
        if kind == 'status':
            st = m.get('status') or {}
            return 'いまは閉鎖中' if st.get('level') == 'restricted' else '通年で歩ける'
        raise SystemExit('不明な差し込み：' + mm.group(0))
    return re.sub(r'\{(time|dist|up|train|fare|status):([a-z0-9_]+)\}', rep, text)


CSS = '''<style id="la-css">
.la-choose{display:grid;gap:8px;margin-top:12px}
.la-choose a{display:block;text-decoration:none;border-radius:10px;padding:10px 12px;color:#3a3530;font-size:13px;line-height:1.6;border:1px solid #e0dbd4}
.la-choose b{display:block;font-size:14px}
.la-sec{margin:22px 0 10px}
.la-sec h2{font-size:18px;font-weight:800;line-height:1.4;padding-left:10px;border-left-width:4px;border-left-style:solid}
.la-sec p{font-size:13px;color:#5a5248;line-height:1.8;margin-top:6px}
.sb-diff{background:#e6eef8;color:#1a4a70}.sb-co{background:#f3efe6;color:#6a5a40}
.la-why{font-size:14px;line-height:1.85;color:#3a3530;margin:4px 0 10px}
.la-h{font-size:12px;font-weight:700;color:#6a6058;margin-bottom:4px}
.la-sum{font-weight:600;color:#1a3050;margin-left:8px}
.la-course,.la-access,.la-caut{margin:10px 0}
.la-course table{width:100%;border-collapse:collapse;font-size:12.5px}
.la-course th,.la-course td{border-bottom:1px solid #eee9e0;padding:6px 4px;text-align:left;vertical-align:top}
.la-course thead th{font-size:11px;color:#9a9088;font-weight:600}
.la-course tbody th{font-weight:600;color:#3a3530;width:46%}
.la-course td{white-space:nowrap;color:#1a3050;font-weight:700}
.la-course .la-alt th,.la-course .la-alt td{color:#7a7068;font-weight:500}
.la-src,.la-anote{font-size:11.5px;color:#8a8078;line-height:1.7;margin-top:4px}
.la-src a{color:#8a8078}
.la-alt-access .la-legs{background:#f1f6ec;color:#3a5a28}
.la-legs{font-size:12.5px;line-height:1.9;background:#eef4fb;border-radius:8px;padding:6px 10px;color:#1a4a70}
.la-st{font-weight:700}.la-mv{font-size:11.5px;color:#4a6a88}.la-ar{margin:0 5px;color:#8aa0b8}
.la-caut ul{font-size:12.5px;line-height:1.8;color:#5a4a3a;padding-left:18px}
.mc-closed{margin:6px 0 8px;padding:8px 10px;background:#fdecea;border-left:3px solid #c0392b;border-radius:6px;font-size:12.5px;line-height:1.6;color:#7a1f14}
.mc-closed a{color:#7a1f14}
.mc-caution{margin:6px 0 8px;padding:8px 10px;background:#fff6e0;border-left:3px solid #d99a00;border-radius:6px;font-size:12.5px;line-height:1.6;color:#6a4a00}
</style>'''


def build(slug, cfg, by, gear, pages_dir):
    path = os.path.join(pages_dir, slug, 'index.html')
    src = open(path, encoding='utf-8').read()
    color, tint = cfg['color'], cfg['tint']
    url = 'https://tozan-navi.com/search/%s/' % slug
    ids = [it['id'] for s in cfg['sections'] for it in s['items']]
    n = len(ids)

    # ---- head ----
    def sub1(pat, rep, s, flags=0):
        out, c = re.subn(pat, lambda _m: rep, s, count=1, flags=flags)
        if c != 1:
            raise SystemExit('%s: 置き換え先が見つかりません：%s' % (slug, pat))
        return out
    s = src
    s = sub1(r'<title>.*?</title>', '<title>%s</title>' % E(cfg['metaTitle']), s, re.S)
    s = sub1(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % E(cfg['description']), s)
    s = sub1(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="%s">' % E(cfg['title']), s)
    s = sub1(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="%s">' % E(cfg['description']), s)
    s = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', '', s, flags=re.S)
    s = re.sub(r'<style id="la-css">.*?</style>\n?', '', s, flags=re.S)
    s = re.sub(r'<!-- generated: scripts/gen_line_articles\.py[^>]*-->\n?', '', s)
    faq = [(q['q'], fill(q['a'], by)) for q in cfg['faq']]
    ld = [
        {'@context': 'https://schema.org', '@type': 'Article', 'headline': cfg['title'], 'description': cfg['description'],
         'dateModified': TODAY, 'author': {'@type': 'Organization', 'name': 'Yamatch', 'url': 'https://tozan-navi.com/'}},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Yamatch', 'item': 'https://tozan-navi.com/'},
            {'@type': 'ListItem', 'position': 2, 'name': cfg['title'], 'item': url}]},
        {'@context': 'https://schema.org', '@type': 'ItemList', 'name': cfg['title'], 'numberOfItems': n, 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': by[mid]['name'], 'url': 'https://tozan-navi.com/mountains/%s/' % mid}
            for i, mid in enumerate(ids)]},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]},
    ]
    head_add = MARK + '\n' + ''.join('<script type="application/ld+json">%s</script>\n' % json.dumps(x, ensure_ascii=False) for x in ld) + CSS + '\n'
    s, c = re.subn(r'(<link rel="canonical" href="[^"]*">\n)', lambda mm: mm.group(1) + head_add, s, count=1)
    if c != 1:
        raise SystemExit(slug + ': canonical がありません')

    # ---- main ----
    choose = ''.join('<a href="%s" style="background:%s"><b>%s</b>%s</a>' % (E(c['href']), tint, E(c['label']), E(c['text'])) for c in cfg['choose'])
    secs = []
    for sec in cfg['sections']:
        cards = ''.join(card(by[it['id']], it, cfg, gear) for it in sec['items'])
        secs.append('<div class="la-sec" id="%s"><h2 style="border-left-color:%s">%s</h2><p>%s</p></div>\n%s'
                    % (sec['id'], color, E(sec['title']), E(sec['lead']), cards))
    faq_html = ''.join('    <div class="faq-item">\n      <h3 class="faq-q" style="color:%s;">%s</h3>\n      <div class="faq-a"><p>%s</p></div>\n    </div>\n'
                       % (color, E(q), E(a)) for q, a in faq)
    rel = ''.join('    <a href="%s" class="il-link" style="color:%s;">→ %s</a>\n' % (E(h), color, E(t)) for h, t in cfg['related'])
    main = (
        '<main>\n  <div class="page-head" style="border-top:4px solid %(c)s;">\n'
        '    <div class="page-kw" style="color:%(c)s;">%(kw)s</div>\n    <h1>%(h1)s</h1>\n'
        '    <div class="page-intro">%(lead)s</div>\n    <div class="la-choose">%(choose)s</div>\n'
        '    <p class="page-count">全%(n)d山 · 数字は山のデータと同じ値（%(today)s 更新）</p>\n  </div>\n'
        '%(secs)s'
        '  <div class="cta-banner" style="background:linear-gradient(135deg,%(c)s,%(c)saa);">\n'
        '    <div class="cta-title">自分に合う山を診断</div>\n    <div class="cta-sub">12問・約2分。16タイプのどれかと、そのタイプに合う山がわかる</div>\n'
        '    <a href="/recommend/?start=1" class="cta-btn" style="color:%(c)s;">無料で診断する →</a>\n  </div>\n'
        '  <div class="faq-section">\n    <h2 style="border-bottom-color:%(c)s;">よくある質問</h2>\n%(faq)s  </div>\n'
        '  <div class="internal-links">\n    <div class="il-title">関連するまとめ</div>\n%(rel)s  </div>\n</main>'
    ) % {'c': color, 'kw': E(cfg['kw']), 'h1': E(cfg['title']), 'lead': E(cfg['lead']), 'choose': choose, 'n': n,
         'today': TODAY, 'secs': ''.join(secs), 'faq': faq_html, 'rel': rel}
    s = sub1(r'<main>.*?</main>', main, s, re.S)
    # 「新宿から約◯分」を書き換える前の仕組みは使わない（カードに mc-train が無い）
    s = re.sub(r'<script>\n\(function\(\)\{\n  // \.mc-train内の「新宿から約◯分」.*?</script>\n', '', s, flags=re.S)
    if not s.rstrip().endswith('</html>'):
        raise SystemExit(slug + ': </html> で終わっていません')
    if s.count('<div') != s.count('</div>'):
        raise SystemExit('%s: div の開閉が合いません（%d / %d）' % (slug, s.count('<div'), s.count('</div>')))
    return path, s


def main():
    global TODAY
    import datetime
    TODAY = datetime.date.today().isoformat()
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    cfgs = load('data/line_articles.json')
    by = {m['id']: m for m in load('data/mountains.json')}
    gear = load('data/gear-data.json')
    slugs = [k for k in cfgs if not k.startswith('_')] if a.all else a.slugs
    if not slugs:
        ap.error('記事の slug か --all を指定してください')
    for slug in slugs:
        path, s = build(slug, cfgs[slug], by, gear, os.path.join(ROOT, 'search'))
        if a.dry_run:
            print(slug, len(s), '（書き込まない）')
            continue
        open(path, 'w', encoding='utf-8').write(s)
        print(slug, '書きました', path)


if __name__ == '__main__':
    main()
