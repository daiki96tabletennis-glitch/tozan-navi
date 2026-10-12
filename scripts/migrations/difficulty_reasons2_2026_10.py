#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""難易度の理由を、山ごとに調べた内容に書き直す（2026-10-12・第2回 12山）。書き方は difficulty_reasons_2026_10.py と同じ。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
V = '2026-10-12'
R = {
    'yakedake': (['新中の湯ルートは道が整備されていて、鎖場やはしごがない'],
                 ['活火山。山頂付近に噴気があり、浮き石と落石が多い。登る前に火山の状況を確認する',
                  '上高地側（焼岳小屋〜上高地）は長いはしごと鎖場があり、雨の日は大変滑りやすい',
                  '新中の湯ルートは水場・売店・トイレがない。ぬかるみが多く、山頂直下は岩礫帯で道が狭い',
                  '山頂の南峰は岩が崩れやすく登れない（登るのは北峰）'],
                 ['https://www.japanesealps.net/north/yakedake/sinnakanoyu/', 'https://www.japanesealps.net/north/yakedake/kamikouchi/', 'https://yamatabitabi.com/archives/114509']),
    'kasagatake': (['山頂直下に笠ヶ岳山荘がある'],
                   ['笠新道は北アルプスでも指折りの急登。登山口から杓子平まで、標高差1,000m以上を登り続ける',
                    '笠新道の登山口から笠ヶ岳山荘まで、水場も山小屋もない。途中で引き返す以外の逃げ道がない',
                    '新穂高からの標高差は約1,800m。往復13時間前後かかり、山小屋泊が現実的',
                    '下りも急坂が長く続き、体力と集中力が要る'],
                   ['https://yamahack.com/4748', 'https://tozan100kei.com/route/kasagatake-kasashindo.php', 'https://souraku.jp/home/newpage182.html']),
    'bandai': (['八方台コースは山頂までの高低差が少なく、時間的に最短で登れる（磐梯山ビジターセンター）。標準は登り2時間10分・下り1時間30分'],
               ['弘法清水から山頂までは、狭い急坂が30分ほど続く。濡れた岩や木の根で滑りやすい',
                '弘法清水から上は複数のコースが合流し、道が狭いのでシーズン中は渋滞しやすい',
                '山頂にトイレがない。八方台登山口へは路線バスがない',
                '翁島コースはガレ場の急登で、体力のある人向け'],
               ['https://www.bandaisan.or.jp/fun/happoudaitozanguchi/', 'https://urabandai-vc.jp/trekking/20happoudai/', 'https://yamahack.com/2601']),
    'kintoki': (['技術的に難しい所はなく、公時神社からの道は山頂へまっすぐ登るので迷いにくい'],
                ['標高差が約600mあり、急登が続くのでやや体力が要る',
                 '公時神社コースは金時宿り石の先から山頂まで急な登り。山頂手前に岩場がある',
                 '乙女峠側は赤土の急斜面やロープのある区間があり、濡れると滑りやすい',
                 '水場がない（トイレは山頂にある）'],
                ['https://www.japanesealps.net/200moutains/kintokiyama/jinja/', 'https://yamatabitabi.com/archives/136831/', 'https://www.hakonenavi.jp/feature/14394']),
    'fuji': (['開山期間中は山小屋と救護所があり、登山道が整備されている'],
             ['山頂の酸素は平地の約3分の2。高山病になる人が多く、山小屋に1泊して体を慣らすのが基本',
              '富士宮ルートは最短だが急登が続く。六合目から上は急な岩場で、七合目から山頂は岩の多い道。落石に注意（富士登山オフィシャルサイト）',
              '富士宮ルートは同じ道を下る。岩が多く滑りやすい下りが新七合目付近まで続き、膝に負担がかかる',
              '吉田ルートは下山時に須走ルートとの分岐で道を間違えやすい',
              '登れるのは開山期間だけ。閉山後は山小屋・トイレが閉まり、救護体制もない'],
             ['https://www.fujisan-climb.jp/comparison-of-routes/', 'https://www.fuji-net.co.jp/report/cat-camp-climbing-outdoor/6022/']),
    'adatara': (['ゴンドラ（ロープウェイ）で薬師岳まで上がれ、山頂駅から山頂まで約1時間30分。登山道はよく整備されている'],
                ['山頂と稜線は風をさえぎるものがなく、強風であおられて転ぶ危険がある。休憩時は防寒着が要る',
                 '霧が出ると視界が急に悪くなる。牛ノ背は濃霧のとき道を外しやすい',
                 '沼ノ平は火山ガスの危険があり立入禁止（1997年に死亡事故）。規制の表示とロープを守る',
                 '山頂直下に短い岩場（鎖）がある'],
                ['https://www.japanesealps.net/100moutains/adatarayama/gondora/', 'https://www.bousai.go.jp/kohou/kouhoubousai/h24/67/volcano.html', 'https://www.tif.ne.jp/kuroganegoya/climbing.html']),
    'nikko_shirane': (['ロープウェイで標高約2,000mまで上がれ、序盤はなだらかな樹林の道'],
                      ['大日如来を過ぎると急な登りになり、標高2,450mあたりで森林限界を越える',
                       '山頂直下は砂利と岩の斜面（ザレ場・ガレ場）の急登。足元が不安定で、下りは膝に負担がかかる',
                       '山頂部は岩が多く起伏があり、最高点へは一度下って登り返す',
                       '標高2,500m級で風が強く、防寒着が要る'],
                      ['https://www.japanesealps.net/100moutains/nikkoushiranesan/marunuma/', 'https://yamahack.com/1916']),
    'hakusan': (['砂防新道は最短で登れ、休憩所や水場がある整備の行き届いた道（石川県）',
                 '室堂と南竜に山小屋があり、1泊2日にできる（宿泊は予約制）'],
                ['別当出合から山頂まで標高差は約1,450m。日帰りは往復8時間ほどかかり、体力が要る',
                 'ジグザグの急な上り坂が続く区間がある（石川県）',
                 '観光新道は急勾配で滑りやすく、水場がない（石川県）。下りで使う人が多いが、疲れていると転びやすい',
                 '残雪のある時期は軽アイゼンが要る'],
                ['https://www.pref.ishikawa.jp/sizen/hakusan/climb/sabo-shindo/', 'https://www.pref.ishikawa.lg.jp/hakusan/tozaninf/attention.html']),
    'nasu': (['ロープウェイを使えば、山頂駅から茶臼岳の山頂まで約50分'],
             ['風が特に強い山。春と秋は立っていられないほど吹くことがあり、強風の日はロープウェイも止まる',
              '砂れき・ザレ場・ガレ場の歩きにくい道。登山靴が要る',
              '活火山で、火山ガスに注意が要る。森林限界より上で、天気の影響を受けやすい',
              '峰の茶屋から朝日岳へは、道幅の狭い所や急な岩場がある',
              '水場がない'],
             ['https://www.yama-nikki.jp/posts/nasudake-guide/', 'https://www.jac.or.jp/oyako/f15/d202020.html', 'https://yamap.com/model-courses/23915']),
    'naeba': (['祓川コースは鎖場がなく、木道の区間は歩きやすい',
               '水場が和田小屋と雷清水の2か所にある'],
              ['祓川コースは岩と泥の道が長く、ぬかるみが多い。スパッツがあるとよい',
               '九合目からの最後の登りが急で、手を使う所もある',
               '小赤沢コースは五合目から上に鎖場が6〜7か所あり、八合目付近がいちばん急',
               '山頂に水場がない。祓川登山口へ直行するバスがない'],
              ['https://www.japanesealps.net/100moutains/naebasan/haraigawa/', 'https://yamahack.com/1885', 'https://niigataclimb.com/naeba_koakasawa/']),
    'okutama': (['上日川峠から大菩薩峠を回る周回は難所がほとんどなく、3〜4時間で歩ける',
                 '福ちゃん荘・介山荘などの山小屋がコース上にある'],
                ['唐松尾根は急な登りと岩場があり、雨の日や下りは滑りやすい。雷岩の手前が急登',
                 '裂石から登ると標高差が大きく、体力が要る。丸川峠経由は健脚向け',
                 '冬は登山道が凍結し、6本爪以上のアイゼンが要る。上日川峠への道路は冬季閉鎖がある'],
                ['https://yamahack.com/5723', 'https://www.japanesealps.net/100moutains/daibosatu/', 'https://www.yama-nikki.jp/posts/daibosatsune/']),
    'jonengatake': (['一ノ沢ルートは沢沿いのゆるやかな道が長く、常念乗越に常念小屋がある'],
                    ['登山口から山頂まで標高差が約1,500mあり、日帰りは往復10時間を超える',
                     '胸突八丁は急登で、谷側が切れ落ちていて足場の狭い所がある。滑落に注意',
                     '時期によって胸突八丁の手前に雪渓が残り、アイゼンが要る。雨のあとは沢が増水する',
                     '常念小屋から山頂までは岩とガレ場の急な登り'],
                    ['https://www.japanesealps.net/north/jonendake/ichinosawa/', 'https://www.kojitusanso.jp/tozan-report/detail/?fm=29823', 'https://yamahack.com/1697']),
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
