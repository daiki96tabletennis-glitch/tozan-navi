"""コースごとの技術的難易度（各県の「山のグレーディング」）を routes[].tech に入れる（2026-11-04）

運営者の指示：鎖場や岩場が多く技術の難しい山・コースが分かるラベルを付ける。
- 根拠は各県が公表している「山のグレーディング」の技術的難易度（A〜E）だけ。
  サイトのコースと、グレーディングのルートの登山口と道筋が同じものだけに付ける。
  サイトのコースが、評価のある区間をすべて含むとき（例：八峰キレットを通る縦走）は、
  含む区間のいちばん高い評価を付ける（`basis: "contains"`。評価はその区間の値で、コース全体の値ではない）。
- 道筋が違う・一部しか重ならないコースには付けない（推測で付けない）。
- ラベル：C＝「難所あり」（はしご・鎖場・雪渓・渡渉など、ミスすると転落・滑落の危険がある場所）、
  D・E＝「岩場の難所」（厳しい岩稜・手を使う岩場が続く）。A・B はラベルを出さない（値は残す）。
何度流しても同じ結果になる（前の tech を置き換える）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKED = '2026-11-04'

SRC = {
    'nagano': ('信州 山のグレーディング一覧表（長野県・2026年）', 'https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/gure-dexingu.html'),
    'hyaku': ('日本百名山のグレーディング一覧表（長野県ほか）', 'https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/gure-dexingu.html'),
    'yamanashi': ('山梨 山のグレーディング（山梨県）', 'https://www.pref.yamanashi.jp/kankou-sgn/shintyaku/grading.html'),
    'niigata': ('新潟 山のグレーディング（新潟県）', 'https://www.pref.niigata.lg.jp/site/opendata/1356812341916.html'),
    'shizuoka': ('静岡県山のグレーディング（静岡県）', 'https://www.pref.shizuoka.jp/kankosports/kanko/kankoseisaku/1040866/1052256.html'),
    'gunma': ('群馬県 登山ルート別 難易度グレーディング一覧表（群馬県・令和7年4月改定）', 'https://www.pref.gunma.jp/01/g3500213.html'),
    'gifu': ('岐阜県山のグレーディング（岐阜県）', 'https://www.pref.gifu.lg.jp/page/14382.html'),
}

# 山ID: {コースの番号（0から）: (評価, 出典, グレーディングのルート名, 'same' か 'contains', 補足)}
G = {
    'fuji': {0: ('B', 'shizuoka', '富士山(富士宮口)', 'same', ''), 1: ('B', 'yamanashi', '富士山（スバルライン五合目）', 'same', ''), 2: ('B', 'shizuoka', '富士山(須走口)', 'same', '')},
    'kumotori': {0: ('B', 'hyaku', '雲取山（鴨沢）', 'same', '')},
    'amagi': {0: ('B', 'shizuoka', '天城山(天城高原ゴルフ場)', 'same', '')},
    'okutama': {0: ('A', 'yamanashi', '大菩薩嶺（ロッジ長兵衛）＜大菩薩峠・唐松尾根＞', 'same', '')},
    'kobushigatake': {1: ('B', 'nagano', '甲武信ヶ岳（毛木平）＜甲武信ヶ岳→十文字峠＞', 'same', ''), 2: ('B', 'yamanashi', '甲武信ヶ岳（西沢渓谷入口）＜徳ちゃん新道＞', 'same', '')},
    'mizugaki': {0: ('C', 'yamanashi', '瑞牆山（瑞牆山荘）', 'same', ''), 2: ('C', 'yamanashi', '瑞牆山（瑞牆山荘）・金峰山（瑞牆山荘）', 'contains', '')},
    'kinpusan': {0: ('A', 'yamanashi', '金峰山（大弛峠）', 'same', ''), 1: ('B', 'nagano', '金峰山（廻り目平）', 'same', ''), 2: ('C', 'yamanashi', '金峰山（瑞牆山荘）', 'same', '')},
    'houou': {0: ('B', 'yamanashi', '鳳凰山（夜叉神峠）', 'same', ''), 1: ('C', 'yamanashi', '鳳凰山（青木鉱泉）＜地蔵岳・中道＞', 'same', '')},
    'nantaisan': {0: ('B', 'hyaku', '男体山（中宮祠）', 'same', '')},
    'kitadake': {0: ('B', 'yamanashi', '北岳（広河原）＜草すべり＞', 'same', ''), 1: ('C', 'hyaku', '間ノ岳（広河原）＜草すべり＞', 'same', ''), 2: ('C', 'yamanashi', '北岳→農鳥岳（広河原・奈良田）', 'same', '')},
    'yatsugatake': {0: ('C', 'nagano', '赤岳（美濃戸）＜北沢・地蔵尾根＞／赤岳（美濃戸）＜南沢・文三郎＞', 'contains', ''), 1: ('C', 'nagano', '赤岳（美濃戸）＜北沢・地蔵尾根＞／赤岳（美濃戸）＜南沢・文三郎＞', 'contains', ''), 2: ('C', 'nagano', '赤岳・横岳・硫黄（美濃戸）', 'same', '')},
    'keirisan': {0: ('B', 'nagano', '蓼科山（七合目登山口）', 'same', '')},
    'asama': {1: ('A', 'nagano', '黒斑山（車坂峠）', 'same', ''), 2: ('B', 'nagano', '前掛山（浅間登山口）', 'same', '')},
    'tanigawa': {0: ('B', 'gunma', '谷川岳＜天神尾根＞', 'same', ''), 1: ('C', 'gunma', '谷川岳＜西黒尾根＞', 'same', ''), 2: ('C', 'gunma', '谷川岳＜西黒尾根＞', 'contains', '')},
    'nikko_shirane': {0: ('B', 'gunma', '日光白根山＜丸沼＞', 'same', ''), 1: ('B', 'gunma', '日光白根山＜菅沼＞', 'same', '')},
    'takeson': {0: ('C', 'gunma', '剣ヶ峰山→武尊山', 'same', '')},
    'komagatake': {0: ('C', 'nagano', '甲斐駒ヶ岳（北沢峠）＜仙水峠・双児山＞', 'same', ''), 1: ('D', 'yamanashi', '甲斐駒ヶ岳（竹宇駒ヶ岳神社）', 'same', '黒戸尾根')},
    'senjogatake': {0: ('C', 'yamanashi', '仙丈ヶ岳（北沢峠）＜小仙丈ヶ岳＞', 'same', '')},
    'shirouma': {0: ('B', 'nagano', '白馬岳（栂池）', 'same', ''), 1: ('C', 'nagano', '白馬岳（猿倉）', 'same', '大雪渓')},
    'norikura': {0: ('B', 'hyaku', '乗鞍岳（畳平）', 'same', '')},
    'tateyama': {1: ('B', 'hyaku', '雄山→別山（室堂ターミナル）', 'same', '')},
    'tsurugi': {0: ('E', 'hyaku', '剱岳（室堂ターミナル）＜別山尾根＞', 'same', 'カニのタテバイ・ヨコバイ'), 1: ('E', 'hyaku', '剱岳（馬場島）＜早月尾根＞', 'same', ''), 2: ('E', 'hyaku', '剱岳（室堂ターミナル）＜別山尾根＞', 'contains', '')},
    'yari': {0: ('C', 'nagano', '槍ヶ岳（上高地）', 'same', ''), 1: ('C', 'hyaku', '槍ヶ岳（新穂高）＜飛騨乗越＞', 'same', ''), 2: ('C', 'nagano', '表銀座（中房温泉・上高地）', 'same', '')},
    'hotaka': {0: ('C', 'nagano', '奥穂高岳（上高地）＜涸沢＞', 'same', ''), 1: ('D', 'nagano', '前穂高岳（上高地）＜重太郎新道＞', 'contains', ''),
               2: ('D', 'gifu', '西穂高岳（新穂高ロープウェイ）', 'contains', '西穂高岳まででD。西穂高岳〜奥穂高岳（ジャンダルム）の区間だけの評価は無い')},
    'yakedake': {0: ('B', 'nagano', '焼岳（新中ノ湯登山口）', 'same', '')},
    'kashimayari': {0: ('B', 'nagano', '鹿島槍ヶ岳（扇沢）', 'same', ''), 1: ('C', 'nagano', '鹿島槍ヶ岳（大谷原）', 'same', ''), 2: ('D', 'nagano', '八峰キレット（アルプス平駅・大谷原）', 'contains', '八峰キレット')},
    'arafune': {0: ('B', 'gunma', '荒船山（内山峠）', 'same', '')},
    'kazahariyama': {0: ('B', 'nagano', '御座山（栗生登山口）', 'same', '')},
    'iwasugesan': {1: ('B', 'nagano', '岩菅山（岩菅山登山口）', 'same', '')},
    'iizunasan': {0: ('B', 'nagano', '飯縄山（一ノ鳥居苑地）', 'same', '')},
    'kenashiyama': {0: ('B', 'shizuoka', '毛無山(麓)', 'same', '')},
    'nanaitsurasan': {0: ('A', 'yamanashi', '七面山（羽衣）', 'same', '')},
    'arasawadake': {0: ('D', 'niigata', '荒沢岳（銀山平登山口）', 'same', '前嵓'), 1: ('D', 'niigata', '荒沢岳（銀山平登山口）', 'contains', '前嵓')},
    'yarigatake2': {0: ('D', 'yamanashi', '笊ヶ岳（老平）', 'same', ''), 2: ('D', 'shizuoka', '笊ヶ岳(椹島)', 'same', '')},
    'gakedake': {0: ('C', 'nagano', '餓鬼岳（白沢登山口）', 'same', ''), 1: ('C', 'nagano', '餓鬼岳（白沢登山口）', 'contains', '')},
    'arikayama': {1: ('C', 'nagano', '有明山（中房）', 'same', '')},
    'keizandake': {0: ('A', 'nagano', '経ヶ岳（仲仙寺）', 'same', '')},
    'echigokoma': {0: ('B', 'niigata', '越後駒ヶ岳（枝折峠登山口）', 'same', '')},
    'hiragadake': {0: ('D', 'gunma', '平ヶ岳（鷹ノ巣駐車場）', 'same', '')},
    'naeba': {0: ('B', 'niigata', '苗場山（祓川駐車場）＜祓川ルート＞', 'same', ''), 1: ('B', 'nagano', '苗場山（小赤沢三合目）', 'same', '')},
    'amakazari': {0: ('C', 'nagano', '雨飾山（小谷温泉）', 'same', ''), 1: ('B', 'niigata', '雨飾山（雨飾温泉駐車場）', 'same', '')},
    'hiuchi': {0: ('B', 'niigata', '火打山（笹ヶ峰登山口）', 'same', '')},
    'takatsuma': {0: ('D', 'nagano', '高妻山（戸隠キャンプ場）（周回）', 'same', ''), 2: ('D', 'nagano', '戸隠山（奥社駐車場・戸隠キャンプ場）', 'contains', '戸隠山の蟻の塔渡り')},
    'kasagatake': {0: ('C', 'hyaku', '笠ヶ岳（新穂高）＜笠新道＞', 'same', ''), 1: ('C', 'hyaku', '笠ヶ岳（新穂高）＜笠新道・小池新道＞', 'same', '')},
    'ontakesan': {0: ('B', 'nagano', '御嶽山（田の原）', 'same', ''), 1: ('B', 'nagano', '御嶽山（飯森高原駅）', 'same', ''), 2: ('B', 'gifu', '御嶽山（濁河）', 'same', '')},
    'goryudake': {0: ('C', 'nagano', '五竜岳（アルプス平駅）', 'same', ''), 1: ('C', 'nagano', '唐松・五竜（八方池山荘・アルプス平駅）', 'same', '')},
    'sukai': {0: ('D', 'gunma', '皇海山（銀山平）', 'same', ''), 1: ('D', 'gunma', '皇海山（銀山平）', 'contains', '')},
    'kisokoma': {0: ('B', 'nagano', '木曽駒ヶ岳（千畳敷）', 'same', '')},
    'utsukushigahara': {2: ('B', 'nagano', '美ヶ原（三城牧場）', 'same', '')},
    'karamatsu': {0: ('B', 'nagano', '唐松岳（八方池山荘）', 'same', ''), 1: ('C', 'nagano', '唐松・五竜（八方池山荘・アルプス平駅）', 'same', ''), 2: ('D', 'nagano', '不帰キレット（猿倉・八方池山荘）', 'same', '不帰ノ嶮')},
    'utsugi': {0: ('C', 'nagano', '空木岳（駒ヶ根高原）', 'same', ''), 1: ('C', 'nagano', '木曽駒→空木（千畳敷・駒ヶ根高原）', 'same', ''), 2: ('D', 'nagano', '空木→越百（今朝沢橋）', 'same', '')},
    'enasan': {0: ('B', 'nagano', '恵那山（峰越林道ゲート）＜広河原登山口＞', 'same', ''), 1: ('B', 'hyaku', '恵那山（神坂峠登山口）', 'same', ''), 2: ('B', 'hyaku', '恵那山（前宮登山口）', 'same', '')},
    'shiomidake': {0: ('D', 'nagano', '塩見岳（鳥倉）', 'same', ''), 1: ('D', 'nagano', '塩見岳（鳥倉）', 'contains', '')},
    'arakawadake': {1: ('D', 'shizuoka', '千枚・荒川・赤石岳（椹島）（周回）', 'same', '')},
    'akaisidake': {0: ('D', 'shizuoka', '赤石岳(椹島)', 'same', ''), 1: ('D', 'shizuoka', '千枚・荒川・赤石岳（椹島）（周回）', 'same', '')},
    'hijiridade': {0: ('C', 'shizuoka', '聖岳(聖沢)', 'same', ''), 1: ('D', 'shizuoka', '赤石岳・聖岳(椹島・聖沢)', 'same', ''), 2: ('D', 'shizuoka', '赤石岳・聖岳(椹島・聖沢)', 'contains', '')},
    'terkari': {0: ('B', 'nagano', '光岳（易老渡）', 'same', ''), 1: ('D', 'hyaku', '茶臼岳・光岳(畑薙大吊橋)', 'same', '')},
    'yakushidake': {0: ('B', 'hyaku', '薬師岳（折立）', 'same', '')},
    'kurobegorodam': {0: ('B', 'hyaku', '北ノ俣岳・黒部五郎岳（折立）', 'same', ''), 1: ('C', 'hyaku', '黒部五郎岳（飛越トンネル）', 'same', '')},
    'ainodake': {0: ('C', 'hyaku', '間ノ岳（広河原）＜草すべり＞', 'same', ''), 1: ('C', 'yamanashi', '北岳→農鳥岳（広河原・奈良田）', 'same', ''), 2: ('C', 'yamanashi', '北岳→農鳥岳（広河原・奈良田）', 'same', '逆向き')},
    'noutori': {1: ('C', 'yamanashi', '北岳→農鳥岳（広河原・奈良田）', 'same', '')},
    'hakusan': {2: ('C', 'gifu', '白山（大白川温泉）', 'same', '')},
    'minamikomagatake': {0: ('D', 'nagano', '南駒ヶ岳（今朝沢橋）', 'same', ''), 1: ('D', 'nagano', '南駒ヶ岳（今朝沢橋）', 'contains', '')},
    'chogatake': {1: ('B', 'nagano', '蝶ヶ岳（三股）', 'same', '')},
    'tsubakurodake': {0: ('B', 'nagano', '燕岳（中房温泉）', 'same', '')},
    'harinokidake': {0: ('B', 'nagano', '針ノ木岳（扇沢）', 'same', '')},
    'eboshidake_kita': {0: ('C', 'nagano', '烏帽子岳（高瀬ダム）＜ブナ立尾根＞', 'same', ''), 1: ('C', 'nagano', '烏帽子岳（高瀬ダム）＜ブナ立尾根＞', 'contains', '')},
    'tengudake': {0: ('B', 'nagano', '天狗岳（渋ノ湯）', 'same', '')},
    'kitayokodake': {0: ('A', 'nagano', '北横岳（ロープウェイ）', 'same', '')},
    'nishihotaka': {0: ('D', 'gifu', '西穂高岳（新穂高ロープウェイ）', 'same', ''), 1: ('C', 'gifu', '独標（新穂高ロープウェイ）', 'same', ''), 2: ('D', 'nagano', '西穂高岳（上高地）', 'same', '')},
    'kentoku': {0: ('C', 'yamanashi', '乾徳山（徳和駐車場）＜銀晶水＞', 'same', ''), 1: ('C', 'yamanashi', '乾徳山（徳和駐車場）＜銀晶水＞', 'contains', '')},
    'kayagatake': {0: ('B', 'yamanashi', '茅ヶ岳（深田公園駐車場）', 'same', '')},
}


# グレーディングに無いコースで、自治体・警察の公式の案内に岩場・鎖場の危険が書いてあるもの（評価の文字は無い）
# level: hard＝「岩場の難所」（上級者向け・大変危険と書いてある）／caution＝「難所あり」
OFFICIAL = {
    'myogisan': {i: ('hard', '群馬県（自然環境課）「妙義山」', 'https://www.pref.gunma.jp/01/e2310245.html',
                     '中間道から上の白雲山・金洞山のコースは「険しい岩場が多くあり大変危険」で、初心者は登らないよう呼びかけている') for i in (0, 1, 2)},
    'ryokami': {1: ('caution', '埼玉県警察「両神山・山岳遭難ハザードマップ」', 'https://www.police.pref.saitama.lg.jp/documents/10285/ryoukami.pdf',
                    '八丁尾根の岩稜帯。両神山は鎖場や急斜面での転落・滑落による遭難が多い')},
}


def main():
    path = os.path.join(ROOT, 'data/mountains.json')
    ms = json.load(open(path))
    by = {m['id']: m for m in ms}
    n = 0
    for mid, rs in G.items():
        m = by.get(mid)
        if not m:
            raise SystemExit('山が無い: ' + mid)
        routes = m.get('routes') or []
        for r in routes:
            r.pop('tech', None)
        for i, (grade, src, gname, basis, note) in rs.items():
            if i >= len(routes):
                raise SystemExit('コースが無い: %s %d' % (mid, i))
            label, url = SRC[src]
            t = {'grade': grade, 'source': label, 'sourceUrl': url, 'gradedRoute': gname, 'basis': basis, 'lastVerified': CHECKED}
            if note:
                t['note'] = note
            routes[i]['tech'] = t
            n += 1
    for mid, rs in OFFICIAL.items():
        routes = by[mid].get('routes') or []
        for r in routes:
            r.pop('tech', None)
        for i, (level, label, url, note) in rs.items():
            routes[i]['tech'] = {'grade': None, 'level': level, 'source': label, 'sourceUrl': url, 'basis': 'official', 'note': note, 'lastVerified': CHECKED}
            n += 1
    with open(path, 'w') as f:
        json.dump(ms, f, ensure_ascii=False, indent=2)  # 前のファイルと同じく最後に改行を付けない
    print('コースに評価を入れた:', n)


if __name__ == '__main__':
    main()
