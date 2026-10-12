#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""予約の開始日を公式ページから毎年読み取るための「レシピ」を、いまの公式ページの文から作る補助スクリプト。
使い方：python3 scripts/huts_make_recipes.py            （候補を表示するだけ）
        python3 scripts/huts_make_recipes.py --write    （確かめが通ったものを data/huts_recipes.json に足す）

やること：
  1. 予約の開始が「一斉解放型」（huts_rules の fix・年つき）で、まだレシピの無い小屋を対象にする
  2. その小屋の公式ページ（と1階層先の予約・案内のページ）から、いまデータにある日付（例：3月18日）と「予約」「受付」を含む1行を探す
  3. その行の数字を「何の数字でもよい」に置き換えた正規表現を作る（年・月・日・時・分は取り出す）
  4. 作った正規表現をページ全体に当て直し、当たるのがその1行だけで、取り出した月日がいまのデータと同じときだけ採用する
来年、公式ページが同じ言い回しで日付だけ変えれば、新しい日付が読める。言い回しが変わると読めなくなり、定期更新の報告に出る。
読み取った値は huts_auto.py の確認（年が今年か来年・実在する日付・前の年から45日以内）を通ったものだけ使われる。
"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import huts_auto as ha
import huts_rules as hr

Z = str.maketrans('０１２３４５６７８９：／', '0123456789:/')
DG = r'[0-9０-９]'


def target_huts():
    huts = json.load(open(os.path.join(ROOT, 'data', 'huts.json'), encoding='utf-8'))['huts']
    rp = os.path.join(ROOT, 'data', 'huts_recipes.json')
    have = {r['hut'] for r in json.load(open(rp, encoding='utf-8'))['recipes'] if r['field'] in ('bookingStart', 'bookingStartDate')}
    out = []
    for h in huts:
        if h.get('bookingNone') or h['name'] in have or not (h.get('officialUrl') or '').strip():
            continue
        a = h.get('auto') or {}
        r = hr.derive(h['name'], (a.get('bookingStart') or {}).get('value') or h.get('bookingStart'),
                      (a.get('bookingStartWeb') or {}).get('value'), (a.get('bookingWindow') or {}).get('value'))
        if r and r['t'] == 'fix' and r.get('y'):
            out.append((h, r))
    return out


def make(line, m, d):
    """line の中の「m月d日」（または m/d）を見つけ、その前後を使った正規表現と、取り出す番号を返す。作れなければ None"""
    t = line
    dm = re.search(r'(?<![0-9０-９])(%s{1,2})\s*(月|/|／)\s*(%s{1,2})\s*(日)?' % (DG, DG), t)
    hit = None
    for x in re.finditer(r'(?<![0-9０-９/／])(%s{1,2})\s*(月|/|／)\s*(%s{1,2})(?![0-9０-９])' % (DG, DG), t):
        if int(x.group(1).translate(Z)) == m and int(x.group(3).translate(Z)) == d:
            hit = x
            break
    if not hit:
        return None
    a, b = max(0, hit.start() - 28), min(len(t), hit.end() + 22)
    before, after = t[a:hit.start()], t[hit.end():b]

    def lit(s):       # 文字はそのまま、数字の並びは「数字なら何でも」、空白はあってもなくてもよい、（月）などの曜日は何曜日でもよい
        out = ''
        for part in re.split(r'([0-9０-９]+|\s+|[（(]\s*[月火水木金土日祝・]{1,3}\s*[）)])', s):
            if not part:
                continue
            if re.fullmatch(r'[0-9０-９]+', part):
                out += DG + '{1,4}'
            elif part.isspace():
                out += r'\s*'
            elif re.fullmatch(r'[（(]\s*[月火水木金土日祝・]{1,3}\s*[）)]', part):
                out += r'(?:\s*[（(][月火水木金土日祝・]{1,3}[）)])?'
            else:
                out += re.escape(part)
        return out

    groups, rx = {}, ''
    ym = list(re.finditer(r'(?:20|２０)%s{2}' % DG, before))
    if ym:
        y = ym[-1]
        rx += lit(before[:y.start()]) + r'((?:20|２０)%s{2})' % DG + lit(before[y.end():])
        groups['year'] = 1
    else:
        rx += lit(before)
    n = len(groups)
    rx += r'(%s{1,2})\s*%s\s*(%s{1,2})' % (DG, re.escape(hit.group(2)), DG)
    groups['month'], groups['day'] = n + 1, n + 2
    n += 2
    tm = re.match(r'(\s*日?\s*[（(][^）)]{1,3}[）)]|\s*日)?(\s*(?:午前|AM|am|朝)?\s*)(%s{1,2})\s*(時|:|：)\s*(%s{2})?' % (DG, DG), after)
    if not tm and re.match(r'\s*日?\s*(?:[（(][^）)]{1,3}[）)])?\s*正午', after):
        noon = re.match(r'\s*日?\s*(?:[（(][^）)]{1,3}[）)])?\s*正午', after)
        rx += r'\s*日?(?:\s*[（(][^）)]{1,3}[）)])?\s*正午'
        after = after[noon.end():]
        groups['noon'] = True
    if tm and not (tm.group(2) or '').strip() in ('午後', 'PM'):
        rx += (r'\s*日?(?:\s*[（(][^）)]{1,3}[）)])?' if tm.group(1) else '') + lit(tm.group(2) or '') + r'(%s{1,2})\s*%s' % (DG, re.escape(tm.group(4)))
        groups['hour'] = n + 1
        n += 1
        if tm.group(5):
            rx += r'\s*(%s{2})' % DG
            groups['minute'] = n + 1
            n += 1
        rest = after[tm.end():]
    else:
        rest = after
    rx += lit(rest[:14])
    return rx, groups


def main():
    write = '--write' in sys.argv
    rp = os.path.join(ROOT, 'data', 'huts_recipes.json')
    data = json.load(open(rp, encoding='utf-8'))
    ok, ng = [], []
    for h, rule in target_huts():
        # 公式サイトのトップ（と、そこから1階層たどれるページ）だけを見る。年ごとに別のURLになるお知らせ記事を直接指すと、翌年は読めないため
        urls = [h['officialUrl'].strip()]
        b = (h.get('bookingSourceUrl') or '').strip()
        if b and b not in urls and not re.search(r'yamatan\.net|yamakei-online|news|topics|article|archives|blog|entry|info_detail|\d{5,}|%[0-9A-Fa-f]{2}', b):
            urls.append(b)          # 予約の案内の固定ページ。お知らせ記事（年ごとに別URL）は除く
        elif b and not re.search(r'yamatan\.net|yamakei-online', b):
            # お知らせ記事そのものは翌年には古くなるので、その一覧のページ（記事URLの1つ上・2つ上）を見る。
            # 一覧に並ぶ記事名や、そこから「予約」の付くリンクを1階層たどった先に、同じ言い回しが出れば読める
            up = re.sub(r'[^/]+/?$', '', b)
            for cand in (up, re.sub(r'[^/]+/$', '', up)):
                if re.match(r'https?://[^/]+/.+', cand) and cand not in urls:
                    urls.append(cand)
        done = False
        for u in urls:
            lines = ha.page_lines(u)
            for l in lines:
                if not re.search(r'予約|受付|受け付け', l) or len(l) > 260:
                    continue
                mk = make(l, rule['m'], rule['d'])
                if not mk:
                    continue
                rx, g = mk
                try:
                    hits = [x for x in lines if re.search(rx, x)]
                except re.error:
                    continue
                mm = re.search(rx, l)
                # 当たる行が複数あるとき（過去の年の案内が残っているページ）は、ページの上から最初に当たるのがこの行のときだけ使う
                if not mm or not hits or hits[0] != l:
                    continue
                noon = g.pop('noon', False)
                vals = {k: int(mm.group(i).translate(Z)) for k, i in g.items()}
                if vals['month'] != rule['m'] or vals['day'] != rule['d'] or (vals.get('year') and vals['year'] != rule['y']):
                    continue
                out = '{%d}月{%d}日' % (g['month'], g['day'])
                if g.get('hour'):
                    out += ' {%d}:%s' % (g['hour'], ('{%d}' % g['minute']) if g.get('minute') else '00')
                if noon:
                    out += ' 12:00'
                out += 'から' + ('（{%d}年）' % g['year'] if g.get('year') else '')
                rec = dict({'hut': h['name'], 'field': 'bookingStartDate', 'url': u, 'regex': rx, 'out': out}, **g)
                if noon:
                    rec['fixedTime'] = '12:00'
                ok.append((rec, l))
                done = True
                break
            if done:
                break
        if not done:
            ng.append(h['name'])
    for rec, l in ok:
        print('○', rec['hut'], '|', l[:110])
        print('    ', rec['regex'][:150], '→', rec['out'], {k: rec[k] for k in ('year', 'month', 'day', 'hour', 'minute') if k in rec})
    print('作れた %d 軒／作れなかった %d 軒：%s' % (len(ok), len(ng), '、'.join(ng)))
    if write and ok:
        data['recipes'].extend(r for r, _ in ok)
        json.dump(data, open(rp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('data/huts_recipes.json に %d 件を追加しました' % len(ok))


if __name__ == '__main__':
    main()
