#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""診断の「おすすめの理由」用の featurePoints（第7回：17山・2026-10-10）。山梨の里山と奥武蔵・秩父の山。
内容は、観光協会・自治体・国土交通省の解説・山岳メディアの記事で確認できた事実だけを書く。出典は featureSources に残す。
九鬼山は検索で具体的な情報が取れなかったため、今回は登録しない。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-10'
DATA = {
    'mitsutoge': (['https://www.yamanashi-kankou.jp/special/21meizan/mitsutoge.html', 'https://yamahack.com/1657'], [
        ('view', '目の前の富士山', '河口湖をはさんですぐ向かいに富士山があり、山頂から大きく迫る姿が見える。写真を撮りに来る人も多い'),
        ('rock', '屏風岩', '山頂のすぐ下の屏風岩は、ロッククライミングの練習場として知られる'),
        ('flower', '花の山', 'アツモリソウの自生地として知られ、めずらしい高山植物が多い'),
        ('hut', '山頂の山小屋', '台地のような山頂に、通年営業の「四季楽園」と三ツ峠山荘が建つ'),
        ('collector', '3つの峰', '開運山・御巣鷹山・木無山の3つをあわせて三ツ峠山と呼ぶ'),
    ]),
    'ishiwariyama': (['https://www.mlit.go.jp/tagengo-db/common/001553169.pdf', 'https://yamahack.com/1659'], [
        ('historic', '石割神社の巨岩', '八合目の石割神社に、割れ目の入った巨岩がある。すき間を3回通り抜けると幸運が訪れると伝わる'),
        ('challenge', '403段の石段', '神社へは、403段の長い石段を登っていく'),
        ('view', '富士山と山中湖', '木がまばらな山頂から、正面に富士山、足もとに山中湖、遠くに南アルプスが見える'),
        ('ridge', '平尾山への周回', '山頂から平尾山へ尾根を歩いて、約3時間で一周できる'),
    ]),
    'kayagatake': (['https://yamahack.com/1692', 'https://yamahack.com/7768'], [
        ('historic', '深田久弥ゆかりの山', '『日本百名山』の著者・深田久弥が登山中に亡くなった山。登山口に深田記念公園がある'),
        ('view', '山頂の眺め', '山頂から八ヶ岳と南アルプスを見渡せる'),
        ('rock', '女岩', '登山道の途中で「女岩」と呼ばれる岩場のそばを通る'),
        ('ridge', '金ヶ岳へ', '隣の金ヶ岳まで足をのばして歩ける'),
    ]),
    'kentoku': (['https://yamahack.com/1656', 'https://hinata.me/article/996045339372329518'], [
        ('rock', '山頂直下の鳳岩', '最後に「鳳岩」と呼ばれる大きな岩を鎖で登る。途中の髭剃岩にも鎖がある'),
        ('highland', '森・草原・岩場', '登るにつれて樹林、草原、岩場と、景色が次々に変わる'),
        ('view', '360度の山頂', '岩の山頂から、ぐるりと見渡す眺めが広がる'),
        ('historic', '夢窓国師の修行の地', '鎌倉時代に禅僧の夢窓疎石が修行したと伝わり、ゆかりの場所が残る'),
        ('river', '錦晶水', '道の途中に「錦晶水」という水場がある'),
    ]),
    'ogiyama': (['https://yamahack.com/1705', 'https://www.yamanashi-kankou.jp/course/nature/otsuki005.html'], [
        ('view', '広い山頂と富士山', '広々とした山頂から富士山がよく見える。大月市の「秀麗富嶽十二景」のひとつ'),
        ('collector', '扇を広げた形', '南から見ると扇を広げたように幅広く見えることが、名前の由来といわれる'),
        ('season', '桜と紅葉', '富士山といっしょに、春は桜、秋は紅葉が見られる'),
        ('ridge', '百蔵山へ', '隣の百蔵山とつないで歩く人が多い'),
    ]),
    'momakurasan': (['https://yamahack.com/1750', 'https://yamahack.com/1705'], [
        ('view', '秀麗富嶽十二景', '大月市が選んだ「秀麗富嶽十二景」のひとつで、山頂から富士山がよく見える'),
        ('historic', '桃太郎伝説', '桃太郎の伝説が残る山'),
        ('collector', '郡内三山', '扇山・権現山とあわせて「郡内三山」と呼ばれる'),
        ('season', '桜と紅葉', '富士山といっしょに、桜や紅葉が見られる'),
    ]),
    'takagawayama': (['https://yamahack.com/1635', 'https://www.pref.yamanashi.jp/documents/91117/tekute16_p16.pdf'], [
        ('view', '360度の山頂', '山頂は360度の展望で、目の前に富士山が見える。「秀麗富嶽十二景」のひとつ'),
        ('easy', '駅から2時間', 'JR初狩駅から山頂まで約2時間。東京から日帰りできる'),
        ('ridge', '駅から駅へ', '初狩駅から登って、富士急行の田野倉駅へ下りるなど、コースの選び方が多い'),
    ]),
    'iwadonoyama': (['https://www.nap-camp.com/mag/11956', 'https://www.yamanashi-kankou.jp/special/history/kofujoj_06.html'], [
        ('historic', '岩殿城跡', '武田二十四将のひとり小山田信茂の居城の跡。岩山の形を生かした東国屈指の山城で、本丸跡や、巨岩が道をふさぐ揚城戸跡が残る'),
        ('view', '富士山と大月の街', '開けた山頂から、富士山と大月の街並みを見下ろせる。「秀麗富嶽十二景」のひとつ'),
        ('collector', 'スカイツリーと同じ高さ', '標高634m。東京スカイツリーと同じ高さの岩山'),
        ('rock', '鎖場', 'ところどころに鎖場があり、ほどよいスリルがある'),
    ]),
    'izugatake': (['https://yamahack.com/3366', 'https://www.pref.saitama.lg.jp/b0502/sizennkouenn23/izugatakewokoeru.html'], [
        ('historic', '子ノ権現の大わらじ', '縦走の先にある子ノ権現は足腰の守り仏。境内に、人の背丈を超える大きなわらじがある'),
        ('ridge', '起伏のある稜線', '標高は1,000mに届かないが、急な登りもある起伏に富んだ稜線を歩ける'),
        ('ridge', '駅から駅へ', '正丸駅から登り、伊豆ヶ岳と子ノ権現を経て吾野駅へ下りるのが定番'),
        ('flower', 'アズマイチゲ', '3月中旬〜4月下旬、白いアズマイチゲが咲く'),
        ('rock', 'チャートの岩山', '両神山と同じチャートという硬い岩でできていて、山頂のまわりは急な地形'),
    ]),
    'bukosan': (['https://yamahack.com/7547', 'https://www.nap-camp.com/mag/71661'], [
        ('collector', '秩父のシンボル', '石灰岩でできた山で、白く削られた独特の岩肌が秩父の街から見える'),
        ('view', '山頂の展望台', '山頂の展望台から秩父盆地を見下ろせる。晴れた日は富士山や南アルプスも見える'),
        ('forest', '大杉', '登山道の途中に、太い杉の大木が立つ「大杉の広場」がある'),
        ('historic', '御嶽神社', '山頂に武甲山御嶽神社がある'),
        ('flower', '春の山野草', '春はカタクリなどの山野草が道のわきに咲く'),
    ]),
    'hodosan': (['https://www.nap-camp.com/mag/105537', 'https://yamahack.com/1677'], [
        ('flower', 'ロウバイ園', '山頂一帯に約3,000本のロウバイが植えられ、1月中旬〜2月下旬に甘い香りが広がる'),
        ('historic', '宝登山神社の奥宮', '山頂に、火よけ・盗難よけで知られる宝登山神社の奥宮がある'),
        ('casual', 'ロープウェイと小動物公園', 'ロープウェイで約5分。山頂にはサルやウサギのいる小動物公園もある'),
        ('easy', '家族で歩ける', '長瀞駅からの道は急な登りが少なく、親子でも歩きやすい'),
    ]),
    'hiwadayama': (['https://tabi-mag.jp/sa0010/', 'https://matcha-jp.com/jp/10909'], [
        ('view', '巾着田を見下ろす', '金刀比羅神社の鳥居の前から、ふもとの巾着田と街並みを見渡せる。晴れた日は東京スカイツリーも見える'),
        ('historic', '金刀比羅神社の鳥居', '森の中に立つ大きな石の鳥居が、この山のいちばんの目印'),
        ('rock', '男坂と女坂', '神社への道は、岩場と鎖のある「男坂」と、ゆるやかな「女坂」に分かれる'),
        ('easy', '駅から15分', '西武池袋線の高麗駅から登山口まで歩いて約15分'),
    ]),
    'tenzandake': (['https://tabi-mag.jp/sa0023', 'https://san-tatsu.jp/articles/24647/'], [
        ('historic', '天覧山の名前', '明治16年、明治天皇が山頂から陸軍の演習をご覧になったことから、天覧山と呼ばれるようになった'),
        ('historic', '十六羅漢', '徳川綱吉の母・桂昌院が、病気平癒のお礼に寄進した十六羅漢の石仏がある'),
        ('view', '街と関東平野', '天覧山の山頂から、飯能の街と関東平野、東京スカイツリーや新宿のビル群まで見える'),
        ('historic', '見返り坂と雨乞いの池', '源義経の母・常盤御前が景色を振り返ったと伝わる「見返り坂」と、多峯主山の「雨乞いの池」を通る'),
        ('casual', 'アニメの舞台', 'アニメ「ヤマノススメ」の舞台で、聖地めぐりに訪れる人も多い'),
    ]),
    'maruyama_okubusuma': (['https://www.ne.jp/asahi/tokyo/ono/yama/kokunai/maruyama.htm'], [
        ('view', '山頂の展望台', '山頂に大きなコンクリートの展望台があり、武甲山や両神山を見渡せる'),
        ('easy', '駅から登れる', '芦ヶ久保駅から山頂まで約1時間45分'),
        ('historic', '札所を通る道', '秩父三十四観音霊場の札所・金昌寺を経由して登る道がある'),
    ]),
    'futagoyama_okumusa': (['https://yamap.com/model-courses/95105', 'https://www.seiburailway.jp/railways/trailrun/advanced.html'], [
        ('ridge', '雌岳と雄岳', '雌岳と雄岳の2つの峰からなる。高いほうの雄岳は標高882.7m'),
        ('rock', 'ロープのある急坂', '雌岳のすぐ下は急で、すべりやすい場所にロープが張られている'),
        ('view', '雄岳から武甲山', '雄岳から、武甲山と秩父の街を望める'),
        ('flower', '春のアカヤシオ', '春は尾根にアカヤシオと桜が咲く'),
    ]),
    'kannokura': (['https://san-tatsu.jp/articles/221625/', 'https://yamahack.com/4492'], [
        ('ridge', '駅から駅へ', '東武竹沢駅から三光神社、官ノ倉山、石尊山、北向不動を経て小川町駅へ、約3時間で歩ける'),
        ('view', '低くても眺めがよい', '標高344mと低いが眺めがよく、山頂の正面に石尊山、笠山や堂平山も見える'),
        ('historic', '石碑と庚申塔', '道のわきに古い石碑や庚申塔が残り、昔の生活の道だった名残を感じられる'),
        ('rock', '石尊山の鎖場', '石尊山からの下りに、鎖のある急な坂がある'),
        ('easy', '小学生から登れる', '小学生から登れる手軽な山で、寺や神社をめぐりながら歩ける'),
    ]),
    'hafuzan_chichibu': (['https://www.pref.saitama.lg.jp/a0508/shisetsu/kanfure8titibubonchi.html', 'https://yamahack.com/2103'], [
        ('view', '秩父盆地の眺め', 'チャートの岩峰になった山頂から、秩父盆地を見下ろせる'),
        ('historic', '札所34番・水潜寺', '秩父札所めぐりの結願の寺、水潜寺へ下る巡礼の道が通る'),
        ('rock', '猿岩と鎖場', '尾根の途中に「猿岩」と呼ばれる岩や、鎖のある場所がある'),
        ('river', '秩父華厳の滝', 'ふもとに秩父華厳の滝がある'),
    ]),
}
for mid, (srcs, pts) in DATA.items():
    m = N[mid]
    assert len(pts) >= 3, mid
    m['featurePoints'] = [{'tag': t, 'label': l, 'text': x} for t, l, x in pts]
    m['featureSources'] = srcs
    m['featureCheckedAt'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('今回:', len(DATA), '／登録済み:', sum(1 for m in D if m.get('featurePoints')), '／全', len(D))
