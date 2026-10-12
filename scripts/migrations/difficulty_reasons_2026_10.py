#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""難易度の理由を、山ごとに調べた内容に書き直す（2026-10-12・第1回 13山）。

対象：Search Console で「◯◯ 難易度」の検索が多いのに、難易度の欄がひな形
（「◯◯は上級レベル（コース定数…）。代表コースの…。初心者には不向きで…」）だった山。
書くのは、その難易度になる具体的な理由（岩場・鎖・はしご・急登・行程の長さ・雪渓・規制・逃げ場）で、各出典に書かれていることだけ。
「＋」は登りやすくしている点、「−」（class="minus"）は難しくしている点。
出典は dlReasonsSources に残す。ひな形の文（dlNoteHtml）は dlNoteHtmlOld に退避する。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
V = '2026-10-12'

R = {
    'yari': (['槍沢ルートは上高地から梓川沿いにゆるやかな登りが続き、槍ヶ岳山荘までは技術より歩く時間の長さが負担になる',
              '山頂の穂先は登り専用・下り専用のルートに分かれている'],
             ['山頂直下の穂先（高さ約100m）は、急な岩場を鎖とはしごで登り下りする。高度感があり、落石にも注意が要る',
              '上高地からの往復は約14時間の長丁場で、山小屋に泊まるのが一般的',
              '標高3,000mを超えるので、高山病と天候の急変への備えが要る'],
             ['https://meizanmap.com/mountain/yarigatake/', 'https://www.japanesealps.net/north/yarigatake/yarisawa/']),
    'kitadake': (['白根御池小屋・肩の小屋・北岳山荘があり、1泊2日で無理のない計画を組める'],
                 ['広河原から山頂まで標高差は約1,600m。白根御池小屋から稜線へ上がる「草すべり」は急登で、砂利で滑りやすく下りの転倒に注意',
                  '山頂直下はガレ場と岩稜。八本歯のコルを通る道は、丸太のはしごが20本ほど続く',
                  '大樺沢（左俣）は雪渓が残り、例年7月末ごろまでアイゼンが要る',
                  '午後は雷雨になりやすく、早出・早着が基本'],
                 ['https://meizanmap.com/mountain/kitadake/', 'https://www.japanesealps.net/south/kitatake/happonba/', 'https://yamatabitabi.com/archives/140283']),
    'shibutsu': (['鳩待峠から小至仏山を経由する道は、山ノ鼻からの東面登山道より傾斜がゆるやかで、多くの人が使う'],
                 ['山頂付近の岩（蛇紋岩）は大変滑りやすく、濡れているときは特に注意が要る',
                  '山ノ鼻からの東面登山道は上り専用で、山頂から尾瀬ヶ原へは下れない',
                  '残雪期は植生保護のため登山道が閉鎖される期間がある（期間は年ごとに確認）',
                  '山頂付近にトイレがない'],
                 ['https://oze-fnd.or.jp/ozb/route/route2/r1/', 'https://oze-fnd.or.jp/wp4/wp-content/uploads/2023/04/shibutsu2.pdf']),
    'karamatsu': (['ゴンドラとリフトで八方池山荘（標高約1,830m）まで上がれ、八方池までは木道が整備されている',
                   '「信州 山のグレーディング」で、八方池山荘からの往復は技術的難易度B・体力度3。北アルプスの入門に向く'],
                  ['丸山ケルンから先にガレ場と短い鎖場（桟道）がある',
                   '雪の多い年は扇雪渓の通過にアイゼンが要ることがある',
                   '日帰りは帰りのリフト最終に間に合わせる必要があり、時間に余裕がない'],
                  ['https://www.yamareco.com/modules/yamainfo/grading_detail.php?id=40', 'https://yamahack.com/2307', 'https://www.japanesealps.net/north/karamatsudake/happouone/']),
    'ontakesan': (['田の原から歩き始められ、往復は日帰りできる'],
                  ['活火山。登山届の提出とヘルメットの着用が求められる（王滝村）',
                   '王滝口から剣ヶ峰まで通れるのは、規制が緩和されている期間だけ。奥の院方面とお鉢めぐりは入山規制が続いている（期間・範囲は年ごとに確認）',
                   '標高3,067mの高所で、高山病と天候の急変に注意が要る'],
                  ['https://www.vill.otaki.nagano.jp/bousai/funka_information.html']),
    'kisokoma': (['ロープウェイで千畳敷（標高約2,600m）まで上がれ、山頂までの往復は約4時間',
                  '乗越浄土から先はゆるやかな稜線歩きで、道はロープで区切られている'],
                 ['千畳敷から乗越浄土へ上がる八丁坂がいちばんの急登。岩や浮き石があり、落石にも注意',
                  '標高2,500mを超えるので息が上がりやすく、高山病に注意。乗越浄土は風が強いことが多く、防寒着が要る',
                  '冬は別の山。アイゼン・ピッケルが必要で、乗越浄土の下は雪崩にも注意が要る'],
                 ['https://yamahack.com/5817', 'https://www.japanesealps.net/center/kisokoma/']),
    'tonosaki': (['道ははっきりしていて、途中にベンチや山小屋があり休憩しやすい（秦野市観光協会）'],
                 ['大倉から山頂まで、標高差約1,200mをひたすら登る一本調子の尾根',
                  '天神平の先から花立山荘にかけて、木の階段が連続する急坂がある（秦野市観光協会）',
                  '下りも階段が続き、膝に負担がかかる',
                  '歩行距離は約14km。秦野市観光協会の目安は歩行約6時間'],
                 ['https://www.kankou-hadano.org/climbing/course05.html', 'https://yamahack.com/6622']),
    'kentoku': (['山頂直下の鳳岩の鎖場には迂回路がある'],
                ['山頂直下の鳳岩は、長さ約20mの急な一枚岩を鎖で登る。高度感がある',
                 '髭剃岩の周辺にも鎖場があり、山頂付近は露岩帯で岩が濡れると滑りやすい',
                 '登山口からの標高差が大きく、歩く時間も長い'],
                ['https://www.japanesealps.net/200moutains/kentokuzan/tokuwa_course/', 'https://yamap.com/mountains/14413']),
    'kinpusan': (['大弛峠からは片道約2時間30分で、危険な箇所が少ない'],
                 ['瑞牆山荘側から登ると距離10km超・標高差1,000m超で、砂払ノ頭から先は岩の多い稜線歩きになる',
                  '千代ノ吹上の付近は片側が切れ落ちている',
                  '雪が付くと滑りやすく、チェーンスパイクなどが要る'],
                 ['https://www.japanesealps.net/100moutains/kinpusan/ohdarumi/', 'https://yamahack.com/4813', 'https://yamatabitabi.com/archives/124238']),
    'akagi': (['黒檜山・駒ヶ岳の周回は3時間半ほど。駒ヶ岳側は木の階段が整備されている'],
              ['黒檜山への登りは直登が多く、岩がゴロゴロした急坂',
               '駒ヶ岳から大洞へ下る道は、鉄の階段がある急な道',
               '冬は積雪・凍結があり、アイゼンが要る（6本爪以上が安心）'],
              ['https://www.japanesealps.net/100moutains/akagiyama/kurobisan/', 'https://yamasugu.com/mt-akagi-difficulty/', 'https://www.japanesealps.net/100moutains/akagiyama/w_kurobisan/']),
    'makihata': (['井戸尾根コースはよく整備されていて、登山の基本を守っていれば特に危険な箇所はない（新潟県）'],
                 ['行程が長く、気力・体力が要る（新潟県）。標高差は約1,400m',
                  '樹林帯は粘土質で滑りやすく、下りでスリップしやすい',
                  'ヌクビ沢・割引沢の沢コースは落石と滑落の事故が多い上級者向けで、下山には使わない（新潟県）'],
                 ['https://www.pref.niigata.lg.jp/site/kenkei/osirase-anzen-ansin-mizuyamajsetugaijiko-sangaku-natuyama-jouhou-s9makihata-s9makihata.html', 'https://yamatabitabi.com/archives/146503']),
    'takao': (['1号路は舗装されていて、休憩所やトイレがそろう。ケーブルカー・リフトも使える',
               '6号路は沢沿いの道で、危険な箇所は少ない'],
              ['6号路と稲荷山コースは未舗装。木の根や岩が濡れると滑りやすく、山頂付近までトイレ・売店がない',
               '稲荷山コースは尾根道で、いちばん体力を使う'],
              ['https://takao-fumoto.com/takaosan-navi/takaosan-climbing-course/', 'https://www.japanesealps.net/200moutains/takaosan/6gou/', 'https://yamahack.com/2026']),
    'chogatake': (['三股ルートは鎖場やはしごがなく、北アルプスの入門に向く（「信州 山のグレーディング」で技術的難易度B・体力度4）'],
                  ['三股ルートは最短だが急登。スリップ・転倒に注意（蝶ヶ岳ヒュッテ）',
                   '長塀尾根はつづら折りの急登のあと、樹林帯の長い尾根歩きが続く',
                   '距離が長く標高差も1,000mを超えるので、日帰りは体力が要る',
                   '残雪期は雪崩・滑落の危険がある（蝶ヶ岳ヒュッテ）'],
                  ['https://chougatake.com/climb/', 'https://www.yamareco.com/modules/yamainfo/grading_detail.php?id=74']),
}

D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
assert set(R) <= set(N), set(R) - set(N)
for mid, (plus, minus, src) in R.items():
    m = N[mid]
    assert not m.get('dlReasonsHtml'), mid + ' は個別の理由が入っている'
    li = ''.join('\n    <li>%s</li>' % x for x in plus) + ''.join('\n    <li class="minus">%s</li>' % x for x in minus)
    m['dlReasonsHtml'] = '<ul class="dl-reasons">' + li + '\n  </ul>'
    m['dlReasonsSources'] = src
    m['dlReasonsCheckedAt'] = V
    if m.get('dlNoteHtml'):
        m['dlNoteHtmlOld'] = m['dlNoteHtml']
        m['dlNoteHtml'] = None
    m['mountainUpdated'] = V
    print(mid, m['name'], len(plus), len(minus))
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
