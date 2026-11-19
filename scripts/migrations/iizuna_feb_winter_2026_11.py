# -*- coding: utf-8 -*-
"""飯縄山の2月を冬山装備にする（2026-11-19。運営者の指示「2月を冬山装備に」）

根拠：ヤマレコの記録（一ノ鳥居からの冬道。2021年12月〜2026年3月）で、2月は前爪のあるアイゼン・ピッケルを使った・勧める記録が3年ある
（2022-02 駒つなぎの場からアイゼンを付けピッケル、2025-02「急登が多くチェーンスパイクでは滑ってきつい。10本以上のアイゼン」、
2026-02「ほかの登山者は前爪ありアイゼンの人が多かった」）。1月・3月は年が足りないので軽アイゼン等のまま（アイゼンのカードの文で補う）。
やること（何度流しても同じ結果）：gearCalendar の2月・季節の4項目・装備カード（2月＝冬靴・12本爪アイゼン・ピッケル（条件次第）、
1月＝来月分のアイゼン）・よくある質問（シーズン）・手で作った記事とまとめの装備カードの写し。
fix_gear_calendar_hut_reports_2026_11.py の CRAMPON_TEXT から（飯縄山, 2月）を外し、FAQ の新しい文をこのスクリプトと同じにした。
このあと gen_mountain_pages.py --id iizunasan → build_packing_mountains.py → gen_recommend_gear.py → build_winter_find.py → gen_find_winter.py → check_pages.py
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'migrations'))
import add_gear_new_mountains_2026_11 as A  # noqa: E402
from fix_split_month_gear_2026_11 import variants_attr  # noqa: E402

DAY = '2026-11-19'
MID = 'iizunasan'
MP = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
FAQ_OLD = ('飯縄山の雪の無いシーズンは5月〜10月が目安です。11月〜4月は積雪・凍結があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が要ります。'
           '12月〜3月の冬道は駒つなぎの場から急な斜面を登るので、10本爪以上のアイゼンが安心という登山記録が多くあります。'
           '実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。')
FAQ_NEW = ('飯縄山の雪の無いシーズンは5月〜10月が目安です。11月〜1月と3月〜4月は積雪・凍結があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が要ります。'
           '2月は12本爪アイゼン・ピッケル等の冬山装備が要る時期です。'
           '12月〜3月の冬道は駒つなぎの場から急な斜面を登るので、10本爪以上のアイゼンが安心という登山記録が多くあります。'
           '実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。')
CRAMPON = dict(A.WINTER, r='冬道は駒つなぎの場から急な斜面を登ります。2月は雪が締まって滑りやすく、前爪のある10本爪以上のアイゼンを使った・勧める登山記録が多い時期です。'
                         '事前に最新の積雪・凍結情報を確認してください。')
AXE = dict(A.AXE, i='条件次第', r='駒つなぎの場から上の急な斜面で、ピッケルを使った登山記録があります。雪が硬く締まった日や、急な所に不安がある人は持っていきましょう。'
                                 '使い方に慣れていない場合は経験者と一緒に。事前に最新の積雪・凍結情報を確認してください。')
LEG = {'s-ok': 'アイゼン不要', 's-gear': '軽アイゼン等', 's-hard': '冬山装備', 's-closed': '入山不可'}


def circ(ms):
    ms = sorted(set(ms))
    if not ms:
        return '不可'
    if len(ms) == 12:
        return '通年'
    runs, cur = [], [ms[0]]
    for x in ms[1:]:
        if x == cur[-1] + 1:
            cur.append(x)
        else:
            runs.append(cur)
            cur = [x]
    runs.append(cur)
    if len(runs) > 1 and runs[0][0] == 1 and runs[-1][-1] == 12:
        runs[0] = runs.pop() + runs[0]
    runs.sort(key=lambda r: r[0] if r[0] != 12 or len(r) == 1 else 0)
    return '・'.join('%d月〜%d月' % (r[0], r[-1]) if len(r) > 1 else '%d月' % r[0] for r in runs)


def main():
    raw = open(MP, encoding='utf-8').read()
    M = json.loads(raw)
    m = next(x for x in M if x['id'] == MID)
    cal, sc = m['gearCalendar'], m['seasonCalendar']
    assert cal[1] in ('light_crampons', 'winter_gear'), cal[1]
    changed = cal[1] != 'winter_gear'
    cal[1] = 'winter_gear'
    sc[1] = 's-hard'
    m['calLegend'] = [LEG[c] for c in ('s-ok', 's-gear', 's-hard', 's-closed') if c in sc]
    m['seasonNoGear'] = circ([i + 1 for i in range(12) if sc[i] == 's-ok'])
    m['season6Crampons'] = circ([i + 1 for i in range(12) if sc[i] == 's-gear'])
    qs = [f for f in m['faq'] if 'シーズン' in f['question']]
    assert len(qs) == 1
    if qs[0]['answer'] != FAQ_NEW:
        assert qs[0]['answer'] == FAQ_OLD, qs[0]['answer']
        qs[0]['answer'] = FAQ_NEW
        changed = True
    if changed:
        m['mountainUpdated'] = max(m.get('mountainUpdated') or '', DAY)
    open(MP, 'w', encoding='utf-8').write(json.dumps(M, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))

    G = json.load(open(GP, encoding='utf-8'))
    feb = G[MID]['2']
    out = []
    for c in feb:
        if c['c'] == 'shoe':
            out.append(dict(A.W_SHOE2))
        elif c['c'] == 'crampon':
            out.append(dict(CRAMPON))
        elif c['c'] in ('axe', 'crampon_next'):
            continue
        else:
            out.append(c)
    idx = max(i for i, c in enumerate(out) if c['c'] == 'crampon') + 1
    out.insert(idx, dict(AXE))
    G[MID]['2'] = out
    jan = [c for c in G[MID]['1'] if c['c'] != 'crampon_next']
    idx = max(i for i, c in enumerate(jan) if c['c'] in ('shoe', 'rain', 'crampon')) + 1
    jan.insert(idx, dict(A.WINTER_NEXT))
    G[MID]['1'] = jan
    with open(GP, 'w', encoding='utf-8') as f:
        json.dump(G, f, ensure_ascii=False, indent=2)
        f.write('\n')

    import re
    pat = re.compile(r'(data-gear-mid="' + MID + r'"[^>]*?data-gear-variants=")([^"]*)(")')
    for p in sorted(glob.glob(os.path.join(ROOT, 'articles/*/index.html')) + glob.glob(os.path.join(ROOT, 'search/*/index.html'))):
        s = open(p, encoding='utf-8').read()
        if '<!-- generated: scripts/gen_line_articles' in s:
            continue
        new = pat.sub(lambda x: x.group(1) + variants_attr(G[MID]) + x.group(3), s)
        if new != s:
            open(p, 'w', encoding='utf-8').write(new)
            print('記事の写し', os.path.relpath(p, ROOT))
    print('ok', cal, m['seasonNoGear'], m['season6Crampons'])


if __name__ == '__main__':
    main()
