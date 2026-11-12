"""陣馬山の電車・バスの本線を、高尾駅北口からの西東京バス「美32」（陣馬高原下行き）にする（2026-11-11。運営者の指示）

前の本線は藤野駅からの神奈川中央交通「野08」（和田行き）で、2026年6月の改正で土日祝は全便運休・平日の朝だけになっていた。
高尾駅北口〜陣馬高原下：美32・37分（京王バス・西東京バスの「バスナビ」の発着時刻表。1時間に1本ほど・平日と土日祝とも）。
バス運賃 680円（NAVITIME の区間の運賃。西東京バスの公式の区間運賃表は見つからず要確認）。
電車（Yahoo!路線情報・2026-11-14 土曜 7時台・IC優先）：
  新宿→高尾 JR中央線中央特快 44分・715円
  大宮→高尾 JR埼京線・武蔵野線・中央線（武蔵浦和・西国分寺乗換）72分・1,034円
  横浜→高尾 JR横浜線・中央線（八王子乗換）72分・1,034円
合計：新宿 81分・1,395円／大宮 109分・1,714円／横浜 109分・1,714円

記事2本（電車で行ける日帰り登山20選・JR中央線の登山記事）は、藤野駅から歩いて相模湖駅へ下りるコースのまま載せるので、
記事の側に藤野駅までの区間を持たせる（courses.jinba.legs ／ line_articles の legs・fare）。時間は前の山のデータの値、
運賃は記事の courses.jinba.fares（Yahoo!路線情報・2026-10-30 確認）。

何度流しても同じ結果。このあと mark_train_routes_2026_11.py → build_access_tier.py --write → build_meta.py --write
→ gen_mountain_pages.py --id jinba → gen_line_articles.py jr-chuo-hiking → gen_train_daytrip.py → sync_search_pages.py --all → check_pages.py
"""
import json
import os
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'mountains.json')
TD = os.path.join(ROOT, 'data', 'train_daytrip.json')
LA = os.path.join(ROOT, 'data', 'line_articles.json')
TODAY = '2026-11-11'
BUS_TT = 'https://transfer.navitime.biz/bus-navi/pc/transfer/DepArrTimeList?snode=00020348&gnode=00042341'


def leg(station, icon=None, line=None, minutes=None):
    if icon is None:
        return {'station': station}
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}


def text(legs):
    out = []
    for l in legs:
        out.append(l['station'])
        if l.get('method'):
            mins = l['durationMin']
            t = ('約%d時間%d分' % (mins // 60, mins % 60) if mins >= 60 else '約%d分' % mins).replace('時間0分', '時間')
            out.append(l['method']['line'] + t)
    return '→'.join(out)


def hm(mins):
    return ('%d時間%d分' % (mins // 60, mins % 60) if mins % 60 else '%d時間' % (mins // 60)) if mins >= 60 else '%d分' % mins


BUS = [leg('高尾駅', 'bus', '西東京バス「美32」', 37), leg('陣馬高原下')]
ROUTES = {
    'shinjuku': {'legs': [leg('新宿駅', 'train', 'JR中央線（中央特快）', 44)] + BUS},
    'omiya': {'legs': [leg('大宮駅', 'train', 'JR埼京線・武蔵野線・中央線（武蔵浦和・西国分寺乗換）', 72)] + BUS},
    'yokohama': {'legs': [leg('横浜駅', 'train', 'JR横浜線・中央線（八王子乗換）', 72)] + BUS},
}
FARES = {'shinjuku': 1395, 'omiya': 1714, 'yokohama': 1714}

# 記事（藤野駅から歩くコース）の藤野駅までの区間。時間は前の山のデータ（藤野駅からのバスの前の区間）
FUJINO = {
    'shinjuku': [leg('新宿駅', 'train', 'JR中央線（高尾乗換込み）', 58), leg('藤野駅')],
    'omiya': [leg('大宮駅', 'train', 'JR武蔵野線・中央線（西国分寺・高尾乗換込み）', 89), leg('藤野駅')],
    'yokohama': [leg('横浜駅', 'train', 'JR横浜線・中央線（八王子・高尾乗換込み）', 83), leg('藤野駅')],
}


def mountain(m):
    tr = m['trainRoutes']
    tr['badge'] = {'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'}
    tr['lineName'] = 'JR中央線・西東京バス「美32」陣馬高原下行'
    tr['routes'] = json.loads(json.dumps(ROUTES))
    tr['note'] = None
    tr['summaryNote'] = None
    y = 'https://transit.yahoo.co.jp/search/result?from=%s&to=%s&type=1' % (quote('新宿'), quote('高尾駅'))
    tr['links'] = [{'type': 'yahoo', 'label': '乗換案内で検索', 'url': y},
                   {'type': 'bus', 'label': 'バス時刻表', 'url': BUS_TT}]
    m['busLinks'] = [y]
    m['busScheduleLinks'] = [BUS_TT]
    for dep, key in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
        m['trainTime' + key] = sum(l.get('durationMin') or 0 for l in ROUTES[dep]['legs'])
        m['fare' + key] = FARES[dep]
        m['transfers' + key] = 1
    m['trainAccess'] = text(ROUTES['shinjuku']['legs'])
    m['trainAccessOmiya'] = text(ROUTES['omiya']['legs'])
    m['trainAccessYokohama'] = text(ROUTES['yokohama']['legs'])
    m['trainInfo'] = '新宿→高尾駅（中央線約44分）→バス約37分'
    m['nearestStation'] = '高尾駅'
    m['trainAccessHtml'] = render_ts_section(tr, m)
    m['mountainUpdated'] = TODAY
    hit = 0
    for f in m.get('faq') or []:
        if f['question'].startswith('陣馬山へのアクセス方法'):
            f['answer'] = ('JR中央線の高尾駅北口から西東京バス「美32」で陣馬高原下へ（約37分・1時間に1本ほど）。新宿から約%s・1,395円、'
                           '大宮から約%s・1,714円、横浜から約%s・1,714円が目安です。藤野駅から歩いて登る道もあります。'
                           '車の場合は都心から約1時間15分が目安です。'
                           % (hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama'])))
            hit += 1
    assert hit == 1, hit


def articles():
    td = json.load(open(TD, encoding='utf-8'))
    c = td['courses']['jinba']
    c.pop('accessUntil', None)
    c['legs'] = json.loads(json.dumps(FUJINO))
    json.dump(td, open(TD, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    la = json.load(open(LA, encoding='utf-8'))
    n = 0

    def walk(o):
        nonlocal n
        if isinstance(o, dict):
            if o.get('id') == 'jinba' and ('accessUntil' in o or 'legs' in o):
                o.pop('accessUntil', None)
                o['legs'] = json.loads(json.dumps(FUJINO['shinjuku']))
                o['fare'] = td['courses']['jinba']['fares']['shinjuku']
                n += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(la)
    assert n == 1, n
    json.dump(la, open(LA, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def main():
    M = json.load(open(PATH, encoding='utf-8'))
    m = [x for x in M if x['id'] == 'jinba'][0]
    mountain(m)
    json.dump(M, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    articles()
    print('jinba', m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'])
    print('  ', m['trainAccess'])


if __name__ == '__main__':
    main()
