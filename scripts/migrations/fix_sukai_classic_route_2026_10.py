#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""皇海山：通れない群馬側（皇海橋）のルートが代表コースのままだった問題を直す（2026-10-10）。

確認した一次情報
  - 沼田市「交通規制のお知らせ【市道皇海線（根利栗原川林道）】」（令和8年9月1日更新）：落石のため当面の間通行止め
    https://www.city.numata.gunma.jp/life/kotsu/douro/1018292.html
  - 日光市観光協会「皇海山」：銀山平駐車場より7時間半、往復12時間半。庚申山荘は令和8年4月16日から避難小屋として利用再開（無料・予約不要・寝袋持参）
    https://www.nikko-kankou.org/spot/1108
距離・累積標高・標準コースタイムは公式の数字が無いため、YAMAPのモデルコース（24.4km・のぼり2,216m・14時間17分・定数56）を使う
    https://yamap.com/mountains/169
通洞駅からのタクシーの所要時間・料金は確認できなかったため、FAQから外す。
"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from calc_route_coeff import route_coeff
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'sukai'][0]
V = '2026-10-10'
NUMATA = 'https://www.city.numata.gunma.jp/life/kotsu/douro/1018292.html'
NIKKO = 'https://www.nikko-kankou.org/spot/1108'
YAMAP = 'https://yamap.com/mountains/169'

RNAME = '銀山平〜庚申山〜鋸山〜皇海山〜六林班峠（周回）'
r = {'name': RNAME, 'time': '14時間17分', 'distance': '24.4km', 'elevation': '+2216m',
     'waypoints': '銀山平 → 一の鳥居 → 庚申山荘 → 庚申山 → 鋸山 → 皇海山 → 鋸山 → 六林班峠 → 庚申山荘 → 銀山平',
     'sourceUrl': YAMAP, 'lastVerified': V}
r['coeff'] = route_coeff(r)
assert r['coeff'] == 57, r['coeff']
m['routes'] = [r]
C = r['coeff']
m['coeffMin'] = m['coeffMax'] = C
m['courseCoefficient'] = [C, C]
m['courseCoefficientRange'] = '%d〜%d' % (C, C)
m['difficulty'] = '上級'
m['daytrip'] = False
m['types'] = ['challenge', 'collector', 'adventure']
m['description'] = '栃木と群馬の境にある足尾山塊の主峰。群馬側の林道が通れず、今は足尾の銀山平から庚申山・鋸山を越える長い道のりで登る。'
m['recommendReason'] = '庚申山・鋸山を越える修験の道をたどって登る、足尾山塊の奥深い百名山'
m['parking'] = '銀山平駐車場（約50台・無料）※群馬側の林道は通行止め。クラシックルートの起点'

VP = [
    ('長い行程を歩き通す体力に自信がある人', '標準で14時間を超える周回。途中の庚申山荘（避難小屋）に泊まる計画も立てられる'),
    ('鎖場やはしごの岩稜に慣れている人', '庚申山から鋸山へ、鎖とはしごの続く峰をいくつも越える'),
    ('静かな深い山が好きな人', '山頂は木に囲まれ、樹林の中を黙々と歩く時間が長い'),
]
items = re.findall(r'<div class="rec-item">.*?</div>', m['vibesHtml'], flags=re.S)
assert len(items) == 3
html_ = m['vibesHtml']
for old, (who, why) in zip(items, VP):
    new, c = re.subn(r'<span><strong>.*?</strong>——.*?</span>', lambda _: '<span><strong>%s</strong>——%s</span>' % (who, why), old, flags=re.S)
    assert c == 1
    assert html_.count(old) == 1
    html_ = html_.replace(old, new)
m['vibesHtml'] = html_
m['vibePoints'] = [{'who': a, 'why': b} for a, b in VP]

RNG = m['courseCoefficientRange']
faq = m['faq']
assert len(faq) == 4
faq[0]['answer'] = ('皇海山の難易度は上級、コース定数%sです。初心者には向きません。群馬側の皇海橋からの短いコースは、林道（市道皇海線）の通行止めで使えません。'
                    '現在は栃木県日光市足尾の銀山平から、庚申山・鋸山を越えて登ります。鎖場やはしごが続き、道のわかりにくい場所もあるため、十分な経験が必要です。' % RNG)
faq[1]['question'] = '皇海山の所要時間は？日帰りできますか？'
faq[1]['answer'] = ('日光市観光協会の案内では、銀山平駐車場から山頂まで7時間半、往復で12時間半です。銀山平から庚申山・鋸山・皇海山・六林班峠をまわる周回は24.4km、標準で14時間17分かかります（コース定数%s）。'
                    '日帰りには早朝の出発と十分な体力が必要です。途中の庚申山荘（無料の避難小屋・予約不要・寝袋持参）に泊まる計画も検討してください。' % RNG)
h, mi = divmod(m['driveTimeShinjuku'], 60)
faq[2]['answer'] = ('登山口の銀山平までは公共交通機関の直通ルートがなく、マイカーでのアクセスが基本です。新宿からは車で約%d時間%d分が目安です。銀山平駐車場に車を置いて歩き始めます。'
                    '群馬県沼田市側の皇海橋へ向かう林道（市道皇海線・根利栗原川林道）は、落石のため通行止めです。' % (h, mi))

m['metaTitle'] = '皇海山 登山｜上級・定数%s【百名山】| Yamatch' % RNG
m['ogTitle'] = '皇海山 登山｜標高2,144m・コース定数%s・足尾山塊の秘境【百名山】| Yamatch' % RNG
md = '皇海山（すかいさん・2,144m）は栃木・群馬の境にある百名山。コース定数%s、上級。足尾の銀山平から庚申山・鋸山を越える長いクラシックルートで登る。' % RNG
m['metaDescription'] = md
m['ogDescription'] = md
m['dlNoteHtml'] = ('<p class="dl-note">皇海山は上級レベル（コース定数%s）。代表コースの%sは14時間17分・24.4km・標高差+2216m。初心者には向かず、十分な経験と体力が必要です。</p>' % (RNG, RNAME))
intro = ('%s上級レベルでコース定数%s。標準で14時間を超えるため、早朝に出発するか、庚申山荘（避難小屋）に泊まる計画で登る。代表コース（%s）は所要14時間17分/24.4km/標高差+2216m。' % (m['description'], RNG, RNAME))
m['introHtml'], c = re.subn(r'(<p class="intro-text">).*?(</p>)', lambda mm: mm.group(1) + intro + mm.group(2), m['introHtml'], flags=re.S)
assert c == 1
rl = m['relatedLinksHtml']
for a, b in (('/search/shinjuku-daytrip/', '/search/shinjuku/'), ('/search/ofuna-daytrip/', '/search/ofuna/'),
             ('新宿から日帰りで行ける山一覧', '新宿から行ける山一覧'), ('大船・横浜から日帰りで行ける山一覧', '大船・横浜から行ける山一覧')):
    assert rl.count(a) == 1, a
    rl = rl.replace(a, b)
m['relatedLinksHtml'] = rl

m['annualItems'] = [
    {'kind': 'closure', 'label': '市道皇海線（根利栗原川林道）の通行止め（皇海橋登山口へ行けない）', 'validFrom': None, 'validTo': None,
     'seasonYear': None, 'sourceUrl': NUMATA, 'lastVerified': V, 'note': '落石のため当面の間通行止め（令和8年9月1日更新のお知らせ）'},
    {'kind': 'info', 'label': '庚申山荘（避難小屋）の利用・銀山平からの所要時間', 'validFrom': None, 'validTo': None,
     'seasonYear': None, 'sourceUrl': NIKKO, 'lastVerified': V},
]
m['featureSources'] = ['https://yamahack.com/1915', NIKKO]
m['mountainUpdated'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('皇海山を更新: 定数', RNG)
