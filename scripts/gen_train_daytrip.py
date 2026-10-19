#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「電車で行ける日帰り登山（関東）」まとめ（search/train-daytrip/index.html）を作る。手でページを編集しない。

  python3 scripts/gen_train_daytrip.py           ページを作り直す
  python3 scripts/gen_train_daytrip.py --check   書き込まずに、選んだ山のデータに問題が無いかだけ見る

選ぶ山・帰りの最終バス：data/train_daytrip.json（最終バスは公式の時刻表で確かめた値だけ。未確認は「確認中」）
電車の時間・運賃・乗り継ぎ・コース・特徴：data/mountains.json（山ページと同じ値。特徴は出典つきの featurePoints だけ）
ページの見た目（style・header・footer）は、いまのページから引き継ぐ。
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'search', 'train-daytrip', 'index.html')
URL = 'https://tozan-navi.com/search/train-daytrip/'
E = lambda s: html.escape(str(s if s is not None else ''), quote=True)
DEP = [('shinjuku', '新宿'), ('omiya', '大宮'), ('yokohama', '横浜')]
MARK = '<!-- generated: scripts/gen_train_daytrip.py（手で編集しない） -->'


def hm(minutes):
    if not minutes:
        return None
    h, m = divmod(int(minutes), 60)
    return ('%d時間%d分' % (h, m) if m else '%d時間' % h) if h else '%d分' % m


def yen(v):
    return '{:,}円'.format(int(v)) if v else None


def legs_of(m, dep='shinjuku'):
    r = (((m.get('trainRoutes') or {}).get('routes') or {}).get(dep) or {})
    return r.get('legs') or []


def path_text(m):
    """新宿駅 →（京王線）→ 高尾山口駅 → … の形。最後は登山口"""
    out = []
    legs = legs_of(m)
    for i, l in enumerate(legs):
        st = l.get('station') or ''
        line = (l.get('method') or {}).get('line')
        out.append(E(st))
        if line and i < len(legs) - 1:
            out.append('<span class="td-line">' + E(line) + '</span>')
    return ' → '.join(out)


def rep_route(m):
    rid = m.get('representativeRouteId')
    for r in m.get('routes') or []:
        if rid and r.get('id') == rid:
            return r
    return (m.get('routes') or [{}])[0]


def last_bus_html(lb):
    if not lb:
        return '<div class="td-last td-last-pending"><b>帰りの最終バス</b>確認中</div>'
    st = lb.get('status')
    if st == 'walk':
        return '<div class="td-last td-last-walk"><b>帰り</b>' + E(lb['text']) + '</div>'
    if st == 'ok':
        rows = ''.join('<tr><td>%s → %s</td><td>%s</td><td>%s</td></tr>' % (E(r['from']), E(r['to']), E(r['weekday']), E(r['holiday'])) for r in lb['rows'])
        note = ('<div class="td-last-n">' + E(lb['note']) + '</div>') if lb.get('note') else ''
        src = ('<div class="td-last-s">出典：<a href="%s" target="_blank" rel="noopener">%sの時刻表</a>（%s改正・%s確認）。ダイヤは変わることがあるので、行く前に確かめてください</div>'
               % (E(lb['sourceUrl']), E(lb.get('operator') or '運行会社'), E(lb.get('revised') or ''), E(lb.get('checkedAt') or '')))
        return ('<div class="td-last"><b>帰りの最終バス</b><table class="td-last-t"><tr><th>区間</th><th>平日</th><th>土休日</th></tr>'
                + rows + '</table>' + note + src + '</div>')
    return ('<div class="td-last td-last-pending"><b>帰りの最終バス</b>確認中（%s）。山ページの電車・バス欄の時刻表で確かめてください</div>' % E(lb.get('operator') or '運行会社'))


def card(n, m, lb):
    r = rep_route(m)
    fp = [f for f in (m.get('featurePoints') or []) if f.get('label') and f.get('text')][:2] if m.get('featureSources') else []
    times = ' ／ '.join('%s %s・%s' % (lab, hm(m.get('trainTime' + lab_key.capitalize())), yen(m.get('fare' + lab_key.capitalize())))
                       for lab_key, lab in DEP if m.get('trainTime' + lab_key.capitalize()) and m.get('fare' + lab_key.capitalize()))
    walk = '・'.join(x for x in (E(r.get('time')), E(r.get('distance')), ('標高差' + E(r.get('elevation', '')).lstrip('+')) if r.get('elevation') else '') if x)
    feats = ''.join('<li><b>%s</b>%s</li>' % (E(f['label']), E(f['text'])) for f in fp)
    return (
        '<article class="td-card" id="m-%s">\n' % E(m['id'])
        + '  <div class="td-no">%d</div>\n' % n
        + '  <div class="td-body">\n'
        + '    <h3 class="td-name"><a href="/mountains/%s/">%s</a><span class="td-sub">%s・%s・%sm</span></h3>\n' % (
            E(m['id']), E(m['name']), E(m.get('difficulty')), E(m.get('area') or ''), '{:,}'.format(int(m['elevation'])) if m.get('elevation') else '')
        + '    <div class="td-key"><div><span>新宿から電車・バス</span><b>%s</b></div><div><span>片道の運賃</span><b>%s</b></div><div><span>歩く時間</span><b>%s</b></div></div>\n' % (
            E(hm(m.get('trainTimeShinjuku'))), E(yen(m.get('fareShinjuku'))), E(r.get('time') or '—'))
        + '    <div class="td-path">%s</div>\n' % path_text(m)
        + ('    <div class="td-other">%s</div>\n' % E(times) if times else '')
        + '    <div class="td-walk">代表コース：%s（%s）</div>\n' % (E(r.get('name') or ''), walk)
        + '    %s\n' % last_bus_html(lb)
        + ('    <ul class="td-feat">%s</ul>\n' % feats if feats else '')
        + '    <a href="/mountains/%s/" class="td-link">%sの詳しい情報（天気・装備・地図）→</a>\n' % (E(m['id']), E(m['name']))
        + '  </div>\n</article>'
    )


def main():
    check = '--check' in sys.argv
    cfg = json.load(open(os.path.join(ROOT, 'data', 'train_daytrip.json'), encoding='utf-8'))
    D = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
    sel = [i for g in cfg['groups'] for i in g['ids']]
    probs = []
    for i in sel:
        m = D.get(i)
        if not m:
            probs.append(i + '：mountains.json に無い'); continue
        if not m.get('daytrip'):
            probs.append(i + '：日帰り不可の山'); continue
        if not (m.get('trainTimeShinjuku') and m.get('fareShinjuku') and legs_of(m)):
            probs.append(i + '：電車の時間・運賃・乗り継ぎが無い')
        if (m.get('status') or {}).get('level') == 'restricted':
            probs.append(i + '：規制中の山')
    if probs:
        print('\n'.join(probs))
        sys.exit(1)
    if check:
        print('問題なし（%d山）' % len(sel)); return

    old = open(PAGE, encoding='utf-8').read()
    style = re.search(r'(?s)<style>.*?</style>', old).group(0)
    header = re.search(r'(?s)<header>.*?</header>', old).group(0)
    footer = re.search(r'(?s)<footer>.*?</footer>', old).group(0)
    gtag = re.search(r'(?s)<!-- Google tag \(gtag\.js\) -->.*?</script>\s*<script>.*?</script>', old).group(0)
    extra_css = '''
/* 2026-10 作り直し：電車で行く人向けの20選 */
.td-index{background:white;border-radius:14px;border:1px solid #e0dbd4;padding:14px;margin-bottom:12px;overflow-x:auto}
.td-index table{border-collapse:collapse;width:100%;min-width:520px;font-size:12px}
.td-index th,.td-index td{padding:6px 6px;border-bottom:1px solid #f0ede8;text-align:left;white-space:nowrap}
.td-index th{font-size:10.5px;color:#7a7068;font-weight:600}
.td-index td a{color:#2a3820;font-weight:700;text-decoration:none}
.td-gh{font-size:17px;font-weight:800;color:#2a3820;margin:22px 0 4px}
.td-gl{font-size:13px;color:#5a5248;line-height:1.7;margin-bottom:10px}
.td-card{background:white;border-radius:14px;border:1px solid #e0dbd4;margin-bottom:10px;padding:14px;display:flex;gap:10px}
.td-no{font-size:18px;font-weight:900;color:#c0b090;min-width:26px;text-align:center}
.td-body{flex:1;min-width:0}
.td-name{font-size:16px;line-height:1.35;margin-bottom:8px}
.td-name a{color:#2a3820;text-decoration:none}
.td-sub{display:block;font-size:11px;font-weight:400;color:#9a9088;margin-top:2px}
.td-key{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:8px}
.td-key div{background:#f6f4ef;border-radius:8px;padding:6px 8px}
.td-key span{display:block;font-size:10px;color:#9a9088}
.td-key b{font-size:14px;color:#2a3820}
.td-path{font-size:12px;color:#1a4a70;background:#e8f2fb;border-radius:8px;padding:6px 9px;line-height:1.7;margin-bottom:6px}
.td-line{font-size:10.5px;color:#4a6a88;background:#fff;border-radius:4px;padding:0 4px;margin:0 2px}
.td-other{font-size:11px;color:#6a6258;margin-bottom:6px}
.td-walk{font-size:12px;color:#3a5828;background:#f0f6e8;border-radius:8px;padding:6px 9px;margin-bottom:6px}
.td-last{font-size:12px;color:#3a342c;border:1px solid #e6dcc4;background:#fffaf0;border-radius:8px;padding:7px 9px;margin-bottom:8px;line-height:1.6}
.td-last b{display:block;font-size:11px;color:#7a5a20;margin-bottom:2px}
.td-last-walk{border-color:#cfe0c0;background:#f4f9ef}
.td-last-walk b{color:#3a5828}
.td-last-pending{color:#7a7068}
.td-last-t{border-collapse:collapse;width:100%;margin:2px 0 4px}
.td-last-t th,.td-last-t td{font-size:11.5px;padding:3px 4px;border-bottom:1px solid #f0e6d0;text-align:left}
.td-last-t th{font-size:10px;color:#9a8a60;font-weight:600}
.td-last-n,.td-last-s{font-size:10.5px;color:#7a7068}
.td-last-s a{color:#4a6038}
.td-feat{list-style:none;margin:0 0 8px;padding:0}
.td-feat li{font-size:12px;color:#5a5248;line-height:1.6;margin-bottom:3px}
.td-feat b{color:#2a3820;margin-right:6px}
.td-link{font-size:12px;font-weight:700;color:#4a6038;text-decoration:none}
.td-tips{background:white;border-radius:14px;border:1px solid #e0dbd4;padding:16px 18px;margin:16px 0}
.td-tips h2{font-size:16px;color:#2a3820;margin-bottom:8px}
.td-tips li{font-size:13px;color:#4a4540;line-height:1.75;margin:0 0 6px 18px}
.td-more{background:white;border-radius:14px;border:1px solid #e0dbd4;padding:14px;margin-bottom:12px;overflow-x:auto}
.td-more h2{font-size:15px;color:#2a3820;margin-bottom:4px}
.td-more p{font-size:12px;color:#7a7068;margin-bottom:8px}
.td-more table{border-collapse:collapse;width:100%;min-width:480px;font-size:12px}
.td-more th,.td-more td{padding:6px;border-bottom:1px solid #f0ede8;text-align:left;white-space:nowrap}
.td-more th{font-size:10.5px;color:#7a7068;font-weight:600}
.td-more td a{color:#2a3820;text-decoration:none;font-weight:600}
.faq-q{font-size:14px;font-weight:700;color:#2a3820;margin-bottom:6px;line-height:1.5}
@media(max-width:420px){.td-key b{font-size:13px}.td-card{padding:12px 10px}}
'''
    style = style.replace('</style>', extra_css + '</style>')

    cards, n, idx_rows, items = [], 0, [], []
    for g in cfg['groups']:
        cards.append('<h2 class="td-gh" id="g-%s">%s（%d山）</h2>\n<p class="td-gl">%s</p>' % (E(g['key']), E(g['title']), len(g['ids']), E(g['lead'])))
        for i in g['ids']:
            n += 1
            m = D[i]
            lb = cfg['lastBus'].get(i)
            cards.append(card(n, m, lb))
            r = rep_route(m)
            lbs = {'walk': '駅まで徒歩', 'ok': '平日 %s ／ 土休日 %s' % (lb['rows'][-1]['weekday'], lb['rows'][-1]['holiday']) if lb and lb.get('status') == 'ok' else ''}.get((lb or {}).get('status'), '確認中')
            idx_rows.append('<tr><td>%d</td><td><a href="#m-%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                n, E(i), E(m['name']), E(m.get('difficulty')), E(hm(m.get('trainTimeShinjuku'))), E(yen(m.get('fareShinjuku'))), E(r.get('time')), E(lbs)))
            items.append({'@type': 'ListItem', 'position': n, 'url': 'https://tozan-navi.com/mountains/%s/' % i, 'name': m['name']})

    rest = []
    for i, m in D.items():
        if i in sel or not m.get('daytrip') or not m.get('trainTimeShinjuku') or not m.get('fareShinjuku') or not legs_of(m):
            continue
        if (m.get('status') or {}).get('level') == 'restricted':
            continue
        if m['id'] not in OTHERS:
            continue
        rest.append(m)
    rest.sort(key=lambda m: m.get('trainTimeShinjuku') or 999)
    rest_rows = ''.join('<tr><td><a href="/mountains/%s/">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        E(m['id']), E(m['name']), E(m.get('difficulty')), E(hm(m.get('trainTimeShinjuku'))), E(yen(m.get('fareShinjuku'))), E(rep_route(m).get('time'))) for m in rest)

    total = len(sel)
    fast = sorted((D[i] for i in sel), key=lambda m: m['trainTimeShinjuku'])[:3]
    cheap = sorted((D[i] for i in sel), key=lambda m: m['fareShinjuku'])[:3]
    hy = [D[i] for i in cfg['groups'][2]['ids']]
    faqs = [
        ('電車だけで行ける日帰り登山は、どこがおすすめですか？',
         'はじめてなら、新宿から近い%sがおすすめです。どれも電車・バスで2時間以内に登山口に着きます。この記事では、はじめての電車登山・しっかり歩く日帰り・電車で行く百名山の3つに分けて%d山を紹介しています。'
         % ('・'.join('%s（%s）' % (m['name'], hm(m['trainTimeShinjuku'])) for m in fast), total)),
        ('交通費が安いのはどの山ですか？',
         '新宿からの片道の運賃が安いのは、%sです。運賃はこの記事の各山に、新宿・大宮・横浜からの値を載せています。'
         % '・'.join('%s（%s）' % (m['name'], yen(m['fareShinjuku'])) for m in cheap)),
        ('電車とバスで日帰りできる百名山はありますか？',
         'あります。%sは、新幹線や特急、ロープウェイを使って日帰りで登れます。新宿からの電車・バスの時間は%s〜%sです。季節運行のバスやロープウェイが多いので、運行期間を確かめてから計画してください。'
         % ('・'.join(m['name'] for m in hy), hm(min(m['trainTimeShinjuku'] for m in hy)), hm(max(m['trainTimeShinjuku'] for m in hy)))),
        ('帰りのバスに乗り遅れないためには？',
         '登る前に、下山口のバス停の最終便を確かめ、そこから歩く時間を逆算して、登り始める時刻と引き返す時刻を決めておきます。この記事では、確かめられた山から帰りの最終バスを載せています（出典と確認日つき）。山の上では予定より時間がかかることが多いので、最終便の1本か2本前に乗るつもりで歩くと安心です。'),
    ]
    faq_html = ''.join('<div class="faq-item"><div class="faq-q">%s</div><div class="faq-a"><p>%s</p></div></div>' % (E(q), E(a)) for q, a in faqs)
    ld = [
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Yamatch', 'item': 'https://tozan-navi.com/'},
            {'@type': 'ListItem', 'position': 2, 'name': '電車で行ける日帰り登山（関東）', 'item': URL}]},
        {'@context': 'https://schema.org', '@type': 'ItemList', 'name': '電車で行ける日帰り登山（関東）%d選' % total, 'itemListElement': items},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]},
    ]
    title = '電車で行ける日帰り登山（関東）%d選｜新宿から何分・運賃・帰りの最終バス【%s年】 | Yamatch' % (total, cfg.get('year', '2026'))
    desc = ('電車とバスだけで行ける関東の日帰り登山を%d山。%s（%s）から%s（%s）まで、新宿・大宮・横浜からの所要時間と片道の運賃、駅から登山口までの乗り継ぎ、帰りの最終バスを山ごとに載せています。'
            % (total, fast[0]['name'], hm(fast[0]['trainTimeShinjuku']), hy[-1]['name'], hm(hy[-1]['trainTimeShinjuku'])))
    intro = ('電車とバスだけで、関東から日帰りで登れる山を%d山に絞りました。山ごとに、<strong>新宿から登山口までの時間と片道の運賃</strong>、<strong>駅からの乗り継ぎ</strong>、<strong>帰りの最終バス</strong>を載せています。'
             '時間と運賃は、各山のページと同じデータです。最終バスは、運行会社の時刻表で確かめた山から順に載せています。' % total)
    tips = [
        '帰りの最終バスから逆算して、登り始める時刻と「ここで引き返す」時刻を先に決めておく',
        '平日と土曜・休日で時刻が違うバスが多い。季節運行のバス・ロープウェイは運行期間も確かめる',
        '山で予定より遅れることを考えて、最終便の1本か2本前に乗るつもりで歩く',
        '始発に近い電車に乗ると、登山口のバスも空いていて、明るいうちに下りやすい',
        '登山届は、登山口のポストかオンラインで出しておく（家族にも行き先と帰りの電車を伝える）',
    ]
    main_html = '\n'.join([
        '<main>',
        '  <div class="page-head">',
        '    <div class="page-kw">電車 日帰り 登山 関東</div>',
        '    <h1>電車で行ける日帰り登山（関東）%d選｜新宿から何分・運賃・帰りの最終バス</h1>' % total,
        '    <div class="page-intro">%s</div>' % intro,
        '    <p class="page-count">%d山を掲載 · 時間・運賃は山ページのデータ · 最終バスは出典と確認日つき</p>' % total,
        '  </div>',
        '  <div class="related-tags">',
        '    <a href="#g-easy" class="rs-tag">はじめての電車登山</a>',
        '    <a href="#g-solid" class="rs-tag">しっかり歩く日帰り</a>',
        '    <a href="#g-hyaku" class="rs-tag">電車で行く百名山</a>',
        '    <a href="#more" class="rs-tag">ほかの電車で行ける山</a>',
        '  </div>',
        '  <div class="td-index"><table><tr><th>#</th><th>山</th><th>難易度</th><th>新宿から</th><th>片道</th><th>歩く時間</th><th>帰りの最終バス</th></tr>%s</table></div>' % ''.join(idx_rows),
        '\n'.join(cards),
        '  <div class="td-tips"><h2>電車登山で困らないために</h2><ul>%s</ul></div>' % ''.join('<li>%s</li>' % E(t) for t in tips),
        '  <div class="td-more" id="more"><h2>ほかの電車で行ける日帰りの山（%d山）</h2><p>上の%d山のほかにも、電車とバスで日帰りできる山があります。詳しくは各山のページへ。</p><table><tr><th>山</th><th>難易度</th><th>新宿から</th><th>片道</th><th>歩く時間</th></tr>%s</table></div>' % (len(rest), total, rest_rows),
        '  <div class="cta-banner"><div class="cta-title">自分に合う山を12問で診断</div><div class="cta-sub">体力や好みから、登る山を提案します</div><a href="/recommend/" class="cta-btn">診断する →</a></div>',
        '  <div class="faq-section"><h2>よくある質問</h2>%s</div>' % faq_html,
        '  <div class="internal-links"><div class="il-title">関連するまとめ</div>%s</div>' % ''.join(
            '<a href="%s" class="il-link">→ %s</a>' % (u, t) for u, t in RELATED),
        '</main>',
    ])
    page = '\n'.join([
        '<!DOCTYPE html>', '<html lang="ja">', '<head>', '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">',
        '<title>%s</title>' % E(title), gtag,
        '<meta name="description" content="%s">' % E(desc),
        '<meta property="og:title" content="%s">' % E(title),
        '<meta property="og:description" content="%s">' % E(desc),
        '<meta property="og:type" content="website">', '<meta property="og:url" content="%s">' % URL,
        '<link rel="canonical" href="%s">' % URL,
    ] + ['<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in ld] + [
        style, '</head>', '<body>', MARK, header, main_html, footer, '</body>', '</html>', ''])
    open(PAGE, 'w', encoding='utf-8').write(page)
    print('作りました：%d山（ほか%d山）／最終バス 確認済み %d・徒歩 %d・確認中 %d' % (
        total, len(rest), sum(1 for v in cfg['lastBus'].values() if v.get('status') == 'ok'),
        sum(1 for v in cfg['lastBus'].values() if v.get('status') == 'walk'),
        sum(1 for i in sel if (cfg['lastBus'].get(i) or {}).get('status') not in ('ok', 'walk'))))


# 「ほかの電車で行ける山」に並べる山（以前のページに載せていた日帰りの山のうち、20選に入れなかったもの）
OTHERS = ['tenzandake', 'kentoku', 'koganzan', 'nantaisan', 'kirigamine', 'keirisan', 'nanaitsurasan', 'naeba', 'iwasugesan',
          'makihata', 'iizunasan', 'kurohimesan', 'myoko', 'bandai', 'shirouma', 'harinokidake']
RELATED = [('/search/takao-hiking/', '高尾駅から登れる山'), ('/search/hanno-hiking/', '飯能駅から登れる山'), ('/search/shibusawa-hiking/', '渋沢駅から登れる山'),
           ('/search/echigoyuzawa-hiking/', '越後湯沢駅から登れる山'), ('/search/odakyu-hiking/', '小田急線で行ける登山'), ('/search/jr-chuo-hiking/', '中央線で行ける登山'),
           ('/search/seibu-hiking/', '西武線で行ける登山'), ('/search/keiou-hiking/', '京王線で行ける登山'), ('/search/shinjuku-daytrip/', '新宿から日帰りで行ける山'),
           ('/search/shinjuku-beginner/', '新宿から行ける初心者向けの山'), ('/search/ofuna-daytrip/', '大船・横浜から日帰りで行ける山'), ('/recommend/', '12問の登山タイプ診断')]

if __name__ == '__main__':
    main()
