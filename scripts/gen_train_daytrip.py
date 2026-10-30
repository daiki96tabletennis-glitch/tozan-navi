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


CFG = {}


def course(m):
    """記事で使うコース・電車とバスの区間（data/train_daytrip.json の courses。無ければ代表コース・全区間）"""
    return (CFG.get('courses') or {}).get(m['id']) or {}


def chosen_route(m):
    c = course(m)
    if 'route' in c:
        return (m.get('routes') or [{}])[c['route']]
    return rep_route(m)


def dep_legs(m, dep='shinjuku'):
    legs = legs_of(m, dep)
    until = course(m).get('accessUntil')
    if not until:
        return legs, legs
    for i, l in enumerate(legs):
        if l.get('station') == until:
            return legs, legs[:i] + [{'station': until}]
    raise SystemExit('%s：accessUntil の駅（%s）が %s の経路にありません' % (m['id'], until, dep))


def dep_time(m, dep='shinjuku'):
    full, cut = dep_legs(m, dep)
    if cut is full:
        return m.get('trainTime' + dep.capitalize())
    return sum(l.get('durationMin') or 0 for l in cut)


def dep_fare(m, dep='shinjuku'):
    full, cut = dep_legs(m, dep)
    dropped = [l for l in full[len(cut) - 1:] if l.get('method')]
    if cut is full or all('徒歩' in (l['method'].get('line') or '') for l in dropped):
        return m.get('fare' + dep.capitalize())
    return (course(m).get('fares') or {}).get(dep)


def walk_min(t):
    h = re.search(r'(\d+)時間', t or '')
    mi = re.search(r'(\d+)分', t or '')
    return (int(h.group(1)) * 60 if h else 0) + (int(mi.group(1)) if mi else 0)


def path_text(m):
    """新宿駅 →（京王線）→ 高尾山口駅 → … の形。最後は歩き始める場所"""
    out = []
    legs = dep_legs(m)[1]
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
        return '<div class="td-last td-last-pending"><b>🚌 帰りの最終バス</b>確認中</div>'
    st = lb.get('status')
    if st == 'walk':
        return '<div class="td-last td-last-walk"><b>🚶 帰り</b>' + E(lb['text']) + '</div>'
    if st == 'ok':
        rows = ''.join('<tr><td>%s → %s</td><td>%s</td><td>%s</td></tr>' % (E(r['from']), E(r['to']), E(r['weekday']), E(r['holiday'])) for r in lb['rows'])
        note = ('<div class="td-last-n">' + E(lb['note']) + '</div>') if lb.get('note') else ''
        def when(rev, chk):
            rev = rev or ''
            if rev and not rev.endswith(('現在', '年度')):
                rev += '改正'
            return '（%s%s確認）' % (E(rev) + '・' if rev else '', E(chk or ''))
        if lb.get('sources'):
            links = '・'.join('<a href="%s" target="_blank" rel="noopener">%s</a>%s' % (E(x['url']), E(x['label']), when(x.get('revised'), x.get('checkedAt'))) for x in lb['sources'])
        else:
            links = '<a href="%s" target="_blank" rel="noopener">%sの時刻表</a>%s' % (E(lb['sourceUrl']), E(lb.get('operator') or '運行会社'), when(lb.get('revised'), lb.get('checkedAt')))
        src = '<div class="td-last-s">出典：%s。ダイヤは変わることがあるので、行く前に確かめてください</div>' % links
        return ('<div class="td-last"><b>🚌 帰りの最終バス</b><table class="td-last-t"><tr><th>区間</th><th>平日</th><th>土休日</th></tr>'
                + rows + '</table>' + note + src + '</div>')
    note = ('<div class="td-last-n">' + E(lb['note']) + '</div>') if lb.get('note') else ''
    return ('<div class="td-last td-last-pending"><b>🚌 帰りの最終バス</b>確認中（%s）。山ページの電車・バス欄の時刻表で確かめてください%s</div>' % (E(lb.get('operator') or '運行会社'), note))


def last_short(lb):
    """一覧の欄・冒頭の3コースに出す帰りの1行（lastBus の indexRow。無ければ最後の行）。"""
    st = (lb or {}).get('status')
    if st == 'walk':
        return '駅まで徒歩'
    if st == 'ok':
        r = lb['rows'][lb.get('indexRow', -1)]
        return ((lb['indexLabel'] + ' ') if lb.get('indexLabel') else '') + '平日 %s ／ 土休日 %s' % (r['weekday'], r['holiday'])
    return '確認中'


def picks_html(cfg, D):
    """冒頭の「迷ったらこの3コース」。数字はカードと同じデータ、ひとことは山の featurePoints の文。"""
    out = []
    for p in (cfg.get('picks') or {}).get('items') or []:
        m = D[p['id']]
        r = chosen_route(m)
        f = next((x for x in (m.get('featurePoints') or []) if x.get('label') == p.get('feat')), None)
        if f is None or not m.get('photos') or m['id'] not in [i for g in cfg['groups'] for i in g['ids']]:
            sys.exit('picks: %s が記事に無いか写真が無いか、featurePoints に「%s」が無い' % (m['id'], p.get('feat')))
        lb = cfg['lastBus'].get(m['id'])
        img = photo_box(m, 'td-pick-img')
        last = last_short(lb)
        out.append(
            '<div class="td-pick">%s<div class="td-pick-b"><div class="td-pick-l">%s</div>'
            '<div class="td-pick-n"><a href="#m-%s">%s</a><span>%s</span></div>'
            '<div class="td-pick-k">新宿から %s・%s ／ 歩く %s</div>'
            '<div class="td-pick-f"><b>%s</b>%s</div>'
            '<div class="td-pick-r">帰り：%s</div><a class="td-pick-a" href="#m-%s">乗り継ぎ・コースを見る ↓</a></div></div>' % (
                img, E(p['label']), E(m['id']), E(m['name']), E(m.get('difficulty')),
                E(hm(dep_time(m))), E(yen(dep_fare(m))), E(r.get('time') or '—'),
                E(f['label']), E(f['text']), E(('最終バス ' + last) if (lb or {}).get('status') == 'ok' else last), E(m['id'])))
    if not out:
        return ''
    return '  <div class="td-picks"><h2>迷ったらこの3コース</h2><div class="td-pick-g">%s</div></div>' % ''.join(out)


def photo_box(m, cls):
    """山ページの1枚目の写真。card-photos.js が開くたびに山ページの写真（image-credits.json）にそろえる。"""
    ph = (m.get('photos') or [None])[0]
    img = ('<img class="%s" src="%s" alt="%s" loading="lazy" width="600" height="360">' % (cls, E(ph), E(m['name']))) if ph else ''
    return '<div class="td-photo" data-photo-id="%s" data-photo-alt="%s" data-photo-class="%s"%s>%s</div>' % (
        E(m['id']), E(m['name']), cls, '' if ph else ' style="display:none"', img)


def card(n, m, lb):
    r = chosen_route(m)
    fp = [f for f in (m.get('featurePoints') or []) if f.get('label') and f.get('text')][:2] if m.get('featureSources') else []
    times = ' ／ '.join('%s %s・%s' % (lab, hm(dep_time(m, k)), yen(dep_fare(m, k)))
                       for k, lab in DEP if dep_time(m, k) and dep_fare(m, k))
    cnote = course(m).get('note')
    fsrc = course(m).get('faresSource')
    walk = '・'.join(x for x in (E(r.get('distance')), ('標高差' + E(r.get('elevation', '')).lstrip('+')) if r.get('elevation') else '') if x)
    feats = ''.join('<li><b>%s</b>%s</li>' % (E(f['label']), E(f['text'])) for f in fp)
    notes = ''.join('<li>%s</li>' % x for x in (
        ('🗺️ ほかの出発地から：' + E(times)) if times else '',
        E(cnote) if cnote else '',
        ('運賃の出典：' + E(fsrc)) if fsrc else '') if x)
    return (
        '<article class="td-card" id="m-%s">\n' % E(m['id'])
        + '  <h3 class="td-name"><span class="td-no">%d</span><a href="/mountains/%s/">%s</a><span class="td-sub">%s・%s・%sm</span></h3>\n' % (
            n, E(m['id']), E(m['name']), E(m.get('difficulty')), E(m.get('area') or ''), '{:,}'.format(int(m['elevation'])) if m.get('elevation') else '')
        + '  %s\n' % photo_box(m, 'td-photo-img')
        + '  <div class="td-key"><div><span>🚃 新宿から</span><b>%s</b></div><div><span>💴 片道</span><b>%s</b></div><div><span>🥾 歩く</span><b>%s</b></div></div>\n' % (
            E(hm(dep_time(m))), E(yen(dep_fare(m))), E(r.get('time') or '—'))
        + '  <div class="td-sec"><div class="td-h">🚃 行き方（新宿から）</div><div class="td-path">%s</div>%s</div>\n' % (
            path_text(m), ('<ul class="td-notes">%s</ul>' % notes) if notes else '')
        + '  <div class="td-sec"><div class="td-h">🥾 コース</div><div class="td-walk"><b>%s</b><span>%s%s</span></div></div>\n' % (
            E(r.get('name') or ''), E(r.get('time') or ''), ('・' + walk) if walk else '')
        + '  <div class="td-sec">%s</div>\n' % last_bus_html(lb)
        + ('  <div class="td-sec"><div class="td-h">✨ 見どころ</div><ul class="td-feat">%s</ul></div>\n' % feats if feats else '')
        + '  <a href="/mountains/%s/" class="td-link">⛰️ %sの天気・装備・地図を見る →</a>\n' % (E(m['id']), E(m['name']))
        + '</article>'
    )


def main():
    check = '--check' in sys.argv
    cfg = json.load(open(os.path.join(ROOT, 'data', 'train_daytrip.json'), encoding='utf-8'))
    CFG.update(cfg)
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
    for g in cfg['groups']:
        for i in g['ids']:
            if i in D and g.get('maxWalkMin') and walk_min(chosen_route(D[i]).get('time')) > g['maxWalkMin']:
                probs.append('%s：歩く時間（%s）が「%s」の説明より長い' % (i, chosen_route(D[i]).get('time'), g['title']))
            if i in D and not dep_fare(D[i]):
                probs.append(i + '：記事のコースまでの運賃が分からない（courses の fares に書く）')
    if probs:
        print('\n'.join(probs))
        sys.exit(1)
    if check:
        print('問題なし（%d山）' % len(sel)); return

    old = open(PAGE, encoding='utf-8').read()
    style = re.search(r'(?s)<style>.*?</style>', old).group(0)
    # 前回このスクリプトが足した分（印から </style> まで）を外す。外さないと作り直すたびに同じ CSS が積み重なる（2026-10-30 に約10回分たまっていた）
    style = re.sub(r'(?s)\n?/\* 2026-10 作り直し：電車で行く人向けの20選 \*/.*?(?=</style>)', '', style)
    style = re.sub(r'\s*</style>$', '\n</style>', style)
    header = re.search(r'(?s)<header\b[^>]*>.*?</header>', old).group(0)
    footer = re.search(r'(?s)<footer>.*?</footer>', old).group(0)
    gtag = re.search(r'(?s)<!-- Google tag \(gtag\.js\) -->.*?</script>\s*<script>.*?</script>', old).group(0)
    extra_css = '''
/* 2026-10 作り直し：電車で行く人向けの20選 */
.td-picks{margin:4px 0 14px}
.td-picks h2{font-size:17px;font-weight:800;color:#2a3820;margin:0 0 8px}
.td-pick-g{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.td-pick{display:flex;flex-direction:column;background:white;border-radius:14px;border:1px solid #e0dbd4;overflow:hidden}
.td-pick-n a{color:#2a3820;text-decoration:none}
.td-pick-a{font-size:12px;font-weight:700;color:#4a6038;text-decoration:none;margin-top:2px}
.td-pick-img{width:100%;height:150px;object-fit:cover;display:block}
.td-pick .td-photo{margin:0}
.td-pick .td-photo .ym-photo-credit{margin:5px 12px 0 !important}
.td-pick .ym-photo-credit{order:0 !important;margin:4px 10px 0 !important;font-size:10px !important}
.td-pick-b{padding:10px 12px 12px;display:flex;flex-direction:column;gap:5px}
.td-pick-l{font-size:11px;font-weight:700;color:#4e6535}
.td-pick-n{font-size:17px;font-weight:800;color:#2a3820;line-height:1.3}
.td-pick-n span{font-size:11px;font-weight:600;color:#9a9088;margin-left:6px}
.td-pick-k{font-size:12px;color:#1a4a70;background:#e8f2fb;border-radius:8px;padding:5px 8px}
.td-pick-f{font-size:12px;color:#5a5248;line-height:1.6}
.td-pick-f b{display:block;color:#2a3820;font-size:12px}
.td-pick-r{font-size:11.5px;color:#3a5828}
@media(max-width:680px){.td-pick-g{grid-template-columns:1fr}.td-pick-img{height:170px}}
.td-index{background:white;border-radius:14px;border:1px solid #e0dbd4;padding:14px;margin-bottom:12px;overflow-x:auto}
.td-index table{border-collapse:collapse;width:100%;min-width:520px;font-size:12px}
.td-index th,.td-index td{padding:6px 6px;border-bottom:1px solid #f0ede8;text-align:left;white-space:nowrap}
.td-index th{font-size:10.5px;color:#7a7068;font-weight:600}
.td-index td a{color:#2a3820;font-weight:700;text-decoration:none}
.td-gh{font-size:17px;font-weight:800;color:#2a3820;margin:22px 0 4px}
.td-gl{font-size:13px;color:#5a5248;line-height:1.7;margin-bottom:10px}
.td-card{background:white;border-radius:16px;border:1px solid #e0dbd4;margin-bottom:16px;padding:18px 18px 16px}
.td-name{font-size:19px;line-height:1.4;margin-bottom:12px;display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 10px}
.td-no{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:28px;border-radius:50%;background:#4e6535;color:#fff;font-size:14px;font-weight:800;align-self:center}
.td-name a{color:#2a3820;text-decoration:none}
.td-sub{flex-basis:100%;font-size:12px;font-weight:400;color:#8a8078}
.td-photo{margin:0 0 14px}
.td-photo-img{width:100%;height:220px;object-fit:cover;border-radius:12px;display:block}
.td-photo .ym-photo-credit{order:0 !important;margin:5px 2px 0 !important;font-size:10.5px !important}
.td-key{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px}
.td-key div{background:#f6f4ef;border-radius:10px;padding:9px 10px}
.td-key span{display:block;font-size:11px;color:#8a8078;margin-bottom:2px}
.td-key b{font-size:15px;color:#2a3820}
.td-sec{margin-bottom:16px}
.td-h{font-size:13px;font-weight:800;color:#2a3820;margin-bottom:7px}
.td-path{font-size:13px;color:#1a4a70;background:#e8f2fb;border-radius:10px;padding:10px 12px;line-height:1.9}
.td-line{font-size:11px;color:#4a6a88;background:#fff;border-radius:4px;padding:1px 5px;margin:0 2px}
.td-notes{list-style:none;margin:8px 0 0;padding:0}
.td-notes li{font-size:12px;color:#6a6258;line-height:1.75;margin-bottom:6px;padding-left:12px;position:relative}
.td-notes li:before{content:"";position:absolute;left:2px;top:.75em;width:4px;height:4px;border-radius:50%;background:#b8ae9e}
.td-walk{font-size:13px;color:#3a5828;background:#f0f6e8;border-radius:10px;padding:10px 12px;line-height:1.7}
.td-walk b{display:block;font-weight:700}
.td-walk span{font-size:12.5px;color:#5a7048}
.td-last{font-size:13px;color:#3a342c;border:1px solid #e6dcc4;background:#fffaf0;border-radius:10px;padding:10px 12px;line-height:1.75}
.td-last b{display:block;font-size:13px;font-weight:800;color:#7a5a20;margin-bottom:4px}
.td-last-walk{border-color:#cfe0c0;background:#f4f9ef}
.td-last-walk b{color:#3a5828}
.td-last-pending{color:#7a7068}
.td-last-t{border-collapse:collapse;width:100%;margin:2px 0 8px}
.td-last-t th,.td-last-t td{font-size:12.5px;padding:7px 5px;border-bottom:1px solid #f0e6d0;text-align:left;line-height:1.6}
.td-last-t td:nth-child(2),.td-last-t td:nth-child(3),.td-last-t th:nth-child(2),.td-last-t th:nth-child(3){white-space:nowrap;text-align:center;width:3.6em}
.td-last-t td:nth-child(2),.td-last-t td:nth-child(3){font-weight:700;font-size:14px}
.td-last-t th{font-size:11px;color:#9a8a60;font-weight:600}
.td-last-n,.td-last-s{font-size:11.5px;color:#7a7068;line-height:1.75;margin-top:6px}
.td-last-s a{color:#4a6038}
.td-feat{list-style:none;margin:0;padding:0}
.td-feat li{font-size:13px;color:#5a5248;line-height:1.8;margin-bottom:10px}
.td-feat b{display:block;color:#2a3820}
.td-link{display:block;font-size:13px;font-weight:700;color:#4a6038;text-decoration:none;background:#f0f6e8;border-radius:10px;padding:11px 12px;text-align:center}
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
@media(max-width:420px){.td-card{padding:16px 14px 14px}.td-key{gap:6px}.td-key div{padding:8px 8px}.td-key b{font-size:14px}.td-photo-img{height:190px}}
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
            r = chosen_route(m)
            # 一覧の欄に出す行（lastBus の indexRow。無ければ最後の行）。ケーブルカーの最終が先に来る山などで使う
            lbs = last_short(lb)
            idx_rows.append('<tr><td>%d</td><td><a href="#m-%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                n, E(i), E(m['name']), E(m.get('difficulty')), E(hm(dep_time(m))), E(yen(dep_fare(m))), E(r.get('time')), E(lbs)))
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
    fast = sorted((D[i] for i in sel), key=lambda m: dep_time(m))[:3]
    cheap = sorted((D[i] for i in sel), key=lambda m: dep_fare(m))[:3]
    hy = [D[i] for i in cfg['groups'][2]['ids']]
    faqs = [
        ('電車だけで行ける日帰り登山は、どこがおすすめですか？',
         'はじめてなら、新宿から近い%sがおすすめです。どれも電車・バスで2時間以内に登山口に着きます。この記事では、はじめての電車登山・しっかり歩く日帰り・電車で行く百名山の3つに分けて%d山を紹介しています。'
         % ('・'.join('%s（%s）' % (m['name'], hm(dep_time(m))) for m in fast), total)),
        ('交通費が安いのはどの山ですか？',
         '新宿からの片道の運賃が安いのは、%sです。運賃はこの記事の各山に、新宿・大宮・横浜からの値を載せています。'
         % '・'.join('%s（%s）' % (m['name'], yen(dep_fare(m))) for m in cheap)),
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
            % (total, fast[0]['name'], hm(dep_time(fast[0])), hy[-1]['name'], hm(dep_time(hy[-1]))))
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
        picks_html(cfg, D),
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
        style, '</head>', '<body>', MARK, header, main_html, footer, '<script src="/assets/js/to-top.js?v=20261025a" defer></script>', '<script src="/assets/js/card-photos.js?v=20261030" defer></script>', '<script src="/assets/js/card-photo-credits.js?v=20261031" defer></script>', '</body>', '</html>', ''])
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
