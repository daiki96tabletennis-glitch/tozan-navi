"""ピッケルのカード（axe）を、出典で確かめた結果に合わせる（2026-11-12。運営者の指示「実際いるか確かめて」→「条件次第にする」）

add_axe_winter_2026_11.py で冬山装備の月にピッケルのカードを足した57山（前は1枚も無かった山）を、
山小屋の現地情報・警察庁の冬山情報・長野県警・尾瀬保護財団・山と溪谷・ガイドのツアーの持ち物で確かめた（個人の登山記録は使わない）。
確かめた内容は .claude/axe_findings_2026_11.tsv。
- 要る（25山）：「推奨」のまま
- 要らない（4山：北横岳・蔵王山・西吾妻山・安達太良山）：カードを外す
- 条件次第（3山：日光白根山・甲武信ヶ岳・針ノ木岳）：「条件次第」にし、条件を書く
- 確かめられなかった（25山）：「条件次第」にし、一般の注意を書く
前からピッケルのカードがあった15山は変えない。ページの文には出典の名前・「確かめられていない」ことを書かない（運営者の指示・2026-11-12）。何度流しても同じ結果。
このあと add_axe_winter_2026_11.py は流さない（流すと外した4山に戻る。NONE を見て足さないようにした）。
このあと gen_mountain_pages.py --all → gen_recommend_gear.py → gen_line_articles.py（路線別の記事）→ check_pages.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GP = os.path.join(ROOT, 'data', 'gear-data.json')
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'migrations'))
from fix_split_month_gear_2026_11 import variants_attr  # noqa: E402

# 要らない：出典（4山）と、登山記録（2021年11月以降・1山に複数。2026-11-12。運営者の指示「確かめられない山は登山記録を参照しても良い」）
NONE = ['kitayokodake', 'zaosan', 'azuma', 'adatara',
        'nantaisan', 'shirane_gunma', 'kenashiyama', 'kazahariyama', 'enasan', 'keizandake']
# 要る（登山記録で、ピッケルを使った・要ったという記録が続く山）：「推奨」にもどす
NEED = ['takeson', 'bandai', 'jonengatake', 'yakedake', 'chogatake', 'echigokoma', 'naeba']
AXE_R = ('急な雪面・凍結した斜面ではピッケルによる滑落停止技術が必要です。冬季登山に不慣れな場合は経験者との同行をおすすめします。'
         '事前に最新の積雪・凍結情報を確認してください。')
COND = {
    'nikko_shirane': '初冬はストックで歩けることもありますが、急な雪面や凍結した斜面ではピッケルと滑落停止の技術が必要です。出かける前に最新の積雪・凍結情報を確認してください。',
    'kobushigatake': '初冬は軽アイゼンやチェーンスパイクで歩けることが多いですが、残雪期に奥秩父の主脈を縦走するときはピッケルが要ります。出かける前に最新の積雪・凍結情報を確認してください。',
    'harinokidake': '雪渓や急な雪面を歩くときは、ピッケルがあると安全です。出かける前に最新の積雪・凍結情報を確認してください。',
    'shibutsu': '鳩待峠からの往復はアイゼンで歩ける日が多いですが、山の鼻へ下る急な雪の斜面や、風の強い日はピッケルがあると安全です。出かける前に最新の積雪・凍結情報を確認してください。',
    'kurohimesan': 'スノーシューで歩ける日が多いですが、雪が締まっているときの急な下りではピッケルがあると安全です。出かける前に最新の積雪・凍結情報を確認してください。',
    'tairappyo': 'ワカン・スノーシューやアイゼンで歩ける日が多いですが、稜線の雪が固く締まっているときはピッケルがあると安全です。出かける前に最新の積雪・凍結情報を確認してください。',
    'sennokurayama': 'ワカン・スノーシューやアイゼンで歩ける日が多いですが、稜線の雪が固く締まっているときはピッケルがあると安全です。出かける前に最新の積雪・凍結情報を確認してください。',
}
# 記録が足りない（冬山装備の月に登れる記録が少ない・道路の冬期閉鎖など）：一般の注意のまま
UNVERIFIED = ['iwasugesan', 'nakawarayama', 'arikayama', 'arasawadake', 'sukai', 'karisaka', 'shirasunayama', 'takatsuma']
UNVERIFIED_R = ('急な雪面や凍結した斜面を歩くときは、ピッケルと滑落停止の技術が必要です。コースや雪の状態によっては不要なこともあるので、'
                '出かける前に最新の積雪・凍結情報を確認してください。')


def main():
    G = json.load(open(GP, encoding='utf-8'))
    n = {'外した': 0, '条件次第': 0}
    for mid in NONE:
        for mo, cards in G[mid].items():
            k = len(cards)
            cards[:] = [c for c in cards if c['c'] != 'axe']
            n['外した'] += k - len(cards)
    for mid in NEED:
        for cards in G[mid].values():
            for c in cards:
                if c['c'] == 'axe':
                    c['i'] = '推奨'
                    c['r'] = AXE_R
    for mid, r in list(COND.items()) + [(x, UNVERIFIED_R) for x in UNVERIFIED]:
        hit = 0
        for cards in G[mid].values():
            for c in cards:
                if c['c'] == 'axe':
                    c['i'] = '条件次第'
                    c['r'] = r
                    hit += 1
        assert hit, mid
        n['条件次第'] += hit
    with open(GP, 'w', encoding='utf-8') as f:
        json.dump(G, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(n)
    pages = glob.glob(os.path.join(ROOT, 'articles/*/index.html')) + glob.glob(os.path.join(ROOT, 'search/*/index.html'))
    for p in sorted(pages):
        s = open(p, encoding='utf-8').read()
        if '<!-- generated: scripts/gen_line_articles' in s:
            continue
        hit = []
        for mid in sorted(set(re.findall(r'data-gear-mid="([a-z0-9_-]+)"', s))):
            if mid not in G:
                continue
            pat = re.compile(r'(data-gear-mid="' + mid + r'"[^>]*?data-gear-variants=")([^"]*)(")')
            new = pat.sub(lambda m: m.group(1) + variants_attr(G[mid]) + m.group(3), s)
            if new != s:
                hit.append(mid)
                s = new
        if hit:
            open(p, 'w', encoding='utf-8').write(s)
            print('記事の写し', os.path.relpath(p, ROOT), ' '.join(hit))


if __name__ == '__main__':
    main()
