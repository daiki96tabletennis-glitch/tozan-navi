"""鎖場の多いコース・有名な鎖場のあるコースに routes[].chains を付ける（2026-11-10。運営者の指示）

対象は「鎖場が多い・続く」か「名前の付いた有名な鎖場がある」コース。1〜2か所の短い鎖だけのコースは入れない。
根拠は、自治体・観光庁・山と溪谷社（ヤマケイオンラインの山の案内・記事、YAMAP の山の紹介文）・登山ガイドのサイト
（日本アルプス登山ガイド japanesealps.net、ニッポン旅マガジン、The Japan Alps）の本文で、鎖場が多い・続く・名前が
書いてあることを確かめたものだけ（2026-11-10。個人の登山記録は使わない）。道筋が出典のコースと同じコースだけに付ける。

確かめたが入れなかった山（出典の本文で「多い・続く」とまで言えなかった）：瑞牆山（標準のコースははしご・ロープ）、
十二ヶ岳（ロープが中心）、苗場山の小赤沢（「途中鎖場なども」）、有明山、岩殿山・鋸岳（個人の記録しか見つからない）、
伊豆ヶ岳（男坂は落石で通行自粛）。赤岳の地蔵尾根の往復・奥穂高岳の西穂高岳からの縦走は、出典の区間を通るか確かめられず外した。

chains = {spots: 鎖場の場所・名前, source, sourceUrl, lastVerified}
何度流しても同じ結果。コースを変えたら見直す（check_pages.py セクション23）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
DAY = '2026-11-10'

JA = ('日本アルプス登山ガイド', 'https://www.japanesealps.net')


def c(spots, source, url):
    return {'spots': spots, 'source': source, 'sourceUrl': url, 'lastVerified': DAY}


# (山ID, コース名の頭) → chains
CHAINS = {
    ('myogisan', '妙義神社〜大の字〜大のぞき'): c('奥の院・大のぞき下の三連の鎖場', '日本アルプス登山ガイド「妙義山 白雲山コース」', JA[1] + '/200moutains/myougisan/hakuunsan/'),
    ('myogisan', '妙義神社〜相馬岳〜鷹戻し'): c('奥の院・大のぞき下の三連の鎖場など', '日本アルプス登山ガイド「妙義山 白雲山コース」', JA[1] + '/200moutains/myougisan/hakuunsan/'),
    ('ryokami', '上落合橋〜八丁峠'): c('八丁尾根（クサリ場の連続）', 'YAMAP「両神山」の紹介文（山と溪谷社）', 'https://yamap.com/mountains/24'),
    ('tsurugi', '室堂〜雷鳥沢〜剱沢'): c('カニのタテバイ・カニのヨコバイ', 'ヤマケイオンライン「剱岳」（山と溪谷社）', 'https://www.yamakei-online.com/yamanavi/yama.php?yama_id=496'),
    ('tsurugi', '室堂〜一ノ越〜立山'): c('カニのタテバイ・カニのヨコバイ', 'ヤマケイオンライン「剱岳」（山と溪谷社）', 'https://www.yamakei-online.com/yamanavi/yama.php?yama_id=496'),
    ('takatsuma', '戸隠奥社〜戸隠山'): c('胸突岩などの鎖場・蟻の塔渡り', 'ニッポン旅マガジン「戸隠山『蟻の塔渡り』とは」', 'https://tabi-mag.jp/arinotowatari/'),
    ('tanigawa', '土合口〜西黒尾根'): c('西黒尾根の岩稜（3か所の鎖場が続く）', '日本アルプス登山ガイド「谷川岳 西黒尾根コース」', JA[1] + '/100moutains/tanigawadake/nishikuroone/'),
    ('tanigawa', '西黒尾根〜谷川岳〜一ノ倉岳'): c('西黒尾根の岩稜（3か所の鎖場が続く）', '日本アルプス登山ガイド「谷川岳 西黒尾根コース」', JA[1] + '/100moutains/tanigawadake/nishikuroone/'),
    ('komagatake', '竹宇駒ヶ岳神社〜黒戸尾根'): c('黒戸尾根のはしご・鎖', '観光庁「甲斐駒ヶ岳」（地域観光資源の多言語解説文）', 'https://www.mlit.go.jp/tagengo-db/en/R6-00201.html'),
    ('arasawadake', '銀山平〜前山〜前嵓'): c('前嵓の鉄鎖', 'ヤマケイオンライン「荒沢岳」（山と溪谷社）', 'https://www.yamakei-online.com/yamanavi/yama.php?yama_id=307'),
    ('arasawadake', '裏越後三山'): c('前嵓の鉄鎖', 'ヤマケイオンライン「荒沢岳」（山と溪谷社）', 'https://www.yamakei-online.com/yamanavi/yama.php?yama_id=307'),
    ('takeson', '武尊神社〜武尊沢'): c('武尊神社からのルートの上部（鎖場が連続）', '日本アルプス登山ガイド「武尊山」', JA[1] + '/100moutains/hotakayama/'),
    ('yari', '上高地〜槍沢'): c('山頂の穂先（鎖とはしご）', '日本アルプス登山ガイド「槍ヶ岳 槍沢コース」', JA[1] + '/north/yarigatake/yarisawa/'),
    ('yari', '新穂高温泉〜槍平'): c('山頂の穂先（鎖とはしご）', '日本アルプス登山ガイド「槍ヶ岳 槍沢コース」', JA[1] + '/north/yarigatake/yarisawa/'),
    ('yari', '表銀座'): c('山頂の穂先（鎖とはしご）', '日本アルプス登山ガイド「槍ヶ岳 槍沢コース」', JA[1] + '/north/yarigatake/yarisawa/'),
    ('hotaka', '上高地〜涸沢〜穂高岳山荘'): c('穂高岳山荘から上のクサリと2連の鉄ハシゴ', 'The Japan Alps「穂高岳 難所詳細ルートガイド（涸沢ルート）」', 'https://thejapanalps.com/wp-content/uploads/2021/12/okuhotaka-dake.pdf'),
    ('hotaka', '上高地〜岳沢〜前穂高岳'): c('穂高岳山荘から上のクサリと2連の鉄ハシゴ', 'The Japan Alps「穂高岳 難所詳細ルートガイド（涸沢ルート）」', 'https://thejapanalps.com/wp-content/uploads/2021/12/okuhotaka-dake.pdf'),
    ('sukai', '銀山平〜庚申山〜鋸山〜皇海山〜六林班峠'): c('庚申山〜鋸山（ハシゴと鎖場の連続）', '山と溪谷オンライン「日帰り百名山の最難関・皇海山クラシックルート」', 'https://www.yamakei-online.com/yama-ya/detail.php?id=5316'),
    ('sukai', '銀山平〜庚申山〜鋸山〜皇海山（往復）'): c('庚申山〜鋸山（ハシゴと鎖場の連続）', '山と溪谷オンライン「日帰り百名山の最難関・皇海山クラシックルート」', 'https://www.yamakei-online.com/yama-ya/detail.php?id=5316'),
    ('kentoku', '徳和〜国師ヶ原'): c('籏立岩・山頂直下の一枚岩', '日本アルプス登山ガイド「乾徳山 徳和コース」', JA[1] + '/200moutains/kentokuzan/tokuwa_course/'),
    ('kentoku', '徳和〜乾徳山〜道満山'): c('籏立岩・山頂直下の一枚岩', '日本アルプス登山ガイド「乾徳山 徳和コース」', JA[1] + '/200moutains/kentokuzan/tokuwa_course/'),
    ('kentoku', '大平高原〜乾徳山'): c('籏立岩・山頂直下の一枚岩', '日本アルプス登山ガイド「乾徳山 徳和コース」', JA[1] + '/200moutains/kentokuzan/tokuwa_course/'),
    ('myoko', '燕温泉〜北地獄谷'): c('九合目の鎖場（貝摺ノ嶮）', '日本アルプス登山ガイド「妙高山 燕登山道コース」', JA[1] + '/100moutains/myokosan/tsubame_tozando/'),
    ('myoko', '妙高高原スカイケーブル'): c('九合目の鎖場（貝摺ノ嶮）', '日本アルプス登山ガイド「妙高山 燕登山道コース」', JA[1] + '/100moutains/myokosan/tsubame_tozando/'),
    ('myoko', '燕温泉〜天狗堂〜妙高山〜長助池'): c('九合目の鎖場（貝摺ノ嶮）', '日本アルプス登山ガイド「妙高山 燕登山道コース」', JA[1] + '/100moutains/myokosan/tsubame_tozando/'),
    ('iyogatake', '平群天神社〜伊予ヶ岳 南峰'): c('山頂への鎖場', 'YAMAP モデルコース「伊予ヶ岳」の説明', 'https://yamap.com/model-courses/58'),
    ('iyogatake', '平群天神社〜伊予ヶ岳〜富山〜岩井駅'): c('山頂への鎖場', 'YAMAP モデルコース「伊予ヶ岳」の説明', 'https://yamap.com/model-courses/58'),
    ('iyogatake', '平群天神社〜伊予ヶ岳〜富山（周回）'): c('山頂への鎖場', 'YAMAP モデルコース「伊予ヶ岳」の説明', 'https://yamap.com/model-courses/58'),
    ('yatsugatake', '美濃戸〜行者小屋〜地蔵尾根'): c('赤岳の南峰〜竜頭峰の岩稜（鎖場が続く）', '山と溪谷オンライン「南八ヶ岳の岩稜を一気に縦走。赤岳〜横岳〜硫黄岳」', 'https://www.yamakei-online.com/yama-ya/detail.php?id=2658'),
    ('yatsugatake', '美濃戸〜赤岳〜横岳'): c('赤岳の南峰〜竜頭峰・横岳（鎖やハシゴが連続）', '山と溪谷オンライン「南八ヶ岳の岩稜を一気に縦走。赤岳〜横岳〜硫黄岳」', 'https://www.yamakei-online.com/yama-ya/detail.php?id=2658'),
}


def main():
    M = json.load(open(PATH, encoding='utf-8'))
    by = {m['id']: m for m in M}
    used = set()
    for m in M:
        for r in m.get('routes') or []:
            hit = [k for k in CHAINS if k[0] == m['id'] and r['name'].startswith(k[1])]
            assert len(hit) <= 1, (m['id'], r['name'], hit)
            if hit:
                r['chains'] = CHAINS[hit[0]]
                used.add(hit[0])
            else:
                r.pop('chains', None)
    missing = set(CHAINS) - used
    if missing:
        raise SystemExit('コースが見つからない：%s' % sorted(missing))
    json.dump(M, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    ms = sorted({k[0] for k in CHAINS})
    print('鎖場を付けたコース：%d（%d山）%s' % (len(CHAINS), len(ms), ' '.join(by[i]['name'] for i in ms)))


if __name__ == '__main__':
    main()
