#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""診断の「おすすめの理由」用の featurePoints（第9回：29山・2026-10-10）。上信越・八ヶ岳周辺・アルプスの残り。
内容は、観光協会・自治体・国の機関の解説・山岳メディアの記事・登山記録で確認できた事実だけを書く。出典は featureSources に残す。
草津白根山は規制中のため登録しない。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-10'
DATA = {
    'hinata': (['https://www.yamanashi-kankou.jp/kankou/spot/p2_2225.html', 'https://www.pref.yamanashi.jp/documents/103416/28_hinatayama.pdf', 'https://yamahack.com/1694'], [
        ('view', '山の上の白い砂浜', '山頂近くの「雁ヶ原」は、花崗岩がくずれた真っ白な砂が一面に広がる。夏でも雪が積もったように見える'),
        ('view', '甲斐駒ヶ岳と八ヶ岳', '雁ヶ原から、甲斐駒ヶ岳と八ヶ岳を間近に望める'),
        ('easy', '道標つきの道', '山頂までを10に区切った道標があり、どこまで登ったかがわかる。丸太の階段などで整えられ、危ないところはない'),
        ('casual', '約1時間半で山頂', '駐車場から約1時間30分で登れる'),
    ]),
    'yakedake': (['https://tabi-mag.jp/syougaike/', 'https://www.jma-net.go.jp/nagano/shosai/kazan/1915yakedake.html', 'https://www.city.matsumoto.nagano.jp/soshiki/7/165070.html'], [
        ('volcano', '北アルプスの活火山', '今も噴気を上げる活火山で、山頂部は溶岩ドーム。北峰のまわりでは火山ガスが出ている'),
        ('volcano', '火口湖の正賀池', '山頂の火口に、正賀池という火口湖がある'),
        ('historic', '大正池をつくった山', '上高地の大正池は、1915年（大正4年）の焼岳の噴火で梓川がせき止められてできた'),
        ('collector', '日本百名山', '標高2,455mの日本百名山'),
    ]),
    'arafune': (['https://yamahack.com/2579', 'https://yamap.com/activities/44178952/article'], [
        ('view', '艫岩の断崖', '山頂台地の北の端「艫岩」は、高さ約200mの垂直の崖。浅間山や妙義山を見渡せる'),
        ('collector', '船の形の山', '山頂が平らな台地になっていて、遠くから見ると船のように見える'),
        ('highland', '平らな山頂台地', '崖の上は平らで、台地の上を歩いて最高点の経塚山（行塚山）へ向かう'),
        ('casual', '内山峠から', '内山峠から登るのが一般的で、経塚山（行塚山）まで約2時間'),
    ]),
    'asamamakurayama': (['https://yamahack.com/3006', 'https://tabi-mag.jp/gu0466/', 'https://yamap.com/activities/5496486/article'], [
        ('view', '浅間山の展望台', '山頂は360度の展望で、浅間山のほか、八ヶ岳、南アルプス、上州の山々が見える'),
        ('easy', '家族で登れる', '二度上峠の近くから登る道は、家族でも登れる手軽なコース'),
        ('casual', '下山後の温泉', 'ふもとに「はまゆう山荘 倉渕川浦温泉」があり、下山後に立ち寄れる'),
    ]),
    'kazahariyama': (['https://yamahack.com/2991', 'https://www.ne.jp/asahi/walking-in-the/mountains-in-japan/ogurayama.htm'], [
        ('view', '岩の山頂', '山頂だけが岩壁をあらわにした岩峰で、360度の眺め。八ヶ岳、南アルプス、浅間山、遠く北アルプスまで見える'),
        ('flower', 'シャクナゲ', '6月中旬〜7月中旬、シャクナゲの群生が咲く'),
        ('collector', '佐久・西上州の最高峰', '日本二百名山。佐久と西上州の山々のなかでいちばん高く、八ヶ岳と向かい合う'),
        ('quiet', '黒木の森の山', '山頂のほかは黒々とした針葉樹におおわれ、はなやかな八ヶ岳の隣で静かにたたずむ'),
    ]),
    'iwasugesan': (['https://yamahack.com/2019', 'https://www.mlit.go.jp/tagengo-db/R1-02223.html'], [
        ('ridge', '志賀高原の稜線', '森を抜けて稜線に出ると、志賀高原を見渡す眺めが続く'),
        ('ridge', '裏岩菅山へ', '志賀高原でいちばん高い裏岩菅山（2,341m）まで足をのばす人が多い'),
        ('flower', '夏の花と秋の紅葉', '7〜8月は高山植物が咲き、9〜10月は紅葉に包まれる'),
        ('collector', '日本二百名山', '日本二百名山で、一等三角点百名山にも選ばれている'),
    ]),
    'iizunasan': (['https://rurubu.jp/andmore/spot/80018531', 'https://yamahack.com/2578'], [
        ('historic', '飯縄権現の山', '奈良時代からの修験の山。飯縄大権現は武田信玄と上杉謙信がともに信仰した'),
        ('historic', '十三仏の道', '南登山道に13体の石仏が並び、ひとつずつ数えながら登れる'),
        ('view', '北信五岳の眺め', '山頂は360度の展望で、戸隠連峰や黒姫山が間近に見える'),
        ('historic', '飯縄神社', '山頂の近くに飯縄神社があり、道ぞいにほこらが多い'),
    ]),
    'kurohimesan': (['https://tenki.jp/lite/mountain/normal/3/23/1034.html', 'https://kotobank.jp/word/%E9%BB%92%E5%A7%AB%E5%B1%B1-58089'], [
        ('wetland', '火口原の池', '外輪山と中央の火口丘のあいだに、七ツ池や大池などの池と湿地がある。日本の重要湿地のひとつ'),
        ('collector', '信濃富士', '形のととのった姿から「信濃富士」と呼ばれる。北信五岳のひとつで、日本二百名山'),
        ('view', '野尻湖と北信五岳', '山頂から野尻湖と北信五岳の山々が見える'),
        ('historic', '黒姫伝説', '大蛇になった黒姫の伝説が、山の名前の由来といわれる'),
        ('forest', '苔むした森', '夏は苔むした森の中を歩く'),
    ]),
    'kenashiyama': (['https://tenki.jp/mountain/normal/5/25/1118.html', 'https://yamap.com/activities/27248268/article'], [
        ('view', '目の前の富士山', '朝霧高原をはさんで富士山と向かい合う。途中に「富士山展望台」があり、大沢崩れまで見える'),
        ('challenge', '急登が2時間', '登山口から約2時間、急な登りが続く'),
        ('collector', '天子山地の最高峰', '山梨と静岡の境にあり、天子山地でいちばん高い。日本二百名山'),
        ('view', '南アルプスの眺め', '稜線に、南アルプスを見渡せる場所がある'),
    ]),
    'shirasunayama': (['https://yamahack.com/3035', 'https://yamap.com/model-courses/93252'], [
        ('flower', '野反湖の花', '登山口の野反湖は、2,000m級の山に囲まれた「天空の湖」。初夏からノゾリキスゲなどの高山植物が咲く'),
        ('ridge', '県境の稜線', '群馬の県境をたどる「ぐんま県境稜線トレイル」が、野反湖から白砂山へ続く'),
        ('season', '湖の紅葉', '秋は、紅葉が野反湖の湖面に映る'),
    ]),
    'nanaitsurasan': (['https://www.yamanashi-kankou.jp/special/2020_shichimensan2.html', 'https://yamahack.com/2040', 'https://www.mlit.go.jp/tagengo-db/common/001557413.pdf'], [
        ('historic', '信仰の山', '法華経の聖地で、山頂の近くに日蓮宗の敬慎院が建つ。登山道には一丁ごとに目印があり、五十丁目まで数えて登る'),
        ('view', '富士山のご来光', '富士山の方角が開け、春分と秋分のころは富士山の山頂から日が昇る「ダイヤモンド富士」が見られる'),
        ('hut', '宿坊に泊まる', '敬慎院の宿坊に泊まり、朝のおつとめとご来光を体験できる'),
        ('challenge', '表参道を4時間', '表参道を約4時間かけて登る'),
    ]),
    'arasawadake': (['https://niigata-kankou.or.jp/spot/7585', 'https://tabi-mag.jp/ng0083/'], [
        ('rock', '前嵓の鎖場', '途中の岩峰「前嵓」は、鎖とはしごで絶壁を登る難所。ヘルメットをかぶって登る'),
        ('challenge', '玄人好みの山', '急な登りと岩場が続く。穂高にたとえられる豪快な姿で、経験者に好まれる'),
        ('view', '奥只見湖の眺め', '山頂から奥只見湖と、越後駒ヶ岳、中ノ岳が見える'),
        ('collector', '日本二百名山', '銀山平から登る、標高1,969mの日本二百名山'),
    ]),
    'nakawarayama': (['https://yamahack.com/3069', 'https://www.asahi-net.or.jp/~az5h-oomr/wanakura.htm'], [
        ('quiet', '奥秩父の秘峰', '奥秩父の深いところにある山で、別名は白石山。日本二百名山'),
        ('ridge', '見晴らしのよい稜線', '山頂へ向かう稜線は眺めがよく、晴れた日は富士山が見える'),
        ('flower', 'シャクナゲ', '花の時期はシャクナゲが咲く'),
        ('challenge', '長い道のり', '山頂まで距離が長く、経験者向きのコース'),
        ('forest', '笹とカラマツ', '1950年代からの大きな伐採のあとに植えられたカラマツと、笹原が広がる'),
    ]),
    'tairappyo': (['https://yamap.com/activities/49177798/article', 'https://yamap.com/activities/49063399/article'], [
        ('flower', '花の百名山', '花の百名山。6月、雪がとけたあとの稜線にお花畑が広がる'),
        ('ridge', '仙ノ倉山への稜線', '樹林を抜けると見晴らしのよい稜線になり、仙ノ倉山まで花の中を歩ける'),
        ('hut', '平標山の家', '山頂から約1km下に「平標山の家」があり、5〜10月は管理人がいる。水も使える'),
    ]),
    'yarigatake2': (['https://yamahack.com/2936', 'https://www.pref.yamanashi.jp/documents/103416/38_zarugatake.pdf'], [
        ('collector', '大笊と小笊', 'ざるを伏せたような形が名前の由来。「大笊」と「小笊」の2つの峰が遠くからも目立つ'),
        ('view', '南アルプス南部の展望', '山頂は360度の展望で、赤石岳や聖岳を間近に見られる'),
        ('challenge', '遠い山頂', 'どの登山口からも遠く、途中に小屋や水場がない'),
        ('quiet', '登る人の少ない山', '南アルプスの白峰南嶺にある日本二百名山で、訪れる人が少ない'),
    ]),
    'gakedake': (['https://yamahack.com/3120', 'https://yamap.com/model-courses/94871'], [
        ('view', '裏銀座の山々', '山頂から、高瀬川をはさんで鷲羽岳、水晶岳、野口五郎岳、烏帽子岳が並んで見える。槍・穂高や立山、剱岳も望める'),
        ('river', '沢ぞいの道', '前半は白沢に沿って、桟道やはしごをたどって進む。魚止ノ滝を過ぎたところに最後の水場がある'),
        ('challenge', '標高差1,600m', '白沢登山口からの標高差は約1,600mで、急な登りが多い'),
        ('hut', '山頂直下の小屋', '餓鬼岳小屋は山頂のすぐ近く。小屋のそばの展望地から、雲海の上のご来光が見られる'),
    ]),
    'arikayama': (['https://yamahack.com/3164', 'https://www.rinya.maff.go.jp/j/kokuyu_rinya/kokumin_mori/katuyo/reku/rekumori/ariakeyama.html'], [
        ('collector', '信濃富士', '富士山に似たどっしりした形で、「信濃富士」「安曇富士」「有明富士」と呼ばれる'),
        ('historic', '修験の山', '安曇野を見守る信仰の山で、かつては修験者の修行の場だった。ふもとに有明山神社、北岳の山頂に奥宮がある'),
        ('challenge', '急な登り', '表参道は山頂まで約4.4kmで、標高差が約1,400mある'),
        ('historic', '天気の言い伝え', '「どんなに雨が降っても、有明山に雲がなければ晴れる」と言い伝えられる'),
    ]),
    'keizandake': (['https://yamahack.com/3122', 'https://tenki.jp/lite/mountain/normal/3/23/1050.html'], [
        ('view', '八合目の展望', '八合目から、南アルプス、八ヶ岳、御嶽山などが広がって見える。山頂は眺めがよくない'),
        ('historic', '山頂の石仏', '山頂に、山の信仰を伝える石仏や石塔がまつられている'),
        ('forest', '針葉樹の森', 'カラマツやシラビソの高い木の森を登っていく'),
        ('collector', '中央アルプスの北の端', '中央アルプスの北の端にある日本二百名山。仲仙寺から登る'),
    ]),
    'sukai': (['https://yamahack.com/1915', 'https://www.rinya.maff.go.jp/kanto/nikkou/invitation/pdf/sukaisan.pdf'], [
        ('historic', '修験の「三山駆け」', '庚申山から鋸山の11の峰を越えて皇海山へ向かう道は「三山駆け」と呼ばれ、江戸時代に多くの修験者が歩いた'),
        ('challenge', '長いクラシックルート', '栃木県の足尾から歩くルートは約25km。群馬県側の林道が通れなくなり、今はこの道が主流'),
        ('rock', '鋸山の鎖場', '鋸山と皇海山のあいだに、鎖やロープのかかった場所がいくつもある'),
        ('forest', '森の中の山頂', '山頂は木に囲まれて眺めがなく、ほとんどが樹林の中の道'),
    ]),
    'arakawadake': (['https://tabi-mag.jp/sz586/', 'https://yamahack.com/2556'], [
        ('flower', 'カールのお花畑', '氷河がけずった谷の底に、南アルプスでも指折りのお花畑が広がる。シナノキンバイやハクサンイチゲが咲く'),
        ('collector', '荒川三山', '前岳・中岳・悪沢岳をあわせて荒川三山と呼ぶ。悪沢岳（3,141m）は南アルプスで3番目に高い'),
        ('alpine', '日本最南端の氷河地形', '悪沢岳から中岳にかけて、はっきりした氷河地形が残る。日本でいちばん南にある'),
        ('hut', '山小屋2泊の周回', '椹島から千枚小屋、荒川小屋に泊まり、千枚岳、悪沢岳、赤石岳とめぐる2泊3日が定番'),
    ]),
    'kurobegorodam': (['https://yamahack.com/2289', 'https://tenki.jp/mountain/famous100/4/19/158.html'], [
        ('alpine', '東面のカール', '東側に氷河がけずった大きな谷があり、底には羊の群れのように岩が並ぶ'),
        ('flower', '水の豊かなお花畑', 'カールは雪どけ水が豊かで、コバイケイソウやミヤマキンポウゲが群れて咲く'),
        ('collector', '名前の由来', '大きな岩がごろごろした場所を指す「ゴーロ」に、「五郎」の字を当てたといわれる'),
        ('hut', '北アルプスの奥', '北アルプスの中央部の奥深い山。太郎平小屋から歩き、黒部五郎小舎に泊まれる'),
    ]),
    'ainodake': (['https://tabi-mag.jp/yn0363/', 'https://yamahack.com/2332'], [
        ('collector', '日本で3番目の高さ', '標高3,190m。日本で3番目、南アルプスでは北岳に次いで高い'),
        ('ridge', '白峰三山の縦走', 'ふもとから直接登る道がなく、北岳、農鳥岳とつなぐ白峰三山の縦走で登る。北岳山荘から約2時間'),
        ('view', '広い山頂', '山頂も稜線も広く、どっしりした大きな山。山頂は見晴らしがよい'),
        ('alpine', '細沢カール', '山頂の東側に、氷河がけずった細沢カールが見える'),
    ]),
    'noutori': (['https://yamahack.com/3057', 'https://tabi-mag.jp/yn0379/'], [
        ('collector', '鳥の雪形', '雪どけのころ、山肌に白い鳥の形が現れる。ふもとの農家が田植えを始める合図にしたことが名前の由来'),
        ('ridge', '稜線の景色', '農鳥小屋から大門沢の下降点まで、変化のある美しい稜線が続く'),
        ('view', '富士山の眺め', '山頂から富士山がよく見える'),
        ('alpine', 'ライチョウの稜線', '山頂のまわりはハイマツの広がる高山帯で、ライチョウに出会えることがある'),
        ('hut', '農鳥小屋', '間ノ岳と西農鳥岳のあいだ、標高2,800mに農鳥小屋がある'),
    ]),
    'karisaka': (['https://tabi-mag.jp/yn0381/', 'https://tabi-mag.jp/3majorpasses/'], [
        ('historic', '日本三大峠の雁坂峠', '手前の雁坂峠（2,082m）は、三伏峠、針ノ木峠とならぶ日本三大峠のひとつ'),
        ('historic', '繭を運んだ道', '峠越えの道は秩父往還。明治から大正のころ、秩父の女性たちが繭を背負って塩山の市場まで運んだ'),
        ('view', '峠の眺め', '雁坂峠から富士山と南アルプスが見える'),
        ('hut', '雁坂小屋', '峠の埼玉県側に雁坂小屋がある'),
    ]),
    'nokogiriyama': (['https://yamahack.com/3280', 'https://www.pref.yamanashi.jp/documents/66779/minamiarupusuanzentozansuisinkuiki.pdf'], [
        ('rock', '難所の続く岩稜', '岩に穴のあいた「鹿窓」、鎖で岩壁を越える「小ギャップ」など、難所が続く'),
        ('challenge', '熟練者だけの山', '一般の登山道がなく、岩場を長時間歩く技術と、道を見つける力が必要'),
        ('collector', 'のこぎりの歯', '南アルプスの北の端にあり、のこぎりの歯のような荒々しい姿が名前の由来'),
    ]),
    'minamikomagatake': (['https://yamahack.com/2686', 'https://yamap.com/activities/18264253/article'], [
        ('view', '白い岩と緑のハイマツ', '白い花崗岩と緑のハイマツの対比が美しい。山頂はさえぎるものがなく、まわりの山々を見渡せる'),
        ('ridge', '中央アルプス南部の縦走', '越百山、仙涯嶺、南駒ヶ岳、赤椰岳、空木岳とつないで歩ける'),
        ('flower', '夏のお花畑', '夏は高山植物のお花畑が広がる'),
        ('collector', '日本二百名山', '中央アルプスの主稜線にある日本二百名山'),
    ]),
    'harinokidake': (['https://yamahack.com/2031', 'https://tabi-mag.jp/nn707/'], [
        ('alpine', '針ノ木雪渓', '白馬大雪渓、剱沢雪渓とならぶ日本三大雪渓のひとつ、針ノ木雪渓を登る'),
        ('flower', '高山植物', '道ぞいにコマクサ、チングルマ、シナノキンバイ、キヌガサソウなどが咲く'),
        ('hut', '峠の山小屋', '日本三大峠のひとつ針ノ木峠に針ノ木小屋があり、針ノ木岳と蓮華岳の拠点になる'),
        ('view', '黒部湖の眺め', '山頂から黒部湖を見下ろせる'),
    ]),
    'eboshidake_kita': (['https://tabi-mag.jp/nn763/', 'https://yamahack.com/3110'], [
        ('rock', '烏帽子の形の岩塔', '山頂は花崗岩の岩の塔で、烏帽子に似た形が名前の由来'),
        ('challenge', 'ブナ立尾根', '高瀬ダムから烏帽子小屋へのブナ立尾根は、三大急登のひとつに数えられる。標高差は約1,250m'),
        ('ridge', '裏銀座の起点', '槍ヶ岳へ続く「裏銀座縦走コース」の出発点として知られる'),
        ('view', '白い砂と緑のハイマツ', '白い花崗岩の砂と緑のハイマツの対比が美しい。日本二百名山'),
        ('hut', '烏帽子小屋', '稜線に烏帽子小屋があり、山頂まで約45分'),
    ]),
    'noguchigoro': (['https://yamahack.com/3218', 'https://yamap.com/model-courses/98272'], [
        ('view', '広い山頂', '山頂は広くなだらかで、360度の展望。槍ヶ岳、水晶岳、赤牛岳など北アルプスの山々に囲まれる'),
        ('ridge', '裏銀座の稜線', '裏銀座の縦走路にあり、稜線の先に槍ヶ岳を見ながら歩く'),
        ('collector', '名前の由来', '「五郎」は、大きな石がごろごろした場所を指す「ゴーロ」から来ている'),
        ('hut', '野口五郎小屋', '山頂のすぐ下に、家族で営む小さな野口五郎小屋がある'),
    ]),
}
for mid, (srcs, pts) in DATA.items():
    m = N[mid]
    assert len(pts) >= 3, mid
    assert not m.get('featurePoints'), mid
    m['featurePoints'] = [{'tag': t, 'label': l, 'text': x} for t, l, x in pts]
    m['featureSources'] = srcs
    m['featureCheckedAt'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('今回:', len(DATA), '／登録済み:', sum(1 for m in D if m.get('featurePoints')), '／全', len(D))
print('未登録:', [m['name'] for m in D if not m.get('featurePoints')])
