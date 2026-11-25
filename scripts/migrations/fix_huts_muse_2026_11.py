"""山小屋の予約情報・定員の反映（2026-11-25。運営者が MUSE に頼んだ調査 135軒の結果を、出典のページを開いて原文・数字を確かめたものだけ）

頼んだ文と対象は .claude/huts_research_request_2026_11.md・huts_research_targets_2026_11.csv、結果の控えは .claude/huts_research_results_2026_11.csv と、追加の調査の _v2.csv（2回目に反映）。
もとの表（huts_checked.CAPACITY・huts_booking_extra.BOOKING_EXTRA の 2026-11-25 の項目）と同じ値を、data/huts.json の該当の小屋にだけ当てる。
build_huts_from_nagano.py を流すと定期更新の自動の値（auto など）が消えるため、まるごと作り直さない。何度流しても同じ結果。

入れなかったもの：苗場山頂ヒュッテの「1月5日から」（Instagram の画像の文字だけ）、長田山荘・中の湯温泉旅館・野口五郎小屋の予約の開始
（出典で原文を読めなかった）、宝永山荘の定員（予約サイト50人・登山組合と静岡県80人で食い違う）、茶臼小屋・大滝山荘・菊屋・薬師岳山荘の定員
（出典で数字を確かめられなかった）、LUCY尾瀬鳩待・雲上閣の定員（部屋の内訳からの足し算）、位ヶ原山荘（感染症対策の時期の人数）、
白山南竜山荘（150人に取り消し線・削減後の人数なし）。
2回目で入れなかったもの：半蔵坊の定員（予約サイト18人・静岡県12人。1回目に入れた18人も外した）、萬岳荘45人（恵那山ネットの古い施設案内。公式は宿泊部屋4室）、
長田山荘（公式の本文を読めない）、四季楽園・天狗温泉浅間山荘・黒沢池ヒュッテなど山と溪谷オンライン・業界一覧だけの値、赤岳山荘・赤岳鉱泉・有明荘・三条の湯など出典で食い違う定員、
徳澤園の2027年の日程（Instagram だけ）、元祖室の開始日（まとめサイトだけ）。

  python3 scripts/migrations/fix_huts_muse_2026_11.py && python3 scripts/gen_huts_page.py && python3 scripts/huts_excel.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import huts_checked  # noqa: E402
from huts_booking_extra import BOOKING_EXTRA  # noqa: E402

DAY = '2026-11-25'
BOOK = ['馬場島荘', '馬の背ヒュッテ', '栂池山荘', '白山南竜山荘', '石室山荘', '須走口五合目 山荘菊屋', '宝永山荘', '本八合目 富士山ホテル', '花小屋',
        '須走口五合目 東富士山荘', '七合目行場山荘', '天狗温泉浅間山荘', 'ヒュッテみさやま', '至仏山荘', '苗場山頂ヒュッテ－自然体験交流センター',
        # 2回目（v2）
        '本八合目 富士山ホテル', '須走口八合目 江戸屋（下江戸屋）', '徳沢ロッヂ', '八島山荘', '佐藤小屋', '金峰山小屋', '二の池ヒュッテ', '須走口七合目 大陽館',
        '砂払五合目 吉野屋', '大沢小屋', '雲海荘', '鎌岩館', '御殿場口新六合目 半蔵坊']


def main():
    path = os.path.join(ROOT, 'data', 'huts.json')
    data = json.load(open(path, encoding='utf-8'))
    by = {h['name']: h for h in data['huts']}
    cap = [n for n, c in huts_checked.CAPACITY.items() if c.get('checkedAt') == DAY]
    names = sorted(set(BOOK) | set(cap))
    assert set(names) <= set(by), set(names) - set(by)
    for n in names:
        h = by[n]
        huts_checked.apply(h)
        x = BOOKING_EXTRA.get(n) or {}
        if n in BOOK:
            if x.get('s'):
                h['bookingStart'] = x['s']
                h.pop('bookingStartUnstated', None)
            if x.get('m'):
                h['bookingMethods'] = x['m']
            if x.get('r'):
                h['bookingRequired'] = True
            if x.get('p'):
                h['openText'] = x['p']
                h['periodManual'] = True
            if x.get('t'):
                h['tel'] = x['t']
            if x.get('src'):
                h['bookingSourceUrl'] = x['src']
        print(n, '|', (h.get('capacityFix') or {}).get('value'), '|', h.get('bookingMethods'), '|', h.get('bookingStart'))
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(len(names), '軒')


if __name__ == '__main__':
    main()
