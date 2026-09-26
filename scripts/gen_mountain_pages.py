#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_mountain_pages.py

mountains.json (+ data/gear-data.json) を正本データとして、
mountains/<id>/index.html を自動生成するスクリプト。

使い方:
    python scripts/gen_mountain_pages.py --id takao
    python scripts/gen_mountain_pages.py --all
    python scripts/gen_mountain_pages.py --all --dry-run

設計方針:
- 既存の mountains/<id>/index.html を「入力」として読み込む必要はない
  （正本データ = data/mountains.json + data/gear-data.json + 本スクリプトの
  生成ロジック + scripts/_base_mountain_style.css + scripts/_weather_widget_block.html
  だけで全156山を再生成できる）。
- 一部の項目（アクセス説明文・関連リンク・地図ボタン等）は、山ごとに長期間
  手修正された編集的コンテンツのため、生成ロジックで再現せず
  mountains.json 側にHTMLスニペットとして正本化した「不透明フィールド」
  （vibesHtml / introHtml / dlNoteHtml / dlReasonsHtml / trainAccessHtml /
  relatedLinksHtml / mapBtnsHtml / metaTitle / metaDescription）をそのまま
  出力する。これらは extract_opaque_fields.py 等で mountains.json に
  書き込み済みで、本スクリプトはそれを読むだけで、既存HTMLファイルには
  一切アクセスしない。
- 出力は書き込み前に一時ファイルに書いてから置換し、生成結果が既存と
  同一なら書き換えを行わない（べき等性）。
- 必須データが欠けている場合は例外を送出し、そのファイルの上書きをしない。
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_recommend_gear  # noqa: E402  (診断用月別装備JSONの生成。gear-data.json変更時に同時更新するため)
from render_transit_routes import render_ts_section  # noqa: E402  (trainRoutes構造化データからのHTML生成。2026-09-23移行)

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(SITE_ROOT, "data", "mountains.json")
GEAR_DATA_PATH = os.path.join(SITE_ROOT, "data", "gear-data.json")
BASE_CSS_PATH = os.path.join(SITE_ROOT, "scripts", "_base_mountain_style.css")
WEATHER_BLOCK_PATH = os.path.join(SITE_ROOT, "scripts", "_weather_widget_block.html")
HERO_PHOTO_SCRIPT_PATH = os.path.join(SITE_ROOT, "scripts", "_hero_photo_script.html")

# id を持たない例外ページ（mountains/ 配下だが mountains.json に存在しない、
# または独自の役割を持つ特殊ページ）。gen_mountain_pages.py は一切触れない。
EXCLUDED_DIRS = {"daibosatsurei", "nikko_nantai", "shirane_nikko", "takao-hiking"}

# mountains.json には存在するが、head部のJSON-LD形式（@graph/TouristAttraction）や
# ページ構造そのものが他の155山と根本的に異なる特殊構造ページ。
# 安全に自動生成できると確認できるまでは対象外とし、既存HTMLを保持する。
EXCLUDED_IDS = {"tanzawa"}

DEP_ORDER = [
    ("大船駅", "driveOfuna", "ofuna"),
    ("新宿駅", "driveShinjuku", "shinjuku"),
    ("横浜駅", "driveYokohama", "yokohama"),
    ("大宮駅", "driveOmiya", "omiya"),
    ("立川駅", "driveTachikawa", "tachikawa"),
]
# ai-a グリッドは 大船/横浜/新宿/大宮/立川 の順で表示される
AIA_ORDER = [
    ("大船駅", "driveOfuna"),
    ("横浜駅", "driveYokohama"),
    ("新宿駅", "driveShinjuku"),
    ("大宮駅", "driveOmiya"),
    ("立川駅", "driveTachikawa"),
]

DIFF_SCORE = {"初級": 2, "初〜中級": 4, "中級": 6, "中〜上級": 8, "上級": 10, "初〜上級": 6}
DIFF_BADGE_COLOR = {
    "初級": ("#edf4e8", "#3a5a3a"),
    "初〜中級": ("#edf4e8", "#3a5a3a"),
    "中級": ("#f8f0e0", "#7a6020"),
    "中〜上級": ("#fde8d8", "#8a5010"),
    "上級": ("#fde8e8", "#8a2020"),
    "初〜上級": ("#f8f0e0", "#7a6020"),
}
CAR_ACCESS_MAX_MIN = 360  # 6時間 = バーの100%


class GenError(Exception):
    pass


def require(mt, field):
    v = mt.get(field)
    if v is None or v == "":
        raise GenError(f"{mt.get('id')}: 必須フィールド {field} が欠損しています")
    return v


def esc(s):
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt_min(minutes):
    """分 -> 'N時間M分' / 'N時間' 形式"""
    minutes = int(round(minutes))
    h = minutes // 60
    m = minutes % 60
    if h == 0:
        return f"{m}分"
    if m == 0:
        return f"{h}時間"
    return f"{h}時間{m}分"


def fmt_elevation(elevation):
    return f"{elevation:,}"


def fmt_hero_time(minutes):
    """ymFormatHeroTime() (mountain-engine.js) と同じロジックで
    hero-time の初期表示値・単位を計算する。"""
    if minutes is None:
        return "-", "時間〜"
    minutes = int(minutes)
    if minutes < 60:
        return str(minutes), "分〜"
    hrs = minutes / 60
    s = f"{hrs:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    return s, "時間〜"


_CSS_CACHE = {}


def load_static_assets():
    if "css" not in _CSS_CACHE:
        with open(BASE_CSS_PATH, encoding="utf-8") as f:
            _CSS_CACHE["css"] = f.read()
        with open(WEATHER_BLOCK_PATH, encoding="utf-8") as f:
            _CSS_CACHE["weather"] = f.read()
        with open(HERO_PHOTO_SCRIPT_PATH, encoding="utf-8") as f:
            _CSS_CACHE["hero_photo"] = f.read()
    return _CSS_CACHE["css"], _CSS_CACHE["weather"]


def load_hero_photo_script():
    load_static_assets()
    return _CSS_CACHE["hero_photo"]


FONT_STYLE_TAG = (
    '<style>h1,h2,h3,.ym-logo,.type-name,.mountain-name,.sec-title,'
    '.header-title{font-family:"Zen Kaku Gothic New",-apple-system,sans-serif;}</style>'
)

GTAG_BLOCK = (
    '<!-- Google tag (gtag.js) -->\n'
    '<script async src="https://www.googletagmanager.com/gtag/js?id=G-TMTVVTEEGF"></script>\n'
    '<script>\n'
    '  window.dataLayer = window.dataLayer || [];\n'
    '  function gtag(){dataLayer.push(arguments);}\n'
    "  gtag('js', new Date());\n"
    "  gtag('config', 'G-TMTVVTEEGF');\n"
    '</script>\n'
    '<link rel="apple-touch-icon" sizes="180x180" href="/icon-180.png">\n'
    '<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">\n'
    '<link rel="icon" type="image/png" sizes="32x32" href="/favicon.ico">\n'
    '<link rel="manifest" href="/manifest.json">\n'
)

FONTS_LINK = (
    '<link href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@700;900'
    '&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">\n'
)

HEADER_BLOCK = (
    '<header>\n'
    '  <div class="header-inner">\n'
    '    <a href="/" style="display:flex;align-items:center;gap:6px;text-decoration:none;'
    'flex:1;min-width:0;"><svg width="24" height="24" viewBox="0 0 36 36" '
    'style="flex-shrink:0"><polygon points="18,4 34,30 2,30" fill="#405830"/>'
    '<polygon points="18,10 30,30 6,30" fill="#6a8055"/>'
    '<polygon points="10,30 17,17 24,30" fill="#2c4020"/></svg>\n'
    '      <div class="header-title" style="color:white;font-size:20px;font-weight:700;'
    'font-family:Georgia,serif;line-height:1;">Yamatch</div>\n'
    '    </a>\n'
    '    <a href="/" class="back-btn">← 一覧に戻る</a>\n'
    '  </div>\n'
    '  <div class="dep-row" id="dep-row">\n'
    "    <button class=\"dep-btn-m\" onclick=\"changeDep('大船')\">大船駅</button>\n"
    "    <button class=\"dep-btn-m\" onclick=\"changeDep('新宿')\">新宿駅</button>\n"
    "    <button class=\"dep-btn-m\" onclick=\"changeDep('横浜')\">横浜駅</button>\n"
    "    <button class=\"dep-btn-m\" onclick=\"changeDep('大宮')\">大宮駅</button>\n"
    "    <button class=\"dep-btn-m\" onclick=\"changeDep('立川')\">立川駅</button>\n"
    '  </div>\n'
    '</header>\n'
)

GEAR_NOTE = (
    '<div class="gear-note">※価格・在庫は変動します。最新情報は各リンク先でご確認ください。'
    '当サイトはAmazonアソシエイト・楽天アフィリエイトを利用しています。</div>'
)

NOTE_BLOCK = (
    '  <div class="note">\n'
    '    <strong>⚠ ご注意</strong><br>\n'
    '    所要時間は高速道路利用時の目安です。交通状況や季節により大きく変動します。'
    '登山前は必ず最新の道路状況・登山道情報・天気予報をご確認ください。\n'
    '  </div>\n'
)

FEEDBACK_LINK_BLOCK = (
    '  <div style="text-align:center;margin-bottom:16px;">\n'
    '    <a href="https://forms.gle/qsXvFTcj6H1TM7ra7" target="_blank" '
    'style="font-size:11px;color:#a09888;text-decoration:underline;'
    'text-underline-offset:3px;">情報の誤り・改善提案はこちら</a>\n'
    '  </div>\n'
)

FOOTER_BLOCK = (
    '<footer style="text-align:center;padding:20px 16px;font-size:12px;color:#a09888;'
    'border-top:1px solid #e8e4dc;margin-top:8px">\n'
    '  <p>Yamatch — 出発地から登る山を探せる登山サーチ</p>\n'
    '  <p style="margin-top:6px">\n'
    '    <a href="/terms/" style="color:#6a8055">利用規約</a>\n'
    '    <span style="margin:0 8px;opacity:0.4">|</span>\n'
    '    <a href="/privacy/" style="color:#6a8055">プライバシーポリシー</a>\n'
    '    <span style="margin:0 8px;opacity:0.4">|</span>\n'
    '    <a href="/about/" style="color:#6a8055">運営者</a>\n'
    '  </p>\n'
    '  <p style="margin-top:8px;opacity:0.6;">© 2026 Yamatch. All rights reserved.</p>\n'
    '</footer>\n'
)

NEARBY_STICKY_SCRIPT = (
    '<div class="nearby-sticky" id="nearby-sticky-bar" style="display:none">\n'
    '  <div class="nearby-sticky-heading">近くて似た山</div>\n'
    '  <div class="nearby-sticky-row" id="nearby-sticky-items"></div>\n'
    '</div>\n'
    '\n'
    '\n'
    '<a href="#" class="nearby-sticky" id="nearby-sticky-bar" style="display:none">\n'
    '  <span><span class="nearby-sticky-label">近くて似た山</span>'
    '<span class="nearby-sticky-name" id="nearby-sticky-name"></span></span>\n'
    '  <span class="nearby-sticky-arrow">→</span>\n'
    '</a>\n'
    '<script>\n'
    '(function(){\n'
    "  var firstCard = document.querySelector('.rg .rc');\n"
    '  if(!firstCard) return;\n'
    "  var bar = document.getElementById('nearby-sticky-bar');\n"
    "  var nameEl = document.getElementById('nearby-sticky-name');\n"
    "  var nameSrc = firstCard.querySelector('.rn');\n"
    '  if(!nameSrc) return;\n'
    "  bar.href = firstCard.getAttribute('href');\n"
    '  nameEl.textContent = nameSrc.textContent;\n'
    "  var relSection = document.querySelector('.rw');\n"
    '  var shown = false;\n'
    "  window.addEventListener('scroll', function(){\n"
    '    var scrollY = window.scrollY || document.documentElement.scrollTop;\n'
    '    var pastThreshold = scrollY > 700;\n'
    '    var pastSection = relSection ? (relSection.getBoundingClientRect().top < '
    'window.innerHeight * 0.3) : false;\n'
    '    var shouldShow = pastThreshold && !pastSection;\n'
    "    if(shouldShow && !shown){ bar.style.display='flex'; "
    "requestAnimationFrame(function(){bar.classList.add('visible');}); shown = true; }\n"
    "    else if(!shouldShow && shown){ bar.classList.remove('visible'); shown = false; }\n"
    '  }, {passive:true});\n'
    '})();\n'
    '</script>\n'
)


def render_head(mt):
    title = esc(require(mt, "metaTitle"))
    desc = esc(require(mt, "metaDescription"))
    og_title = esc(mt.get("ogTitle") or mt["metaTitle"])
    og_desc = esc(mt.get("ogDescription") or mt["metaDescription"])
    mid = mt["id"]
    url = f"https://tozan-navi.com/mountains/{mid}/"
    updated = mt.get("ogUpdatedTime") or "2026-01-01T00:00:00+09:00"
    css, _ = load_static_assets()

    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="ja">')
    parts.append("<head>")
    parts.append('<meta charset="UTF-8">')
    parts.append('<meta name="viewport" content="width=device-width,initial-scale=1.0">')
    parts.append(f"<title>{title}</title>")
    parts.append(f'<meta name="description" content="{desc}">')
    parts.append(f'<meta property="og:title" content="{og_title}">')
    parts.append(f'<meta property="og:description" content="{og_desc}">')
    parts.append('<meta property="og:image" content="https://tozan-navi.com/ogp.png">')
    parts.append(f'<meta property="og:url" content="{url}">')
    parts.append('<meta property="og:type" content="article">')
    parts.append('<meta name="twitter:card" content="summary_large_image">')
    parts.append(f'<meta property="og:updated_time" content="{updated}">')
    parts.append(f'<link rel="canonical" href="{url}">')
    parts.append(
        '<meta name="google-site-verification" '
        'content="dJ2byH9b8xF8S5lqAyWV-DqRwPGLEjWXs_-Un9oXGHs" />'
    )
    parts.append('<link rel="stylesheet" href="../../assets/css/mountain.css">')
    parts.append(f"<style>{css}</style>")
    parts.append(GTAG_BLOCK.rstrip("\n"))
    parts.append(render_jsonld(mt))
    parts.append(FONTS_LINK.rstrip("\n"))
    parts.append(FONT_STYLE_TAG)
    parts.append("</head>")
    return "\n".join(parts)


def render_jsonld(mt):
    mid = mt["id"]
    name = mt["name"]
    url = f"https://tozan-navi.com/mountains/{mid}/"
    faq = mt.get("faq") or []
    faq_obj = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in faq
        ],
    }
    breadcrumb_obj = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Yamatch", "item": "https://tozan-navi.com/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": url},
        ],
    }
    lines = []
    if faq:
        lines.append(
            '<script type="application/ld+json">'
            + json.dumps(faq_obj, ensure_ascii=False)
            + "</script>"
        )
    lines.append(
        '<script type="application/ld+json">'
        + json.dumps(breadcrumb_obj, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )
    return "\n".join(lines)


def render_bookmark_tabs(mt):
    tabs = []
    if mt.get("hasWeatherWidget"):
        tabs.append(("weather-card", "天気"))
    if mt.get("trainAccessHtml"):
        tabs.append(("sec-train", "電車・バス"))
    tabs.append(("sec-car", "車アクセス時間"))
    tabs.append(("sec-parking", "登山口・駐車場"))
    tabs.append(("sec-season", "アイゼン要否"))
    tabs.append(("sec-routes", "ルート"))
    tabs.append(("sec-gear", "装備"))
    buttons = "".join(
        f'<button type="button" class="bookmark-tab" data-target="{target}">{label}</button>'
        for target, label in tabs
    )
    return f'<div class="bookmark-tabs" id="bookmark-tabs">{buttons}</div>'


def render_hero(mt):
    name = esc(require(mt, "name"))
    kana = esc(mt.get("kana") or "")
    area = esc(require(mt, "area"))
    category = esc(mt.get("category") or "")
    difficulty = esc(require(mt, "difficulty"))
    elevation = require(mt, "elevation")
    coeff_range = esc(require(mt, "courseCoefficientRange"))
    ofuna_min = mt.get("driveOfuna")
    hero_time, hero_unit = fmt_hero_time(ofuna_min)

    return (
        f'<div class="hero-new{" hero-100" if mt.get("category") == "百名山" else ""}">\n'
        '    <svg class="hero-bg-svg" viewBox="0 0 100 60" fill="#2a5010" style="opacity:0.04">\n'
        '      <polygon points="50,5 95,55 5,55"/><polygon points="75,20 100,55 50,55"/>'
        '<polygon points="20,28 50,55 0,55"/>\n'
        '    </svg>\n'
        '    <div class="hero-top">\n'
        '      <div>\n'
        f'        <h1 class="mountain-name">{name}</h1>\n'
        f'        <div class="mountain-kana">{kana}</div>\n'
        f'        <div class="mountain-area">📍 {area}</div>\n'
        '        <div class="hero-badges">\n'
        f'          <span class="cat-badge-new">{category}</span>\n'
        f'          <span class="diff-badge-new">{difficulty}</span>\n'
        '        </div>\n'
        '      </div>\n'
        '    </div>\n'
        '    <div class="stats-row">\n'
        f'      <div class="stat-card"><div class="stat-val">{fmt_elevation(elevation)}</div>'
        '<div class="stat-unit">m</div><div class="stat-label">標高</div></div>\n'
        f'      <div class="stat-card"><div class="stat-val">{coeff_range}</div>'
        '<div class="stat-unit">コース定数</div>'
        f'<div class="stat-label">難易度：{difficulty}</div></div>\n'
        '      <div class="stat-card" id="hero-access"><div class="stat-val" id="hero-time">'
        f'{hero_time}</div><div class="stat-unit" id="hero-unit">{hero_unit}</div>'
        '<div class="stat-label" id="hero-dep-label">大船から</div></div>\n'
        '    </div>\n'
        '  </div>'
    )


def render_dl_card(mt):
    difficulty = esc(require(mt, "difficulty"))
    score = DIFF_SCORE.get(mt["difficulty"], 5)
    if mt["difficulty"] == "上級":
        on_class = "dl-seg on hard"
    elif mt["difficulty"] == "中〜上級":
        on_class = "dl-seg on warn"
    else:
        on_class = "dl-seg on"
    segs = "".join(
        f'<div class="{on_class if i < score else "dl-seg"}"></div>' for i in range(10)
    )
    note_html = mt.get("dlNoteHtml") or ""
    reasons_html = mt.get("dlReasonsHtml") or ""
    tail = note_html or reasons_html or ""
    return (
        '<div class="card dl-card">\n'
        '  <h2 style="font-size:15px;font-weight:700;color:#2a3820;margin-bottom:8px;'
        'padding-bottom:6px;border-bottom:2px solid #eaf1e0;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" style="vertical-align:-3px;'
        'margin-right:4px" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3 20 L9 8 L13 15 L16 11 L21 20 Z"/></svg>難易度</h2>\n'
        '  <div class="dl-head">\n'
        '    <span class="dl-label">難易度</span>\n'
        f'    <span class="dl-value">{difficulty}</span>\n'
        f'    <span class="dl-score">10段階中 {score}</span>\n'
        '  </div>\n'
        f'  <div class="dl-bar">{segs}</div>\n'
        '  <div class="dl-scale"><span>やさしい</span><span>難しい</span></div>\n'
        f'  {tail}\n'
        '</div>'
    )


def render_weather(mt):
    if not mt.get("hasWeatherWidget"):
        return ""
    _, weather_tpl = load_static_assets()
    return weather_tpl.replace("__MID__", mt["id"])


def render_train_access(mt):
    # 2026-09-23移行: trainRoutes(構造化データ)があればそちらから生成する。
    # 合計所要時間・運賃はレグ合計からではなく既存のtrainTimeXxx/fareXxxを使う
    # （理由はclaude/transit-data-restructure-plan.mdのPhase1検証結果を参照）。
    # trainRoutesが無い場合（車のみ山、パース対象外）は旧来のtrainAccessHtmlに
    # フォールバックし、既存表示を壊さない。
    train_routes = mt.get("trainRoutes")
    if train_routes:
        ts = render_ts_section(train_routes, mt)
        if ts:
            return f'<div class="card" id="sec-train">\n  {ts}\n</div>'
    ts = mt.get("trainAccessHtml")
    if not ts:
        return ""
    return f'<div class="card" id="sec-train">\n  {ts}\n</div>'


def render_car_access(mt):
    rows = []
    for dep, field in AIA_ORDER:
        minutes = mt.get(field)
        if minutes is None:
            continue
        pct = min(100, round(minutes / CAR_ACCESS_MAX_MIN * 100))
        rows.append(
            f'<div class="ai-a" data-dep="{dep}" data-min="{minutes}">'
            f'<div class="ai-a-dep">{dep}</div>'
            f'<div class="ai-a-bar-wrap"><div class="ai-a-bar" style="width:{pct}%"></div></div>'
            f'<div class="ai-a-val">{fmt_min(minutes)}</div></div>'
        )
    rows_html = "\n".join(rows)
    return (
        '<div class="card" id="sec-car"><h2><svg width="16" height="16" viewBox="0 0 24 24" '
        'style="vertical-align:-3px;margin-right:4px"><path d="M4 13l1.5-4A2 2 0 0 1 7.3 8h9.4a2 '
        '2 0 0 1 1.8 1.2L20 13z" fill="currentColor"/><rect x="2.5" y="13" width="19" height="4.5" '
        'rx="2" fill="currentColor"/><rect x="6.5" y="9.2" width="4" height="2.8" rx="0.5" '
        'fill="white"/><rect x="11.5" y="9.2" width="6" height="2.8" rx="0.5" fill="white"/>'
        '<circle cx="6.5" cy="17.5" r="1.6" fill="#3a3530"/><circle cx="17.5" cy="17.5" r="1.6" '
        'fill="#3a3530"/></svg>車でのアクセス時間</h2>\n'
        f'    <div class="ag-a" id="access-grid">\n{rows_html}\n    </div>\n'
        '  </div>'
    )


def render_parking(mt):
    trailhead = esc(require(mt, "trailhead"))
    parking = esc(mt.get("parking") or "")
    address = esc(mt.get("address") or mt.get("trailheadAddress") or "")
    map_btns = mt.get("mapBtnsHtml") or ""
    return (
        '<div class="card" id="sec-parking"><h2><svg width="16" height="16" viewBox="0 0 24 24" '
        'style="vertical-align:-3px;margin-right:4px" fill="none" stroke="currentColor" '
        'stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="3"/>'
        '<path d="M9 16V8h3.5a2.5 2.5 0 0 1 0 5H9" stroke-linecap="round" '
        'stroke-linejoin="round"/></svg>登山口・駐車場</h2>\n'
        '<div class="info-rows">\n'
        f'<div class="info-row"><span class="info-label">登山口</span>'
        f'<span class="info-val">{trailhead}</span></div>\n'
        f'<div class="info-row"><span class="info-label">駐車場</span>'
        f'<span class="info-val">{parking}</span></div>\n'
        f'<div class="info-row"><span class="info-label">住所</span>'
        f'<span class="info-val">{address}</span></div>\n'
        '</div>\n'
        f'{map_btns}\n'
        '</div>'
    )


def render_season(mt):
    cal = require(mt, "seasonCalendar")
    legend = mt.get("calLegend") or []
    months = "".join(
        f'<div class="cal-m"><div class="cal-l">{i+1}</div>'
        f'<div class="cal-b {cal[i]}"></div></div>'
        for i in range(12)
    )
    colors = ["#c8d4b8", "#d4c19a", "#b08868"]
    legend_html = "".join(
        f'<div class="leg"><div class="leg-dot" style="background:{colors[i]}"></div>{esc(t)}</div>'
        for i, t in enumerate(legend[:3])
    )
    return (
        '<div class="card" id="sec-season"><h2><svg width="16" height="16" viewBox="0 0 24 24" '
        'style="vertical-align:-3px;margin-right:4px" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="5" width="18" height="16" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/>'
        '<line x1="8" y1="3" x2="8" y2="7"/><line x1="16" y1="3" x2="16" y2="7"/></svg>'
        'シーズンカレンダー</h2>\n'
        f'    <div class="calendar">{months}</div>\n'
        f'    <div class="cal-legend">\n  {legend_html}\n</div>\n'
        '  </div>'
    )


def render_routes(mt):
    routes = require(mt, "routes")
    items = []
    for i, r in enumerate(routes, start=1):
        name = esc(r.get("name") or "")
        chips = []
        if r.get("time"):
            chips.append(f'<span class="rl-chip">⏱&nbsp;{esc(r["time"])}</span>')
        if r.get("distance"):
            chips.append(f'<span class="rl-chip">距離&nbsp;{esc(r["distance"])}</span>')
        if r.get("elevation"):
            chips.append(f'<span class="rl-chip">↑&nbsp;{esc(r["elevation"])}</span>')
        if r.get("coeff") is not None:
            chips.append(f'<span class="rl-chip">定数&nbsp;{esc(r["coeff"])}</span>')
        waypoints_html = ""
        if r.get("waypoints"):
            waypoints_html = f'<div class="rl-waypoints">{esc(r["waypoints"])}</div>'
        items.append(
            f'<div class="rl-item"><div class="rl-num">{i}</div><div class="rl-content">'
            f'<div class="rl-name">{name}</div>{waypoints_html}'
            f'<div class="rl-chips">{"".join(chips)}</div></div></div>'
        )
    items_html = "".join(items)
    coeff_note = ""
    if any(r.get("coeff") is not None for r in routes):
        coeff_note = ('<p style="font-size:11px;color:#9a9088;margin-top:8px;line-height:1.6;">'
                      '※ルートごとの定数は、時間・距離・累積標高差から一般式で算出した目安です'
                      '（下りの累積標高差は登りと同じと仮定）。</p>')
    return (
        '<div class="card" id="sec-routes"><h2><svg width="16" height="16" viewBox="0 0 24 24" '
        'style="vertical-align:-3px;margin-right:4px" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="5" cy="19" r="2"/><circle cx="19" cy="5" r="2"/>'
        '<path d="M5 17 C5 12 9 12 9 9 C9 6 12 6 12 9 C12 13 19 13 19 7"/></svg>'
        f'代表的な登山ルート</h2><div class="route-list-c">{items_html}</div>{coeff_note}</div>'
    )


def render_yamap(mt):
    url = mt.get("yamapUrl")
    if not url:
        return ""
    return (
        f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer" class="yamap-btn">\n'
        '    <svg width="18" height="18" viewBox="0 0 36 36" fill="#4e6535">'
        '<polygon points="18,4 34,30 2,30"/>'
        '<polygon points="18,10 30,30 6,30" fill="#6a8055"/></svg>\n'
        '    YAMAPで詳細を見る\n'
        '  </a>'
    )


def render_climbed(mt):
    mid = mt["id"]
    style = mt.get("climbedBtnStyle", "flat")
    if style == "rounded":
        btn_style = (
            "width:100%;display:flex;align-items:center;justify-content:center;gap:8px;"
            "background:white;color:#4e6535;font-weight:700;font-size:15px;padding:15px;"
            "border-radius:12px;border:2px solid #c8d4b8;margin-bottom:12px;cursor:pointer;"
            "-webkit-tap-highlight-color:transparent;"
        )
        icon_html = '    <span id="climbed-icon">🏳</span>\n'
        icon_on = "        icon.textContent='🚩';\n"
        icon_off = "        icon.textContent='🏳';\n"
        border_off = "        btn.style.borderColor='#c8d4b8';\n"
        cel_icon = '<div style="font-size:36px;margin-bottom:6px">🚩</div>'
    else:
        btn_style = (
            "width:100%;display:flex;align-items:center;justify-content:center;gap:8px;"
            "background:white;color:#4e6535;font-weight:700;font-size:15px;padding:15px;"
            "border-radius:4px;border:1.5px solid #1a1a16;margin-bottom:12px;cursor:pointer;"
            "-webkit-tap-highlight-color:transparent;"
        )
        icon_html = (
            '    <svg id="climbed-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M4 21V4a1 1 0 0 1 1-1h11l-2 5 2 5H6"/></svg>\n'
        )
        icon_on = (
            "        icon.innerHTML='<path d=\"M4 21V4a1 1 0 0 1 1-1h11l-2 5 2 5H6\" "
            "fill=\"currentColor\"/>';\n"
        )
        icon_off = (
            "        icon.innerHTML='<path d=\"M4 21V4a1 1 0 0 1 1-1h11l-2 5 2 5H6\"/>';\n"
        )
        border_off = "        btn.style.borderColor='#1a1a16';\n"
        cel_icon = (
            '<div style="margin-bottom:6px"><svg width="32" height="32" viewBox="0 0 24 24" '
            'fill="none" stroke="white" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"><path d="M4 21V4a1 1 0 0 1 1-1h11l-2 5 2 5H6"/></svg></div>'
        )
    return (
        '<!-- 登頂記録ボタン -->\n'
        f'  <button id="climbed-btn" onclick="toggleClimbed()" style="{btn_style}">\n'
        f'{icon_html}'
        '    <span id="climbed-label">登頂記録に追加</span>\n'
        '  </button>\n'
        '  <script>\n'
        '  (function(){\n'
        f"    var MTN_ID = '{mid}';\n"
        "    var CLM_KEY = 'ym_climbed';\n"
        "    function getArr(){ try{ return JSON.parse(localStorage.getItem(CLM_KEY)||'[]'); "
        "}catch(e){ return []; } }\n"
        "    function isClimbed(){ return getArr().some(function(e){ return e[0]===MTN_ID; }); }\n"
        '    function updateBtn(){\n'
        "      var btn = document.getElementById('climbed-btn');\n"
        "      var icon = document.getElementById('climbed-icon');\n"
        "      var label = document.getElementById('climbed-label');\n"
        '      if (!btn) return;\n'
        '      if (isClimbed()){\n'
        "        btn.style.background='#eaf1e0';\n"
        "        btn.style.borderColor='#4e6535';\n"
        "        btn.style.color='#2a4820';\n"
        f"{icon_on}"
        "        label.textContent='登頂済み（タップで解除）';\n"
        '      } else {\n'
        "        btn.style.background='white';\n"
        f"{border_off}"
        "        btn.style.color='#4e6535';\n"
        f"{icon_off}"
        "        label.textContent='登頂記録に追加';\n"
        '      }\n'
        '    }\n'
        '    window.toggleClimbed = function(){\n'
        '      var arr = getArr();\n'
        '      if (isClimbed()){\n'
        "        if (!confirm('登頂記録を解除しますか？')) return;\n"
        '        arr = arr.filter(function(e){ return e[0]!==MTN_ID; });\n'
        '        localStorage.setItem(CLM_KEY, JSON.stringify(arr));\n'
        '      } else {\n'
        "        var today = new Date().toISOString().slice(0,10);\n"
        "        arr.push([MTN_ID, today, '']);\n"
        '        localStorage.setItem(CLM_KEY, JSON.stringify(arr));\n'
        '        // お祝い表示\n'
        "        var cel = document.createElement('div');\n"
        "        cel.style.cssText='position:fixed;top:50%;left:50%;transform:translate(-50%,"
        "-50%);background:rgba(20,45,15,0.92);color:white;border-radius:16px;padding:20px 32px;"
        "text-align:center;z-index:9999;font-family:sans-serif;animation:celPop .35s "
        "cubic-bezier(.34,1.56,.64,1)';\n"
        f"        cel.innerHTML='{cel_icon}"
        "<div style=\"font-size:16px;font-weight:800\">登頂記録に追加しました！</div>"
        "<div style=\"font-size:12px;margin-top:4px;opacity:0.7\">マイページで確認できます</div>';\n"
        '        document.body.appendChild(cel);\n'
        '        setTimeout(function(){ cel.remove(); }, 1800);\n'
        '      }\n'
        '      updateBtn();\n'
        '    };\n'
        '    updateBtn();\n'
        '  })();\n'
        '  </script>'
    )


def render_gear(mt, gear_data):
    mid = mt["id"]
    md = gear_data.get(mid)
    name = esc(mt["name"])
    if not md:
        variants_attr = ""
    else:
        groups = {}
        order = []
        for month in sorted(md.keys(), key=int):
            items = md[month]
            key = json.dumps(items, ensure_ascii=False)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(int(month))
        outer = {k: groups[k] for k in order}
        outer_json = json.dumps(outer, ensure_ascii=False)
        variants_attr = outer_json.replace('"', "&quot;")

    return (
        f'<div class="gear-section" id="sec-gear"><h2><svg width="16" height="16" '
        'viewBox="0 0 24 24" style="vertical-align:-3px;margin-right:4px" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M20 13V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v6"/>'
        '<path d="M4 13h16v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/>'
        f'<path d="M9 5V3h6v2"/></svg>{name}を登るための装備</h2>'
        f'<div class="gear-cards-scroll" data-gear-mid="{mid}" '
        f'data-gear-variants="{variants_attr}"></div>'
        f'{GEAR_NOTE}</div>'
    )


def render_faq(mt):
    faq = mt.get("faq") or []
    if not faq:
        return ""
    items = "".join(
        '<div class="faq-item">\n'
        f'    <h2 class="faq-q">{esc(item["question"])}</h2>\n'
        '    <div class="faq-a">\n'
        f'      <div><p>{esc(item["answer"])}</p></div>\n'
        '    </div>\n'
        '  </div>\n'
        for item in faq
    )
    return (
        '<div class="card">\n'
        '  <h2 style="font-size:15px;font-weight:700;color:#2a3820;'
        'margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #eaf1e0;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" style="vertical-align:-3px;'
        'margin-right:4px" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/>'
        '<path d="M9.5 9.2a2.5 2.5 0 1 1 3.7 2.2c-.8.5-1.2 1-1.2 2"/>'
        f'<line x1="12" y1="17" x2="12" y2="17.1"/></svg>よくある質問</h2>\n{items}</div>'
    )


def render_nearby(mt, by_id):
    nearby_ids = mt.get("nearby") or []
    cards = []
    for nid in nearby_ids:
        nm = by_id.get(nid)
        if not nm:
            continue
        color = "blue" if nm.get("category") == "百名山" else "green"
        diff = nm.get("difficulty") or ""
        bg, fg = DIFF_BADGE_COLOR.get(diff, ("#edf4e8", "#3a5a3a"))
        coeff = nm.get("courseCoefficientRange") or ""
        ofuna_min = nm.get("driveOfuna")
        shinjuku_min = nm.get("driveShinjuku")
        yokohama_min = nm.get("driveYokohama")
        omiya_min = nm.get("driveOmiya")
        ofuna_s = fmt_min(ofuna_min) if ofuna_min is not None else ""
        cards.append(
            f'<a href="/mountains/{nid}/" class="rc rc-{color}">'
            f'<div class="rn">{esc(nm.get("name",""))}</div>'
            f'<div class="rb"><span class="rbd" style="background:{bg};color:{fg}">{esc(diff)}</span>'
            f'<span class="rbc">定数{esc(coeff)}</span></div>'
            f'<div class="rt" id="nearby-time-{nid}" '
            f'data-ofuna="{fmt_min(ofuna_min) if ofuna_min is not None else ""}" '
            f'data-shinjuku="{fmt_min(shinjuku_min) if shinjuku_min is not None else ""}" '
            f'data-yokohama="{fmt_min(yokohama_min) if yokohama_min is not None else ""}" '
            f'data-omiya="{fmt_min(omiya_min) if omiya_min is not None else ""}">{ofuna_s}'
            f'<span class="rs" id="nearby-label-{nid}">大船から</span></div></a>'
        )
    if not cards:
        return ""
    cards_html = "\n".join(cards)
    return (
        '<div class="rw"><p class="rh"><svg width="14" height="14" viewBox="0 0 24 24" '
        'style="vertical-align:-2px;margin-right:3px" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3 20 L9 9 L13 15 L16 11 L21 20 Z"/></svg>近くて似た山</p>'
        f'<div class="rg">{cards_html}\n</div></div>'
    )


def render_warn_banner(mt):
    wb = mt.get("warnBanner")
    if not isinstance(wb, dict):
        return ""
    level = wb.get("type", "yellow")
    title = esc(wb.get("title", ""))
    text = esc(wb.get("text", ""))
    url = wb.get("url")
    link_text = esc(wb.get("linkText", ""))
    link_html = ""
    if url:
        link_html = f'\n      <a href="{esc(url)}" target="_blank" rel="noopener" class="warn-link">{link_text} →</a>'
    return (
        f'<div class="warn-banner warn-banner-{level}">\n'
        '    <div class="warn-icon">⚠️</div>\n'
        '    <div class="warn-body">\n'
        f'      <div class="warn-title warn-title-{level}">{title}</div>\n'
        f'      <div class="warn-text">{text}</div>{link_html}\n'
        '    </div>\n'
        '  </div>'
    )


def render_share(mt):
    mid = mt["id"]
    name = mt["name"]
    url = f"https://tozan-navi.com/mountains/{mid}/"
    line_text = f"{name}の登山情報"
    return (
        '<div class="share-section">\n'
        '    <button class="share-btn share-btn-native" onclick="shareNative()">'
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
        'style="vertical-align:middle"><polyline points="16 8 12 4 8 8"/>'
        '<line x1="12" y1="4" x2="12" y2="16"/>'
        '<path d="M8 12H5a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7a1 1 0 0 0-1-1h-3"/>'
        '</svg> シェア</button>\n'
        '  </div>\n'
        '  <div class="share-fallback" id="share-fallback" style="display:none;">\n'
        f'    <a href="https://line.me/R/msg/text/?{esc(line_text)}%0A{esc(url)}" target="_blank" '
        "class=\"share-btn share-btn-line\" onclick=\"gtag('event','share_click',"
        "{method:'line'})\"><svg width=\"13\" height=\"13\" viewBox=\"0 0 24 24\" "
        'style="vertical-align:-2px;margin-right:4px" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 4h16v12H8l-4 4z"/></svg>LINE</a>\n'
        f'    <a href="https://twitter.com/intent/tweet?text={esc(line_text)}&url={esc(url)}" '
        "target=\"_blank\" class=\"share-btn share-btn-x\" onclick=\"gtag('event',"
        "'share_click',{method:'x'})\">𝕏 X</a>\n"
        '    <button class="share-btn share-btn-copy" onclick="copyUrl()">'
        '<svg width="13" height="13" viewBox="0 0 24 24" style="vertical-align:-2px;'
        'margin-right:4px" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M9 15 L15 9"/>'
        '<path d="M10.5 6.5l1-1a4 4 0 0 1 5.6 5.6l-1.4 1.4"/>'
        '<path d="M13.5 17.5l-1 1a4 4 0 0 1-5.6-5.6l1.4-1.4"/>'
        '</svg>URLコピー</button>\n'
        '  </div>\n'
        f'{FEEDBACK_LINK_BLOCK.rstrip(chr(10))}'
    )


def render_scripts(mt):
    mid = mt["id"]
    name = mt["name"]
    hero_min_map = {}
    for _, field, key in DEP_ORDER:
        v = mt.get(field)
        if v is not None:
            hero_min_map[key] = str(v)
    init_obj = {
        "id": mid,
        "name": name,
        "heroMinMap": hero_min_map,
        "nearbyIds": mt.get("nearby") or [],
    }
    init_json = json.dumps(init_obj, ensure_ascii=False, indent=2)
    hero_photo = ""
    if mt.get("hasHeroPhotoScript"):
        hero_photo = load_hero_photo_script().replace("__MID__", mid) + "\n"
    return (
        "<script>\n"
        f"var YM_MOUNTAIN_INIT = {init_json};\n"
        "</script>\n"
        '<script src="../../assets/js/mountain-engine.js"></script>\n'
        "\n\n\n"
        f"{hero_photo}"
        f"{NEARBY_STICKY_SCRIPT}"
        "\n\n"
        '<script src="../../assets/js/gear-common.js"></script>\n'
        '<script src="../../assets/js/mountain.js"></script>'
    )


def generate_page(mt, by_id, gear_data):
    mid = mt["id"]
    updated = esc(mt.get("mountainUpdated") or "")

    body_sections = [
        HEADER_BLOCK.rstrip("\n"),
        "<main>",
        f'  {render_bookmark_tabs(mt)}',
        f'  <div class="mountain-updated">最終更新: {updated}</div>',
        f'  {render_hero(mt)}',
        "",
        "  <!-- ① こんな人におすすめ -->",
        f'  {mt.get("vibesHtml","")}',
    ]
    weather = render_weather(mt)
    weather_before_intro = bool(weather) and mt.get("weatherBeforeIntro")
    if weather_before_intro:
        body_sections.append("")
        body_sections.append(f"  {weather}")
    warn = render_warn_banner(mt)
    if warn:
        body_sections.append(f"  {warn}")
    body_sections.append(f'  {mt.get("introHtml","")}')
    body_sections.append("")
    body_sections.append(f'  {render_dl_card(mt)}')

    if weather and not weather_before_intro:
        body_sections.append("")
        body_sections.append(f"  <!-- 天気ウィジェット -->")
        body_sections.append(f"  {weather}")

    caution = mt.get("routeCautionHtml")
    if caution:
        body_sections.append("")
        body_sections.append("")
        body_sections.append(f"  {caution}")

    train = render_train_access(mt)
    if train:
        body_sections.append("")
        body_sections.append(f"  {train}")

    body_sections.append("")
    body_sections.append(f'  {render_car_access(mt)}')
    body_sections.append("")
    body_sections.append(f'  {render_parking(mt)}')
    body_sections.append(f'  {render_season(mt)}')
    body_sections.append("")
    body_sections.append(f'  {render_routes(mt)}')
    body_sections.append("")
    yamap = render_yamap(mt)
    if yamap:
        body_sections.append(f"  {yamap}")
        body_sections.append("")
    body_sections.append(f'  {render_climbed(mt)}')
    body_sections.append(f'{render_gear(mt, gear_data)}{mt.get("relatedLinksHtml","")}')
    body_sections.append("")
    faq = render_faq(mt)
    if faq:
        body_sections.append(faq)
        body_sections.append("")
    nearby = render_nearby(mt, by_id)
    if nearby:
        body_sections.append(nearby)
    body_sections.append("")
    body_sections.append(NOTE_BLOCK.rstrip("\n"))
    body_sections.append("")
    body_sections.append(f'  {render_share(mt)}')
    body_sections.append("</main>")
    body_sections.append(FOOTER_BLOCK.rstrip("\n"))
    body_sections.append(render_scripts(mt))
    body_sections.append("</body>")
    body_sections.append("</html>")

    html = render_head(mt) + "\n<body>\n" + "\n".join(body_sections) + "\n"
    return html


def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    with open(GEAR_DATA_PATH, encoding="utf-8") as f:
        gear_data = json.load(f)
    return data, gear_data


def generate_one(mid, by_id, gear_data, dry_run=False):
    if mid in EXCLUDED_IDS:
        raise GenError(f"{mid}: 特殊構造ページのため自動生成の対象外です（EXCLUDED_IDS）")
    mt = by_id.get(mid)
    if mt is None:
        raise GenError(f"{mid}: mountains.json に存在しません")
    html = generate_page(mt, by_id, gear_data)

    out_path = os.path.join(SITE_ROOT, "mountains", mid, "index.html")
    if dry_run:
        return html

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp_path = out_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(html)

    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing = f.read()
        if existing == html:
            os.remove(tmp_path)
            return None  # unchanged

    os.replace(tmp_path, out_path)
    return html


def main():
    parser = argparse.ArgumentParser(description="mountains.json から山ページを自動生成")
    parser.add_argument("--id", help="生成する山のID（1件のみ）")
    parser.add_argument("--all", action="store_true", help="全156山を生成")
    parser.add_argument("--dry-run", action="store_true", help="ファイルに書き込まず結果のみ確認")
    args = parser.parse_args()

    if not args.id and not args.all:
        parser.error("--id または --all を指定してください")

    data, gear_data = load_data()
    by_id = {m["id"]: m for m in data}

    if args.id:
        targets = [args.id]
    else:
        targets = [m["id"] for m in data if m["id"] not in EXCLUDED_IDS]
        skipped = [m["id"] for m in data if m["id"] in EXCLUDED_IDS]
        if skipped:
            print(f"スキップ（特殊構造ページ、既存HTMLを保持）: {skipped}")

    changed = 0
    unchanged = 0
    errors = []
    for mid in targets:
        try:
            result = generate_one(mid, by_id, gear_data, dry_run=args.dry_run)
            if args.dry_run:
                print(f"[dry-run] {mid}: {len(result)} chars")
            elif result is None:
                unchanged += 1
            else:
                changed += 1
                print(f"generated: {mid}")
        except GenError as e:
            errors.append(str(e))
            print(f"ERROR: {e}", file=sys.stderr)

    print(f"\n完了: 変更 {changed} / 変更なし {unchanged} / エラー {len(errors)}")

    # 山ページ生成と連動して、診断用の月別軽量装備JSON（recommend-gear/*.json）も
    # gear-data.json から再生成する（dry-runやエラー時は実行しない）。
    if not args.dry_run and not errors:
        written = gen_recommend_gear.generate()
        print(f"診断用装備JSONを更新: {len(written)} ファイル")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
