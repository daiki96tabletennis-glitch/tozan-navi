"""冬の装備の区分と、登山口への道路の冬期閉鎖を直す（2026-11-12。運営者の指示「毛無山・御座山・経ヶ岳・恵那山の冬山装備の区分が厳しすぎる点と、
白砂山・荒沢岳・越後駒ヶ岳の冬山装備の月が道路閉鎖で登山口へ行けない点を、さらに調査して修正して」）

1. 冬山装備 → 軽アイゼン等（登山記録。2021年11月以降・1山に複数。一覧は .claude/axe_records_2026_11.md）
   - 毛無山 12〜2月：チェーンスパイク・チェーンアイゼンで歩いた記録が続く（2022-12-30・2023-01-07・2023-01-14・2022-02-26）
   - 御座山 12〜3月：ノーアイゼン・軽アイゼン・チェーンスパイクの記録が続く（2022-01-10・2022-02-26・2024-01-23・2023-02-22）。3月の記録は無いが、1・2月と同じとした
   - 恵那山・経ヶ岳は冬山装備のまま（恵那山は12本爪を使った記録が多い。経ヶ岳は深い雪でワカン・スノーシューが要る）
   gearCalendar・季節の4項目（seasonCalendar・calLegend・seasonNoGear・season6Crampons）・装備カード（登山靴・アイゼン・来月分）をそろえる。
   装備カードは、同じ山の11月（軽アイゼン等の月）の登山靴・アイゼンのカードを使う。
2. 登山口への道路の冬期閉鎖（annualItems の kind "closure"。日向山の林道の冬期閉鎖と同じ書き方。装備カレンダーは変えない＝登山道の閉鎖ではないため）
   - 白砂山：国道405号（中之条町入山 和光原〜野反湖）2026-11-25 15時〜2027-04-21 10時（予定）（群馬県道路管理課）
   - 越後駒ヶ岳：国道352号 駒ノ湯入口〜銀山平（石抱橋）2026-11-04 9時から。解除は例年6月下旬（新潟県魚沼地域振興局）。枝折峠はこの区間
   - 荒沢岳：銀山平へ行く奥只見シルバーラインの冬期閉鎖。2026年は3/20 6時に解除（4/17 18時まで夜間通行止め）。今冬の閉鎖の開始は未発表（魚沼市）。
     荒沢岳の駐車場（銀山平）は国道352号の閉鎖区間（駒ノ湯入口〜石抱橋、銀山平船着場〜県境）のあいだにある（OpenStreetMap の位置で確かめた）
   期間の分からない項目はページに出ない（出典の見張りだけ）。
何度流しても同じ結果。このあと build_packing_mountains.py → gen_mountain_pages.py --all → gen_recommend_gear.py
→ gen_line_articles.py（odakyu-hiking・jr-chuo-hiking・seibu-hiking）→ sync_search_hubs.py --write → check_pages.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MP = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'migrations'))
from fix_split_month_gear_2026_11 import variants_attr  # noqa: E402
import add_gear_new_mountains_2026_11 as A  # noqa: E402

DAY = '2026-11-12'
LIGHT = {'kenashiyama': [12, 1, 2], 'kazahariyama': [12, 1, 2, 3]}
SEASON_TEXT = {'seasonNoGear': '5月〜10月', 'season6Crampons': '11月〜4月'}
RANK = {'no_crampons': 0, 'light_crampons': 1, 'winter_gear': 2, 'closed': -1}

CLOSURES = {
    'shirasunayama': {
        'kind': 'closure', 'label': '国道405号の冬期閉鎖（和光原〜野反湖。野反湖へ車で行けない）',
        'validFrom': '2026-11-25', 'validTo': '2027-04-21', 'seasonYear': '2026〜27',
        'sourceUrl': 'https://www.pref.gunma.jp/06/h2810053.html', 'lastVerified': DAY,
        'note': '11/25 15時〜4/21 10時の予定。解除の日は雪の状況で変わることがある',
    },
    'echigokoma': {
        'kind': 'closure', 'label': '国道352号の冬期通行止め（駒ノ湯入口〜銀山平。枝折峠へ車で行けない）',
        'validFrom': '2026-11-04', 'validTo': None, 'seasonYear': 2026,
        'sourceUrl': 'https://www.pref.niigata.lg.jp/site/uonuma-seibi/352toukiheisa.html', 'lastVerified': DAY,
        'note': '解除は例年6月下旬で、今季の日は未発表', 'needsVerification': True,
    },
    'arasawadake': {
        'kind': 'closure', 'label': '奥只見シルバーラインの冬期閉鎖（銀山平へ車で行けない）',
        'validFrom': None, 'validTo': None, 'seasonYear': None,
        'sourceUrl': 'https://www.city.uonuma.lg.jp/page/1022378.html', 'lastVerified': DAY,
        'note': '2026年は3月20日6時に解除（4月17日18時までは夜間も通行止め）。今冬の閉鎖の開始は未発表', 'needsVerification': True,
    },
}


def cur_of(v):
    return v if isinstance(v, str) else v['before']


def main():
    M = json.load(open(MP, encoding='utf-8'))
    G = json.load(open(GP, encoding='utf-8'))
    by = {m['id']: m for m in M}
    for mid, mos in LIGHT.items():
        m = by[mid]
        cal = m['gearCalendar']
        for mo in mos:
            assert cal[mo - 1] in ('winter_gear', 'light_crampons'), (mid, mo, cal[mo - 1])
            cal[mo - 1] = 'light_crampons'
            m['seasonCalendar'][mo - 1] = 's-gear'
        assert all(cur_of(v) != 'winter_gear' for v in cal), mid
        m['calLegend'] = ['アイゼン不要', '軽アイゼン等']
        m.update(SEASON_TEXT)
        m['mountainUpdated'] = DAY
        mm = G[mid]
        base = mm['11']
        shoe = [c for c in base if c['c'] == 'shoe'][0]
        cramp = [c for c in base if c['c'] == 'crampon'][0]
        assert 'G12' not in cramp['p'], (mid, cramp)
        for mo in mos:
            cards = mm[str(mo)]
            rain = [c for c in cards if c['c'] == 'rain']
            rest = [c for c in cards if c['c'] not in ('shoe', 'rain', 'crampon', 'crampon_next', 'axe')]
            cards[:] = [dict(shoe)] + [dict(c) for c in rain] + [dict(cramp)] + rest
        # 来月分のアイゼン：来月の区分が厳しくなる月だけ（fix_gear_cards_2026_11.py と同じ決まり）
        for mo in range(1, 13):
            cards = mm[str(mo)]
            cur, nxt = cur_of(cal[mo - 1]), cur_of(cal[mo % 12])
            want = nxt if RANK.get(nxt, -1) > RANK.get(cur, -1) and nxt != 'no_crampons' else None
            have = [c for c in cards if c['c'] == 'crampon_next']
            got = None if not have else ('winter_gear' if 'G12' in have[0]['p'] else 'light_crampons')
            if got != want:
                cards[:] = [c for c in cards if c['c'] != 'crampon_next']
                if want:
                    idx = max(i for i, c in enumerate(cards) if c['c'] in ('shoe', 'rain', 'crampon')) + 1
                    cards.insert(idx, dict(A.WINTER_NEXT if want == 'winter_gear' else A.LIGHT_NEXT))
    for mid, item in CLOSURES.items():
        m = by[mid]
        its = [a for a in m.get('annualItems') or [] if a.get('label') != item['label']]
        its.append(dict(item))
        m['annualItems'] = its
        m['mountainUpdated'] = DAY
    json.dump(M, open(MP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    with open(GP, 'w', encoding='utf-8') as f:
        json.dump(G, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('冬山装備→軽アイゼン等：毛無山 12〜2月・御座山 12〜3月。道路の冬期閉鎖：白砂山・越後駒ヶ岳・荒沢岳')
    pages = glob.glob(os.path.join(ROOT, 'articles/*/index.html')) + glob.glob(os.path.join(ROOT, 'search/*/index.html'))
    for p in sorted(pages):
        s = open(p, encoding='utf-8').read()
        if '<!-- generated: scripts/gen_line_articles' in s:
            continue
        hit = []
        for mid in LIGHT:
            pat = re.compile(r'(data-gear-mid="' + mid + r'"[^>]*?data-gear-variants=")([^"]*)(")')
            new = pat.sub(lambda x: x.group(1) + variants_attr(G[mid]) + x.group(3), s)
            if new != s:
                hit.append(mid)
                s = new
        if hit:
            open(p, 'w', encoding='utf-8').write(s)
            print('記事の写し', os.path.relpath(p, ROOT), ' '.join(hit))


if __name__ == '__main__':
    main()
