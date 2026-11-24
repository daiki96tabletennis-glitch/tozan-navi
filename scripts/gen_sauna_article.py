#!/usr/bin/env python3
"""まとめ記事「サウナシュラン受賞サウナに寄れる山」（/articles/saunachelin-hiking/）を作る（2026-11-16。運営者の指示）

- 中身：data/saunachelin_hiking.json（受賞年・日帰り利用・位置・山と車の時間）と mountains.json（コース・難易度・地図ボタンの行き先）
- 地図：assets/js/sauna-map.js（Leaflet＋地理院タイル）。サウナと、山の登山口・駐車場（地図ボタンの行き先）を点線で結ぶ
- 見た目は冬の特集記事の部品（gen_winter_specials.py）。手で編集しない
  python3 scripts/gen_sauna_article.py          書く
  python3 scripts/gen_sauna_article.py --check  同じかを見る
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gen_winter_specials as W  # noqa: E402
import ym_icons  # noqa: E402

SLUG = 'saunachelin-hiking'
UPDATED = '2026-11-16'
BANNER = 'hero_saunachelin_hiking.jpg?v=20261116b'
esc = W.esc
CSS_EXTRA = ('<style>'
             '.smap{height:300px;border-radius:12px;margin:10px 0 4px;background:#e8e4da;z-index:0}'
             '.smap-all{height:360px}'
             '.smap-tip{font-size:12px;font-weight:700;padding:2px 6px}'
             '.sc-award{display:inline-block;background:#fff4e8;color:#a0522d;border:1px solid #f0d2b4;font-size:12px;font-weight:700;border-radius:12px;padding:2px 10px;margin:0 6px 4px 0}'
             '.sc-legend{font-size:12px;color:#666;margin:0 0 8px}'
             '.sc-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin:0 4px 0 8px;vertical-align:-1px}'
             '.sc-mt{border-top:1px solid #eee9e0;padding:8px 0}.sc-mt:first-child{border-top:0}'
             '.sc-mt b a{color:#4a6038}'
             '.sc-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}'
             '.sc-links a{display:inline-flex;align-items:center;gap:5px;background:#f3f0e8;border:1px solid #e3ddcf;color:#3a5a28;font-weight:700;font-size:13px;border-radius:10px;padding:7px 12px;text-decoration:none}'
             '.sc-plan{display:inline-block;background:#f3efe4;color:#5a4a2a;font-weight:700;font-size:12px;border-radius:8px;padding:1px 8px;margin-left:6px}.sc-time{display:inline-block;background:#eef4fb;color:#1a4a70;font-weight:700;font-size:12.5px;border-radius:8px;padding:1px 8px;margin-left:6px}'
             '</style>')


def links(s):
    """公式サイト・案内のページ・地図（Google マップ。施設の座標で開く）。運営者の指示・2026-11-16"""
    out = ['<a href="%s" target="_blank" rel="noopener">%s 公式サイト</a>' % (esc(s['home']), ym_icons.svg('link', style=ym_icons.ICON_STYLE))]
    if s.get('urlLabel') and s['url'] != s['home']:
        out.append('<a href="%s" target="_blank" rel="noopener">%s %s</a>' % (esc(s['url']), ym_icons.svg('clipboard-list', style=ym_icons.ICON_STYLE), esc(s['urlLabel'])))
    out.append('<a href="https://www.google.com/maps/search/?api=1&amp;query=%.6f%%2C%.6f" target="_blank" rel="noopener">%s 地図で見る（Google マップ）</a>' % (
        s['lat'], s['lng'], ym_icons.svg('map-pin', style=ym_icons.ICON_STYLE)))
    return ''.join(out)


def gm(m):
    g = re.search(r'(?:destination=|query=|q=|@)(-?\d+\.\d+)(?:,|%2C)(-?\d+\.\d+)', m.get('gmapUrl') or '')
    return float(g.group(1)), float(g.group(2))


def build():
    D = json.load(open(os.path.join(ROOT, 'data', 'saunachelin_hiking.json'), encoding='utf-8'))
    M = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
    cards, rows, allmap, toc = [], [], [], []
    for n, s in enumerate(D['saunas'], 1):
        mpts, mts = [], []
        for x in s['mountains']:
            m = M[x['id']]
            r = m['routes'][0]
            if x.get('lat'):
                la, lo, frm = x['lat'], x['lng'], x['from']
            else:
                la, lo = gm(m)
                frm = '登山口・駐車場（地図の行き先）'
            how = x.get('walk') or '車で約%d分' % x['car']
            mpts.append({'n': m['name'], 'la': la, 'lo': lo, 't': how})
            plan, pnote = trip_plan(m, r, x)
            mts.append('<div class="sc-mt"><b><a href="/mountains/%s/">%s</a></b><span class="sc-time">%s</span><span class="sc-plan">%s</span><br>'
                       '<span style="font-size:13px;color:#555">%sから。代表コース：%s（%s・難易度 %s）%s</span></div>' % (
                           m['id'], esc(m['name']), esc(how), esc(plan), esc(frm), esc(r['name']), esc(r['time']), esc(m.get('difficulty') or ''), esc(pnote)))
            rows.append(['<a href="#s-%s" style="color:#4a6038;font-weight:700">%s</a>' % (s['key'], esc(m['name'])),
                         esc(s['name']), esc(how), esc('・'.join(s['awards']))])
        pt = {'s': {'n': s['name'], 'la': s['lat'], 'lo': s['lng']}, 'm': mpts}
        allmap.append(pt)
        toc.append('<li style="margin:3px 0"><a href="#s-%s" style="color:#4a6038">%d. %s</a></li>' % (s['key'], n, esc(s['name'])))
        cards.append(
            '<div class="mountain-card" id="s-%s">\n  <div class="mountain-card-header">\n'
            '    <h2 class="mountain-card-title" style="margin:0;padding:0;border:none;font-size:18px;line-height:1.4">%d. %s</h2>\n'
            '    <div class="mountain-card-sub">%s・%s</div>\n  </div>\n  <div class="mountain-card-body">\n'
            '    <div>%s</div>\n    <p style="margin:6px 0 8px">%s</p>\n    %s%s\n'
            '    <div class="smap" data-smap="%s" role="img" aria-label="%sと近くの山の登山口の位置"></div>\n'
            '    <p class="sc-legend"><span class="sc-dot" style="background:#c8650a"></span>サウナ<span class="sc-dot" style="background:#4e6535"></span>山の登山口・駐車場（点線は直線で結んだもの。道のりではありません）</p>\n'
            '    <h3 style="font-size:15px;margin:12px 0 2px;color:#2a3e2a">近くの山</h3>\n    %s\n'
            '    <div class="sc-links">%s</div>\n  </div>\n</div>' % (
                s['key'], n, esc(s['name']), esc(s['area']), esc(s['kind']),
                ''.join('<span class="sc-award">サウナシュラン%s 受賞</span>' % esc(a) for a in s['awards']),
                esc(s['text']), W.row('日帰り利用', esc(s['dayuse'])), '',
                esc(json.dumps(pt, ensure_ascii=False, separators=(',', ':'))), esc(s['name']), ''.join(mts), links(s)))
    nm = len(rows)
    body = '\n'.join([
        '<div class="lead-box">「サウナシュラン」に選ばれたことのあるサウナのうち、Yamatch に載っている山の登山口から車で30分ほどで行けて、日帰りで使える%d施設を地図にまとめました。'
        '下山のあとに、全国から選ばれたサウナで整えてみませんか。</div>' % len(D['saunas']),
        '<nav class="tips-card" id="toc" aria-label="目次" style="padding:16px 20px"><div style="font-weight:700;color:#2a3e2a;margin-bottom:6px">目次</div>'
        '<ul style="margin:0;padding:0;list-style:none;font-size:14px;line-height:1.7"><li style="margin:3px 0"><a href="#map" style="color:#4a6038">地図で見る</a></li>'
        '<li style="margin:3px 0"><a href="#list" style="color:#4a6038">山とサウナの一覧</a></li>%s'
        '<li style="margin:3px 0"><a href="#about" style="color:#4a6038">選び方と注意</a></li><li style="margin:3px 0"><a href="#faq" style="color:#4a6038">よくある質問</a></li></ul></nav>' % ''.join(toc),
        '<h2 id="map">地図で見る</h2>',
        '<div class="smap smap-all" data-smap="%s" role="img" aria-label="サウナと近くの山の位置"></div>' % esc(json.dumps({'list': allmap}, ensure_ascii=False, separators=(',', ':'))),
        '<p class="sc-legend"><span class="sc-dot" style="background:#c8650a"></span>サウナ<span class="sc-dot" style="background:#4e6535"></span>山の登山口・駐車場（点にふれると名前が出ます）</p>',
        '<h2 id="list">山とサウナの一覧（%d山）</h2>' % nm,
        W.table(['山', 'サウナ', '登山口から', 'サウナシュラン'], rows),
        '<p style="font-size:12.5px;color:#666;margin:4px 0 16px">車の時間は、山の地図ボタンの行き先（駐車場・登山口）から、道路の経路検索（OpenStreetMap の道路データ）で求めた目安です。渋滞や冬の通行止めは含みません。山の横の印（日帰り向け・早朝出発・健脚向け・前泊・宿泊がおすすめ）は、新宿からの車の往復と代表コースの歩く時間、サウナの1時間を足した合計（12時間以内／15時間以内／それより長い）で分けた目安で、休憩や渋滞は入れていません。</p>',
        '\n'.join(cards),
        '<h2 id="about">選び方と注意</h2>',
        '<div class="tips-card" style="padding:16px 20px"><ul style="margin:0 0 0 18px;line-height:1.9">'
        '<li>サウナシュランは、毎年11月11日に「今行くべき全国のサウナ施設」として11施設が発表される賞です（<a href="%s" target="_blank" rel="noopener" style="color:#4a6038">サウナシュラン公式サイト</a>）。受賞年は公式サイトの各年のページによります</li>'
        '<li>選んだのは、日帰りで使えると公式サイトで確かめられた施設だけです。泊まる人だけのサウナ・会員制の施設・日帰りでサウナを使えるか確かめられない施設は入れていません</li>'
        '<li>予約制・水着で入る施設があります。料金・営業時間・予約は、出かける前に各施設の公式サイトで確かめてください</li>'
        '<li>登山のあとは汗で水分が足りなくなりがちです。水分をとり、体調が落ち着いてからサウナに入りましょう</li></ul></div>' % esc(D['chelinSource']),
        '<h2>あわせて読みたい</h2>',
        '<div class="tips-card" style="padding:16px 20px"><ul style="margin:0 0 0 18px;line-height:1.9">'
        '<li><a href="/articles/hiking-onsen-sauna/" style="color:#4a6038;font-weight:700">登山のあとの温泉・サウナが最高な山12選</a></li>'
        '<li><a href="/search/train-daytrip/" style="color:#4a6038;font-weight:700">電車で行ける日帰り登山20選</a></li></ul></div>',
        '<p style="font-size:12.5px;color:#777;margin-top:14px">※施設の情報は2026年11月16日に確かめたものです。地図：地理院タイル。</p>',
    ])
    S = {s['key']: s for s in D['saunas']}
    faq = [
        ('サウナシュランに選ばれたサウナで、登山のあとに寄れるのはどこですか？',
         'この記事では、%sの%d施設を紹介しています。どれも Yamatch に載っている山の登山口から車で30分ほど（鎌倉アルプスは鎌倉駅から徒歩3分）で、日帰りで使えます。' % ('・'.join(s['name'] for s in D['saunas']), len(D['saunas']))),
        ('殿堂入りのサウナに寄れる山はありますか？',
         'The Sauna（LAMP野尻湖）は、サウナシュランを2019年・2022年・2023年に受賞し、殿堂入りしています。妙高山・黒姫山の登山口から車で約15分です（目安）。'),
        ('電車で行く登山のあとに寄れるサウナシュランのサウナは？',
         '鎌倉アルプスのコースの終わりの鎌倉駅から、御成桑拿 Onari Sauna（2026年受賞）が徒歩3分です。'),
        ('富士山が見えるサウナはありますか？',
         'CYCL（2024年受賞）は、富士山と山中湖を望む湖畔のサウナです。石割山の登山口から車で約15分です（目安）。'),
    ]
    W.UPDATED = UPDATED
    title = 'サウナシュラン受賞サウナに寄れる山%d選｜登山口から車30分以内・日帰りOK【地図つき】' % nm
    page = W.page(SLUG, title,
                  'サウナシュランに選ばれたことのあるサウナのうち、登山口から車で30分ほどで行けて日帰りで使える%d施設と、近くの%d山を地図で紹介。受賞年・日帰り利用・車の時間の目安つき。' % (len(D['saunas']), nm),
                  'サウナシュラン受賞サウナに<br>寄れる山%d選' % nm, 'サウナ', ['地図つき', '日帰り'], body, faq, 'サウナシュラン受賞サウナに寄れる山', BANNER)
    page = page.replace('</head>', CSS_EXTRA + '\n</head>', 1)
    page = page.replace('<script src="/assets/js/card-photo-credits.js?v=20261124" defer></script>',
                        '<script src="/assets/js/sauna-map.js?v=20261116" defer></script>', 1)
    return ym_icons.emoji_to_icons(page)


def walk_min(t):
    h = re.search(r'(\d+)時間', t or '')
    mi = re.search(r'(\d+)分', t or '')
    return (int(h.group(1)) if h else 0) * 60 + (int(mi.group(1)) if mi else 0)


def trip_plan(m, r, x):
    """東京から登山とサウナを1日でできるかの目安（2026-11-18。外部の監査の指摘「施設が日帰りで使えることと、東京から1日で回れることは別」）。
    新宿からの車の往復＋代表コースの歩く時間＋サウナ（1時間）の合計で分ける：12時間以内＝日帰り向け、15時間以内＝早朝出発・健脚向け、
    それより長い・山が日帰り不可＝前泊・宿泊がおすすめ。休憩・渋滞は入れていない"""
    w = walk_min(r.get('time'))
    drive = m.get('driveTimeShinjuku') or 0
    total = drive * 2 + w + 60
    if not m.get('daytrip') or total > 15 * 60:
        plan = '前泊・宿泊がおすすめ'
    elif total > 12 * 60:
        plan = '早朝出発・健脚向け'
    else:
        plan = '東京から日帰り向け'
    note = ''
    if r.get('courseType') == 'traverse' and not x.get('walk'):
        note = '。縦走コースなので、車で行くときは下山口から車へ戻る方法も考えておきましょう（車の時間は登山口・駐車場から）'
    return plan, note


def main():
    s = build()
    p = os.path.join(ROOT, 'articles', SLUG, 'index.html')
    old = open(p, encoding='utf-8').read() if os.path.exists(p) else None
    if '--check' in sys.argv:
        print('同じ' if old == s else '違う')
        sys.exit(0 if old == s else 1)
    if s.count('<div') != s.count('</div>') or not s.rstrip().endswith('</html>'):
        raise SystemExit('ページの形が壊れている')
    if old != s:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(s)
        print('書きました', os.path.relpath(p, ROOT))
    else:
        print('変わらない')


if __name__ == '__main__':
    main()
