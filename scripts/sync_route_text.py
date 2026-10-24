#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""コース（routes）を直した山の文章を、新しいコースのデータに合わせる（2026-10-24〜）。

  python3 scripts/sync_route_text.py <山ID> [<山ID> ...]

- コース定数の幅（coeffMin / coeffMax / courseCoefficientRange）をルートの定数から作り直し、文章中の「コース定数◯〜◯」を合わせる
  （新しい形式の山は coeffFromRoutes を付けて build_derived.py に任せる）
- 紹介文（introHtml）の「代表コース（…）は所要…」を代表ルートの値にする（旧い形式の山。新しい形式は build_derived.py が行う）
- よくある質問の「日帰りできますか／所要時間」の答えを、ルートの値から作り直す。答えの最後の「新宿から登山口までは…」の文は残す
- 人が書いた文（難易度の理由など）に残る古い時間は自動では直さない。直したあとに check で一覧を出す
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'data', 'mountains.json')


def mins(t):
    m = re.fullmatch(r'\s*(?:(\d+)時間)?(?:(\d+)分)?\s*', t or '')
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0) if m and (m.group(1) or m.group(2)) else None


def rep_route(m):
    rs = m.get('routes') or []
    for r in rs:
        if m.get('representativeRouteId') and r.get('id') == m['representativeRouteId']:
            return r
    for r in rs:
        if (r.get('status') or {}).get('state') != 'closed':
            return r
    return rs[0] if rs else None


def dayok(r):
    t = mins(r.get('time'))
    return t is not None and t <= 510 and '泊' not in (r.get('name') or '') and (r.get('status') or {}).get('state') != 'closed'


def elev_txt(r):
    return (r.get('elevation') or '').replace('+', '')


def fix_coeff(m, new):
    pat = re.compile(r'((?:コース)?定数\s*)\d+(?:〜\d+)?')
    def fix(v):
        if isinstance(v, str): return pat.sub(lambda x: x.group(1) + new, v)
        if isinstance(v, list): return [fix(x) for x in v]
        if isinstance(v, dict): return {k: fix(x) for k, x in v.items()}
        return v
    for k in ('introHtml', 'faq', 'description', 'dlNoteHtml'):
        if m.get(k): m[k] = fix(m[k])


def day_answer(m, old):
    name = m['name']
    tail = ''
    mt = re.search(r'(新宿から登山口までは[^。]*。.*)$', old or '')
    if mt: tail = mt.group(1)
    rs = [r for r in (m.get('routes') or []) if r.get('time')]
    if m.get('daytrip'):
        ds = sorted([r for r in rs if dayok(r)], key=lambda r: mins(r['time']))
        parts = ['はい、%sは日帰りできます。' % name]
        for i, r in enumerate(ds):
            parts.append('%s%sは%s（%s・標高差%s）。' % ('いちばん短い' if i == 0 and len(ds) > 1 else '', r['name'], r['time'], r.get('distance'), elev_txt(r)))
        if ds and mins(ds[0]['time']) >= 480:
            parts.append('歩く時間が長いので、早朝に出発できる計画にしてください。')
        longs = [r for r in rs if r not in ds and (r.get('status') or {}).get('state') != 'closed']
        if longs:
            parts.append('%sは山小屋に泊まる計画が基本です。' % '・'.join(r['name'] for r in longs))
    else:
        rep = rep_route(m)
        parts = ['%sは山小屋泊が基本です。' % name]
        for r in sorted([r for r in rs if (r.get('status') or {}).get('state') != 'closed'], key=lambda r: mins(r['time']) or 0):
            parts.append('%sは歩行%s（%s・標高差%s）。' % (r['name'], r['time'], r.get('distance'), elev_txt(r)))
    return ''.join(parts) + tail


def sync(m):
    rep = rep_route(m)
    cs = [r['coeff'] for r in (m.get('routes') or []) if r.get('coeff') is not None]
    if m.get('dataModel') == 'ssot-v1':
        m['coeffFromRoutes'] = True
    elif cs:
        lo, hi = min(cs), max(cs)
        new = str(lo) if lo == hi else '%d〜%d' % (lo, hi)
        m['coeffMin'], m['coeffMax'], m['courseCoefficientRange'] = lo, hi, new
        if 'courseCoefficient' in m: m['courseCoefficient'] = [lo, hi]
        fix_coeff(m, new)
        if rep and m.get('introHtml'):
            m['introHtml'] = re.sub(r'代表コース（[^）]*(?:（[^）]*）)?[^）]*）は所要[^。]*。',
                                    '代表コース（' + rep['name'] + '）は所要' + rep['time'] + '/' + (rep.get('distance') or '') + '/標高差' + (rep.get('elevation') or '') + '。',
                                    m['introHtml'])
        if rep and m.get('dlNoteHtml'):
            m['dlNoteHtml'] = re.sub(r'代表コースの[^。]*?は[^。]*?標高差[^。]*。',
                                     '代表コースの' + rep['name'] + 'は' + rep['time'] + '・' + (rep.get('distance') or '') + '・標高差' + (rep.get('elevation') or '') + '。',
                                     m['dlNoteHtml'])
    # 紹介文の「日帰りでの登山が可能／山小屋泊が一般的」を日帰りの区分に合わせる
    if m.get('introHtml'):
        m['introHtml'] = m['introHtml'].replace('日帰りでの登山が可能', '@@DAY@@').replace('山小屋泊が一般的', '@@DAY@@') \
            .replace('@@DAY@@', '日帰りでの登山が可能' if m.get('daytrip') else '山小屋泊が一般的')
    # よくある質問の「代表的な◯◯は◯時間・◯km・標高差◯が目安。◯◯（◯時間）という選び方もできます。」を作り直す
    others = [r for r in (m.get('routes') or []) if r is not rep and (r.get('status') or {}).get('state') != 'closed']
    def tmpl(_):
        t = '代表的な%sは%s・%s・標高差%sが目安。' % (rep['name'], rep['time'], rep.get('distance'), rep.get('elevation'))
        if others:
            t += '%sという選び方もできます。' % '、'.join('%s（%s）' % (r['name'], r['time']) for r in others)
        return t
    for q in m.get('faq') or []:
        if rep and '代表的な' in q.get('answer', ''):
            q['answer'] = re.sub(r'代表的な[^。]*?は[^。]*?が目安。(?:[^。]*?という選び方もできます。)?', tmpl, q['answer'])
    for q in m.get('faq') or []:
        if '日帰り' in q.get('question', ''):
            q['answer'] = day_answer(m, q.get('answer'))


if __name__ == '__main__':
    ids = sys.argv[1:]
    D = json.load(open(PATH, encoding='utf-8'))
    n = 0
    for m in D:
        if m['id'] in ids:
            sync(m); n += 1
    json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('文章を合わせた山: %d' % n)
