#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""旧構造の山に annualItems（毎年変わる情報：期間・出典・確認日）を持たせる最初の登録（2026-10-06）。
期間つきの項目は山ページに表示され、期限を過ぎると自動で「終了」の注記が付く。
期間なしの項目（災害の通行止めなど）は表示せず、出典ページの変更検知だけに使う。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-06'
def item(kind, label, url, vf=None, vt=None, note=None):
    d = {'kind': kind, 'label': label, 'validFrom': vf, 'validTo': vt, 'seasonYear': int(vt[:4]) if vt else None,
         'sourceUrl': url, 'lastVerified': V}
    if note: d['note'] = note
    return d
SEED = {
    'chogatake': [
        item('transport', '松本〜新島々〜上高地の路線バス', 'https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/', '2026-04-17', '2026-11-15', '予約優先制'),
        item('transport', '穂高駅〜三股の路線バス「三股線」', 'https://www.city.azumino.nagano.jp/soshiki/6/129486.html', '2026-07-17', '2026-10-13', '期間中の63日間のみ・WEB予約必須'),
    ],
    'houou': [item('transport', '韮崎駅〜青木鉱泉・御座石温泉の登山バス', 'https://houougoya.jp/access/', '2026-06-20', '2026-10-12', '土日と三連休のみ・完全予約制')],
    'terkari': [item('transport', '道の駅遠山郷〜易老渡の予約制タクシー', 'https://tohyamago.com/archives/3681', '2026-07-01', '2026-11-08', '4時30分発・事前予約')],
    'utsukushigahara': [item('transport', '松本駅〜美ヶ原自然保護センターの直行バス', 'https://visitmatsumoto.com/news/detail_22.html', '2026-06-06', '2026-10-12', '土日祝。7月13日〜8月31日は毎日')],
    'hijiridade': [item('closure', '便ヶ島〜西沢渡の通行止め（災害復旧）', 'https://tohyamago.com/archives/18')],
    'nokogiriyama': [item('closure', '戸台河原駐車場の利用不可', 'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_tozan/tozanshanominasamahe/2021todaigawara.html')],
    'iide': [item('closure', '弥平四郎側：新長坂ルートの通行止め・林道の状況', 'https://www.town.nishiaizu.fukushima.jp/site/kanko/797.html')],
    'hinata': [item('closure', '錦滝方面の通行禁止・林道の冬季閉鎖', 'https://www.yamanashi-kankou.jp/kankou/spot/p2_2225.html')],
    'tsurugi': [item('info', '馬場島の利用期間・アクセス', 'https://www.town.kamiichi.toyama.jp/page/2045.html')],
    'arafune': [item('info', '相沢登山口の駐車場・コース状況', 'https://www.town.shimonita.lg.jp/kanko/m03/m05/05.html')],
    'kumotori': [item('info', '三峯神社線の運賃・便数', 'https://www.seibubus.co.jp/sp/rosen/mitsumine/')],
}
for mid, items in SEED.items():
    N[mid]['annualItems'] = items
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(' '.join(SEED))
