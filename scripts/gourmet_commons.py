#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事「山の茶屋・山小屋グルメ」の写真を Wikimedia Commons から探して取り込むツール。

  python3 scripts/gourmet_commons.py all
      写真がまだ無い項目すべてを、お店・山小屋の名前で探し、見比べ用のページ（.claude/gourmet_commons/index.html）を作る
  python3 scripts/gourmet_commons.py search <key> [追加の検索語 ...]
      1項目だけ探す（見比べ用のページは .claude/gourmet_commons/<key>.html）。英語の名前（例：Nabewari）なども足せる
      いつも使う語は data/mountain_gourmet.json の項目に commonsQueries（配列）で書いておける
      料理名などで見つかった写真は、たいてい別のお店のもの。そのお店の写真として使わない（ページに注意を出す）
  python3 scripts/gourmet_commons.py apply <key> <番号> [写真の説明]
      選んだ候補（Commons の幅約1200pxの縮小版）を images/articles/mountain-gourmet/<key>.jpg に保存し、
      data/mountain_gourmet.json の image（作者・ライセンス・Commons のページ）を書き込む
      料理ではなく建物の写真を選んだときは、写真の説明（例：「みくりが池温泉の売店」）を付ける（画像の代替テキストになる）
  python3 scripts/gourmet_commons.py clear <key>
      その項目の写真を外す（ファイルは消さない）

候補は商用で使えるライセンス（CC0・パブリックドメイン・CC BY・CC BY-SA）だけ。
選ぶのは人（そのお店・料理の写真かを確かめてから apply する）。自動では選ばない。
apply のあとは python3 scripts/gen_gourmet_article.py で記事を作り直す（写真の下に作者・ライセンス・Commons へのリンクが出る）。
"""
import json, os, re, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'mountain_gourmet.json')
IMG_DIR = os.path.join(ROOT, 'images', 'articles', 'mountain-gourmet')
WORK = os.path.join(ROOT, '.claude', 'gourmet_commons')     # 候補の一覧（公開のコピーには含めない）
API = 'https://commons.wikimedia.org/w/api.php'
UA = 'YamatchGourmetTool/1.0 (https://tozan-navi.com/)'
OK_LICENSE = re.compile(r'^(CC0( 1\.0)?|Public domain|PD|CC BY(-SA)?( [0-9.]+)?( [a-z]{2,3})?)$', re.I)


def api(params):
    params = dict(params, format='json')
    req = urllib.request.Request(API + '?' + urllib.parse.urlencode(params), headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def strip_html(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or '')).strip()


def load():
    return json.load(open(DATA, encoding='utf-8'))


def save(d):
    json.dump(d, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def item(d, key):
    for x in d['items']:
        if x['key'] == key:
            return x
    sys.exit('その key はありません：' + key)


def queries(it, extra):
    """(検索語, 種類)。name＝お店の名前（・で分けたものも）、mountain＝山名（茶屋が写っていることがある）、extra＝追加の語"""
    qs = [(it['place'], 'name')]
    parts = [x.strip() for x in it['place'].split('・')]
    if len(parts) > 1:
        qs += [(x, 'name') for x in parts]
    m = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    m = m if isinstance(m, list) else m.get('mountains', m)
    mt = next((x for x in m if x.get('id') == it['mountainId']), None)
    if mt and mt.get('name'):
        qs.append((mt['name'] + ' 茶屋' if it['group'] == 'teahouse' else mt['name'] + ' 山小屋', 'mountain'))
    qs += [(w, 'extra') for w in (it.get('commonsQueries') or []) + list(extra)]
    return qs


def find(it, extra):
    seen, cands = set(), []
    for w, kind in queries(it, extra):
        res = api({'action': 'query', 'generator': 'search', 'gsrnamespace': 6, 'gsrsearch': w, 'gsrlimit': 30,
                   'prop': 'imageinfo', 'iiprop': 'url|size|extmetadata|mime', 'iiurlwidth': 1200})
        for p in sorted(((res.get('query') or {}).get('pages') or {}).values(), key=lambda p: p.get('index', 0)):
            if p['title'] in seen:
                continue
            seen.add(p['title'])
            ii = (p.get('imageinfo') or [{}])[0]
            if ii.get('mime') not in ('image/jpeg', 'image/png', 'image/webp'):
                continue
            md = ii.get('extmetadata') or {}
            lic = strip_html((md.get('LicenseShortName') or {}).get('value'))
            if not OK_LICENSE.match(lic) or strip_html((md.get('Restrictions') or {}).get('value')):
                continue
            cands.append({'title': p['title'], 'query': w, 'kind': kind, 'license': lic,
                          'licenseUrl': strip_html((md.get('LicenseUrl') or {}).get('value')),
                          'author': strip_html((md.get('Artist') or {}).get('value')) or '作者不明',
                          'description': strip_html((md.get('ImageDescription') or {}).get('value'))[:160],
                          'date': strip_html((md.get('DateTimeOriginal') or {}).get('value'))[:10],
                          'width': ii.get('width'), 'height': ii.get('height'),
                          'thumb': ii.get('thumburl') or ii.get('url'), 'pageUrl': ii.get('descriptionurl')})
    os.makedirs(WORK, exist_ok=True)
    json.dump(cands, open(os.path.join(WORK, it['key'] + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return cands


def E(s):
    return (str(s or '')).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def section(it, cands):
    cards = []
    for i, c in enumerate(cands, 1):
        warn = {'name': '', 'mountain': '<div class="w2">山名で見つかった写真（お店が写っているか確かめる）</div>'}.get(
            c['kind'], '<div class="w">追加の語で見つかった写真（料理名なら別のお店の可能性が高い）</div>')
        cards.append('<div class="c"><b>%d</b> %s%s<img src="%s" loading="lazy"><small>%s ／ %s ／ %s ／ %s×%s<br>%s</small>'
                     '<a href="%s" target="_blank">Commons のページを開く</a></div>' % (
                         i, E(c['title'][5:]), warn, E(c['thumb']), E(c['author']), E(c['license']), E(c['date']),
                         c['width'], c['height'], E(c['description']), E(c['pageUrl'])))
    return ('<h2>%s ― %s（%s）</h2><p class="cmd">取り込み：<code>python3 scripts/gourmet_commons.py apply %s 番号</code>　料理：%s</p>%s' % (
        E(it['place']), E(it['key']), len(cands), E(it['key']), E(it['food']), ''.join(cards) or '<p>候補なし（英語の名前などを足して search で探す）</p>'))


def page(name, body):
    out = os.path.join(WORK, name)
    open(out, 'w', encoding='utf-8').write(
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>グルメ写真の候補</title>'
        '<style>body{font-family:sans-serif;margin:16px;background:#f0ede5}h2{border-top:2px solid #4e6535;padding-top:12px;margin-top:28px}'
        '.c{display:inline-block;vertical-align:top;width:300px;margin:6px;padding:8px;background:#fff;border:1px solid #ddd;font-size:13px}'
        '.c img{display:block;width:100%;height:200px;object-fit:contain;background:#eee;margin:6px 0}.w{color:#b33;font-weight:bold}.w2{color:#a60;font-weight:bold}'
        '.cmd code{background:#fff;padding:2px 6px}</style>'
        '<h1>山グルメ記事の写真の候補（Wikimedia Commons）</h1><p>そのお店・料理の写真かを確かめてから選ぶ。料理の写真が無いときは、お店の建物の写真でもよい。</p>' + body)
    return os.path.relpath(out, ROOT)


def cmd_search(key, extra):
    it = item(load(), key)
    cands = find(it, extra)
    print('%s（%s）：候補 %d 件' % (key, it['place'], len(cands)))
    for i, c in enumerate(cands, 1):
        print('  %2d. %s%s ｜ %s ｜ %s' % (i, {'name': '', 'mountain': '[山名] '}.get(c['kind'], '[追加] '), c['title'][5:70], c['author'][:30], c['license']))
    print('見比べ用のページ：' + page(key + '.html', section(it, cands)))


def cmd_all():
    body = []
    for it in load()['items']:
        if (it.get('image') or {}).get('src'):
            continue
        cands = find(it, [])
        print('%-20s %s：候補 %d 件' % (it['key'], it['place'], len(cands)))
        body.append(section(it, cands))
    print('見比べ用のページ：' + page('index.html', ''.join(body)))


def cmd_apply(key, n, alt=None):
    f = os.path.join(WORK, key + '.json')
    if not os.path.exists(f):
        sys.exit('先に search か all を実行してください')
    cands = json.load(open(f, encoding='utf-8'))
    c = cands[int(n) - 1]
    if c['kind'] != 'name':
        print('注意：お店の名前以外で見つかった写真です。そのお店の写真か、Commons のページで確かめてください')
    os.makedirs(IMG_DIR, exist_ok=True)
    out = os.path.join(IMG_DIR, key + '.jpg')
    data = urllib.request.urlopen(urllib.request.Request(c['thumb'], headers={'User-Agent': UA}), timeout=60).read()
    if c['thumb'].lower().split('?')[0].endswith(('.jpg', '.jpeg')):
        open(out, 'wb').write(data)
    else:
        tmp = out + '.tmp'
        open(tmp, 'wb').write(data)
        os.system('sips -s format jpeg "%s" --out "%s" >/dev/null 2>&1' % (tmp, out))
        os.remove(tmp)
    d = load()
    it = item(d, key)
    it['image'] = {'src': '/images/articles/mountain-gourmet/%s.jpg' % key,
                   'alt': alt or (it.get('image') or {}).get('alt') or it['place'],
                   'credit': c['author'], 'license': c['license'], 'licenseUrl': c['licenseUrl'], 'pageUrl': c['pageUrl'],
                   'source': 'wikimedia_commons', 'commonsTitle': c['title']}
    save(d)
    print('取り込みました：%s ← %s（%s / %s）' % (os.path.relpath(out, ROOT), c['title'], c['author'], c['license']))
    print('次に：python3 scripts/gen_gourmet_article.py')


def cmd_clear(key):
    d = load()
    it = item(d, key)
    it['image'] = {'src': None, 'alt': (it.get('image') or {}).get('alt') or it['place'], 'credit': None}
    save(d)
    print('外しました：' + key)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a == ['all']:
        cmd_all()
    elif len(a) >= 2 and a[0] == 'search':
        cmd_search(a[1], a[2:])
    elif len(a) in (3, 4) and a[0] == 'apply':
        cmd_apply(a[1], a[2], a[3] if len(a) == 4 else None)
    elif len(a) == 2 and a[0] == 'clear':
        cmd_clear(a[1])
    else:
        print(__doc__)
