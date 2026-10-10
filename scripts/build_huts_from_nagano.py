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
# 山小屋名（出典の表記）→ 関係する山のID
HUT_MOUNTAINS = {
    '槍ヶ岳山荘': ['yari'], 'ヒュッテ大槍': ['yari'], '殺生小屋': ['yari'], '槍沢ロッヂ': ['yari'],
    '穂高岳山荘': ['hotaka'], '涸沢小屋': ['hotaka'], '涸沢ヒュッテ': ['hotaka'], '岳沢小屋': ['hotaka'],
    '横尾山荘': ['yari', 'hotaka', 'chogatake'], '徳沢ロッヂ': ['chogatake'], '氷壁の宿 徳澤園': ['chogatake'],
    '蝶ヶ岳ヒュッテ': ['chogatake'], '大滝山荘': ['chogatake'], '常念小屋': ['jonengatake'], '焼岳小屋': ['yakedake'],
    '燕山荘': ['otenshoudake'], '大天荘': ['otenshoudake'], '大天井ヒュッテ': ['otenshoudake'], '中房温泉': ['otenshoudake', 'arikayama'], '有明荘': ['arikayama'],
    '餓鬼岳小屋': ['gakedake'], '七倉山荘': ['eboshidake_kita', 'noguchigoro'], '烏帽子小屋': ['eboshidake_kita'], '野口五郎小屋': ['noguchigoro'],
    '白馬山荘': ['shirouma'], '村営白馬岳頂上宿舎': ['shirouma'], '白馬大池山荘': ['shirouma'], '猿倉荘': ['shirouma'], '栂池山荘': ['shirouma'], '栂池ヒュッテ': ['shirouma'],
    '唐松岳頂上山荘': ['karamatsu'], '村営八方池山荘': ['karamatsu'], '五竜山荘': ['goryudake'], 'キレット小屋': ['goryudake', 'kashimayari'],
    '冷池山荘': ['kashimayari'], '種池山荘': ['kashimayari'], '針ノ木小屋': ['harinokidake'], '大沢小屋': ['harinokidake'],
    '肩ノ小屋': ['norikura'], '位ヶ原山荘': ['norikura'],
    '北沢峠 こもれび山荘': ['komagatake', 'senjogatake'], '大平山荘': ['komagatake', 'senjogatake'], '仙丈小屋': ['senjogatake'], '馬の背ヒュッテ': ['senjogatake'],
    '塩見小屋': ['shiomidake'], '三伏峠小屋': ['shiomidake'], '聖光小屋': ['hijiridade', 'terkari'], '県営光岳小屋': ['terkari'],
    '駒ヶ岳頂上山荘': ['kisokoma'], '宝剣山荘': ['kisokoma'], '天狗荘': ['kisokoma'], '西駒山荘': ['kisokoma'],
    '木曽殿山荘': ['utsugi'], '空木駒峰ヒュッテ': ['utsugi'], '越百小屋': ['minamikomagatake'],
    '蓼科山頂ヒュッテ': ['keirisan'], '蓼科山荘': ['keirisan'],
    '赤岳頂上山荘': ['yatsugatake'], '赤岳天望荘': ['yatsugatake'], '行者小屋': ['yatsugatake'], '赤岳鉱泉': ['yatsugatake'], '赤岳山荘': ['yatsugatake'],
    '美濃戸山荘': ['yatsugatake'], '硫黄岳山荘': ['yatsugatake'],
    '苗場山頂ヒュッテ－自然体験交流センター': ['naeba'], '甲武信小屋': ['kobushigatake'], '十文字小屋': ['kobushigatake'], '金峰山小屋': ['kinpusan'],
    '二ノ池山荘': ['ontakesan'], '二の池ヒュッテ': ['ontakesan'], '女人堂（金剛堂）': ['ontakesan'], '石室山荘': ['ontakesan'], '七合目行場山荘': ['ontakesan'],
    '天狗温泉浅間山荘': ['asama'], '鷲が峰ひゅって': ['kirigamine'], 'ヒュッテみさやま': ['kirigamine'], '八島山荘': ['kirigamine'],
    '美ヶ原高原ホテル・山本小屋': ['utsukushigahara'],
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
    '穂高岳山荘': (M1 + '（4/27〜5/20の宿泊分は4月20日から電話のみ）', ['電話']), '涸沢小屋': (M1 + '（4月25日から現地電話で受付開始）', ['電話']),
    '涸沢ヒュッテ': (M1, ['Web']), '横尾山荘': (M1, ['Web（繁忙期は限定数のみ）']), '徳沢ロッヂ': (None, ['Web（完全予約制）']), '氷壁の宿 徳澤園': (None, None),
    '岳沢小屋': (M1, ['Web']), '焼岳小屋': (M1, ['電話', 'FAX']), '有明荘': (None, None), '中房温泉': ('宿泊日の2か月前から', ['Web']),
    '燕山荘': ('3月18日から（2026年）', None), '餓鬼岳小屋': (None, None), '大天荘': (None, ['Web']), '大天井ヒュッテ': (M1, None),
    '常念小屋': (M1, None), '蝶ヶ岳ヒュッテ': (M1, ['Web']), '大滝山荘': (M1, None), '七倉山荘': (None, None), '烏帽子小屋': (M1, None),
    '野口五郎小屋': (None, ['電話（Web予約は不可）']), '栂池ヒュッテ': (None, ['Web']), '栂池山荘': (None, None),
    '白馬大池山荘': ('5月20日 7:00から（2026年）', ['Web']), '猿倉荘': ('5月20日 7:00から（2026年）', ['Web']),
    '白馬山荘': ('夏季（6/20〜）の宿泊分は5月20日 7:00から（2026年）', ['Web']), '村営白馬岳頂上宿舎': ('5月8日 9:00から（2026年）', None),
    '唐松岳頂上山荘': (None, None), '村営八方池山荘': (None, None), '五竜山荘': ('5月20日 7:00から（2026年）', ['Web']), 'キレット小屋': ('5月20日 7:00から（2026年）', ['Web']),
    '冷池山荘': (None, None), '種池山荘': (None, None), '針ノ木小屋': (None, None), '大沢小屋': (None, None), '肩ノ小屋': (None, None),
    '位ヶ原山荘': ('宿泊日の3か月前から', ['Web']),
    '北沢峠 こもれび山荘': (None, None), '大平山荘': (None, ['電話のみ']), '仙丈小屋': (None, None), '馬の背ヒュッテ': (None, ['Web（Yamatan）', '電話']),
    '塩見小屋': (None, None), '三伏峠小屋': (None, ['Web（オンライン予約）']), '聖光小屋': ('3月20日から（2026年）', ['電話（1週間前まで）']), '県営光岳小屋': (None, ['Webのみ']),
    '西駒山荘': ('2月20日から（2026年・Web予約）', ['Web']), '駒ヶ岳頂上山荘': (None, None), '宝剣山荘': (None, None), '天狗荘': (None, None),
    '木曽殿山荘': (None, None), '空木駒峰ヒュッテ': ('6月1日から（2026年）', None), '越百小屋': (None, None),
    '蓼科山頂ヒュッテ': (None, None), '蓼科山荘': (None, None), '硫黄岳山荘': (None, None), '赤岳頂上山荘': (None, None), '赤岳天望荘': (None, None),
    '行者小屋': (None, None), '赤岳鉱泉': (None, None), '赤岳山荘': (None, None), '美濃戸山荘': (None, None),
    '天狗温泉浅間山荘': (None, None), '苗場山頂ヒュッテ－自然体験交流センター': (None, ['電話']), '美ヶ原高原ホテル・山本小屋': (None, None),
    '八島山荘': (None, ['Web', '電話']), '鷲が峰ひゅって': (None, None), 'ヒュッテみさやま': (None, None), '十文字小屋': (None, None),
    '甲武信小屋': (None, None), '金峰山小屋': (None, None), '七合目行場山荘': (None, None), '女人堂（金剛堂）': (None, None), '石室山荘': (None, None),
    '二ノ池山荘': (None, ['電話のみ']), '二の池ヒュッテ': (None, ['公式LINE']),
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
            for mid in HUT_MOUNTAINS[name]:
                assert mid in M, (name, mid)
            huts.append({
                'id': hid, 'name': name, 'region': region, 'mountainIds': HUT_MOUNTAINS[name],
                'location': d.get('location'), 'officialUrl': d['url'], 'tel': d.get('tel') or None,
                # openText は出典の「開設」欄の原文（営業期間・予約の区分）。ページにはそのまま出す
                'openText': d.get('openText'), 'bookingStart': start, 'bookingMethods': methods, 'bookingRequired': required,
                # 規模（収容人数）は出典に無い。公式サイトで確認できたものだけ手で入れる（作り直しても残す）
                'capacity': prev.get('capacity'), 'capacitySourceUrl': prev.get('capacitySourceUrl'),
                'sourceUrl': d['sourceUrl'], 'sourceUpdated': d['sourceUpdated'], 'lastVerified': datetime.date.today().isoformat(),
            })
    assert set(HUT_BOOKING) == set(HUT_MOUNTAINS), set(HUT_BOOKING) ^ set(HUT_MOUNTAINS)
    missing = sorted(set(HUT_MOUNTAINS) - seen)
    ids = [h['id'] for h in huts]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
    json.dump({'note': '山小屋まとめ（β）。出典は長野県 山小屋情報ポータルサイト。scripts/build_huts_from_nagano.py が作る（capacity だけ手入力）',
               'seasonYear': 2026, 'huts': huts}, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('山小屋', len(huts), '件／出典に見つからなかった名前:', missing)


if __name__ == '__main__':
    main()
