#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋の公式サイト・予約サイトから、年ごとの値（営業期間・予約の開始・定員）を自動で取り出す仕組み。AIは使わない。

取得元は3種類。確かさの高い順に使う。
  A. 予約サイト「やまたん」の小屋ページ（data/huts_sources.json の yamatan）
     定員・営業期間・予約方法が項目として登録されているので、そのまま読める
  B. 公式ページの決まった言い回し（data/huts_recipes.json のレシピ）
     「2026年営業期間：6月20日〜10月12日」のような文を、小屋ごとの正規表現で読む
  C. 一覧の出典（長野県のポータル・山と溪谷オンライン）… build_huts_from_nagano.py / update_huts.py が担当

読み取った値は、次の確認を通ったものだけを「自動の値」として採用する（通らなければ採用せず、理由を報告する）。
  1. 年が今年か来年である（古い年の記載が残っているだけのページを拾わない）
  2. 月日が実在する日付である
  3. 前の年の値がある場合、日付のずれが45日以内である（大きくずれたら、読み違いか大きな変更なので人が確認する）
採用した値は data/huts_history.json に年ごとに積み上げる（翌年の確認3に使い、「例年◯月ごろ」の目安にもなる）。
"""
import datetime, html, json, os, re, subprocess, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import huts_fetch as hf

ZEN = str.maketrans('０１２３４５６７８９', '0123456789')
LINK_RE = re.compile(r'予約|宿泊|ご利用|料金|案内|reserv|yoyaku|stay|guide|plan|syukuhaku|shukuhaku|info|price|annai', re.I)
_cache = {}


def _raw(url):
    try:
        return subprocess.run(['curl', '-s', '-L', '-k', '-m', '20', '-A', hf.UA, url], capture_output=True).stdout
    except Exception:
        return b''


def page_lines(url):
    """公式ページと、そこから1階層たどった予約・宿泊案内のページ（最大5つ）の本文の行"""
    if url in _cache:
        return _cache[url]
    b = _raw(url)
    try:
        t = b.decode('utf-8')
    except UnicodeDecodeError:
        t = b.decode('cp932', 'replace')
    host = urllib.parse.urlparse(url).netloc
    subs = []
    for m in re.finditer(r'<a\b[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', t, flags=re.S | re.I):
        href = urllib.parse.urljoin(url, html.unescape(m.group(1)))
        if urllib.parse.urlparse(href).netloc != host or re.search(r'\.(pdf|jpe?g|png|gif|zip)$', href, re.I):
            continue
        if (LINK_RE.search(re.sub(r'<[^>]+>', '', m.group(2))) or LINK_RE.search(href)) and href not in subs and href.rstrip('/') != url.rstrip('/'):
            subs.append(href)
    lines = []
    for u in [url] + subs[:5]:
        for l in hf.fetch_text(u) or []:
            if l not in lines:
                lines.append(l)
    _cache[url] = lines
    return lines


LINK_DEEP = re.compile(r'予約|宿泊|ご利用|料金|案内|お知らせ|新着|ニュース|トピック|reserv|yoyaku|stay|guide|plan|syukuhaku|shukuhaku|info|price|annai|news|topics|booking', re.I)
_deep = {}
# お知らせの一覧らしいページ（リンクの文字かアドレスで見分ける）と、その中で読みに行く記事（題に予約・受付・営業などがあるもの）
NEWS_LIST = re.compile(r'お知らせ|新着|ニュース|トピック|ブログ|日記|news|topics|blog|whatsnew|information|/info', re.I)
ARTICLE = re.compile(r'予約|受付|受け付け|営業|シーズン|年度|オープン|小屋開け')
SKIP_EXT = re.compile(r'\.(pdf|jpe?g|png|gif|zip|docx?|xlsx?)$', re.I)


def _decode(b):
    m = re.search(br'charset=["\']?([A-Za-z0-9_\-]+)', b[:3000])
    for enc in ([m.group(1).decode('ascii', 'ignore')] if m else []) + ['utf-8', 'cp932', 'euc-jp']:
        try:
            return b.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return b.decode('utf-8', 'replace')


def _text_lines(fragment):
    t = re.sub(r'(?is)<(script|style|noscript)\b.*?</\1>', ' ', fragment)
    t = re.sub(r'(?s)<[^>]+>', '\n', t)
    return [x for x in (re.sub(r'\s+', ' ', html.unescape(l)).strip() for l in t.split('\n')) if x]


def _links(url, page_html, host):
    """ページの中の、同じサイトへのリンク：[(アドレス, リンクの文字)]"""
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', page_html, flags=re.S | re.I):
        href = urllib.parse.urljoin(url, html.unescape(m.group(1)))
        if urllib.parse.urlparse(href).netloc != host or SKIP_EXT.search(href):
            continue
        out.append((href, re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(2)))).strip()))
    return out


def feed_articles(url, top_html, today=None, limit=4):
    """お知らせの更新情報（RSS / Atom のフィード）から、予約・営業にかかわる新しい記事を読む。
    戻り値：[{'title', 'link', 'lines'}]。フィードが無い・読めないサイトでは []。
    フィードは、ページの <link rel="alternate"> に書かれたものを使う。書かれていなくても WordPress のサイトなら /feed/ を試す。
    新しい順に並んでいるので、一覧ページの作りに左右されずに、新しいお知らせを拾える。古い記事（240日より前）は読まない"""
    today = today or datetime.date.today()
    feeds = []
    for m in re.finditer(r'<link\b[^>]*>', top_html, flags=re.I):
        tag = m.group(0)
        if re.search(r'rel=["\']alternate["\']', tag, re.I) and re.search(r'type=["\']application/(rss|atom)\+xml["\']', tag, re.I) and not re.search(r'comments', tag, re.I):
            h = re.search(r'href=["\']([^"\']+)["\']', tag)
            if h:
                feeds.append(urllib.parse.urljoin(url, html.unescape(h.group(1))))
    if not feeds and 'wp-content' in top_html:
        feeds.append(url.rstrip('/') + '/feed/')
    out, seen = [], set()
    for f in feeds[:2]:
        x = _decode(_raw(f))
        if '<item' not in x and '<entry' not in x:
            continue
        for it in re.findall(r'(?is)<(?:item|entry)\b.*?</(?:item|entry)>', x):
            def tag(names):
                for n in names:
                    mm = re.search(r'(?is)<%s\b[^>]*>(.*?)</%s>' % (n, n), it)
                    if mm:
                        v = mm.group(1).strip()
                        cd = re.match(r'(?is)<!\[CDATA\[(.*)\]\]>$', v)
                        return cd.group(1) if cd else html.unescape(v)
                return ''
            title = re.sub(r'<[^>]+>', '', tag(['title'])).strip()
            link = tag(['link']).strip()
            if not link:
                mm = re.search(r'(?is)<link\b[^>]*href=["\']([^"\']+)["\']', it)
                link = html.unescape(mm.group(1)) if mm else ''
            if not title or not ARTICLE.search(title) or link in seen:
                continue
            when = tag(['pubDate', 'published', 'updated', 'dc:date'])
            d = None
            try:
                import email.utils
                d = email.utils.parsedate_to_datetime(when).date()
            except Exception:
                mm = re.match(r'(\d{4})-(\d{2})-(\d{2})', when or '')
                if mm:
                    d = datetime.date(int(mm.group(1)), int(mm.group(2)), int(mm.group(3)))
            if d and (today - d).days > 240:
                continue
            body = _text_lines(tag(['content:encoded', 'content', 'description', 'summary']))
            if sum(len(l) for l in body) < 200 and link and not SKIP_EXT.search(link):
                body = hf.fetch_text(link) or body         # フィードが要約だけのときは、記事のページを読む
            seen.add(link)
            out.append({'title': title, 'link': link, 'lines': [title] + body})
            if len(out) >= limit:
                return out
    return out


def page_lines_deep(url, limit=12, follow=True, extra=6):
    """page_lines より広く見る版：公式ページと、そこから1階層たどった予約・案内・お知らせのページ（最大 limit 個）。
    予約開始の書き方を型で探すとき（huts_patterns.py）に使う。
    follow=True のときは、お知らせの先の記事まで読む（合わせて最大 extra 個）：
      1) お知らせのフィード（RSS / Atom）にある、予約・営業にかかわる新しい記事（feed_articles）
      2) お知らせの一覧のページから、題に「予約」「受付」「営業」などがある記事へもう1階層
    古い年の記事を拾っても、使う側の確認（年が今年か来年・前の日付から45日以内・候補が1つ）で落ちる"""
    key = (url, follow)
    if key in _deep:
        return _deep[key]
    t = _decode(_raw(url))
    host = urllib.parse.urlparse(url).netloc
    subs, lists = [], []
    for href, text in _links(url, t, host):
        if (LINK_DEEP.search(text) or LINK_DEEP.search(href)) and href not in subs and href.rstrip('/') != url.rstrip('/'):
            subs.append(href)
            if NEWS_LIST.search(text) or NEWS_LIST.search(href):
                lists.append(href)
    subs = subs[:limit]
    lines = []

    def add(ls):
        for l in ls or []:
            if l not in lines:
                lines.append(l)
    for u in [url] + subs:
        add(hf.fetch_text(u))
    if follow:
        got = set([url] + subs)
        n = 0
        for a in feed_articles(url, t):
            if n >= extra:
                break
            add(a['lines'])
            got.add(a['link'])
            n += 1
        ty = (str(datetime.date.today().year), str(datetime.date.today().year + 1))
        for lu in [url] + [u for u in lists if u in subs]:
            if n >= extra:
                break
            page = t if lu == url else _decode(_raw(lu))
            arts = [(h, x) for h, x in _links(lu, page, host) if h not in got and ARTICLE.search(x) and len(x) >= 6]
            arts.sort(key=lambda p: (0 if any(y in p[1] for y in ty) else 1, 0 if re.search(r'予約|受付', p[1]) else 1))   # 今年・来年の年が題にある記事、予約の記事を先に
            for h, x in arts[:3]:
                if n >= extra:
                    break
                got.add(h)
                add([x])
                add(hf.fetch_text(h))
                n += 1
    _deep[key] = lines
    return lines


def yamatan(slug):
    """やまたんの小屋ページ → {capacity, open_period, reservation_method}。取れなければ {}"""
    t = _raw('https://www.yamatan.net/hut/' + slug).decode('utf-8', 'replace')
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, flags=re.S)
    if not m:
        return {}
    out = {}

    def walk(o):
        if isinstance(o, dict):
            for k in ('capacity', 'open_period', 'reservation_method'):
                if k in o and o[k] not in (None, '') and k not in out:
                    out[k] = o[k]
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    try:
        data = json.loads(m.group(1))
        walk(data)
        hut = ((data.get('props') or {}).get('pageProps') or {}).get('hut') or {}
    except (ValueError, AttributeError):
        return {}
    # 予約できる範囲：Web予約を受け付けている小屋で、「宿泊日の◯日前／◯か月前から」が登録されているものだけ（0 は未設定）
    num, typ = hut.get('before_reservation_num'), hut.get('beforeReservationType')
    if (hut.get('hut_profile') or {}).get('is_reserve') and isinstance(num, int) and num > 0 and typ in ('days', 'months'):
        tm = re.fullmatch(r'(\d\d):(\d\d):\d\d', str(hut.get('canReserveStartDateTime') or ''))
        at = ' %d:%s' % (int(tm.group(1)), tm.group(2)) if tm and tm.group(0) != '23:59:59' else ''
        out['window'] = 'Web予約は宿泊日の%d%s前%sから' % (num, '日' if typ == 'days' else 'か月', at)
    return out


NEWS_RE = re.compile(r'[\U0001F539\U0001F538]\s*(.+?)（[^（）]*）の(20\d\d)年度(\S*?)シーズン（[^（）]*）を(\d+)月(\d+)日(\d+)時(?:(\d+)分)?よりご予約受付を開始')


def yamatan_news(url):
    """やまたんの「◯年度シーズン予約開始のお知らせ」→ [(お知らせ上の小屋名, 年, シーズン名, 月, 日, 時, 分)]
    1軒ずつ「◯◯（山域）の2026年度シーズン（期間）を5月1日11時よりご予約受付を開始」の形で並んでいる"""
    text = ''.join(hf.fetch_text(url) or [])
    out = []
    for m in NEWS_RE.finditer(text):
        row = (m.group(1).strip(), int(m.group(2)), m.group(3), int(m.group(4)), int(m.group(5)), int(m.group(6)), int(m.group(7) or 0))
        if row not in out:
            out.append(row)
    return out


def _doy(month, day):
    return datetime.date(2001, month, day).timetuple().tm_yday


def check(year, month, day, prev, today):
    """確認1〜3。問題があれば理由の文字列、無ければ None"""
    if year is not None and year not in (today.year, today.year + 1):
        return '記載の年が %d 年（今年・来年ではない）' % year
    if month is not None:
        try:
            datetime.date(2000, month, day or 1)
        except ValueError:
            return '日付として成り立たない（%s月%s日）' % (month, day)
        if prev and prev.get('month'):
            diff = abs(_doy(month, day or 1) - _doy(prev['month'], prev.get('day') or 1))
            diff = min(diff, 365 - diff)
            if diff > 45:
                return '前の年（%s）から %d 日ずれている' % (prev.get('value'), diff)
    return None


def target_year(today):
    """いま見張っている年。11月以降は来年の情報（予約開始・営業期間）が出始めるので、来年を対象にする"""
    return today.year + 1 if today.month >= 11 else today.year


def due_huts(huts, today):
    """今日、集中して見に行く小屋の名前の集合。
    前の年に日付つきの値（例：予約の開始 5月20日）が取れている小屋は、その日の44日前〜14日後を「発表が出そうな期間」とみなし、
    対象の年の値がまだ取れていないあいだだけ、3日に1回見に行く。それ以外は月1回（update_huts.py が毎月1日に全小屋を見る）。
    何日前型の小屋は rule_watch_huts（発表が多い時期の2か月前から週1回）。"""
    hpath = os.path.join(ROOT, 'data', 'huts_history.json')
    hist = json.load(open(hpath, encoding='utf-8')) if os.path.exists(hpath) else {}
    ty = target_year(today)
    by_id = {h['id']: h['name'] for h in huts}
    out = set()
    if today.toordinal() % 3:
        return out
    for key, years in hist.items():
        if str(ty) in years:
            continue          # 対象の年の値は取得済み → 月1回に戻す
        dated = [v for k, v in sorted(years.items()) if v.get('month')]
        if not dated:
            continue
        last = dated[-1]
        try:
            expect = datetime.date(ty, last['month'], last.get('day') or 1)
        except ValueError:
            continue
        if expect - datetime.timedelta(days=44) <= today <= expect + datetime.timedelta(days=14):
            name = by_id.get(key.split(':')[0])
            if name:
                out.add(name)
    return out


def season_window(today):
    """予約開始の発表が多い時期（何日前型の小屋の決まりが変わっていないかを確かめる期間）。
    一斉解放型・期間区切り型の小屋の予約開始日（data/huts_rules.json）を早い順に並べ、
    早いほうから1割目の日付の60日前（＝ふつうの予約開始の約2か月前）から、9割目の日付の14日後までを期間とする。
    いまのデータでは、おおよそ12月上旬〜6月末。データが変われば期間も動く。(期間の始まり, 終わり) を返す。期間外なら None"""
    path = os.path.join(ROOT, 'data', 'huts_rules.json')
    if not os.path.exists(path):
        return None
    days = []
    for v in json.load(open(path, encoding='utf-8'))['huts'].values():
        r = v.get('r') or {}
        if r.get('t') == 'fix':
            days.append(_doy(r['m'], r['d']))
        elif r.get('t') == 'phase':
            days += [_doy(x['m'], x['d']) for x in r['p']]
    # 秋に来季分の受付を始める小屋（10〜11月）は少数なので、春の山に合わせるために7月以降は数えない
    days = sorted(d for d in days if d < _doy(7, 1))
    if len(days) < 10:
        return None
    lo, hi = days[len(days) // 10], days[len(days) * 9 // 10]
    for y in (today.year, today.year + 1):
        base = datetime.date(y, 1, 1)
        start = base + datetime.timedelta(days=lo - 1 - 60)
        end = base + datetime.timedelta(days=hi - 1 + 14)
        if start <= today <= end:
            return start, end
    return None


def rule_watch_huts(huts, today):
    """今日、決まりが変わっていないかを確かめに行く小屋の名前の集合。
    予約の開始が「宿泊日の何日前・何か月前」「宿泊月の前月◯日」で決まる小屋が対象で、season_window の期間中、週1回。
    （期間外は、毎月1日の全小屋の確認だけ）"""
    if not season_window(today) or today.toordinal() % 7:
        return set()
    import huts_rules
    out = set()
    for h in huts:
        if h.get('bookingNone'):
            continue
        a = h.get('auto') or {}
        r = huts_rules.derive(h['name'], h.get('bookingStart'), (a.get('bookingStartWeb') or {}).get('value'), (a.get('bookingWindow') or {}).get('value'))
        if r and r.get('t') in ('rel', 'mon'):
            out.add(h['name'])
    return out


def run(huts, today=None, only=None, previous=None):
    """huts（data/huts.json の小屋のリスト）に自動の値を書き込み、報告の行を返す。
    only：今日見に行く小屋の名前（None なら全部）。見に行かない小屋は、previous（前回の huts.json）の自動の値を引き継ぐ"""
    today = today or datetime.date.today()
    previous = previous or {}
    src_all = json.load(open(os.path.join(ROOT, 'data', 'huts_sources.json'), encoding='utf-8'))
    src = src_all['huts']
    recipes = json.load(open(os.path.join(ROOT, 'data', 'huts_recipes.json'), encoding='utf-8'))['recipes']
    hpath = os.path.join(ROOT, 'data', 'huts_history.json')
    hist = json.load(open(hpath, encoding='utf-8')) if os.path.exists(hpath) else {}
    by_name = {h['name']: h for h in huts}
    report = []
    for h in huts:
        h['auto'] = {} if (only is None or h['name'] in only) else ((previous.get(h['id']) or {}).get('auto') or {})
    # A. やまたん
    for name, s in src.items():
        h = by_name.get(name)
        if not h or not s.get('yamatan') or (only is not None and name not in only):
            continue
        y = yamatan(s['yamatan'])
        url = 'https://www.yamatan.net/hut/' + s['yamatan']
        if not y:
            report.append('- %s：予約サイトのページを読めませんでした（%s）' % (name, url))
            continue
        cap = str(y.get('capacity') or '').translate(ZEN).replace(' ', '')
        if re.fullmatch(r'\d{1,4}', cap):
            h['auto']['capacity'] = {'value': int(cap), 'source': url}
        per = str(y.get('open_period') or '').strip()
        yrs = [int(x) for x in re.findall(r'(20\d\d)', per.translate(ZEN))]
        if per and (not yrs or max(yrs) >= today.year):
            h['auto']['season'] = {'value': per, 'source': url}
        elif per:
            report.append('- %s：予約サイトの営業期間が古い年のまま（%s）' % (name, per))
        if y.get('window'):
            h['auto']['bookingWindow'] = {'value': y['window'], 'source': url}
        if y.get('reservation_method'):
            h['auto']['bookingText'] = {'value': re.sub(r'\s+', ' ', str(y['reservation_method']))[:600], 'source': url}
    # A2. やまたんの「シーズン予約開始のお知らせ」（Web予約の受付開始日時が小屋ごとに並ぶ）
    news = src_all.get('yamatanNews') or {}
    if news.get('url'):
        rows = yamatan_news(news['url'])
        if not rows:
            report.append('- 予約サイトの「予約開始のお知らせ」を読めませんでした（%s）' % news['url'])
        elif max(r[1] for r in rows) < target_year(today):
            report.append('- 予約サイトの「予約開始のお知らせ」が %d 年度のまま。%d 年度のお知らせが出ていたら data/huts_sources.json の yamatanNews.url を差し替える'
                          % (max(r[1] for r in rows), target_year(today)))
        per = {}
        for nm, year, season, mo, d, hh, mi in rows:
            name = news['names'].get(nm)
            if name and name in by_name and (only is None or name in only):
                per.setdefault(name, []).append((year, season, mo, d, hh, mi))
        for name, ents in per.items():
            h = by_name[name]
            year = max(e[0] for e in ents)
            ents = sorted((e for e in ents if e[0] == year), key=lambda e: (e[2], e[3]))
            key = h['id'] + ':bookingStartWeb'
            prev_years = sorted(k for k in hist.get(key, {}) if int(k) < year)
            prev = hist[key][prev_years[-1]] if prev_years else None
            bad = check(year, ents[0][2], ents[0][3], prev, today)
            parts = ['%s%d月%d日 %d:%02dから' % ((e[1] + 'の分は') if len(ents) > 1 and e[1] else '', e[2], e[3], e[4], e[5]) for e in ents]
            value = '、'.join(parts) + '（%d年。Web予約）' % year
            if bad:
                report.append('- %s：読み取った値「%s」は採用しませんでした（%s）' % (name, value, bad))
                continue
            h['auto']['bookingStartWeb'] = {'value': value, 'source': news['url'], 'year': year}
            if len(ents) == 1:      # 受付開始が1回だけの小屋は、通知用に月・日・時刻も控える
                h['auto']['bookingStartWeb'].update({'month': ents[0][2], 'day': ents[0][3], 'time': '%d:%02d' % (ents[0][4], ents[0][5])})
            old = hist.setdefault(key, {}).get(str(year))
            if not old or old.get('value') != value:
                hist[key][str(year)] = {'value': value, 'month': ents[0][2], 'day': ents[0][3], 'seenAt': today.isoformat()}
    # B. 公式ページのレシピ
    for r in recipes:
        if only is not None and r['hut'] not in only:
            continue
        h = by_name.get(r['hut'])
        if not h:
            report.append('- レシピの小屋名が見つかりません：%s' % r['hut'])
            continue
        m = None
        for l in page_lines(r['url']):
            m = re.search(r['regex'], l)
            if m:
                break
        if not m:
            report.append('- %s：公式ページから「%s」を読み取れませんでした（言い回しが変わった可能性。%s）' % (
                r['hut'], '予約の開始' if r['field'] == 'bookingStart' else '営業期間', r['url']))
            continue
        g = [None] + [(x or '').translate(ZEN) for x in m.groups()]
        num = lambda k: int(g[r[k]]) if r.get(k) else None
        year, month, day = num('year'), num('month'), num('day')
        key = h['id'] + ':' + r['field']
        if year is None and month:
            # 年の書かれていない文：前に読んだ月日と違っていれば、新しい年（いま見張っている年）の発表とみなす。
            # 同じ月日なら年は付けない（去年の文が残っているだけかもしれないため）
            last = [v for k, v in sorted(hist.get(key, {}).items()) if v.get('month')]
            if last and (last[-1]['month'], last[-1].get('day')) != (month, day):
                year = target_year(today)
        prev_years = sorted(k for k in hist.get(key, {}) if year is None or int(k) < year)
        prev = hist[key][prev_years[-1]] if prev_years else None
        bad = check(year, month, day, prev, today)
        value = r['out']
        for i in range(1, len(g)):
            value = value.replace('{%d}' % i, g[i])
        if bad:
            report.append('- %s：読み取った値「%s」は採用しませんでした（%s）' % (r['hut'], value, bad))
            continue
        h['auto'][r['field']] = {'value': value, 'source': r['url'], 'year': year, 'month': month, 'day': day}
        if r.get('hour'):
            h['auto'][r['field']]['time'] = '%d:%s' % (int(g[r['hour']]), g[r['minute']] if r.get('minute') else '00')
        elif r.get('fixedTime'):
            h['auto'][r['field']]['time'] = r['fixedTime']
        ykey = str(year or today.year)
        old = hist.setdefault(key, {}).get(ykey)
        if not old or old.get('value') != value:
            if old:
                report.append('- %s：%s が変わりました（%s → %s）' % (r['hut'], '予約の開始' if r['field'] == 'bookingStart' else '営業期間', old.get('value'), value))
            hist[key][ykey] = {'value': value, 'month': month, 'day': day, 'seenAt': today.isoformat()}
    # C. 型で読む（huts_patterns.py）：一覧の出典の文と、公式サイトの予約・案内・お知らせのページから、予約開始の書き方を型どおりに探す。
    #    - 前の年の日付が分かっている一斉解放型の小屋：年が今年か来年で、前の日付から45日以内の候補が1つに決まれば、自動で使う
    #    - 予約の開始が未登録の小屋・型と食い違う小屋：自動では使わず、候補として報告する
    #    あわせて、いまの日付を履歴に入れておく（前の年の日付の前後だけ3日に1回見に行く仕組みに乗せるため）
    import huts_patterns
    import huts_rules
    have = set(r['hut'] for r in recipes if r['field'] in ('bookingStart', 'bookingStartDate'))
    names = [h['name'] for h in huts]
    for h in huts:
        if h.get('bookingNone'):
            continue
        a = h.get('auto') or {}
        rule = huts_rules.derive(h['name'], h.get('bookingStart'), (a.get('bookingStartWeb') or {}).get('value'), (a.get('bookingWindow') or {}).get('value'))
        key = h['id'] + ':bookingStartDate'
        if rule and rule.get('t') == 'fix' and rule.get('y') and str(rule['y']) not in hist.get(key, {}):
            hist.setdefault(key, {})[str(rule['y'])] = {'value': '%d月%d日から（%d年）' % (rule['m'], rule['d'], rule['y']), 'month': rule['m'], 'day': rule['d'],
                                                         'seenAt': today.isoformat(), 'seed': True}
        if only is not None and h['name'] not in only:
            continue
        cs = [c for c in huts_patterns.candidates(h, page_lines_deep, names) if c['score'] >= 5]
        fix = [c for c in cs if c['t'] == 'fix' and c.get('y') in (today.year, today.year + 1)]
        rel = [c for c in cs if c['t'] in ('rel', 'mon')]

        def text(c):
            return '%d月%d日%sから（%d年）' % (c['m'], c['d'], (' ' + c['time']) if c.get('time') else '', c['y'])
        if rule and rule.get('t') == 'fix':
            if h['name'] in have and a.get('bookingStartDate') or a.get('bookingStart'):
                continue                      # 小屋ごとのレシピで読めているときは、そちらを使う
            prev = {'month': rule['m'], 'day': rule['d'], 'value': '%d月%d日' % (rule['m'], rule['d'])}
            ok = [c for c in fix if (not rule.get('y') or c['y'] >= rule['y']) and check(c['y'], c['m'], c['d'], prev, today) is None]
            if not ok:
                continue
            top_y = max(c['y'] for c in ok)
            ok = [c for c in ok if c['y'] == top_y]
            dates = sorted(set((c['m'], c['d']) for c in ok))
            if len(dates) > 1:
                report.append('- %s：%d年の予約開始らしい日付が複数あり、決められませんでした（自動では反映していません）\n    %s' % (
                    h['name'], top_y, ' ／ '.join(c['line'][:70] for c in ok[:3])))
                continue
            c = ok[0]
            h['auto']['bookingStartDate'] = {'value': text(c), 'source': c.get('url') or '', 'year': c['y'], 'month': c['m'], 'day': c['d'], 'by': 'pattern', 'line': c['line'][:160]}
            if c.get('time'):
                h['auto']['bookingStartDate']['time'] = c['time']
            old = hist.setdefault(key, {}).get(str(c['y']))
            if not old or (old.get('month'), old.get('day')) != (c['m'], c['d']):
                if not rule.get('y') or c['y'] > rule['y'] or (c['m'], c['d']) != (rule['m'], rule['d']):
                    report.append('- %s：予約の開始を公式の記載から読み取りました → %s（前回 %d月%d日）\n    %s\n    %s' % (
                        h['name'], text(c), rule['m'], rule['d'], c['line'][:110], c.get('url') or ''))
                hist[key][str(c['y'])] = {'value': text(c), 'month': c['m'], 'day': c['d'], 'seenAt': today.isoformat()}
        elif not rule:
            found = fix[:2] + rel[:1]
            if found:
                report.append('- %s：予約の開始らしい記載が見つかりました（未登録の小屋。自動では反映していません。確かめて登録してください）\n%s' % (
                    h['name'], '\n'.join('    %s｜%s' % (c['line'][:110], c.get('url') or '') for c in found)))
        elif rule.get('t') in ('rel', 'mon'):
            # 何日前型・月ごと型：決まりが変わっていないかを確かめる。自動では書き換えず、違いを見つけたら報告する。
            #   a) 「◯か月前」の数字がいまのデータと違う（手で書いた型の小屋は、書き方が特殊なので対象外）
            #   b) 今年・来年の日付で「◯月◯日から予約受付」という書き方が出てきた（一斉解放に変わった可能性）
            # 同じ記載を毎週報告しないように、報告した行は履歴に覚えておく。確かめた日も残す
            wkey = h['id'] + ':ruleWatch'
            w = hist.setdefault(wkey, {})
            seen = set(w.get('reported') or [])
            unit = {'m': 'か月', 'd': '日', 'w': '週間'}
            notes = []
            same = False
            if rule['t'] == 'rel' and rel and rel[0]['t'] == 'rel':
                c = rel[0]
                if (c['n'], c['u']) == (rule['n'], rule['u']):
                    same = True
                elif h['name'] not in huts_rules.RULES:
                    notes.append(('rel:%d%s' % (c['n'], c['u']), '決まりが、いまのデータ（%d%s前）と違う書き方で見つかりました（%d%s前）' % (
                        rule['n'], unit[rule['u']], c['n'], unit[c['u']]), c))
            if rule['t'] == 'mon' and rel and rel[0]['t'] == 'mon':
                c = rel[0]
                if (c['n'], c.get('d') or 1) == (rule['n'], rule.get('d') or 1):
                    same = True
                else:
                    notes.append(('mon:%d-%d' % (c['n'], c.get('d') or 1), '決まりが、いまのデータ（%dか月前の%d日）と違う書き方で見つかりました（%dか月前の%d日）' % (
                        rule['n'], rule.get('d') or 1, c['n'], c.get('d') or 1), c))
            for c in fix[:1]:
                notes.append(('fix:%d-%d-%d' % (c['y'], c['m'], c['d']), '%d年%d月%d日から予約を受け付ける、という書き方が見つかりました（いまのデータは%s。一斉解放に変わった可能性）' % (
                    c['y'], c['m'], c['d'], '%d%s前' % (rule['n'], unit[rule['u']]) if rule['t'] == 'rel' else '宿泊月の%dか月前' % rule['n']), c))
            for k, msg, c in notes:
                if k in seen:
                    continue
                seen.add(k)
                report.append('- %s：予約の開始の%s。自動では反映していません。確かめてください\n    %s｜%s' % (h['name'], msg, c['line'][:110], c.get('url') or ''))
            w['checkedAt'] = today.isoformat()
            w['result'] = 'same' if same and not notes else 'diff' if notes else 'notfound'
            if seen:
                w['reported'] = sorted(seen)
    json.dump(hist, open(hpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    return report
