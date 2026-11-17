"""スノーシュー（ワカン）が要る月を山に入れる（2026-11-17。運営者の指示「装備カレンダーと装備カードでスノーシューが要る山と月はそう表示したい」）

調べ方（運営者が決めた）：公式の案内、無ければ過去5年（2021年11月以降）の登山記録で、その月に別の人の2件以上がスノーシュー・ワカンを使った月。
調べた全113山の結果は .claude/snowshoe_research/result_*.json（8つの地域に分けて調べた）。入れるのは確からしさが中の5山だけ（運営者の指示）。
低い4山（仙ノ倉山12月・会津駒ヶ岳1〜2月・五竜岳1〜2月・立山11月）は入れていない（来季の記録で見直す候補）。
- 記録が1件だけでも、前後の月がどちらも「要る」月は入れた（間の月だけ空けると「要らない」と読めるため）：巻機山の1月・西吾妻山の2月
- 西吾妻山（1〜3月）と経ヶ岳（1月）は、記録・ガイドのツアーで12本爪アイゼン・ピッケルまでは要らないので、装備カレンダーを冬山装備 → 軽アイゼン等にして
  「スノーシュー等」の区分にする（運営者の指示「もう一度調べてどちらが良いか判断して」）。西吾妻山＝山と溪谷社のツアー（1月・3月、持ち物はスノーシュー）、
  アルパインツアーの雪山講習会（スノーシューかワカン・6本爪の軽アイゼン、ピッケルは無し）、2026-02-20 の記録（天元台からスノーシュー）。
  経ヶ岳＝2022-01-31（ピッケルもアイゼンも不要）・2023-01-21（チェーンスパイク＋ワカン）・2023-01-08（スノーシューが無く撤退）
- 装備カードには「スノーシュー」のカードを足す（アイゼン・ピッケルの次）。西吾妻山・経ヶ岳の下げた月は、12本爪アイゼンのカードを6本爪にし、靴の文を直す
何度流しても同じ結果。このあと build_packing_mountains.py → gen_mountain_pages.py --all → gen_recommend_gear.py → gen_line_articles.py --all → check_pages.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MP = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
RD = os.path.join(ROOT, '.claude', 'snowshoe_research')
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'migrations'))
from fix_split_month_gear_2026_11 import variants_attr  # noqa: E402
import add_gear_new_mountains_2026_11 as R  # noqa: E402
from fix_winter_gear_road_closures_2026_11 import RANK, cur_of  # noqa: E402

DAY = '2026-11-17'
MONTHS = {'tanigawa': [12, 1, 2], 'makihata': [12, 1, 2, 3], 'tairappyo': [12], 'azuma': [1, 2, 3], 'keizandake': [1]}
LOWER = {'azuma': [1, 2, 3], 'keizandake': [1]}   # 冬山装備 → 軽アイゼン等
# スノーシュー登山の定番の山（2026-11-17。運営者の指示「入笠山・霧ヶ峰・美ヶ原などスノーシュー登山で定番の山が入っていないのはおかしい」）
# 公式・自治体の観光局・ガイド会社が、その山（代表コースか、冬に行けるほうのコース）で冬のスノーシューのツアー・コースを案内している月。
# 踏み固められた道は軽アイゼン・チェーンスパイクでも歩けるので、装備カードは「条件次第」にして、そのことを書く
TEIBAN = {
    'nyukasayama': [1, 2], 'kirigamine': [1, 2], 'utsukushigahara': [1, 2, 3], 'asama': [12, 1, 2, 3],   # 浅間山の12月は 2026-11-17 に足した（fix_gear_calendar_hut_reports_2026_11.py。高峰温泉の現地情報）
    'kitayokodake': [1, 2, 3],   # 2026-11-17 運営者の指示「入れて」（長野県の観光サイトがスノーシューで山頂に立てる山として紹介）
}
TEIBAN_SRC = {
    'nyukasayama': [
        {'url': 'https://hoshinoresorts.com/ja/hotels/risonareyatsugatake/activities/13108/', 'date': '2027-01-04〜2027-02-28（開催期間）', 'kind': 'official',
         'says': 'ゴンドラで標高1,800mへ上がり、スノーシューなどで登山道を歩いて入笠山の山頂へ行くトレッキング'},
        {'url': 'https://san-tatsu.jp/pressrelease/507217/', 'date': '2026-02', 'kind': 'official',
         'says': '富士見パノラマリゾートの発表。入笠山のスノートレッキングは距離や高低差が抑えられ、初めてのスノーシューでも歩ける'},
        {'url': 'https://yamap.com/activities/37142196/article', 'date': '2025-01-11', 'kind': 'record', 'says': '雪はやや多め。スノーシューを借りて歩いた（トレースは良好）'},
    ],
    'kirigamine': [
        {'url': 'https://www.asoview.com/item/activity/pln3000032467/', 'date': '2026-11（掲載）', 'kind': 'official',
         'says': '霧ヶ峰自然教室の冬の八島湿原スノーシューウォーク。スノーシューを使うかは積雪で決める'},
        {'url': 'https://www.yamakei-online.com/cl_record/detail.php?id=23885', 'date': '2022-01-10', 'kind': 'record', 'says': '車山肩〜車山〜蝶々深山をスノーシューで歩いた'},
        {'url': 'https://yamap.com/activities/37782981/article', 'date': '2025-02-11', 'kind': 'record', 'says': '車山肩から車山をスノーシューで歩いた。パウダースノーのトレイル'},
    ],
    'utsukushigahara': [
        {'url': 'https://www.yamakei-online.com/yama-ya/detail.php?id=1756', 'date': '2021-12-14（取材 2021-02-03〜04）', 'kind': 'official',
         'says': '山と溪谷社の記事。スノーシューの適期は1月上旬〜3月中旬。山本小屋ふる里館（冬も車で行ける）から王ヶ鼻へ往復'},
    ],
    'kitayokodake': [
        {'url': 'https://www.go-nagano.net/nature-and-outdoors/id17126', 'date': '2024-12-12（更新）', 'kind': 'official',
         'says': '長野県の観光サイト。入笠山と北横岳はゴンドラ（ロープウェイ）を使って2000m級の山頂に立てるスノーシューの山。シーズンは12月中旬〜4月上旬'},
        {'url': 'https://www.yamakei-online.com/tour/detail.php?tour_id=298770', 'date': '2027-01-20・02-07・03-06（ツアーの日程）', 'kind': 'official',
         'says': '山と溪谷社のツアー。ロープウェイで上がり坪庭までスノーシューで歩く。北横岳の山頂へはアイゼンで登るコース'},
    ],
    'asama': [
        {'url': 'https://www.komoro-tour.jp/wp/wp-content/uploads/2024/12/790c62004ec3c11fe2276ace4498a392.pdf', 'date': '2025-01-25・02-22・03-08（開催日）', 'kind': 'official',
         'says': '小諸市観光局のツアー「雪山初心者大歓迎！スノーシューで行く」黒斑山（車坂峠から）'},
        # 12月（2026-11-17。fix_gear_calendar_hut_reports_2026_11.py の ASAMA_SRC と同じ）
        {'url': 'https://www.yamakei-online.com/mt_info/past.php?id=1069&yy=2022', 'date': '2022-12-20', 'kind': 'official',
         'says': '高峰温泉（車坂峠の近く）の現地情報「週末の雪で50cm積もっています。スノーシューを楽しめる季節になりました」'},
        {'url': 'https://www.yamakei-online.com/mt_info/past.php?id=1069&yy=2022', 'date': '2022-12-26', 'kind': 'official',
         'says': '高峰温泉（車坂峠の近く）の現地情報「登山道では70cm以上の積雪があり、スノーシューが必要です」'},
        {'url': 'https://www.yamakei-online.com/mt_info/past.php?id=1069&yy=2024', 'date': '2024-12-30', 'kind': 'official',
         'says': '高峰温泉（車坂峠の近く）の現地情報「パウダースノーの雪がたくさん積もり、スノーシューを楽しめます」'},
    ],
}
TEIBAN_NOTE = {
    'nyukasayama': '冬はスノーシューで歩くのが定番（ゴンドラ山頂駅から）。踏み固められた道は軽アイゼン・チェーンスパイクでも歩ける',
    'kirigamine': '冬はスノーシューで歩くのが定番（車山肩・八島湿原）。踏み固められた道は軽アイゼン・チェーンスパイクでも歩ける',
    'utsukushigahara': '冬はスノーシューで歩くのが定番。冬は山本小屋ふる里館から（美ヶ原自然保護センターへの道は冬期通行止め）',
    'asama': '冬は車坂峠から黒斑山へスノーシューで歩くのが定番（コース2）。前掛山へは冬山装備が要る',
    'kitayokodake': '冬はロープウェイで上がり、坪庭をスノーシューで歩くのが定番。山頂への登りは踏み固められていることが多く、アイゼンで登るツアーもある',
}
TEIBAN_CARD = {'c': 'snowshoe', 'i': '条件次第', 'p': 'MSR ライトニングアッセント',
               'r': '冬はスノーシューで歩くのが定番の山です。新雪の後や道を外れて雪原を歩くならスノーシューを。踏み固められた道は軽アイゼン・チェーンスパイクでも歩けます。'}
EXTRA_SRC = {
    'azuma': [
        {'url': 'https://www.alpine-tour.com/japan_tour/ktswk3/', 'date': '2026-11', 'kind': 'official',
         'says': '雪山講習会（入門）の持ち物はスノーシューかワカン・6本爪の軽アイゼン。ピッケルは無い'},
        {'url': 'https://yamap.com/activities/46243602/article', 'date': '2026-02-20', 'kind': 'record',
         'says': '天元台のリフト終点から西吾妻山へスノーシューで往復。アイゼン・ピッケルの記載なし'},
    ],
    'makihata': [
        {'url': 'https://yamap.com/activities/15387027/article', 'date': '2022-01-25', 'kind': 'record',
         'says': '巻機山・牛ヶ岳まで全行程スノーシューで歩いた'},
    ],
}
NOTE = {
    'makihata': '1月は記録が1件だけだが、12月・2月が「要る」ため同じにした',
    'azuma': '2月は記録が1件だけだが、1月・3月が「要る」ため同じにした。12本爪アイゼン・ピッケルまでは要らない（6本爪の軽アイゼン）',
    'keizandake': '降雪の後やトレースの無い日。トレースがあればチェーンスパイクだけで登れた記録もある。12本爪アイゼン・ピッケルまでは要らない',
}
SNOW_CARD = {'c': 'snowshoe', 'i': '推奨', 'p': 'MSR ライトニングアッセント',
             'r': '雪が深く、トレースが無いと膝〜腰まで沈む時期です。スノーシューかワカン（かんじき）があると沈まずに歩けます。降雪の後は特に要ります。'}
LIGHT_CRAMP = {'c': 'crampon', 'i': '推奨', 'p': 'エバニュー 6本爪アイゼン',
               'r': '凍った所・固い雪の斜面に。12本爪アイゼン・ピッケルまでは要りませんが、6本爪の軽アイゼンかチェーンスパイクを持っていきましょう。'}
SHOE_TEXT = '雪の深い時期です。保温性のある冬用の登山靴で、スノーシューやワカンを付けて歩きます。'


def load_sources(mid):
    out = []
    for f in sorted(glob.glob(os.path.join(RD, 'result_*.json'))):
        for r in json.load(open(f, encoding='utf-8')):
            if r['id'] == mid:
                out += [s for s in r.get('sources') or [] if s.get('kind') in ('official', 'record')]
    return out + EXTRA_SRC.get(mid, [])


def main():
    M = json.load(open(MP, encoding='utf-8'))
    G = json.load(open(GP, encoding='utf-8'))
    by = {m['id']: m for m in M}
    # 前に入れて、いまは外した山の値は消す
    for m in M:
        if m['id'] not in MONTHS and m['id'] not in TEIBAN:
            for k in ('snowshoeMonths', 'snowshoeSources', 'snowshoeNote', 'snowshoeCheckedAt'):
                m.pop(k, None)
    for mid, mos in LOWER.items():
        m = by[mid]
        for mo in mos:
            assert m['gearCalendar'][mo - 1] in ('winter_gear', 'light_crampons'), (mid, mo)
            m['gearCalendar'][mo - 1] = 'light_crampons'
            m['seasonCalendar'][mo - 1] = 's-gear'
        mm = G[mid]
        for mo in mos:
            cards = mm[str(mo)]
            for c in cards:
                if c['c'] == 'crampon':
                    c.clear(); c.update(LIGHT_CRAMP)
                if c['c'] == 'shoe':
                    c['r'] = SHOE_TEXT
            cards[:] = [c for c in cards if c['c'] != 'axe']
        # 来月分のアイゼン：来月の区分が厳しくなる月だけ（fix_winter_gear_road_closures_2026_11.py と同じ決まり）
        cal = m['gearCalendar']
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
                    cards.insert(idx, dict(R.WINTER_NEXT if want == 'winter_gear' else R.LIGHT_NEXT))
        m['mountainUpdated'] = DAY
    for mid, mos in TEIBAN.items():
        m = by[mid]
        m['snowshoeMonths'] = sorted(mos)
        m['snowshoeSources'] = TEIBAN_SRC[mid]
        m['snowshoeCheckedAt'] = DAY
        m['snowshoeNote'] = TEIBAN_NOTE[mid]
        m['mountainUpdated'] = DAY
        for mo in mos:
            cards = G[mid][str(mo)]
            cards[:] = [c for c in cards if c['c'] != 'snowshoe']
            idx = max([i for i, c in enumerate(cards) if c['c'] in ('shoe', 'crampon', 'crampon_next', 'axe', 'helmet')] or [0]) + 1
            cards.insert(idx, dict(TEIBAN_CARD))
    for mid, mos in MONTHS.items():
        m = by[mid]
        m['snowshoeMonths'] = sorted(mos)
        m['snowshoeSources'] = load_sources(mid)
        m['snowshoeCheckedAt'] = DAY
        if NOTE.get(mid):
            m['snowshoeNote'] = NOTE[mid]
        m['mountainUpdated'] = DAY
        for mo in mos:
            cards = G[mid][str(mo)]
            cards[:] = [c for c in cards if c['c'] != 'snowshoe']
            idx = max([i for i, c in enumerate(cards) if c['c'] in ('shoe', 'crampon', 'crampon_next', 'axe', 'helmet')] or [0]) + 1
            cards.insert(idx, dict(SNOW_CARD))
    # 外した山のカードも消す
    for mid, mm in G.items():
        if mid in MONTHS or mid in TEIBAN:
            continue
        for mo, cards in mm.items():
            if any(c['c'] == 'snowshoe' for c in cards):
                cards[:] = [c for c in cards if c['c'] != 'snowshoe']
    json.dump(M, open(MP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    with open(GP, 'w', encoding='utf-8') as f:
        json.dump(G, f, ensure_ascii=False, indent=2)
        f.write('\n')
    for mid, mos in list(MONTHS.items()) + list(TEIBAN.items()):
        print(by[mid]['name'], mos, '出典', len(by[mid]['snowshoeSources']))
    pages = glob.glob(os.path.join(ROOT, 'articles/*/index.html')) + glob.glob(os.path.join(ROOT, 'search/*/index.html'))
    for p in sorted(pages):
        s = open(p, encoding='utf-8').read()
        if '<!-- generated: scripts/gen_line_articles' in s:
            continue
        hit = []
        for mid in list(MONTHS) + list(TEIBAN):
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
