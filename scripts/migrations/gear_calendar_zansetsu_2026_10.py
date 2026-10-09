#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：残雪期の区分が甘かった山を、個別に調べて直す（2026-10-09）。
- 越後駒ヶ岳：6月上旬、小倉山の下・百草ノ池の上・駒の小屋の下・山頂直下に雪渓があり滑り止めが必要（新潟県観光協会、登山記録）
  → 6月を軽アイゼン等に。4月は同じ豪雪の山（巻機山・会津駒ヶ岳）に合わせて冬山装備に
- 荒沢岳：越後駒ヶ岳と同じ山域。個別の記録は取れていないが、同じ扱いにする（安全側）
- 燧ヶ岳：5月下旬〜6月中旬は北面に雪が残り、雪山装備がなければ無理をしない時期。6月も登山道の半分以上が雪で、チェーンスパイクか軽アイゼンが必要
  → 5月を冬山装備、6月を軽アイゼン等に
- 妙高山：燕温泉側は6月ごろまで雪。6月上旬の記録でもろい雪渓。登山適期は7月上旬から → 6月を軽アイゼン等に
- 高妻山：11〜6月は雪。登山適期は7月上旬から。6月はアイゼンを持って登る記録 → 6月を軽アイゼン等に
- 黒姫山：高妻山と同じ戸隠・頸城の山。個別の記録は取れていないが、同じ扱いにする（安全側）
- 谷川岳：5月末、肩の小屋直下の雪渓はアイゼン必須で滑落が多い。群馬県の登山道情報で「天神尾根の残雪は無くなりました」は7月13日
  → 6月を軽アイゼン等に
- 白山：6月は軽アイゼンで歩ける残雪。7月も上部に雪渓が残る年がある（切替日は不明）→ 7月を安全側で軽アイゼン等に
- 木曽駒ヶ岳：本格的なアイゼンが要るのは6月中旬ごろまでで、7月も状況により必要 → 7月を安全側で軽アイゼン等に
- 白馬岳（栂池ルート）：白馬乗鞍岳は6〜7月に大きな雪渓の上を歩く → 7月を軽アイゼン等に
旧フィールド・FAQ・装備カードも同じ内容に揃える。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gear_calendar as G
from build_derived import ranges
P = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
D = json.load(open(P, encoding='utf-8'))
GD = json.load(open(GP, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-09'
LIGHT = {'c': 'crampon', 'i': '推奨', 'p': 'エバニュー 6本爪アイゼン',
         'r': '凍結・残雪が見られる時期です。チェーンスパイクや6本爪アイゼンなどの軽アイゼン等があると滑りにくく安心です。事前に最新の積雪・凍結情報を確認してください。'}
W_SHOE = {'c': 'shoe', 'i': '必須', 'p': 'スカルパ マンタテックGTX', 'r': '本格的な積雪期です。アイゼン対応の冬季ブーツに切り替えましょう。'}
W_CRAMPON = {'c': 'crampon', 'i': '推奨', 'p': 'グリベル G12 ニュークラシック',
             'r': '本格的な積雪期です。12本爪アイゼン・ピッケル等の冬山装備と、雪山の経験が必要です。事前に最新の積雪・凍結情報を確認してください。'}
GEAR = {'light_crampons': 'snow_caution', 'winter_gear': 'winter'}
PLAN = {  # id: {月: (変更前, 変更後)}
    'echigokoma': {4: ('light_crampons', 'winter_gear'), 6: ('no_crampons', 'light_crampons')},
    'arasawadake': {4: ('light_crampons', 'winter_gear'), 6: ('no_crampons', 'light_crampons')},
    'hiuchigatake': {5: ('light_crampons', 'winter_gear'), 6: ('no_crampons', 'light_crampons')},
    'myoko': {6: ('no_crampons', 'light_crampons')},
    'takatsuma': {6: ('no_crampons', 'light_crampons')},
    'kurohimesan': {6: ('no_crampons', 'light_crampons')},
    'tanigawa': {6: ('no_crampons', 'light_crampons')},
    'hakusan': {7: ('no_crampons', 'light_crampons')},
    'kisokoma': {7: ('no_crampons', 'light_crampons')},
    'shirouma': {7: ('no_crampons', 'light_crampons')},
}
FAQ = {
    'echigokoma': '越後駒ヶ岳の登山シーズンは7月〜10月が目安です。豪雪地帯のため6月も登山道に雪渓が残り、軽アイゼン等が必要です。5月までは冬山装備が必要な時期です。残雪の状況は年によって変わるため、直前の最新情報を確認してください。',
    'arasawadake': '荒沢岳の登山シーズンは7月〜10月が目安です。豪雪地帯のため6月も雪が残り、軽アイゼン等が必要になることがあります。5月までは冬山装備が必要な時期です。残雪の状況は年によって変わるため、直前の最新情報を確認してください。',
    'myoko': '妙高山の登山シーズンは7月〜10月が目安です。6月は登山道に雪渓が残り、軽アイゼン等が必要です。残雪の状況は年によって変わるため、直前の最新情報を確認してください。',
    'takatsuma': '高妻山の登山シーズンは7月〜10月が目安です。6月は山頂付近などに雪が残り、軽アイゼン等が必要になることがあります。残雪の状況は年によって変わるため、直前の最新情報を確認してください。',
    'kurohimesan': '黒姫山の登山シーズンは7月〜10月が目安です。6月は雪が残り、軽アイゼン等が必要になることがあります。残雪の状況は年によって変わるため、直前の最新情報を確認してください。',
    'hakusan': '白山の登山シーズンは7月〜10月が目安です。7月も上部に雪渓が残る年があり、軽アイゼン等が必要になることがあります。6月は残雪が多く、5月までは冬山装備が必要な時期です。残雪の状況は年によって変わるため、直前の最新情報を確認してください。',
}


def winter_cards(mid, mo):
    cards = [c for c in GD[mid][str(mo)] if c['c'] not in ('shoe', 'crampon', 'crampon_next')]
    GD[mid][str(mo)] = [dict(W_SHOE)] + [c for c in cards if c['c'] == 'rain'] + [dict(W_CRAMPON)] + [c for c in cards if c['c'] != 'rain']


def light_cards(mid, mo):
    cards = GD[mid][str(mo)]
    cards[:] = [c for c in cards if c['c'] != 'crampon']
    idx = max(i for i, c in enumerate(cards) if c['c'] in ('shoe', 'rain')) + 1
    cards.insert(idx, dict(LIGHT))


for mid, plan in PLAN.items():
    m = N[mid]
    ssot = m.get('dataModel') == 'ssot-v1'
    for mo, (before, after) in plan.items():
        assert m['gearCalendar'][mo - 1] == before, (mid, mo, m['gearCalendar'][mo - 1])
        if ssot:
            m['conditions']['gearMonthly'][mo - 1] = GEAR[after]
        else:
            m['gearCalendar'][mo - 1] = after
            m['seasonCalendar'][mo - 1] = G.CLS[after]
        (winter_cards if after == 'winter_gear' else light_cards)(mid, mo)
    if ssot:
        m['conditions']['gearSource'] = '残雪期の区分を登山記録などで見直し（2026-10-09）'
    else:
        assert not G.validate(m['gearCalendar'])
        keys = set(e for e in m['gearCalendar'] if isinstance(e, str))
        m['calLegend'] = [G.LABEL[k] for k in G.KEYS if k in keys]
        m['seasonNoGear'] = ranges([i + 1 for i in range(12) if m['gearCalendar'][i] == 'no_crampons'])
        hit = [q for q in m['faq'] if 'シーズン' in q['question']]
        assert len(hit) == 1, mid
        hit[0]['answer'] = FAQ[mid]
    m['mountainUpdated'] = V

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(GD, open(GP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
