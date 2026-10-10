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
    対象の年の値がまだ取れていないあいだだけ、3日に1回見に行く。それ以外は月1回（update_huts.py が毎月1日に全小屋を見る）。"""
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


def run(huts, today=None, only=None, previous=None):
    """huts（data/huts.json の小屋のリスト）に自動の値を書き込み、報告の行を返す。
    only：今日見に行く小屋の名前（None なら全部）。見に行かない小屋は、previous（前回の huts.json）の自動の値を引き継ぐ"""
    today = today or datetime.date.today()
    previous = previous or {}
    src = json.load(open(os.path.join(ROOT, 'data', 'huts_sources.json'), encoding='utf-8'))['huts']
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
        prev_years = sorted(k for k in hist.get(key, {}) if year is None or int(k) < year)
        prev = hist[key][prev_years[-1]] if prev_years else None
        bad = check(year, month, day, prev, today)
        value = r['out']
        for i in range(1, len(g)):
            value = value.replace('{%d}' % i, g[i])
        if bad:
            report.append('- %s：読み取った値「%s」は採用しませんでした（%s）' % (r['hut'], value, bad))
            continue
        h['auto'][r['field']] = {'value': value, 'source': r['url'], 'year': year}
        ykey = str(year or today.year)
        old = hist.setdefault(key, {}).get(ykey)
        if not old or old.get('value') != value:
            if old:
                report.append('- %s：%s が変わりました（%s → %s）' % (r['hut'], '予約の開始' if r['field'] == 'bookingStart' else '営業期間', old.get('value'), value))
            hist[key][ykey] = {'value': value, 'month': month, 'day': day, 'seenAt': today.isoformat()}
    json.dump(hist, open(hpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    return report
