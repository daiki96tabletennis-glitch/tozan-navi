#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSOT移行 Phase A/B（2026-10-05）
P0の山（至仏山・白馬岳・甲斐駒ヶ岳・仙丈ヶ岳・常念岳・赤岳・燧ヶ岳・富士山）を
「山 → ルート → 登山口 → アクセス → 季節条件」の新構造へ移行する一回限りのスクリプト。

・data/trailheads.json / data/accesses.json を新規作成
・mountains.json の対象山に representativeRouteId / routes[].id,trailheadId,accessId / conditions / alerts を追加
・旧フィールドは削除しない（scripts/build_derived.py が新構造から上書き生成する）
・確認できない値は null ＋ needsVerification: true（推測で埋めない）
"""
import json, os, re, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8')); N = {m['id']: m for m in D}
TODAY = '2026-10-05'

def th(id, name, typ, lat, lng, src, verified=True, note=None):
    d = {'id': id, 'name': name, 'type': typ, 'lat': lat, 'lng': lng,
         'coordSource': src, 'lastVerified': TODAY, 'needsVerification': not verified}
    if note: d['note'] = note
    return d
GSI = '国土地理院 地名検索（msearch.gsi.go.jp）'
BTN = '既存の地図ボタン座標（Googleプレイス）'
TH = [
 th('hatomachi-toge', '鳩待峠', 'trailhead', 36.89022, 139.20032, GSI),
 th('oze-tokura', '尾瀬戸倉（駐車場・乗換）', 'accessHub', None, None, None, False, '座標未確認。地図は名称検索で開く'),
 th('sarukura', '猿倉', 'trailhead', 36.74581, 137.80090, GSI + '「猿倉荘」'),
 th('tsugaike-shizenen', '栂池自然園', 'trailhead', 36.78065, 137.81857, GSI + '「栂池自然園ビジターセンター」'),
 th('tsugaike-kogen', '栂池高原駅（ゴンドラ乗り場）', 'accessHub', 36.74946, 137.87143, GSI),
 th('kitazawa-toge', '北沢峠', 'trailhead', 35.74220, 138.21367, GSI),
 th('todai-park', '戸台パーク（駐車場・林道バス乗り場）', 'accessHub', None, None, None, False, '座標未確認。地図は名称検索で開く'),
 th('chikuu-komagatake-jinja', '竹宇駒ヶ岳神社（尾白川渓谷駐車場）', 'trailhead', None, None, None, False, '座標未確認'),
 th('ichinosawa', '一ノ沢登山口', 'trailhead', 36.3328384, 137.7764743, BTN, False),
 th('mitsumata', '三股登山口', 'trailhead', None, None, None, False, '座標未確認'),
 th('minotoguchi', '美濃戸口', 'trailhead', 35.981923, 138.300997, BTN + '／国土地理院「美濃戸別荘地」付近で照合'),
 th('oze-miike', '御池', 'trailhead', 36.9837812, 139.3042064, BTN, False),
 th('numayama-toge', '沼山峠', 'trailhead', 36.94768, 139.33505, GSI + '「沼山峠休憩所」'),
 th('fujinomiya-5th', '富士宮口五合目', 'trailhead', 35.336923, 138.732619, BTN, False),
 th('mizugatsuka', '水ヶ塚駐車場（マイカー規制時の乗換）', 'accessHub', None, None, None, False, '座標未確認。地図は名称検索で開く'),
 th('subaru-5th', '富士スバルライン五合目（吉田口）', 'trailhead', None, None, None, False, '座標未確認'),
]

def take_access(mid, aid, name, th_id, **kw):
    """既存の山データの電車アクセスを、そのままアクセスデータへ移す"""
    m = N[mid]
    a = {'id': aid, 'name': name, 'trailheadId': th_id, 'mapTargetId': kw.pop('mapTargetId', th_id),
         'trainRoutes': copy.deepcopy(m.get('trainRoutes')),
         'fares': {'shinjuku': m.get('fareShinjuku'), 'omiya': m.get('fareOmiya'), 'yokohama': m.get('fareYokohama')},
         'trainTimes': {'shinjuku': m.get('trainTimeShinjuku'), 'omiya': m.get('trainTimeOmiya'), 'yokohama': m.get('trainTimeYokohama')},
         'transfers': {'shinjuku': m.get('transfersShinjuku'), 'omiya': m.get('transfersOmiya'), 'yokohama': m.get('transfersYokohama')},
         'busLinks': m.get('busLinks'), 'busScheduleLinks': m.get('busScheduleLinks'),
         'car': kw.pop('car', None), 'operation': kw.pop('operation', None),
         'sourceUrl': kw.pop('sourceUrl', None), 'lastVerified': TODAY,
         'needsVerification': kw.pop('needsVerification', False)}
    a.update(kw)
    return a
def empty_access(aid, name, th_id, note, **kw):
    a = {'id': aid, 'name': name, 'trailheadId': th_id, 'mapTargetId': kw.pop('mapTargetId', th_id), 'trainRoutes': None,
         'fares': None, 'trainTimes': None, 'transfers': None, 'busLinks': None, 'busScheduleLinks': None,
         'car': kw.pop('car', None), 'operation': kw.pop('operation', None), 'sourceUrl': kw.pop('sourceUrl', None),
         'lastVerified': TODAY, 'needsVerification': True, 'note': note}
    a.update(kw); return a
def op(statusType, mode, validFrom=None, validTo=None, reservation=None, note=None, year=2026):
    return {'statusType': statusType, 'mode': mode, 'validFrom': validFrom, 'validTo': validTo,
            'seasonYear': year, 'reservation': reservation, 'note': note}

AC = []
# 至仏山：鳩待峠
AC.append(take_access('shibutsu', 'hatomachi-toge', '鳩待峠へのアクセス（戸倉で乗換）', 'hatomachi-toge', mapTargetId='oze-tokura',
    car={'parking': N['shibutsu'].get('parking'), 'restriction': '鳩待峠へはマイカーで入れない。戸倉駐車場で乗合バス・乗合タクシーに乗り換える'},
    operation=op('annual', 'seasonal', None, None, None, '戸倉〜鳩待峠の乗合バス・タクシーの2026年の運行期間は未確認'),
    needsVerification=True))
# 白馬岳：猿倉／栂池
AC.append(take_access('shirouma', 'sarukura', '猿倉へのアクセス', 'sarukura',
    car={'parking': N['shirouma'].get('parking'), 'restriction': None},
    operation=op('annual', 'seasonal', None, None, '運行日限定・予約制（空席があれば当日乗車可）', '猿倉線の2026年の運行日は公式時刻表で確認'),
    sourceUrl='https://www.alpico.co.jp/traffic/', needsVerification=True))
AC.append(empty_access('tsugaike', '栂池自然園へのアクセス（ゴンドラ・ロープウェイ）', 'tsugaike-shizenen', '電車・バスの経路と運賃は未作成（要確認）', mapTargetId='tsugaike-kogen'))
# 甲斐駒ヶ岳・仙丈ヶ岳：北沢峠（戸台パーク経由）
kz = take_access('komagatake', 'kitazawa-toge', '北沢峠へのアクセス（戸台パークから林道バス）', 'kitazawa-toge', mapTargetId='todai-park',
    car={'parking': '戸台パーク駐車場（林道バス乗り場）', 'restriction': '北沢峠へは一般車両で入れない。戸台パークから南アルプス林道バスに乗り換える'},
    operation=op('annual', 'seasonal', '2026-06-01', '2026-11-03', None, '戸台口〜北沢峠の運行期間（4/25〜5/31は歌宿まで）。山梨側の広河原〜北沢峠は災害復旧のため運行休止'),
    sourceUrl='https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_jikokuhyo.html')
AC.append(kz)
AC.append(empty_access('chikuu', '竹宇駒ヶ岳神社へのアクセス（黒戸尾根）', 'chikuu-komagatake-jinja', '電車・バスの経路と運賃は未作成（要確認）'))
# 常念岳：一ノ沢／三股
AC.append(take_access('jonengatake', 'ichinosawa', '一ノ沢登山口へのアクセス（林道通行止め中）', 'ichinosawa',
    car={'parking': None, 'restriction': '林道一ノ沢線は一般車両通行止め。市内の駐車場に停め、地元タクシーで通行止め箇所の手前まで行き、歩行者用通路を通って登山口へ（約1.5km）'},
    operation=op('temporary', 'restricted', None, '2027-01-31', None, '災害復旧工事の竣工予定は令和9年（2027年）1月末'),
    sourceUrl='https://www.city.azumino.nagano.jp/soshiki/32/66871.html'))
AC.append(empty_access('mitsumata', '三股登山口へのアクセス', 'mitsumata', '電車・バスの経路と運賃は未作成（要確認）'))
# 赤岳：美濃戸口
AC.append(take_access('yatsugatake', 'minotoguchi', '美濃戸口へのアクセス', 'minotoguchi',
    car={'parking': N['yatsugatake'].get('parking'), 'restriction': None},
    operation=op('annual', 'seasonal', '2026-05-02', '2026-10-25', None, '茅野駅〜美濃戸口線の2026年の運行期間'),
    sourceUrl='https://www.alpico.co.jp/traffic/local/suwa/minotoguchi/'))
# 燧ヶ岳：御池／沼山峠
AC.append(take_access('hiuchigatake', 'oze-miike', '御池へのアクセス', 'oze-miike',
    car={'parking': N['hiuchigatake'].get('parking'), 'restriction': '御池への道路は冬期閉鎖（2026年は4/24 14時に開通）'},
    operation=op('annual', 'seasonal', '2026-04-24', None, None, '道路の開通日。会津バス檜枝岐線の2026年の運行期間は未確認'),
    sourceUrl='https://oze-fnd.or.jp/archives/197543/', needsVerification=True))
AC.append(empty_access('numayama-toge', '沼山峠へのアクセス（御池からシャトルバス）', 'numayama-toge',
    '御池までは「御池へのアクセス」と同じ。御池〜沼山峠はシャトルバス（片道900円、2026年は5/23〜10/25運行）。所要時間は未確認',
    mapTargetId='oze-miike', viaAccessId='oze-miike',
    car={'parking': N['hiuchigatake'].get('parking'), 'restriction': '御池〜沼山峠は一般車両通行不可。御池駐車場からシャトルバスに乗り換える'},
    operation=op('annual', 'seasonal', '2026-05-23', '2026-10-25', None, '御池〜沼山峠シャトルバスの2026年の運行期間'),
    sourceUrl='https://news.aizubus.com/entry/2026/05/15/093130'))
# 富士山：富士宮口／吉田口
AC.append(empty_access('fujinomiya-5th', '富士宮口五合目へのアクセス', 'fujinomiya-5th',
    '電車・バスの経路と運賃は未作成（要確認）。マイカー規制期間（2026年は7/10 9:00〜9/10 18:00）は水ヶ塚駐車場からシャトルバス（片道1,320円・往復2,400円・約40分）',
    mapTargetId='mizugatsuka',
    car={'parking': '水ヶ塚駐車場（マイカー規制期間の乗換駐車場）', 'restriction': '2026年は7/10 9:00〜9/10 18:00がマイカー規制。期間中は水ヶ塚駐車場からシャトルバスで富士宮口五合目へ'},
    operation=op('annual', 'seasonal', '2026-07-10', '2026-09-10', None, '開山期間・マイカー規制期間（富士宮口）'),
    sourceUrl='https://www.pref.shizuoka.jp/machizukuri/doro/fujisandoro/1029179.html'))
AC.append(take_access('fuji', 'subaru-5th', '富士スバルライン五合目（吉田口）へのアクセス', 'subaru-5th',
    car=None, operation=op('annual', 'seasonal', '2026-07-01', '2026-09-10', None, '吉田ルートの2026年の開山期間'),
    sourceUrl='https://www.pref.yamanashi.jp/fujisan/annzenn/documents/r8fujitozan.html', needsVerification=True))

# 駅名に混ざっていた注記の整理・バッジ修正
for a in AC:
    tr = a.get('trainRoutes')
    if not tr: continue
    if a['id'] == 'oze-miike':
        for r in tr['routes'].values(): r['legs'][-1]['station'] = '御池'
    if a['id'] == 'minotoguchi':
        tr['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ 季節運行（2026年は5/2〜10/25）'}
        for r in tr['routes'].values(): r['legs'][-1]['station'] = '美濃戸口'
    if a['id'] == 'kitazawa-toge':
        tr['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ 季節運行（2026年は6/1〜11/3）'}
        for r in tr['routes'].values(): r['legs'][-1]['station'] = '北沢峠'
    if a['id'] == 'ichinosawa':
        tr['note'] = ('💡 林道一ノ沢線は災害のため一般車両通行止め（復旧工事の竣工予定は2027年1月末）。'
                      '穂高駅から地元タクシー（南安タクシー・安曇観光タクシー・あづみの第一交通）で通行止め箇所の手前まで行き、'
                      '歩行者用通路を通って登山口まで約1.5km歩く。'
                      '三股コースは季節限定の予約制タクシーで三股まで行く方法もある。')

# 住所（既存データで登山口・拠点と一致しているものだけ引き継ぐ。不明は空）
ADDR = {'oze-tokura': '群馬県利根郡片品村戸倉', 'hatomachi-toge': '群馬県利根郡片品村戸倉', 'todai-park': '長野県伊那市長谷',
        'ichinosawa': '長野県安曇野市穂高有明', 'minotoguchi': '長野県茅野市泉野', 'oze-miike': '福島県南会津郡檜枝岐村',
        'numayama-toge': '福島県南会津郡檜枝岐村', 'fujinomiya-5th': '静岡県富士宮市粟倉地先', 'sarukura': '長野県北安曇郡白馬村北城'}
for t in TH: t['address'] = ADDR.get(t['id'])
json.dump({t['id']: t for t in TH}, open(os.path.join(ROOT, 'data', 'trailheads.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump({a['id']: a for a in AC}, open(os.path.join(ROOT, 'data', 'accesses.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# ── 山データ ──
GEAR = {'s-ok': 'normal', 's-gear': 'snow_caution', 's-hard': 'winter'}
def base_conditions(m):
    if (m.get('conditions') or {}).get('gearMonthly'):  # 再実行時は既存の値を使う
        return {'gearMonthly': list(m['conditions']['gearMonthly']), 'trailPeriods': [], 'gearSource': m['conditions'].get('gearSource')}
    return {'gearMonthly': [GEAR[c] for c in m['seasonCalendar']], 'trailPeriods': [], 'gearSource': '旧シーズンカレンダーから変換（アイゼン本数の断定はやめ、3段階に読み替え）'}
def setup(mid, rep, route_defs, alerts=None, trail_periods=None, gear_override=None):
    m = N[mid]
    assert len(route_defs) == len(m['routes']), mid
    for r, (rid, thid, acid, extra) in zip(m['routes'], route_defs):
        r['id'] = rid; r['trailheadId'] = thid; r['accessId'] = acid
        r.pop('status', None)
        if extra: r.update(extra)
    m['representativeRouteId'] = rep
    c = base_conditions(m)
    if trail_periods: c['trailPeriods'] = trail_periods
    if gear_override:
        for i, g in gear_override.items(): c['gearMonthly'][i - 1] = g
    m['conditions'] = c
    m['alerts'] = alerts or []
    m['dataModel'] = 'ssot-v1'
    m['mountainUpdated'] = TODAY
def alert(title, text, level, statusType, src, validFrom=None, validTo=None, link=None):
    return {'title': title, 'text': text, 'level': level, 'statusType': statusType, 'validFrom': validFrom, 'validTo': validTo,
            'sourceUrl': src, 'linkText': link or '公式情報', 'lastVerified': TODAY}

# 標高差の表記エラー（++900mm）を修正
for r in N['hiuchigatake']['routes']:
    r['elevation'] = re.sub(r'^\++(\d+)m+$', r'+\1m', r['elevation'])

setup('shibutsu', 'hatomachi-roundtrip',
  [('hatomachi-roundtrip', 'hatomachi-toge', 'hatomachi-toge', None), ('yamanohana-traverse', 'hatomachi-toge', 'hatomachi-toge', None)],
  alerts=[alert('至仏山は残雪期に登山道が全面閉鎖されます', '2026年は5月7日〜6月19日、鳩待峠〜オヤマ沢田代〜至仏山〜山ノ鼻の登山道が閉鎖されました（植生保護のため。残雪の状況で期間が変わることがあります）。通常の登山は6月20日からです。鳩待峠へはマイカーで入れず、戸倉で乗合バス・タクシーに乗り換えます。', 'yellow', 'annual', 'https://oze-fnd.or.jp/archives/197701/', link='尾瀬保護財団')],
  trail_periods=[{'from': '2026-05-07', 'to': '2026-06-19', 'status': 'closed', 'label': '登山道全面閉鎖（植生保護）', 'sourceUrl': 'https://oze-fnd.or.jp/archives/197701/'}])
setup('shirouma', 'tsugaike-roundtrip',
  [('daisekkei-roundtrip', 'sarukura', 'sarukura', {'status': {'state': 'closed', 'from': '2026-08-31', 'to': None, 'label': '通行止め（2026年8月31日〜当面の間）', 'statusType': 'temporary', 'sourceUrl': 'https://hakubakan.com/hut/trail260826/', 'lastVerified': TODAY}}),
   ('tsugaike-roundtrip', 'tsugaike-shizenen', 'tsugaike', None)],
  alerts=[alert('白馬大雪渓ルートは通行止め', '大雨の影響で大雪渓の融雪が早く進み、2026年8月31日から当面の間、白馬大雪渓ルートは通行止めです。白馬岳へは栂池（白馬大池）ルート、または猿倉から白馬鑓温泉ルートを利用してください。', 'red', 'temporary', 'https://hakubakan.com/hut/trail260826/', validFrom='2026-08-31', link='白馬館の通行止め情報')])
KZ_ALERT = alert('北沢峠へは戸台パークから林道バスで', '北沢峠へは一般車両で入れません。戸台パーク（伊那市）から南アルプス林道バスに乗り換えます（2026年の北沢峠までの運行は6月1日〜11月3日）。山梨側の広河原〜北沢峠は災害復旧のため運行休止中で、広河原からは行けません。', 'yellow', 'annual', 'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_jikokuhyo.html', validFrom='2026-06-01', validTo='2026-11-03', link='伊那市 南アルプス林道バス')
setup('komagatake', 'kitazawa-roundtrip',
  [('kuroto-roundtrip', 'chikuu-komagatake-jinja', 'chikuu', None), ('kitazawa-roundtrip', 'kitazawa-toge', 'kitazawa-toge', None)],
  alerts=[KZ_ALERT])
setup('senjogatake', 'kosenjo-roundtrip',
  [('kosenjo-roundtrip', 'kitazawa-toge', 'kitazawa-toge', None), ('yabusawa-loop', 'kitazawa-toge', 'kitazawa-toge', None)],
  alerts=[copy.deepcopy(KZ_ALERT)])
setup('jonengatake', 'ichinosawa-roundtrip',
  [('ichinosawa-roundtrip', 'ichinosawa', 'ichinosawa', None), ('mitsumata-traverse', 'mitsumata', 'mitsumata', None)],
  alerts=[alert('一ノ沢登山口への林道は一般車両通行止め', '林道一ノ沢線は災害のため一般車両通行止めです（復旧工事の竣工予定は2027年1月末）。登山口の駐車場は使えません。市内の駐車場に停め、地元タクシーで通行止め箇所の手前まで行き、歩行者用通路を通って登山口まで約1.5km歩きます。', 'red', 'temporary', 'https://www.city.azumino.nagano.jp/soshiki/32/66871.html', validTo='2027-01-31', link='安曇野市の北アルプス登山情報')])
setup('yatsugatake', 'minamisawa-loop',
  [('minamisawa-loop', 'minotoguchi', 'minotoguchi', None), ('kitazawa-loop', 'minotoguchi', 'minotoguchi', None)])
setup('hiuchigatake', 'miike-roundtrip',
  [('miike-roundtrip', 'oze-miike', 'oze-miike', None), ('numayama-choei', 'numayama-toge', 'numayama-toge', None)])
setup('fuji', 'fujinomiya',
  [('fujinomiya', 'fujinomiya-5th', 'fujinomiya-5th', None), ('yoshida', 'subaru-5th', 'subaru-5th', None)],
  alerts=[alert('富士宮口は登山シーズン中マイカー規制', '2026年は7月10日9時〜9月10日18時が富士宮口のマイカー規制期間でした。期間中は水ヶ塚駐車場に停め、シャトルバス（約40分）で富士宮口五合目へ向かいます。2026年の開山期間は9月10日で終了しており、閉山中は山小屋・バスの営業がなく、登山道は冬季閉鎖されます。', 'yellow', 'annual', 'https://www.pref.shizuoka.jp/machizukuri/doro/fujisandoro/1029179.html', validFrom='2026-07-10', validTo='2026-09-10', link='静岡県 富士山マイカー規制')],
  trail_periods=[{'from': '2026-01-01', 'to': '2026-07-09', 'status': 'closed', 'label': '閉山期間（冬季閉鎖）', 'sourceUrl': 'https://www.pref.shizuoka.jp/machizukuri/doro/fujisandoro/1029179.html'},
                 {'from': '2026-09-11', 'to': '2026-12-31', 'status': 'closed', 'label': '閉山期間（冬季閉鎖）', 'sourceUrl': 'https://www.pref.shizuoka.jp/machizukuri/doro/fujisandoro/1029179.html'}])
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('trailheads', len(TH), 'accesses', len(AC), 'mountains migrated', sum(1 for m in D if m.get('dataModel') == 'ssot-v1'))
