"""山小屋まとめの監査の反映（2026-11-09。ChatGPT の指摘を公式・自治体のページで確かめ、ほかの小屋の公式リンクも開いて確かめた）

直したもとの表（build_huts_from_nagano.py が使う）と同じ値を、data/huts.json の該当の小屋にだけ当てる。
build_huts_from_nagano.py を流すと定期更新の自動の値（auto など）が消えるため、まるごと作り直さない。何度流しても同じ結果。

- 定員（huts_checked.CAPACITY）：広河原山荘 101人（新しい山荘の収用人員。前は旧施設の約32人）、北岳山荘 80人、北岳肩の小屋 80人
  （どちらも前は山と溪谷オンラインの約150人）、蓼科山頂ヒュッテ 33人（前は約70人）、七ツ石小屋 10人（前は予約サイトの8人）、
  萬岳荘「宿泊部屋4室」（前は予約サイトの5人。公式に人数の記載なし）
- 予約（huts_booking_extra.py）：萬岳荘に予約フォーム（電話は12:00〜13:00）、蓼科山頂ヒュッテの2027年度の受付開始日、
  広河原山荘の個室は電話（山梨交通トラベル事業部）
- 公式リンク（huts_official_urls.json の override）：高谷池ヒュッテ・広河原山荘・尾瀬沼ヒュッテ・農鳥小屋・三国小屋・本山小屋・蛭ヶ岳山荘
- 標高（huts_checked.ELEVATION）と、公式サイトの無い小屋の「公式の案内」（huts_checked.INFO_URL）は gen_huts_page.py が直接読む

  python3 scripts/migrations/fix_huts_audit_2026_11.py && python3 scripts/gen_huts_page.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import huts_checked  # noqa: E402
from huts_booking_extra import BOOKING_EXTRA  # noqa: E402

NAMES = ['広河原山荘', '北岳山荘', '北岳肩の小屋', '蓼科山頂ヒュッテ', '七ツ石小屋', '萬岳荘', '高谷池ヒュッテ', '尾瀬沼ヒュッテ',
         '農鳥小屋', '三国岳避難小屋（三国小屋）', '飯豊山避難小屋（本山小屋）', '蛭ヶ岳山荘']


def main():
    path = os.path.join(ROOT, 'data', 'huts.json')
    data = json.load(open(path, encoding='utf-8'))
    over = json.load(open(os.path.join(ROOT, 'data', 'huts_official_urls.json'), encoding='utf-8')).get('override') or {}
    by = {h['name']: h for h in data['huts']}
    assert set(NAMES) <= set(by), set(NAMES) - set(by)
    for n in NAMES:
        h = by[n]
        if n in over:
            if h.get('bookingSourceUrl') == h.get('officialUrl'):
                h['bookingSourceUrl'] = over[n]
            h['officialUrl'] = over[n]
        huts_checked.apply(h)
        x = BOOKING_EXTRA.get(n) or {}
        if x.get('s'):
            h['bookingStart'] = x['s']
            h.pop('bookingStartUnstated', None)
        if x.get('m'):
            h['bookingMethods'] = x['m']
        if x.get('r'):
            h['bookingRequired'] = True
        if x.get('src'):
            h['bookingSourceUrl'] = x['src']
        print(n, '|', h.get('officialUrl'), '|', (h.get('capacityFix') or {}).get('text'), '|', h.get('bookingMethods'), '|', h.get('bookingStart'))
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
