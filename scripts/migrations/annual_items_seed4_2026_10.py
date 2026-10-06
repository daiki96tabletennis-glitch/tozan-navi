#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""annualItems 登録・第4回：御嶽山・蓼科山・草津白根山（2026-10-06）。
出典：王滝村公式「田の原線バス」（令和8年7月4日〜10月18日、土日祝と8/3〜7・8/10、木曽福島駅8:40→田の原9:55、片道1,500円）、
      茅野市・アルピコ交通（蓼科高原ラウンドバス 2026年5月2日〜10月25日）、JRバス関東 草津・白根エリア運行情報（草津温泉〜白根火山は全便運休）
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-06'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
def item(kind, label, url, vf=None, vt=None, note=None):
    d = {'kind': kind, 'label': label, 'validFrom': vf, 'validTo': vt, 'seasonYear': int(vt[:4]) if vt else None, 'sourceUrl': url, 'lastVerified': V}
    if note: d['note'] = note
    return d
def resync(m, times=False):
    R = m['trainRoutes']['routes']
    if times:
        for dep, K in DEPS:
            m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V

# 御嶽山：バスは約75分（100分と載せていた）。2026年の運行日を登録
m = N['ontakesan']
old = {K: m['trainTime' + K] for _, K in DEPS}
for dep, _ in DEPS:
    hit = [l for l in m['trainRoutes']['routes'][dep]['legs'] if l['station'] == '木曽福島駅']
    assert len(hit) == 1 and hit[0]['durationMin'] == 100, dep
    hit[0]['durationMin'] = 75
a = '木曽福島駅から田の原（王滝口）へはおんたけ交通バスで約100分。季節運行（例年7月〜10月）で本数が非常に少なく、運行期間外はタクシー利用となる'
assert a in m['trainRoutes']['note']
m['trainRoutes']['note'] = m['trainRoutes']['note'].replace(a,
    '木曽福島駅から田の原（王滝口）へは田の原線のバスで約75分。2026年は7月4日〜10月18日の土日祝だけの運行（8月3日〜7日と10日は平日も運行）で、1日2便。運行のない日はタクシーを使う')
m['annualItems'] = [
    item('transport', '木曽福島駅〜田の原のバス（田の原線）', 'https://www.vill.otaki.nagano.jp/kurashi/basu_tanohara.html', '2026-07-04', '2026-10-18', '土日祝のみ。8月3日〜7日と10日は平日も運行'),
    item('trail', '山頂まで登れる期間（立入規制の緩和）', m['status']['sourceUrl'], '2026-07-01', '2026-10-14', '期間外は入山できない'),
]
resync(m, times=True)
for q in m['faq']:
    for _, K in DEPS:
        pass
print('ontake', old, {K: m['trainTime' + K] for _, K in DEPS})

# 蓼科山
m = N['keirisan']
m['trainRoutes']['summaryNote'] = '※蓼科高原ラウンドバスの2026年の運行は5月2日〜10月25日。蓼科山登山口を通る便は土日祝と7月下旬〜8月下旬の毎日だけで、1日1往復。必ず最新の時刻表を確認する'
m['annualItems'] = [item('transport', '茅野駅〜蓼科山登山口方面のバス（蓼科高原ラウンドバス）', 'https://www.alpico.co.jp/traffic/local/suwa/kitayatsugatake/', '2026-05-02', '2026-10-25', '蓼科山登山口経由は土日祝と夏の毎日・1日1往復')]
resync(m)

# 草津白根山
m = N['shirane_gunma']
m['trainRoutes']['note'] = m['trainRoutes']['note'].rstrip('。') + '。草津温泉〜白根火山のバスは、道路の状況により当面の間、全便運休している'
m['annualItems'] = [item('closure', '草津温泉〜白根火山のバス（全便運休中）', 'https://www.jrbuskanto.co.jp/jwp/local_emergency/e_kusatsu'),
                    item('closure', '草津白根山の立入規制', m['status']['sourceUrl'])]
m['annualNotApplicable'] = True
resync(m)
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for q in N['ontakesan']['faq']:
    if 'アクセス' in q['question']: print(q['answer'])
