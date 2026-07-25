#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ギアデータベース ページ生成スクリプト v2
data/gear-*.json から /gear/ 以下の全ページを生成する。

出力:
  out/gear/index.html                          ハブページ
  out/gear/brands/index.html                   ブランド一覧
  out/gear/brands/{brandId}/index.html         ブランド詳細(おすすめの山を含む)
  out/gear/category/{categoryId}/index.html    カテゴリページ
  out/gear/collections/{collectionId}/index.html  コレクション(SEOロングテール)ページ
  out/data/mountain-gear-links.json            山→ギアの逆引き(山ページ側の将来統合用)

新しいブランド・商品・カテゴリ・コレクションを追加する場合は、対応するJSONに
エントリを追加してこのスクリプトを再実行するだけでよい(HTMLは手書きしない)。
"""
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BASE, "data")
OUT = BASE


def load(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


BRANDS = load("gear-brands.json")
ITEMS = load("gear-items.json")
CATEGORIES = load("gear-categories.json")
COLLECTIONS = load("gear-collections.json")
MOUNTAINS = load("mountains-lookup.json")

BRAND_BY_ID = {b["id"]: b for b in BRANDS}

# ---- オリジナルSVGアイコン(実物の写真・ロゴは使わず自作の線画で代替) ----
CATEGORY_ICON_PATHS = {
    "backpack": """<path d="M8.5 8.2C8.5 5 10 2.6 12 2.6s3.5 2.4 3.5 5.6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><rect x="5.5" y="8.2" width="13" height="13.2" rx="4" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="8.7" y="13" width="6.6" height="5.2" rx="1.4" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M9 8.2v2.4M15 8.2v2.4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>""",
    "rainwear": """<path d="M9 3.5l3 2 3-2 3 3-2 2v13.5H8V8.5l-2-2z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M12 5.5v3.3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M9.5 12h5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>""",
    "apparel": """<path d="M9 3L4.5 7l2 4l2.5-2.5V11h6V8.5l2.5 2.5l2-4L15 3c0 1.3-1.3 2.2-3 2.2S9 4.3 9 3z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M8.7 13.3h6.6v8.7h-2.6v-6h-1.4v6H8.7z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>""",
    "shoes": """<path d="M4 19.6v-2.8c0-1.7 1-3.2 2.6-3.8L7 4.3A1.3 1.3 0 0 1 8.3 3h1.9A1.3 1.3 0 0 1 11.5 4.3v11.4c1.1.3 2 1 2.6 2 .6.2 1.1.7 1.1 1.4v.5c0 1.1-.9 2-2 2H5.2c-.7 0-1.2-.5-1.2-1z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M8.2 7h2.3M8.2 9.8h2.3M8.2 12.6h2.3" stroke="currentColor" stroke-width="1" stroke-linecap="round"/><path d="M4 19.6h13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>""",
    "accessory": """<path d="M8 10.5V9a4 4 0 0 1 8 0v1.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M6.5 10.5h11l-1 10a2 2 0 0 1-2 1.8h-5a2 2 0 0 1-2-1.8z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>""",
    "cap": """<path d="M4.5 14.5c0-4.4 3.4-8 7.5-8s7.5 3.6 7.5 8" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M4.5 14.5h11.5c2.8 0 5 .7 6.5 1.6-1.5 1-3.8 1.6-6.6 1.6H8c-2 0-3.5-1.4-3.5-3.2z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M12 6.5v2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>""",
    "pole": """<path d="M8 4.5l9 15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M6 6.2l3.6-2.2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><ellipse cx="14.3" cy="15.2" rx="2.6" ry="1" fill="none" stroke="currentColor" stroke-width="1.3" transform="rotate(28 14.3 15.2)"/><path d="M16.2 18.3l1 1.7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>""",
}


def render_category_icon(category_id, size=22):
    path = CATEGORY_ICON_PATHS.get(category_id, CATEGORY_ICON_PATHS["accessory"])
    return '<svg width="' + str(size) + '" height="' + str(size) + '" viewBox="0 0 24 24">' + path + '</svg>'


def render_logo_badge(brand, size=40):
    color = brand.get("accentColor", "#4e6535")
    mono = brand.get("monogram", brand["name"][0])
    font_size = int(size * (0.40 if len(mono) <= 2 else 0.30))
    return (
        '<span class="brand-badge" style="width:' + str(size) + 'px;height:' + str(size) + 'px;background:' + color + '">'
        '<span style="font-size:' + str(font_size) + 'px;font-weight:800;color:#fff;letter-spacing:.03em;font-family:\'Zen Kaku Gothic New\',sans-serif">' + esc(mono) + '</span>'
        '</span>'
    )


def render_item_visual(item):
    brand = BRAND_BY_ID.get(item["brandId"], {})
    color = brand.get("accentColor", "#4e6535")
    images = item.get("images") or []
    if images:
        return (
            '<div class="item-visual item-visual-photo">'
            '<img src="' + esc(images[0]) + '" alt="' + esc(item["name"]) + '" loading="lazy">'
            '</div>'
        )
    icon = render_category_icon(item.get("categoryId", "accessory"), size=34)
    return (
        '<div class="item-visual" style="background:linear-gradient(160deg,' + color + '22,' + color + '0d)">'
        '<span class="item-visual-icon" style="color:' + color + '">' + icon + '</span>'
        '</div>'
    )


IG_ICON_SVG = """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.2" cy="6.8" r="1" fill="currentColor" stroke="none"/></svg>"""


def render_instagram_embed(brand):
    url = brand.get("instagramUrl")
    if not url:
        return ""
    color = brand.get("accentColor", "#4e6535")
    return (
        '<div class="secline"><span class="pg-eyebrow">SNS — 公式Instagram</span></div>'
        '<a href="' + esc(url) + '" target="_blank" rel="nofollow noopener" class="ig-link-card">'
        '<span class="ig-link-icon" style="background:' + color + '">' + IG_ICON_SVG + '</span>'
        '<span class="ig-link-text">'
        '<span class="ig-link-title">' + esc(brand["name"]) + '</span>'
        '<span class="ig-link-sub">最新の投稿をInstagramで見る</span>'
        '</span>'
        '<span class="ig-link-arrow">→</span>'
        '</a>'
    )


AMAZON_TAG = "amazonafdaiki-22"


def render_purchase_links(item):
    links = []
    japan_url = item.get("japanUrl")
    if japan_url:
        links.append('<a href="' + esc(japan_url) + '" target="_blank" rel="nofollow noopener">日本正規代理店で見る</a>')
    asin = item.get("amazonAsin")
    if asin:
        url = "https://www.amazon.co.jp/dp/" + asin + "?tag=" + AMAZON_TAG
        links.append('<a href="' + url + '" target="_blank" rel="nofollow noopener sponsored">Amazonで見る</a>')
    rakuten_url = item.get("rakutenUrl")
    if rakuten_url:
        links.append('<a href="' + esc(rakuten_url) + '" target="_blank" rel="nofollow noopener sponsored">楽天市場で見る</a>')
    if not links:
        return ""
    note = ""
    if asin or rakuten_url:
        note = '<div class="item-purchase-note">※価格・在庫は変動します。最新情報は各リンク先でご確認ください。当サイトはAmazonアソシエイト・楽天アフィリエイトを利用しています。</div>'
    else:
        note = '<div class="item-purchase-note">※価格・在庫は変動します。最新情報は各リンク先でご確認ください。</div>'
    return '<div class="item-purchase-links">' + "　/　".join(links) + '</div>' + note

STYLE = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --sugi:#4e6535; --miyama:#243d20; --washi:#f0ede5; --wakaba:#c8d4b8;
  --sumi:#1a1a16; --ink:#3a3530; --hai:#93897c; --line:#e6e1d7;
  --shadow-sm:0 1px 1px rgba(26,22,14,.03), 0 2px 5px rgba(26,22,14,.05);
  --shadow:0 1px 2px rgba(26,22,14,.04), 0 10px 28px -8px rgba(26,22,14,.14);
}
body{font-family:"Hiragino Sans","Noto Sans JP",-apple-system,BlinkMacSystemFont,sans-serif;background:var(--washi);color:var(--ink);font-size:15px;line-height:1.7;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
h1,h2{font-family:"Zen Kaku Gothic New",sans-serif}
header{background:var(--miyama);padding:12px 16px}
.header-inner{max-width:480px;margin:0 auto;display:flex;align-items:center;gap:8px}
.header-title{color:white;font-family:"Zen Kaku Gothic New",sans-serif;font-size:15px;font-weight:900;margin-left:auto}
.back-btn{color:white;font-size:12px;white-space:nowrap;border:1px solid rgba(255,255,255,0.5);border-radius:5px;padding:4px 10px}
main{max-width:480px;margin:0 auto;padding:18px 20px 24px}

.pgtitle{padding:8px 0 6px}
.gear-hero-img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:20px;margin-top:10px;box-shadow:var(--shadow);display:block}
.pg-eyebrow{font-size:10.5px;font-weight:700;letter-spacing:.16em;color:var(--sugi)}
.pgtitle h1{font-weight:900;font-size:24px;color:var(--sumi);margin-top:8px;letter-spacing:-.01em;line-height:1.3}
.pgtitle p{font-size:12.5px;color:var(--hai);margin-top:8px;line-height:1.7}

.intro-note{background:#fff;border-radius:16px;padding:16px 18px;margin:16px 0 22px;box-shadow:var(--shadow-sm);font-size:12.5px;color:var(--ink);line-height:1.75}
.intro-note b{color:var(--sugi)}

.tile-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:8px}
.tile{background:#fff;border-radius:16px;padding:16px 14px;box-shadow:var(--shadow-sm)}
.gear-type-strip{display:flex;justify-content:space-between;gap:6px;margin:18px 0 4px;padding:16px 10px;background:#fff;border-radius:16px;box-shadow:var(--shadow-sm)}
.gear-strip-item{display:flex;flex-direction:column;align-items:center;gap:6px;flex:1}
.gear-strip-icon{width:40px;height:40px;border-radius:50%;background:var(--washi);display:flex;align-items:center;justify-content:center;color:var(--sugi)}
.gear-strip-label{font-size:9.5px;color:var(--hai);font-weight:700;white-space:nowrap}

.tile-icon-badge{display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:12px;background:var(--wakaba);margin-bottom:10px}
.tile-icon-svg{display:flex;color:var(--sugi)}
.tile-icon-svg svg{display:block}
.tile-name{font-size:13.5px;font-weight:800;color:var(--sumi)}
.tile-desc{font-size:10.5px;color:var(--hai);margin-top:4px;line-height:1.5}
.tile-soon{font-size:9.5px;color:#fff;background:var(--hai);border-radius:999px;padding:2px 8px;display:inline-block;margin-top:8px;font-weight:700}

.brand-badge{position:relative;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;flex-shrink:0;box-shadow:0 2px 6px -2px rgba(0,0,0,.3);border:2px solid rgba(255,255,255,.5)}

.item-visual{width:100%;aspect-ratio:16/9;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:12px}
.item-visual-icon{display:flex}
.item-visual-icon svg{display:block}

.brand-card{display:block;background:#fff;border-radius:20px;padding:20px;margin-bottom:16px;box-shadow:var(--shadow)}
.brand-card-head{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.brand-flag{font-size:20px;line-height:1}
.brand-name{font-size:19px;font-weight:900;color:var(--sumi);font-family:"Zen Kaku Gothic New",sans-serif;letter-spacing:-.01em}
.brand-kana{font-size:11px;color:var(--hai);margin-top:1px}
.brand-desc{font-size:12.5px;color:var(--ink);line-height:1.75;margin-bottom:12px}
.brand-tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:2px}
.brand-tag{font-size:10.5px;color:var(--sugi);background:var(--wakaba);border-radius:999px;padding:4px 10px;font-weight:700}
.brand-chevron-row{display:flex;justify-content:flex-end;align-items:center;gap:4px;margin-top:8px;font-size:11.5px;color:var(--sugi);font-weight:700}

.brand-hero{background:#fff;border-radius:20px;padding:22px 20px;margin-bottom:18px;box-shadow:var(--shadow)}
.brand-hero-top{display:flex;align-items:center;gap:10px;margin-bottom:4px}
.brand-meta-line{font-size:12px;color:var(--hai);margin-top:8px}

.secline{display:flex;align-items:center;gap:12px;margin:28px 0 10px}
.secline::after{content:"";flex:1;height:1px;background:var(--line)}
.sec-desc{font-size:11.5px;color:var(--hai);line-height:1.7;margin:4px 0 12px}
.desc-block{font-size:13px;color:var(--ink);line-height:1.85}

.feature-list{list-style:none;margin-top:4px}
.feature-list li{position:relative;padding-left:18px;font-size:13px;color:var(--ink);line-height:1.75;margin-bottom:8px}
.feature-list li::before{content:"";position:absolute;left:0;top:9px;width:6px;height:6px;border-radius:50%;background:var(--sugi)}

.info-table{background:#fff;border-radius:16px;padding:16px 18px;box-shadow:var(--shadow-sm);margin-top:6px}
.info-row{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:12.5px}
.info-row:last-child{border-bottom:none}
.info-row span:first-child{color:var(--hai);flex-shrink:0}
.info-row span:last-child{color:var(--ink);text-align:right;font-weight:600}

.item-card{background:#fff;border-radius:18px;padding:18px;margin-bottom:14px;box-shadow:var(--shadow)}
.item-brand-link{font-size:11px;color:var(--sugi);font-weight:700;margin-bottom:4px;display:inline-block}
.item-name{font-size:15.5px;font-weight:800;color:var(--sumi);margin-bottom:4px}
.item-cat{display:inline-block;font-size:10px;color:var(--sugi);background:var(--wakaba);border-radius:999px;padding:2px 9px;font-weight:700;margin-bottom:8px}
.item-specs{display:flex;flex-wrap:wrap;gap:8px;font-size:11.5px;color:var(--hai);margin-bottom:8px}
.item-specs b{color:var(--ink)}
.item-desc{font-size:12.5px;color:var(--ink);line-height:1.75;margin-bottom:8px}
.item-feature-list{list-style:none;margin-bottom:10px}
.item-feature-list li{position:relative;padding-left:16px;font-size:12px;color:var(--ink);line-height:1.7;margin-bottom:5px}
.item-feature-list li::before{content:"";position:absolute;left:0;top:8px;width:5px;height:5px;border-radius:50%;background:var(--sugi)}
.item-avail{font-size:11.5px;color:var(--hai);margin-bottom:10px}
.item-link{display:inline-block;font-size:12.5px;font-weight:700;color:var(--sugi);text-decoration:underline;text-decoration-color:var(--wakaba);text-underline-offset:3px}

.mtn-card{display:flex;justify-content:space-between;align-items:center;background:#fff;border-radius:14px;padding:14px 16px;margin-bottom:10px;box-shadow:var(--shadow-sm)}
.mtn-name{font-size:14px;font-weight:800;color:var(--sumi)}
.mtn-meta{font-size:11px;color:var(--hai);margin-top:2px}
.mtn-chevron{color:var(--sugi);font-size:14px;font-weight:700}

.empty-note{background:#fff;border-radius:16px;padding:20px 18px;text-align:center;font-size:12.5px;color:var(--hai);box-shadow:var(--shadow-sm)}

.item-visual-photo{background:#f0ede5;overflow:hidden}
.item-visual-photo img{width:100%;height:100%;object-fit:contain}
.item-purchase-links{font-size:12.5px;font-weight:700;color:var(--sugi);margin-top:8px}
.item-purchase-links a{text-decoration:underline;text-decoration-color:var(--wakaba);text-underline-offset:2px}
.item-purchase-note{font-size:10px;color:var(--hai);margin-top:6px;line-height:1.6}

.ig-link-card{display:flex;align-items:center;gap:12px;background:#fff;border-radius:16px;padding:14px 16px;box-shadow:var(--shadow-sm)}
.ig-link-icon{flex-shrink:0;width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;color:#fff}
.ig-link-text{flex:1;display:flex;flex-direction:column;gap:2px;min-width:0}
.ig-link-title{font-size:13.5px;font-weight:800;color:var(--sumi)}
.ig-link-sub{font-size:11.5px;color:var(--hai)}
.ig-link-arrow{flex-shrink:0;color:var(--sugi);font-weight:700;font-size:16px}

.official-cta{background:var(--sugi);border-radius:20px;padding:26px 22px;text-align:center;margin-top:26px;box-shadow:var(--shadow)}
.official-cta p{color:rgba(255,255,255,.75);font-size:12px;margin-bottom:16px;line-height:1.7}
.official-cta a{display:inline-block;background:#fff;color:var(--sugi);font-weight:700;font-size:13px;padding:11px 26px;border-radius:999px}

.cta{background:var(--sugi);border-radius:20px;padding:28px 24px;text-align:center;margin-top:28px;box-shadow:var(--shadow)}
.cta h2{color:#fff;font-size:17px;font-weight:900;margin-bottom:10px;letter-spacing:-.01em}
.cta p{color:rgba(255,255,255,.7);font-size:12.5px;margin-bottom:18px;line-height:1.7}
.cta a{display:inline-block;background:#fff;color:var(--sugi);font-weight:700;font-size:13px;padding:11px 28px;border-radius:999px}

.other-links{font-size:12.5px;margin-top:26px;color:var(--hai)}
.other-links a{color:var(--sugi);font-weight:700;text-decoration:underline;text-decoration-color:var(--wakaba)}

.bottom-nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:768px;background:white;border-top:1px solid #e8e4dc;display:flex;z-index:100;box-shadow:0 -2px 12px rgba(0,0,0,0.08);padding-bottom:env(safe-area-inset-bottom,0px)}
.bottom-nav a{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:8px 4px 10px;text-decoration:none;color:#a09888;gap:3px;font-size:16px}
.bottom-nav a span:last-child{font-size:10px;font-weight:500}
"""

BOTTOM_NAV = """<nav class="bottom-nav">
  <a href="/"><span><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></span><span>ホーム</span></a>
  <a href="/recommend/"><span><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="12,3 14,10 12,12 10,10" fill="currentColor" stroke="none"/><polygon points="12,21 10,14 12,12 14,14" fill="currentColor" opacity="0.5" stroke="none"/><circle cx="12" cy="12" r="1.5" fill="white" stroke="none"/></svg></span><span>診断</span></a>
  <a href="/articles/"><span><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></span><span>記事</span></a>
  <a href="/mypage/"><span><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span><span>マイページ</span></a>
</nav>
<div style="height:64px"></div>"""


def esc(s):
    return "" if s is None else str(s)


def breadcrumb_jsonld(items):
    # items: list of (name, url_or_None). Last item usually has url_or_None=None (current page).
    entries = []
    for i, (name, path) in enumerate(items, start=1):
        entry = {"@type": "ListItem", "position": i, "name": name}
        if path:
            entry["item"] = "https://tozan-navi.com" + path
        entries.append(entry)
    data = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": entries}
    return json.dumps(data, ensure_ascii=False)


def page_shell(title, description, canonical_path, back_href, header_label, body_html,
                breadcrumbs=None, extra_jsonld=None, noindex=False, og_image=None):
    url = "https://tozan-navi.com" + canonical_path
    og_image_url = og_image or "https://tozan-navi.com/ogp.png"
    robots_tag = '<meta name="robots" content="noindex,follow">\n' if noindex else ""
    jsonld_blocks = ""
    if breadcrumbs:
        jsonld_blocks += '<script type="application/ld+json">' + breadcrumb_jsonld(breadcrumbs) + '</script>\n'
    if extra_jsonld:
        jsonld_blocks += '<script type="application/ld+json">' + json.dumps(extra_jsonld, ensure_ascii=False) + '</script>\n'
    return """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>""" + esc(title) + """</title>
<meta name="description" content=\"""" + esc(description) + """\">
""" + robots_tag + """<meta property="og:title" content=\"""" + esc(title) + """\">
<meta property="og:description" content=\"""" + esc(description) + """\">
<meta property="og:image" content=\"""" + og_image_url + """\">
<meta property="og:url" content=\"""" + url + """\">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href=\"""" + url + """\">
<link rel="icon" href="/favicon.ico">
<link rel="manifest" href="/manifest.json">
<link href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@700;900&display=swap" rel="stylesheet">
<style>""" + STYLE + """</style>
""" + jsonld_blocks + """</head>
<body>
<header>
  <div class="header-inner">
    <a href=\"""" + back_href + """\" class="back-btn">← 戻る</a>
    <div class="header-title">""" + esc(header_label) + """</div>
  </div>
</header>
<main>
""" + body_html + """
</main>
""" + BOTTOM_NAV + """
</body>
</html>
"""


def fmt_spec(label, value, unit=""):
    if value is None:
        return ""
    return '<span><b>' + label + '</b> ' + str(value) + unit + '</span>'


def render_item_card(item, show_brand_link=True):
    brand = BRAND_BY_ID.get(item["brandId"], {})
    specs = []
    if item.get("capacityRange"):
        specs.append(fmt_spec("容量", item["capacityRange"]))
    elif item.get("capacityL"):
        specs.append(fmt_spec("容量", item["capacityL"], "L"))
    if item.get("weightG"):
        specs.append(fmt_spec("重量", item["weightG"], "g"))
    if item.get("priceRange"):
        specs.append(fmt_spec("価格帯", item["priceRange"]))
    specs_html = "".join([s for s in specs if s])

    purposes = "・".join(item.get("purposes") or [])
    materials = "、".join(item.get("materials") or [])

    features_html = ""
    if item.get("features"):
        lis = "".join(['<li>' + esc(f) + '</li>' for f in item["features"]])
        features_html = '<ul class="item-feature-list">' + lis + '</ul>'

    desc_parts = []
    if materials:
        desc_parts.append("素材：" + materials)
    if item.get("waterproof"):
        desc_parts.append("防水性：" + item["waterproof"])
    if purposes:
        desc_parts.append("おすすめ用途：" + purposes)
    desc_html = ""
    if desc_parts:
        desc_html = '<div class="item-desc">' + "<br>".join(desc_parts) + '</div>'

    avail_html = ""
    if item.get("japanAvailability"):
        avail_html = '<div class="item-avail">日本での購入：' + esc(item["japanAvailability"]) + '</div>'

    link_html = ""
    if item.get("officialUrl"):
        link_html = '<a class="item-link" href="' + esc(item["officialUrl"]) + '" target="_blank" rel="nofollow noopener">ブランド公式サイトで見る →</a>'

    purchase_html = render_purchase_links(item)

    brand_link_html = ""
    if show_brand_link and brand:
        brand_link_html = '<a class="item-brand-link" href="/gear/brands/' + brand["id"] + '/">' + esc(brand["name"]) + '</a><br>'

    return (
        '<div class="item-card">'
        + render_item_visual(item)
        + brand_link_html
        + '<div class="item-name">' + esc(item["name"]) + '</div>'
        '<span class="item-cat">' + esc(item.get("category", "")) + '</span>'
        '<div class="item-specs">' + specs_html + '</div>'
        + desc_html
        + features_html
        + avail_html
        + link_html
        + purchase_html
        + '</div>'
    )


def render_brand_card(b):
    tags_html = "".join(['<span class="brand-tag">' + esc(t) + '</span>' for t in b.get("tags", [])])
    return (
        '<a href="/gear/brands/' + b["id"] + '/" class="brand-card">'
        '<div class="brand-card-head">' + render_logo_badge(b, size=44) + ''
        '<div><div class="brand-name">' + esc(b["name"]) + '</div>'
        '<div class="brand-kana">' + esc(b.get("countryFlag")) + ' ' + esc(b.get("nameKana", "")) + '・' + esc(b.get("country", "")) + '・' + esc(b.get("founded", "")) + '年創業</div></div></div>'
        '<div class="brand-desc">' + esc(b.get("description", ""))[:80] + '…</div>'
        '<div class="brand-tags">' + tags_html + '</div>'
        '<div class="brand-chevron-row">ブランドを見る ›</div>'
        '</a>'
    )


def render_mountain_card(mid):
    m = MOUNTAINS.get(mid)
    if not m:
        return ""
    meta = "・".join([x for x in [m.get("area"), (str(m.get("elevation")) + "m" if m.get("elevation") else None), m.get("category")] if x])
    return (
        '<a href="/mountains/' + mid + '/" class="mtn-card">'
        '<div><div class="mtn-name">' + esc(m["name"]) + '</div>'
        '<div class="mtn-meta">' + esc(meta) + '</div></div>'
        '<div class="mtn-chevron">›</div>'
        '</a>'
    )


# ---------- 1. ハブページ /gear/ ----------

def render_tile_icon_badge(category_id):
    icon = render_category_icon(category_id, size=26)
    return '<span class="tile-icon-badge"><span class="tile-icon-svg">' + icon + '</span></span>'


GEAR_TYPE_STRIP = [
    ("apparel", "ウェア"),
    ("shoes", "シューズ"),
    ("backpack", "バックパック"),
    ("cap", "キャップ"),
    ("pole", "ポール"),
]


def render_gear_type_strip():
    items = ""
    for cid, label in GEAR_TYPE_STRIP:
        icon = render_category_icon(cid, size=24)
        items += (
            '<div class="gear-strip-item">'
            '<span class="gear-strip-icon">' + icon + '</span>'
            '<span class="gear-strip-label">' + label + '</span>'
            '</div>'
        )
    return '<div class="gear-type-strip">' + items + '</div>'


def gen_hub():
    tiles = ""
    for c in CATEGORIES[:3]:  # バックパック/レインウェア/シューズ を主要タイルに
        if c["status"] == "coming_soon":
            tiles += (
                '<div class="tile">' + render_tile_icon_badge(c["id"]) +
                '<div class="tile-name">' + esc(c["name"]) + '</div>'
                '<div class="tile-desc">' + esc(c["description"]) + '</div>'
                '<span class="tile-soon">近日公開</span></div>'
            )
        else:
            tiles += (
                '<a href="/gear/category/' + c["id"] + '/" class="tile">' + render_tile_icon_badge(c["id"]) +
                '<div class="tile-name">' + esc(c["name"]) + '</div>'
                '<div class="tile-desc">' + esc(c["description"]) + '</div>'
                '</a>'
            )

    collection_links = "".join([
        '<a href="/gear/collections/' + col["id"] + '/" class="tile">'
        '<div class="tile-name">' + esc(col["title"]) + '</div>'
        '<div class="tile-desc">' + esc(col["description"])[:34] + '…</div>'
        '</a>'
        for col in COLLECTIONS
    ])

    body = """
<div class="pgtitle">
  <span class="pg-eyebrow">GEAR — 登山用品データベース</span>
  <h1>登山ギアを探す</h1>
  <p>日本ではまだ情報が少ない、海外の注目登山ブランドとその商品をまとめました。カテゴリ・条件から探せます。</p>
</div>

<img src="/images/gear/gear-hero.jpg" alt="山を背景に並べられた登山用バックパック・レインウェア・調理器具などの登山装備一式" class="gear-hero-img" loading="eager">

""" + render_gear_type_strip() + """

<div class="intro-note">
  <b>このページについて：</b>「日本で一番、登山用品を探しやすいデータベース」を目指して育てているコーナーです。まずは海外ブランド5つ・代表商品から。少しずつ拡充していきます。
</div>

<div class="secline"><span class="pg-eyebrow">CATEGORY — カテゴリから探す</span></div>
<div class="tile-grid">""" + tiles + """</div>

<div class="secline"><span class="pg-eyebrow">COLLECTIONS — こんな条件で探す</span></div>
<div class="tile-grid">""" + collection_links + """</div>

<div class="secline"><span class="pg-eyebrow">BRANDS</span></div>
<p class="sec-desc">ブランドから探したい方はこちら。</p>
<a href="/gear/brands/" class="brand-card" style="text-align:center">
  <div class="brand-chevron-row" style="justify-content:center;font-size:14px">ブランド一覧を見る ›</div>
</a>

<div class="cta">
  <h2>山を探してみよう</h2>
  <p>ギアが決まったら、次はどこへ登るか。出発地・コース定数から山を検索できます</p>
  <a href="/">山を検索する →</a>
</div>
"""
    html = page_shell(
        "登山ギアを探す｜海外注目ブランドの登山用品データベース - Yamatch",
        "CAYL、Pa'lante、Hyperlite Mountain Gearなど海外の登山用品ブランドをカテゴリ・条件から探せます。",
        "/gear/", "/", "GEAR", body,
        breadcrumbs=[("ホーム", "/"), ("ギア", None)],
        og_image="https://tozan-navi.com/images/gear/gear-hero.jpg"
    )
    write("gear/index.html", html)


# ---------- 2. ブランド一覧 /gear/brands/ ----------

def gen_brand_list():
    cards = "".join([render_brand_card(b) for b in BRANDS])
    body = """
<div class="pgtitle">
  <span class="pg-eyebrow">GEAR / BRANDS</span>
  <h1>登山ギアブランド一覧</h1>
  <p>韓国・欧州・アメリカのULシーンを牽引する5ブランドを紹介しています。</p>
</div>
""" + cards
    html = page_shell(
        "登山ギアブランド一覧｜海外の注目ULブランドまとめ - Yamatch",
        "CAYL、Pa'lante、Hyperlite Mountain Gear、Klättermusen、NORRØNAなど海外の登山用品ブランドをまとめて紹介。",
        "/gear/brands/", "/gear/", "BRANDS", body,
        breadcrumbs=[("ホーム", "/"), ("ギア", "/gear/"), ("ブランド一覧", None)]
    )
    write("gear/brands/index.html", html)


# ---------- 3. ブランド詳細 /gear/brands/{id}/ ----------

def gen_brand_pages():
    for brand in BRANDS:
        brand_items = [i for i in ITEMS if i["brandId"] == brand["id"]]
        items_html = "".join([render_item_card(i, show_brand_link=False) for i in brand_items])

        tags_html = "".join(['<span class="brand-tag">' + esc(t) + '</span>' for t in brand.get("tags", [])])
        features_html = "".join(['<li>' + esc(f) + '</li>' for f in brand.get("features", [])])
        recommended = "・".join(brand.get("recommendedFor") or [])
        categories_str = "・".join(brand.get("categories") or [])

        other_brands = [b for b in BRANDS if b["id"] != brand["id"]]
        other_links = "、".join(['<a href="/gear/brands/' + b["id"] + '/">' + esc(b["name"]) + '</a>' for b in other_brands])

        mountain_cards = "".join([render_mountain_card(mid) for mid in brand.get("relatedMountainIds", [])])
        mountains_section = ""
        if mountain_cards:
            mountains_section = (
                '<div class="secline"><span class="pg-eyebrow">MOUNTAINS — このブランドが似合う山</span></div>'
                '<p class="sec-desc">' + esc(brand["name"]) + 'のテイストと相性がよい山をピックアップしました。</p>'
                + mountain_cards
            )

        founder = brand.get("founder")
        founder_str = ("・" + founder) if founder else ""

        hero_img_html = ""
        if brand.get("heroImage"):
            hero_img_html = '<img src="' + esc(brand["heroImage"]) + '" alt="' + esc(brand["name"]) + 'のギアを山の稜線に置いたイメージカット" class="gear-hero-img" loading="eager" style="margin-bottom:18px">'

        body = """
""" + hero_img_html + """
<div class="brand-hero">
  <div class="brand-hero-top">""" + render_logo_badge(brand, size=52) + """
    <div>
      <div class="brand-name">""" + esc(brand["name"]) + """</div>
      <div class="brand-kana">""" + esc(brand.get("countryFlag")) + """ """ + esc(brand.get("nameKana", "")) + """</div>
    </div>
  </div>
  <div class="brand-meta-line">""" + esc(brand.get("country")) + """・""" + esc(brand.get("founded")) + """年創業""" + founder_str + """・""" + esc(categories_str) + """</div>
  <div class="brand-tags">""" + tags_html + """</div>
</div>

<div class="secline"><span class="pg-eyebrow">ABOUT — ブランドについて</span></div>
<div class="desc-block">""" + esc(brand.get("description", "")) + """</div>

<div class="secline"><span class="pg-eyebrow">FEATURES — 特徴</span></div>
<ul class="feature-list">""" + features_html + """</ul>

<div class="secline"><span class="pg-eyebrow">INFO</span></div>
<div class="info-table">
  <div class="info-row"><span>創業国</span><span>""" + esc(brand.get("country")) + """</span></div>
  <div class="info-row"><span>創業年</span><span>""" + esc(brand.get("founded")) + """年</span></div>
  <div class="info-row"><span>主なカテゴリ</span><span>""" + esc(categories_str) + """</span></div>
  <div class="info-row"><span>おすすめ用途</span><span>""" + esc(recommended) + """</span></div>
  <div class="info-row"><span>日本での購入</span><span>""" + esc(brand.get("japanAvailability")) + """</span></div>
</div>

<div class="secline"><span class="pg-eyebrow">PRODUCTS — 代表商品</span></div>
""" + items_html + mountains_section + render_instagram_embed(brand) + """

<div class="official-cta">
  <p>価格・在庫・最新モデルは公式サイトでご確認ください</p>
  <a href=\"""" + esc(brand.get("officialUrl")) + """\" target="_blank" rel="nofollow noopener">""" + esc(brand["name"]) + """ 公式サイトへ →</a>
""" + ('<p style="margin-top:14px">日本からは<a href="' + esc(brand.get("japanUrl", "")) + '" target="_blank" rel="nofollow noopener" style="color:#fff;text-decoration:underline">日本正規代理店サイト</a>からも購入できます</p>' if brand.get("japanUrl") else "") + """
</div>

<div class="other-links">他のブランドも見る：""" + other_links + """</div>
"""
        title = brand["name"] + "（" + brand.get("nameKana", "") + "）とは｜ブランド紹介・代表商品 - Yamatch"
        description = brand["name"] + "の特徴、創業国・創業年、代表商品の容量・重量・価格帯、日本での購入可否をまとめました。"
        org_schema = {
            "@context": "https://schema.org",
            "@type": "Brand",
            "name": brand["name"],
            "description": brand.get("description", ""),
            "url": brand.get("officialUrl", ""),
            "foundingDate": str(brand.get("founded", "")),
            "slogan": brand.get("nameKana", ""),
        }
        html = page_shell(
            title, description, "/gear/brands/" + brand["id"] + "/", "/gear/brands/", "BRAND", body,
            breadcrumbs=[("ホーム", "/"), ("ギア", "/gear/"), ("ブランド一覧", "/gear/brands/"), (brand["name"], None)],
            extra_jsonld=org_schema,
            og_image=("https://tozan-navi.com" + brand["heroImage"]) if brand.get("heroImage") else None
        )
        write("gear/brands/" + brand["id"] + "/index.html", html)


# ---------- 4. カテゴリページ /gear/category/{id}/ ----------

def gen_category_pages():
    for c in CATEGORIES:
        if c["status"] == "coming_soon":
            body = """
<div class="pgtitle">
  <span class="pg-eyebrow">GEAR / CATEGORY</span>
  <h1>""" + esc(c["name"]) + """</h1>
  <p>""" + esc(c["description"]) + """</p>
</div>
<div class="empty-note">""" + esc(c["name"]) + """は準備中です。追加され次第、このページで紹介します。</div>
<div class="other-links" style="margin-top:20px"><a href="/gear/">← ギアトップへ戻る</a></div>
"""
        else:
            matched = [i for i in ITEMS if i.get("categoryId") == c["id"]]
            items_html = "".join([render_item_card(i) for i in matched]) if matched else '<div class="empty-note">現在このカテゴリの商品を準備中です。</div>'
            hero_html = ""
            if c.get("heroImage"):
                hero_html = '<img src="' + esc(c["heroImage"]) + '" alt="' + esc(c["name"]) + 'を身につけて山の稜線で休憩する登山者たち" class="gear-hero-img" loading="eager">'
            body = """
<div class="pgtitle">
  <span class="pg-eyebrow">GEAR / CATEGORY</span>
  <h1>""" + esc(c["name"]) + """</h1>
  <p>""" + esc(c["description"]) + """</p>
</div>
""" + hero_html + """
""" + items_html + """
<div class="other-links" style="margin-top:20px"><a href="/gear/">← ギアトップへ戻る</a> ｜ <a href="/gear/brands/">ブランド一覧へ</a></div>
"""
        title = c["name"] + "｜海外ブランドの登山用品を探す - Yamatch"
        description = c["description"]
        item_list_schema = None
        if c["status"] != "coming_soon" and matched:
            item_list_schema = {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "name": c["name"],
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "name": it["name"],
                        "url": "https://tozan-navi.com/gear/brands/" + it["brandId"] + "/",
                    }
                    for i, it in enumerate(matched)
                ],
            }
        html = page_shell(
            title, description, "/gear/category/" + c["id"] + "/", "/gear/", "CATEGORY", body,
            breadcrumbs=[("ホーム", "/"), ("ギア", "/gear/"), (c["name"], None)],
            extra_jsonld=item_list_schema,
            noindex=(c["status"] == "coming_soon"),
            og_image=("https://tozan-navi.com" + c["heroImage"]) if c.get("heroImage") else None
        )
        write("gear/category/" + c["id"] + "/index.html", html)


# ---------- 5. コレクションページ /gear/collections/{id}/ ----------

def item_matches_filter(item, brand, f):
    if "categoryId" in f and item.get("categoryId") != f["categoryId"]:
        return False
    if "brandTag" in f and f["brandTag"] not in (brand.get("tags") or []):
        return False
    if "brandCountry" in f and brand.get("country") != f["brandCountry"]:
        return False
    if "capacityMin" in f or "capacityMax" in f:
        cap = item.get("capacityL")
        if cap is None:
            return False
        if "capacityMin" in f and cap < f["capacityMin"]:
            return False
        if "capacityMax" in f and cap > f["capacityMax"]:
            return False
    if "weightMax" in f:
        w = item.get("weightG")
        if w is None or w > f["weightMax"]:
            return False
    return True


def gen_collection_pages():
    for col in COLLECTIONS:
        f = col["filter"]
        matched = [i for i in ITEMS if item_matches_filter(i, BRAND_BY_ID.get(i["brandId"], {}), f)]
        # ブランド国だけの絞り込み(korea-brands等)はブランドカードも出す
        brand_matches = []
        if "brandCountry" in f and "categoryId" not in f:
            brand_matches = [b for b in BRANDS if b.get("country") == f["brandCountry"]]

        items_html = "".join([render_item_card(i) for i in matched])
        brand_cards_html = "".join([render_brand_card(b) for b in brand_matches])

        if not matched and not brand_matches:
            content = '<div class="empty-note">現在この条件に合う商品を準備中です。</div>'
        else:
            content = brand_cards_html + items_html

        body = """
<div class="pgtitle">
  <span class="pg-eyebrow">""" + esc(col["eyebrow"]) + """</span>
  <h1>""" + esc(col["title"]) + """</h1>
  <p>""" + esc(col["description"]) + """</p>
</div>
""" + content + """
<div class="other-links" style="margin-top:20px"><a href="/gear/">← ギアトップへ戻る</a></div>
"""
        title = col["title"] + "｜Yamatch ギアデータベース"
        item_list_schema = None
        if matched:
            item_list_schema = {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "name": col["title"],
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "name": it["name"],
                        "url": "https://tozan-navi.com/gear/brands/" + it["brandId"] + "/",
                    }
                    for i, it in enumerate(matched)
                ],
            }
        html = page_shell(
            title, col["description"], "/gear/collections/" + col["id"] + "/", "/gear/", "COLLECTION", body,
            breadcrumbs=[("ホーム", "/"), ("ギア", "/gear/"), (col["title"], None)],
            extra_jsonld=item_list_schema
        )
        write("gear/collections/" + col["id"] + "/index.html", html)


# ---------- 6. 山→ギア 逆引きデータ(将来の山ページ統合用) ----------

def gen_mountain_gear_links():
    links = {}
    for b in BRANDS:
        for mid in b.get("relatedMountainIds", []):
            links.setdefault(mid, {"recommendedBrandIds": [], "recommendedItemIds": []})
            links[mid]["recommendedBrandIds"].append(b["id"])
    for item in ITEMS:
        for mid in item.get("relatedMountainIds", []) or []:
            links.setdefault(mid, {"recommendedBrandIds": [], "recommendedItemIds": []})
            links[mid]["recommendedItemIds"].append(item["id"])
    write("data/mountain-gear-links.json", json.dumps(links, ensure_ascii=False, indent=2))


def write(rel_path, content):
    full = os.path.join(OUT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("generated:", rel_path)


def main():
    gen_hub()
    gen_brand_list()
    gen_brand_pages()
    gen_category_pages()
    gen_collection_pages()
    gen_mountain_gear_links()


if __name__ == "__main__":
    main()
