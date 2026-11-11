"""岩場が有名なコース・岩場の多いコースに routes[].rocks を付け、絞り込みの「岩場」（vibes の rock）をそろえる
（2026-11-11。運営者の指示「岩場が有名なコースがある山や岩場がたくさんある山は岩のアイコンでラベル付け。フィルターの岩場も同じ山にする」）

対象は、コースに「岩場・岩稜が続く」「岩峰・岩塔・奇岩が並ぶ」と書かれたもの、または名前の付いた有名な岩（五丈岩・オベリスクなど）を通るもの。
根拠は鎖場と同じ決まり：YAMAP の山の紹介文（山と溪谷社）・ヤマケイオンラインの山の案内・登山ガイドのサイトの本文で確かめたものだけ
（個人の登山記録は使わない）。道筋が出典の区間を通るコースだけに付ける。

鎖場のコース（routes[].chains。add_route_chains_2026_11.py）も岩場の山に数える（鎖場は岩場にあるため）。
そのコースには rocks を重ねて付けない（ページで「鎖場」と「岩場」が並ばないように）。

山の vibes の rock は「rocks か chains のコースがある山」と同じにする（トップの絞り込み・山選び診断・登山タイプ診断が使う）。

確かめて入れなかった山（出典の本文で岩場とまで言えない・個人の記録しか無い）：富士山、
北岳（八本歯のコルのはしごはサイトのコースが通るか確かめられない）、那須岳・大岳山・十二ヶ岳・破風山・古賀志山・二子山・官ノ倉山・
岩殿山・鋸岳（ガイドのサイト・山と溪谷社の本文が見つからない）・高川山・黒姫山・有明山・飯豊山（公式のページが読めない）・塔ノ岳・焼岳・雨飾山・苗場山・安達太良山・日光白根山・至仏山・
針ノ木岳・野口五郎岳・餓鬼岳・棒ノ折山（白谷沢は谷の岩壁）・荒船山（艫岩は展望の崖）・幕山・三ツ峠山（岩壁はクライミングの練習場）・
御岳山（ロックガーデンは沢沿いのなだらかな道）・鋸山（地獄のぞきは展望の岩）・伊豆ヶ岳（男坂は通行自粛）。

rocks = {spots, source, sourceUrl, lastVerified}
何度流しても同じ結果。コースを変えたら見直す（check_pages.py セクション24）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
DAY = '2026-11-11'


def c(spots, source, url):
    return {'spots': spots, 'source': source, 'sourceUrl': url, 'lastVerified': DAY}


def ym(name, num):
    return ('YAMAP「%s」の紹介文（山と溪谷社）' % name, 'https://yamap.com/mountains/%d' % num)


TSUKUBA = c('白雲橋・おたつ石コースの奇岩の道と、女体山からの岩場', *ym('筑波山', 90))
MIZUGAKI = c('花崗岩の岩峰が林立し、岩塔の根元を縫って登る', *ym('瑞牆山', 177))
AKADAKE = c('森林限界から上はすべて岩場', *ym('赤岳', 101))
KINTOKI = c('山頂周辺は岩場混じりの急な斜面', *ym('金時山', 91))
OGURA = c('岩峰になった山頂部', *ym('御座山', 18))
TATESHINA = c('大きな岩塊が折り重なる山頂', *ym('蓼科山', 149))
SHIOMI = c('山頂一帯の岩場帯', *ym('塩見岳', 182))
MINAMIKOMA = c('山頂付近に花崗岩の岩が乱立', *ym('南駒ヶ岳', 2439))
EBOSHI = c('山頂の烏帽子の形の岩塔', *ym('烏帽子岳', 55))
KARAMATSU = c('唐松岳から五竜岳・白馬岳へ続く岩稜帯（不帰ノ嶮）', *ym('唐松岳', 58))
KASHIMA = c('八峰キレット（日本三大キレットのひとつ）', *ym('鹿島槍ヶ岳', 174))
UTSUGI = c('千畳敷からの縦走路の岩場', *ym('空木岳', 180))
HIWADA = c('男坂の岩場', *ym('日和田山', 16255))
SEKIROU = c('登山道に多くの奇岩', *ym('石老山', 16200))
TSURUGI = c('険しい岩場の山（早月尾根）', *ym('剱岳', 11))
NISHIHO = c('西穂独標から山頂へ連なる岩稜', *ym('西穂高岳', 1409))
JANDARM = c('西穂高岳〜奥穂高岳の岩稜（北アルプス屈指の難コース）', *ym('西穂高岳', 1409))
HOUOU = c('地蔵岳のオベリスク（花崗岩の尖塔）', 'ヤマケイオンライン「鳳凰山 地蔵岳」（山と溪谷社）',
          'https://www.yamakei-online.com/yamanavi/yama.php?yama_id=584')
KINPU = c('山頂の五丈岩（花崗岩の巨岩）', 'ヤマケイオンライン「金峰山」（山と溪谷社）',
          'https://www.yamakei-online.com/yamanavi/yama.php?yama_id=351')
TSUBAKURO = c('山頂一帯の花崗岩の奇岩（めがね岩・イルカ岩）', 'ニッポン旅マガジン「燕岳・メガネ岩」',
              'https://tabi-mag.jp/tsubakuro-megane/')

# (山ID, コース名の頭) → rocks
ROCKS = {
    ('tsukuba', '筑波山神社〜白雲橋コース'): TSUKUBA,
    ('tsukuba', 'つつじヶ丘〜おたつ石コース'): TSUKUBA,
    ('mizugaki', '瑞牆山荘〜富士見平小屋〜瑞牆山'): MIZUGAKI,
    ('mizugaki', 'みずがき山自然公園'): MIZUGAKI,
    ('mizugaki', '瑞牆山荘〜瑞牆山〜富士見平〜金峰山'): MIZUGAKI,
    ('yatsugatake', '美濃戸口〜美濃戸〜行者小屋'): AKADAKE,
    ('kintoki', '金時神社入口'): KINTOKI,
    ('kintoki', '公時神社〜金時山〜矢倉沢峠'): KINTOKI,
    ('kintoki', '乙女峠'): KINTOKI,
    ('kazahariyama', '栗生登山口'): OGURA,
    ('kazahariyama', '白岩'): OGURA,
    ('kazahariyama', '長者の森'): OGURA,
    ('keirisan', '七合目登山口'): TATESHINA,
    ('keirisan', 'すずらん峠〜幸徳平'): TATESHINA,
    ('keirisan', 'すずらん峠〜蓼科山〜蓼科山荘'): TATESHINA,
    ('shiomidake', '越路〜鳥倉登山口〜三伏峠'): SHIOMI,
    ('shiomidake', '越路〜鳥倉登山口〜塩見岳〜蝙蝠岳'): SHIOMI,
    ('minamikomagatake', '伊奈川ダム〜越百山〜仙涯嶺'): MINAMIKOMA,
    ('minamikomagatake', '伊奈川ダム〜越百山〜南駒ヶ岳〜赤椰岳'): MINAMIKOMA,
    ('eboshidake_kita', '高瀬ダム〜ブナ立尾根'): EBOSHI,
    ('eboshidake_kita', '高瀬ダム〜烏帽子岳〜野口五郎岳'): EBOSHI,
    ('karamatsu', '八方尾根〜唐松岳〜五竜岳'): KARAMATSU,
    ('karamatsu', '八方池山荘〜唐松岳〜不帰ノ嶮'): KARAMATSU,
    ('goryudake', 'アルプス平〜遠見尾根〜五竜岳〜唐松岳'): KARAMATSU,
    ('kashimayari', '柏原新道〜鹿島槍ヶ岳〜八峰キレット'): KASHIMA,
    ('utsugi', '千畳敷〜檜尾岳'): UTSUGI,
    ('utsugi', '伊奈川ダム〜越百山〜南駒ヶ岳〜空木岳'): MINAMIKOMA,
    ('hiwadayama', '日和田山登山口〜男坂'): HIWADA,
    ('ishirousan', '石老山登山口'): SEKIROU,
    ('ishirousan', '石老山入口〜石老山〜大明神〜さがみ湖'): SEKIROU,
    ('ishirousan', '石老山入口〜石老山〜大明神〜嵐山'): SEKIROU,
    ('tsurugi', '馬場島〜早月尾根'): TSURUGI,
    ('hotaka', '西穂高口駅〜西穂高岳〜ジャンダルム'): JANDARM,
    ('nishihotaka', '西穂高口駅〜西穂山荘〜西穂独標〜西穂高岳'): NISHIHO,
    ('nishihotaka', '上高地〜西穂山荘'): NISHIHO,
    ('houou', '青木鉱泉〜ドンドコ沢〜地蔵岳'): HOUOU,
    ('houou', '夜叉神峠〜薬師岳〜観音岳〜地蔵岳'): HOUOU,
    ('kinpusan', '大弛峠'): KINPU,
    ('kinpusan', '廻り目平'): KINPU,
    ('kinpusan', '瑞牆山荘〜富士見平〜金峰山'): KINPU,
    ('tsubakurodake', '中房温泉〜合戦尾根'): TSUBAKURO,
    ('tsubakurodake', '中房温泉〜燕岳〜北燕岳'): TSUBAKURO,
}


def main():
    M = json.load(open(PATH, encoding='utf-8'))
    used = set()
    for m in M:
        for r in m.get('routes') or []:
            hit = [k for k in ROCKS if k[0] == m['id'] and r['name'].startswith(k[1])]
            assert len(hit) <= 1, (m['id'], r['name'], hit)
            if hit:
                assert not r.get('chains'), ('鎖場のコースに重ねない', m['id'], r['name'])
                r['rocks'] = ROCKS[hit[0]]
                used.add(hit[0])
            else:
                r.pop('rocks', None)
    missing = set(ROCKS) - used
    if missing:
        raise SystemExit('コースが見つからない：%s' % sorted(missing))
    added, removed, rocky = [], [], []
    for m in M:
        is_rock = any(r.get('rocks') or r.get('chains') for r in m.get('routes') or [])
        v = list(m.get('vibes') or [])
        if is_rock:
            rocky.append(m['name'])
            if 'rock' not in v:
                v.append('rock')
                added.append(m['name'])
        elif 'rock' in v:
            v = [x for x in v if x != 'rock']
            removed.append(m['name'])
        if 'vibes' in m or v:
            m['vibes'] = v
    json.dump(M, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('岩場の山：%d' % len(rocky))
    print('岩場のタグを足した：%s' % ' '.join(added))
    print('岩場のタグを外した：%d %s' % (len(removed), ' '.join(removed)))


if __name__ == '__main__':
    main()
