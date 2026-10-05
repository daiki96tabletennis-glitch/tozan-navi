#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSOT移行 Phase C（2026-10-06）: P1の11山を新構造へ移行する一回限りのスクリプト。
対象: 谷川岳・木曽駒ヶ岳・唐松岳・五竜岳・火打山・日光白根山・金峰山・大菩薩嶺・乗鞍岳・槍ヶ岳・奥穂高岳
確認できない値は null ＋ needsVerification: true。
"""
import json, os, re, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def jl(n): return json.load(open(os.path.join(ROOT, 'data', n), encoding='utf-8'))
def jd(n, o): json.dump(o, open(os.path.join(ROOT, 'data', n), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
D = jl('mountains.json'); N = {m['id']: m for m in D}; TH = jl('trailheads.json'); AC = jl('accesses.json')
TODAY = '2026-10-06'
GSI = '国土地理院 地名検索（msearch.gsi.go.jp）'
BTN = '既存の地図ボタン座標（Googleプレイス）'
def th(id, name, typ, lat, lng, src, verified=True, note=None, address=None):
    TH[id] = {'id': id, 'name': name, 'type': typ, 'lat': lat, 'lng': lng, 'coordSource': src,
              'lastVerified': TODAY, 'needsVerification': not verified, 'address': address}
    if note: TH[id]['note'] = note
def op(statusType, mode, validFrom=None, validTo=None, reservation=None, note=None, year=2026):
    return {'statusType': statusType, 'mode': mode, 'validFrom': validFrom, 'validTo': validTo,
            'seasonYear': year, 'reservation': reservation, 'note': note}
def take(mid, aid, name, th_id, **kw):
    m = N[mid]
    a = {'id': aid, 'name': name, 'trailheadId': th_id, 'mapTargetId': kw.pop('mapTargetId', th_id),
         'trainRoutes': copy.deepcopy(m.get('trainRoutes')),
         'fares': {'shinjuku': m.get('fareShinjuku'), 'omiya': m.get('fareOmiya'), 'yokohama': m.get('fareYokohama')},
         'trainTimes': {'shinjuku': m.get('trainTimeShinjuku'), 'omiya': m.get('trainTimeOmiya'), 'yokohama': m.get('trainTimeYokohama')},
         'transfers': {'shinjuku': m.get('transfersShinjuku'), 'omiya': m.get('transfersOmiya'), 'yokohama': m.get('transfersYokohama')},
         'busLinks': m.get('busLinks'), 'busScheduleLinks': m.get('busScheduleLinks'),
         'car': kw.pop('car', None), 'operation': kw.pop('operation', None), 'sourceUrl': kw.pop('sourceUrl', None),
         'lastVerified': TODAY, 'needsVerification': kw.pop('needsVerification', False)}
    a.update(kw); AC[aid] = a; return a
def empty(aid, name, th_id, note, **kw):
    a = {'id': aid, 'name': name, 'trailheadId': th_id, 'mapTargetId': kw.pop('mapTargetId', th_id), 'trainRoutes': None,
         'fares': None, 'trainTimes': None, 'transfers': None, 'busLinks': None, 'busScheduleLinks': None,
         'car': kw.pop('car', None), 'operation': kw.pop('operation', None), 'sourceUrl': kw.pop('sourceUrl', None),
         'lastVerified': TODAY, 'needsVerification': True, 'note': note}
    a.update(kw); AC[aid] = a; return a
def L(st, icon, line, d): return {'station': st, 'method': {'icon': icon, 'line': line}, 'durationMin': d, 'fareYen': None}
GEAR = {'s-ok': 'normal', 's-gear': 'snow_caution', 's-hard': 'winter'}
def alert(title, text, level, statusType, src, validFrom=None, validTo=None, link=None):
    return {'title': title, 'text': text, 'level': level, 'statusType': statusType, 'validFrom': validFrom, 'validTo': validTo,
            'sourceUrl': src, 'linkText': link or '公式情報', 'lastVerified': TODAY}
def setup(mid, rep, route_defs, alerts=None):
    m = N[mid]
    assert len(route_defs) == len(m['routes']), mid
    for r, (rid, thid, acid) in zip(m['routes'], route_defs):
        assert thid in TH and acid in AC, (mid, thid, acid)
        r['id'] = rid; r['trailheadId'] = thid; r['accessId'] = acid
    m['representativeRouteId'] = rep
    if not (m.get('conditions') or {}).get('gearMonthly'):
        m['conditions'] = {'gearMonthly': [GEAR[c] for c in m['seasonCalendar']], 'trailPeriods': [],
                           'gearSource': '旧シーズンカレンダーから変換（アイゼン本数の断定はやめ、3段階に読み替え）'}
    m['alerts'] = alerts or []
    m['dataModel'] = 'ssot-v1'; m['mountainUpdated'] = TODAY
def parking(mid): return N[mid].get('parking')
PK = {i: parking(i) for i in ['tanigawa', 'kisokoma', 'karamatsu', 'goryudake', 'hiuchi', 'nikko_shirane', 'kinpusan', 'okutama', 'norikura', 'yari']}

# ── 谷川岳 ──
th('tenjindaira', '天神平（ロープウェイ山頂駅）', 'trailhead', 36.82059, 138.94953, GSI + '「天神平駅」')
th('tanigawadake-joch', '谷川岳ヨッホ by 星野リゾート（ロープウェイ乗り場・旧谷川岳ロープウェイ）', 'accessHub', 36.8363931, 138.9619534, BTN, False, address='群馬県利根郡みなかみ町湯檜曽')
th('nishikuro-tozanguchi', '西黒尾根登山口', 'trailhead', None, None, None, False, '座標未確認')
JOCH_OP = op('annual', 'seasonal', '2026-04-18', '2026-11-15', None, '谷川岳ヨッホ（ロープウェイ）の2026年グリーンシーズン営業期間（予定）')
if 'doai' not in AC:  # 既存の土合駅ルートは別アクセスとして保持
    a = take('tanigawa', 'doai', '土合駅から谷川岳ヨッホへ（JR上越線）', 'tenjindaira', mapTargetId='tanigawadake-joch',
             car={'parking': PK['tanigawa'], 'restriction': None}, operation=JOCH_OP)
    for r in a['trainRoutes']['routes'].values():
        for l in r['legs']:
            l['station'] = l['station'].replace('谷川岳ロープウェイ乗り場', '谷川岳ヨッホ（ロープウェイ乗り場）')
    a['trainRoutes']['note'] = (a['trainRoutes'].get('note') or '').replace('谷川岳ロープウェイ土合口駅', '谷川岳ヨッホ（ロープウェイ乗り場）')
    a['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ ロープウェイは季節営業（2026年は4/18〜11/15）'}
tail = [L('上毛高原駅', 'bus', '関越交通バス「水上線」', 45), L('谷川岳ヨッホ（ロープウェイ乗り場）', 'ropeway', 'ロープウェイ', 15), {'station': '天神平駅'}]
AC['tanigawadake-joch'] = {
    'id': 'tanigawadake-joch', 'name': '谷川岳ヨッホ（ロープウェイ）へのアクセス（上毛高原駅からバス）', 'trailheadId': 'tenjindaira', 'mapTargetId': 'tanigawadake-joch',
    'trainRoutes': {'badge': {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ ロープウェイは季節営業（2026年は4/18〜11/15）'},
        'lineName': '上越新幹線・関越交通バス「水上線」',
        'routes': {'shinjuku': {'legs': [L('新宿駅', 'train', 'JR湘南新宿ライン・上越新幹線とき（大宮乗換）', 83)] + copy.deepcopy(tail)},
                   'omiya': {'legs': [L('大宮駅', 'train', '上越新幹線とき', 38)] + copy.deepcopy(tail)},
                   'yokohama': {'legs': [L('横浜駅', 'train', 'JR上野東京ライン・上越新幹線とき（東京乗換）', 111)] + copy.deepcopy(tail)}},
        'note': '💡 上毛高原駅から関越交通バス「水上線」で谷川岳ヨッホ（旧谷川岳ロープウェイ）まで約45分・1,600円。ロープウェイで天神平まで約15分（運賃は別途）。新幹線は自由席の料金。JR上越線の土合駅から歩く経路もある（下りホームから地上まで462段の階段、駅からロープウェイ乗り場まで徒歩約20分）。',
        'summaryNote': '※運賃にロープウェイ代は含みません', 'links': (N['tanigawa'].get('trainRoutes') or {}).get('links')},
    'fares': {'shinjuku': 6990, 'omiya': 6660, 'yokohama': 7970}, 'trainTimes': {'shinjuku': 143, 'omiya': 98, 'yokohama': 171},
    'transfers': None, 'busLinks': N['tanigawa'].get('busLinks'), 'busScheduleLinks': N['tanigawa'].get('busScheduleLinks'),
    'car': {'parking': PK['tanigawa'], 'restriction': None}, 'operation': JOCH_OP, 'altAccessIds': ['doai'],
    'sourceUrl': 'https://tanigawadake-joch.com/', 'lastVerified': TODAY, 'needsVerification': False,
    'fareSource': 'Yahoo!路線情報（新宿・大宮・横浜→上毛高原：5,390/5,060/6,370円）＋関越交通バス1,600円'}
empty('nishikuro', '西黒尾根登山口へのアクセス', 'nishikuro-tozanguchi', '谷川岳ヨッホ（ロープウェイ乗り場）までは「谷川岳ヨッホへのアクセス」と同じ。乗り場から登山口までの徒歩時間は未確認', mapTargetId='tanigawadake-joch', viaAccessId='tanigawadake-joch', car={'parking': PK['tanigawa'], 'restriction': None})
setup('tanigawa', 'tenjin-roundtrip', [('tenjin-roundtrip', 'tenjindaira', 'tanigawadake-joch'), ('nishikuro-roundtrip', 'nishikuro-tozanguchi', 'nishikuro')])

# ── 木曽駒ヶ岳 ──
th('senjojiki', '千畳敷（ロープウェイ山頂駅）', 'trailhead', 35.77744, 137.81344, GSI + '「千畳敷駅」')
th('suganodai', '菅の台バスセンター（駐車場・バス乗り場）', 'accessHub', 35.7432283, 137.8912366, BTN, False, address='長野県駒ヶ根市赤穂黒川平')
a = take('kisokoma', 'senjojiki', '千畳敷へのアクセス（菅の台からバス・ロープウェイ）', 'senjojiki', mapTargetId='suganodai',
    car={'parking': PK['kisokoma'], 'restriction': 'しらび平（ロープウェイ乗り場）へは一般車両で入れない。菅の台バスセンターで路線バスに乗り換える'},
    operation=op('annual', 'year', None, None, None, 'バス・ロープウェイは通年運行（夏ダイヤ2026/4/10〜11/30、それ以外は冬ダイヤ。点検運休あり）'),
    sourceUrl='https://www.chuo-alps.com/')
a['trainRoutes']['badge'] = {'type': 'year', 'style': None, 'icon': 'check', 'label': '通年運行（冬ダイヤ・点検運休あり）'}
setup('kisokoma', 'senjojiki-roundtrip', [('senjojiki-roundtrip', 'senjojiki', 'senjojiki'), ('nogaike-loop', 'senjojiki', 'senjojiki')],
  alerts=[alert('しらび平へはマイカーで入れません', '木曽駒ヶ岳のロープウェイ乗り場（しらび平）は一般車両進入不可です。菅の台バスセンターに駐車し、路線バスとロープウェイを乗り継いで千畳敷へ上がります。繁忙期は待ち時間が長くなります。', 'yellow', 'permanent', 'https://www.chuo-alps.com/', link='中央アルプス駒ヶ岳ロープウェイ')])

# ── 唐松岳 ──
th('happoike-sanso', '八方池山荘（リフト終点）', 'trailhead', None, None, None, False, '座標未確認')
th('happo-station', '八方駅（八方アルペンライン乗り場）', 'accessHub', 36.70168, 137.83715, GSI, address='長野県北安曇郡白馬村北城')
a = take('karamatsu', 'happo', '八方アルペンライン（ゴンドラ・リフト）へのアクセス', 'happoike-sanso', mapTargetId='happo-station',
    car={'parking': PK['karamatsu'], 'restriction': None},
    operation=op('annual', 'seasonal', '2026-06-06', '2026-11-03', None, '八方アルペンラインの2026年グリーンシーズン営業期間（5/30・5/31も営業）'),
    sourceUrl='https://www.happo-one.jp/news/38573/')
a['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ ゴンドラ・リフトは季節営業（2026年は6/6〜11/3）'}
setup('karamatsu', 'happo-roundtrip', [('happo-roundtrip', 'happoike-sanso', 'happo'), ('kaerazu-traverse', 'happoike-sanso', 'happo')])

# ── 五竜岳 ──
th('alps-daira', 'アルプス平（テレキャビン山頂駅）', 'trailhead', None, None, None, False, '座標未確認')
th('escal-plaza', 'エスカルプラザ（白馬五竜テレキャビン乗り場）', 'accessHub', 36.66368, 137.8350899, BTN, False, address='長野県北安曇郡白馬村神城')
a = take('goryudake', 'goryu-telecabin', '白馬五竜テレキャビンへのアクセス', 'alps-daira', mapTargetId='escal-plaza',
    car={'parking': PK['goryudake'], 'restriction': None},
    operation=op('annual', 'seasonal', '2026-06-20', '2026-10-18', None, 'テレキャビンの2026年グリーンシーズン通常営業期間（6/6・7・13・14は先行営業）'),
    sourceUrl='https://www.hakubaescal.com/shokubutsuen/gondola/cal/')
a['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ テレキャビンは季節営業（2026年は6/20〜10/18）'}
setup('goryudake', 'tomi-roundtrip', [('tomi-roundtrip', 'alps-daira', 'goryu-telecabin')])

# ── 火打山 ──
th('sasagamine', '笹ヶ峰登山口', 'trailhead', 36.8687215, 138.0787663, BTN + '／国土地理院「休暇村妙高笹ヶ峰キャンプ場」付近で照合', address='新潟県妙高市杉野沢')
a = take('hiuchi', 'sasagamine', '笹ヶ峰へのアクセス', 'sasagamine', car={'parking': PK['hiuchi'], 'restriction': None},
    operation=op('annual', 'seasonal', '2026-07-11', '2026-10-25', None, '笹ヶ峰直行バスの2026年の運行期間（観光サイト掲載値。頸南バスの公式時刻表では未確認。運賃も要確認）'),
    sourceUrl='http://niigata-kankou.or.jp/spot/detail_31014.html', needsVerification=True)
a['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ バスは季節運行（2026年は7/11〜10/25）'}
a['trainRoutes']['note'] = '💡 妙高高原駅〜笹ヶ峰の頸南バス「笹ヶ峰直行バス」は季節運行（2026年は7月11日〜10月25日）。運行日により便数が異なるため公式サイトでの確認が必須。バスの運行が終わっても登山道は歩ける（マイカーまたはタクシー）。笹ヶ峰から火打山山頂までは約4時間30分。高谷池ヒュッテでの1泊もおすすめ。'
a['trainRoutes']['summaryNote'] = '※バスの運行終了後も登山道は利用できます（公共交通なし）'
for r in a['trainRoutes']['routes'].values(): r['legs'][-1]['station'] = '笹ヶ峰'
setup('hiuchi', 'sasagamine-roundtrip', [('sasagamine-roundtrip', 'sasagamine', 'sasagamine')])

# ── 日光白根山 ──
th('marunuma-sancho', '丸沼高原ロープウェイ山頂駅', 'trailhead', None, None, None, False, '座標未確認')
th('marunuma-kogen', '丸沼高原（日光白根山ロープウェイ乗り場）', 'accessHub', 36.814633, 139.3300313, BTN, False, address='群馬県利根郡片品村東小川')
th('suganuma-tozanguchi', '菅沼登山口', 'trailhead', None, None, None, False, '座標未確認')
a = take('nikko_shirane', 'marunuma-ropeway', '丸沼高原（日光白根山ロープウェイ）へのアクセス', 'marunuma-sancho', mapTargetId='marunuma-kogen',
    car={'parking': PK['nikko_shirane'], 'restriction': None},
    operation=op('annual', 'seasonal', '2026-06-04', '2026-11-08', None, 'ロープウェイの2026年グリーンシーズン営業期間（天候・点検で運休あり）。山の登山適期とは別'),
    sourceUrl='https://www.marunuma.jp/green/2399/')
a['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ ロープウェイは季節営業（2026年は6/4〜11/8）'}
a['trainRoutes']['note'] = '💡 沼田駅から丸沼高原へは関越交通バスを鎌田で乗り継ぐ必要があり、本数が限られる。ロープウェイの2026年グリーンシーズン営業は6月4日〜11月8日（天候・点検で運休あり）。'
empty('suganuma', '菅沼登山口へのアクセス', 'suganuma-tozanguchi', '電車・バスの経路と運賃は未作成（要確認）')
setup('nikko_shirane', 'ropeway-roundtrip', [('ropeway-roundtrip', 'marunuma-sancho', 'marunuma-ropeway'), ('suganuma-roundtrip', 'suganuma-tozanguchi', 'suganuma')])

# ── 金峰山 ──
th('odarumi-toge', '大弛峠', 'trailhead', 35.87313, 138.66306, GSI, address='山梨県山梨市牧丘町')
th('mawarimedaira', '廻り目平', 'trailhead', None, None, None, False, '座標未確認')
a = take('kinpusan', 'odarumi', '大弛峠へのアクセス（塩山駅から予約制バス）', 'odarumi-toge', car={'parking': PK['kinpusan'], 'restriction': None},
    operation=op('annual', 'seasonal', '2026-05-30', '2026-11-08', '土・日・祝日のみ運行。WEB予約のみ（現金払い）', '栄和交通の大弛峠線（ツアー形式）の2026年の運行期間。道路状況で早く終わることがある'),
    sourceUrl='https://eiwa-kotsu.jp/oodarumi.html')
a['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ 土日祝のみ・要WEB予約（2026年は5/30〜11/8）'}
a['trainRoutes']['summaryNote'] = '※バスはWEB予約のみ。2026年は5月30日〜11月8日の土・日・祝日に運行（塩山駅北口〜大弛峠 片道3,000円）'
empty('mawarimedaira', '廻り目平へのアクセス', 'mawarimedaira', '電車・バスの経路と運賃は未作成（要確認）')
setup('kinpusan', 'odarumi-roundtrip', [('odarumi-roundtrip', 'odarumi-toge', 'odarumi'), ('mawarimedaira-roundtrip', 'mawarimedaira', 'mawarimedaira')])

# ── 大菩薩嶺 ──
th('kamihikawa-toge', '上日川峠', 'trailhead', 35.73168, 138.83236, GSI, address='山梨県甲州市塩山上萩原')
th('saketsuishi', '裂石（大菩薩峠登山口）', 'trailhead', 35.73844, 138.80139, GSI + '「裂石」')
a = take('okutama', 'kamihikawa', '上日川峠へのアクセス（甲斐大和駅からバス）', 'kamihikawa-toge', car={'parking': PK['okutama'], 'restriction': '上日川峠への道路は冬季閉鎖'},
    operation=op('annual', 'seasonal', '2026-04-18', '2026-12-13', None, '栄和交通「大菩薩上日川峠線」の2026年の運行期間（土日祝中心・一部平日）'),
    sourceUrl='https://eiwa-kotsu.jp/', needsVerification=True)
a['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ 土日祝中心の季節運行（2026年は4/18〜12/13）'}
for r in a['trainRoutes']['routes'].values(): r['legs'][-1]['station'] = '上日川峠'
empty('saketsuishi', '裂石（大菩薩峠登山口）へのアクセス', 'saketsuishi', '電車・バスの経路と運賃は未作成（要確認）')
setup('okutama', 'kamihikawa-loop', [('kamihikawa-loop', 'kamihikawa-toge', 'kamihikawa'), ('saketsuishi-route', 'saketsuishi', 'saketsuishi')])

# ── 乗鞍岳 ──
th('tatamidaira', '畳平', 'trailhead', 36.1247548, 137.5537662, BTN, False, address='岐阜県高山市丹生川町')
th('norikura-kogen', '乗鞍高原観光センター（シャトルバス乗り場）', 'accessHub', None, None, None, False, '座標未確認。地図は名称検索で開く')
a = take('norikura', 'tatamidaira', '畳平へのアクセス（乗鞍高原からシャトルバス）', 'tatamidaira', mapTargetId='norikura-kogen',
    car={'parking': '乗鞍高原観光センター駐車場（長野側）／ほおのき平駐車場（岐阜側）', 'restriction': '畳平へは一般車両で入れない。乗鞍高原（長野側）またはほおのき平（岐阜側）でシャトルバスに乗り換える'},
    operation=op('annual', 'seasonal', '2026-07-01', '2026-10-31', '予約優先制（空席があれば予約なしで乗車可）。往復とも事前予約を推奨', '乗鞍高原〜畳平シャトルバスの2026年の運行期間。運賃は公式の運賃表で要確認'),
    sourceUrl='https://www.alpico.co.jp/traffic/local/kamikochi/echoline/', needsVerification=True)
a['trainRoutes']['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ 季節運行・予約優先制（2026年は7/1〜10/31）'}
a['trainRoutes']['summaryNote'] = '※畳平シャトルバスは2026年は7月1日〜10月31日運行。予約優先制で、空席があれば予約なしでも乗車できます（往復とも事前予約を推奨）'
a['trainRoutes']['note'] = re.sub(r'乗鞍高原〜畳平のシャトルバスは[^。]*。帰りの畳平発も[^。]*。', '乗鞍高原〜畳平のシャトルバスは予約優先制（乗車日の1か月前から予約可）で約55分。空席があれば予約なしでも乗車できるが、満席の日があるため往復とも事前予約が安全。', a['trainRoutes'].get('note') or '')
for r in a['trainRoutes']['routes'].values():
    r['legs'][-1]['station'] = '畳平'
    for l in r['legs']:
        if l.get('method') and '畳平シャトルバス' in l['method']['line']: l['method']['line'] = '畳平シャトルバス（予約優先制）'
setup('norikura', 'tatamidaira-roundtrip', [('tatamidaira-roundtrip', 'tatamidaira', 'tatamidaira'), ('katanokoya-roundtrip', 'tatamidaira', 'tatamidaira')],
  alerts=[alert('畳平へはマイカーで入れません', '乗鞍岳の畳平（2,702m）へは一般車両の乗り入れが禁止されています。乗鞍高原（長野側）またはほおのき平（岐阜側）からシャトルバスを利用します。2026年の乗鞍高原〜畳平シャトルバスは7月1日〜10月31日の運行で、予約優先制です。', 'yellow', 'annual', 'https://www.alpico.co.jp/traffic/local/kamikochi/echoline/', validFrom='2026-07-01', validTo='2026-10-31', link='アルピコ交通')])

# ── 上高地（槍ヶ岳・奥穂高岳で共有）──
th('kamikochi-bt', '上高地バスターミナル', 'trailhead', 36.2487537, 137.6380649, BTN, False, address='長野県松本市安曇')
th('sawando', '沢渡（さわんど）駐車場', 'accessHub', None, None, None, False, '座標未確認。地図は名称検索で開く')
th('shinhotaka-onsen', '新穂高温泉', 'trailhead', 36.28588, 137.57570, GSI + '「新穂高温泉駅」')
a = take('yari', 'kamikochi', '上高地へのアクセス', 'kamikochi-bt', mapTargetId='sawando',
    car={'parking': PK['yari'], 'restriction': '上高地へは一般車両で入れない（通年マイカー規制）。沢渡またはあかんだな駐車場でシャトルバス・タクシーに乗り換える'},
    operation=op('annual', 'seasonal', '2026-04-17', '2026-11-15', '予約優先制（往路・復路とも。乗車日の1か月前から予約可）', '松本〜新島々〜上高地の路線バスの2026年の運行期間'),
    sourceUrl='https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/')
tr = a['trainRoutes']
tr['badge'] = {'type': 'seasonal', 'style': None, 'icon': 'check', 'label': '⚠️ 季節運行・予約優先制（2026年は4/17〜11/15）'}
ktail = [L('松本駅', 'train', '松本電鉄上高地線', 30), L('新島々駅', 'bus', 'アルピコ交通バス（予約優先制）', 65), {'station': '上高地バスターミナル'}]
tr['routes'] = {'shinjuku': {'legs': [L('新宿駅', 'train', 'JR特急あずさ', 150)] + copy.deepcopy(ktail)},
                'omiya': {'legs': [L('大宮駅', 'train', 'JR埼京線・武蔵野線・中央線（立川乗換）', 55), L('立川駅', 'train', 'JR特急あずさ', 140)] + copy.deepcopy(ktail)},
                'yokohama': {'legs': [L('横浜駅', 'train', 'JR横浜線', 50), L('八王子駅', 'train', 'JR特急あずさ', 151)] + copy.deepcopy(ktail)}}
tr['note'] = ('💡 新島々駅〜上高地のアルピコ交通バスは約1時間。2026年は予約優先制で、往路・復路とも乗車日の1か月前から予約できる（空席があれば予約なしでも乗車可）。'
              '松本電鉄上高地線（松本〜新島々）は予約不要だが交通系ICカードは使えない。上高地は通年マイカー規制のため一般車両は入れない。'
              'バスタ新宿発の夜行「さわやか信州号」なら上高地に早朝到着でき乗り換えも不要。大宮は立川、横浜は八王子で特急あずさに乗ると安い。')
tr['summaryNote'] = '※松本〜新島々 710円＋新島々〜上高地 3,100円（2026年）'
a['fares'] = {'shinjuku': 10540, 'omiya': 10230, 'yokohama': 10230}
a['trainTimes'] = {'shinjuku': 245, 'omiya': 290, 'yokohama': 296}
a['fareSource'] = 'JR特急あずさ 新宿〜松本6,730円（JR公式料金表）／大宮・横浜〜松本6,420円（Yahoo!路線情報）＋上高地線710円＋バス3,100円'
empty('shinhotaka', '新穂高温泉へのアクセス', 'shinhotaka-onsen', '電車・バスの経路と運賃は未作成（要確認）。バスタ新宿から新穂高温泉行きの高速バスがある（笠ヶ岳のアクセスを参照）')
KA = alert('上高地へはマイカーで入れません', '上高地は通年マイカー規制です。沢渡（さわんど）またはあかんだな駐車場に停め、シャトルバス・タクシーに乗り換えます。松本〜新島々〜上高地の路線バスは2026年は4月17日〜11月15日の運行で、往路・復路とも予約優先制です。', 'yellow', 'annual', 'https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/', validFrom='2026-04-17', validTo='2026-11-15', link='アルピコ交通')
setup('yari', 'yarisawa-roundtrip', [('yarisawa-roundtrip', 'kamikochi-bt', 'kamikochi'), ('hidazawa-roundtrip', 'shinhotaka-onsen', 'shinhotaka')], alerts=[KA])
setup('hotaka', 'karasawa-route', [('karasawa-route', 'kamikochi-bt', 'kamikochi'), ('shiradashi-route', 'shinhotaka-onsen', 'shinhotaka')], alerts=[copy.deepcopy(KA)])

jd('trailheads.json', TH); jd('accesses.json', AC); jd('mountains.json', D)
print('trailheads', len(TH), 'accesses', len(AC), 'migrated', sum(1 for m in D if m.get('dataModel') == 'ssot-v1'))
