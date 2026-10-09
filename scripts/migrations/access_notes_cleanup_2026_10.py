#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""電車・バス欄の注記の整理（2026-10-09）。
- 表示：運賃欄の下の注記（summaryNote）と補足（note）の2か所を、1つの箇条書きにまとめる（render_transit_routes.py）
- 内容：アクセスと関係のない項目（コースの説明・所要時間・難易度・山小屋・見どころ・下山後の温泉など）を削除する。
  アクセス・予約・運行期間・運賃・前泊の要否・規制に関わる項目は残す。削除する項目は下の一覧で1つずつ指定する（機械的な一括削除はしない）
全山の trainAccessHtml を作り直す。新構造の山は accesses.json を直し、build_derived.py で反映する。
"""
import json, os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section, format_note_items
P = os.path.join(ROOT, 'data', 'mountains.json')
AP = os.path.join(ROOT, 'data', 'accesses.json')
D = json.load(open(P, encoding='utf-8'))
AC = json.load(open(AP, encoding='utf-8'))
N = {m['id']: m for m in D}
DROP = {
    'tanzawa': ['大倉から大倉尾根を登り、塔ノ岳を経て丹沢山へ', '往復18kmの長い行程なので、日帰りは健脚向け', '山小屋泊も検討を'],
    'kumotori': ['鴨沢から雲取山山頂までは約5時間30分で、日帰りは健脚者向け', '雲取山荘・七ツ石小屋などでの1泊が一般的'],
    'amagi': ['万二郎岳・万三郎岳の周回は約3時間30分、アマギシャクナゲの開花期（5月下旬〜6月上旬）が人気'],
    'ryokami': ['鋸状の岩峰でクサリ場が多い'],
    'mizugaki': ['みずがき山荘から瑞牆山山頂までは約2時間30分で日帰り可能', '金峰山との縦走も人気'],
    'kinpusan': ['金峰山まで往復4時間程度で日帰り可能'],
    'asama': ['浅間山は活火山で噴火警戒レベルにより入山範囲が変わる',
              '前掛山は2026年5月にレベル1へ引き下げられ約3年ぶりに登山道が解放されたが、出発前に気象庁の火山情報を必ず確認すること'],
    'norikura': ['畳平は標高2,702mで夏でも冷えるため防寒具必須', '畳平から剣ヶ峰までは約1時間30分で、3,000m峰の中では最も手軽に登れる山として人気'],
    'tateyama': ['室堂は標高2,450mで夏でも冷えるため防寒具必須'],
    'myoko': ['燕温泉には無料の露天風呂「黄金の湯」があり、下山後に立ち寄れる', '火打山とあわせて登る場合は笹ヶ峰が起点になる'],
    'hirugata': ['蛭ヶ岳は丹沢最高峰で大倉からの日帰りは健脚者向け（往復10時間超）'],
    'kintoki': ['金時山は箱根エリアで最も人気の山のひとつで登山道が整備されており初心者にも登りやすい'],
    'kayagatake': ['深田久弥終焉の地として知られる山'],
    'kenashiyama': ['急登が続くコースのため、体力に応じて無理のない計画を'],
    'yarigatake2': ['南アルプス深南部の難関ルート', '標準コースタイム16時間半の健脚向けルートで、前泊・テント泊が基本'],
    'hiuchi': ['笹ヶ峰から火打山山頂までは約4時間30分', '高谷池ヒュッテでの1泊もおすすめ'],
    'utsugi': ['日帰りは健脚者向けで、駒峰ヒュッテや空木平避難小屋での1泊が一般的'],
    'hiwadayama': ['日和田山は岩場のクライミング練習地としても知られ、男坂は岩場歩きの入門に適している', '標高305mと低く登山時間も短いため、初心者や家族連れにも人気'],
    'sannotou': ['大倉から三ノ塔は丹沢入門として人気', '表尾根縦走の起点にもなります'],
    'koubousan': ['下山後に鶴巻温泉（陣屋など）でひと風呂どうぞ', '下山は秦野駅へ縦走がおすすめ'],
    'kagenobusan': ['高尾山・陣馬山との縦走起点としても人気'],
    'kusatoriyama': ['登山口まで整備された道が続きます'],
    'iyogatake': ['伊予ヶ岳は標高336mながら山頂直下に鎖場があり、「房総のマッターホルン」と呼ばれる岩峰', '富山（とみさん）とセットで登られることが多い'],
    'takanosuyama': ['稲村岩尾根は奥多摩三大急登のひとつとされ体力が必要'],
    'taiheizan': ['太平山神社まで階段が続くため歩きやすい靴を推奨'],
    'juunigadake': ['毛無山から十二ヶ岳への縦走路にはロープ・鎖場・岩尾根に架かる吊り橋があり、標高1,683mの低山ながら岩場歩きの経験が必要な中級者向けルート',
                    '西湖畔の周回コースとして人気で、富士山の展望が優れている'],
    'kogashiyama': ['古賀志山は標高583mながら岩場・鎖場が多く、複数のバリエーションルートがある', '初心者は北コース・南コースなど整備された道を選ぶこと'],
}


def clean(text, drops, prefix, found):
    if not text:
        return text
    items = format_note_items(text)
    keep = [i for i in items if i not in drops]
    for i in items:
        if i in drops:
            found.add(i)
    if len(keep) == len(items):
        return text
    return (prefix + '。'.join(keep)) if keep else None


removed = 0
for mid, drops in DROP.items():
    m = N[mid]
    found = set()
    if m.get('dataModel') == 'ssot-v1':
        targets = [AC[r['accessId']]['trainRoutes'] for r in m['routes'] if r.get('accessId') in AC and AC[r['accessId']].get('trainRoutes')]
    else:
        targets = [m['trainRoutes']]
    for tr in targets:
        tr['note'] = clean(tr.get('note'), drops, '💡 ', found)
        tr['summaryNote'] = clean(tr.get('summaryNote'), drops, '※', found)
    assert found == set(drops), (mid, set(drops) - found)
    removed += len(drops)

# 全山の表示を作り直す（旧構造）。新構造は build_derived.py が作る
n = 0
for m in D:
    if m.get('dataModel') == 'ssot-v1' or not (m.get('trainRoutes') or {}).get('routes'):
        continue
    html = render_ts_section(m['trainRoutes'], m)
    if html != m.get('trainAccessHtml'):
        m['trainAccessHtml'] = html
        n += 1
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(AC, open(AP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('削除した項目:', removed, '／表示を作り直した山（旧構造）:', n)
