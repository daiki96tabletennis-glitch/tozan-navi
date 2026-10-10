#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""診断の「おすすめの理由」用に、山ごとの特徴を調べて featurePoints に持たせる（第1回：8山・2026-10-09）。
featurePoints: [{"tag": 特徴の種類, "label": 見出し, "text": その山ならではの具体的な内容}]
  tag は診断の加点項目と同じ語（view / forest / ridge / rock / historic / casual / flower / river / hut / season など）。
  診断は、利用者のタイプで加点された tag の項目を優先して3つ出す。
内容は、観光協会・自治体・山岳メディアの記事で確認できた事実だけを書く。出典は featureSources に残す。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-09'
DATA = {
    'takao': (['https://www.gltjp.com/ja/article/item/20493/'], [
        ('view', '山頂の展望', '山頂の広場から、晴れた日は富士山と丹沢の山並みが見える'),
        ('historic', '修験の霊山', '古くから山伏が修行した信仰の山で、その歴史に触れる行事や体験がある'),
        ('casual', '山頂の茶屋', '山頂には屋根つきの休憩所と、戦後すぐから登山者をもてなしてきた茶屋がある'),
        ('season', '紅葉', '秋がいちばん美しい季節とされ、紅葉は11月中旬〜12月上旬が見頃'),
    ]),
    'tsukuba': (['https://yamahack.com/358', 'https://www.mapple.net/article/720/'], [
        ('rock', '奇岩めぐり', '白雲橋コースは「弁慶七戻り」「胎内くぐり」「ガマ石」など、名前のついた巨岩が次々に現れる'),
        ('view', '女体山の展望', '最高点の女体山から、霞ヶ浦と関東平野を見下ろす360度の眺めが広がる'),
        ('historic', '筑波山神社', '「西の富士、東の筑波」と並び称された名山。山頂の本殿で、登った人だけの御朱印を受けられる'),
        ('casual', '御幸ヶ原', '男体山と女体山のあいだの平らな鞍部に、ケーブルカーの駅と食堂・売店が並ぶ'),
        ('ridge', '2つの頂', '男体山と女体山の2つの峰を、ひと登りずつでつないで歩ける'),
    ]),
    'tanzawa': (['https://kanagawa-kankou.or.jp/spot/7437', 'https://www.pref.kanagawa.jp/docs/f4y/02yama/tanzawa_tozan.html'], [
        ('forest', '山頂のブナ林', '広くなだらかな山頂のまわりに、ブナの大木の森が残る'),
        ('ridge', '塔ノ岳からの稜線', '塔ノ岳から続くゆるやかな稜線は、西に富士山を見ながら歩ける'),
        ('flower', 'ツツジの季節', '5月中旬〜6月上旬、高いところでシロヤシオとトウゴクミツバツツジが咲き、1年でいちばん登山者が多い'),
        ('hut', 'みやま山荘', '山頂に通年営業の山小屋があり、泊まりで丹沢の主脈を歩ける'),
    ]),
    'tonosaki': (['https://yamahack.com/6622', 'https://tabi-mag.jp/kn0780/'], [
        ('view', '山頂の大展望', '低いところから一気に立ち上がる山で、山頂から富士山・相模湾・秦野の街まで遮るものなく見える'),
        ('challenge', '大倉尾根', '階段が延々と続くことから「バカ尾根」と呼ばれる、登りごたえのある尾根'),
        ('hut', '茶屋と山小屋', '大倉尾根には山頂までに5軒の茶屋・山小屋があり、休みながら登れる'),
        ('ridge', '丹沢主脈の眺め', '山頂から蛭ヶ岳や檜洞丸など、丹沢の主な峰が並んで見える'),
        ('rock', '表尾根', '表尾根から登ると、烏尾山の先に岩場と鎖場がある'),
    ]),
    'oyama': (['https://kanagawa-kankou.or.jp/features/tanzawa-oyama', 'https://www.veltra.com/jp/yokka/article/the-charm-of-climbing-oyama/'], [
        ('view', '下社からの眺め', '阿夫利神社下社からの眺めはミシュラン・グリーンガイドで二つ星。相模平野・江の島・三浦半島を見渡せる'),
        ('historic', '大山詣り', '江戸の庶民がこぞって出かけた「大山詣り」の山。阿夫利神社は2,200年前の創建と伝わる'),
        ('casual', 'ケーブルカー', '中腹の下社までケーブルカーで上がれ、そこから山頂の本社まで約90分'),
    ]),
    'mitakesan': (['https://www.nap-camp.com/mag/102697', 'https://www.gltjp.com/ja/directory/item/14173/'], [
        ('flower', 'レンゲショウマ', '関東一といわれる群生地。7月下旬〜8月下旬、富士峰園地の斜面に薄紫の花が数万株咲く'),
        ('historic', '武蔵御嶽神社と御師の集落', '山頂に武蔵御嶽神社が鎮まり、江戸時代から続く御師の宿坊が今も並ぶ'),
        ('river', 'ロックガーデン', '沢沿いの散策路で、いくつもの滝を見ながら歩ける。紅葉の時期も人気'),
        ('historic', '綾広の滝', '古くから御嶽神社の禊（みそぎ）の神事が行われてきた滝'),
        ('casual', 'ケーブルカー', 'ケーブルカーで山上まで上がれ、体力に自信がなくても山の自然を楽しめる'),
    ]),
    'kumotori': (['https://yamahack.com/609', 'https://www.yamanashi-kankou.jp/special/lg/tabayama_26.html'], [
        ('ridge', '石尾根', '七ツ石山を過ぎると視界が開け、丹沢・富士山・南アルプスを見ながら広い尾根を歩く'),
        ('hut', '雲取山荘', '山荘に泊まれば、東京の夜景と日の出を山の上から見られる'),
        ('collector', '東京都最高峰', '東京都でいちばん高い山で、日本百名山・花の百名山に選ばれている'),
        ('easy', '鴨沢からの道', '鴨沢からの道はよく踏まれていて危ないところが少なく、ゆるやかな登りが続く'),
        ('view', '振り返る富士山', '七ツ石山から山頂へ向かう登りで、振り返ると富士山が見える'),
    ]),
    'kintoki': (['https://www.hakone-geopark.jp/area-guide/hakone2/009kintokiyama.html', 'https://tabi-mag.jp/kn0163/'], [
        ('view', '富士山の正面', '山頂から迫力のある富士山が見え、左手に芦ノ湖、仙石原を挟んで大涌谷も望める'),
        ('historic', '金太郎伝説', '童話「金太郎」の舞台。登山口の公時神社は金太郎（坂田公時）をまつり、道の途中に「公時宿り石」がある'),
        ('casual', '山頂の茶屋', '山頂に金時茶屋と金太郎茶屋の2軒があり、食事ができる'),
        ('volcano', '箱根の火山', '箱根外輪山の一角にあるが、成り立ちは箱根火山の側火山という成層火山'),
        ('casual', 'まさかりの標柱', '山頂には金太郎のまさかりをかたどった標柱があり、記念撮影の定番'),
    ]),
}
for mid, (srcs, pts) in DATA.items():
    m = N[mid]
    assert len(pts) >= 3, mid
    m['featurePoints'] = [{'tag': t, 'label': l, 'text': x} for t, l, x in pts]
    m['featureSources'] = srcs
    m['featureCheckedAt'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('featurePoints を設定:', len(DATA), '／全', len(D))
