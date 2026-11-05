"""記事「アイゼン不要で冬に登れる山（関東）」を5選→7選にし、値をいまのデータに合わせる（2026-11-05。運営者の指示）

- 足す山：筑波山・明神ヶ岳（どちらも装備カレンダーが12か月「アイゼン不要」）
- 各カードの車・電車の時間（新宿から）、コース定数の幅、冬のバッジ、装備カードを mountains.json・gear-data.json から作り直す
  （前は10月のコース見直しの前の値のままだった。例：高尾山の定数「8〜51」）
- 冬のバッジは gearCalendar で決める：12か月すべて no_crampons なら「❄️ 通年アイゼン不要」、12〜2月だけなら「❄️ 12〜2月アイゼン不要」
- 特徴・おすすめ理由の文は、前からの5山は前の文のまま、足す2山は山の特徴（featurePoints）に書いてあることだけで書く
- 写真はページのスクリプトが mountains.json の photos から入れる。前のカードにあった記事の写真（images/photo-0X.jpg）はそのまま残す
- 弘法山の閉鎖の注意（data-closed）は前のカードから引き継ぐ
何度流しても同じ結果になる（前のカードの文を読み直して作るため、2回目は同じ文が出る）。
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

CAR_SVG = ('<svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><path d="M4 13l1.5-4A2 2 0 0 1 7.3 8h9.4a2 2 0 0 1 1.8 1.2L20 13z" fill="currentColor"/><rect x="2.5" y="13" width="19" height="4.5" rx="2" fill="currentColor"/><rect x="6.5" y="9.2" width="4" height="2.8" rx="0.5" fill="white"/><rect x="11.5" y="9.2" width="6" height="2.8" rx="0.5" fill="white"/><circle cx="6.5" cy="17.5" r="1.6" fill="#3a3530"/><circle cx="17.5" cy="17.5" r="1.6" fill="#3a3530"/></svg>')
TRAIN_SVG = ('<svg width="12" height="12" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><path d="M2 7 H14 L20 11.5 V17 H2 Z" fill="currentColor"/><rect x="4" y="9.5" width="3" height="3" fill="white"/><rect x="9" y="9.5" width="3" height="3" fill="white"/><line x1="1" y1="19.5" x2="21" y2="19.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>')
THUMB_SVG = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:3px;display:inline-block"><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/><path d="M7 10v12"/></svg>')


def mins(n):
    n = int(n)
    if n < 60:
        return f'約{n}分'
    h, m = divmod(n, 60)
    return f'約{h}時間' + (f'{m}分' if m else '')


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
    """前のカードから、特徴・おすすめ理由・閉鎖の注意を山ごとに読む"""
    out = {}
    for cm in re.finditer(r'<div class="mountain-card">([\s\S]*?)(?=<div class="mountain-card">|<h2)', s):
        c = cm.group(1)
        mid = re.search(r'data-mountain-id="([^"]+)"', c).group(1)
        feat = re.search(r'<span class="info-label">特徴</span><span class="info-val">([\s\S]*?)</span></div>', c)
        why = re.search(r'<strong>おすすめ理由：</strong>([\s\S]*?)</div>', c)
        closed = re.search(r'(<div class="mc-closed"[\s\S]*?</div>)', c)
        img = re.search(r'(<img src="[^"]*" class="mountain-photo"[^>]*>)', c)
        out[mid] = (html.unescape(feat.group(1)) if feat else None, html.unescape(why.group(1)) if why else None,
                    closed.group(1) if closed else '', img.group(1) if img else '')
    return out


def card(i, m, feat, why, closed, img, gear):
    mid = m['id']
    rng = f'{m["coeffMin"]}〜{m["coeffMax"]}' if m.get('coeffMin') != m.get('coeffMax') else str(m['coeffMin'])
    e = html.escape
    return (
        '<div class="mountain-card">\n'
        f'  <div class="mountain-card-header" data-mountain-id="{mid}">\n'
        f'    <div class="mountain-card-title">{NUM[i]} {e(m["name"])}</div>\n'
        f'    <div class="mountain-card-sub">{e(short_area(m["area"]))}・標高{m["elevation"]:,}m</div>\n'
        '  </div>\n'
        + (f'  {img}\n' if img else '')
        + (f'  {closed}\n' if closed else '') +
        '  <div class="mountain-card-body">\n'
        f'    <div class="info-row"><span class="info-label">{CAR_SVG} 車</span><span class="info-val">新宿から{mins(m["driveTimeShinjuku"])}</span></div>\n'
        f'    <div class="info-row"><span class="info-label">{TRAIN_SVG} 電車</span><span class="info-val">新宿から{train_label(m)}{mins(m["trainTimeShinjuku"])}</span></div>\n'
        f'    <div class="info-row"><span class="info-label">コース定数</span><span class="info-val"><span class="coeff-badge">{rng}</span><span class="winter-badge">{winter_badge(m["gearCalendar"])}</span></span></div>\n'
        f'    <div class="info-row"><span class="info-label">特徴</span><span class="info-val">{e(feat)}</span></div>\n'
        f'    <div class="reason-box">{THUMB_SVG} <strong>おすすめ理由：</strong>{e(why)}</div>\n'
        f'    <a href="/mountains/{mid}/" class="detail-link">{e(m["name"])}の詳細情報を見る →</a>'
        f'<div class="gear-section-label"><img src="/images/icons/backpack.webp" width="18" height="18" alt="" style="vertical-align:-4px;margin-right:2px"> {e(m["name"])}の装備</div>'
        f'<div class="gear-cards-scroll" data-gear-mid="{mid}" data-gear-variants="{variants_attr(gear[mid])}"></div>\n'
        '  </div>\n'
        '</div>'
    )


def sub1(pat, rep, s):
    t, n = re.subn(pat, rep, s)
    if n < 1:
        raise SystemExit('見つからない: ' + pat)
    return t


def main():
    ms = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data/mountains.json')))}
    gear = json.load(open(os.path.join(ROOT, 'data/gear-data.json')))
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
        cards.append(card(i, ms[mid], f, w, c, im, gear))
    body = '<h2>おすすめ7山</h2>' + ''.join(cards) + '\n'
    s = sub1(r'<h2>おすすめ[57]山</h2>[\s\S]*?(?=<h2)', body.replace('\\', '\\\\'), s)
    desc = f'厳冬期でもアイゼンなしで楽しめる関東の山7選。{names}を、冬の装備の区分・アクセス・見どころ付きで紹介。'
    s = sub1(r'<title>アイゼン不要で冬に登れる山（関東）[57]選 \| Yamatch</title>', '<title>アイゼン不要で冬に登れる山（関東）7選 | Yamatch</title>', s)
    s = sub1(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}冬こそ低山登山のベストシーズンです。">', s)
    s = sub1(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="アイゼン不要で冬に登れる山（関東）7選 | Yamatch">', s)
    s = sub1(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{desc}">', s)
    s = sub1(r'"headline":"アイゼン不要で冬に登れる山（関東）[57]選","description":"[^"]*"', f'"headline":"アイゼン不要で冬に登れる山（関東）7選","description":"{desc}"', s)
    s = sub1(r'"dateModified":"[0-9-]+"', f'"dateModified":"{UPDATED}"', s)
    s = sub1(r'"name":"アイゼン不要で冬に登れる山[57]選"', '"name":"アイゼン不要で冬に登れる山7選"', s)
    s = sub1(r'"text":"高尾山・鋸山・弘法山・御岳山・陣馬山(・筑波山・明神ヶ岳)?など[^"]*"',
             f'"text":"{names}など、関東の標高1,200m以下の山は太平洋側の気候の影響で積雪が少なく、Yamatchの装備の区分では冬も「アイゼン不要」です。ただし雪が降ったあとの数日は凍結が残ることがあるので、出発前に直近の降雪を確認してください。"', s)
    s = sub1(r'\{"@type":"Question","name":"(❄️通年アイゼン不要と積雪少\(要確認\)の違いは何ですか？|「❄️ 通年アイゼン不要」は何を基準にしていますか？)","acceptedAnswer":\{"@type":"Answer","text":"[^"]*"\}\}',
             '{"@type":"Question","name":"「❄️ 通年アイゼン不要」は何を基準にしていますか？","acceptedAnswer":{"@type":"Answer","text":"Yamatchの装備カレンダーで、12か月すべてが「アイゼン不要」の区分になっている山です。雪が降ったあとの数日だけ滑り止めが要る日は例外として扱っているので、念のためチェーンスパイクを持っていくと安心です。"}}', s)
    s = sub1(r'（関東）[57]選</h1>', '（関東）7選</h1>', s)
    s = sub1(r'楽しめる[57]山を厳選しました。', '楽しめる7山を厳選しました。', s)
    s = sub1(r'最終更新: [0-9-]+</span>', f'最終更新: {UPDATED}</span>', s)
    s = sub1(r"title:'アイゼン不要で冬に登れる山（関東）[57]選'", "title:'アイゼン不要で冬に登れる山（関東）7選'", s)
    open(PAGE, 'w', encoding='utf-8').write(s)

    # 記事を紹介しているほかのページ
    for rel, pat, rep in (
        ('articles/index.html', r'alt="アイゼン不要で冬に登れる山[57]選"', 'alt="アイゼン不要で冬に登れる山7選"'),
        ('articles/kanto-day-trip-100/index.html', r'アイゼン不要で冬に登れる山（関東）[57]選', 'アイゼン不要で冬に登れる山（関東）7選'),
        ('articles/train-access-mountains/index.html', r'アイゼン不要で冬に登れる山（関東）[57]選', 'アイゼン不要で冬に登れる山（関東）7選'),
    ):
        p = os.path.join(ROOT, rel)
        t = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(sub1(pat, rep, t))
    print('ok', names)


if __name__ == '__main__':
    main()
