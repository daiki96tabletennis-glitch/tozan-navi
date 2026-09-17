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
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__MACOSX']
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

        # 注: trainTimeShinjuku/Yokohama/Omiya は、どの山ページのHTML/JSからも参照されていない
        # 孤立フィールドであることが判明した（ts-time-valとの連動関係が元から存在しない）ため、
        # 所要時間の同期チェックは見送っている。運用ガイド(README.md)の既知課題に記載。

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


# --- レポート出力 ----------------------------------------------------------

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

    text = '\n'.join(report)
    print(text)

    total = (len(broken_links) + len(broken_images) + len(required_field_issues)
             + len(seo_issues) + len(title_dupes) + len(mismatch_issues) + len(transit_issues))

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
                'total': total,
            }, f, ensure_ascii=False, indent=2)

    sys.exit(1 if total > 0 else 0)


if __name__ == '__main__':
    main()
