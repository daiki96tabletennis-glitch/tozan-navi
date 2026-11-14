"""大菩薩嶺（okutama）の上日川峠へのバスの運行期間と、県道の冬期閉鎖を入れる（2026-11-15。運営者の指示。外部の監査の指摘を公式で確かめた）

- バス：栄和交通「大菩薩上日川峠線時刻表」（PDF。https://eiwa-kotsu.jp/root.html からリンク）
    「2026年4月18日（土）〜12月13日（日）間の 土・日・祝日（一部平日有り）を運行します。※季節運行のため運行日は変更になる場合があります。」
  前は季節運行の期限（annualItems の transport）が入っておらず、冬もこの行き方がそのまま出ていた
  （山ページの電車・バス・アクセス難易度・月ごとの数え方・期限の見張りに出ない）
- 県道：甲州市「大菩薩への県道の冬期閉鎖期間と問い合わせについて」（2022-01-13 更新）
    県道201号（塩山停車場大菩薩線・塩山側・裂石〜上日川峠）12月中旬〜4月中旬、県道218号（大菩薩初鹿野線・大和側・一の平林道交差点〜上日川峠）1月上旬〜4月中旬。
  今冬の日付は発表されていないので、期間なしの closure（出典の見張りだけ。毎日の規制・閉鎖の見張りにも入る）
- 注記に「バスは4月中旬〜12月中旬の土日祝だけ（冬は県道も閉鎖）」を足す（1山3項目まで）

何度流しても同じ結果。このあと build_access_tier.py --write → gen_mountain_pages.py --id okutama → gen_winter_specials.py → check_pages.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

DAY = '2026-11-15'
BUS = {'kind': 'transport', 'label': '甲斐大和駅〜上日川峠のバス（栄和交通 大菩薩上日川峠線）', 'validFrom': '2026-04-18',
       'validTo': '2026-12-13', 'seasonYear': 2026, 'sourceUrl': 'https://eiwa-kotsu.jp/root.html', 'lastVerified': DAY,
       'note': '土・日・祝日（一部平日）。12月14日から4月中旬までは運休'}
ROAD = {'kind': 'closure', 'label': '上日川峠への県道の冬期閉鎖', 'validFrom': None, 'validTo': None, 'seasonYear': None,
        'sourceUrl': 'https://www.city.koshu.yamanashi.jp/faq/2012033100570/', 'lastVerified': DAY,
        'note': '例年、県道201号（塩山側）は12月中旬〜4月中旬、県道218号（大和側）は1月上旬〜4月中旬。今冬の日付は未発表'}
NOTE = '上日川峠へのバスは4月中旬〜12月中旬の土日祝だけ（冬は県道も閉鎖）'

path = os.path.join(ROOT, 'data', 'mountains.json')
M = json.load(open(path, encoding='utf-8'))
m = next(x for x in M if x['id'] == 'okutama')
items = [x for x in (m.get('annualItems') or []) if x.get('label') not in (BUS['label'], ROAD['label'])]
m['annualItems'] = items + [BUS, ROAD]
tr = m['trainRoutes']
note = tr.get('note') or ''
if NOTE not in note:
    tr['note'] = (note.rstrip('。') + '。' + NOTE) if note else NOTE
m['trainAccessHtml'] = render_ts_section(tr, m)
m['mountainUpdated'] = DAY
json.dump(M, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', tr['note'])
