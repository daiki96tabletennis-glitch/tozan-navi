#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋の公式サイト・予約ページの文から、「予約の開始」の書き方を型どおりに読み取る（小屋ごとの設定なしで全小屋に当てる）。

書き方の型は、すでに予約の開始が分かっている小屋の公式ページを調べて決めた（python3 scripts/huts_patterns.py --analyze で再集計できる）。
  A. 一斉解放型・予約語が先　「2026年の予約受付は4月1日（水）10時より開始」「ご予約は2月1日より承ります」
  B. 一斉解放型・日付が先　　「5月12日午前9時より受付開始」「3月18日(水)10:00から予約受付を開始します」
  C. 見出し＋日付　　　　　　「予約受付開始：5月11日(月）午前9時」「受付開始 5月26日（火）10:00〜」
  R. 何日前・何か月前解放型　「宿泊日の1か月前から」「3ヶ月前の同日より」「前月同日の午前7時より」「90日前から予約可能」
  M. 月ごと解放型　　　　　　「宿泊月の前月1日から」「利用月の2か月前の1日」
書かれている場所は、トップページのお知らせ、予約・宿泊案内のページ、料金のページ、外部の予約サイトの4つ（PDFや画像の中は読めない）。

読み取った候補には点数を付ける。テント・団体・ツアー・個室・冬季だけの日付、キャンセルや締切の日付、営業開始日を、予約の開始と取り違えないように減点する。
自動で使ってよいかどうかは huts_auto.py が決める（前の年の値との照合など）。このファイルは候補を出すだけ。

使い方：
  python3 scripts/huts_patterns.py --analyze   分かっている小屋で、型がどれだけ当たるかを集計する
  python3 scripts/huts_patterns.py --scan      全小屋の候補を一覧にする（データは書き換えない）
"""
import json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

WD = r'(?:\s*[（(]\s*[月火水木金土日祝・]{1,3}\s*[）)])?'
TIME = r'(?:\s*(午前|午後|AM|PM|am|pm|朝)?\s*(\d{1,2})\s*(?:時|:)\s*(\d{2})?\s*分?|\s*(正午))?'
DATE = r'(?:(20\d\d)\s*年\s*)?(?<![\d/.])(\d{1,2})\s*(?:月|/)\s*(\d{1,2})(?![\d/])\s*日?' + WD + TIME
BOOK = r'(?:予約|受付|受け付け|お申込み|申込)'
START = r'(?:より|から|～|〜|スタート|開始|承り|受け付け|受付)'
PAT_A = re.compile(BOOK + r'[^。！!\n]{0,40}?' + DATE + r'[^。！!\n]{0,14}?' + START)
PAT_B = re.compile(DATE + r'\s*(?:より|から|～|〜)?[^。！!\n]{0,24}?' + BOOK + r'[^。！!\n]{0,16}?(?:開始|スタート|承|いたします|致します|します|可能)')
PAT_C = re.compile(r'(?:予約|受付)(?:受付)?(?:開始|スタート)(?:日時?|日)?\s*[:：は]?\s*' + DATE)
MON = r'(?:か月|ヶ月|カ月|ケ月|ヵ月|箇月)'
REL1 = re.compile(r'(?:ご?宿泊|ご?利用|チェックイン|お泊り|お泊まり)(?:予定)?日?\s*の?\s*(\d{1,3})\s*(' + MON + r'|日|週間)\s*前')
REL2 = re.compile(r'(\d{1,2})\s*' + MON + r'\s*前\s*の?\s*(?:同日|同じ日)')
REL3 = re.compile(r'前月\s*(?:の)?\s*(?:同日|同じ日)')
REL4 = re.compile(r'(\d{1,3})\s*(日|' + MON + r')\s*前\s*(?:の\s*\d{1,2}\s*(?:時|:)\S{0,4})?\s*(?:から|より)\s*(?:ご?予約|受付)')
MONTHLY = re.compile(r'(?:宿泊|利用)\s*月\s*の\s*(?:(\d)\s*' + MON + r'\s*前|前月)\s*の?\s*(\d{1,2})\s*日')
NEG = [(r'キャンセル|取消|取り消し|締切|締め切|〆切|変更は|料金改定|価格改定|値上げ', -5), (r'テント|幕営|キャンプ', -2), (r'団体|ツアー|旅行会社|名様以上|名以上', -2),
       (r'個室', -1), (r'冬季|冬期|年末年始|GW|ゴールデンウィーク|残雪期', -1), (r'営業開始|営業期間|オープン|小屋開け|開山', -2),
       (r'まで(?:に|の|。|$)', -2), (r'終了|終わり|満室', -2), (r'求人|アルバイト|スタッフ募集|イベント|講習|バス|ロープウェイ|ゴンドラ', -4)]
ERA = re.compile(r'令和\s*(\d{1,2})\s*年')


def norm(s):
    return unicodedata.normalize('NFKC', s or '').replace('〜', '～')


def _year_near(lines, i):
    """その行の年（書いてあれば）。無ければ前の3行・後ろの1行から探す"""
    for j in (i, i - 1, i - 2, i - 3, i + 1):
        if 0 <= j < len(lines):
            m = re.search(r'(20\d\d)\s*年', lines[j]) or re.search(r'(20\d\d)\s*(?:シーズン|season)', lines[j], re.I)
            if m:
                return int(m.group(1)), j == i
            e = ERA.search(lines[j])
            if e:
                return 2018 + int(e.group(1)), j == i
    return None, False


def _time(ampm, hh, mi, noon):
    if noon:
        return '12:00'
    if not hh:
        return None
    h = int(hh)
    if ampm in ('午後', 'PM', 'pm') and h < 12:
        h += 12
    if h > 24:
        return None
    return '%d:%s' % (h, mi or '00')


def extract(raw_lines):
    """ページの行のリスト → 候補のリスト。fix：{'t':'fix','y','m','d','time','score','line','pat'}／rel：{'t':'rel','u','n',...}／mon"""
    lines = [norm(l) for l in raw_lines]
    out = []
    for i, t in enumerate(lines):
        if len(t) > 240 or len(t) < 6:
            continue
        ctx = ' '.join(lines[max(0, i - 2):i + 1])
        has_book = bool(re.search(BOOK, t))
        # 一斉解放型
        for pat, name in ((PAT_A, 'A'), (PAT_B, 'B'), (PAT_C, 'C')):
            for m in pat.finditer(t):
                g = m.groups()
                y, mo, d = g[0], int(g[1]), int(g[2])
                if not (1 <= mo <= 12 and 1 <= d <= 31):
                    continue
                yy, same = (int(y), True) if y else _year_near(lines, i)
                score = 3 + (2 if same else 1 if yy else 0) + (1 if g[4] or g[6] else 0) + (1 if name == 'C' else 0)
                seg = t[max(0, m.start() - 12):m.end() + 12]
                dm = re.search(r'(\d{1,2})\s*(?:月|/)\s*(\d{1,2})\s*日?' + WD, t[m.start():m.end()])
                tail = t[m.start() + (dm.end() if dm else 0):][:14] if name != 'A' else t[m.end() - 6:m.end() + 12]
                if re.match(r'\s*(?:\d{1,2}\s*(?:時|:)\s*\d{0,2}分?)?\s*(?:以降|泊|の?ご?宿泊|ご?利用分|まで|迄|の?ご?予約\s*(?:→|は|について))', tail) or re.search(r'分まで|泊まで|宿泊分まで|まで[、,。]', seg):
                    score -= 4
                if re.search(r'→|⇒', t[:m.start()][-6:]) is None and re.search(r'のご予約\s*(?:→|⇒)', t[m.end() - 2:m.end() + 10]):
                    score -= 4
                for rx, pen in NEG:
                    if re.search(rx, seg):
                        score += pen
                    elif re.search(rx, t):
                        score += pen / 2.0
                out.append({'t': 'fix', 'y': yy, 'm': mo, 'd': d, 'time': _time(g[3], g[4], g[5], g[6]), 'score': score, 'line': raw_lines[i].strip(), 'pat': name})
        # 何日前・何か月前解放型
        if has_book or re.search(BOOK, ctx):
            rel = None
            m = REL1.search(t) or REL4.search(t)
            if m:
                rel = (int(m.group(1)), 'm' if re.fullmatch(MON, m.group(2)) else 'w' if m.group(2) == '週間' else 'd')
            else:
                m = REL2.search(t)
                if m:
                    rel = (int(m.group(1)), 'm')
                elif REL3.search(t):
                    m = REL3.search(t)
                    rel = (1, 'm')
            if rel and 0 < rel[0] <= 400:
                score = 4 + (1 if has_book else 0)
                # 「3日前まで」「10日前…契約の解除」は予約の締切・取消の話
                if re.match(r'\s*(?:[（(][^）)]{0,8}[）)])?\s*(?:まで|迄|以降は|を過ぎ)', t[m.end():m.end() + 14]) or re.search(r'解除|違約|取消料|キャンセル料', t):
                    score -= 5
                for rx, pen in NEG[:1] + NEG[6:7]:
                    if re.search(rx, t[max(0, m.start() - 10):m.end() + 14]):
                        score += pen
                tm = re.search(r'(午前|午後|AM|PM|朝)?\s*(\d{1,2})\s*(?:時|:)\s*(\d{2})?', t[m.end():m.end() + 14])
                out.append({'t': 'rel', 'n': rel[0], 'u': rel[1], 'time': _time(tm.group(1), tm.group(2), tm.group(3), None) if tm else None,
                            'score': score, 'line': raw_lines[i].strip(), 'pat': 'R'})
            m = MONTHLY.search(t)
            if m:
                out.append({'t': 'mon', 'n': int(m.group(1) or 1), 'd': int(m.group(2)), 'score': 5, 'line': raw_lines[i].strip(), 'pat': 'M'})
    # 同じ内容はまとめ、点数の高い順に
    seen, uniq = set(), []
    for c in sorted(out, key=lambda x: -x['score']):
        key = (c['t'], c.get('y'), c.get('m'), c.get('d'), c.get('n'), c.get('u'))
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq


LIST_REL = re.compile(r'(\d{1,2})\s*' + MON + r'\s*前\s*(?:から)?\s*(?:の)?\s*(?:予約制|予約|受付)|(?:予約制|予約)\s*[（(]\s*(\d{1,2})\s*' + MON + r'\s*前')
LIST_D = r'(?<![\d/～~\-])(\d{1,2})\s*/\s*(\d{1,2})(?![\d/])' + WD + r'\s*(?:(\d{1,2})\s*[:：]\s*(\d{2}))?'
LIST_FIX1 = re.compile(LIST_D + r'\s*(?:～|~|から|より)(?!\s*(?:20\d\d\s*/\s*)?\d{1,2}\s*(?:/|月))\s*[^、。＊]{0,14}?(?:予約受付|受付開始|予約開始|予約$|予約\s|受付$|予約可)')                    # 5/20（水）7:00～Webで予約受付開始
LIST_FIX2 = re.compile(r'(?:予約|受付)(?:受付)?\s*(?:開始)?\s*[:：は]\s*' + LIST_D + r'\s*(?:～|~|から|より)?(?!\s*\d{1,2}\s*/)')   # 宿泊予約：5/8（金）9:00～開始 ／ Web予約は2/20～
LIST_FIX3 = re.compile(LIST_D + r'\s*(?:～|~|から|より)\s*(?:完全)?予約制')                                                   # 3/18～完全予約制


def extract_list(text):
    """山小屋の一覧（長野県のポータル・山と溪谷の山小屋リスト）の1行の書き方から読む。
    「2026/4/27～11/3、1か月前予約制」「＊宿泊予約：5/8（金）9:00～開始」「5/20（水）7：00～Webで予約受付開始」「Web予約は2/20～」「3/18～完全予約制」
    営業期間（a～b）の日付や、テント・個室・年越し・夏季だけの但し書きの日付は、予約の開始として読まない"""
    t = norm(text)
    ym = re.match(r'\s*(20\d\d)', t)
    year = int(ym.group(1)) if ym else None
    out = []
    for seg in re.split(r'[、,＊*※]|\s{2,}', t):
        seg = seg.strip()
        if not seg:
            continue
        m = LIST_REL.search(seg)
        if m:
            out.append({'t': 'rel', 'n': int(m.group(1) or m.group(2)), 'u': 'm', 'time': None, 'score': 6, 'line': text.strip(), 'pat': 'L'})
            continue
        if re.search(r'テント|幕営|キャンプ|個室|年越し|年末年始|団体|夏季シーズン|残雪期|GW|まで|休業|休館|改定', seg):
            continue
        for pat in (LIST_FIX1, LIST_FIX2, LIST_FIX3):
            m = pat.search(seg)
            if m:
                mo, d = int(m.group(1)), int(m.group(2))
                if 1 <= mo <= 12 and 1 <= d <= 31:
                    out.append({'t': 'fix', 'y': year, 'm': mo, 'd': d, 'time': ('%d:%s' % (int(m.group(3)), m.group(4))) if m.group(3) else None,
                                'score': 6, 'line': text.strip(), 'pat': 'L'})
                break
    return out


def pages_of(h):
    """その小屋で見に行くページ：公式サイト（と1階層先の予約・案内のページ）、予約の案内の固定ページ"""
    urls = []
    for u in ((h.get('officialUrl') or '').strip(), (h.get('bookingSourceUrl') or '').strip()):
        if u and u not in urls and not re.search(r'yamatan\.net|yamakei-online', u):
            urls.append(u)
    return urls


def candidates(h, page_lines, all_names=()):
    """その小屋の候補：一覧の出典の文（openText）→ 公式サイト・予約の案内のページ、の順に読む。
    同じサイトをグループの小屋で共有していることがあるので、ほかの小屋の名前だけが出てくる行は減点する"""
    out = []
    for c in extract_list(h.get('openText') or ''):
        c['url'] = h.get('sourceUrl') or ''
        c['src'] = 'list'
        out.append(c)
    mine = norm(re.sub(r'[（(].*?[）)]', '', h['name'])).replace(' ', '')
    short = mine[-4:] if len(mine) > 4 else mine
    others = [norm(re.sub(r'[（(].*?[）)]', '', n)).replace(' ', '') for n in all_names if n != h['name']]
    for u in pages_of(h):
        for c in extract(page_lines(u)):
            ln = norm(c['line']).replace(' ', '')
            if short not in ln and any(len(o) >= 4 and o in ln for o in others):
                c['score'] -= 3
            c['url'] = u
            c['src'] = 'site'
            out.append(c)
    out.sort(key=lambda x: -x['score'])
    return out


def main():
    import huts_auto as ha
    import huts_rules as hr
    huts = json.load(open(os.path.join(ROOT, 'data', 'huts.json'), encoding='utf-8'))['huts']
    mode = '--analyze' if '--analyze' in sys.argv else '--scan'
    stat = {'fix': [0, 0, 0], 'rel': [0, 0, 0], 'mon': [0, 0, 0]}      # 対象・ページに候補あり・最上位の候補が正解
    pats, wrong, new = {}, [], []
    for h in huts:
        if h.get('bookingNone') or not pages_of(h):
            continue
        a = h.get('auto') or {}
        rule = hr.derive(h['name'], h.get('bookingStart'), (a.get('bookingStartWeb') or {}).get('value'), (a.get('bookingWindow') or {}).get('value'))
        cs = [c for c in candidates(h, ha.page_lines, [x['name'] for x in huts]) if c['score'] >= 5]
        if rule and rule['t'] in stat:
            st = stat[rule['t']]
            st[0] += 1
            same = [c for c in cs if c['t'] == rule['t']]
            if rule['t'] == 'fix':
                good = [c for c in same if (c['m'], c['d']) == (rule['m'], rule['d'])]
            elif rule['t'] == 'rel':
                good = [c for c in same if (c['n'], c['u']) == (rule['n'], rule['u']) or (rule['u'] == 'w' and c['u'] == 'd' and c['n'] == rule['n'] * 7)]
            else:
                good = [c for c in same if c['n'] == rule['n']]
            if good:
                st[1] += 1
                pats[good[0]['pat']] = pats.get(good[0]['pat'], 0) + 1
                if same and same[0] is good[0]:
                    st[2] += 1
                else:
                    wrong.append((h['name'], rule, same[0]))
            elif same:
                wrong.append((h['name'], rule, same[0]))
        elif not rule and cs:
            new.append((h['name'], cs[:2]))
    print('■ 分かっている小屋での当たり方（対象／ページに正しい候補あり／最上位の候補が正しい）')
    for k, v in stat.items():
        print('  %s：%d／%d／%d' % ({'fix': '一斉解放型', 'rel': '何日前型', 'mon': '月ごと型'}[k], v[0], v[1], v[2]))
    print('  当たった型の内訳：', pats)
    print('■ 最上位の候補がいまのデータと違う小屋（%d軒）' % len(wrong))
    for n, r, c in wrong:
        print('  ', n, '｜いま', {k: r[k] for k in r if k in ('t', 'y', 'm', 'd', 'n', 'u')}, '｜候補', {k: c[k] for k in c if k in ('t', 'y', 'm', 'd', 'n', 'u', 'score')}, '｜', c['line'][:80])
    if mode == '--scan':
        print('■ 予約の開始が未登録の小屋で見つかった候補（%d軒）' % len(new))
        for n, cs in new:
            for c in cs:
                print('  ', n, '｜', {k: c[k] for k in c if k in ('t', 'y', 'm', 'd', 'time', 'n', 'u', 'score')}, '｜', c['line'][:100], '｜', c['url'])


if __name__ == '__main__':
    main()
