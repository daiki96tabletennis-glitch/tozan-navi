#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事「山の茶屋・山小屋グルメ」（articles/mountain-gourmet/index.html）を作る。手でページを編集しない。

  python3 scripts/gen_gourmet_article.py

中身：data/mountain_gourmet.json（泊まらなくても食べられるものだけ。出典つき）
山の難易度・代表コース・山小屋の営業期間：data/mountains.json・data/huts.json
写真：各項目の image.src（例 /images/articles/mountain-gourmet/nabewari.jpg）。ファイルがあるときだけ写真の枠を出す。
見た目（style・header・保存/共有のボタン）は articles/tokyo-daytrip-5/index.html から引き継ぐ。
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUG = 'mountain-gourmet'
OUT = os.path.join(ROOT, 'articles', SLUG, 'index.html')
TPL = os.path.join(ROOT, 'articles', 'tokyo-daytrip-5', 'index.html')
URL = 'https://tozan-navi.com/articles/%s/' % SLUG
E = lambda s: html.escape(str(s if s is not None else ''), quote=True)
MARK = '<!-- generated: scripts/gen_gourmet_article.py（手で編集しない） -->'


def rep_route(m):
    rid = m.get('representativeRouteId')
    for r in m.get('routes') or []:
        if rid and r.get('id') == rid:
            return r
    return (m.get('routes') or [{}])[0]


def main():
    cfg = json.load(open(os.path.join(ROOT, 'data', 'mountain_gourmet.json'), encoding='utf-8'))
    D = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
    H = {h['id']: h for h in json.load(open(os.path.join(ROOT, 'data', 'huts.json'), encoding='utf-8'))['huts']}
    for it in cfg['items']:
        assert it['mountainId'] in D, it['key']
        assert it.get('sources') or it.get('hutId'), it['key'] + '：出典が無い'
        if it.get('hutId'):
            assert it['hutId'] in H, it['key']
    tpl = open(TPL, encoding='utf-8').read()
    gtag = re.search(r'(?s)<!-- Google tag \(gtag\.js\) -->.*?</script>\s*<script>.*?</script>', tpl).group(0)
    style = re.search(r'(?s)<style>.*?</style>', tpl).group(0)
    header = re.search(r'(?s)<header>.*?</header>', tpl).group(0)
    tail = re.search(r'(?s)</main>(.*)</body>', tpl).group(1).replace("'tokyo-daytrip-5'", "'%s'" % SLUG)
    tail = re.sub(r"title:'[^']*'", "title:'山の茶屋・山小屋グルメ'", tail)
    style = style.replace('</style>', '''
/* 山グルメの記事 */
.gm-toc{background:#fff;border:1px solid #e0dbd4;border-radius:12px;padding:12px 14px;margin:14px 0}
.gm-toc b{display:block;font-size:12px;color:#7a7068;margin-bottom:6px}
.gm-toc a{display:block;font-size:13px;color:#2a3820;text-decoration:none;padding:3px 0}
.gm-group{font-size:19px;margin:26px 0 6px}
.gm-lead{font-size:13.5px;color:#5a5248;line-height:1.8;margin-bottom:12px}
.gm-card{background:#fff;border:1px solid #e0dbd4;border-radius:14px;margin-bottom:12px;overflow:hidden}
.gm-photo{margin:0;background:#eeeae2}
.gm-photo img{display:block;width:100%;aspect-ratio:3/2;object-fit:cover}
.gm-photo figcaption{font-size:10.5px;color:#8a8070;padding:4px 12px}
.gm-photo figcaption a{color:#8a8070}
.gm-body{padding:14px 16px}
.gm-place{font-size:17px;font-weight:800;color:#2a3820;margin:0 0 2px}
.gm-where{font-size:12px;color:#8a8070;margin-bottom:8px}
.gm-food{font-size:14.5px;line-height:1.75;color:#2f2b26;background:#fbf7ee;border-left:3px solid #c9a24a;border-radius:4px;padding:8px 10px;margin-bottom:8px}
.gm-notes{font-size:12.5px;color:#5a5248;line-height:1.7;margin-bottom:8px}
.gm-mt{font-size:12px;color:#3a5828;background:#f0f6e8;border-radius:8px;padding:6px 9px;margin-bottom:8px}
.gm-mt a{color:#2a3820;font-weight:700}
.gm-src{font-size:10.5px;color:#8a8070;line-height:1.6}
.gm-src a{color:#4a6038}
.gm-tips li{font-size:13.5px;line-height:1.8;margin:0 0 6px 18px;color:#3a3530}
</style>''')

    groups = []
    items = []
    n = 0
    for g in cfg['groups']:
        cards = []
        for it in [x for x in cfg['items'] if x['group'] == g['key']]:
            n += 1
            m = D[it['mountainId']]
            r = rep_route(m)
            img = it.get('image') or {}
            photo = ''
            if img.get('src') and os.path.exists(os.path.join(ROOT, img['src'].lstrip('/'))):
                cap = ''
                if img.get('source') == 'wikimedia_commons':
                    # CC BY / BY-SA は作者・ライセンス・元のページの表示が必要
                    lic = E(img.get('license') or '')
                    if img.get('licenseUrl'):
                        lic = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(img['licenseUrl']), lic)
                    cap = '<figcaption>写真：%s（%s）／<a href="%s" target="_blank" rel="noopener">Wikimedia Commons</a></figcaption>' % (
                        E(img.get('credit') or '作者不明'), lic, E(img.get('pageUrl') or ''))
                elif img.get('credit'):
                    cap = '<figcaption>写真：%s</figcaption>' % E(img['credit'])
                photo = ('<figure class="gm-photo"><img src="%s" alt="%s" loading="lazy">%s</figure>'
                         % (E(img['src']), E(img.get('alt') or it['place']), cap))
            if it.get('hutId'):
                h = H[it['hutId']]
                src = ('出典：<a href="%s" target="_blank" rel="noopener">%sの公式サイト</a>（メニューは年によって変わります）。営業期間：%s（<a href="/huts/%s/">山小屋の情報</a>）'
                       % (E(it.get('official') or h.get('officialUrl')), E(h['name']), E((h.get('openText') or '公式サイトで確認').split('＊')[0].strip()), E(h['id'])))
            else:
                src = '出典：' + '、'.join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(s['url']), E(s['label'])) for s in it['sources']) + '（営業日・メニューは変わります）'
            cards.append(
                '<article class="gm-card" id="%s">%s<div class="gm-body">' % (E(it['key']), photo)
                + '<h3 class="gm-place">%s</h3><div class="gm-where">%s</div>' % (E(it['place']), E(it['where']))
                + '<div class="gm-food">%s</div>' % E(it['food'])
                + ('<div class="gm-notes">%s</div>' % E(it['notes']) if it.get('notes') else '')
                + '<div class="gm-mt"><a href="/mountains/%s/">%s</a>（%s・%s）代表コース：%s %s</div>' % (
                    E(m['id']), E(m['name']), E(m.get('difficulty')), '日帰り可' if m.get('daytrip') else '山小屋泊が基本', E(r.get('name')), E(r.get('time')))
                + '<div class="gm-src">%s</div></div></article>' % src)
            items.append({'@type': 'ListItem', 'position': n, 'name': '%s（%s）' % (it['place'], m['name']), 'url': URL + '#' + it['key']})
        groups.append('<h2 class="gm-group" id="g-%s">%s</h2><p class="gm-lead">%s</p>%s' % (E(g['key']), E(g['title']), E(g['lead']), ''.join(cards)))

    total = len(cfg['items'])
    title = '山の茶屋・山小屋グルメ%d選｜泊まらなくても食べられる名物【%s年】 | Yamatch' % (total, cfg['checkedAt'][:4])
    desc = ('鍋割山荘の鍋焼きうどん、景信山の天ぷら、立山・みくりが池温泉のブルーベリーソフト、涸沢小屋のもつ煮など、'
            '泊まらなくても食べられる山の茶屋・山小屋の名物を%d軒。山の難易度・代表コースと、出典つきで紹介します。' % total)
    faqs = [
        ('山小屋に泊まらなくても食事はできますか？', '多くの山小屋は、泊まらない登山者にも昼の軽食や喫茶を出しています。この記事では、泊まる人だけの夕食・朝食は除き、日中に立ち寄って食べられるものだけを紹介しています。'),
        ('山の茶屋はいつ営業していますか？', '関東の低山の茶屋は、土日・休日が中心で、天候によって休むことがあります。アルプスの山小屋は夏〜秋が中心です。営業日・メニューは変わるので、行く前に公式の情報や山小屋の案内で確かめてください。'),
        ('日帰りで行けるおすすめはどこですか？', '電車で日帰りしやすいのは、鍋割山（鍋割山荘の鍋焼きうどん）、景信山・小仏城山（茶屋の天ぷら・なめこ汁）、陣馬山、金時山です。乗り物で高いところへ上がれる立山・室堂や栂池自然園の山小屋も、日帰りで寄れます。'),
    ]
    ld = [
        {'@context': 'https://schema.org', '@type': 'Article', 'headline': title.split(' | ')[0], 'description': desc, 'dateModified': cfg['checkedAt'],
         'author': {'@type': 'Organization', 'name': 'Yamatch'}, 'mainEntityOfPage': URL},
        {'@context': 'https://schema.org', '@type': 'ItemList', 'name': '山の茶屋・山小屋グルメ', 'numberOfItems': total, 'itemListElement': items},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Yamatch', 'item': 'https://tozan-navi.com/'},
            {'@type': 'ListItem', 'position': 2, 'name': '記事一覧', 'item': 'https://tozan-navi.com/articles/'},
            {'@type': 'ListItem', 'position': 3, 'name': '山の茶屋・山小屋グルメ', 'item': URL}]},
    ]
    toc = '<div class="gm-toc"><b>目次</b>%s<a href="#tips">楽しむためのコツ</a></div>' % ''.join('<a href="#g-%s">%s</a>' % (E(g['key']), E(g['title'])) for g in cfg['groups'])
    tips = ['営業日を確かめる。低山の茶屋は土日・休日が中心で、雨の日や平日は閉まっていることが多い',
            '人気のメニューは昼前に売り切れることがある。お目当てがあるなら早めに着く',
            '山の上は電波が弱く、使える支払い方法も限られることがあるので、現金を少し持っていく',
            'ごみは持ち帰る。山の上でのごみの処理には手間と費用がかかる',
            '食べる時間も計画に入れて、帰りのバス・ロープウェイの時刻に間に合うようにする']
    main_html = (
        '<a id="top"></a><div class="article-hero"><div class="hero-inner"><div class="article-label">山のグルメ</div>'
        '<h1 class="article-title">山の茶屋・山小屋グルメ%d選<br>泊まらなくても食べられる名物</h1>' % total
        + '<p class="article-desc">山頂の茶屋の天ぷらや鍋焼きうどん、アルプスの山小屋の昼ごはん。日帰りや立ち寄りで味わえるものだけを集めました。</p>'
        '<div class="article-meta"><span class="meta-pill updated-pill">最終更新: %s</span><span class="meta-pill">%d軒</span></div></div></div>\n' % (cfg['checkedAt'], total)
        + '<main>\n<div class="lead-box">山歩きの楽しみのひとつが、山の上で食べるごはんです。この記事では、サイトで紹介している山のなかから、'
          '<strong>泊まらなくても食べられる</strong>茶屋・山小屋の名物を%d軒選びました。泊まる人だけの夕食・朝食は入れていません。'
          'メニューは山小屋の公式サイトや、自治体・登山メディアの記事で確かめたもので、出典を各項目に付けています。値段や営業時間は変わりやすいので載せていません。</div>\n' % total
        + toc + '\n'.join(groups)
        + '<h2 id="tips">山のグルメを楽しむためのコツ</h2><ul class="gm-tips">%s</ul>' % ''.join('<li>%s</li>' % E(t) for t in tips)
        + '<h2>よくある質問</h2>' + ''.join('<div class="faq-item"><div class="faq-q">%s</div><div class="faq-a"><p>%s</p></div></div>' % (E(q), E(a)) for q, a in faqs)
        + '\n<div class="other-articles"><a href="/search/train-daytrip/" class="other-article-link"><span>電車で行ける日帰り登山（関東）</span><span>→</span></a>'
          '<a href="/huts/" class="other-article-link"><span>山小屋の予約開始日・予約方法まとめ</span><span>→</span></a>'
          '<a href="/articles/" class="other-article-link"><span>記事一覧をみる</span><span>→</span></a></div>\n')
    page = '\n'.join([
        '<!DOCTYPE html>', '<html lang="ja">', '<head>', gtag, '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<title>%s</title>' % E(title), '<meta name="description" content="%s">' % E(desc),
        '<meta property="og:title" content="%s">' % E(title.split(' | ')[0]), '<meta property="og:description" content="%s">' % E(desc),
        '<meta property="og:type" content="article">', '<meta property="og:url" content="%s">' % URL,
        '<meta property="og:site_name" content="Yamatch">', '<link rel="canonical" href="%s">' % URL,
    ] + ['<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in ld]
      + [style, '</head>', '<body>', MARK, header, main_html + '</main>' + tail + '</body>', '</html>', ''])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(page)
    shown = sum(1 for it in cfg['items'] if (it.get('image') or {}).get('src') and os.path.exists(os.path.join(ROOT, it['image']['src'].lstrip('/'))))
    print('作りました：%d軒（写真あり %d）→ %s' % (total, shown, os.path.relpath(OUT, ROOT)))


if __name__ == '__main__':
    main()
