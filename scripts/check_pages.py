#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAMATCH 公開前自動チェックスクリプト（Phase 0）

data/mountains.json を正本として、サイト全体の整合性を検査する。
Phase 1以降（CSS/JS外部化・テンプレ生成化）の変更が既存ページを壊していないか
を確認する回帰テストとしても使う想定。

検査項目:
  1. 画像切れ            ローカル画像パス（src="/...")の実在確認
  2. リンク切れ           ローカルリンク先（href="/...")の実在確認
  3. 必須データ欠損        mountains.json の必須フィールド（常時／電車アクセスありのみ）
  4. title / description / canonical 欠損   インデックス対象ページのみ（noindex/リダイレクトは除外）
  5. title 重複           インデックス対象ページ間での重複
  6. JSON と HTML の不一致  運賃・標高・コース定数がHTML本文と食い違っていないか
  7. 交通情報の欠損        trainAccessがある山にアクセス表セクションがあるか／逆に無い山に残っていないか
  8. trainRoutes構造化データの整合性
  9. ルートの他山コピー     routes[]が別の山と同一内容（時間・距離・標高差まで一致）になっていないか
 10. 所要時間の不一致      trainTimeXxx が trainRoutes の legs 合計と一致するか／trainAccess文章の所要時間が legs に存在するか
 11. 記事・検索ページの駅名  山カードの「〇〇駅→バス…」の駅が、その山の経路データに存在するか
 12. コース定数の異常値      FAQ・紹介文の「定数X〜Y」でY>100 または X>Y
 13. 規制中の山の掲載        status.level が restricted の山が、通常の検索ページ・記事のおすすめに載っていないか
 14. 特急の座席制度         あずさ・かいじ・富士回遊等の全車指定席特急に「自由席」と書いていないか

使い方:
  python3 scripts/check_pages.py                    # レポートをテキスト出力
  python3 scripts/check_pages.py --json out.json    # JSON でも出力（後続フェーズ・CI用）
  python3 scripts/check_pages.py --only mountains    # mountains/配下のみ検査（高速）

終了コード: 異常が1件でもあれば1、なければ0
"""
import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)

IMG_EXT = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.ico')

# --- 必須フィールド定義 -----------------------------------------------

ALWAYS_REQUIRED = [
    'id', 'name', 'kana', 'elevation', 'difficulty', 'category',
    'courseCoefficientRange', 'driveTime', 'area', 'lat', 'lng',
    'description', 'season', 'trailhead',
]

# trainAccess が入っている山でだけ必須になるフィールド
# 注: trainLine/nearestStationは、trainAccessの文中に路線・最寄駅名を
#     埋め込む形で運用されている山が26件以上あり必須にできないため対象外
#     （例: tanzawa の trainAccess は「小田急小田原線」の路線名を文中に含む）
TRAIN_REQUIRED_IF_TRAIN_ACCESS = [
    'fareShinjuku', 'fareYokohama', 'fareOmiya',
    'trainAccessYokohama', 'trainAccessOmiya',
]


def load_mountains():
    path = os.path.join(ROOT, 'data', 'mountains.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def iter_html_files(only=None):
    """サイト内の全HTMLファイルを列挙する。only指定時はそのサブディレクトリのみ。"""
    base = os.path.join(ROOT, only) if only else ROOT
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__MACOSX'
                       and not (dirpath == ROOT and d == 'scripts')]  # scripts/配下は部品HTML（公開ページではない）
        for fn in filenames:
            if fn.endswith('.html'):
                yield os.path.join(dirpath, fn)


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def rel(path):
    return os.path.relpath(path, ROOT)


def is_noindex(html):
    return bool(re.search(r'<meta[^>]*name=["\']robots["\'][^>]*noindex', html, re.I))


def is_redirect_stub(html):
    return bool(re.search(r'http-equiv=["\']refresh["\']', html, re.I))


def local_path_exists(url_path):
    """サイトルートからの絶対パス（/foo/bar または /foo/bar/）がファイルとして存在するか。"""
    p = url_path.split('#')[0].split('?')[0]
    if not p.startswith('/'):
        return True  # 相対パス・外部URLはここでは対象外（呼び出し側でフィルタ済み前提）
    fs_path = os.path.join(ROOT, p.lstrip('/'))
    if os.path.isdir(fs_path):
        return os.path.isfile(os.path.join(fs_path, 'index.html'))
    if fs_path.endswith('/'):
        return os.path.isfile(os.path.join(fs_path, 'index.html'))
    return os.path.isfile(fs_path)


def is_local_url(url):
    if not url:
        return False
    if url.startswith('//') or url.startswith('http://') or url.startswith('https://'):
        return False
    if url.startswith(('mailto:', 'tel:', 'javascript:', '#', 'data:')):
        return False
    if not url.startswith('/'):
        return False
    # JS文字列連結の断片（例: '<a href="/mountains/' + id + '/'）を誤検出しないよう、
    # パスとして不正な文字（クォート・プラス・空白・波括弧など）を含むものは除外する
    if re.search(r'''['"+{}\s]''', url):
        return False
    return True


SCRIPT_BLOCK_RE = re.compile(r'<script\b[^>]*>.*?</script>', re.S | re.I)
SCRIPT_SRC_RE = re.compile(r'<script[^>]*\bsrc=["\']([^"\']+)["\']', re.I)


def strip_scripts(html):
    """静的なhref/src抽出の前に<script>本体を除去する。
    JS内でテンプレート文字列連結によって組み立てられる '<a href="/mountains/' + id + '/">'
    のような断片は、通常のhref抽出regexでは誤検出されるため対象から外す
    （動的に生成されるリンク/画像パスの検証はPhase 0の対象外）。"""
    return SCRIPT_BLOCK_RE.sub('', html)


# --- 各チェック ----------------------------------------------------------

def check_broken_links(html_files):
    issues = []
    href_re = re.compile(r'href=["\']([^"\']+)["\']')
    for path in html_files:
        html = read(path)
        # <script src="..."> はJSファイル本体への参照なので静的に検証できる
        script_srcs = set(SCRIPT_SRC_RE.findall(html))
        static_html = strip_scripts(html)
        urls = set(href_re.findall(static_html)) | script_srcs
        for url in urls:
            if not is_local_url(url):
                continue
            if not local_path_exists(url):
                issues.append({'file': rel(path), 'url': url})
    return issues


def check_broken_images(html_files):
    issues = []
    src_re = re.compile(r'<(?:img|source)[^>]+src=["\']([^"\']+)["\']', re.I)
    bg_re = re.compile(r'background(?:-image)?\s*:\s*url\(["\']?([^"\')]+)["\']?\)')
    for path in html_files:
        html = read(path)
        static_html = strip_scripts(html)
        urls = set(src_re.findall(static_html)) | set(bg_re.findall(static_html))
        for url in urls:
            if not is_local_url(url):
                continue
            if not local_path_exists(url):
                issues.append({'file': rel(path), 'url': url})
    return issues


def check_required_fields(mountains):
    issues = []
    for m in mountains:
        mid = m.get('id', '?')
        for f in ALWAYS_REQUIRED:
            v = m.get(f)
            if v is None or v == '':
                issues.append({'id': mid, 'field': f, 'problem': '空/欠損（必須フィールド）'})
        if m.get('trainAccess'):
            for f in TRAIN_REQUIRED_IF_TRAIN_ACCESS:
                v = m.get(f)
                if v is None or v == '':
                    issues.append({'id': mid, 'field': f, 'problem': '電車アクセスありなのに欠損'})
        else:
            # trainAccessが無いのに関連フィールドだけ入っている＝逆方向の不整合
            for f in TRAIN_REQUIRED_IF_TRAIN_ACCESS:
                v = m.get(f)
                if v:
                    issues.append({'id': mid, 'field': f, 'problem': 'trainAccessが空なのに値がある（不整合）'})
    return issues


def check_seo_meta(html_files):
    """title / description / canonical欠損。noindex・リダイレクトスタブは対象外。"""
    issues = []
    titles = {}  # title文字列 -> [file,...]
    for path in html_files:
        html = read(path)
        if is_noindex(html) or is_redirect_stub(html):
            continue
        title_m = re.search(r'<title>(.*?)</title>', html, re.S)
        title = title_m.group(1).strip() if title_m else ''
        desc_m = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.I)
        desc = desc_m.group(1).strip() if desc_m else ''
        canon_m = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\']', html, re.I)
        canon = canon_m.group(1).strip() if canon_m else ''

        if not title:
            issues.append({'file': rel(path), 'problem': 'title欠損'})
        if not desc:
            issues.append({'file': rel(path), 'problem': 'description欠損'})
        if not canon:
            issues.append({'file': rel(path), 'problem': 'canonical欠損'})

        if title:
            titles.setdefault(title, []).append(rel(path))
    return issues, titles


def check_title_duplicates(titles):
    return [{'title': t, 'files': files} for t, files in titles.items() if len(files) > 1]


def fmt_yen(n):
    return '{:,}'.format(n)


def check_json_html_mismatch(mountains, root=None):
    """運賃・標高・コース定数のJSON値がHTML本文中に見当たらないケースを検出する。
    (存在しない＝本文とJSONの数字が食い違っている、または表記ゆれの可能性)"""
    issues = []
    mdir = root or os.path.join(ROOT, 'mountains')
    for m in mountains:
        mid = m['id']
        path = os.path.join(mdir, mid, 'index.html')
        if not os.path.isfile(path):
            issues.append({'id': mid, 'problem': f'mountains/{mid}/index.html が存在しない'})
            continue
        html = read(path)
        if is_redirect_stub(html):
            continue

        elev = m.get('elevation')
        if elev and f'{elev}m' not in html and f'{fmt_yen(elev)}m' not in html:
            issues.append({'id': mid, 'field': 'elevation', 'json': elev,
                            'problem': f'標高{elev}mの表記がHTML中に見つからない'})

        ccr = m.get('courseCoefficientRange')
        if ccr and ccr not in html:
            issues.append({'id': mid, 'field': 'courseCoefficientRange', 'json': ccr,
                            'problem': f'コース定数{ccr}の表記がHTML中に見つからない'})

        # 運賃：本文の権威データ（ts-fare-val data-*属性）がJSONの運賃3種と一致するか（3種とも検査する）
        for dep, field in (('shinjuku', 'fareShinjuku'), ('yokohama', 'fareYokohama'), ('omiya', 'fareOmiya')):
            fare = m.get(field)
            if not fare:
                continue
            attr_m = re.search(rf'data-{dep}="片道約([\d,]+)円"', html)
            if attr_m:
                html_fare = int(attr_m.group(1).replace(',', ''))
                if html_fare != fare:
                    issues.append({'id': mid, 'field': field, 'json': fare, 'html': html_fare,
                                    'problem': 'アクセス表の運賃(ts-fare-val)がJSONと不一致'})

        # 所要時間：trainTimeShinjuku/Yokohama/Omiya は山個別ページの表示には使われないが、
        # トップページ(index.html)のgetTrainTime()/getAccessTier()がソート・フィルター・
        # アクセス難易度バッジ(良好/ふつも/要計画)の判定に直接使用している。
        # 本文の権威データ(ts-time-val data-*属性)とズレると、そのままトップページの
        # 表示・絞り込み結果が実際のアクセス時間と食い違うため、運賃と同様に同期チェックする。
        # (2026-09-22: 84山121件のズレを検出・同期済み。以後の再発防止のためのチェック)
        tsval_m = re.search(r'<span class="ts-time-val"([^>]*)>', html)
        if tsval_m:
            html_attrs = dict(re.findall(r'data-(\w+)="([^"]*)"', tsval_m.group(1)))
            for dep, field in (('shinjuku', 'trainTimeShinjuku'), ('yokohama', 'trainTimeYokohama'), ('omiya', 'trainTimeOmiya')):
                json_min = m.get(field)
                if json_min is None:
                    continue
                html_str = html_attrs.get(dep)
                if html_str is None:
                    continue
                dur_m = re.match(r'約(?:(\d+)時間)?(?:(\d+)分)?', html_str)
                if not dur_m or (dur_m.group(1) is None and dur_m.group(2) is None):
                    continue
                html_min = (int(dur_m.group(1)) if dur_m.group(1) else 0) * 60 + (int(dur_m.group(2)) if dur_m.group(2) else 0)
                if html_min != json_min:
                    issues.append({'id': mid, 'field': field, 'json': json_min, 'html': html_min,
                                    'problem': 'トップページの所要時間(ts-time-val)がJSONと不一致(ソート/フィルター/アクセスバッジに影響)'})

        # FAQPage JSON-LD内の「アクセス方法」回答文にある運賃額が、JSONの運賃3種と食い違っていないか
        # （駐車場代・ロープウェイ代等の無関係な金額を拾わないよう、FAQPageのアクセス関連の回答文だけに絞る）
        faq_m = re.search(r'<script type="application/ld\+json">(\{"@context".*?"FAQPage".*?\})</script>', html)
        if faq_m:
            try:
                faq_data = json.loads(faq_m.group(1))
            except json.JSONDecodeError:
                faq_data = None
            if faq_data:
                for qa in faq_data.get('mainEntity', []):
                    name = qa.get('name', '')
                    answer = qa.get('acceptedAnswer', {}).get('text', '')
                    if 'アクセス' not in name and '運賃' not in name:
                        continue
                    yen_in_faq = set(int(v.replace(',', '')) for v in re.findall(r'([\d,]{3,7})円', answer))
                    expected = {m.get('fareShinjuku'), m.get('fareYokohama'), m.get('fareOmiya')}
                    expected = {v for v in expected if v}
                    stray = sorted(yen_in_faq - expected)
                    if stray:
                        issues.append({'id': mid, 'field': 'FAQ内運賃',
                                        'json': sorted(expected), 'html': stray,
                                        'problem': 'FAQ「アクセス方法」回答の運賃額がJSON(運賃3種)と不一致'})
    return issues


def check_transit_section(mountains, root=None):
    """trainAccessがある山にアクセス表セクション（ts-fare-val）が実在するか。"""
    issues = []
    mdir = root or os.path.join(ROOT, 'mountains')
    for m in mountains:
        mid = m['id']
        path = os.path.join(mdir, mid, 'index.html')
        if not os.path.isfile(path):
            continue
        html = read(path)
        if is_redirect_stub(html):
            continue
        has_section = 'ts-fare-val' in html or 'ts-time-val' in html
        if m.get('trainAccess') and not has_section:
            issues.append({'id': mid, 'problem': 'trainAccessがあるのにアクセス表セクションがHTMLに無い'})
        if not m.get('trainAccess') and has_section:
            issues.append({'id': mid, 'problem': 'trainAccessが空なのにアクセス表セクションがHTMLに残っている'})
    return issues


def check_train_routes_schema(mountains):
    """trainRoutes構造化データの整合性チェック（2026-09-23 Phase5で追加）。
    - trainAccessHtmlとtrainRoutesの有無が食い違っていないか（Phase3移行で全131山に同時付与したはず）
    - trainRoutes.routesの各出発地が、legsを持つなら構造的に妥当か（station必須、終点以外はmethod.icon/line必須）
    """
    issues = []
    for m in mountains:
        mid = m['id']
        has_html = bool(m.get('trainAccessHtml'))
        train_routes = m.get('trainRoutes')
        has_routes = bool(train_routes)

        if has_html and not has_routes:
            issues.append({'id': mid, 'problem': 'trainAccessHtmlはあるのにtrainRoutesが無い（Phase3移行漏れの疑い）'})
            continue
        if has_routes and not has_html:
            issues.append({'id': mid, 'problem': 'trainRoutesはあるのにtrainAccessHtmlが無い（想定外の組み合わせ）'})

        if not train_routes:
            continue

        routes = train_routes.get('routes') or {}
        any_legs = False
        for dep, route in routes.items():
            if not route:
                continue
            legs = route.get('legs') or []
            if not legs:
                continue
            any_legs = True
            for i, leg in enumerate(legs):
                if not leg.get('station'):
                    issues.append({'id': mid, 'problem': f'trainRoutes.routes.{dep}.legs[{i}]にstationが無い'})
                is_last = (i == len(legs) - 1)
                method = leg.get('method')
                if not is_last:
                    if not method:
                        issues.append({'id': mid, 'problem': f'trainRoutes.routes.{dep}.legs[{i}]（終点以外）にmethodが無い'})
                    elif not method.get('icon') or not method.get('line'):
                        issues.append({'id': mid, 'problem': f'trainRoutes.routes.{dep}.legs[{i}].methodにicon/lineが欠けている'})
        if has_html and not any_legs:
            issues.append({'id': mid, 'problem': 'trainRoutesはあるがどの出発地にもlegsが無い（パース失敗の疑い）'})
    return issues


# --- レポート出力 ----------------------------------------------------------

# --- 9〜14: 再発防止用チェック（実際に見つかった誤りのパターン） -----------------

# 同一内容のルートを複数の山が持つのが正当なもの（同じ縦走路を共有する山）
SHARED_ROUTE_ALLOWLIST = {
    ('椹島〜荒川岳〜赤石岳縦走（2泊）', frozenset({'arakawadake', 'akaisidake'})),
}


def check_route_duplicates(mountains):
    """routes[] の (名前, 時間, 距離, 標高差) が別の山と完全一致していないか（他山からのコピー混入）。"""
    seen = {}
    for m in mountains:
        for r in m.get('routes') or []:
            key = (r.get('name'), r.get('time'), r.get('distance'), r.get('elevation'))
            seen.setdefault(key, set()).add(m['id'])
    issues = []
    for key, ids in seen.items():
        if len(ids) > 1 and (key[0], frozenset(ids)) not in SHARED_ROUTE_ALLOWLIST:
            issues.append({'id': '/'.join(sorted(ids)),
                           'problem': f'ルート「{key[0]}」が複数の山で完全に同一（他山からのコピー混入の疑い）'})
    return issues


def _minutes(text):
    """「約1時間20分」「約35分」「約2時間」を分に変換。"""
    out = []
    for h, mi in re.findall(r'約(?:(\d+)時間)?(?:(\d+)分)?', text):
        if not h and not mi:
            continue
        out.append((int(h) if h else 0) * 60 + (int(mi) if mi else 0))
    return out


def check_time_consistency(mountains):
    issues = []
    dep_fields = (('shinjuku', 'trainTimeShinjuku', 'trainAccess'),
                  ('omiya', 'trainTimeOmiya', 'trainAccessOmiya'),
                  ('yokohama', 'trainTimeYokohama', 'trainAccessYokohama'))
    for m in mountains:
        tr = (m.get('trainRoutes') or {}).get('routes') or {}
        for dep, tfield, afield in dep_fields:
            route = tr.get(dep)
            if not route:
                continue
            legs = route['legs']
            leg_mins = [l.get('durationMin') for l in legs if l.get('durationMin')]
            total = sum(leg_mins)
            t = m.get(tfield)
            # 表示時間は「legs合計＋乗換待ち」が許容（乗換1回あたり最大10分＋誤差2分）。合計より短い／乗換待ちを超える余分は不整合
            allowed = 10 * max(len(legs) - 1, 1) + 2
            if t is not None and (t < total or t - total > allowed):
                issues.append({'id': m['id'], 'problem': f'{tfield}={t} が legs 合計 {total} と不整合（許容: +0〜{allowed}分）'})
            # 文章中の所要時間は、括弧書きの補足（乗換込みの合計など）を除き、いずれかの leg の時間と一致すること
            text = m.get(afield) or ''
            if not isinstance(text, str):
                continue
            # 文章の時間は「単独のleg」または「連続するlegの合計」（乗換込みの表記）のどちらかに一致すること（±3分は丸め誤差として許容）
            sums = set(leg_mins)
            for i in range(len(leg_mins)):
                acc = 0
                for j in range(i, len(leg_mins)):
                    acc += leg_mins[j]
                    sums.add(acc)
            for mins in _minutes(re.sub(r'（[^）]*）|\([^)]*\)', '', text)):
                if not any(abs(mins - x) <= 3 for x in sums):
                    issues.append({'id': m['id'],
                                   'problem': f'{afield} の「{mins}分」が trainRoutes の legs（{sorted(set(leg_mins))}）に存在しない'})
                    break
    return issues


STATION_BEFORE_BUS = re.compile(r'([^\s→「」（）()<>＞>]{1,10}駅)」?(?:（[^）]*）)?→(?:[^→<]{0,25}?)バス')


def check_article_stations(mountains):
    """search/・articles/ の山カードにある「〇〇駅→…バス」の駅が、その山の経路データに存在するか。"""
    stations = {}
    for m in mountains:
        st = set()
        for r in ((m.get('trainRoutes') or {}).get('routes') or {}).values():
            for l in r['legs']:
                st.add(l['station'])
        for f in ('trainAccess', 'trainAccessOmiya', 'trainAccessYokohama'):
            if isinstance(m.get(f), str):
                st |= set(re.findall(r'([^\s→「」（）()]{1,10}駅)', m[f]))
        tr = m.get('trainRoutes') or {}
        for f in ('note', 'summaryNote'):
            if isinstance(tr.get(f), str):
                st |= set(re.findall(r'([^\s→「」（）()、。]{1,10}駅)', tr[f]))
        stations[m['id']] = st
    issues = []
    for sub in ('search', 'articles'):
        base = os.path.join(ROOT, sub)
        if not os.path.isdir(base):
            continue
        for slug in sorted(os.listdir(base)):
            path = os.path.join(base, slug, 'index.html')
            if not os.path.isfile(path):
                continue
            html = strip_scripts(read(path))
            for blk in re.split(r'(?=<div class="mountain-card)', html)[1:]:
                idm = re.search(r'data-mountain-id="([^"]+)"', blk) or re.search(r'href="/mountains/([^/"]+)/"', blk)
                if not idm or idm.group(1) not in stations:
                    continue
                # 山カード自身のアクセス行（mc-train）だけを対象にする（カード後ろのFAQ・注記の文章は他の山の話のことがある）
                text = ' '.join(re.sub(r'<[^>]+>', ' ', t) for t in re.findall(r'<div class="mc-train"[^>]*>(.*?)</div>', blk, re.S))
                for st in STATION_BEFORE_BUS.findall(text):
                    if not any(st == s2 or st in s2 or s2 in st for s2 in stations[idm.group(1)]):
                        issues.append({'id': idm.group(1),
                                       'problem': f'{sub}/{slug}: 「{st}→…バス」の駅が経路データに無い（{sorted(stations[idm.group(1)])[:6]}…）'})
                        break
    return issues


def check_coeff_anomalies(mountains):
    issues = []
    pat = re.compile(r'定数(\d+)〜(\d+)')
    for m in mountains:
        texts = [m.get('introHtml') or '', m.get('metaDescription') or '', m.get('ogDescription') or ''] + \
                [f.get('answer') or '' for f in m.get('faq') or []]
        for t in texts:
            for a, b in pat.findall(re.sub(r'<[^>]+>', '', t)):
                if int(b) > 100 or int(a) > int(b):
                    issues.append({'id': m['id'], 'problem': f'コース定数の異常値「定数{a}〜{b}」'})
        for r in m.get('routes') or []:
            c = r.get('coeff')
            if c is not None and (c < 1 or c > 120):
                issues.append({'id': m['id'], 'problem': f'ルート「{r.get("name")}」の coeff={c} が異常'})
    return issues


def check_restricted_listings(mountains):
    """規制中(restricted)の山が、通常の検索ページ・記事のおすすめに載っていないか。"""
    restricted = [m['id'] for m in mountains if (m.get('status') or {}).get('level') == 'restricted']
    issues = []
    for sub in ('search', 'articles'):
        base = os.path.join(ROOT, sub)
        if not os.path.isdir(base):
            continue
        for slug in sorted(os.listdir(base)):
            path = os.path.join(base, slug, 'index.html')
            if not os.path.isfile(path):
                continue
            html = read(path)
            blocks = re.split(r'(?=<div class="mountain-card)', html)[1:]
            for mid in restricted:
                if any(re.search(r'data-mountain-id="%s"|href="/mountains/%s/"' % (re.escape(mid), re.escape(mid)), b.split('<div class="mountain-card', 2)[1] if False else b[:6000]) for b in blocks):
                    issues.append({'id': mid, 'problem': f'規制中の山が {sub}/{slug} のおすすめカードに載っている'})
    return issues


ASSIGNED_SEAT_TRAINS = r'(?:あずさ|かいじ|富士回遊|富士山ビュー特急|スペーシア|サフィール踊り子|踊り子|ひたち|ときわ)'


def check_seat_terms(html_files):
    """全車指定席の特急に「自由席」と書いていないか。"""
    issues = []
    pat = re.compile(ASSIGNED_SEAT_TRAINS + r'[^。<]{0,60}自由席|自由席[^。<]{0,60}' + ASSIGNED_SEAT_TRAINS)
    for path in html_files:
        html = strip_scripts(read(path))
        txt = re.sub(r'<[^>]+>', '', html)
        for mm in pat.finditer(txt):
            ctx = txt[max(0, mm.start() - 15):mm.end() + 25]
            if re.search(r'ありません|ではない|はない|なし|指定席のみ|全車指定席', ctx):
                continue  # 「自由席はありません」等、正しい説明は除外
            issues.append({'id': rel(path), 'problem': '全車指定席の特急に「自由席」の記述がある'})
            break
    return issues


KNOWN_ISSUES_PATH = os.path.join(SCRIPT_DIR, 'check_known_issues.json')


def _issue_key(it):
    return f"{it['id']}|{it['problem']}"


def load_known():
    if os.path.isfile(KNOWN_ISSUES_PATH):
        with open(KNOWN_ISSUES_PATH, encoding='utf-8') as f:
            return json.load(f)
    return {}


def split_known(name, issues, known):
    """既知の未解決（調査待ちのレガシー）と新規に分ける。新規のみ異常として数える。"""
    k = set(known.get(name, []))
    new = [it for it in issues if _issue_key(it) not in k]
    old = [it for it in issues if _issue_key(it) in k]
    return new, old


def section(title, issues, formatter):
    lines = [f'## {title}（{len(issues)}件）']
    if not issues:
        lines.append('- 異常なし')
    else:
        for it in issues[:200]:
            lines.append('- ' + formatter(it))
        if len(issues) > 200:
            lines.append(f'- ...他 {len(issues) - 200} 件')
    lines.append('')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', metavar='PATH', help='結果をJSONでも出力するファイルパス')
    ap.add_argument('--only', choices=['mountains'], help='mountains/配下のみ検査する')
    ap.add_argument('--update-baseline', action='store_true',
                    help='セクション10・11の現在の指摘を「既知の未解決」として check_known_issues.json に保存する')
    args = ap.parse_args()

    mountains = load_mountains()
    html_files = list(iter_html_files(only='mountains' if args.only == 'mountains' else None))

    broken_links = check_broken_links(html_files)
    broken_images = check_broken_images(html_files)
    required_field_issues = check_required_fields(mountains)
    seo_issues, titles = check_seo_meta(html_files)
    title_dupes = check_title_duplicates(titles)
    mismatch_issues = check_json_html_mismatch(mountains)
    transit_issues = check_transit_section(mountains)
    train_routes_issues = check_train_routes_schema(mountains)
    route_dup_issues = check_route_duplicates(mountains)
    time_issues = check_time_consistency(mountains)
    station_issues = check_article_stations(mountains)
    coeff_issues = check_coeff_anomalies(mountains)
    restricted_issues = check_restricted_listings(mountains)
    seat_issues = check_seat_terms(html_files)

    if args.update_baseline:
        with open(KNOWN_ISSUES_PATH, 'w', encoding='utf-8') as f:
            json.dump({'10': sorted(_issue_key(i) for i in time_issues),
                       '11': sorted(_issue_key(i) for i in station_issues)}, f, ensure_ascii=False, indent=1)
        print('baseline updated:', len(time_issues), len(station_issues))
    known = load_known()
    time_issues, time_known = split_known('10', time_issues, known)
    station_issues, station_known = split_known('11', station_issues, known)

    report = []
    report.append('# YAMATCH 公開前自動チェック結果\n')
    report.append(section('1. 画像切れ', broken_images,
                           lambda it: f"{it['file']} → {it['url']}"))
    report.append(section('2. リンク切れ', broken_links,
                           lambda it: f"{it['file']} → {it['url']}"))
    report.append(section('3. 必須データ欠損（mountains.json）', required_field_issues,
                           lambda it: f"{it['id']}: {it['field']} — {it['problem']}"))
    report.append(section('4. title / description / canonical 欠損', seo_issues,
                           lambda it: f"{it['file']} — {it['problem']}"))
    report.append(section('5. title 重複', title_dupes,
                           lambda it: f"「{it['title']}」 — {', '.join(it['files'])}"))
    report.append(section('6. JSON と HTML の情報不一致', mismatch_issues,
                           lambda it: f"{it['id']}: {it['problem']}"
                                      + (f" (json={it['json']}, html={it.get('html', it.get('html_extra'))})"
                                         if 'json' in it else '')))
    report.append(section('7. 交通情報の欠損／不整合', transit_issues,
                           lambda it: f"{it['id']}: {it['problem']}"))
    report.append(section('8. trainRoutes構造化データの整合性', train_routes_issues,
                           lambda it: f"{it['id']}: {it['problem']}"))
    fmt = lambda it: f"{it['id']}: {it['problem']}"
    report.append(section('9. ルートの他山コピー', route_dup_issues, fmt))
    report.append(section('10. 所要時間の不一致（legs合計・文章）', time_issues, fmt))
    report.append(section('11. 記事・検索ページの駅名', station_issues, fmt))
    report.append(section('12. コース定数の異常値', coeff_issues, fmt))
    report.append(section('13. 規制中の山の掲載', restricted_issues, fmt))
    report.append(section('14. 特急の座席制度', seat_issues, fmt))
    report.append(f"## 参考：既知の未解決（調査待ちのレガシー。件数に含めない）\n- 10. 所要時間: {len(time_known)}件 / 11. 駅名: {len(station_known)}件（scripts/check_known_issues.json）\n")

    text = '\n'.join(report)
    print(text)

    total = (len(broken_links) + len(broken_images) + len(required_field_issues)
             + len(seo_issues) + len(title_dupes) + len(mismatch_issues) + len(transit_issues)
             + len(train_routes_issues) + len(route_dup_issues) + len(time_issues)
             + len(station_issues) + len(coeff_issues) + len(restricted_issues) + len(seat_issues))

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump({
                'broken_links': broken_links,
                'broken_images': broken_images,
                'required_field_issues': required_field_issues,
                'seo_issues': seo_issues,
                'title_duplicates': title_dupes,
                'json_html_mismatch': mismatch_issues,
                'transit_issues': transit_issues,
                'train_routes_issues': train_routes_issues,
                'route_duplicates': route_dup_issues,
                'time_issues': time_issues,
                'station_issues': station_issues,
                'coeff_anomalies': coeff_issues,
                'restricted_listings': restricted_issues,
                'seat_terms': seat_issues,
                'total': total,
            }, f, ensure_ascii=False, indent=2)

    sys.exit(1 if total > 0 else 0)


if __name__ == '__main__':
    main()
