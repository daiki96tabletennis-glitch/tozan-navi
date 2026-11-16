"""冬山装備の山の、登山口への道路の冬期閉鎖を足す（2026-11-17。運営者の指示「冬登山の山選び診断」の準備）
冬の山選び診断（/find/winter/）で、冬山装備の月に日帰りで行ける山の候補（19山）について、冬に登山口まで行けるかを公式の情報で確かめた。
確かめられた閉鎖だけを annualItems の closure に足す（日向山・白砂山と同じ書き方。装備カレンダーは変えない＝登山道の閉鎖ではないため）。
  - 那須岳：主要地方道 那須高原線 大丸温泉〜峠の茶屋登山口園地 2026-12-14 11時〜2027-03-26 11時（3/12 からロープウェイ山麓駅まで解除）
    栃木県「通行規制に関する情報」（更新日 2026-10-20）
  - 磐梯山：磐梯山ゴールドライン（八方台登山口がある）2026-11-13 17時から。解除は令和9年4月下旬頃の予定（福島県 2026-11-13 更新）
  - 蔵王山：蔵王エコーライン（澄川スキー場入口〜山形県境 8.9km）の冬期閉鎖。2024年は11/5 17時から 2025年4/25 11時まで（宮城県大河原土木事務所）。
    今冬の日付は未発表なので期間なし（ページには出ず、出典の見張りと診断の判定だけに使う）
確かめられなかった山（冬の登山口までの道路・バスの公式の情報が見つからない）は足さない。一覧は CLAUDE.md の「冬の山選び診断」。
何度流しても同じ結果。このあと gen_mountain_pages.py --id nasu bandai zaosan → check_pages.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MP = os.path.join(ROOT, 'data', 'mountains.json')
DAY = '2026-11-17'

CLOSURES = {
    'nasu': {
        'kind': 'closure', 'label': '県道 那須高原線の冬期通行止め（大丸温泉〜峠の茶屋。峠の茶屋へ車で行けない）',
        'validFrom': '2026-12-14', 'validTo': '2027-03-26', 'seasonYear': '2026〜27',
        'sourceUrl': 'https://www.pref.tochigi.lg.jp/h57/system/desaki/desaki/tusukoukisei/zyuutai7.html', 'lastVerified': DAY,
        'note': '12/14 11時〜3/26 11時の予定。3/12からロープウェイ山麓駅までは通れる',
    },
    'bandai': {
        'kind': 'closure', 'label': '磐梯山ゴールドラインの冬期通行止め（八方台へ車で行けない）',
        'validFrom': '2026-11-13', 'validTo': None, 'seasonYear': '2026〜27',
        'sourceUrl': 'https://www.pref.fukushima.lg.jp/sec/41351a/sv-gl-ll-closed-for-winter.html', 'lastVerified': DAY,
        'note': '11/13 17時から。解除は2027年4月下旬ごろの予定', 'needsVerification': True,
    },
    'zaosan': {
        'kind': 'closure', 'label': '蔵王エコーラインの冬期閉鎖（刈田岳へ車で行けない）',
        'validFrom': None, 'validTo': None, 'seasonYear': None,
        'sourceUrl': 'https://www.pref.miyagi.jp/documents/35909/r7zaoecholine.pdf', 'lastVerified': DAY,
        'note': '2024年は11月5日17時から2025年4月25日11時まで（澄川スキー場入口〜山形県境）。今冬の日付は未発表', 'needsVerification': True,
    },
}


def main():
    M = json.load(open(MP, encoding='utf-8'))
    by = {m['id']: m for m in M}
    changed = []
    for mid, item in CLOSURES.items():
        m = by[mid]
        old = m.get('annualItems') or []
        its = [a for a in old if a.get('label') != item['label']]
        its.append(dict(item))
        if its != old:
            m['annualItems'] = its
            m['mountainUpdated'] = DAY
            changed.append(mid)
    json.dump(M, open(MP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('冬期閉鎖を足した山：', ' '.join(changed) or 'なし（同じ内容）')


if __name__ == '__main__':
    main()
