"""まとめ記事「サウナシュラン受賞サウナに寄れる山」（/articles/saunachelin-hiking/）へのリンクを、記事に載せた山のページの「関連するまとめ」に足す（2026-11-16）
山は data/saunachelin_hiking.json の saunas[].mountains。外れた山のリンクは外す。リンクは「登山タイプ診断」の前。何度流しても同じ結果。
このあと gen_mountain_pages.py --id <山ID>... → check_pages.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import ym_icons  # noqa: E402

DAY = '2026-11-16'
HREF = '/articles/saunachelin-hiking/'
SUB = '登山口から車で30分ほど・日帰りで使えるサウナを地図で'
ICON = ym_icons.svg('flame', size='14', cls='ym-ic', style='vertical-align:-2px;margin-right:3px')


def main():
    path = os.path.join(ROOT, 'data', 'mountains.json')
    M = json.load(open(path, encoding='utf-8'))
    D = json.load(open(os.path.join(ROOT, 'data', 'saunachelin_hiking.json'), encoding='utf-8'))
    near = {}
    for s in D['saunas']:
        for x in s['mountains']:
            near.setdefault(x['id'], s['name'])
    pat = re.compile(r'    <a href="%s" class="related-link-item">.*?</a>\n' % re.escape(HREF), re.S)
    changed = []
    for m in M:
        s = m.get('relatedLinksHtml') or ''
        new = pat.sub('', s)
        if m['id'] in near:
            k = new.find('    <a href="/recommend/"')
            if k < 0:
                raise SystemExit('登山タイプ診断のリンクが無い：' + m['id'])
            main_ = 'サウナシュラン受賞サウナに寄れる山（%s）' % near[m['id']]
            new = new[:k] + ('    <a href="%s" class="related-link-item">\n      <span class="related-link-main">%s%s</span>\n'
                             '      <span class="related-link-sub">%s</span>\n    </a>\n' % (HREF, ICON, main_, SUB)) + new[k:]
        if new != s:
            m['relatedLinksHtml'] = new
            m['mountainUpdated'] = DAY
            changed.append(m['id'])
    json.dump(M, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(' '.join(changed))


if __name__ == '__main__':
    main()
