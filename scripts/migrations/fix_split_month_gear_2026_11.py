"""月の途中で冬山装備に変わる月の装備カードを直す（2026-11-11。運営者の指示「直す」）

gear-data.json のカードは1か月に1組だけで、月の途中で区分が変わる月（燕岳の11月＝16日から冬山装備、
北アルプス・南アルプス・八ヶ岳などの10月＝11日から冬山装備。31山）は前半の軽アイゼン等のカードになっていた。
そのうえ「来月分」のカードの文が「来月から本格的な積雪期」で、切り替わる日と食い違っていた。

- 「来月分」のカード（crampon_next）を、切り替わる日を書いた文と見出し（l）にする
- 切り替わる日からは、山ページ（mountain.js）が翌月（冬山装備）のカードを出す（gen_mountain_pages.py の data-gear-switch）
- 手で作った記事・まとめにある、その山の装備カードの写し（data-gear-variants）も作り直し、data-gear-switch を付け、
  ページの描く処理にも同じ切り替えと見出し（l）を入れる（2026-11-11：コース定数30・40・50、電車で行ける山）
何度流しても同じ結果。このあと gen_mountain_pages.py --all → gen_recommend_gear.py → check_pages.py
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GP = os.path.join(ROOT, 'data', 'gear-data.json')
MP = os.path.join(ROOT, 'data', 'mountains.json')


def main():
    G = json.load(open(GP, encoding='utf-8'))
    n = 0
    for m in json.load(open(MP, encoding='utf-8')):
        cal = m.get('gearCalendar') or []
        for i, v in enumerate(cal):
            if not (isinstance(v, dict) and v.get('before') == 'light_crampons' and v.get('after') == 'winter_gear'):
                continue
            mon, d = i + 1, v['changeDate']
            cards = G[m['id']][str(mon)]
            nx = [c for c in cards if c['c'] == 'crampon_next']
            assert len(nx) == 1 and 'G12' in nx[0]['p'], (m['id'], mon)
            nx[0]['l'] = 'アイゼン(%d日ごろから)' % d
            nx[0]['r'] = ('%d月%d日ごろから本格的な積雪期に入ります。それ以降は12本爪アイゼン・ピッケル・冬山用の登山靴などの冬山装備と、'
                          '雪山の経験が必要です。' % (mon, d))
            n += 1
    with open(GP, 'w', encoding='utf-8') as f:
        json.dump(G, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('直した月', n)
    articles(G)


def variants_attr(md):
    # gen_mountain_pages.render_gear と同じ形
    groups, order = {}, []
    for month in sorted(md.keys(), key=int):
        key = json.dumps(md[month], ensure_ascii=False)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(int(month))
    return json.dumps({k: groups[k] for k in order}, ensure_ascii=False).replace('"', '&quot;')


def switch_of(cal):
    # gen_mountain_pages.gear_closed_attrs と同じ決まり
    return ','.join('%d:%d' % (i + 1, e['changeDate']) for i, e in enumerate(cal)
                    if isinstance(e, dict) and e.get('after') != 'closed' and cal[(i + 1) % 12] == e.get('after'))


JS_MONTH = """    var month = now.getMonth() + 1;
    var cards = null;
"""
JS_SWITCH = """    var month = now.getMonth() + 1;
    var cards = null;
    // 月の途中で区分が変わる月は、切り替わる日から翌月のカードを出す（data-gear-switch="月:日"。2026-11-11）
    (container.getAttribute('data-gear-switch') || '').split(',').forEach(function(x){
      var a = x.split(':');
      if(+a[0] === month && now.getDate() >= +a[1]) month = month % 12 + 1;
    });
"""
JS_LABEL = ('var label = window.GEAR_LABEL[c.c] || c.c;', 'var label = c.l || window.GEAR_LABEL[c.c] || c.c;')


def articles(G):
    MS = {m['id']: m for m in json.load(open(MP, encoding='utf-8'))}
    sw = {k: switch_of(m.get('gearCalendar') or []) for k, m in MS.items()}
    pages = glob.glob(os.path.join(ROOT, 'articles/*/index.html')) + glob.glob(os.path.join(ROOT, 'search/*/index.html'))
    for p in sorted(pages):
        s = open(p, encoding='utf-8').read()
        if '<!-- generated: scripts/gen_line_articles' in s:
            continue  # 路線別の記事は gen_line_articles.py で作り直す
        mids = [k for k in re.findall(r'data-gear-mid="([a-z0-9_-]+)"', s) if sw.get(k) and k in G]
        if not mids:
            continue
        for mid in mids:
            pat = re.compile(r'data-gear-mid="' + mid + r'"(?: data-gear-switch="[^"]*")?([^>]*?data-gear-variants=")[^"]*(")')
            s, k = pat.subn(lambda m: 'data-gear-mid="%s" data-gear-switch="%s"%s%s%s' % (mid, sw[mid], m.group(1), variants_attr(G[mid]), m.group(2)), s)
            assert k == 1, (p, mid, k)
        if JS_SWITCH not in s:
            assert s.count(JS_MONTH) == 1, p
            s = s.replace(JS_MONTH, JS_SWITCH)
        if JS_LABEL[1] not in s:
            assert s.count(JS_LABEL[0]) == 1, p
            s = s.replace(JS_LABEL[0], JS_LABEL[1])
        open(p, 'w', encoding='utf-8').write(s)
        print('記事の写し', os.path.relpath(p, ROOT), ' '.join(mids))


if __name__ == '__main__':
    main()
