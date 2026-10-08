#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""年次データの見張り：未確認だった5山のうち、確認できた分を登録する（2026-10-08）。
出典：
- 西吾妻山：天元台高原「ロープウェイ・リフト」https://www.green.tengendai.jp/ropeway-lift
  2026年 ロープウェイ 6月13日〜11月3日、夏山リフト 6月13日〜10月25日。
  運休日 6/17・6/24・7/1・7/8・8/19・8/26・9/2・9/9、10/27〜10/29
- 岩菅山：長電バス 奥志賀高原線は通年運行（2026年4月7日改正の時刻表、冬はスキーシーズンのダイヤ）。季節運行ではない
- 日向山：公共交通は通年（小淵沢駅からタクシー）。毎年変わるのは矢立石への林道の冬期閉鎖だけ。
  山梨県 県営林道通行規制情報 https://www.pref.yamanashi.jp/rindoujyouhou/ （前季は2025年12月10日〜2026年4月24日。今季は未発表）
- 雁坂嶺：甲州市の案内（窪平・西沢渓谷線、年の記載なし）で運行パターンを確認。
  西沢渓谷入口まで行くのは「4月下旬〜9月下旬の土日祝」と「4月下旬〜5月上旬、7月中旬〜8月中旬、10月上旬〜11月下旬」。
  それ以外は窪平止まり。2026年の日付は事業者サイトで確認できず、期限は登録しない
- 飯豊山：喜多方市のページは道路情報のみで、2026年の登山アクセスバスの運行日は確認できない。期限は登録しない
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-08'

# 西吾妻山
m = N['azuma']
SRC = 'https://www.green.tengendai.jp/ropeway-lift'
m['annualItems'] = [
    {'kind': 'transport', 'label': '天元台の夏山リフト（北望台まで）', 'validFrom': '2026-06-13', 'validTo': '2026-10-25',
     'seasonYear': 2026, 'sourceUrl': SRC, 'lastVerified': V, 'note': '水曜を中心に運休日あり'},
    {'kind': 'transport', 'label': '天元台ロープウェイ', 'validFrom': '2026-06-13', 'validTo': '2026-11-03',
     'seasonYear': 2026, 'sourceUrl': SRC, 'lastVerified': V, 'note': '10月27日〜29日は運休'},
    {'kind': 'info', 'label': '米沢駅〜白布温泉の山交バス', 'validFrom': None, 'validTo': None, 'seasonYear': None,
     'sourceUrl': 'https://www.yamakobus.jp/busroute5/yzs1/', 'lastVerified': '2026-10-06'}]
tr = m['trainRoutes']
tr['note'] = (tr['note'].rstrip('。') + '。2026年はロープウェイが6月13日〜11月3日、夏山リフトが6月13日〜10月25日の運行。'
              '6月17日・24日、7月1日・8日、8月19日・26日、9月2日・9日と10月27日〜29日は運休')
m['trainAccessHtml'] = render_ts_section(tr, m)
m['mountainUpdated'] = V

# 岩菅山
m = N['iwasugesan']
tr = m['trainRoutes']
tr['badge'] = {'type': 'year', 'style': None, 'icon': 'check', 'label': '通年運行（季節でダイヤが変わる）'}
m['annualItems'] = [{'kind': 'info', 'label': '湯田中駅〜志賀高原の長電バス「奥志賀高原線」のダイヤ', 'validFrom': None, 'validTo': None,
                     'seasonYear': None, 'sourceUrl': 'https://www.nagadenbus.co.jp/local/diagram/', 'lastVerified': V}]
m['annualNotApplicable'] = True
m['trainAccessHtml'] = render_ts_section(tr, m)
m['mountainUpdated'] = V

# 日向山
m = N['hinata']
m['annualItems'] = (m.get('annualItems') or []) + [
    {'kind': 'closure', 'label': '矢立石登山口への林道（雨乞尾白川線）の冬期閉鎖', 'validFrom': None, 'validTo': None,
     'seasonYear': None, 'sourceUrl': 'https://www.pref.yamanashi.jp/rindoujyouhou/', 'lastVerified': V,
     'note': '前季は2025年12月10日〜2026年4月24日。今季は未発表'}]
m['annualNotApplicable'] = True

# 雁坂嶺
m = N['karisaka']
tr = m['trainRoutes']
tr['summaryNote'] = ('※西沢渓谷入口まで行く便は例年、4月下旬〜9月下旬の土日祝と、4月下旬〜5月上旬・7月中旬〜8月中旬・10月上旬〜11月下旬だけ。'
                     'それ以外の日は窪平止まり。'
                     '運賃は特急かいじ利用（乗車券2,090円＋指定席1,580円）＋バス（1,220円）の合計')
m['trainAccessHtml'] = render_ts_section(tr, m)
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['山梨交通「西沢渓谷線」の2026年の運行日（西沢渓谷入口まで行く期間の正確な日付）が未確認。山梨交通 塩山営業所 0553-33-3141']
m['needsVerification'] = True
m['mountainUpdated'] = V

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
