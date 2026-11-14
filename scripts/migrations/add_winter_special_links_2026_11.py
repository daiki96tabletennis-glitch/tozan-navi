"""冬の特集記事3本へのリンクを、関係する山のページの「関連するまとめ」に足す（2026-11-12。運営者の指示「冬でも検索から来てもらえる人を増やす」）

- 初日の出登山（/articles/hatsuhinode-hiking/）：記事に載せた7山
- ダイヤモンド富士（/articles/diamond-fuji/）：記事に載せた山（gen_winter_specials.py の diamond_list と同じ）
- 冬にしか見られない絶景（/articles/winter-views/）：記事に載せた6山
リンクは「登山タイプ診断」（/recommend/。いつも最後）の前に入れる。足した山は mountainUpdated を今日にする。
何度流しても同じ結果。記事に載せる山を変えたら流し直す（記事から外れた山のリンクは外す）。
このあと gen_mountain_pages.py --all → check_pages.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gen_winter_specials as G  # noqa: E402

DAY = '2026-11-14'
ICON = ('<svg width="14" height="14" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/>'
        '<path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>')
ARTICLES = [
    ('/articles/hatsuhinode-hiking/', '初日の出登山 関東｜山頂の日の出の時刻', '元日の始発で間に合うか・初詣ができる神社つき'),
    ('/articles/diamond-fuji/', 'ダイヤモンド富士が見える場所・山と時間', '2026-2027年のカレンダー。山頂から見られる日付と時刻を計算'),
    ('/articles/winter-views/', '冬の絶景が見られる山（樹氷・霧氷・雪山）', '関東近郊。雪山初心者向けのロープウェイの山・日帰りのコース・冬の装備'),
]


def item(href, main, sub):
    return ('    <a href="%s" class="related-link-item">\n      <span class="related-link-main">%s%s</span>\n'
            '      <span class="related-link-sub">%s</span>\n    </a>\n' % (href, ICON, main, sub))


def main():
    path = os.path.join(ROOT, 'data', 'mountains.json')
    M = json.load(open(path, encoding='utf-8'))
    by = {m['id']: m for m in M}
    SC = json.load(open(os.path.join(ROOT, 'data', 'summit_coords.json'), encoding='utf-8'))['mountains']
    W = json.load(open(os.path.join(ROOT, 'data', 'winter_specials.json'), encoding='utf-8'))
    who = {
        # 初日の出は公開するまで（publish が false のあいだ）リンクしない
        '/articles/hatsuhinode-hiking/': {it['id'] for it in W['hatsuhinode']['mountains']} if W['hatsuhinode'].get('publish', True) else set(),
        '/articles/diamond-fuji/': {x['m']['id'] for x in G.diamond_list(by, SC, W)},
        '/articles/winter-views/': {it['id'] for it in W['views']['mountains']},
    }
    changed = []
    for m in M:
        s = m.get('relatedLinksHtml') or ''
        new = s
        for href, main_, sub in ARTICLES:
            pat = re.compile(r'    <a href="%s" class="related-link-item">.*?</a>\n' % re.escape(href), re.S)
            new = pat.sub('', new)
            if m['id'] in who[href]:
                k = new.find('    <a href="/recommend/"')
                if k < 0:
                    raise SystemExit('登山タイプ診断のリンクが無い：' + m['id'])
                new = new[:k] + item(href, main_, sub) + new[k:]
        if new != s:
            m['relatedLinksHtml'] = new
            m['mountainUpdated'] = DAY
            changed.append(m['name'])
    json.dump(M, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('足した山 %d：%s' % (len(changed), '・'.join(changed)))


if __name__ == '__main__':
    main()
