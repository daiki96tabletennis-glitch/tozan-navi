#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""マイカー規制で、駐車場からバスに乗り換える山に、そのバスの案内（区間・運賃・運行期間・案内ページ）を入れる（2026-10-19）。
規制バナーの中に「駐車場からのバス」の枠として出す（gen_mountain_pages.py の render_car_shuttle）。
運賃は各運行会社・自治体の公式の資料で確かめた値だけ（推測・按分なし）。出典は sourceUrl、確認日は lastVerified。
七倉（烏帽子岳・野口五郎岳）は、高瀬ダムまでタクシーだけでバスが無いので対象外。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
V = '2026-10-19'
ASHIYASU = {'route': '市営芦安駐車場 → 広河原', 'fare': '路線バス 1,450円、乗合タクシー 1,400円（大人片道。運賃とは別に利用者協力金300円）',
            'period': '2026年6月26日〜11月3日', 'validTo': '2026-11-03',
            'note': '路線バスは山梨交通、乗合タクシーは芦安観光タクシー。11月3日はサイクルイベントのため運行できない時間帯があります',
            'url': 'https://www.pref.yamanashi.jp/documents/2071/r8-mycar.pdf', 'linkText': '山梨県 2026年のマイカー規制と時刻表・運賃（PDF）'}
TODAI = {'route': '戸台パーク → 北沢峠（南アルプス林道バス）', 'fare': '大人片道 1,150円（18L以上のザックなどは手回り品料金220円）',
         'period': '2026年6月1日〜11月3日（北沢峠まで）', 'validTo': '2026-11-03',
         'url': 'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/174h_nok20240320.html', 'linkText': '伊那市 南アルプス林道バスの時刻・運賃'}
SAWANDO = {'route': '沢渡（さわんど）→ 上高地（シャトルバス）', 'fare': '大人片道 1,600円、往復 3,000円',
           'period': '2026年4月17日〜11月15日', 'validTo': '2026-11-15',
           'url': 'https://www.alpico.co.jp/traffic/local/kamikochi/sawando/', 'linkText': 'アルピコ交通 さわんど〜上高地の時刻・運賃',
           'sourceUrl': 'https://www.alpico.co.jp/traffic/datas/files/2026/03/13/d8627e1e8ba4b728cca0151d4cb577bcb0118234.pdf'}
ALPEN = {'route': '立山駅 → 室堂（立山ケーブルカー・立山高原バス）', 'fare': '大人片道 4,090円、往復 7,380円',
         'note': '運賃は2026年2月27日現在（立山黒部アルペンルートの公式サイト）',
         'url': 'https://www.alpen-route.com/access_new/fare/person/', 'linkText': '立山黒部アルペンルートの運賃',
         'sourceUrl': 'https://www.alpen-route.com/access_new/fare/person/route_data.json'}
HATANAGI = {'route': '畑薙第一ダム → 椹島（特種東海フォレストの送迎バス）', 'fare': '往復無料（特種東海フォレストの山小屋・ロッヂに1泊以上する人だけが乗れます）',
            'note': '運賃を払って乗る路線バスではないため、宿泊しない人は乗れません',
            'url': 'https://www.t-forest.com/alpsinfo/bus/', 'linkText': '特種東海フォレスト 送迎バスの案内'}
S = {
    'kitadake': ASHIYASU, 'ainodake': ASHIYASU, 'noutori': ASHIYASU,
    'komagatake': TODAI, 'senjogatake': TODAI,
    'yari': SAWANDO, 'hotaka': SAWANDO, 'chogatake': SAWANDO,
    'tateyama': ALPEN, 'tsurugi': ALPEN,
    'arakawadake': HATANAGI, 'akaisidake': HATANAGI,
    'norikura': {'route': '乗鞍高原観光センター → 乗鞍山頂（畳平）', 'fare': '大人 2,450円（上り。乗鞍岳自動車利用適正化協力金200円を含む）',
                 'period': '2026年7月1日〜10月31日', 'validTo': '2026-10-31', 'note': '予約優先制（乗車日の1か月前の同じ日の0:00から予約できます）',
                 'url': 'https://www.alpico.co.jp/traffic/local/kamikochi/echoline/', 'linkText': 'アルピコ交通 乗鞍山頂シャトルバス',
                 'sourceUrl': 'https://www.alpico.co.jp/traffic/datas/files/2026/05/06/a973d48ce04cd80479f5d5530b12742189570fac.pdf'},
    'shibutsu': {'route': '尾瀬戸倉 → 鳩待峠（乗合バス・乗合タクシー）', 'fare': '大人片道 1,300円',
                 'period': '2026年4月18日〜11月3日', 'validTo': '2026-11-03',
                 'url': 'https://www.pref.gunma.jp/uploaded/attachment/697963.pdf', 'linkText': '群馬県 尾瀬のマイカー規制と乗合バス（PDF）'},
    'hakusan': {'route': '市ノ瀬 → 別当出合（シャトルバス）', 'fare': '大人片道 1,000円、往復 2,000円',
                'period': 'マイカー規制の日だけ運行（規制日は石川県の案内）', 'note': '運賃は、石川県の案内ページが紹介している運行会社（株式会社マップ）のページの表記',
                'url': 'https://map.ishikawa.jp/hakusan-bus-2025/', 'linkText': '白山登山バスの運賃・運行日',
                'sourceUrl': 'https://www.pref.ishikawa.lg.jp/hakusan/tozaninf/peak2.html'},
    'fuji': {'route': '水ヶ塚駐車場 → 富士宮口五合目（シャトルバス）', 'fare': '大人片道 1,320円、往復 2,400円',
             'period': '2026年7月10日〜9月10日（富士宮口のマイカー規制期間）', 'validTo': '2026-09-10',
             'url': 'https://www.pref.shizuoka.jp/machizukuri/doro/fujisandoro/1029179.html', 'linkText': '静岡県 富士山マイカー規制'},
}
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
assert set(S) <= set(N), set(S) - set(N)
for mid, v in S.items():
    c = dict(v)
    c.setdefault('sourceUrl', c['url'])
    c['lastVerified'] = V
    N[mid]['carShuttle'] = c
    N[mid]['mountainUpdated'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(S), '山')
