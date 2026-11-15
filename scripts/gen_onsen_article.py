#!/usr/bin/env python3
"""記事「登山のあとの温泉・サウナ」（/articles/hiking-onsen-sauna/）を作る（2026-11-15。運営者の指示。元の案は運営者が用意した HTML）

- 中身：data/onsen_sauna.json（施設の料金・日帰りの時間・最終受付・設備。公式サイトで確かめた値だけ）と mountains.json（コース・時間・難易度・冬の装備・山の写真）
- 見た目は冬の特集記事（gen_winter_specials.py）と同じ部品（ヘッダー・カード・表・フッター・CSS）を使う
- 施設の写真は外観だけ：Wikimedia Commons（作者・ライセンスを写真の下に出す）、楽天トラベルの宿は楽天トラベルの API（assets/js/onsen-rakuten.js が開いたときに読む）
- 手で編集しない
  python3 scripts/gen_onsen_article.py          書く
  python3 scripts/gen_onsen_article.py --check  書かずに、いまのファイルと同じかを見る
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gen_winter_specials as W  # noqa: E402
import ym_icons  # noqa: E402

SLUG = 'hiking-onsen-sauna'
UPDATED = '2026-11-15'
BANNER = 'hero_onsen_sauna.jpg?v=20261115b'
esc = W.esc


def ic(name):
    return ym_icons.svg(name, style=ym_icons.ICON_STYLE)


CSS_EXTRA = ('<style>'
             '.os-fac{background:#fbfaf6;border:1px solid #ebe6da;border-radius:12px;padding:12px 14px;margin:12px 0}'
             '.os-fac h3{font-size:16px;margin:0 0 2px;color:#2a3e2a}'
             '.os-type{font-size:12px;color:#7a6a4a;font-weight:700;margin:0}'
             '.os-tags{display:flex;flex-wrap:wrap;gap:5px;margin:6px 0 8px}'
             '.os-tags span{background:#eef3e8;color:#3a5a28;font-size:11.5px;font-weight:700;border-radius:12px;padding:2px 9px}'
             '.os-fac .info-row{padding:6px 0}'
             '.os-fac img{display:block;width:100%;aspect-ratio:3/2;object-fit:cover;border-radius:10px;margin:8px 0 2px}'
             '.os-links{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;margin-top:8px}'
             '.os-links a{color:#4a6038;font-weight:700}'
             '.os-move{background:#eef4fb;color:#1a4a70;border-radius:8px;padding:8px 12px;font-size:13.5px;line-height:1.7;margin:10px 0}'
             '.os-rk{margin:8px 0 2px}.os-rk img{aspect-ratio:auto;max-height:260px}'
             '.os-rk-cap{font-size:11px;color:#7a776e;margin:2px 0 6px}'
             '</style>')


def credit(ph):
    return ('<div class="ym-photo-credit" style="font-size:11px;line-height:1.5;color:#7a776e;margin:2px 0 6px;padding:0 2px;word-break:break-word">'
            '写真（外観）：%s（<a href="%s" target="_blank" rel="noopener">%s</a>、<a href="%s" target="_blank" rel="noopener">Wikimedia Commons</a>）</div>' % (
                esc(ph['credit']), esc(ph['licenseUrl']), esc(ph['license']), esc(ph['pageUrl'])))


def facility(f, alt_label):
    photo = ''
    if f.get('photo'):
        ph = f['photo']
        photo = '<img src="%s" alt="%s" loading="lazy">' % (esc(ph['src']), esc(ph['alt'])) + credit(ph)
    elif f.get('rakutenHotelNo'):
        # 楽天トラベルの宿の写真（API の画像。楽天トラベルへのリンクつき。読めなければ何も出さない）
        photo = '<div class="os-rk" data-rk-hotel="%s" data-rk-name="%s" hidden></div>' % (esc(f['rakutenHotelNo']), esc(f['name']))
    rows = ''.join([
        W.row('料金（大人）', esc(f['fee'])),
        W.row('日帰りの時間' if 'ホテル' in f['type'] else '営業時間', esc(f['hours'])),
        W.row('最終受付', esc(f['last'])),
    ])
    return ('<div class="os-fac" id="f-%s"><p class="os-type">%s・%s</p><h3>%s</h3>%s<div class="os-tags">%s</div><p style="margin:0 0 6px">%s</p>%s'
            '<p class="ws-src" style="margin-top:6px">%s %s</p><div class="os-links">%s</div></div>') % (
        esc(f['key']), esc(alt_label), esc(f['type']), esc(f['name']), photo, ''.join('<span>%s</span>' % esc(t) for t in f['tags']), esc(f['text']), rows,
        ic('lightbulb'), esc(f['note']),
        ''.join('<a href="%s" target="_blank" rel="noopener">%s →</a>' % (esc(l['url']), esc(l['label'])) for l in f['links']))


def mountain_photo(m):
    ph = m.get('photos') or []
    if not ph:
        return ''
    return '<img src="%s" class="mountain-photo" alt="%s" loading="lazy">' % (esc(ph[0]), esc(m['name']))


def build():
    D = json.load(open(os.path.join(ROOT, 'data', 'onsen_sauna.json'), encoding='utf-8'))
    M = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
    cards, rows, toc = [], [], []
    for n, p in enumerate(D['plans'], 1):
        m = M[p['id']]
        r = m['routes'][p['route']]
        names = m['name']
        course = [W.row('コース', '%s（%s・難易度 %s）' % (esc(r['name']), esc(r['time']), esc(m.get('difficulty') or '')))]
        if p.get('also'):
            m2 = M[p['also']]
            r2 = m2['routes'][p['alsoRoute']]
            names = '%s・%s' % (m['name'], m2['name'])
            course.append(W.row('もう一つのコース', '<a href="/mountains/%s/" style="color:#4a6038;font-weight:700">%s</a>：%s（%s・難易度 %s）' % (
                m2['id'], esc(m2['name']), esc(r2['name']), esc(r2['time']), esc(m2.get('difficulty') or ''))))
        course.append(W.row('冬の装備', esc(W.winter_gear(m))))
        facs = p['facilities']
        fac_html = ''.join(facility(f, 'おすすめ' if i == 0 else 'もう一つの選択肢') for i, f in enumerate(facs))
        title = '%s × %s' % (names, facs[0]['name'])
        toc.append('<li style="margin:3px 0"><a href="#p-%s" style="color:#4a6038">%d. %s</a></li>' % (m['id'], n, esc(title)))
        cards.append(
            '<div class="mountain-card" id="p-%s">\n  <div class="mountain-card-header" data-mountain-id="%s">\n'
            '    <h2 class="mountain-card-title" style="margin:0;padding:0;border:none;font-size:18px;line-height:1.4">%d. %s</h2>\n'
            '    <div class="mountain-card-sub">%s・標高%sm・%s</div>\n  </div>\n  %s%s\n  <div class="mountain-card-body">\n'
            '    <p style="margin-bottom:10px">%s</p>\n    %s\n'
            '    <div class="os-move">%s <b>下山後の行き方</b>：%s</div>\n    %s\n'
            '    <p style="margin-top:10px"><a href="/mountains/%s/" style="color:#4a6038;font-weight:700">%sの登山ガイド（コース・アクセス・装備）を見る →</a></p>\n  </div>\n</div>' % (
                m['id'], m['id'], n, esc(title), esc(m.get('prefecture') or m.get('area') or ''), '{:,}'.format(int(m['elevation'])), esc(p['mode']),
                mountain_photo(m), W.closed(m), esc(p['why']), ''.join(course), ic('route'), esc(p['move']), fac_html, m['id'], esc(m['name'])))
        tm = esc(r['time']) + (('／' + esc(M[p['also']]['routes'][p['alsoRoute']]['time'])) if p.get('also') else '')
        rows.append(['<a href="#p-%s" style="color:#4a6038;font-weight:700">%s</a>' % (m['id'], esc(names)), tm,
                     '<br>'.join(esc(f['name']) for f in facs), esc(p['moveShort']), '<br>'.join(esc(f['feeShort']) for f in facs)])

    def pick(tag_words):
        out = []
        for p in D['plans']:
            if any(any(w in t for t in f['tags']) for f in p['facilities'] for w in tag_words):
                out.append('<a href="#p-%s" style="color:#4a6038;font-weight:700">%s</a>' % (p['id'], esc(M[p['id']]['name'])))
        return '・'.join(out)
    purpose = [
        ('サウナを楽しむ', pick(['サウナ'])),
        ('駅の近く・下山口のそば', '<a href="#p-kagenobusan" style="color:#4a6038;font-weight:700">景信山・高尾山</a>・<a href="#p-kukiyama" style="color:#4a6038;font-weight:700">九鬼山</a>・<a href="#p-ishirousan" style="color:#4a6038;font-weight:700">石老山</a>・<a href="#p-hinodesaan" style="color:#4a6038;font-weight:700">日の出山</a>・<a href="#p-kamakura_alps" style="color:#4a6038;font-weight:700">鎌倉アルプス</a>'),
        ('景色を眺めて入る', '<a href="#p-bukosan" style="color:#4a6038;font-weight:700">武甲山</a>（露天風呂から武甲山）・<a href="#p-kamakura_alps" style="color:#4a6038;font-weight:700">鎌倉アルプス</a>（海と江の島）・<a href="#p-ishirousan" style="color:#4a6038;font-weight:700">石老山</a>（露天風呂から石老山）・<a href="#p-tenzandake" style="color:#4a6038;font-weight:700">天覧山</a>（宮沢湖）'),
        ('車で行く', '<a href="#p-kirigamine" style="color:#4a6038;font-weight:700">霧ヶ峰・蓼科山</a>・<a href="#p-hinata" style="color:#4a6038;font-weight:700">日向山</a>'),
    ]
    n = len(D['plans'])
    body = '\n'.join([
        '<div class="lead-box">山を歩いて汗をかいたら、温泉につかってサウナで整える。そんな一日のために、Yamatch に載っている山から、下山後に寄れる温泉・サウナがある%d山を選びました。'
        '料金・日帰り入浴の時間・最終受付は、施設の公式サイトで%sに確かめた値です（ホテルは日帰り入浴の時間）。出かける前に、公式サイトで当日の営業を確かめてください。</div>' % (n, '2026年11月15日'),
        '<nav class="tips-card" id="toc" aria-label="目次" style="padding:16px 20px"><div style="font-weight:700;color:#2a3e2a;margin-bottom:6px">目次</div>'
        '<ul style="margin:0;padding:0;list-style:none;font-size:14px;line-height:1.7"><li style="margin:3px 0"><a href="#purpose" style="color:#4a6038">目的で選ぶ</a></li>'
        '<li style="margin:3px 0"><a href="#list" style="color:#4a6038">%d山の一覧（歩く時間・施設・料金）</a></li>%s'
        '<li style="margin:3px 0"><a href="#tips" style="color:#4a6038">登山のあとに温泉・サウナを楽しむために</a></li><li style="margin:3px 0"><a href="#faq" style="color:#4a6038">よくある質問</a></li></ul></nav>' % (n, ''.join(toc)),
        '<h2 id="purpose">目的で選ぶ</h2>',
        '<div class="tips-card" style="padding:14px 18px;line-height:1.9"><ul style="margin:0 0 0 18px">%s</ul></div>' % ''.join(
            '<li><b>%s</b>：%s</li>' % (esc(a), b) for a, b in purpose),
        '<h2 id="list">%d山の一覧（歩く時間・施設・料金）</h2>' % n,
        W.table(['山', '歩く時間', '温泉・サウナ', '下山後の行き方', '料金（大人）'], rows),
        '<p style="font-size:12.5px;color:#666;margin:4px 0 16px">歩く時間は Yamatch に載せている代表コースの値（休憩を含まない）。料金は大人1人・日帰りの通常の料金で、タオル・館内着・岩盤浴などは別料金のことがあります。</p>',
        '\n'.join(cards),
        '<h2 id="tips">登山のあとに温泉・サウナを楽しむために</h2>',
        '<div class="tips-card" style="padding:16px 20px"><ul style="margin:0 0 0 18px;line-height:1.9">'
        '<li><b>最終受付から逆算する</b>：ホテルの日帰り入浴は受付が夕方に終わることがあります。歩き始めの時間を早めにしましょう</li>'
        '<li><b>帰りの電車・バスを先に調べる</b>：下山口や温泉からのバスは本数が少ないことがあります</li>'
        '<li><b>水分をとってから入る</b>：登山のあとは汗で水分が足りなくなりがちです。体調がすぐれないときは、サウナを控えましょう</li>'
        '<li><b>着替えと袋を持っていく</b>：下山後の着替え、タオル、濡れた服を入れる袋。持ち物は<a href="/packing/" style="color:#4a6038;font-weight:700">持ち物チェックリスト</a>で確かめられます</li>'
        '<li><b>冬は早めに下りる</b>：日の入りが早く、標高の高い山は雪や凍結があります。山ごとの「冬の装備」を見てください</li></ul></div>',
        '<h2>あわせて読みたい</h2>',
        '<div class="tips-card" style="padding:16px 20px"><ul style="margin:0 0 0 18px;line-height:1.9">'
        '<li><a href="/search/train-daytrip/" style="color:#4a6038;font-weight:700">電車で行ける日帰り登山20選</a></li>'
        '<li><a href="/articles/mountain-gourmet/" style="color:#4a6038;font-weight:700">山の茶屋・山小屋グルメ</a></li>'
        '<li><a href="/articles/winter-no-crampons/" style="color:#4a6038;font-weight:700">冬でも登れる関東の山7選｜雪なし・アイゼン不要</a></li></ul></div>',
        '<p style="font-size:12.5px;color:#777;margin-top:14px">※料金・営業時間・休館日・日帰り入浴の条件は、施設の都合で変わります。利用する日の情報は公式サイトで確かめてください（%s 確認）。</p>' % '2026年11月15日',
    ])
    P = {p['id']: p for p in D['plans']}
    F = {f['key']: f for p in D['plans'] for f in p['facilities']}
    faq = [
        ('下山後に温泉に入れる、関東から日帰りの山は？',
         'この記事では%d山を紹介しています。電車で行くなら、コースの終わりがつるつる温泉の日の出山、下山口のそばにさがみ湖温泉 うるりがある石老山、高尾山口駅のそばに極楽湯やサウナがある景信山・高尾山が行きやすい山です。' % n),
        ('サウナがある、登山のあとに寄れる施設は？',
         'TAKAO 36 SAUNA（高尾山口駅から徒歩2分）、京王高尾山温泉 極楽湯、より道の湯（都留市駅から徒歩1分）、山賊サウナ（入生田駅）、箱根湯寮、さがみ湖温泉 うるり、つるつる温泉、西武秩父駅前温泉 祭の湯、稲村ヶ崎温泉、べるが 尾白の湯などにサウナがあります。'),
        ('高尾山のあとに行ける温泉・サウナは？',
         '高尾山口駅のとなりの京王高尾山温泉 極楽湯（%s、最終受付%s）と、駅から徒歩2分の TAKAO 36 SAUNA（%s、最終受付%s）があります。' % (
             F['gokurakuyu']['feeShort'], F['gokurakuyu']['last'], F['takao36']['feeShort'], F['takao36']['last'])),
        ('ホテルの日帰り入浴は何時まで入れますか？',
         'ホテルマウント富士は、満天星の湯の受付が14:00〜18:00、はなれの湯が12:00〜16:00（水曜は14:00〜16:00）で、土日・繁忙期は15:00で受付を終える場合があります。池の平ホテルの湖天の湯は11:30〜23:00（最終受付22:00）です。'),
        ('武甲山の帰りに寄れる温泉は？',
         '西武秩父駅前温泉 祭の湯です。露天風呂から武甲山が見え、サウナと水風呂もあります（%s、最終受付%s）。登山口の一ノ鳥居へのバスは無いので、行き帰りはタクシーか車です。' % (F['matsurinoyu']['feeShort'], F['matsurinoyu']['last'])),
        ('日の出山のつるつる温泉への行き方と帰り方は？',
         '御岳山駅から日の出山を通ってつるつる温泉へ下りるコース（%s）です。帰りは西東京バスで武蔵五日市駅へ（約20分）。最終受付は%sです。' % (M['hinodesaan']['routes'][1]['time'], F['tsurutsuru']['last'])),
    ]
    W.UPDATED = UPDATED
    page = W.page(SLUG, '登山のあとの温泉・サウナが最高な山%d選【関東発・日帰り】料金・最終受付・下山後の行き方' % n,
                  '下山後に温泉やサウナに寄れる関東発の日帰り登山%d山。歩く時間、温泉・サウナの料金と最終受付（ホテルは日帰り入浴の時間）、下山口からの行き方を公式サイトで確かめて紹介します。' % n,
                  '登山のあとの温泉・サウナが<br>最高な山%d選' % n, '温泉・サウナ', ['関東発', '日帰り'], body, faq, '登山のあとの温泉・サウナ', BANNER)
    page = page.replace('</head>', CSS_EXTRA + '\n</head>', 1)
    page = page.replace('<script src="/assets/js/card-photo-credits.js?v=20261105b" defer></script>',
                        '<script src="/assets/js/card-photo-credits.js?v=20261105b" defer></script>\n<script src="/assets/js/onsen-rakuten.js?v=20261115" defer></script>', 1)
    page = ym_icons.emoji_to_icons(page)
    return page


def main():
    s = build()
    p = os.path.join(ROOT, 'articles', SLUG, 'index.html')
    old = open(p, encoding='utf-8').read() if os.path.exists(p) else None
    if '--check' in sys.argv:
        print('同じ' if old == s else '違う')
        sys.exit(0 if old == s else 1)
    if s.count('<div') != s.count('</div>') or not s.rstrip().endswith('</html>'):
        raise SystemExit('ページの形が壊れている')
    if old != s:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(s)
        print('書きました', os.path.relpath(p, ROOT))
    else:
        print('変わらない')


if __name__ == '__main__':
    main()
