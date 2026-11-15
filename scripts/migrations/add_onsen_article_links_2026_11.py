"""記事「登山のあとの温泉・サウナ」（/articles/hiking-onsen-sauna/）へのリンクを、記事に載せた山のページの「関連するまとめ」に足す（2026-11-15）
記事に載せる山は data/onsen_sauna.json の plans（id と also）。外れた山のリンクは外す。リンクは「登山タイプ診断」の前。何度流しても同じ結果。
このあと gen_mountain_pages.py --id <山ID>... → check_pages.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import ym_icons  # noqa: E402

DAY = '2026-11-15'
HREF = '/articles/hiking-onsen-sauna/'
MAIN = '登山のあとの温泉・サウナが最高な山12選'
SUB = '下山後に寄れる温泉・サウナの料金・最終受付・行き方'
ICON = ym_icons.svg('waves', size='14', cls='ym-ic', style='vertical-align:-2px;margin-right:3px')


def main():
    path = os.path.join(ROOT, 'data', 'mountains.json')
    M = json.load(open(path, encoding='utf-8'))
    D = json.load(open(os.path.join(ROOT, 'data', 'onsen_sauna.json'), encoding='utf-8'))
    who = {p['id'] for p in D['plans']} | {p['also'] for p in D['plans'] if p.get('also')} | {i for p in D['plans'] for i in p.get('linkAlso', [])}
    pat = re.compile(r'    <a href="%s" class="related-link-item">.*?</a>\n' % re.escape(HREF), re.S)
    changed = []
    for m in M:
        s = m.get('relatedLinksHtml') or ''
        new = pat.sub('', s)
        if m['id'] in who:
            k = new.find('    <a href="/recommend/"')
            if k < 0:
                raise SystemExit('登山タイプ診断のリンクが無い：' + m['id'])
            new = new[:k] + ('    <a href="%s" class="related-link-item">\n      <span class="related-link-main">%s%s</span>\n'
                             '      <span class="related-link-sub">%s</span>\n    </a>\n' % (HREF, ICON, MAIN, SUB)) + new[k:]
        if new != s:
            m['relatedLinksHtml'] = new
            m['mountainUpdated'] = DAY
            changed.append(m['id'])
    json.dump(M, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(' '.join(changed))


if __name__ == '__main__':
    main()
