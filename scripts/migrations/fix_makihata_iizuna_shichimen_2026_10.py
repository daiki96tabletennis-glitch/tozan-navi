#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巻機山・飯縄山・七面山：「季節運行」の表記が実態と違っていたのを直す（2026-10-06）。
出典：南魚沼市観光協会（六日町〜清水線は2026年3月31日で廃止、4月1日からMOSS・平日のみ）、南魚沼市公式（MOSSの運行日・予約）、
      アルピコ交通（戸隠線は冬ダイヤあり＝通年運行。飯綱登山口に停車）、早川町観光協会（はやかわ乗合バスは毎日運行・1日4本）
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
DEPS = ('shinjuku', 'omiya', 'yokohama')
def resync(m):
    R = m['trainRoutes']['routes']
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V
def info(label, url):
    return {'kind': 'info', 'label': label, 'validFrom': None, 'validTo': None, 'seasonYear': None, 'sourceUrl': url, 'lastVerified': V}

# 巻機山：季節運行ではなく「平日のみ・予約制」
m = N['makihata']
m['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ 平日のみ・要予約'}
m['trainRoutes']['summaryNote'] = '※六日町駅〜清水の路線バスは2026年3月31日で廃止。4月1日からはオンデマンド交通「MOSS」だけ（月〜金、乗車の1週間前から30分前まで予約）'
m['annualItems'] = [info('六日町駅〜清水のオンデマンド交通「MOSS」', 'https://www.city.minamiuonuma.niigata.jp/docs/ondemand-koutsu.html')]
m['annualNotApplicable'] = True
resync(m)

# 飯縄山：戸隠線は通年運行。終点の表記をバス停名に合わせる
m = N['iizunasan']
m['trainRoutes']['badge'] = {'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'}
for dep in DEPS:
    legs = m['trainRoutes']['routes'][dep]['legs']
    assert legs[-1]['station'] == '一ノ鳥居苑地', dep
    legs[-1] = {'station': '飯綱登山口バス停（一ノ鳥居苑地）'}
m['trainRoutes']['summaryNote'] = '※戸隠線は通年運行（12月上旬〜3月は冬ダイヤ）。降りるバス停は「飯綱登山口」'
m['annualItems'] = [info('長野駅〜戸隠の路線バス（戸隠線）のダイヤ', 'https://www.alpico.co.jp/traffic/local/nagano/togakushi/')]
m['annualNotApplicable'] = True
resync(m)

# 七面山：バスは毎日運行。ただしバスが着くのは「七面山登山口・赤沢入口」で、羽衣まではタクシー
m = N['nanaitsurasan']
m['trainRoutes']['badge'] = {'type': 'year', 'style': None, 'icon': 'check', 'label': '毎日運行（1日4本）'}
for dep in DEPS:
    legs = m['trainRoutes']['routes'][dep]['legs']
    assert legs[-1]['station'] == '羽衣登山口（季節）' and legs[-2]['station'] == '身延駅', dep
    legs[-2]['method']['line'] = 'はやかわ乗合バス'
    legs[-1] = {'station': '七面山登山口・赤沢入口バス停', 'method': {'icon': 'taxi', 'line': 'タクシー（所要時間は未確認）'}, 'durationMin': None, 'fareYen': None}
    legs.append({'station': '羽衣登山口'})
m['trainRoutes']['note'] = ('💡 身延駅から、はやかわ乗合バス（奈良田温泉行き）で「七面山登山口・赤沢入口」へ。毎日運行だが1日4本しかない。'
                            'バス停から表参道の登山口（羽衣）までは離れているので、タクシーを使う。'
                            '登山用のザックを車内に持ち込むと、手回り品料金200円がかかる。'
                            '予約が必要との情報もあるため、乗る前に早川町へ確認する。'
                            '特急ふじかわ（甲府〜身延）を使えば約25分短縮できるが、特急券が別途必要で本数も少ない（表示は普通列車の場合）')
m['trainRoutes']['summaryNote'] = '※所要時間と運賃はバス停まで。羽衣までのタクシーは含まない'
m['annualItems'] = [info('身延駅〜奈良田温泉のはやかわ乗合バス', 'https://hayakawakankou.jp/access/')]
m['annualNotApplicable'] = True
m['needsVerification'] = True
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['はやかわ乗合バスの予約要否（農鳥岳のページでは「前日19時までの予約制」、早川町観光協会のページでは「予約不要」）',
                                                  'バス停〜羽衣のタクシーの時間と料金', '身延駅〜七面山登山口・赤沢入口のバスの所要時間（20分）']
resync(m)
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
