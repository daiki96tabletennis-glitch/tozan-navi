# -*- coding: utf-8 -*-
"""公式サイト・自治体の案内で確かめた、山小屋の営業期間と定員（手で書く。出典と確認日つき）。

自動で取り直す出典（長野県のポータル・山と溪谷オンラインの一覧・やまたん）が公式と食い違うときに、ここに書いた値を優先して表示する。
build_huts_from_nagano.py が data/huts.json の seasonFix / capacityFix に入れ、gen_huts_page.py と huts_excel.py が使う。

SEASON：'value' はページに出す営業期間（「4/27～5/31、7/1～11/3」の形にすると営業中マークの期間として読める）。
        None なら営業期間はいまの表示のまま、'note' だけ添える。'note' は出どころと補足（短く）。
CAPACITY：'value' は人数（数）、'text' は表示（「約50人」など。無ければ「◯人」）。
推測は書かない。来季の発表が出たら、出典を読んで書き直す（月次更新）。2026-10-20 に ChatGPT の監査の指摘を一次情報で確かめて作った。
"""

CHECKED = '2026-10-20'
TF = 'https://www.t-forest.com/alpsinfo/climber/lodgeinfo/'
YATSU = 'http://www.yatsugatake.gr.jp/'
KITAKATA = 'https://www.city.kitakata.fukushima.jp/soshiki/sangyo-y/43737.html'

SEASON = {
    '横尾山荘': {'value': '4/27～5/31、7/1～11/3', 'note': '11/3の宿泊まで。6月は修繕工事のため宿泊と外来食堂が休み（売店とテント場は利用可）',
              'source': 'https://www.yokoo-sanso.co.jp/news/1793/'},
    '中房温泉': {'value': '4/27～11/23', 'note': '宿泊の開始は4/27（日帰り入浴などは4/24から。公式4月16日のお知らせ）。終わりは長野県のポータル・予約サイトの記載',
              'source': 'https://nakabusa.com/'},
    '苗場山頂ヒュッテ－自然体験交流センター': {'value': '6/1～10/18', 'note': '完全予約制（電話）。栄村秋山郷観光協会の2026年の案内',
                                'source': 'http://sakae-akiyamago.com/stay/4888/'},
    '椹島ロッヂ': {'value': '4/26～11/15', 'note': '予定。東海フォレストの施設案内', 'source': 'https://www.t-forest.com/alpsinfo/sawarajima-lodge/'},
    '越百小屋': {'value': '営業休止（2026年度から。再開は未定）', 'note': '越百避難小屋は利用できる（長野県の観光サイト）',
             'source': 'https://db.go-nagano.net/topics_detail6/id%3D5784'},
    '大沢小屋': {'value': '2026年の営業は終了', 'note': '8月17日のお知らせ「今シーズンの大沢小屋の営業は終了いたしました」。例年は7月上旬～9月下旬',
             'source': 'http://www.harinoki.com/'},
    '雲海荘': {'value': '2026年の営業は終了', 'note': '公式9月10日のお知らせ。公式の営業期間の記載は「6月下旬～9月下旬」「7月上旬～9月上旬」の2通りある',
            'source': 'http://www.unkaiso.com/'},
    '東洋館': {'value': '7/1～9/9', 'note': '9/9の宿泊まで。2027年は7/1～9/8の宿泊の予定（公式）', 'source': 'https://www.fuji-toyokan.jp/news/39/'},
    '県営光岳小屋': {'value': '7/11～9/30', 'note': '9/30の宿泊まで（公式の予約ページ）', 'source': 'https://www.chillnn.com/1863f95fe2d74'},
    'ヒュッテみさやま': {'value': None, 'note': '冬季営業は2026年11月6日～2027年3月7日（金土日の予約が基本。1～2月は平日も相談可）',
                 'source': 'https://huttemisayama.net/%E5%86%AC%E5%AD%A3%E5%96%B6%E6%A5%AD%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6/'},
    '三国岳避難小屋（三国小屋）': {'value': None, 'note': '管理人の滞在は2026年7月3日～10月11日（喜多方市）。それ以外は無人の避難小屋', 'source': KITAKATA},
    '飯豊山避難小屋（本山小屋）': {'value': None, 'note': '管理人の滞在は2026年7月3日～10月12日（喜多方市）。それ以外は無人の避難小屋', 'source': KITAKATA},
    '飯豊切合小屋': {'value': '7/1～10/12', 'note': '管理人の2026年度の案内では、常駐は7/1～9/30、10月は2～4日・9～12日、10/12に小屋閉め（喜多方市の案内では管理人の滞在は7/3～10/12）。それ以外は無人の避難小屋', 'source': 'https://iide.3gaku.jp/'},
    'ホテル立山': {'value': '宿泊は2026年8月31日で終了', 'note': '宿泊サービス部門は8月31日の営業で終了。飲食・売店は営業を続けている（公式）',
              'source': 'https://h-tateyama.alpen-route.co.jp/'},
    '赤岳天望荘': {'value': None, 'note': '2026年の営業期間は公式サイトに記載がない（表示は長野県のポータルの2025年の記載）', 'source': YATSU},
    '美濃戸山荘': {'value': None, 'note': '2026年の営業期間は公式サイトに記載がない（表示は長野県のポータルの2025年の記載）', 'source': YATSU},
}
# 2026-10-21 追加（同じ監査の続き。各ページの原文で確認）
SEASON.update({
    '涸沢ヒュッテ': {'value': '4/27～5/10、6/1～11/3', 'note': '5/11～5/31は改修工事のため休業（公式の2026年度営業スケジュール）', 'source': 'https://karasawa-hyutte.com/inn/'},
    '五竜山荘': {'value': '4/25～5/5、6/20～10/12', 'note': '公式の2026年営業期間（残雪期を含む）', 'source': 'https://hakubakan.com/lodge/goryusanso/'},
    '二ノ池山荘': {'value': '7/1～10/11', 'note': '公式「令和８年は７月１日より、１０月１１日まで営業」', 'source': 'http://ninoike2905.com/'},
    '長衛小屋': {'value': '4/25～5/5、6/13～11/3', 'note': 'GWは素泊まりのみ。11/2の泊まりまで（公式2026年3月26日のお知らせ）', 'source': 'https://choei.ashiyasu.com/news/180/'},
    '北岳肩の小屋': {'value': '6/26～10/25', 'note': '10/24の宿泊まで（公式）', 'source': 'https://katanokoya.com/'},
    '剱御前小舎': {'value': '4/28～10/17', 'note': '10/17の宿泊まで。10/18は昼の売店だけ（公式）', 'source': 'https://www.tsurugigozengoya.net/'},
    '金峰山小屋': {'value': '4/下～11/下', 'note': '冬季は週末と年末年始のみ。3月～4月中旬は休み（公式）', 'source': 'https://www.kimpou.com/'},
    '馬場島荘': {'value': '5/上～11/中', 'note': '冬期は12月下旬～1月上旬。水曜定休（2026年は7/18～9/29は休まず営業）。予約サイトの小屋の案内', 'source': 'https://www.yamatan.net/hut/banbazimaso'},
    '富士一館': {'value': '7/1～9/10', 'note': '公式の全営業期間。2026年の営業は終了', 'source': 'https://www.fuji-ichikan.jp/'},
    '太子館': {'value': '6/30～9/9', 'note': '宿泊日の期間（公式の予約受付の案内）', 'source': 'https://www.mfi.or.jp/~taisikan/'},
    'LUCY尾瀬鳩待（旧 鳩待山荘）': {'value': '4/29～10/24', 'note': '公式の2026年の営業期間', 'source': 'https://hoshinoresorts.com/ja/hotels/lucyozehatomachi/'},
    'ロッヂ長兵衛': {'value': '通年', 'note': '12月～4月中旬は完全予約（公式）', 'source': 'http://www.choubei.info/'},
    '栂池山荘': {'value': '6/6～10/25', 'note': '宿泊は10/24が最終日（公式）', 'source': 'https://www.tsugaikesansou.jp/'},
    '萬岳荘': {'value': '4/29～11/24', 'note': '事前予約制（長野県の山小屋のページの2026年の記載）', 'source': 'https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/sotaikyo/yamagoya/yamagoya_cyuualps.html'},
    '蓼科山頂ヒュッテ': {'value': None, 'note': '2026～27年の年末年始（12/31・1/1泊）に特別営業（公式）', 'source': 'https://www.tateshinayama.com/newyear'},
})

CAPACITY = {
    '硫黄岳山荘': {'value': 80, 'note': '受け入れをコロナ前の半分以下に制限', 'source': 'https://iodake.jp/sanso/'},
    '中岳避難小屋': {'value': 5, 'source': TF},
    '赤石岳避難小屋': {'value': 10, 'source': TF},
    '椹島ロッヂ': {'value': 80, 'source': 'https://www.t-forest.com/alpsinfo/sawarajima-lodge/'},
    '駒ヶ岳頂上山荘': {'value': 50, 'text': '約50人', 'source': 'https://miyadakankou.co.jp/chojosansou'},
    '天狗荘': {'value': 100, 'text': '約100人', 'source': 'https://miyadakankou.co.jp/tengusou'},
    '赤岳天望荘': {'value': 138, 'source': YATSU},
    '美濃戸山荘': {'value': 61, 'source': YATSU},
    '七合目行場山荘': {'value': 30, 'source': 'http://www.ontake-7-gyouba.com/details.html'},
    '夜叉神ヒュッテ': {'value': 25, 'source': 'http://yashajin-hutte.com/'},
    '雲海荘': {'value': 60, 'source': 'https://www.unkaiso.com/about/index.html'},
    '平標山乃家': {'value': 12, 'note': '小屋泊まりの定員。隣の避難小屋（予約不要・10名ほど）は別', 'source': 'https://tairappyouyama.wixsite.com/yamanoie/'},
    '新七合目 御来光山荘': {'value': 140, 'source': 'https://www.fuji-tozan.com/mountain_lodge/goraiko_sanso/'},
    '尾瀬御池ロッジ': {'value': 60, 'source': 'https://www.oze-info.jp/ozh_stay/miikelodge/'},
    '尾瀬沼ヒュッテ': {'value': 112, 'source': 'https://www.oze-info.jp/ozh_stay/ozenumahutte/'},
}

CAPACITY.update({   # 2026-10-21 追加
    '涸沢小屋': {'value': 80, 'text': '80人程度', 'source': 'https://karasawagoya.com/facility/index.html'},
    '常念小屋': {'value': 186, 'source': 'https://www.mt-jonen.com/about/'},
    '蝶ヶ岳ヒュッテ': {'value': 150, 'text': '30人～最大150人程度', 'source': 'https://chougatake.com/stay/'},
    '冷池山荘': {'value': 120, 'text': '約120人', 'note': '公式の「2025年夏山」の今季の人数（コロナ前は250人）', 'source': 'https://www.kasimayari.jp/annai.htm'},
    '聖光小屋': {'value': 18, 'source': 'https://seikougoya.info/'},
    '仙水小屋': {'value': 20, 'source': 'https://www.minamialps-net.jp/yamagoya/021_sensui'},
    '夜叉神峠小屋': {'value': 15, 'source': 'https://www.city.minami-alps.yamanashi.jp/docs/yasyajintouge_koya.html'},
    '白根御池小屋': {'value': 61, 'source': 'https://shiraneoike.ashiyasu.com/about/'},
    '介山荘': {'value': 26, 'text': '2人部屋4室・3人部屋6室', 'source': 'http://kaizansou.jp/weekly.html'},
    '頂上富士館': {'value': 120, 'source': 'https://fujisanchou.com/guide-for-tw/'},
    '白山室堂': {'value': 750, 'text': '収容750人', 'note': '現在は宿泊定員を制限', 'source': 'https://hakusan-guide.or.jp/hakusan_stay/murodou/'},
    'ヒュッテ大槍': {'value': 96, 'note': '2020年から半分以下に制限', 'source': 'https://www.enzanso.co.jp/hutte-ooyari'},
    '大天荘': {'value': 150, 'note': '2020年から半分以下に制限', 'source': 'https://www.enzanso.co.jp/daitenso'},
    'ロッヂ長兵衛': {'value': 23, 'source': 'http://www.choubei.info/'},
    '県営光岳小屋': {'value': 20, 'text': '20人（小屋泊）', 'source': 'https://www.chillnn.com/1863f95fe2d74'},
})


def apply(h):
    """data/huts.json の1軒に、確かめた値を入れる（無ければ消す）"""
    s, c = SEASON.get(h['name']), CAPACITY.get(h['name'])
    if s:
        h['seasonFix'] = dict(s, checkedAt=CHECKED)
    else:
        h.pop('seasonFix', None)
    if c:
        h['capacityFix'] = dict(c, checkedAt=CHECKED)
    else:
        h.pop('capacityFix', None)
    return h
