"""装備カレンダーを山小屋の現地報告（5年分）で見直す（2026-11-17。運営者の指示「怪しい山を再調査して修正方針を固めて」→「修正作業を進めて」）

調べ方：山と溪谷オンラインの「山岳最新情報」（山小屋・ビジターセンターが日付つきで書く現地の報告）の過去ログ
（https://www.yamakei-online.com/mt_info/past.php?id=<施設>&yy=<年>。2022〜2026年の5年分・38施設・約5,000件）を読み、
代表コースの道の上に雪・凍結があるかを月ごとに見た。決まり（運営者と決めた）：
- 付けるのは、代表コースの道の上に、その時期は例年（5年のうち3年以上）傾斜のある雪か凍結がある月だけ。山に雪があっても道に無ければ付けない
- 月の一部だけなら月の途中で分ける（切替日は11・16・21日のどれか）。1〜2年だけ要った月は区分を変えず、装備カードの文で補う
- 冬山装備との境：山小屋が「前爪アイゼン・ピッケル」「雪山装備」と書く時期が冬山装備。「軽アイゼン」「チェーンスパイク」「お守り」は軽アイゼン等
- 「チェーンスパイクでは不可」と山小屋が書く山は、装備カードの文で6本爪以上と書く
- 出典が取れない変更（軽くするのも重くするのも）はしない
確からしさが中のもの（南アルプスのほかの山の秋・三頭山などの3月・赤城山の5月など）と、出典が取れなかったもの（経ヶ岳・西吾妻山の12月・飯縄山など）は入れていない。

直すもの（出典は EVIDENCE）
- 夏の残雪：木曽駒ヶ岳 7月＝不要／槍ヶ岳・奥穂高岳・剱岳 7月＝20日まで軽アイゼン等／唐松岳 7月＝15日まで／立山 7月＝10日まで／妙高山 7月＝20日まで
- 秋：北アルプスの16山の冬山装備の始まり 10/11 → 10/21／甲斐駒ヶ岳 10月＝軽アイゼン等・11/21から冬山装備／木曽駒ヶ岳 10月＝軽アイゼン等（11月から冬山装備）
  ／甲武信ヶ岳・金峰山 11月＝軽アイゼン等／谷川岳 11/11から冬山装備／瑞牆山 10月＝不要
- 春：三ツ峠山・大岳山 3月＝軽アイゼン等／瑞牆山 5月＝不要／蛭ヶ岳・丹沢山 4月＝10日まで軽アイゼン等
- スノーシュー：浅間山に12月を足す（高峰温泉）
- 装備カードの文：白馬岳 7月・金峰山 4月は「チェーンスパイクでは滑りやすい。6本爪以上」
- よくある質問のシーズンの答え：装備カレンダーと食い違う13山（「5月〜11月が登りやすい」の12山など）と、白馬岳の難易度の答え（代表コースは栂池から）
新構造の山は conditions（gearMonthly・gearSplits）を直して build_derived.derive で作り直す。旧構造の山は gearCalendar と季節の4項目を直す。
装備カード（gear-data.json）は、区分が変わる月の靴・アイゼン・ピッケルと、来月分のアイゼンを gearCalendar に合わせる
（fix_gear_cards_2026_11.py と同じ決まり）。月の途中の切替の見出しは fix_split_month_gear_2026_11.py を中で呼ぶ。手で作った記事・まとめの装備カードの写しも作り直す。
何度流しても同じ結果。このあと build_packing_mountains.py → gen_mountain_pages.py --all → gen_recommend_gear.py → gen_line_articles.py --all
→ sync_search_hubs.py --write → gen_huts_page.py → build_winter_find.py → gen_find_winter.py → gen_winter_specials.py → check_pages.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MP = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'migrations'))
import build_derived  # noqa: E402
import fix_split_month_gear_2026_11 as SPLIT  # noqa: E402
import add_gear_new_mountains_2026_11 as A  # noqa: E402
from add_snowshoe_months_2026_11 import TEIBAN_CARD  # noqa: E402

DAY = '2026-11-17'
YK = 'https://www.yamakei-online.com/mt_info/past.php?id=%s&yy=%s'
HUT = {'1035': '宝剣山荘', '1046': '槍ヶ岳山荘', '1047': '穂高岳山荘', '1048': '涸沢ヒュッテ', '1036': '剱澤小屋', '1096': '白馬大池山荘',
       '1039': '唐松岳頂上山荘', '1037': '立山室堂山荘', '1016': '高谷池ヒュッテ', '1091': '甲斐駒ヶ岳 七丈小屋', '1073': '甲武信小屋',
       '1015': '瑞牆山荘', '1010': '谷川岳登山指導センター', '1088': '三つ峠山荘', '1065': '御岳ビジターセンター', '1013': '蛭ヶ岳山荘',
       '1069': '高峰温泉'}

# 根拠（山小屋の報告の日付と文。山と溪谷オンラインの過去ログ。2026-11-17 に読んだ）
EVIDENCE = {
    '木曽駒ヶ岳 7月は不要': [
        ('1035', '2022-07-14', '千畳敷から八丁坂～稜線、稜線上の登山道は残雪なし。駒飼の池～濃ヶ池方面では10m程の雪渓が2～3本残っています'),
        ('1035', '2023-06-21', '八丁坂登山道の残雪は夏道が完全に出ています'),
        ('1035', '2024-06-28', 'カール内の雪は少なくなり、八丁坂は夏道が完全に出ています'),
        ('1035', '2026-06-12', 'カール内からの登山道は、ほぼ夏道が現れました'),
    ],
    '槍ヶ岳 7月は20日まで軽アイゼン等': [
        ('1046', '2023-07-13', '槍沢ルートは軽アイゼンあると安心'),
        ('1046', '2025-07-02', '槍沢は一部残雪あり（暫時雪切りします）軽アイゼンあると安心'),
        ('1046', '2026-07-16', '槍沢は雪慣れない方は軽アイゼンがお守り(南岳新道はアイゼン必要)'),
        ('1046', '2022-07-28', '主なルートに支障なし'),
    ],
    '奥穂高岳 7月は20日まで軽アイゼン等': [
        ('1047', '2022-07-13', '涸沢～稜線まで心配な方は軽アイゼンをお守りに'),
        ('1047', '2023-07-12', '涸沢からの穂高岳へはまだ軽アイゼンがお守りです'),
        ('1047', '2025-07-08', 'ザイデングラート残雪あり軽アイゼン使用を（慣れない方は爪多いアイゼンで）'),
        ('1047', '2024-07-20', '涸沢からの登山道の残雪はほぼ融雪'),
        ('1047', '2024-07-26', '登山道上の残雪はありません'),
    ],
    '剱岳 7月は20日まで軽アイゼン等': [
        ('1036', '2022-07-20', '剱岳までは一部雪渓歩きがあり心配な方は軽アイゼンをお守りに'),
        ('1036', '2026-07-16', '剱岳一般ルートまだ残雪あり雪慣れない方は6本爪アイゼン用意を'),
        ('1036', '2024-07-22', '剣岳一般ルートは夏道。アイゼンも不要'),
        ('1036', '2026-07-25', '融雪進み雪渓も縮小。剱岳別山尾根ルートの登山道通常通り通行可'),
    ],
    '唐松岳 7月は15日まで軽アイゼン等': [
        ('1039', '2023-07-04', '八方尾根はほぼ融雪しましたが一部雪渓あり。軽アイゼンがお守りです'),
        ('1039', '2024-07-03', '融雪進む八方尾根。間もなく夏道となります。念のため軽アイゼンあると安心'),
        ('1039', '2025-07-02', '八方尾根は冬道夏道混在で残雪あり軽アイゼンの用意を（特に下り注意）'),
        ('1039', '2026-07-01', '八方尾根は残雪あり軽アイゼンの用意を'),
        ('1039', '2023-07-12', '八方尾根＆五龍岳方面に大きな支障なし'),
    ],
    '立山 7月は10日まで軽アイゼン等': [
        ('1037', '2023-07-06', '登山道の一部に残雪あります（軽アイゼンあると安心）'),
        ('1037', '2024-07-03', '室堂～一の越＆雷鳥平～剣御前など残雪ありチェーンスパイクより軽アイゼン推奨'),
        ('1037', '2025-07-02', '剣御前小屋、室堂山、大走りの下りは軽アイゼンの用意を'),
        ('1037', '2024-07-10', '室堂平ほぼ夏道'),
        ('1037', '2025-07-10', '例年並みの融雪、雪渓箇所あるもアイゼン不要（下り慎重に）'),
    ],
    '妙高山 7月は20日まで軽アイゼン等': [
        ('1016', '2022-07-14', '主ルートに支障の連絡なし（妙高岳へはアイゼンあると安心）'),
        ('1016', '2023-07-11', '妙高山は6本爪アイゼンがお守り'),
        ('1016', '2023-07-19', '妙高山はチェーンスパイクがお守り'),
        ('1016', '2024-07-02', '妙高山は6本爪アイゼン推奨'),
    ],
    '白馬岳（栂池から）7月は6本爪以上': [
        ('1096', '2025-07-04', '白馬乗鞍は爪多いアイゼン必要（チェーンスパイクNG）'),
        ('1096', '2025-07-14', '白馬乗鞍はアイゼンとストック必要（チェーンスパイク厳しい）'),
        ('1096', '2026-07-03', '白馬乗鞍岳付近に雪渓あり8本爪アイゼンとピッケル必要(フィクスロープなし)'),
        ('1096', '2024-08-07', '白馬乗鞍岳上部の雪渓もアイゼン不要'),
    ],
    '北アルプスの冬山装備は10/21ごろから': [
        ('1046', '2022-10-27', '標高2500m以上で積雪あり、軽アイゼンは必須です'),
        ('1046', '2022-11-01', '本日降雪中。山荘前積雪あり。冬装備+軽アイゼンは必須'),
        ('1046', '2023-10-06', '昨日吹雪。稜線は積雪と凍結。前爪アイゼン＋冬装備必要'),
        ('1047', '2024-10-23', '今後は天候次第で雪や凍結あり。防寒＆アイゼンの携行を'),
        ('1047', '2024-10-29', '一瞬で冬になる時期、天候次第で降雪へ。防寒＆アイゼン必要'),
        ('1037', '2025-10-30', '10/27初冠雪。断続的に続く降雪で20～30cm（吹溜り1m）積雪'),
        ('1046', '2026-10-28', '10/28初冠雪。防寒装備（手袋など小物も）＋軽アイゼンなど必携'),
        ('1046', '2026-10-31', '雪山装備必要（積雪20～30、吹溜り50cm）'),
    ],
    '甲斐駒ヶ岳 10月は軽アイゼン等・11/21から冬山装備': [
        ('1091', '2022-11-17', '防寒着とチェーンスパイクをお忘れなく'),
        ('1091', '2022-11-24', '小屋前積雪15cm。小屋より上はさらに積雪増。前爪アイゼン＋ピッケル必須のコンディション'),
        ('1091', '2023-11-16', '11/15山頂へはチェーンスパイク必要'),
        ('1091', '2023-11-22', '山頂へはアイゼン＆ピッケルの冬装備必要'),
        ('1091', '2024-11-21', '登山道に積雪や凍結があります。滑り止め（チェーンアイゼンや軽アイゼン等)必要'),
        ('1091', '2025-11-21', '山頂残雪あり雪山装備必要'),
        ('1091', '2026-11-13', '小屋から上は凍結することあり軽アイゼンなど用意を'),
    ],
    '木曽駒ヶ岳 10月は軽アイゼン等': [
        ('1035', '2022-10-28', '3日前に降った雪が凍結により滑りやすくなっています'),
        ('1035', '2023-10-27', '周囲は雪が薄く被っています。安全登山の御守りとしてチェーンスパイクや軽アイゼンの用意を'),
        ('1035', '2022-11-11', '積雪量は3～5cm、冬装備を整えて登山を楽しんでください'),
    ],
    '甲武信ヶ岳 11月は軽アイゼン等': [
        ('1073', '2022-11-10', '日陰は残雪凍結があり軽アイゼンなど必要'),
        ('1073', '2023-11-09', 'チェーンスパイク(軽アイゼン)はお守りとして携行を'),
        ('1073', '2025-11-11', '万全の防寒対策＋チェーンスパイクや軽アイゼンの用意を'),
        ('1073', '2026-11-10', '11/9初雪。防寒具(手袋なども)＋軽アイゼンやチェーンスパイクの用意を'),
    ],
    '金峰山 11月は軽アイゼン等・瑞牆山 10月は不要': [
        ('1015', '2022-11-16', '初冬となり毎朝氷が張るため張り滑り止めの用意を'),
        ('1015', '2023-11-16', '標高の高い所では凍結が予想されます。チェーンスパイクの携行を'),
        ('1015', '2025-11-13', '冬となり氷点下の日も！防寒具＋雨具＋ライト＋軽アイゼンなど必携'),
        ('1015', '2026-11-11', '金峰山は冠雪、瑞牆山凍結→軽アイゼン+防寒具(手袋なども)必携'),
        ('1015', '2022-10-25', '10/25朝は初雪で屋根が白くなりました。昼ころには融けましたが念のため軽アイゼンなどの用意を'),
        ('1015', '2023-10-27', '初雪はまだですが防寒防風対策必要'),
    ],
    '金峰山 4月は6本爪以上・瑞牆山 5月は不要': [
        ('1015', '2023-04-19', '金峰山はアイゼン必要(4本爪やチェーンスパイクでは不適切)。瑞牆山も軽アイゼンがお守りです'),
        ('1015', '2024-04-17', 'GWまでは瑞牆山6本爪アイゼン推奨（チェーンスパイクは厳しい）。金峰山6本爪以上で'),
        ('1015', '2024-04-25', 'GW中、瑞牆山チェーンスパイク。金峰山6本爪アイゼンで'),
        ('1015', '2025-05-13', '金峰山は軽アイゼンなどの用意を'),
    ],
    '谷川岳 11/11から冬山装備': [
        ('1010', '2022-11-22', '凍結と積雪に注意。これからはしっかりとした冬山装備が必要です'),
        ('1010', '2023-11-14', '標高1500m以上は凍結しています。雪山装備は必携です'),
        ('1010', '2024-11-12', '現在はほぼ解けていますが、しっかりとした冬山装備が必要です'),
        ('1010', '2026-11-10', '稜線、山頂付近には雪がありますので冬山装備が必要です'),
    ],
    '三ツ峠山 3月は軽アイゼン等': [
        ('1088', '2022-03-23', '3/22に20cmほどの積雪'),
        ('1088', '2024-03-18', 'どのルートにも残雪や凍結箇所があります。滑り止めの携行に加え、足元の防水対策を'),
        ('1088', '2025-03-19', '昨夜から降雪が続き、20cm以上積もっています'),
        ('1088', '2026-03-26', '山頂付近の標高で10〜15cmほどの積雪'),
    ],
    '大岳山 3月は軽アイゼン等': [
        ('1065', '2022-03-10', '軽アイゼンやチェーンスパイクの携行を（ロツクガーデンも凍結）'),
        ('1065', '2024-03-22', '大岳方面は軽アイゼンなど必要'),
        ('1065', '2025-03-21', '参道を除きチェーンスパイクや軽アイゼン必要'),
    ],
    '蛭ヶ岳・丹沢山 4月は10日まで軽アイゼン等': [
        ('1013', '2022-04-04', '4/3からの降雪で10時の山頂は積雪40cm。吹き溜まり70cm'),
        ('1013', '2022-04-11', '先週大雪だった山頂の雪はほとんど融けましたが、登山にはアイゼンと防寒具が必要です'),
        ('1013', '2025-04-03', '3月終盤の雨と雪で主脈稜線は霧氷。積雪残雪あり'),
        ('1013', '2026-04-14', 'まだ氷点下の朝あり装備油断なく'),
    ],
    '浅間山 12月はスノーシュー': [
        ('1069', '2022-12-20', '週末の雪で50cm積もっています。スノーシューを楽しめる季節になりました'),
        ('1069', '2022-12-26', '登山道では70cm以上の積雪があり、スノーシューが必要です'),
        ('1069', '2024-12-30', 'パウダースノーの雪がたくさん積もり、スノーシューを楽しめます'),
    ],
}

L, W, N = 'light_crampons', 'winter_gear', 'no_crampons'


def sp(before, after, day):
    return {'split': True, 'before': before, 'after': after, 'changeDate': day}


NALPS_OCT_OLD = ['tsurugi', 'tateyama', 'harinokidake', 'kurobegorodam', 'kashimayari', 'kasagatake', 'nishihotaka', 'otenshoudake',
                 'noguchigoro', 'yakushidake']
NALPS_OCT = NALPS_OCT_OLD + ['yari', 'hotaka', 'shirouma', 'goryudake', 'jonengatake', 'norikura']
# 旧構造の山：gearCalendar の月 → 新しい値（前の値の確かめ）
OLD = {
    'tsurugi': {7: (L, sp(L, N, 21))},
    'tateyama': {7: (N, sp(L, N, 11))},
    'myoko': {7: (N, sp(L, N, 21))},
    'kobushigatake': {11: (W, L)},
    'mizugaki': {5: (L, N), 10: (L, N)},
    'mitsutoge': {3: (N, L)},
    'otake': {3: (N, L)},
    'hirugata': {4: (L, sp(L, N, 11))},
    'tanzawa': {4: (L, sp(L, N, 11))},
}
for _mid in NALPS_OCT_OLD:
    OLD.setdefault(_mid, {})
# 新構造の山：conditions を直す（gearSplits は月 → 値、None は消す。gearMonthly は月 → 値）
SSOT = {
    'kisokoma': {'monthly': {7: 'normal'}, 'splits': {10: None}},
    'yari': {'splits': {7: sp(L, N, 21)}},
    'hotaka': {'splits': {7: sp(L, N, 21)}},
    'karamatsu': {'splits': {7: sp(L, N, 16)}},
    'komagatake': {'splits': {10: None, 11: sp(L, W, 21)}},
    'kinpusan': {'monthly': {11: 'snow_caution'}},
    'tanigawa': {'splits': {11: sp(L, W, 11)}},
}
for _mid in ('shirouma', 'goryudake', 'jonengatake', 'norikura'):
    SSOT.setdefault(_mid, {})

CRAMPON_TEXT = {
    ('shirouma', 7): '白馬乗鞍岳の急な雪渓を越えます。7月は雪が固く残る年が多く、チェーンスパイクでは滑りやすいので、6本爪以上のアイゼンを持っていきましょう。事前に最新の残雪情報を確認してください。',
    ('kinpusan', 4): '山頂付近に残雪・凍結が残る時期です。チェーンスパイクでは滑りやすいので、6本爪以上のアイゼンを持っていきましょう。事前に最新の積雪・凍結情報を確認してください。',
}

ASAMA_SRC = [{'url': YK % ('1069', y), 'date': d, 'kind': 'official', 'says': '高峰温泉（車坂峠の近く）の現地情報「%s」' % t}
             for h, d, t in EVIDENCE['浅間山 12月はスノーシュー'] for y in [d[:4]]]

# よくある質問（シーズン）の答え。前の文 → 新しい文（前の文が見つからず新しい文も無ければ止まる）
FAQ = {
    'tateyama': ('立山の登山シーズンは7月〜10月が目安です。実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。',
                 '立山の登山シーズンは7月〜10月上旬が目安です。7月上旬は室堂から稜線への道に雪渓が残り、軽アイゼン等（チェーンスパイク・6本爪アイゼン等）があると安心です。'
                 '10月下旬からは12本爪アイゼン・ピッケル等の冬山装備が要る年が多くなります。実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。'),
    'myoko': ('6月は登山道に雪渓が残り、軽アイゼン等が必要です。',
              '6月〜7月中旬は山頂の近くに雪渓が残り、6本爪アイゼンなどの軽アイゼン等が必要です。'),
    'kobushigatake': ('甲武信ヶ岳の登山シーズンは6月〜10月が目安です。実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。',
                      '甲武信ヶ岳の登山シーズンは6月〜10月が目安です。10月〜11月と4月〜5月は凍結や残雪があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が要ります。'
                      '12月〜3月は12本爪アイゼン・ピッケル等の冬山装備が要る時期です。実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。'),
    'mizugaki': ('瑞牆山の登山シーズンは5月〜11月が目安です。実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。',
                 '瑞牆山の登山シーズンは5月〜10月が目安です。11月〜4月は山頂直下などに凍結や残雪があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が要ります。'
                 '実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。'),
    'mitsutoge': ('通年（冬季アイゼン推奨）が登りやすいシーズンです。',
                  '三ツ峠山は通年登れます。12月〜3月は登山道に積雪や凍結があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が要ります。'
                  '積雪・凍結の状況は年によって変わるため、直前の最新情報を確認してください。'),
    'otake': ('12月〜2月は積雪や凍結があり', '12月〜3月は積雪や凍結があり'),
    'hirugata': ('蛭ヶ岳の登山シーズンは通年（冬季積雪注意）が目安です。実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。',
                 '蛭ヶ岳は通年登られています。12月〜4月上旬は積雪や凍結があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が要ります。'
                 '実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。'),
    'tanzawa': ('12月〜4月の冬季は積雪・凍結のため', '12月〜4月上旬の冬季は積雪・凍結のため'),
    'asama': ('浅間山の登山シーズンは活火山のため入山規制あり・確認要が目安です。実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。',
              '浅間山は活火山で、前掛山へ登れるかは噴火警戒レベルで変わります（気象庁・小諸市の最新情報を確認）。雪の無い6月〜9月が登りやすく、5月と10月は軽アイゼン等（チェーンスパイク・6本爪アイゼン等）が、'
              '11月〜4月は12本爪アイゼン・ピッケル等の冬山装備が要ります。12月〜3月は車坂峠から黒斑山へスノーシューで歩くのが定番です。'
              '実際の残雪・気象状況は年によって変動するため、直前の最新情報も確認してください。'),
    'akagi': ('4〜11月がおすすめです。10月の紅葉が美しい。12〜3月は積雪・凍結があるため軽アイゼンが必要です。',
              '雪の心配なく歩けるのは6月〜10月で、10月の紅葉が美しい。11月〜5月は積雪・凍結があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が要ります。'
              '積雪・凍結の状況は年によって変わるため、直前の最新情報を確認してください。'),
    'tairappyo': ('12〜4月は積雪により一般ルートへの入山は困難です。',
                  '12月〜4月は12本爪アイゼン・ピッケル等の冬山装備が要る雪山で、12月は深い雪にスノーシューやワカンも要ります。冬山の経験者向けです。'),
}
# 「5月〜11月が登りやすいシーズンです」（冬山装備の月を含む。ひな形の文）を装備カレンダーに合う文にする
TEMPLATE_OLD = '5月〜11月が登りやすいシーズンです。冬季は積雪・凍結に注意が必要です。'
TEMPLATE_IDS = ['yarigatake2', 'gakedake', 'hiragadake', 'kasagatake', 'arakawadake', 'akaisidake', 'hijiridade', 'terkari',
                'yakushidake', 'kurobegorodam', 'eboshidake_kita', 'noguchigoro']
SHIROUMA_OLD = '猿倉からの往復は標高差1,700m・所要13時間。大雪渓は夏でも雪が残り軽アイゼン必須で、落石の危険がある区間です。日帰りは非現実的で山小屋泊が前提の山です。'

RANK = {N: 0, L: 1, W: 2}
LEGEND = build_derived.LEGEND
CLS = {N: 's-ok', L: 's-gear', W: 's-hard', 'closed': 's-closed'}


def b(v):
    return v if isinstance(v, str) else v['before']


def cats(v):
    return {v} if isinstance(v, str) else {v['before'], v['after']}


def jun(d):
    return '上旬' if d <= 10 else ('中旬' if d <= 20 else '下旬')


def circ(months):
    """月の番号 → 「11月〜4月」「6月・10月」（12月から1月へまたがる並びもつなげる）"""
    ms = sorted(set(months))
    if not ms:
        return '不可'
    if len(ms) == 12:
        return '通年'
    runs, cur = [], [ms[0]]
    for x in ms[1:]:
        if x == cur[-1] + 1:
            cur.append(x)
        else:
            runs.append(cur)
            cur = [x]
    runs.append(cur)
    if len(runs) > 1 and runs[0][0] == 1 and runs[-1][-1] == 12:
        runs[0] = runs.pop() + runs[0]
    runs.sort(key=lambda r: r[0] if r[0] != 12 or len(r) == 1 else 0)
    return '・'.join(f'{r[0]}月〜{r[-1]}月' if len(r) > 1 else f'{r[0]}月' for r in runs)


def template_answer(m):
    """ひな形の答えの代わり：装備カレンダーから作る（月の途中で変わる月は上旬・中旬・下旬で書く）"""
    cal = m['gearCalendar']
    ok = [i + 1 for i, v in enumerate(cal) if v == N]
    light = [i + 1 for i, v in enumerate(cal) if v == L]
    winter = [i + 1 for i, v in enumerate(cal) if v == W]
    split = [(i + 1, v) for i, v in enumerate(cal) if isinstance(v, dict)]
    assert all(v['before'] == L and v['after'] == W for _, v in split), m['id']
    assert len(split) <= 1, m['id']
    lt = circ(light) if light else ''
    wt = circ(winter)
    if split:
        mo, v = split[0]
        d = v['changeDate']
        lt = '・'.join(x for x in [lt, f'{mo}月{jun(d - 1)}まで'] if x)
        # 冬山装備は、切り替わる月の後半から続く月まで
        end = mo
        while (end % 12 + 1) in winter:
            end = end % 12 + 1
        assert set(winter) == set(((mo + k - 1) % 12) + 1 for k in range(1, (end - mo) % 12 + 1)), m['id']
        wt = f'{mo}月{jun(d)}から{end}月まで'
    parts = [f"{m['name']}の登山シーズンは{circ(ok)}が目安です。"]
    if lt:
        parts.append(f'{lt}は残雪や凍結で軽アイゼン等（チェーンスパイク・6本爪アイゼン等）が、')
    parts.append(f'{wt}は12本爪アイゼン・ピッケル等の冬山装備が要る時期です。')
    parts.append('残雪や凍結の状況は年によって変わるため、直前の最新情報を確認してください。')
    return ''.join(parts)


def shirouma_answer(m):
    r = m['routes'][0] if m.get('representativeRouteId') is None else [x for x in m['routes'] if x['id'] == m['representativeRouteId']][0]
    elev = re.sub(r'^\+', '', str(r.get('elevation') or ''))
    return ('代表コースの栂池自然園からの往復は%s・標高差%sで、山小屋に泊まるのが前提です。7月は白馬乗鞍岳の急な雪渓を通り、6本爪以上のアイゼンが要る年が多くあります。'
            '猿倉から大雪渓を登るコースも、夏でも雪渓を歩くのでアイゼンが要り、落石の危険がある区間です。') % (r['time'], elev)


def set_cards(G, mid, mo, cat):
    """その月（前半）の区分が変わったときの靴・アイゼン・ピッケル"""
    cards = G[mid][str(mo)]
    has = [c for c in cards if c['c'] == 'crampon']
    kind = None if not has else (W if 'G12' in has[0]['p'] else L)
    want = None if cat == N else cat
    if kind == want:
        return False
    assert want != W, (mid, mo)   # 冬山装備に上げる月は無い
    if want is None:
        cards[:] = [c for c in cards if c['c'] not in ('crampon', 'axe')]
        return True
    # 軽アイゼン等：冬山装備のカード（靴・12本爪・ピッケル）からは、同じ山の軽アイゼン等の月の靴に替える
    if kind == W:
        tmpl = None
        for k in range(1, 12):
            for mm in (mo - k, mo + k):
                m2 = (mm - 1) % 12 + 1
                c2 = G[mid][str(m2)]
                cr = [c for c in c2 if c['c'] == 'crampon']
                if cr and 'G12' not in cr[0]['p']:
                    tmpl = c2
                    break
            if tmpl:
                break
        assert tmpl, (mid, mo)
        shoe = [dict(c) for c in tmpl if c['c'] == 'shoe']
        out = []
        for c in cards:
            if c['c'] == 'shoe':
                out.extend(shoe)
            elif c['c'] == 'crampon':
                out.append(dict(A.LIGHT))
            elif c['c'] == 'axe':
                continue
            else:
                out.append(c)
        cards[:] = out
        return True
    idx = max(i for i, c in enumerate(cards) if c['c'] in ('shoe', 'helmet', 'rain')) + 1
    cards.insert(idx, dict(A.LIGHT))
    return True


def fix_next(G, mid, cal):
    """来月分のアイゼン（fix_gear_cards_2026_11.py と同じ決まり）。月の途中で変わる月でなくなった月の見出し（l）は外す"""
    for mo in range(1, 13):
        cards = G[mid][str(mo)]
        v = cal[mo - 1]
        cur = b(v)
        if cur == 'closed':
            continue
        nxt = v['after'] if isinstance(v, dict) else b(cal[mo % 12])
        nx = [c for c in cards if c['c'] == 'crampon_next']
        got = None if not nx else (W if 'G12' in nx[0]['p'] else L)
        if nxt in RANK and RANK[nxt] > RANK[cur]:
            want = nxt
        elif cur == W and nxt == L and got == L:
            want = got
        else:
            want = None
        stale = nx and 'l' in nx[0] and not (isinstance(v, dict) and v['after'] == W)
        if got != want or stale:
            cards[:] = [c for c in cards if c['c'] != 'crampon_next']
            if want:
                idx = max(i for i, c in enumerate(cards) if c['c'] in ('shoe', 'rain', 'crampon')) + 1
                cards.insert(idx, dict(A.WINTER_NEXT if want == W else A.LIGHT_NEXT))


def main():
    M = json.load(open(MP, encoding='utf-8'))
    G = json.load(open(GP, encoding='utf-8'))
    by = {m['id']: m for m in M}
    TH = json.load(open(os.path.join(ROOT, 'data', 'trailheads.json'), encoding='utf-8'))
    AC = json.load(open(os.path.join(ROOT, 'data', 'accesses.json'), encoding='utf-8'))
    before_cal = {mid: json.dumps(by[mid]['gearCalendar']) for mid in list(OLD) + list(SSOT)}

    # 1. 旧構造の山
    for mid, ch in OLD.items():
        m = by[mid]
        cal = m['gearCalendar']
        assert m.get('dataModel') != 'ssot-v1', mid
        items = dict(ch)
        if mid in NALPS_OCT:
            items[10] = (sp(L, W, 11), sp(L, W, 21))
        for mo, (old, new) in items.items():
            if cal[mo - 1] == new:
                continue
            assert cal[mo - 1] == old, (mid, mo, cal[mo - 1])
            cal[mo - 1] = new
        sc = m['seasonCalendar']
        changed_sc = False
        for i, v in enumerate(cal):
            if gear_ok(sc[i], v):
                continue
            sc[i] = CLS[b(v)]
            changed_sc = True
        if changed_sc:
            m['calLegend'] = [LEGEND[c] for c in ('s-ok', 's-gear', 's-hard', 's-closed') if c in sc]
            m['seasonNoGear'] = circ([i + 1 for i in range(12) if sc[i] == 's-ok'])
            m['season6Crampons'] = circ([i + 1 for i in range(12) if sc[i] == 's-gear'])

    # 2. 新構造の山
    for mid, ch in SSOT.items():
        m = by[mid]
        assert m.get('dataModel') == 'ssot-v1', mid
        c = m['conditions']
        for mo, val in (ch.get('monthly') or {}).items():
            c['gearMonthly'][mo - 1] = val
        spl = c.get('gearSplits') or {}
        for mo, val in (ch.get('splits') or {}).items():
            if val is None:
                spl.pop(str(mo), None)
            else:
                spl[str(mo)] = {'before': val['before'], 'after': val['after'], 'changeDate': val['changeDate']}
        if mid in NALPS_OCT:
            assert spl['10']['before'] == L and spl['10']['after'] == W, mid
            spl['10']['changeDate'] = 21
        c['gearSplits'] = spl or None
        build_derived.derive(m, TH, AC)

    # 3. スノーシュー：浅間山の12月
    am = by['asama']
    am['snowshoeMonths'] = sorted(set((am.get('snowshoeMonths') or []) + [12]))
    srcs = [s for s in am.get('snowshoeSources') or [] if 'mt_info/past.php?id=1069' not in s['url']]
    am['snowshoeSources'] = srcs + ASAMA_SRC
    am['snowshoeCheckedAt'] = DAY
    dec = G['asama']['12']
    if not any(c['c'] == 'snowshoe' for c in dec):
        idx = max(i for i, c in enumerate(dec) if c['c'] in ('shoe', 'crampon', 'crampon_next', 'axe', 'helmet')) + 1
        dec.insert(idx, dict(TEIBAN_CARD))

    # 4. 装備カード
    changed = set()
    for mid in list(OLD) + list(SSOT):
        cal = by[mid]['gearCalendar']
        if json.dumps(cal) != before_cal[mid]:
            changed.add(mid)
        for mo in range(1, 13):
            if b(cal[mo - 1]) != 'closed' and set_cards(G, mid, mo, b(cal[mo - 1])):
                changed.add(mid)
        fix_next(G, mid, cal)
    for (mid, mo), text in CRAMPON_TEXT.items():
        cr = [c for c in G[mid][str(mo)] if c['c'] == 'crampon']
        assert len(cr) == 1 and 'G12' not in cr[0]['p'], (mid, mo)
        cr[0]['r'] = text
        changed.add(mid)
    changed.add('asama')

    # 5. よくある質問
    for mid, (old, new) in FAQ.items():
        m = by[mid]
        hit = 0
        for f in m['faq']:
            if 'シーズン' not in f['question']:
                continue
            if old in f['answer']:
                f['answer'] = f['answer'].replace(old, new)
                hit += 1
            elif new in f['answer']:
                hit += 1
        assert hit == 1, (mid, hit)
        changed.add(mid)
    for mid in TEMPLATE_IDS:
        m = by[mid]
        qs = [f for f in m['faq'] if 'シーズン' in f['question']]
        assert len(qs) == 1, mid
        new = template_answer(m)
        assert qs[0]['answer'] in (TEMPLATE_OLD, new), (mid, qs[0]['answer'])
        qs[0]['answer'] = new
        changed.add(mid)
    sm = by['shirouma']
    qs = [f for f in sm['faq'] if '初心者' in f['question']]
    assert len(qs) == 1
    new = shirouma_answer(sm)
    if SHIROUMA_OLD in qs[0]['answer']:
        qs[0]['answer'] = qs[0]['answer'].replace(SHIROUMA_OLD, new)
    assert new in qs[0]['answer'], qs[0]['answer']
    build_derived.derive(sm, TH, AC)

    for mid in changed:
        by[mid]['mountainUpdated'] = DAY
    json.dump(M, open(MP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    with open(GP, 'w', encoding='utf-8') as f:
        json.dump(G, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('直した山', len(changed), ' '.join(sorted(changed)))

    # 6. 月の途中で冬山装備に変わる月の「来月分」の見出し・文と、手で作った記事の写し（切替のある山）
    SPLIT.main()
    articles(sorted(changed))


def gear_ok(cls, v):
    from gear_calendar import FROM_CLS
    return FROM_CLS.get(cls) in cats(v)


def articles(mids):
    """手で作った記事・まとめにある装備カードの写し（data-gear-variants）と切替（data-gear-switch）を作り直す"""
    G = json.load(open(GP, encoding='utf-8'))
    MS = {m['id']: m for m in json.load(open(MP, encoding='utf-8'))}
    pages = glob.glob(os.path.join(ROOT, 'articles/*/index.html')) + glob.glob(os.path.join(ROOT, 'search/*/index.html'))
    for p in sorted(pages):
        s = open(p, encoding='utf-8').read()
        if '<!-- generated: scripts/gen_line_articles' in s:
            continue
        hit = []
        for mid in mids:
            if 'data-gear-mid="%s"' % mid not in s or mid not in G:
                continue
            sw = SPLIT.switch_of(MS[mid]['gearCalendar'])
            pat = re.compile(r'data-gear-mid="' + mid + r'"(?: data-gear-switch="[^"]*")?([^>]*?data-gear-variants=")[^"]*(")')
            attr = (' data-gear-switch="%s"' % sw) if sw else ''
            new, k = pat.subn(lambda x: 'data-gear-mid="%s"%s%s%s%s' % (mid, attr, x.group(1), SPLIT.variants_attr(G[mid]), x.group(2)), s)
            assert k >= 1, (p, mid)
            if sw:
                assert SPLIT.JS_SWITCH in new, p
            if new != s:
                hit.append(mid)
                s = new
        if hit:
            open(p, 'w', encoding='utf-8').write(s)
            print('記事の写し', os.path.relpath(p, ROOT), ' '.join(hit))


if __name__ == '__main__':
    main()
