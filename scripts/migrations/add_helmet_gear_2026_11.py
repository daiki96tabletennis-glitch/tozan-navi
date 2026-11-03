"""装備カードに登山ヘルメットを足す（2026-11-03。運営者の指示）

対象：長野県の「山岳ヘルメット着用奨励山域」（2013年指定・2023年改正）の区間を、
サイトのコースが通る山だけ。
出典：https://www.pref.nagano.lg.jp/kankoki/sangaku/helmet.html （2026-11-03 確認）
  岩稜帯（無雪期）：槍・穂高連峰のうち北穂高岳〜涸沢岳・屏風岩、前穂高岳（北尾根〜吊尾根）一帯、
    西穂高岳〜奥穂高岳、北穂高岳〜南岳（大キレット）、槍ヶ岳北鎌尾根・東鎌尾根／不帰の嶮周辺、
    八峰キレット周辺／甲斐駒ケ岳、鋸岳／宝剣岳／戸隠山、西岳
  活火山（無雪期）：焼岳、乗鞍岳、御嶽山、浅間山
  積雪期：滑落、転落、落石等の危険のあるすべての山域
  「活動火山対策特別措置法では、ヘルメットを含む必要な装備の携帯は活火山を登山する者の努力義務」
槍・穂高はほかに、上高地観光旅館組合「登山用ヘルメットのすすめ」（2019-04-02）が
「槍ヶ岳・穂高連峰への入山時にはヘルメットの携帯・着用を！」と呼びかけている。

必要度：山全体が指定（または槍・穂高）なら「推奨」、指定の区間を通るコースが一部だけなら
「条件次第」（そのコースを文に書く）。冬山装備の月は、長野県が積雪期は危険のある山域すべてを
指定しているので「推奨」にして、その一文を足す。
カードは各月の2枚目（登山靴の次）。何度流しても同じ結果になる（前の helmet カードは外してから入れる）。
直したら gen_mountain_pages.py --id …・gen_recommend_gear.py、カードの写しを持つ記事は
このスクリプトが一緒に直す。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

PRODUCT = 'ブラックダイヤモンド ハーフドーム ヘルメット'
SNOW = '雪の時期は、滑落・転落・落石の危険がある山域すべてで着用が勧められています（長野県）。'
VOLCANO = '活火山に登る人は、ヘルメットなどの携帯に努めることになっています（活動火山対策特別措置法）。'
YARIHO = '上高地観光旅館組合も、槍・穂高に入るときのヘルメットの携帯・着用を呼びかけています。'

# (必要度, 文)。文は出典に書いてあることだけ
HELMET = {
    'komagatake': ('推奨', '甲斐駒ヶ岳は、滑落・転落・落石の多い岩稜帯として、長野県が「山岳ヘルメット着用奨励山域」に指定しています。'),
    'nokogiriyama': ('推奨', '鋸岳は、滑落・転落・落石の多い岩稜帯として、長野県が「山岳ヘルメット着用奨励山域」に指定しています。'),
    'yakedake': ('推奨', '焼岳は、活火山として長野県が「山岳ヘルメット着用奨励山域」に指定しています。' + VOLCANO),
    'norikura': ('推奨', '乗鞍岳は、活火山として長野県が「山岳ヘルメット着用奨励山域」に指定しています。' + VOLCANO),
    'ontakesan': ('推奨', '御嶽山は、活火山として長野県が「山岳ヘルメット着用奨励山域」に指定しています。' + VOLCANO),
    'asama': ('条件次第', '前掛山まで登るコースは、活火山の浅間山として長野県が「山岳ヘルメット着用奨励山域」に指定している山域です。' + VOLCANO),
    'hotaka': ('推奨', '吊尾根（前穂高岳〜奥穂高岳）と、西穂高岳〜奥穂高岳（ジャンダルム）は、長野県の「山岳ヘルメット着用奨励山域」の区間です。' + YARIHO),
    'yari': ('推奨', '表銀座で通る東鎌尾根は、長野県の「山岳ヘルメット着用奨励山域」の区間です。' + YARIHO),
    'kashimayari': ('条件次第', '五竜岳への縦走で通る八峰キレットは、長野県の「山岳ヘルメット着用奨励山域」の区間です。柏原新道・赤岩尾根からの往復は区間に入りません。'),
    'karamatsu': ('条件次第', '白馬鑓温泉への縦走で通る不帰ノ嶮は、長野県の「山岳ヘルメット着用奨励山域」の区間です。八方尾根からの往復は区間に入りません。'),
    'takatsuma': ('条件次第', '戸隠奥社から戸隠山を通るコースは、長野県の「山岳ヘルメット着用奨励山域」の区間です。一不動・弥勒尾根からのコースは区間に入りません。'),
}


def winter_months(mt):
    """冬山装備（前半・後半のどちらかでも）の月"""
    out = set()
    cal = mt.get('gearCalendar') or []
    for i, v in enumerate(cal):
        vals = [v.get('before'), v.get('after')] if isinstance(v, dict) else [v]
        if 'winter_gear' in vals:
            out.add(i + 1)
    return out


def card_for(mid, month, winter):
    need, text = HELMET[mid]
    if month in winter:
        need = '推奨'
        text = text + SNOW
    return {'c': 'helmet', 'i': need, 'p': PRODUCT, 'r': text}


def variants_attr(md):
    # gen_mountain_pages.render_gear と同じ形
    groups, order = {}, []
    for month in sorted(md.keys(), key=int):
        key = json.dumps(md[month], ensure_ascii=False)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(int(month))
    return json.dumps({k: groups[k] for k in order}, ensure_ascii=False).replace('"', '&quot;')


def main():
    mts = json.load(open(os.path.join(ROOT, 'data/mountains.json')))
    mts = {m['id']: m for m in (mts if isinstance(mts, list) else mts['mountains'])}
    gpath = os.path.join(ROOT, 'data/gear-data.json')
    gear = json.load(open(gpath))
    missing = [m for m in HELMET if m not in mts or m not in gear]
    if missing:
        sys.exit('山が見つからない: %s' % missing)
    for mid in HELMET:
        win = winter_months(mts[mid])
        for month, cards in gear[mid].items():
            cards = [c for c in cards if c.get('c') != 'helmet']
            pos = 1 if cards and cards[0].get('c') == 'shoe' else 0
            cards.insert(pos, card_for(mid, int(month), win))
            gear[mid][month] = cards
        print(mid, '月数', len(gear[mid]), '冬山装備の月', sorted(win))
    with open(gpath, 'w') as f:
        json.dump(gear, f, ensure_ascii=False, indent=2)
        f.write('\n')

    # 手で作った記事・まとめにある装備カードの写しも合わせる
    import glob
    pages = glob.glob(os.path.join(ROOT, 'articles/*/index.html')) + glob.glob(os.path.join(ROOT, 'search/*/index.html'))
    for p in pages:
        s = open(p).read()
        if '<!-- generated: scripts/gen_line_articles' in s:
            continue  # 路線別の記事は gen_line_articles.py で作り直す
        total = 0
        for mid in HELMET:
            pat = re.compile(r'(data-gear-mid="' + mid + r'"[^>]*?data-gear-variants=")([^"]*)(")')
            s, n = pat.subn(lambda m: m.group(1) + variants_attr(gear[mid]) + m.group(3), s)
            total += n
        if total:
            open(p, 'w').write(s)
            print('記事の写し', os.path.relpath(p, ROOT), total)


if __name__ == '__main__':
    main()
