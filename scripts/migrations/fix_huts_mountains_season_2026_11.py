"""山小屋の「対応する山」と営業期間を直す（2026-11-17。運営者の指示「これを参考に直して」＝クラウドの Claude が公式サイトで照らした報告）

1. 対応する山：10月のコースの見直しで、次の小屋がサイトのコースの通過点・登山口になった（YAMAP のモデルコースの通過点で確かめた）。
   別ルート（otherMountains）から「対応する山」（mountainIds）に移す。
   - 木曽殿山荘：空木岳のコース3（伊奈川ダム〜越百山〜南駒ヶ岳〜空木岳の周回。YAMAP 65404 の通過点に「木曽殿山荘」）
   - 越百小屋：空木岳を足す（同じコース3。通過点の越百避難小屋の隣）
   - 硫黄岳山荘：八ヶ岳（赤岳）のコース3（赤岳〜横岳〜硫黄岳の周回。YAMAP 132）
   - 女人堂（金剛堂）・石室山荘・七合目行場山荘：御嶽山のコース2（黒沢口。YAMAP 1514）
   - 天狗温泉浅間山荘：浅間山のコース3の登山口（YAMAP 97745「浅間山荘登山口」）
2. 営業期間（huts_checked.SEASON）：仙丈小屋・塩見小屋は公式の営業期間の終わりが10/12（予約サイト・長野県の案内は最後の宿泊日の10/11）。
   雷鳥沢ヒュッテは公式に日付が無く、やまたんと山と溪谷オンラインの一覧で食い違うので注記を添える。
build_huts_from_nagano.py の HUT_MOUNTAINS / HUT_OTHER と huts_checked.py は直してある。build を単独で流さず、data/huts.json の該当の小屋にだけ同じ値を当てる。
何度流しても同じ結果。このあと gen_huts_page.py → huts_excel.py → gen_mountain_pages.py --id （asama・utsugi・yatsugatake・ontakesan を1つずつ）
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import huts_checked  # noqa: E402
from build_huts_from_nagano import HUT_MOUNTAINS, HUT_OTHER  # noqa: E402

MOVE = ['木曽殿山荘', '越百小屋', '硫黄岳山荘', '女人堂（金剛堂）', '石室山荘', '七合目行場山荘', '天狗温泉浅間山荘']
SEASON = ['仙丈小屋', '塩見小屋', '雷鳥沢ヒュッテ']


def main():
    path = os.path.join(ROOT, 'data', 'huts.json')
    data = json.load(open(path, encoding='utf-8'))
    seen = set()
    for h in data['huts']:
        n = h['name']
        if n in MOVE:
            h['mountainIds'] = list(HUT_MOUNTAINS[n])
            h['otherMountains'] = [{'id': m, 'relation': r} for m, r in HUT_OTHER.get(n, [])]
            seen.add(n)
        if n in SEASON:
            huts_checked.apply(h)
            seen.add(n)
    missing = set(MOVE + SEASON) - seen
    if missing:
        sys.exit('見つからない小屋：%s' % sorted(missing))
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('直した小屋', len(seen))


if __name__ == '__main__':
    main()
