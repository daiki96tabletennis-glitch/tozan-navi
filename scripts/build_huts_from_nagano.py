#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋まとめ（β）のデータ data/huts.json を、長野県「山小屋情報ポータルサイト」から作る。

出典：長野県 山小屋情報ポータルサイト（北アルプス／南アルプス／中央アルプス／八ヶ岳／その他）
      https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/sotaikyo/yamagoya/yamagoya.html
載っている項目：山小屋名・公式サイト・位置・連絡先・開設（営業期間、予約の区分、予約方法）
載っていない項目：規模（収容人数）。data/huts.json の capacity は、公式サイトで確認できたものだけを入れる（このスクリプトは既存の値を残す）。

どの小屋をどの山に結び付けるか（HUT_MOUNTAINS）は手で決めている。サイトに載せている山に関係する、有人の小屋だけを対象にする。
使い方：python3 scripts/build_huts_from_nagano.py   （出典ページを取得して data/huts.json を作り直す）
"""
import datetime, hashlib, html, json, os, re, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/sotaikyo/yamagoya/'
PAGES = [('yamagoya_kitaalps.html', '北アルプス'), ('yamagoya_minamialps.html', '南アルプス'), ('yamagoya_cyuualps.html', '中央アルプス'),
         ('yamagoya_yatsugatake.html', '八ヶ岳'), ('yamagoya_sonota.html', 'その他')]
# 山小屋名（出典の表記）→ 関係する山のID。
# ここに書くのは、サイトに載せているルート（mountains.json の routes）の登山口・途中・山頂にある小屋だけ。
# 別のルートや縦走で使う小屋は、下の HUT_OTHER に書く（2026-10-10 に全78軒をルートと突き合わせて見直し）
HUT_MOUNTAINS = {
    '槍ヶ岳山荘': ['yari'], 'ヒュッテ大槍': ['yari'], '殺生小屋': ['yari'], '槍沢ロッヂ': ['yari'],
    '穂高岳山荘': ['hotaka'], '涸沢小屋': ['hotaka'], '涸沢ヒュッテ': ['hotaka'], '岳沢小屋': [],
    '横尾山荘': ['yari', 'hotaka'], '徳沢ロッヂ': ['chogatake'], '氷壁の宿 徳澤園': ['chogatake'],
    '蝶ヶ岳ヒュッテ': ['chogatake'], '大滝山荘': [], '常念小屋': ['jonengatake'], '焼岳小屋': ['yakedake'],
    '燕山荘': ['otenshoudake'], '大天荘': ['otenshoudake'], '大天井ヒュッテ': [], '中房温泉': ['otenshoudake', 'arikayama'], '有明荘': ['arikayama'],
    '餓鬼岳小屋': ['gakedake'], '七倉山荘': ['eboshidake_kita', 'noguchigoro'], '烏帽子小屋': ['eboshidake_kita'], '野口五郎小屋': ['noguchigoro'],
    '白馬山荘': ['shirouma'], '村営白馬岳頂上宿舎': ['shirouma'], '白馬大池山荘': ['shirouma'], '猿倉荘': ['shirouma'], '栂池山荘': ['shirouma'], '栂池ヒュッテ': ['shirouma'],
    '唐松岳頂上山荘': ['karamatsu'], '村営八方池山荘': ['karamatsu'], '村営天狗山荘': ['karamatsu'], '五竜山荘': ['goryudake'], 'キレット小屋': [],
    '冷池山荘': ['kashimayari'], '種池山荘': ['kashimayari'], '針ノ木小屋': ['harinokidake'], '大沢小屋': ['harinokidake'],
    '肩ノ小屋': ['norikura'], '位ヶ原山荘': [],
    '北沢峠 こもれび山荘': ['komagatake', 'senjogatake'], '大平山荘': ['komagatake', 'senjogatake'], '仙丈小屋': ['senjogatake'], '馬の背ヒュッテ': ['senjogatake'],
    '塩見小屋': ['shiomidake'], '三伏峠小屋': ['shiomidake'], '聖光小屋': ['hijiridade', 'terkari'], '県営光岳小屋': ['terkari'],
    '駒ヶ岳頂上山荘': ['kisokoma'], '宝剣山荘': ['kisokoma'], '天狗荘': ['kisokoma'], '西駒山荘': [],
    '木曽殿山荘': [], '空木駒峰ヒュッテ': ['utsugi'], '越百小屋': ['minamikomagatake'],
    '蓼科山頂ヒュッテ': ['keirisan'], '蓼科山荘': ['keirisan'],
    '赤岳頂上山荘': ['yatsugatake'], '赤岳天望荘': ['yatsugatake'], '行者小屋': ['yatsugatake'], '赤岳鉱泉': ['yatsugatake'], '赤岳山荘': ['yatsugatake'],
    '美濃戸山荘': ['yatsugatake'], '硫黄岳山荘': [],
    '苗場山頂ヒュッテ－自然体験交流センター': ['naeba'], '甲武信小屋': ['kobushigatake'], '十文字小屋': [], '金峰山小屋': ['kinpusan'],
    '二ノ池山荘': ['ontakesan'], '二の池ヒュッテ': ['ontakesan'], '女人堂（金剛堂）': [], '石室山荘': [], '七合目行場山荘': [],
    '天狗温泉浅間山荘': [], '鷲が峰ひゅって': ['kirigamine'], 'ヒュッテみさやま': ['kirigamine'], '八島山荘': ['kirigamine'],
    '美ヶ原高原ホテル・山本小屋': ['utsukushigahara'], '山本小屋ふる里館': ['utsukushigahara'], '萬岳荘': [],
}
# 別のルート・縦走で使う小屋：山小屋名 → [(山のID, どういう関係か)]
HUT_OTHER = {
    '岳沢小屋': [('hotaka', '岳沢・前穂高岳経由のルート')],
    '横尾山荘': [('chogatake', '横尾から登るルート')],
    '大滝山荘': [('chogatake', '大滝山・徳本峠への縦走')],
    '大天井ヒュッテ': [('otenshoudake', '山頂の西側。槍ヶ岳への縦走路')],
    'キレット小屋': [('goryudake', '鹿島槍ヶ岳との縦走（八峰キレット）'), ('kashimayari', '五竜岳との縦走（八峰キレット）')],
    '位ヶ原山荘': [('norikura', '乗鞍高原側から歩いて登るルート')],
    '西駒山荘': [('kisokoma', '桂小場からのルート')],
    '木曽殿山荘': [('utsugi', '木曽駒ヶ岳方面からの縦走')],
    '硫黄岳山荘': [('yatsugatake', '硫黄岳・横岳からの縦走')],
    '十文字小屋': [('kobushigatake', '十文字峠経由のルート')],
    '女人堂（金剛堂）': [('ontakesan', '黒沢口のルート')], '石室山荘': [('ontakesan', '黒沢口のルート')], '七合目行場山荘': [('ontakesan', '黒沢口のルート')],
    '天狗温泉浅間山荘': [('asama', '火山館コース（前掛山方面）の登山口')],
    '萬岳荘': [('enasan', '神坂峠の近く（富士見台高原）。前泊・後泊に使える')],
}
# 八ヶ岳のページにも「キレット小屋」（赤岳・権現岳の間）があるので、北アルプスのものだけを使う
ONLY_REGION = {'キレット小屋': '北アルプス'}


def fetch(page):
    req = urllib.request.Request(BASE + page, headers={'User-Agent': 'Mozilla/5.0 (compatible; yamatch-huts)'})
    return urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')


def parse(page, region):
    s = fetch(page)
    upd = re.search(r'更新日：(\d{4})年(\d{1,2})月(\d{1,2})日', s)
    updated = '%s-%02d-%02d' % (upd.group(1), int(upd.group(2)), int(upd.group(3))) if upd else None
    out = []
    for tb in re.findall(r'<table\b.*?</table>', s, flags=re.S):
        rows = [html.unescape(re.sub(r'<(?!a\b|/a>)[^>]+>', '', r)).replace('\xa0', ' ').strip() for r in re.findall(r'<td[^>]*>(.*?)</td>', tb, flags=re.S)]
        if not rows:
            continue
        a = re.search(r'<a href="([^"]*)"', rows[0])
        d = {'name': re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', rows[0])).strip(), 'url': a.group(1) if a else None,
             'region': region, 'sourceUrl': BASE + page, 'sourceUpdated': updated}
        for r in rows[1:]:
            t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', r)).strip()
            for k, key in (('位置', 'location'), ('連絡先', 'tel'), ('現地', 'telSite'), ('開設', 'openText')):
                if t.startswith(k):
                    d[key] = re.sub(r'^%s\s*[：:；;]\s*' % k, '', t)
        out.append(d)
    return out


# 予約の開始と方法：出典の「開設」欄を読んで、手で書き写したもの（機械的な読み取りはしない）。
# 出典に書かれていない項目は None（ページでは「公式サイトで確認」と出す）。日付は2026年シーズンの実績。
# 値は（予約の開始, 予約方法のリスト）
M1 = '宿泊日の1か月前から'
HUT_BOOKING = {
    '槍ヶ岳山荘': (M1, ['Web']), 'ヒュッテ大槍': ('5月19日から（2026年）', None), '殺生小屋': (M1, None), '槍沢ロッヂ': (M1, ['Web']),
    '穂高岳山荘': (M1 + '（4/27〜5/20の宿泊分は4月20日から電話のみ）', ['電話']), '涸沢小屋': (M1 + '（4/27〜5/25の宿泊分は一括して4月25日から）', ['電話']),
    '涸沢ヒュッテ': (M1 + '（5名以上は電話のみで、前月同日の朝8:00から）', ['Web（やまたん・4名まで）', '電話']),
    '横尾山荘': (M1 + '（電話は前月同日の朝7:00から。Webは8名まで）', ['Web（やまたん）', '電話']), '徳沢ロッヂ': ('1月28日 9:00から（2026年）', ['Web（完全予約制）']), '氷壁の宿 徳澤園': (None, None),
    '岳沢小屋': (M1, ['Web']), '焼岳小屋': (M1, ['電話', 'FAX']), '有明荘': (None, None), '中房温泉': ('Webは宿泊日の90日前 0:00から（出典の記載は「2か月前予約制」）', ['Web（やまたん ほか）', '電話']),
    '燕山荘': ('3月18日から（2026年）', None), '餓鬼岳小屋': (None, None), '大天荘': ('予約制（空きがあれば当日も可。開始日の記載なし）', ['Web']), '大天井ヒュッテ': (M1, None),
    '常念小屋': (M1, None), '蝶ヶ岳ヒュッテ': ('Webは宿泊日の6週前の同じ曜日 0:00から（電話は日程が異なる。出典の記載は「1か月前予約制」）', ['Web（やまたん）', '電話']), '大滝山荘': (M1, None), '七倉山荘': (None, None), '烏帽子小屋': (M1, None),
    '野口五郎小屋': (None, ['電話（Web予約は不可）']), '栂池ヒュッテ': (None, ['Web']), '栂池山荘': (None, None),
    '白馬大池山荘': ('5月20日 7:00から（2026年）', ['Web']), '猿倉荘': ('5月20日 7:00から（2026年）', ['Web']),
    '白馬山荘': ('残雪期の宿泊分は4月1日 9:00から、夏季（6/20〜）の宿泊分は5月20日 7:00から（2026年）', ['Web']), '村営白馬岳頂上宿舎': ('5月8日 9:00から（2026年）', None),
    '唐松岳頂上山荘': ('宿泊日の120日前から（Web）', ['Web']), '村営八方池山荘': ('随時受付', None), '村営天狗山荘': ('5月8日 9:00から（2026年）', None), '五竜山荘': ('残雪期の宿泊分は4月1日 9:00から、夏季（6/20〜）の宿泊分は5月20日 7:00から（2026年）', ['Web']), 'キレット小屋': ('5月20日 7:00から（2026年）', ['Web']),
    '冷池山荘': (None, ['Web', '電話（前日17時まで）']), '種池山荘': (None, ['Web', '電話（前日17時まで）']), '針ノ木小屋': (None, ['Web', '電話']), '大沢小屋': (None, None), '肩ノ小屋': (None, None),
    '位ヶ原山荘': ('宿泊日の3か月前から', ['Web']),
    '北沢峠 こもれび山荘': ('宿泊日の3か月前の同じ日 0:00から', ['Web（やまたん）', '電話']), '大平山荘': (None, ['電話のみ']), '仙丈小屋': ('宿泊日の3か月前の同じ日から', ['Web（やまたん）', '電話']), '馬の背ヒュッテ': (None, ['Web（Yamatan）', '電話']),
    '塩見小屋': ('4月1日から（Web・やまたん。時刻は公式サイトで確認）', ['Web（やまたん）', '電話']), '三伏峠小屋': ('宿泊日の21日前から（例：8月21日泊は8月1日から）', ['Web（オンライン予約）']), '聖光小屋': ('3月20日から（2026年）', ['電話（1週間前まで）']), '県営光岳小屋': ('6月22日 9:00から（2026年）', ['Webのみ']),
    '西駒山荘': ('2月20日から（2026年・Web予約）', ['Web（やまたん）', '電話']), '駒ヶ岳頂上山荘': (None, None), '宝剣山荘': (None, None), '天狗荘': (None, None),
    '木曽殿山荘': (None, None), '空木駒峰ヒュッテ': ('6月1日から（2026年）', None), '越百小屋': (None, None),
    '蓼科山頂ヒュッテ': (None, None), '蓼科山荘': (None, ['Web（やまたん）']), '硫黄岳山荘': (None, None), '赤岳頂上山荘': (None, None), '赤岳天望荘': (None, None),
    '行者小屋': (None, None), '赤岳鉱泉': (None, None), '赤岳山荘': (None, None), '美濃戸山荘': (None, None),
    '天狗温泉浅間山荘': (None, None), '苗場山頂ヒュッテ－自然体験交流センター': (None, ['電話']), '美ヶ原高原ホテル・山本小屋': (None, None), '山本小屋ふる里館': (None, None), '萬岳荘': (None, ['電話', 'メール']),
    '八島山荘': ('4/29〜5/10の宿泊分は3月29日から。5/11以降はメールフォームでも受付（宿泊の3日前〜当日は電話）', ['Web', '電話']), '鷲が峰ひゅって': ('宿泊月の前月1日 0:00から（例：7月分は6月1日）', ['Web（予約カレンダー）']), 'ヒュッテみさやま': (None, None), '十文字小屋': (None, None),
    '甲武信小屋': (None, None), '金峰山小屋': (None, None), '七合目行場山荘': (None, None), '女人堂（金剛堂）': (None, None), '石室山荘': (None, None),
    '二ノ池山荘': (None, ['電話のみ']), '二の池ヒュッテ': (None, ['公式LINE']),
}

# 規模（収容人数）：各小屋の公式サイトで確認できたものだけ（2026-10-10 確認）。値は（人数, 確認したページ）
YT = 'https://www.yamatan.net/hut/'
HUT_CAPACITY = {
    'ヒュッテ大槍': (96, 'https://www.enzanso.co.jp/hutte-ooyari'), '大天荘': (150, 'https://www.enzanso.co.jp/daitenso'),
    '白馬山荘': (800, 'https://hakubakan.com/lodge/hakubasanso/'), '針ノ木小屋': (60, 'http://www.harinoki.com/'),
    '北沢峠 こもれび山荘': (67, 'https://www.ina-city-kankou.co.jp/yamagoya/kitazawa/'), '仙丈小屋': (35, 'https://www.ina-city-kankou.co.jp/yamagoya/senjo/'),
    '西駒山荘': (28, 'https://www.ina-city-kankou.co.jp/yamagoya/nishikoma/'), '県営光岳小屋': (20, 'https://www.chillnn.com/1863f95fe2d74'),
    '空木駒峰ヒュッテ': (25, 'http://www.komaho.net/hutte/utsugi_hutte1.html'), '二ノ池山荘': (70, None),
    # 予約サイト「やまたん」の各小屋ページ（小屋が登録している定員）
    '馬の背ヒュッテ': (34, YT + 'umanosehutte'), '塩見小屋': (34, YT + 'shiomigoya'), '横尾山荘': (150, YT + 'yokoosanso'),
    '中房温泉': (150, YT + 'nakabusaonsen'), '涸沢ヒュッテ': (140, YT + 'karasawahutte'), '蓼科山荘': (20, YT + 'tateshinasanso'),
}
# 公式サイトの記載が、出典（長野県のポータル）と違っていたもの。ページに「公式サイトの記載」として添える
HUT_OFFICIAL_NOTE = {
    '常念小屋': '通常営業期間は4月27日〜11月4日',
    '苗場山頂ヒュッテ－自然体験交流センター': '営業期間は令和8年6月1日〜10月18日（予約制）',
    '二ノ池山荘': '令和8年は7月1日から10月11日まで営業',
    '唐松岳頂上山荘': '2026年の営業は10月12日までの予定',
}


def main():
    path = os.path.join(ROOT, 'data', 'huts.json')
    old = {}
    if os.path.exists(path):
        old = {h['id']: h for h in json.load(open(path, encoding='utf-8'))['huts']}
    M = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
    huts, seen = [], set()
    for page, region in PAGES:
        for d in parse(page, region):
            name = d['name']
            if name not in HUT_MOUNTAINS or ONLY_REGION.get(name, region) != region:
                continue
            seen.add(name)
            start, methods = HUT_BOOKING[name]
            text = d.get('openText') or ''
            required = bool(re.search(r'完全予約制|要予約|予約制|事前予約|予約のみ', text))
            hid = 'hut-' + hashlib.md5((region + name).encode('utf-8')).hexdigest()[:8]
            prev = old.get(hid, {})
            cap, capsrc = HUT_CAPACITY.get(name, (prev.get('capacity'), prev.get('capacitySourceUrl')))
            others = [{'id': mid, 'relation': rel} for mid, rel in HUT_OTHER.get(name, [])]
            for mid in HUT_MOUNTAINS[name] + [o['id'] for o in others]:
                assert mid in M, (name, mid)
            assert HUT_MOUNTAINS[name] or others, name
            tel = d.get('tel') or None
            if tel in ('連絡先', '同上', ''):
                tel = None
            huts.append({
                'id': hid, 'name': name, 'region': region, 'mountainIds': HUT_MOUNTAINS[name], 'otherMountains': others,
                'location': d.get('location'), 'officialUrl': d['url'], 'tel': tel,
                # openText は出典の「開設」欄の原文（営業期間・予約の区分）。ページにはそのまま出す
                'openText': d.get('openText'), 'bookingStart': start, 'bookingMethods': methods, 'bookingRequired': required,
                # 規模（収容人数）は出典に無い。公式サイトで確認できたものだけ手で入れる（作り直しても残す）
                'capacity': cap, 'capacitySourceUrl': capsrc or d['url'], 'officialNote': HUT_OFFICIAL_NOTE.get(name),
                'sourceUrl': d['sourceUrl'], 'sourceUpdated': d['sourceUpdated'], 'lastVerified': datetime.date.today().isoformat(),
            })
    # 長野県のポータルに載っていない山小屋（scripts/huts_extra.py の手入力）を足す
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from huts_extra import EXTRA_HUTS
    names = set(h['name'] for h in huts)
    for e in EXTRA_HUTS:
        assert e['name'] not in names, e['name']
        names.add(e['name'])
        for mid in e['mountainIds'] + [o['id'] for o in e['otherMountains']]:
            assert mid in M, (e['name'], mid)
        assert e['mountainIds'] or e['otherMountains'], e['name']
        hid = 'hut-' + hashlib.md5((e['region'] + e['name']).encode('utf-8')).hexdigest()[:8]
        huts.append({
            'id': hid, 'name': e['name'], 'region': e['region'], 'mountainIds': e['mountainIds'], 'otherMountains': e['otherMountains'],
            'location': None, 'officialUrl': e['officialUrl'], 'tel': None,
            'openText': e['period'] if e['period'].startswith(('例年', '予約サイト')) else '2026年の営業：' + e['period'], 'bookingStart': e['bookingStart'], 'bookingMethods': e['bookingMethods'], 'bookingRequired': e['bookingRequired'],
            'capacity': e['capacity'], 'capacitySourceUrl': e['capacitySourceUrl'], 'bookingSourceUrl': e['bookingSourceUrl'],
            'sourceUrl': e['sourceUrl'], 'sourceUpdated': None, 'lastVerified': datetime.date.today().isoformat(),
        })
    # 公式サイトを1階層たどって確認した予約の開始・方法（huts_booking_extra.py）と、公式サイトのURL（huts_official_urls.json）を当てる
    from huts_booking_extra import BOOKING_EXTRA
    up = os.path.join(ROOT, 'data', 'huts_official_urls.json')
    off_urls = json.load(open(up, encoding='utf-8'))['huts'] if os.path.exists(up) else {}
    known = set(h['name'] for h in huts)
    assert set(BOOKING_EXTRA) <= known, set(BOOKING_EXTRA) - known
    for h in huts:
        if not h.get('officialUrl') and off_urls.get(h['name']):
            h['officialUrl'] = off_urls[h['name']]
        x = BOOKING_EXTRA.get(h['name'])
        if x:
            if x.get('s'):
                h['bookingStart'] = x['s']
            if x.get('m'):
                h['bookingMethods'] = x['m']
            if x.get('r'):
                h['bookingRequired'] = True
            if x.get('p'):
                h['openText'] = x['p']
            if x.get('n'):
                # 予約という仕組みがない小屋（避難小屋など）。予約の開始・方法は持たせない
                h['bookingNone'] = x['n']
                h['bookingStart'] = None
                h['bookingMethods'] = None
                h['bookingRequired'] = False
            if x.get('u'):
                h['bookingStartUnstated'] = True
            if x.get('src'):
                h['bookingSourceUrl'] = x['src']
            if not h.get('bookingSourceUrl'):
                h['bookingSourceUrl'] = h.get('officialUrl')
    yk_path = os.path.join(ROOT, 'data', 'huts_yamakei.json')
    yk_ref = json.load(open(yk_path, encoding='utf-8'))['huts'] if os.path.exists(yk_path) else {}
    for h in huts:
        r = yk_ref.get(h['name']) or {}
        h['capacityRef'] = r.get('capacity') or r.get('capacityText')
        h['capacityRefUrl'] = ('https://www.yamakei-online.com/lodge/detail.php?id=' + r['lodgeId']) if r.get('lodgeId') else None
    assert set(HUT_BOOKING) == set(HUT_MOUNTAINS), set(HUT_BOOKING) ^ set(HUT_MOUNTAINS)
    missing = sorted(set(HUT_MOUNTAINS) - seen)
    ids = [h['id'] for h in huts]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
    json.dump({'note': '山小屋まとめ（β）。長野県 山小屋情報ポータルサイト＋手入力（scripts/huts_extra.py）。scripts/build_huts_from_nagano.py が作る',
               'seasonYear': 2026, 'huts': huts}, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('山小屋', len(huts), '件／出典に見つからなかった名前:', missing)


if __name__ == '__main__':
    main()
