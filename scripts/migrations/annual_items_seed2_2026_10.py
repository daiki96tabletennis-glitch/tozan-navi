#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""旧構造の山への annualItems 登録・第2回（2026-10-06）。
A: 2026年の運行期間を事業者・自治体の情報で確認できたもの（期間つき → ページに表示、期限切れを自動表示）
B: 期間は確認できず、出典ページだけ登録したもの（表示しない。変更検知の対象）
C: 通年運行で、毎年の更新が要らないもの（annualNotApplicable）
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-06'
def item(label, url, vf=None, vt=None, note=None, kind='transport'):
    d = {'kind': kind, 'label': label, 'validFrom': vf, 'validTo': vt, 'seasonYear': int(vt[:4]) if vt else None,
         'sourceUrl': url, 'lastVerified': V}
    if note: d['note'] = note
    return d

HIROGAWARA = item('甲府駅〜広河原の南アルプス登山バス', 'https://minami-alpskankou.jp/?page_id=6542', '2026-06-26', '2026-11-03', '時期と曜日で便が変わる。広河原〜北沢峠は2026年度運休')
NAKABUSA = item('穂高駅〜中房温泉の定期バス', 'https://nan-an.co.jp/nakabusa/', '2026-04-24', '2026-11-03', '所定日のみ運行')
OGIZAWA = item('信濃大町駅〜扇沢の路線バス', 'https://www.alpico.co.jp/traffic/local/hakuba/ogizawa/', '2026-04-15', '2026-11-30')
ALPEN = item('立山黒部アルペンルート', 'https://www.alpen-route.com/timetable/', '2026-04-15', '2026-11-30', '時刻表の有効期間')
URAGINZA = item('信濃大町駅〜七倉の裏銀座登山バス', 'https://uraginzabus.com/', '2026-07-17', '2026-10-25', '特定日のみ運行・予約不要')
SAWARA = [item('畑薙第一ダム〜椹島の送迎バス', 'https://www.t-forest.com/alpsinfo/bus/', '2026-07-11', '2026-10-12', '宿泊者限定・要予約'),
          item('静岡駅〜畑薙の静鉄バス「南アルプス登山線」', 'https://www.t-forest.com/alpsinfo/bus/', '2026-07-16', '2026-08-16', '予約制')]
ORITATE = item('富山駅〜折立の夏山バス', 'https://www.chitetsu.co.jp/?page_id=741', '2026-07-15', '2026-09-24', '8月27日までは毎日、9月は土日祝のみ・完全予約制')

A = {
    'kitadake': [HIROGAWARA], 'ainodake': [HIROGAWARA], 'noutori': [HIROGAWARA],
    'arikayama': [NAKABUSA], 'otenshoudake': [NAKABUSA],
    'kashimayari': [OGIZAWA], 'harinokidake': [OGIZAWA],
    'tateyama': [ALPEN],
    'eboshidake_kita': [URAGINZA], 'noguchigoro': [URAGINZA],
    'arakawadake': SAWARA, 'akaisidake': SAWARA,
    'yakushidake': [ORITATE], 'kurobegorodam': [ORITATE],
    'mizugaki': [item('韮崎駅〜みずがき山荘の路線バス（韮崎瑞牆線）', 'http://cus4.kyohoku.jp/routebus/kayagatakemizugakidenen-bus/schedule-mizugakiline/', '2026-04-04', '2026-11-23', '平日と土休日でダイヤが違う')],
    'nasu': [item('那須ロープウェイ行きの路線バス（春夏ダイヤ）', 'https://www.kantobus.co.jp/topics/topics.php?id=1416', '2026-04-01', '2026-11-30', '冬ダイヤの間は大丸温泉までで折り返し'),
             item('那須ロープウェイ', 'https://www.nasu-ropeway.jp/news/160', '2026-03-20', '2026-12-13')],
    'arasawadake': [item('浦佐駅〜銀山平・奥只見ダムの急行バス', 'https://www.minamiechigo.co.jp/', '2026-06-01', '2026-11-03', '土日祝と8月13〜16日のみ')],
    'amakazari': [item('南小谷駅〜雨飾高原の村営バス', 'https://www.vill.otari.nagano.jp/soshiki/kankochiikishinko-kankoshoko/gyomu/9/1/163.html', '2026-04-01', '2026-11-30')],
    'koganzan': [item('甲斐大和駅〜上日川峠のバス', 'https://eiwa-kotsu.jp/', '2026-04-18', '2026-12-13', '土日祝が基本')],
    'yakedake': [item('松本〜新島々〜上高地の路線バス（中の湯経由）', 'https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/', '2026-04-17', '2026-11-15', '予約優先制')],
    'hakusan': [item('金沢駅・松任駅〜別当出合の白山登山バス', 'https://map.ishikawa.jp/hakusan-bus-2025/', '2026-07-04', '2026-10-13')],
    'aizu_koma': [item('会津高原尾瀬口駅〜檜枝岐のバス（滝沢登山口まで）', 'https://www.aizubus.com/rosen/jikokuhyou', '2026-05-01', '2026-10-31')],
}
B = {
    'keirisan': ('茅野駅〜蓼科山登山口のバス', 'https://www.alpico.co.jp/traffic/local/suwa/'),
    'kirigamine': ('茅野駅・上諏訪駅〜霧ヶ峰のバス', 'https://www.alpico.co.jp/traffic/local/suwa/'),
    'makihata': ('南魚沼市のオンデマンド交通', 'https://www.city.minamiuonuma.niigata.jp/docs/ondemand-koutsu.html'),
    'shirane_gunma': ('草津温泉〜白根火山方面のバス', 'https://www.navitime.co.jp/bus/diagram/timelist?departure=00026039&arrival=00415568&line=00079689'),
    'kayagatake': ('韮崎駅〜深田記念公園のバス（韮崎深田公園線）', 'http://cus4.kyohoku.jp/routebus/kayagatakemizugakidenen-bus/schedule-fukadakoenline/'),
    'kentoku': ('山梨市駅〜乾徳山登山口のバス', 'https://www.city.yamanashi.yamanashi.jp/site/city-bus/9090.html'),
    'karisaka': ('山梨市駅・塩山駅〜西沢渓谷のバス', 'https://www.city.yamanashi.yamanashi.jp/site/city-bus/9090.html'),
    'iwasugesan': ('湯田中駅〜志賀高原のバス', 'https://www.nagadenbus.co.jp/local/diagram/'),
    'iizunasan': ('長野駅〜戸隠方面のバス', 'https://www.alpico.co.jp/traffic/local/nagano/togakushi/'),
    'shirasunayama': ('長野原草津口駅〜野反湖の町営バス', 'https://www.town.nakanojo.gunma.jp/soshiki/4/3615.html'),
    'nanaitsurasan': ('身延駅〜七面山登山口のバス', 'https://www.navitime.co.jp/diagram/bus/00598418/00090420/0/'),
    'azuma': ('米沢駅〜白布温泉のバス・天元台ロープウェイ', 'https://www.yamakobus.jp/busroute5/yzs1/'),
    'echigokoma': ('小出駅〜枝折峠のバス', 'https://www.minamiechigo.co.jp/'),
    'ontakesan': ('木曽福島駅〜田の原のバス', 'https://ontakekotsu.com/regular'),
    'shiomidake': ('伊那大島駅〜鳥倉登山口の登山バス（2026年の運行は終了。期間は未確認）', 'https://www.ibgr.jp/general-route/torikura_off2/'),
    'tairappyo': ('越後湯沢駅〜平標登山口のバス', 'https://www.minamiechigo.co.jp/rosen/'),
    'mitosaan': ('武蔵五日市駅〜都民の森のバス', 'https://www.nisitokyobus.co.jp/rosen/pocket.html'),
    'tsurugi': None,  # 既存（馬場島）に追加
    'iide': None, 'nokogiriyama': None, 'hijiridade': None,
}
C = ['amagi', 'otake', 'mitakesan']

for mid, items in A.items():
    cur = [x for x in (N[mid].get('annualItems') or []) if x.get('kind') != 'transport']
    N[mid]['annualItems'] = [dict(x) for x in items] + cur
for mid, v in B.items():
    if v:
        N[mid]['annualItems'] = (N[mid].get('annualItems') or []) + [item(v[0], v[1])]
N['tsurugi']['annualItems'] = [dict(ALPEN)] + N['tsurugi']['annualItems']
N['iide']['annualItems'].append(item('山都駅〜川入方面の登山アクセスバス', 'https://www.aizubus.com/rosen/jikokuhyou'))
N['nokogiriyama']['annualItems'].append(item('茅野駅〜戸台パークの南アルプスジオライナー', 'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_jikokuhyo.html'))
N['hijiridade']['annualItems'] = [dict(x) for x in SAWARA] + N['hijiridade']['annualItems']
for mid in C:
    N[mid]['annualNotApplicable'] = True
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(A), len([k for k, v in B.items() if v]) + 2, len(C))
