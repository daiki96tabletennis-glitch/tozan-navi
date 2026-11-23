"""ロープウェイ・ケーブルカーの点検運休を、木曽駒ヶ岳と同じお知らせ（annualItems の kind "suspension"）で入れる（2026-11-19。運営者の指示
「他の山でも類似事例があれば対応して欲しい」。表示は日付で切り替え、出典は見張りで追う＝運営者の選択）。
あわせて、御岳山ケーブルカーの運賃改定（2026-10-01 から大人片道600円→700円）を、御岳山・日の出山・大岳山の運賃に入れる。

公式で確かめたこと（2026-11-19）：
- 北八ヶ岳ロープウェイ（北横岳）：2026年11月24日〜12月18日は整備点検で運休、冬の営業は12月19日から（https://www.kitayatu.jp/ropeway/）。
  前は kind "closure" で入れていたのを suspension にする（30日前からページの上に出る。冬の山選び診断の扱いは同じ）
- 御岳山ケーブルカー（御岳山・日の出山・大岳山）：電車線張替工事 2026年12月9日（始発〜8時40分発は運行）〜12月10日、
  巻上機制御装置点検 2027年1月18日（始発〜8時40分発は運行）〜1月20日。観光リフトも運休
  （御岳登山鉄道 ニュースリリース 2026-10-24 https://www.mitaketozan.co.jp/infomation/release_2026_10_25.pdf）
- 御岳山ケーブルカーの運賃：2026年10月1日から大人片道700円（前は600円。御岳登山鉄道 2026-09-04 https://www.mitaketozan.co.jp/infomation/release_2026_09_04.pdf）。
  Yahoo!乗換案内（2026-11-21 土曜朝・IC）：新宿→御嶽 1,034円・大宮 1,221円・横浜 1,408円、御嶽駅→ケーブル下（西東京バス）340円、ケーブル 700円。
  合計 新宿 2,074円・大宮 2,261円・横浜 2,448円（前は 1,974／2,164／2,344円）
- 新穂高ロープウェイ（西穂高岳）：2026年11月24日〜27日はメンテナンスで全線運休（【2026年度】新穂高ロープウェイの運行計画について。2026-03-09）
- 天元台（西吾妻山）：2026-27年の冬の点検運休 12/9・1/6・2/3・3/10・4/14（ロープウェイ・リフトとも終日。https://www.winter.tengendai.jp/）
確かめられなかった：大山ケーブルカー（公式サイトが 504 で開けない）。
何度流しても同じ結果。このあと gen_mountain_pages.py → build_winter_find.py → gen_find_winter.py → gen_train_daytrip.py → gen_line_articles.py jr-chuo-hiking → check_pages.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

DAY = '2026-11-19'
MITAKE_SRC = 'https://www.mitaketozan.co.jp/infomation/release_2026_10_25.pdf'
MITAKE_NOTE = '点検・工事のためケーブルカーと観光リフトが運休します。'
MITAKE = [
    {'kind': 'suspension', 'label': 'ケーブルカー運休（電車線張替工事）', 'validFrom': '2026-12-09', 'validTo': '2026-12-10', 'seasonYear': '2026',
     'note': MITAKE_NOTE + '12月9日は始発から8時40分発までは運行します', 'sourceUrl': MITAKE_SRC, 'linkText': '御岳登山鉄道のお知らせ', 'lastVerified': DAY},
    {'kind': 'suspension', 'label': 'ケーブルカー運休（巻上機制御装置点検）', 'validFrom': '2027-01-18', 'validTo': '2027-01-20', 'seasonYear': '2026',
     'note': MITAKE_NOTE + '1月18日は始発から8時40分発までは運行します', 'sourceUrl': MITAKE_SRC, 'linkText': '御岳登山鉄道のお知らせ', 'lastVerified': DAY},
]
SUSP = {
    'kitayokodake': [
        {'kind': 'suspension', 'label': '北八ヶ岳ロープウェイ運休（整備点検）', 'validFrom': '2026-11-24', 'validTo': '2026-12-18', 'seasonYear': '2026',
         'note': '整備点検のためロープウェイが運休し、山頂駅へ上がれません。冬の営業は12月19日から', 'sourceUrl': 'https://www.kitayatu.jp/ropeway/',
         'linkText': '北八ヶ岳ロープウェイ', 'lastVerified': DAY},
    ],
    'mitakesan': MITAKE, 'hinodesaan': MITAKE, 'otake': MITAKE,
    'nishihotaka': [
        {'kind': 'suspension', 'label': '新穂高ロープウェイ運休（メンテナンス）', 'validFrom': '2026-11-24', 'validTo': '2026-11-27', 'seasonYear': '2026',
         'note': 'メンテナンスのため新穂高ロープウェイが全線運休し、西穂高口駅へ上がれません（上高地からのコースは別）',
         'sourceUrl': 'https://shinhotaka-ropeway.jp/%e3%80%902026%e5%b9%b4%e5%ba%a6%e3%80%91%e6%96%b0%e7%a9%82%e9%ab%98%e3%83%ad%e3%83%bc%e3%83%97%e3%82%a6%e3%82%a7%e3%82%a4%e3%81%ae%e9%81%8b%e8%a1%8c%e8%a8%88%e7%94%bb%e3%81%ab%e3%81%a4%e3%81%84/',
         'linkText': '新穂高ロープウェイの運行計画', 'lastVerified': DAY},
    ],
    'azuma': [
        {'kind': 'suspension', 'label': '天元台ロープウェイ・リフト運休（点検）', 'validFrom': d, 'validTo': d, 'seasonYear': '2026',
         'note': '索道施設の検査のため、ロープウェイ・リフトとも終日運休します', 'sourceUrl': 'https://www.winter.tengendai.jp/',
         'linkText': '天元台高原 ウィンターシーズン', 'lastVerified': DAY}
        for d in ('2026-12-09', '2027-01-06', '2027-02-03', '2027-03-10', '2027-04-14')
    ],
}
OLD_CLOSURE = '北八ヶ岳ロープウェイの運休（整備点検）'
FARE = {'Shinjuku': (1974, 2074), 'Omiya': (2164, 2261), 'Yokohama': (2344, 2448)}

path = os.path.join(ROOT, 'data', 'mountains.json')
M = json.load(open(path, encoding='utf-8'))
for mid, items in SUSP.items():
    m = next(x for x in M if x['id'] == mid)
    labels = {s['label'] for s in items}
    m['annualItems'] = [a for a in m.get('annualItems') or []
                        if a.get('label') not in labels and a.get('label') != OLD_CLOSURE] + [dict(s) for s in items]
    m['mountainUpdated'] = max(m.get('mountainUpdated') or '', DAY)

# 御岳山ケーブルカーの運賃改定
for mid in ('mitakesan', 'hinodesaan', 'otake'):
    m = next(x for x in M if x['id'] == mid)
    for k, (old, new) in FARE.items():
        if m.get('fare' + k) == old:
            m['fare' + k] = new
    raw = json.dumps(m, ensure_ascii=False)
    for old, new in FARE.values():
        raw = raw.replace(f'{old:,}円', f'{new:,}円')
    m2 = json.loads(raw)
    m.clear()
    m.update(m2)
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    assert not re.search(r'1,974|2,164円|2,344円', json.dumps(m, ensure_ascii=False)), mid
json.dump(M, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
