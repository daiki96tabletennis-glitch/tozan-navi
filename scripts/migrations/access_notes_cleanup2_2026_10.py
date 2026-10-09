#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""電車・バス欄の注記の整理（続き）：2か所を1つにまとめたことで重なった項目を削る（2026-10-09）。
同じ内容を言い換えているだけの項目・アクセスと関係のない項目を、1つずつ指定して削除する。詳しいほうを残す。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section, format_note_items
P = os.path.join(ROOT, 'data', 'mountains.json')
AP = os.path.join(ROOT, 'data', 'accesses.json')
D = json.load(open(P, encoding='utf-8'))
AC = json.load(open(AP, encoding='utf-8'))
N = {m['id']: m for m in D}
DROP = {
    'okutama': ['運行は土日祝が基本で、時期により平日も運行', 'なお駅前のセブンイレブンは2024年1月に閉店しているため、食料は事前に用意を'],
    'koganzan': ['運行は土日祝が基本で、時期により平日も運行', 'なお駅前のセブンイレブンは2024年1月に閉店しているため、食料は事前に用意を'],
    'shirouma': ['猿倉線は7月中旬〜10月中旬の事前予約制（発車オーライネット）', '運賃片道2,000円'],
    'makihata': ['運賃は距離別で、六日町駅〜清水（約15km）は500円', '土日祝や早朝はMOSSが無く、タクシー代が別にかかる',
                 '桜坂駐車場から巻機山山頂（御機屋経由）までは約4時間30分で、井戸尾根は標高差1,200m超の登りが続くため早発が必須'],
    'yarigatake2': ['乗合タクシーの予約を忘れずに'],
    'arikayama': ['定期バスは4月下旬〜11月上旬の季節運行'],
    'otenshoudake': ['定期バスは4月下旬〜11月上旬の季節運行'],
    'adatara': ['二本松駅前～奥岳のバスは運行日・本数が限られる（平日中心）', '事前に時刻表で要確認'],
    'terkari': ['料金は1台15,000〜20,000円（メーター制または時間制）'],
    'kisokoma': ['運賃は日によって変わる'],
    'yaguradake': ['出かける前に箱根登山バスの時刻表で確認を'],
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
