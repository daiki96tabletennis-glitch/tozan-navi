"""タイプ診断の結果の画面（recommend/index.html）とタイプのページ（type/*/、type/index.html）の絵文字を、
線画のアイコン（scripts/ym_icons.py。Lucide と、同じ描き方で作ったもの）に置き換える（2026-11-10。運営者の指示）

- 決まった場所の絵文字だけを置き換える（質問の画面の絵文字・シェア画像の中の ✦・alert の文は対象外）
- 何度流しても同じ結果（置き換えたあとは絵文字が無いので 0 件になる）
- 置き換えの数が想定と違えば止まる
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from ym_icons import svg, mask_url, body  # noqa: E402

# タイプの記号 → アイコン、ページのスラッグ
TYPE_ICON = {
    'ACPS': 'mountain-snow', 'ACPL': 'mountain', 'ACFS': 'climber', 'ACFL': 'map',
    'AHPS': 'camera', 'AHPL': 'sunrise', 'AHFS': 'party-popper', 'AHFL': 'aperture',
    'VCPS': 'book-open', 'VCPL': 'lantern', 'VCFS': 'route', 'VCFL': 'tree-pine',
    'VHPS': 'mountain-hut', 'VHPL': 'meditation', 'VHFS': 'picnic-basket', 'VHFL': 'trees',
}
TYPE_SLUG = {'ACFL': 'variation-seeker', 'ACFS': 'wild-hiker', 'ACPL': 'solitary-climber', 'ACPS': 'mountain-explorer',
             'AHFL': 'photo-walker', 'AHFS': 'party-hiker', 'AHPL': 'silent-climber', 'AHPS': 'view-hunter',
             'VCFL': 'hidden-hiker', 'VCFS': 'mountain-traveler', 'VCPL': 'deep-mountain-seeker', 'VCPS': 'mountain-researcher',
             'VHFL': 'forest-wanderer', 'VHFS': 'mountain-picnic', 'VHPL': 'meditation-hiker', 'VHPS': 'mountain-resort'}
SLUG_TYPE = {v: k for k, v in TYPE_SLUG.items()}
GEAR_ICON = {'shoe': 'hiking-boot', 'crampon': 'snowflake', 'crampon_next': 'snowflake', 'axe': 'pickaxe', 'rain': 'rain-jacket',
             'down': 'down-jacket', 'pole': 'trekking-pole', 'bottle': 'water-bottle', 'bell': 'bell', 'helmet': 'hard-hat'}

# 文字と並べるアイコンの共通の見た目（文字の高さに合わせ、少し下げる）
IC_CSS = '.ym-ic{display:inline-block;vertical-align:-0.14em;flex-shrink:0;}'
MARK = '/* ym-icons */'


def sub(s, old, new, count, label):
    if old not in s and new in s:
        return s  # 置き換え済み
    n = s.count(old)
    if n != count:
        raise SystemExit('%s：%d 件（想定 %d 件）%s' % (label, n, count, old[:60]))
    return s.replace(old, new)


def add_css(s, css, label):
    if MARK in s:
        return s
    assert s.count('</style>') >= 1, label
    return s.replace('</style>', MARK + css + '\n</style>', 1)


def check_mark_css(sel, color=None):
    """::before の ✓ を、線画の check を mask で描いたものにする"""
    return ('%s{content:"";display:inline-block;width:1em;height:1em;vertical-align:-0.14em;background:currentColor;'
            '-webkit-mask:%s center/contain no-repeat;mask:%s center/contain no-repeat;%s}'
            % (sel, mask_url('check'), mask_url('check'), ('color:%s;' % color) if color else ''))


def recommend():
    p = os.path.join(ROOT, 'recommend', 'index.html')
    s = open(p, encoding='utf-8').read()
    L = 'recommend'
    reps = [
        ('    ⚠️ これはこのタイプの標準的な傾向を表示しています。', '    ' + svg('triangle-alert') + ' これはこのタイプの標準的な傾向を表示しています。', 1),
        ('📸 シェア画像を保存（正方形）', svg('image-down') + ' シェア画像を保存（正方形）', 1),
        ('📱 ストーリー用を保存（縦長）', svg('smartphone') + ' ストーリー用を保存（縦長）', 1),
        ('<div class="radar-section-title">📊 あなたの登山スタイル診断</div>', '<div class="radar-section-title">' + svg('radar-chart') + ' あなたの登山スタイル診断</div>', 1),
        ('<span class="radar-score-label">⚡ 行動力</span>', '<span class="radar-score-label">' + svg('zap') + ' 行動力</span>', 1),
        ('<span class="radar-score-label">🏔 挑戦心</span>', '<span class="radar-score-label">' + svg('mountain-snow') + ' 挑戦心</span>', 1),
        ('<span class="radar-score-label">📋 計画性</span>', '<span class="radar-score-label">' + svg('clipboard-list') + ' 計画性</span>', 1),
        ('<span class="radar-score-label">👥 社交性</span>', '<span class="radar-score-label">' + svg('users') + ' 社交性</span>', 1),
        ('<div class="analysis-title">🔍 あなたの診断プロフィール</div>', '<div class="analysis-title">' + svg('id-card') + ' あなたの診断プロフィール</div>', 1),
        ('<div class="sw-title">💡 あなたの登山スタイル</div>', '<div class="sw-title">' + svg('lightbulb') + ' あなたの登山スタイル</div>', 1),
        ('<div class="sw-label s">🔥 強み</div>', '<div class="sw-label s">' + svg('flame') + ' 強み</div>', 1),
        ('<div class="sw-label w">⚠️ 注意点</div>', '<div class="sw-label w">' + svg('triangle-alert') + ' 注意点</div>', 1),
        ('<div class="share-title">📤 友達にも診断してもらおう</div>', '<div class="share-title">' + svg('share-2') + ' 友達にも診断してもらおう</div>', 1),
        ('class="share-btn sb-line">💬 LINE</a>', 'class="share-btn sb-line">' + svg('message-circle') + ' LINE</a>', 1),
        ('onclick="copyResult()">🔗 URLコピー</button>', 'onclick="copyResult()">' + svg('link') + ' URLコピー</button>', 1),
        ('onclick="restart()">↺ もう一度診断する</button>', 'onclick="restart()">' + svg('rotate-ccw') + ' もう一度診断する</button>', 1),
        # おすすめの山のカード（JS の文字列。' を含まない SVG なのでそのまま入る）
        ("'<span class=\"rc-elev\">🏔 '+", "'<span class=\"rc-elev\">" + svg('mountain') + " '+", 1),
        ("'<span class=\"rc-drive-tag\">🚃 電車OK</span>'", "'<span class=\"rc-drive-tag\">" + svg('train-front') + " 電車OK</span>'", 1),
        ("'<div class=\"rc-section-label\">📍 あなたにおすすめの理由</div>'", "'<div class=\"rc-section-label\">" + svg('badge-check') + " あなたにおすすめの理由</div>'", 1),
        ("'<div class=\"rc-section-label\">🎒 '+CURRENT_GEAR_MONTH", "'<div class=\"rc-section-label\">" + svg('backpack') + " '+CURRENT_GEAR_MONTH", 1),
        ("'<div class=\"rc-section-label\">🚌 アクセス</div>'", "'<div class=\"rc-section-label\">" + svg('bus') + " アクセス</div>'", 1),
        ('<span style="font-size:18px;">🤝</span><span class="compat-title">', '<span style="font-size:18px;display:flex;color:#4e6535;">' + svg('handshake') + '</span><span class="compat-title">', 1),
        (".rc-reason::before{content:\"✓ \";font-weight:700;}", check_mark_css('.rc-reason::before') + '.rc-reason::before{margin-right:4px;}', 1),
    ]
    for old, new, n in reps:
        s = sub(s, old, new, n, L)
    # 装備のアイコン：名前の表にして、描くときに SVG にする
    gear_js = 'var GEAR_CAT_ICON={' + ','.join("%s:'%s'" % (k, v) for k, v in GEAR_ICON.items()) + '};'
    s = sub(s, "var GEAR_CAT_ICON={shoe:'👟',crampon:'❄️',crampon_next:'❄️',axe:'⛏️',rain:'🧥',down:'🧤',pole:'🦯',bottle:'💧',bell:'🔔',helmet:'⛑️'};",
            gear_js, 1, L)
    s = sub(s, "icon:GEAR_CAT_ICON[catKey]||'🎒',", "icon:ymIcon(GEAR_CAT_ICON[catKey]||'backpack'),", 1, L)
    # タイプのカードの大きな背景
    s = sub(s, "'<div class=\"type-card-bg\">'+type.emoji+'</div>'+", "'<div class=\"type-card-bg\">'+ymIcon(TYPE_ICON[typeCode])+'</div>'+", 1, L)
    # JS で使うアイコンの表（装備・タイプの背景）。JS の中に書く SVG は ' を含まない
    used = sorted(set(GEAR_ICON.values()) | set(TYPE_ICON.values()) | {'backpack'})
    js = ('\n// 線画のアイコン（scripts/ym_icons.py から。Lucide＝ISC License と、同じ描き方で作ったもの）。2026-11-10〜\n'
          'var YM_ICON_BODY={' + ','.join("'%s':'%s'" % (n, body(n)) for n in used) + '};\n'
          'var TYPE_ICON={' + ','.join("%s:'%s'" % (k, v) for k, v in TYPE_ICON.items()) + '};\n'
          "function ymIcon(n){var b=YM_ICON_BODY[n]||YM_ICON_BODY.backpack;return '<svg class=\"ym-ic\" width=\"1em\" height=\"1em\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\">'+b+'</svg>';}\n")
    if 'var YM_ICON_BODY=' not in s:
        s = sub(s, "var GEAR_CAT_ICON={", js + "var GEAR_CAT_ICON={", 1, L)
    # 見た目：文字と並ぶアイコン、背景の大きなアイコンの色
    css = (IC_CSS + '.type-card-bg .ym-ic{display:block;}.gear-icon{display:flex;color:#4e6535;}'
           '.radar-score-label .ym-ic,.rc-section-label .ym-ic,.rc-drive-tag .ym-ic,.analysis-title .ym-ic{color:#4e6535;}'
           '.sw-label.w .ym-ic{color:#b05030;}')
    s = add_css(s, css, L)
    assert '.analysis-title{' in s
    open(p, 'w', encoding='utf-8').write(s)


def type_pages():
    n_pages = 0
    for p in sorted(glob.glob(os.path.join(ROOT, 'type', '*', 'index.html'))):
        slug = os.path.basename(os.path.dirname(p))
        code = SLUG_TYPE[slug]
        s = open(p, encoding='utf-8').read()
        # ページのタイプの大きな背景
        s2, k = re.subn(r'<div class="type-hero-bg">[^<]*</div>', '<div class="type-hero-bg">' + svg(TYPE_ICON[code]) + '</div>', s)
        if k != 1 and '<div class="type-hero-bg"><svg' not in s:
            raise SystemExit('type-hero-bg %s %d' % (slug, k))
        s = s2

        # 相性の良い登山タイプの印（絵文字と、前に一部だけ入れた Lucide の両方を同じ形にする）
        def chip(m):
            href, label = m.group(1), m.group(3).strip()
            c = SLUG_TYPE[href.strip('/').split('/')[-1]]
            return '<a href="%s" class="type-chip">%s %s</a>' % (href, svg(TYPE_ICON[c]), label)
        s, k = re.subn(r'<a href="(/type/[a-z-]+/)" class="type-chip">((?:<svg.*?</svg>)|[^\s<]+)\s*([^<]+)</a>', chip, s)
        if k == 0:
            raise SystemExit('type-chip %s' % slug)
        css = (IC_CSS + '.type-hero-bg .ym-ic{display:block;}.type-chip{display:inline-flex;align-items:center;gap:4px;}'
               + check_mark_css('.features-list li::before', '#4a6038'))
        s = add_css(s, css, slug)
        # 特徴の ✓（CSS の content の文字）は消し、上の mask の線画で描く
        s = s.replace(".features-list li::before{content:'✓';", ".features-list li::before{content:'';")
        open(p, 'w', encoding='utf-8').write(s)
        n_pages += 1
    # タイプの一覧
    p = os.path.join(ROOT, 'type', 'index.html')
    s = open(p, encoding='utf-8').read()
    s = sub(s, '🧭 登山タイプ診断・全16タイプ', svg('compass') + ' 登山タイプ診断・全16タイプ', 1, 'type/index')
    s = sub(s, '<span class="badge">⏱ 12問・約2分</span>', '<span class="badge">' + svg('timer') + ' 12問・約2分</span>', 1, 'type/index')
    s = add_css(s, IC_CSS, 'type/index')
    open(p, 'w', encoding='utf-8').write(s)
    return n_pages


def main():
    recommend()
    n = type_pages()
    print('recommend/index.html と タイプのページ %d 件・一覧を書き換え' % n)


if __name__ == '__main__':
    main()
