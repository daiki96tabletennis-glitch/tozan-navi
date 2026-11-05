"""記事「冬でも登れる関東の山7選｜雪なし・アイゼン不要（12〜2月）」を作り直す（2026-11-05。運営者の指示）

1回目（5選→7選）：筑波山・明神ヶ岳を足し、5山の値をいまのデータに合わせた
2回目（サイト内の人気記事・検索上位の他サイトの記事と比べた改善）：
- 検索の見出し・説明文を、実際に検索されている言葉（「冬でも登れる 山 関東」「12月 登山 雪 なし 関東」）に合わせる
- 人気記事と同じ作り：目次、山ごとの見出し（h2「① 高尾山（たかおさん）」）、最後に7山の比較表
- 冬に行く前に役立つ情報（データか公式の出典があるものだけ）：
  代表コース（routes の1番目）の歩く時間と「何時までに歩き始めるか」（12月上旬の東京の日の入り 16:28＝国立天文台。
  日の入りの約1時間前の15:30に下山を終えるとして、歩く時間を引き、10分単位で切り下げる。休憩は含まない）、
  帰りの最終バス（data/train_daytrip.json で公式の時刻表を確かめた値がある山だけ）、ケーブルカー・ロープウェーの有無（山のデータに書いてあるものだけ）
- よくある質問を画面にも出す（前は Google 向けのデータの中だけにあった）

値は mountains.json・gear-data.json・train_daytrip.json から作る。特徴・おすすめ理由の文は前のカードから引き継ぐ（足した2山は featurePoints に書いてあることだけで書いた）。
写真はページのスクリプトが mountains.json の photos から入れる。前のカードにあった記事の写真（images/photo-0X.jpg）と、弘法山の閉鎖の注意（data-closed）は引き継ぐ。
何度流しても同じ結果になる。
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAGE = os.path.join(ROOT, 'articles', 'winter-no-crampons', 'index.html')
UPDATED = '2026-11-05'
ORDER = ['takao', 'nokogiriyama_chiba', 'koubousan', 'mitakesan', 'jinba', 'tsukuba', 'myojingatake']
NUM = '①②③④⑤⑥⑦'
TITLE = '冬でも登れる関東の山7選｜雪なし・アイゼン不要（12〜2月）'
SHORT = '冬でも登れる関東の山7選（雪なし・アイゼン不要）'
SUNSET = ('16時28分', 'https://eco.mtk.nao.ac.jp/koyomi/dni/2026/s1312.html')  # 東京・2026年12月1〜13日（国立天文台 暦計算室）
FINISH = 15 * 60 + 30  # 下山を終える目安（日の入りの約1時間前）
NEW_TEXT = {
    'tsukuba': (
        '「西の富士、東の筑波」と並び称された百名山。男体山と女体山の2つの峰があり、最高点の女体山から霞ヶ浦と関東平野を見下ろす360度の眺めが広がります。',
        '白雲橋コースは「弁慶七戻り」「胎内くぐり」「ガマ石」など、名前のついた巨岩が次々に現れて飽きません。2つの峰のあいだの御幸ヶ原にはケーブルカーの駅と食堂・売店があり、山頂の本殿では登った人だけの御朱印を受けられます。',
    ),
    'myojingatake': (
        '箱根の外輪山のひとつ。山全体がカヤとササにおおわれて空が広く、日が当たると笹が黄金色に光ります。',
        '山頂から金時山の向こうに富士山が見え、大涌谷・芦ノ湖・相模湾までぐるりと見渡せます。大雄山駅からバスで行ける最乗寺から登れ、金時山へ尾根をつないで歩くこともできます。7山の中ではいちばん高い1,169mですが、装備の区分は冬も「アイゼン不要」です。',
    ),
}
# ケーブルカー・ロープウェー（山のデータ＝featurePoints・train_daytrip.json の文に書いてあるものだけ）
LIFT = {
    'takao': 'ケーブルカー・リフト',
    'nokogiriyama_chiba': 'ロープウェー',
    'mitakesan': 'ケーブルカー',
    'tsukuba': 'ケーブルカー',
}

CAR_SVG = ('<svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><path d="M4 13l1.5-4A2 2 0 0 1 7.3 8h9.4a2 2 0 0 1 1.8 1.2L20 13z" fill="currentColor"/><rect x="2.5" y="13" width="19" height="4.5" rx="2" fill="currentColor"/><rect x="6.5" y="9.2" width="4" height="2.8" rx="0.5" fill="white"/><rect x="11.5" y="9.2" width="6" height="2.8" rx="0.5" fill="white"/><circle cx="6.5" cy="17.5" r="1.6" fill="#3a3530"/><circle cx="17.5" cy="17.5" r="1.6" fill="#3a3530"/></svg>')
TRAIN_SVG = ('<svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><path d="M2 7 H14 L20 11.5 V17 H2 Z" fill="currentColor"/><rect x="4" y="9.5" width="3" height="3" fill="white"/><rect x="9" y="9.5" width="3" height="3" fill="white"/><line x1="1" y1="19.5" x2="21" y2="19.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>')
THUMB_SVG = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:3px;display:inline-block"><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/><path d="M7 10v12"/></svg>')
H2_RESET = 'margin:0;padding:0;border:none;font-size:18px;line-height:1.4'
TD = 'padding:7px 8px;border-bottom:1px solid #e6e1d6;vertical-align:top;white-space:nowrap'
TH = TD + ';background:#f3f0e8;color:#4a5e3a;font-weight:700;white-space:nowrap;text-align:left'
E = html.escape


def mins(n):
    n = int(n)
    if n < 60:
        return f'約{n}分'
    h, m = divmod(n, 60)
    return f'約{h}時間' + (f'{m}分' if m else '')


def walk_min(t):
    h = re.search(r'(\d+)時間', t)
    m = re.search(r'(\d+)分', t)
    return (int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0)


def hm(n):
    return f'{n // 60}時{n % 60:02d}分'


def short_area(a):
    m = re.match(r'^(東京都|北海道|.+?[都道府県])', a or '')
    return m.group(1) if m else a


def train_label(m):
    legs = (((m.get('trainRoutes') or {}).get('routes') or {}).get('shinjuku') or {}).get('legs') or []
    icons = {((l.get('method') or {}).get('icon')) for l in legs}
    if 'bus' in icons:
        return '電車・バス'
    if 'ropeway' in icons:
        return '電車・ケーブルカー'
    return '電車'


def winter_badge(cal):
    flat = lambda c: [c] if not isinstance(c, dict) else [c.get('before'), c.get('after')]
    if all(v == 'no_crampons' for c in cal for v in flat(c)):
        return '❄️ 通年アイゼン不要'
    if all(v == 'no_crampons' for i in (11, 0, 1) for v in flat(cal[i])):
        return '❄️ 12〜2月アイゼン不要'
    raise SystemExit('冬にアイゼン不要でない山が入っている')


def variants_attr(md):
    groups, order = {}, []
    for month in sorted(md.keys(), key=int):
        key = json.dumps(md[month], ensure_ascii=False)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(int(month))
    return json.dumps({k: groups[k] for k in order}, ensure_ascii=False).replace('"', '&quot;')


def old_texts(s):
    """前のカードから、特徴・おすすめ理由・閉鎖の注意・記事の写真を山ごとに読む"""
    out = {}
    for cm in re.finditer(r'<div class="mountain-card"[^>]*>([\s\S]*?)(?=<div class="mountain-card"|<h2(?! class="mountain-card-title")|<!-- winter-list:end -->)', s):
        c = cm.group(1)
        mid = re.search(r'data-mountain-id="([^"]+)"', c).group(1)
        feat = re.search(r'<span class="info-label">特徴</span><span class="info-val">([\s\S]*?)</span></div>', c)
        why = re.search(r'<strong>おすすめ理由：</strong>([\s\S]*?)</div>', c)
        closed = re.search(r'(<div class="mc-closed"[\s\S]*?</div>)', c)
        img = re.search(r'(<img src="[^"]*" class="mountain-photo"[^>]*>)', c)
        out[mid] = (html.unescape(feat.group(1)) if feat else None, html.unescape(why.group(1)) if why else None,
                    closed.group(1) if closed else '', img.group(1) if img else '')
    return out


def last_bus(mid, td):
    lb = (td.get('lastBus') or {}).get(mid) or {}
    if lb.get('status') != 'ok' or not lb.get('rows'):
        return ''
    r = lb['rows'][0]
    t = f'{r["from"]}→{r["to"]}（{lb["operator"]}）：平日 {r["weekday"]}／土日祝 {r["holiday"]}'
    if lb.get('note'):
        t += '。' + lb['note']
    return (t + f'（<a href="{E(lb["sourceUrl"])}" target="_blank" rel="noopener" style="color:#4a6038">時刻表</a>・{E(lb["revised"])}改正）')


def row(label, val):
    return f'    <div class="info-row"><span class="info-label">{label}</span><span class="info-val">{val}</span></div>\n'


def card(i, m, feat, why, closed, img, gear, td):
    mid = m['id']
    rng = f'{m["coeffMin"]}〜{m["coeffMax"]}' if m.get('coeffMin') != m.get('coeffMax') else str(m['coeffMin'])
    r0 = m['routes'][0]
    w = walk_min(r0['time'])
    start = (FINISH - w) // 10 * 10
    bus = last_bus(mid, td)
    rows = (
        row(f'{CAR_SVG} 車', f'新宿から{mins(m["driveTimeShinjuku"])}')
        + row(f'{TRAIN_SVG} 電車', f'新宿から{train_label(m)}{mins(m["trainTimeShinjuku"])}')
        + row('代表コース', f'{E(r0["name"])}／歩く時間 {E(r0["time"])}（難易度 {E(m["difficulty"])}）')
        + row('冬の歩き始め', f'<strong>{hm(start)}まで</strong>に歩き始める（15時30分に下山を終える場合。休憩の時間は含まない）')
        + (row('帰りの最終バス', bus) if bus else '')
        + (row('乗り物', f'{LIFT[mid]}で登り下りを短くできる') if mid in LIFT else '')
        + row('コース定数', f'<span class="coeff-badge">{rng}</span><span class="winter-badge">{winter_badge(m["gearCalendar"])}</span>')
        + row('特徴', E(feat))
    )
    return (
        f'<div class="mountain-card" id="m-{mid}">\n'
        f'  <div class="mountain-card-header" data-mountain-id="{mid}">\n'
        f'    <h2 class="mountain-card-title" style="{H2_RESET}">{NUM[i]} {E(m["name"])}（{E(m.get("kana") or "")}）</h2>\n'
        f'    <div class="mountain-card-sub">{E(short_area(m["area"]))}・標高{m["elevation"]:,}m</div>\n'
        '  </div>\n'
        + (f'  {img}\n' if img else '')
        + (f'  {closed}\n' if closed else '') +
        '  <div class="mountain-card-body">\n'
        + rows +
        f'    <div class="reason-box">{THUMB_SVG} <strong>おすすめ理由：</strong>{E(why)}</div>\n'
        f'    <a href="/mountains/{mid}/" class="detail-link">{E(m["name"])}の詳細情報を見る →</a>'
        f'<div class="gear-section-label"><img src="/images/icons/backpack.webp" width="18" height="18" alt="" style="vertical-align:-4px;margin-right:2px"> {E(m["name"])}の装備</div>'
        f'<div class="gear-cards-scroll" data-gear-mid="{mid}" data-gear-variants="{variants_attr(gear[mid])}"></div>\n'
        '  </div>\n'
        '</div>'
    )


def toc(ms):
    items = ''.join(f'<li style="margin:3px 0"><a href="#m-{i}" style="color:#4a6038">{NUM[k]} {E(ms[i]["name"])}</a></li>' for k, i in enumerate(ORDER))
    extra = ''.join(f'<li style="margin:3px 0"><a href="#{a}" style="color:#4a6038">{t}</a></li>' for a, t in (
        ('compare', '7山の比較表'), ('tips', '冬の山歩きで気をつけること'), ('faq', 'よくある質問')))
    return ('<nav class="tips-card" id="toc" aria-label="目次" style="padding:16px 20px">'
            '<div style="font-weight:700;color:#2a3e2a;margin-bottom:6px">目次</div>'
            f'<ul style="margin:0;padding:0;list-style:none;font-size:14px;line-height:1.7">{items}</ul>'
            f'<ul style="margin:6px 0 0;padding:6px 0 0;list-style:none;border-top:1px dashed #ddd8d0;font-size:14px;line-height:1.7">{extra}</ul></nav>\n')


def compare_table(ms):
    head = ''.join(f'<th style="{TH}">{h}</th>' for h in ('山', '標高', '新宿から電車', '新宿から車', '代表コースの歩く時間', '難易度', '乗り物'))
    body = ''
    for k, i in enumerate(ORDER):
        m = ms[i]
        cells = [f'<a href="#m-{i}" style="color:#4a6038;font-weight:700">{NUM[k]} {E(m["name"])}</a>', f'{m["elevation"]:,}m',
                 mins(m['trainTimeShinjuku']), mins(m['driveTimeShinjuku']), E(m['routes'][0]['time']), E(m['difficulty']), LIFT.get(i, '—')]
        body += '<tr>' + ''.join(f'<td style="{TD}">{c}</td>' for c in cells) + '</tr>'
    return ('<h2 id="compare">7山の比較表</h2>\n'
            '<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;margin-bottom:8px">'
            f'<table style="border-collapse:collapse;width:100%;min-width:620px;font-size:13px;background:#fff;border-radius:10px">'
            f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>\n'
            '<p style="font-size:12px;color:#8a8078;margin:0 0 8px">電車・車は新宿からの目安。歩く時間は各山の代表コース（休憩を含まないコースタイム）。7山とも、Yamatch の装備カレンダーで12か月「アイゼン不要」の区分です。</p>\n')


def faq_items(s):
    m = re.search(r'"@type":"FAQPage","mainEntity":(\[[\s\S]*?\])\}</script>', s)
    return json.loads(m.group(1))


def faq_block(items):
    qa = ''.join(
        '<details class="tips-card" style="padding:14px 18px;margin-bottom:10px">'
        f'<summary style="font-weight:700;color:#2a3e2a;cursor:pointer">{E(q["name"])}</summary>'
        f'<p style="margin:8px 0 0">{E(q["acceptedAnswer"]["text"])}</p></details>'
        for q in items)
    return f'<!-- winter-faq:start --><h2 id="faq">よくある質問</h2>\n{qa}\n<!-- winter-faq:end -->\n'


def sub1(pat, rep, s, count=0):
    t, n = re.subn(pat, rep, s, count=count)
    if n < 1:
        raise SystemExit('見つからない: ' + pat)
    return t


def main():
    ms = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data/mountains.json')))}
    gear = json.load(open(os.path.join(ROOT, 'data/gear-data.json')))
    td = json.load(open(os.path.join(ROOT, 'data/train_daytrip.json')))
    s = open(PAGE, encoding='utf-8').read()
    old = old_texts(s)
    names = '・'.join(ms[i]['name'] for i in ORDER)
    cards = []
    for i, mid in enumerate(ORDER):
        f, w, c, im = old.get(mid, (None, None, '', ''))
        if mid in NEW_TEXT:
            f, w = NEW_TEXT[mid]
        if not f or not w:
            raise SystemExit('文が無い: ' + mid)
        cards.append(card(i, ms[mid], f, w, c, im, gear, td))
    block = ('<!-- winter-list:start -->' + toc(ms) + '<h2>おすすめ7山</h2>' + ''.join(cards) + '\n'
             + compare_table(ms) + '<!-- winter-list:end -->\n')
    if '<!-- winter-list:start -->' in s:
        s = sub1(r'<!-- winter-list:start -->[\s\S]*?<!-- winter-list:end -->\n', block.replace('\\', '\\\\'), s)
    else:
        s = sub1(r'<h2>おすすめ[57]山</h2>[\s\S]*?(?=<h2>冬山登山で気をつけること)', block.replace('\\', '\\\\'), s)

    # 冬の山歩きで気をつけること（見出しに id、装備と日没の文）
    s = sub1(r'<h2( id="tips")?>冬山登山で気をつけること</h2>', '<h2 id="tips">冬山登山で気をつけること</h2>', s)
    s = sub1(r'<p>低山でもチェーンスパイク[\s\S]*?</p>',
             '<p>低山でもチェーンスパイク（軽アイゼン）を念のため持参すると安心。雪が降ったあとの数日は、日の当たらない斜面や木道に凍結が残ることがあります。'
             '持ち物は<a href="/packing/" style="color:#4a6038;font-weight:bold">持ち物チェックリスト</a>（日帰りのリストを自分用に直せます）と'
             '<a href="/guide/gear-checklist/" style="color:#4a6038;font-weight:bold">冬山の持ち物ガイド</a>で確認しておきましょう。</p>', s)
    s = sub1(r'<p>(冬は日没が早いため|12月上旬の東京の日の入りは)[\s\S]*?</p>',
             f'<p>12月上旬の東京の日の入りは{SUNSET[0]}で、1年でいちばん早い時期です（<a href="{SUNSET[1]}" target="_blank" rel="noopener" style="color:#4a6038">国立天文台</a>）。'
             '山の中は早く暗くなるので、15時30分ごろには下山を終える計画にしましょう。各山の「冬の歩き始め」は、この時刻から代表コースの歩く時間を引いた目安です（休憩の時間は含みません）。</p>', s)

    # よくある質問を画面にも出す（中身は Google 向けのデータと同じ）
    desc = f'12〜2月も雪や凍結が続かず、アイゼンなしで登れる関東の山7選。{names}を、新宿からの時間・歩く時間・冬は何時までに歩き始めるか・帰りの最終バスで比べられます。'
    s = sub1(r'"text":"高尾山・鋸山・弘法山・御岳山・陣馬山(・筑波山・明神ヶ岳)?など[^"]*"',
             f'"text":"{names}など、関東の標高1,200m以下の山は太平洋側の気候の影響で積雪が少なく、Yamatchの装備の区分では冬も「アイゼン不要」です。ただし雪が降ったあとの数日は凍結が残ることがあるので、出発前に直近の降雪を確認してください。"', s)
    s = sub1(r'\{"@type":"Question","name":"(❄️通年アイゼン不要と積雪少\(要確認\)の違いは何ですか？|「❄️ 通年アイゼン不要」は何を基準にしていますか？)","acceptedAnswer":\{"@type":"Answer","text":"[^"]*"\}\}',
             '{"@type":"Question","name":"「❄️ 通年アイゼン不要」は何を基準にしていますか？","acceptedAnswer":{"@type":"Answer","text":"Yamatchの装備カレンダーで、12か月すべてが「アイゼン不要」の区分になっている山です。雪が降ったあとの数日だけ滑り止めが要る日は例外として扱っているので、念のためチェーンスパイクを持っていくと安心です。"}}', s)
    faq = faq_block(faq_items(s))
    if '<!-- winter-faq:start -->' in s:
        s = sub1(r'<!-- winter-faq:start -->[\s\S]*?<!-- winter-faq:end -->\n', faq.replace('\\', '\\\\'), s)
    else:
        s = sub1(r'(?=<h2>まとめ：)', faq.replace('\\', '\\\\'), s, count=1)

    # 検索の見出し・説明文・見出し
    s = sub1(r'<title>[^<]*</title>', f'<title>{TITLE}【2026-27年冬】 | Yamatch</title>', s)
    s = sub1(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', s)
    s = sub1(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{TITLE} | Yamatch">', s)
    s = sub1(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{desc}">', s)
    s = sub1(r'"headline":"[^"]*","description":"[^"]*"', f'"headline":"{TITLE}","description":"{desc}"', s)
    s = sub1(r'"dateModified":"[0-9-]+"', f'"dateModified":"{UPDATED}"', s)
    s = sub1(r'"name":"(アイゼン不要で冬に登れる山[57]選|冬でも登れる関東の山7選（雪なし・アイゼン不要）)"', f'"name":"{SHORT}"', s)
    s = sub1(r'<h1 class="article-title">[\s\S]*?</h1>', '<h1 class="article-title">冬でも登れる関東の山7選<br>雪なし・アイゼン不要（12〜2月）</h1>', s)
    s = sub1(r'<p class="article-desc">[\s\S]*?</p>',
             '<p class="article-desc">12〜2月も雪や凍結が続かず、アイゼンなしで登れる関東の山を7つ選びました。新宿からの時間、歩く時間、冬は何時までに歩き始めるかまで比べられます。</p>', s)
    s = sub1(r'最終更新: [0-9-]+</span>', f'最終更新: {UPDATED}</span>', s)
    s = sub1(r"title:'[^']*'", f"title:'{SHORT}'", s, count=1)
    open(PAGE, 'w', encoding='utf-8').write(s)

    # 記事を紹介しているほかのページ
    for rel, pat, rep in (
        ('articles/index.html', r'alt="(アイゼン不要で冬に登れる山[57]選|冬でも登れる関東の山7選（雪なし・アイゼン不要）)"', f'alt="{SHORT}"'),
        ('articles/kanto-day-trip-100/index.html', r'(アイゼン不要で冬に登れる山（関東）[57]選|冬でも登れる関東の山7選（雪なし・アイゼン不要）)', SHORT),
        ('articles/train-access-mountains/index.html', r'(アイゼン不要で冬に登れる山（関東）[57]選|冬でも登れる関東の山7選（雪なし・アイゼン不要）)', SHORT),
    ):
        p = os.path.join(ROOT, rel)
        t = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(sub1(pat, rep, t))
    print('ok', names)


if __name__ == '__main__':
    main()
