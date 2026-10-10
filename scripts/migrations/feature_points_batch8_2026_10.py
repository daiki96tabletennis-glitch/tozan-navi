#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""診断の「おすすめの理由」用の featurePoints（第8回：24山・2026-10-10）。伊豆・箱根・湘南・房総・栃木と、中央線沿いの山。
内容は、観光協会・自治体・国土交通省の解説・山岳メディアの記事・登山記録で確認できた事実だけを書く。出典は featureSources に残す。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-10'
DATA = {
    'amagi': (['https://yamahack.com/227', 'https://hinata.me/article/833605255419901145'], [
        ('flower', 'シャクナゲの群生', '万二郎岳と万三郎岳のあいだの「石楠立」のあたりにシャクナゲが群生し、5月中旬〜6月初旬に咲く'),
        ('flower', 'アセビのトンネル', '万二郎岳から石楠立にかけて、白いアセビの花が頭の上をおおう。見頃は3月〜4月ごろ'),
        ('forest', 'ブナの原生林', '雨の多い山で、ブナの原生林やヒメシャラの林に包まれる。新緑と紅葉がとくに美しい'),
        ('collector', '伊豆半島の最高峰', '万三郎岳（1,406m）は伊豆半島でいちばん高い。天城山は万二郎岳などをあわせた連山の呼び名'),
    ]),
    'nokogiriyama_chiba': (['https://tabi-mag.jp/ch0442/', 'https://tabi-mag.jp/ch0051/', 'https://rurubu.jp/andmore/article/17930'], [
        ('rock', '地獄のぞき', '石を切り出した跡が落差100mの断崖になり、空中に突き出た岩の先から下をのぞける'),
        ('historic', '石切場の跡', '江戸時代から1985年まで「房州石」を切り出した山。登山道に切り立った巨大な壁が残り、「ラピュタの壁」と呼ばれる'),
        ('historic', '日本寺の大仏', '724年に聖武天皇の命で開かれたと伝わる日本寺があり、石の大仏や千五百羅漢が並ぶ'),
        ('collector', 'のこぎりの歯の稜線', '稜線がのこぎりの歯のように見えることが、名前の由来'),
        ('casual', '駅から歩ける', '浜金谷駅から登り、日本寺の境内を歩いて保田駅へ下りられる。ロープウェーもある'),
    ]),
    'koubousan': (['https://www.kankou-hadano.org/hadano_hiking/hikingmap_ka.pdf', 'https://tabi-mag.jp/kn0332/', 'https://www.pref.kanagawa.jp/docs/ph7/cnt/f7631/2023shokuin-memo-hadanodehiking.html'], [
        ('flower', '桜の名所', '浅間山・権現山・弘法山をあわせた弘法山公園は桜の名所で、「かながわの花の名所100選」に選ばれている'),
        ('view', '権現山の展望台', '権現山の展望台から富士山と相模湾を見渡せる。「関東の富士見百景」のひとつ'),
        ('historic', '鐘楼と大師堂', '弘法山の山頂に鐘楼と大師堂が建つ'),
        ('casual', '下山したら温泉', '秦野駅から歩き始め、吾妻山を越えて鶴巻温泉へ下りる。歩く時間は約2時間10分'),
    ]),
    'kusatoriyama': (['https://www.bepal.net/archives/258060'], [
        ('view', '松見平の眺め', '山頂の休憩所「松見平」から、足もとに城山湖、遠くに都心のビル群が見える'),
        ('quiet', '静かな南高尾', 'にぎやかな高尾山とちがって人が少なく、静かに歩ける'),
        ('challenge', '細かい登り下り', '城山湖のまわりは急な階段が多く、低い山でも足にこたえる'),
    ]),
    'nakimushiyama': (['https://yamahack.com/2081', 'https://yamap.com/model-courses/93246'], [
        ('flower', '春のアカヤシオ', '春、尾根の道ぞいにアカヤシオが咲く'),
        ('view', '日光連山の展望', '山頂の展望台から、日光連山と日光の街並みを見渡せる'),
        ('historic', '修行の山と憾満ヶ淵', 'かつて日光の僧が修行した山。下山した先に、その名残の憾満ヶ淵がある'),
        ('challenge', '木の根の道', '網の目のように張った木の根や、石の段差を越えていく。ぬれるとすべりやすい'),
        ('collector', '名前の由来', '「この山に雲がかかると雨になる」という言い伝えが、名前のもとになった'),
    ]),
    'tomisan': (['https://tabi-mag.jp/ch0234/', 'https://san-tatsu.jp/articles/211239/'], [
        ('historic', '八犬伝の舞台', '曲亭馬琴の『南総里見八犬伝』の舞台で、伏姫籠穴や八犬士終焉の地などが山の中に点在する'),
        ('view', '十一州一覧台', '北峰の広場に「十一州一覧台」という展望台があり、房総の山並みと東京湾を見渡せる'),
        ('ridge', '2つの峰', '北峰（金毘羅峰）と南峰（観音峰）からなる双耳峰'),
    ]),
    'iyogatake': (['https://www.bepal.net/archives/551512', 'https://tabi-mag.jp/ch0233/'], [
        ('rock', '山頂直下の鎖場', '切り立った岩峰に鎖とロープが続き、低い山とは思えないスリルがある'),
        ('collector', '房総のマッターホルン', 'とがった姿から「房総のマッターホルン」と呼ばれる。千葉県でただひとつ「岳」のつく山'),
        ('view', '南峰の眺め', '南峰の山頂は360度の展望で、晴れた日は富士山や伊豆半島まで見える'),
        ('casual', '半日で登れる', '平群天神社から往復で約2時間半、約3km'),
    ]),
    'myojingatake': (['https://www.bepal.net/archives/400430', 'https://www.nap-camp.com/mag/71369'], [
        ('view', '富士山と箱根の全景', '山頂から、金時山の向こうに富士山が見える。大涌谷、芦ノ湖、相模湾までぐるりと見渡せる'),
        ('highland', '笹の道', '山全体がカヤとササにおおわれて空が広い。日が当たると笹が黄金色に光る'),
        ('ridge', '外輪山の尾根歩き', '箱根の外輪山のひとつで、噴煙や温泉街を見下ろしながら尾根を歩ける。金時山へつなぐ道もある'),
        ('historic', '最乗寺から登る', '大雄山駅からバスで行ける最乗寺が登山口。山頂まで約160分'),
    ]),
    'yaguradake': (['https://san-tatsu.jp/articles/311862/', 'https://yamap.com/activities/38683124/article'], [
        ('view', '広い山頂', 'さえぎるもののない広い山頂から、富士山と金時山、明神ヶ岳が見える。晴れた日は江の島も見える'),
        ('casual', '山頂でひと休み', '山頂にベンチとテーブルがあり、ゆっくり休める'),
        ('forest', '杉林の道', '杉の林を抜けて登る。山頂が近づくと坂が急になる'),
    ]),
    'ishirousan': (['https://www.andwander.com/journal/hiking-club/journal-230428.html', 'https://www.asoview.com/leisure/grp1/location/are0141400/'], [
        ('rock', '奇岩と巨岩', '登山道に、言い伝えのある変わった形の岩や大きな岩が次々に現れる'),
        ('historic', '顕鏡寺', '平安時代の876年に建てられた顕鏡寺を通って登る'),
        ('challenge', '段差の大きい道', '岩がごろごろして段差が大きく、ハイキングコースにしては歩きごたえがある'),
        ('collector', '関東百名山', '相模湖の名山として知られ、関東百名山のひとつ'),
    ]),
    'ohnoyama': (['https://www.bepal.net/archives/432861', 'https://www.bepal.net/archives/448514', 'https://www.ktr.mlit.go.jp/chiiki/fujimi0090.html'], [
        ('view', '360度の山頂', '山頂から、富士山、丹沢の山々、足もとの丹沢湖、相模灘、箱根の外輪山まで見渡せる。「関東の富士見百景」のひとつ'),
        ('highland', '牧場の山', '山頂は平らで公園のように広く、草原とベンチがある。下りは牧場の中を歩く'),
        ('casual', '家族で歩ける', 'のどかな雰囲気で、家族連れに人気がある'),
        ('easy', '駅から登れる', 'JR御殿場線の谷峨駅から歩き始められる'),
    ]),
    'makuyama': (['https://hinata.me/article/905774173052178524', 'https://tabi-mag.jp/yugawara-umefes/'], [
        ('flower', '湯河原梅林', 'ふもとに約4,000本の梅が植えられ、早春は山すそが紅白に染まる。見頃に「梅の宴」が開かれる'),
        ('rock', '幕岩', '柱を並べたような岩壁「幕岩」は、ロッククライミングの練習場として知られる'),
        ('view', '相模湾の眺め', '山頂から相模湾を一望できる'),
        ('volcano', '溶岩ドームの山', '約15万年前の噴火でできた箱根火山の側火山で、箱根ジオパークの見どころのひとつ'),
    ]),
    'taiheizan': (['https://www.pref.tochigi.lg.jp/d04/eco/shizenkankyou/shizen/ohira.html', 'https://www.ktr.mlit.go.jp/chiiki/chiiki00000119.html', 'https://tabi-mag.jp/tg0165/'], [
        ('view', '謙信平', '謙信平から関東平野を一望できる。霧に峰が浮かぶ景色は「陸の松島」と呼ばれ、晴れた日は富士山や東京スカイツリーも見える'),
        ('flower', 'あじさい坂', '太平山神社の参道「あじさい坂」は、6〜7月にアジサイが咲く'),
        ('flower', '桜のトンネル', '遊覧道路ぞいに約2km桜並木が続く。「日本さくら名所100選」のひとつ'),
        ('historic', '太平山神社', '山の中腹に太平山神社、ふもとに大中寺がある'),
    ]),
    'kogashiyama': (['https://www.ne.jp/asahi/walking-in-the/mountains-in-japan/kogashiyama.htm', 'https://yamap.com/activities/46508404/article'], [
        ('rock', '岩場の多い低山', '低い山とは思えないごつごつした岩山で、御嶽山の近くなどに鎖場がある'),
        ('view', '日光連山の眺め', '山頂の近くから、男体山・女峰山・日光白根山などの日光連山や那須岳が見える'),
        ('collector', '日本百低山', '画家の小林泰彦が『日本百低山』で「北関東屈指の名低山」と書いた山'),
        ('river', '赤川ダム', 'ふもとの赤川ダムの湖面に、古賀志山が映る'),
    ]),
    'kamakura_alps': (['https://www.bepal.net/archives/536538', 'https://tabi-mag.jp/kn0393/'], [
        ('historic', '建長寺から瑞泉寺へ', '鎌倉五山第一位の建長寺から瑞泉寺まで、約3.8kmを2時間ほどで歩く'),
        ('view', '半僧坊と天園', '建長寺の裏山の半僧坊は、晴れれば富士山が見える。天園は6つの国が見えたことから「六国峠」とも呼ばれる'),
        ('collector', '鎌倉市の最高地点', '途中で、鎌倉市でいちばん高い大平山を通る'),
        ('season', '紅葉', '秋は、天園から赤や黄色に染まった山を見渡せる'),
    ]),
    'okusuyama': (['https://tabi-mag.jp/kn0122/', 'https://www.pa.ktr.mlit.go.jp/wankou/fujimihyakkei/jouhou/073.pdf'], [
        ('view', '360度の山頂', '三浦半島でいちばん高い山。山頂から、丹沢・箱根・伊豆半島と、江の島の上に浮かぶ富士山が見える'),
        ('flower', '菜の花とコスモス', '山頂のすぐ下の大楠平に花畑があり、菜の花は3月中旬〜4月上旬、コスモスは9月上旬〜10月上旬に咲く'),
        ('river', '前田川の遊歩道', '山の湧き水を集めた前田川に、全長1.4kmの遊歩道がある'),
        ('easy', '4つのコース', '山頂へのハイキングコースが4つあり、一年を通して歩ける'),
    ]),
    'azumayama_ninomiya': (['https://kanagawa-kankou.or.jp/spot/347', 'https://tabi-mag.jp/ninomiya-nanohana/'], [
        ('flower', '早咲きの菜の花', '1月上旬〜2月下旬、約6万株の菜の花が山頂の斜面を黄色に染める'),
        ('view', '富士山と相模湾', '芝生の山頂から360度を見渡せる。富士山、箱根、伊豆半島、大島、江の島、房総半島まで見える'),
        ('easy', '駅から約25分', '二宮駅の北口から公園の入口まで歩いて5分、そこから約20分で山頂に着く'),
        ('season', '四季の花', '春は桜、初夏はアジサイ、夏はコスモスが咲く'),
    ]),
    'kuratakeyama': (['https://www.yamanashi-kankou.jp/course/nature/otsuki006.html', 'https://yamap.com/activities/48702095/article'], [
        ('view', '秀麗富嶽十二景', '山頂から富士山がよく見える。大月市の「秀麗富嶽十二景」のひとつ'),
        ('ridge', '高畑山へ駅から駅', '梁川駅から立野峠、倉岳山、穴路峠、高畑山を経て鳥沢駅へ歩ける'),
        ('river', '沢ぞいの登り', '立野峠までは沢に沿って登り、何度か沢を渡る'),
        ('collector', '鞍の形の山', '桂川のほうから見ると馬の鞍の形に見え、昔は「鞍岳山」とも書いた'),
    ]),
    'shodosan_namatate': (['https://yamahack.com/1715', 'https://san-tatsu.jp/articles/550632/'], [
        ('flower', '桜のプロムナード', '尾根に「桜のプロムナード」があり、春は花見の登山者でにぎわう'),
        ('view', '三国山の富士山', 'すぐ隣の三国山は、甲斐・相模・武蔵の3つの国の境。富士山がくっきり見える'),
        ('ridge', '和田峠へ縦走', '茅丸、連行峰、醍醐丸と小さな峰を越えて、陣馬山のふもとの和田峠まで歩ける'),
        ('forest', '新緑の尾根', '山頂は狭いが、新緑の季節は緑に囲まれる'),
    ]),
    'kukiyama': (['https://yamap.com/activities/14831508/article', 'https://yamap.com/activities/46337330/article'], [
        ('view', '富士見平', '山頂の南側の「富士見平」から富士山を大きく望める。大月市の「秀麗富嶽十二景」のひとつ'),
        ('historic', '桃太郎伝説', '百蔵山で生まれた桃太郎が、九鬼山の鬼を退治したという伝説が残る'),
        ('collector', 'リニアが見える', '山の下をリニア実験線のトンネルが通り、登山道から走るリニアが見えることがある'),
        ('easy', '駅から登れる', '富士急行の禾生駅から歩き始められる'),
    ]),
    'juunigadake': (['https://www.yamanashi-kankou.jp/zenryoku/other/climbing.html', 'https://www.minnacamera.com/spots/1444'], [
        ('rock', '12の峰を越える', '毛無山から、名前のもとになった12の峰を次々に越える。鎖場、吊り橋、岩場が続く'),
        ('view', '富士山と2つの湖', '山頂から、富士山と河口湖、西湖をいっしょに眺められる'),
        ('challenge', '低くても手ごわい', '岩場と細い尾根が続き、標高のわりに厳しい。経験者向きの区間がある'),
    ]),
    'ranzan_saitama': (['https://www.pref.saitama.lg.jp/documents/141465/1-5.pdf', 'https://yamap.com/model-courses/94794'], [
        ('collector', '武蔵嵐山の名前', '昭和の初め、京都の嵐山の景色によく似ているとして「武蔵嵐山」と名づけられた'),
        ('river', '嵐山渓谷', '槻川ぞいに約1.6kmの散策コースがあり、冠水橋の上から渓谷を眺められる'),
        ('historic', '与謝野晶子の歌碑', '渓谷に、与謝野晶子が詠んだ「比企の渓」の歌碑が立つ'),
        ('quiet', '静かな渓谷', '水と緑に包まれ、訪れる人が少なく静か'),
    ]),
    'sasakogarigaburiyama': (['https://www.pref.yamanashi.jp/documents/104197/0015.pdf', 'https://yamap.com/activities/46612184/article'], [
        ('view', '秀麗富嶽十二景', '大月市の「秀麗富嶽十二景」のひとつ。登りの途中から富士山と南アルプスが見える'),
        ('historic', '笹子峠と矢立の杉', '甲州街道でいちばんの難所だった笹子峠の山。下りに「矢立の杉」という古い杉を通れる'),
        ('challenge', '急な登り', '登山口からの登りはかなり急'),
        ('easy', '駅から歩ける', '笹子駅から登山口まで歩いて30〜40分'),
    ]),
    'koganzan': (['https://www.ne.jp/asahi/walking-in-the/mountains-in-japan/koganezawarenrei.htm', 'https://yamap.com/activities/33965485/article'], [
        ('collector', '小金沢連嶺の最高峰', '大菩薩峠から南へのびる小金沢連嶺でいちばん高い'),
        ('highland', '笹原の稜線', '隣の牛奥ノ雁ヶ腹摺山へ、笹原の道が続く'),
        ('forest', '苔むした森', '山頂の手前は、苔と倒木の残る手つかずの針葉樹林'),
        ('view', '秀麗富嶽十二景', '牛奥ノ雁ヶ腹摺山とあわせて、大月市の「秀麗富嶽十二景」に選ばれている'),
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
