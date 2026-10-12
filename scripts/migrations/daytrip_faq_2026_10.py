#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「日帰り」の検索が多い24山（data/seo_intents.json）に、日帰りできるかどうかの答えを入れる（2026-10-12）。

1. よくある質問の「◯◯の所要時間は？日帰りできますか？」（全山共通のひな形だった）を、
   「◯◯は日帰りできますか？所要時間の目安」に替え、その山のコースの時間で答える。
2. サイトで「日帰り不可（山小屋泊がおすすめ）」としている7山は、日帰りで歩く人がいるコースがあるかを調べ、
   - あればそのコースに注記（note）と印（status: caution）を付ける。蛭ヶ岳は最短の青根コースを追加する
   - よくある質問では「健脚なら可能・標準は◯時間・一般には山小屋泊」と、調べた範囲で答える
   山全体の daytrip（日帰り可の区分）は変えない（一覧・絞り込みに使う区分で、一般の登山者の目安のため）。
出典は各山の daytripSources に残す。
"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
V = '2026-10-12'
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
I = json.load(open(os.path.join(ROOT, 'data', 'seo_intents.json'), encoding='utf-8'))['mountains']
TARGET = [k for k, v in I.items() if v['intents'].get('日帰り') and k in N]


def minutes(t):
    m = re.match(r'(?:(\d+)時間)?(?:(\d+)分)?', t or '')
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0) if m and (m.group(1) or m.group(2)) else None


# ── 日帰り不可としている7山：調べた内容 ──
HARD = {
    'myoko': {
        'route': '燕温泉', 'label': '健脚なら日帰り可',
        'note': '燕温泉からの往復は、登山ガイドのコースタイムで8〜9時間前後（登り4時間30分〜5時間20分・下り3時間20分〜3時間30分）。早朝に出発すれば日帰りで歩く人が多いコースです。山頂の手前に鎖場があります。',
        'faq': '妙高山は、健脚なら日帰りできます。燕温泉からの往復はコースタイムで8〜9時間前後（標高差は約1,300m）で、早朝の出発が前提です。妙高高原スカイケーブルを使う赤倉からのコースは往復約7時間です。歩く時間が長いので、ゆとりを持つなら高谷池ヒュッテや黒沢池ヒュッテに泊まる計画にしてください。',
        'src': ['https://www.japanesealps.net/100moutains/myokosan/', 'https://yamachizu.jp/course/616']},
    'houou': {
        'route': '青木鉱泉', 'label': '健脚なら日帰り可',
        'note': '青木鉱泉からドンドコ沢を登り、中道を下る周回は、標準コースタイムが約12時間（約15km・累積標高差約2,100m）。健脚者が早朝に出発して日帰りで歩く例があります。ドンドコ沢は道の分かりにくい所があります。',
        'faq': '鳳凰山（鳳凰三山）は、健脚者なら日帰りで歩けます。青木鉱泉からドンドコ沢を登り中道を下る周回が日帰りの定番ですが、標準コースタイムは約12時間（約15km・累積標高差約2,100m）で、夜明け前後の出発が前提です。夜叉神峠からの往復は距離が長く、日帰りには向きません。一般には鳳凰小屋や南御室小屋などに泊まる1泊2日です。',
        'src': ['https://www.yamakei-online.com/cl_record/detail.php?id=129058', 'https://yamasugu.com/houousanzan-route/']},
    'hotaka': {
        'route': '新穂高', 'label': '日帰りは健脚者のみ',
        'note': '新穂高から白出沢を往復する日帰りの記録はありますが、標準コースタイムは約15時間（約22km・累積標高差約2,300m）。夜明け前に出発する健脚者向けです。白出沢は通行止めになることがあるので、事前に確認してください。',
        'faq': '奥穂高岳の日帰りは、一般の登山者にはおすすめできません。新穂高から白出沢を往復する日帰りの記録はありますが、標準コースタイムは約15時間（約22km・累積標高差約2,300m）で、健脚者が夜明け前に出発して12〜13時間かけています。上高地から涸沢を経由する代表コースは往復14時間で、涸沢や穂高岳山荘に泊まる1泊2日〜2泊3日が一般的です。',
        'src': ['https://www.yamakei-online.com/cl_record/detail.php?id=142918', 'https://www.yamareco.com/modules/yamareco/detail-8421302.html']},
    'terkari': {
        'route': '易老渡', 'label': '日帰りは健脚者のみ',
        'note': '芝沢ゲートからの往復は、標準コースタイムが約16時間（約26km・累積標高差約2,700m）。健脚者が未明に出発して12〜13時間で日帰りする記録があります。一般車は芝沢ゲートまでで、易老渡の登山口まで林道を歩きます。',
        'faq': '光岳の日帰りは、長い行動に慣れた健脚者に限られます。芝沢ゲートからの往復は標準コースタイムが約16時間（約26km・累積標高差約2,700m）で、日帰りの記録でも12〜13時間かかっています。一般には光岳小屋（予約制）に泊まる1泊2日です。',
        'src': ['https://yamap.com/model-courses/216', 'https://www.japanesealps.net/south/tekaridake/iroudo/']},
    'shiomidake': {
        'route': '鳥倉〜塩見岳往復', 'label': '日帰りは健脚者のみ',
        'note': '鳥倉登山口からの往復は、標準コースタイムが約14時間（約24km）。健脚者が未明に出発して11〜12時間で日帰りする記録があります。',
        'faq': '塩見岳は、健脚者なら鳥倉登山口から日帰りで往復できますが、標準コースタイムは約14時間（約24km）で、夜明け前の出発が前提です。無理のない計画は、三伏峠小屋か塩見小屋に泊まる1泊2日です。',
        'src': ['https://yamap.com/model-courses/213']},
    'kasagatake': {
        'route': '笠新道', 'label': '日帰りは健脚者のみ',
        'note': '新穂高から笠新道を往復する日帰りの記録があります（13時間半・約24km）。笠新道は登山口から笠ヶ岳山荘まで水場も山小屋もありません。',
        'faq': '笠ヶ岳は、健脚者なら新穂高から笠新道を日帰りで往復できますが、13時間前後（約24km・標高差約1,800m）かかり、途中に水場も山小屋もありません。一般には山頂直下の笠ヶ岳山荘に泊まる1泊2日です。',
        'src': ['https://tozan100kei.com/route/kasagatake-kasashindo.php', 'https://yamahack.com/4748']},
    'hirugata': {
        'route': None, 'label': '日帰りの最短',
        'new_route': {'name': '青根〜姫次〜蛭ヶ岳（往復）', 'time': '9時間45分', 'distance': '20.0km', 'waypoints': '青根登山口 → 黍殻避難小屋 → 姫次 → 蛭ヶ岳',
                      'trailheadName': '青根登山口（釜立林道）', 'status': {'state': 'caution', 'label': '日帰りの最短'},
                      'note': '蛭ヶ岳へ日帰りするときの最短コース。往復約20km・コースタイム9時間45分（YAMA HACK）。大倉から塔ノ岳・丹沢山を経由する往復は11時間以上かかります。',
                      'needsVerification': True, 'sourceUrl': 'https://yamahack.com/3215'},
        'faq': '蛭ヶ岳は、青根から姫次を経由する最短コースなら日帰りできます（往復約20km・コースタイム9時間45分）。大倉から塔ノ岳・丹沢山を越えて往復すると11時間以上かかるので、大倉側からは蛭ヶ岳山荘やみやま山荘に泊まる計画が一般的です。日の短い時期はヘッドランプを持ち、早めに出発してください。',
        'src': ['https://yamahack.com/3215', 'https://yamatabitabi.com/archives/169977']},
}
assert set(HARD) <= set(TARGET), set(HARD) - set(TARGET)

for mid in TARGET:
    m = N[mid]
    name = m['name']
    hit = [q for q in m['faq'] if '日帰り' in q['question']]
    assert len(hit) == 1, (mid, [q['question'] for q in m['faq']])
    q = hit[0]
    if mid in HARD:
        h = HARD[mid]
        assert not m.get('daytrip'), mid
        if h.get('new_route'):
            assert not any(r['name'] == h['new_route']['name'] for r in m['routes'])
            m['routes'].append(dict(h['new_route']))
        else:
            rs = [r for r in m['routes'] if h['route'] in r['name']]
            assert len(rs) == 1, (mid, [r['name'] for r in m['routes']])
            rs[0]['note'] = h['note']
            rs[0]['status'] = {'state': 'caution', 'label': h['label']}
        ans = h['faq']
        m['daytripSources'] = h['src']
    else:
        assert m.get('daytrip'), mid
        rs = [r for r in m['routes'] if minutes(r.get('time')) and (r.get('status') or {}).get('state') != 'closed' and '1泊' not in r['name'] and '泊' not in (r.get('time') or '')]
        rs.sort(key=lambda r: minutes(r['time']))
        assert rs, mid

        def desc(r):
            extra = '・'.join(x for x in (r.get('distance'), ('標高差' + r['elevation'].lstrip('+')) if r.get('elevation') else None) if x)
            return '%sは%s%s' % (r['name'], re.match(r'[^（〜]+', r['time']).group(0), ('（%s）' % extra) if extra else '')
        ans = 'はい、%sは日帰りできます。' % name
        ans += 'いちばん短い' + desc(rs[0]) + '。' if len(rs) > 1 else desc(rs[0]) + '。'
        if len(rs) > 1:
            ans += desc(rs[1]) + '。'
        if minutes(rs[0]['time']) >= 8 * 60:
            ans += '歩く時間が長いので、早朝に出発できる計画にしてください。'
        tr = m.get('trainTimeShinjuku')
        if tr:
            h_, mi = divmod(int(tr), 60)
            ans += '新宿から登山口までは、電車・バスで約%s。' % (('%d時間%d分' % (h_, mi)) if mi else '%d時間' % h_)
        for a in m.get('annualItems') or []:
            if a.get('kind') == 'trail' and a.get('validFrom') and a.get('validTo'):
                f, t = a['validFrom'].split('-'), a['validTo'].split('-')
                ans += 'ただし、山頂まで登れるのは決まった期間だけです（%s年は%d月%d日〜%d月%d日。期間外は登れません）。' % (f[0], int(f[1]), int(f[2]), int(t[1]), int(t[2]))
    q['question'] = '%sは日帰りできますか？所要時間の目安' % name
    q['answer'] = ans
    m['mountainUpdated'] = V
    print(mid, name, '｜', ans[:70])
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(TARGET), '山')
