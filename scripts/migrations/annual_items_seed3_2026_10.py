#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""annualItems 登録・第3回と、南越後観光バスの社名変更の反映（2026-10-06）。
出典：JRバス関東（ジオライナー 2026/7/17〜10/12）、諏訪観光協会・霧ヶ峰自然保護センター（霧ヶ峰線 2026/5/2〜10/25）、
      伊那バス公式の告知（鳥倉線 2026/7/18〜8/30）、十日町市の資料と事業者サイト（2026/4/1 南越後交通バスへ社名変更）
"""
import json, os, re, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-06'
def setitem(mid, label_key, label, url, vf, vt, note):
    its = N[mid]['annualItems']
    hit = [i for i in its if label_key in i['label']]
    assert len(hit) == 1, (mid, label_key)
    hit[0].update({'label': label, 'sourceUrl': url, 'validFrom': vf, 'validTo': vt, 'seasonYear': int(vt[:4]), 'note': note, 'lastVerified': V})

setitem('nokogiriyama', 'ジオライナー', '茅野駅〜戸台パークの南アルプスジオライナー',
        'https://www.jrbuskanto.co.jp/jwp/topics/topics02/20260501_geoliner.html', '2026-07-17', '2026-10-12',
        '金土日祝。7月31日〜8月16日と9月18日〜27日は毎日')
setitem('kirigamine', '霧ヶ峰', '上諏訪駅〜霧ヶ峰の路線バス（霧ヶ峰線）',
        'https://www.kirigamine-vc.jp/information/6585', '2026-05-02', '2026-10-25', '土日祝。8月1日〜30日は毎日')
setitem('shiomidake', '鳥倉', '伊那大島駅〜鳥倉登山口の登山バス（鳥倉線）',
        'https://www.ibgr.jp/general-route/torikura_off2/', '2026-07-18', '2026-08-30', '期間中は毎日・1日2往復')

def swap(m, key, old, new):
    assert old in m['trainRoutes'][key], (m['id'], old)
    m['trainRoutes'][key] = m['trainRoutes'][key].replace(old, new)
swap(N['nokogiriyama'], 'note', '季節運行（例年7月中旬〜10月中旬の金土日祝、繁忙期は毎日）', '季節運行（2026年は7月17日〜10月12日の金土日祝。7月31日〜8月16日と9月18日〜27日は毎日）')
swap(N['shiomidake'], 'note', '鳥倉線は例年7月中旬〜8月下旬のみ運行、往復2便/日と少なく事前計画が必須', '鳥倉線は夏だけの運行（2026年は7月18日〜8月30日）。1日2往復と少ないので事前の計画が必須')

# 社名変更：南越後観光バス → 南越後交通バス（2026年4月1日）
def rename(o):
    if isinstance(o, str): return o.replace('南越後観光バス', '南越後交通バス')
    if isinstance(o, list): return [rename(x) for x in o]
    if isinstance(o, dict): return {k: rename(v) for k, v in o.items()}
    return o
ids = ['nokogiriyama', 'kirigamine', 'shiomidake']
for i, m in enumerate(D):
    if '南越後観光' in json.dumps(m, ensure_ascii=False):
        D[i] = rename(m); ids.append(m['id'])
N = {m['id']: m for m in D}
for mid in ids:
    m = N[mid]
    if m.get('trainRoutes'):
        m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V
assert '南越後観光' not in json.dumps(D, ensure_ascii=False)
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
# 検索ページの表記
for f in ['search/jr-joetsu-hiking/index.html', 'search/echigoyuzawa-hiking/index.html']:
    p = os.path.join(ROOT, f); s = open(p, encoding='utf-8').read()
    s2, c = re.subn('南越後観光バス', '南越後交通バス', s); assert c >= 1
    open(p, 'w', encoding='utf-8').write(s2)
    print(f, c, s2.rstrip().endswith('</html>'), len(re.findall(r'<div\b', s2)) == len(re.findall(r'</div>', s2)))
print(' '.join(sorted(set(ids))))
