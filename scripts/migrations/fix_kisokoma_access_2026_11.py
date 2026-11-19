"""木曽駒ヶ岳の電車・バスを中央アルプス観光の公式の時刻表に合わせ、ロープウェイの点検運休を入れる（2026-11-19。運営者の指示「直して。点検運休の1か月前から表示は出したい（何日から何日はロープウェイ運休みたいな）」）

公式（中央アルプス観光「時刻表」https://chuo-alps.com/timetable/ と、2026年度の路線バス・ロープウェイ時刻表 PDF）で確かめたこと（2026-11-19）：
- 路線バスは駒ヶ根駅前からしらび平まで1本（菅の台バスセンターは3分止まるだけで乗り換えは無い）。駒ヶ根駅前→しらび平 45分・1,050円、
  ロープウェイ しらび平→千畳敷 7分（7分30秒）・1,370円。前のデータは「駒ヶ根駅→バス25分→菅の台バスセンター→中央アルプス観光バス30分→しらび平」で、
  菅の台で乗り換えるように見え、合計も55分だった。運賃の合計は同じ（同じバスの区間）なので変えない
- 2026年12月1日〜6日、2027年1月27日〜2月4日はロープウェイのメンテナンス運休。路線バスは駒ヶ根駅前〜駒ヶ根橋の折り返しだけで、しらび平・千畳敷へは行けない
  （菅の台から先は一年中マイカー規制なので、車でも同じ）
- 時刻表のボタンのリンク先 https://www.chuo-alps.com/access/bus/ はモデルコースのページに飛ぶようになっていたので、時刻表のページに替える
点検運休は annualItems の kind "suspension"（gen_mountain_pages.py の render_suspensions が、始まる30日前から終わる日までページの上に出す）。
何度流しても同じ結果。このあと build_derived.py → build_access_tier.py --write → build_winter_find.py → gen_find_winter.py → gen_mountain_pages.py --id kisokoma → check_pages.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DAY = '2026-11-19'
TIMETABLE = 'https://chuo-alps.com/timetable/'
PDF = 'https://chuo-alps.com/wp-content/uploads/2026/01/%E3%80%90%E7%A2%BA%E5%AE%9A%E3%80%912026R8%E5%B9%B4%E5%BA%A6%E3%83%90%E3%82%B9%E5%81%9C%E6%99%82%E5%88%BB%E8%A1%A8.pdf'
BUS = {'station': '駒ヶ根駅', 'method': {'icon': 'bus', 'line': '路線バス（駒ヶ岳ロープウェイ線）'}, 'durationMin': 45, 'fareYen': None}
ROPE = {'station': 'しらび平', 'method': {'icon': 'ropeway', 'line': 'ロープウェイ'}, 'durationMin': 8, 'fareYen': None}
NOTE = ('点検のためロープウェイが運休します。路線バスも駒ヶ根駅前〜駒ヶ根橋の折り返しだけになり、しらび平・千畳敷へは行けません'
        '（菅の台から先はマイカー規制なので、車でも同じです）')
SUSP = [
    {'kind': 'suspension', 'label': 'ロープウェイ運休（点検）', 'validFrom': '2026-12-01', 'validTo': '2026-12-06', 'seasonYear': '2026',
     'showDaysBefore': 30, 'note': NOTE, 'sourceUrl': PDF, 'linkText': '路線バス・ロープウェイ時刻表（2026年度）', 'lastVerified': DAY},
    {'kind': 'suspension', 'label': 'ロープウェイ運休（点検）', 'validFrom': '2027-01-27', 'validTo': '2027-02-04', 'seasonYear': '2026',
     'showDaysBefore': 30, 'note': NOTE, 'sourceUrl': PDF, 'linkText': '路線バス・ロープウェイ時刻表（2026年度）', 'lastVerified': DAY},
]

apath = os.path.join(ROOT, 'data', 'accesses.json')
araw = open(apath, encoding='utf-8').read()
A = json.loads(araw)
a = A['senjojiki']
tr = a['trainRoutes']
for dep, r in tr['routes'].items():
    legs = r['legs']
    i = next(k for k, l in enumerate(legs) if l.get('station') == '駒ヶ根駅')
    r['legs'] = legs[:i] + [dict(BUS), dict(ROPE), {'station': '千畳敷'}]
a['trainTimes'] = {dep: sum(l.get('durationMin') or 0 for l in r['legs']) for dep, r in tr['routes'].items()}
a['transfers'] = {dep: sum(1 for l in r['legs'] if l.get('method') and l['method'].get('icon') != 'walk') - 1 for dep, r in tr['routes'].items()}
tr['lineName'] = '高速バス（新宿〜駒ヶ根線）・路線バス（駒ヶ岳ロープウェイ線）・駒ヶ岳ロープウェイ'
for l in tr['links']:
    if l.get('type') == 'bus':
        l['url'] = TIMETABLE
        l['label'] = '路線バス・ロープウェイ時刻表'
a['busScheduleLinks'] = [TIMETABLE]
a['operation']['note'] = ('バス・ロープウェイは通年運行（2026年度は夏ダイヤ4/10〜11/30、ほかは冬ダイヤ。'
                          '2026/12/1〜12/6・2027/1/27〜2/4はロープウェイ点検運休）')
a['lastVerified'] = DAY
open(apath, 'w', encoding='utf-8').write(json.dumps(A, ensure_ascii=False, indent=2) + ('\n' if araw.endswith('\n') else ''))

mpath = os.path.join(ROOT, 'data', 'mountains.json')
M = json.load(open(mpath, encoding='utf-8'))
m = next(x for x in M if x['id'] == 'kisokoma')
m['annualItems'] = [x for x in m.get('annualItems') or [] if x.get('kind') != 'suspension'] + [dict(s) for s in SUSP]
m['mountainUpdated'] = max(m.get('mountainUpdated') or '', DAY)
json.dump(M, open(mpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', a['trainTimes'], a['transfers'])
