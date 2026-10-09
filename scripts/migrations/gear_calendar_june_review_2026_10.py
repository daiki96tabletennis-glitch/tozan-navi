#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：6月の区分を山ごとに調べ直した結果を反映する（2026-10-09）。
前回、北ア・南アの2,800m以上の21山を一括で6月＝冬山装備にしたが、運営者の指示で個別に検索・登山記録を確認した。
■ 軽アイゼン等に戻す（6月は軽い滑り止めで歩かれている）
  - 立山：6月下旬、室堂〜一ノ越はシャリ雪でところどころ夏道。チェーンスパイクがあると楽、との登山記録
  - 乗鞍岳（畳平〜剣ヶ峰）：6月は登山道に残雪が数か所。軽アイゼンがあるとよい／チェーンスパイク不要、との登山記録
  - 薬師岳：2026年6月の登山記録でチェーンスパイクを使用。残雪は6月上旬〜7月中旬
  - 大天井岳：燕山荘の案内「大天井岳まで縦走する方は6本歯以上のアイゼンを」
■ 冬山装備に変える
  - 木曽駒ヶ岳：11〜6月は雪山装備が必要（八丁坂の雪の急斜面）
  - 飯豊山：6月上旬に登山シーズンが始まるが、雪渓が残り7月上旬までアイゼン・ピッケルが必要な場合がある
    → 6月を冬山装備、7月は切替日不明のため安全側で軽アイゼン等
■ 冬山装備のまま（根拠あり）：白馬岳（長野県警：6月下旬の雪渓はアイゼン＋ピッケル推奨）、剱岳（10〜6月は積雪期）、
  常念岳（一ノ沢は6月中旬まで雪渓）、笠ヶ岳（6月は標高2,000mから雪）、鹿島槍ヶ岳（6月上旬に雪上の滑落）、北岳、五竜岳
■ 冬山装備のまま（根拠が取れず、安全側）：黒部五郎岳、野口五郎岳、仙丈ヶ岳、甲斐駒ヶ岳、間ノ岳、農鳥岳、塩見岳、赤石岳、荒川岳、聖岳
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gear_calendar as G
from build_derived import ranges
P = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
BK = sys.argv[1]  # 一括変更前の gear-data.json（6月のカードを戻すため）
D = json.load(open(P, encoding='utf-8'))
GD = json.load(open(GP, encoding='utf-8'))
OLD = json.load(open(BK, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-09'
LIGHT = {'c': 'crampon', 'i': '推奨', 'p': 'エバニュー 6本爪アイゼン',
         'r': '凍結・残雪が見られる時期です。チェーンスパイクや6本爪アイゼンなどの軽アイゼン等があると滑りにくく安心です。事前に最新の積雪・凍結情報を確認してください。'}
W_SHOE = {'c': 'shoe', 'i': '必須', 'p': 'スカルパ マンタテックGTX', 'r': '本格的な積雪期です。アイゼン対応の冬季ブーツに切り替えましょう。'}
W_CRAMPON = {'c': 'crampon', 'i': '推奨', 'p': 'グリベル G12 ニュークラシック',
             'r': '本格的な積雪期です。12本爪アイゼン・ピッケル等の冬山装備と、雪山の経験が必要です。事前に最新の積雪・凍結情報を確認してください。'}


def set_month(m, mo, key):
    gear = {'no_crampons': 'normal', 'light_crampons': 'snow_caution', 'winter_gear': 'winter'}[key]
    if m.get('dataModel') == 'ssot-v1':
        m['conditions']['gearMonthly'][mo - 1] = gear
    else:
        m['gearCalendar'][mo - 1] = key
        m['seasonCalendar'][mo - 1] = G.CLS[key]
        keys = set(e for e in m['gearCalendar'] if isinstance(e, str))
        m['calLegend'] = [G.LABEL[k] for k in G.KEYS if k in keys]
        m['seasonNoGear'] = ranges([i + 1 for i in range(12) if m['gearCalendar'][i] == 'no_crampons'])
    m['mountainUpdated'] = V


def winter_cards(mid, mo):
    cards = [c for c in GD[mid][str(mo)] if c['c'] not in ('shoe', 'crampon', 'crampon_next')]
    GD[mid][str(mo)] = [dict(W_SHOE)] + [c for c in cards if c['c'] == 'rain'] + [dict(W_CRAMPON)] + [c for c in cards if c['c'] != 'rain']


def light_cards(mid, mo):
    cards = GD[mid][str(mo)]
    cards[:] = [c for c in cards if c['c'] != 'crampon']
    idx = max(i for i, c in enumerate(cards) if c['c'] in ('shoe', 'rain')) + 1
    cards.insert(idx, dict(LIGHT))


for mid in ('tateyama', 'norikura', 'yakushidake', 'otenshoudake'):
    m = N[mid]
    assert m['gearCalendar'][5] == 'winter_gear', mid
    set_month(m, 6, 'light_crampons')
    GD[mid]['6'] = OLD[mid]['6']
    if m.get('dataModel') == 'ssot-v1':
        m['conditions']['gearSource'] = '6月は登山記録で軽い滑り止めで歩かれているため軽アイゼン等（2026-10-09）'

for mid in ('kisokoma', 'iide'):
    m = N[mid]
    assert m['gearCalendar'][5] == 'light_crampons', mid
    set_month(m, 6, 'winter_gear')
    winter_cards(mid, 6)
    if m.get('dataModel') == 'ssot-v1':
        m['conditions']['gearSource'] = '6月は八丁坂などに雪が残り雪山装備が必要なため冬山装備（2026-10-09）'
m = N['iide']
assert m['gearCalendar'][6] == 'no_crampons'
set_month(m, 7, 'light_crampons')
light_cards('iide', 7)
hit = [q for q in m['faq'] if 'シーズン' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = ('飯豊山の登山シーズンは7月〜9月が目安です。豪雪地帯のため6月は雪渓が残り、12本爪アイゼン・ピッケル等の冬山装備が必要です。'
                    '7月も上旬までは雪渓が残り、軽アイゼン等が必要になることがあります。残雪の状況は年によって変わるため、直前の最新情報を確認してください。')

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(GD, open(GP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
