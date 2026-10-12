#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山ページの検索結果に出るタイトル（metaTitle）と説明文（metaDescription）を、山のデータから作る。
使い方：python3 scripts/build_meta.py            （変更の一覧を出すだけ）
        python3 scripts/build_meta.py --write    （data/mountains.json に書く。このあと gen_mountain_pages.py --all）

ねらい：検索結果でクリックされること。検索する人が知りたい「どれくらいで登れるか・自分に登れるか・どう行くか」を、
タイトルの前半（スマホで切れない約30文字）に、数字で入れる。「コース定数」は一般には通じないのでタイトルには出さない。

  タイトル：{山名} 登山｜{難易度}・{日帰り◯時間／山小屋泊}｜{◯◯駅から徒歩／バス◯分}【百名山・コース・駐車場】｜Yamatch
  説明文  ：{山名}（標高・地域）は{山ごとの一言紹介}。代表コースは{時間・距離・標高差}で{難易度}。{新宿から電車で約◯時間、◯◯駅から…}。駐車場・装備・天気も。

使う値はすべて mountains.json の値（代表コースの時間・距離・標高差、難易度、日帰り、電車・バスの経路と所要時間、車の所要時間、一言紹介）。
新しい事実は足さない。値が無い部分は、その部分を省く。
説明文は、手で書いてある山（metaAuto が無い山のうち、以前のひな形「◯◯の難易度は…」でないもの）は変えない。タイトルは全山を作り直す。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'mountains.json')
LEVEL = {'初級': '初心者向け', '初〜中級': '初〜中級', '中級': '中級', '中〜上級': '中〜上級', '上級': '上級者向け'}
LEVEL_DESC = {'初級': '登山が初めての人でも歩きやすい', '初〜中級': '初心者が次に挑戦しやすい', '中級': '体力のある中級者向け',
              '中〜上級': '経験と体力が要る中〜上級者向け', '上級': '十分な経験が要る上級者向け'}


def hm(x):
    h, mi = divmod(int(x), 60)
    return '%d時間%d分' % (h, mi) if h and mi else ('%d時間' % h if h else '%d分' % mi)


def rep_route(m):
    rs = m.get('routes') or []
    rid = m.get('representativeRouteId')
    for r in rs:
        if rid and r.get('id') == rid:
            return r
    for r in rs:                      # 通行止めのコースは代表にしない
        if (r.get('status') or {}).get('state') != 'closed':
            return r
    return rs[0] if rs else {}


def time_phrase(m, r):
    """「日帰り1時間30分」「1泊2日・歩行10時間」など。時間が無ければ日帰りかどうかだけ"""
    t = (r.get('time') or '').strip()
    core = re.match(r'(\d+時間(?:\d+分)?|\d+分)', t)
    stay = re.search(r'(\d泊\d日|\d泊|\d日間|\d日合計)', t)
    if m.get('daytrip'):
        # 日帰りでも8時間以上歩くコースは「日帰り10時間」とだけ書くと気軽に見えるので、健脚向けと添える
        hours = re.match(r'(\d+)時間', core.group(1)) if core else None
        long_day = bool(hours and int(hours.group(1)) >= 8)
        return (('健脚向け日帰り' if long_day else '日帰り') + core.group(1)) if core else '日帰り'
    if stay and core:
        return '%s・歩行%s' % (stay.group(1).replace('日合計', '日間'), core.group(1))
    return ('山小屋泊・歩行' + core.group(1)) if core else '山小屋泊'


def access(m):
    """(タイトル用の短い言い方, 説明文用の文)。電車・バスの経路が無ければ車"""
    tr = m.get('trainRoutes')
    if tr:
        legs = tr['routes']['shinjuku']['legs']

        def mode(l):
            me = l.get('method') or {}
            line = me.get('line') or ''
            if 'バス' in line and '高速' not in line:
                return 'bus'
            return me.get('icon')
        # 最後に電車を降りる駅（＝登山口への入口の駅）を探す。その先がバス・徒歩・タクシー・ロープウェイ
        rail = [i for i, l in enumerate(legs) if l.get('method') and mode(l) == 'train']
        if rail and rail[-1] + 1 < len(legs):
            gi = rail[-1] + 1
            gw = re.split(r'[（(]', legs[gi]['station'])[0]
            rest = [l for l in legs[gi:] if l.get('method')]
            modes = [mode(l) for l in rest]
            mins = sum(l.get('durationMin') or 0 for l in rest)
            if modes:
                how = 'バス' if 'bus' in modes else 'タクシー' if 'taxi' in modes else 'ロープウェイ' if 'ropeway' in modes else '徒歩'
                short = '%sから%s%s' % (gw, how, hm(mins) if mins and how in ('バス', '徒歩') and len(modes) == 1 else '')
            else:
                # 終点まで「電車」の印が付いている経路：最後の区間が鉄道の名前でなければ、季節運行のバスなどとみなす
                prev = legs[gi - 1]
                line = (prev.get('method') or {}).get('line') or ''
                core = re.sub(r'「.*?」', '', line)        # 「◯◯線」という路線名のバスがあるので、かぎかっこの中は見ない
                if re.search(r'交通|バス', core) or not re.search(r'線|JR|特急|新幹線|鉄道|ライン|電鉄|急行|快速', core):
                    modes = ['bus']
                    short = '%sからバス%s' % (re.split(r'[（(]', prev['station'])[0], hm(prev['durationMin']) if prev.get('durationMin') else '')
                else:
                    short = '%s下車' % gw
            total = m.get('trainTimeShinjuku')
            long_ = ('新宿から電車%sで約%s（%s）' % ('とバス' if 'bus' in modes else '', hm(total), short)) if total else short
            return short, long_
        if m.get('trainTimeShinjuku'):
            return '新宿から高速バス', '新宿から高速バスなどで約%s' % hm(m['trainTimeShinjuku'])
    dt = m.get('driveTimeShinjuku')
    if dt:
        return '新宿から車で%s' % hm(dt), '車は新宿から約%s' % hm(dt)
    return '', ''


_ip = os.path.join(ROOT, 'data', 'seo_intents.json')
INTENT = json.load(open(_ip, encoding='utf-8'))['mountains'] if os.path.exists(_ip) else {}
EASY = ('初級', '初〜中級')


def intent_of(m):
    """その山で、検索する人がいちばん知りたいこと（Search Console の検索語から。scripts/gsc_import.py）。
    検索語のデータが無い山・「コース」「標高差」が多い山は、サイト全体でいちばん多い「難易度」の形にする"""
    top = (INTENT.get(m['id']) or {}).get('top')
    return top if top in ('初心者', '日帰り', '時間', 'アクセス') else '難易度'


def gain(r):
    g = re.search(r'([\d,]+)\s*m', r.get('elevation') or '')
    return format(int(g.group(1).replace(',', '')), ',') + 'm' if g else None


def core_time(r):
    t = re.match(r'(\d+時間(?:\d+分)?|\d+分)', (r.get('time') or '').strip())
    return t.group(1) if t else None


def build_title(m):
    """検索結果の見出し。前半（約30文字）で、その山でいちばん多い疑問に答える"""
    r = rep_route(m)
    name, lv, cat = m['name'], m.get('difficulty') or '', m.get('category')
    tp, ct, g = time_phrase(m, r), core_time(r), gain(r)
    a_short, _ = access(m)
    day = m.get('daytrip')
    it = intent_of(m)
    if it == '初心者':
        head = ('%s登山 初心者向けコース｜%s・難易度%s' % (name, tp, lv)) if lv in EASY else ('%s登山は初心者でも登れる？難易度%s｜%s' % (name, lv, tp))
    elif it == '日帰り':
        head = ('%s 日帰り登山｜%s・難易度%s' % (name, ('歩行' + ct) if ct else '日帰り可', lv)) if day else (
            '%s登山は日帰りできる？山小屋泊が基本%s・難易度%s' % (name, ('（歩行%s）' % ct) if ct else '', lv))
    elif it == '時間':
        head = '%s 登山のコースタイム%s｜難易度%s・%s' % (name, ct or '', lv, '日帰り可' if day else '山小屋泊')
    elif it == 'アクセス':
        head = '%s 登山のアクセス｜%s｜難易度%s・%s' % (name, a_short or '車', lv, tp)
        a_short = ''
    else:
        head = '%s 登山の難易度は%s｜%s%s' % (name, lv, tp, ('・標高差' + g) if g else '')
    tag = '【%s】' % cat if cat in ('百名山', '二百名山') else ''
    if (m.get('status') or {}).get('level') == 'restricted':
        tag = '【入山規制あり】'
    ss = summit_season(m)
    if ss:                                        # 登れる期間が決まっている山は、期間を見出しに出す（期間外に「登れる」と読めないように）
        tag = '【登れるのは%s〜%s】' % (ss[1], ss[2])
    title = head + (('｜' + a_short) if a_short else '') + tag + '｜Yamatch'
    if len(title) > 60 and a_short:              # 長すぎるときは、アクセスの分数を落とす
        a2 = re.sub(r'(?:\d+時間)?(?:\d+分)?$', '', a_short)
        title = head + '｜' + a2 + tag + '｜Yamatch'
    return title


def summit_season(m):
    """山頂まで登れる期間が決まっている山（annualItems の kind: trail。御嶽山の規制緩和、男体山の開山期間など）→ (年, '7/1', '10/14')"""
    for a in m.get('annualItems') or []:
        if a.get('kind') == 'trail' and a.get('validFrom') and a.get('validTo'):
            f, t = a['validFrom'].split('-'), a['validTo'].split('-')
            return int(f[0]), '%d/%d' % (int(f[1]), int(f[2])), '%d/%d' % (int(t[1]), int(t[2]))
    return None


def build_desc(m):
    """検索結果の説明文。最初の1文で、その山でいちばん多い疑問に答える。続けて代表コースの数字、行き方、山ごとの一言"""
    r = rep_route(m)
    name, lv = m['name'], m.get('difficulty') or ''
    ct, day = core_time(r), m.get('daytrip')
    bits = [x for x in (r.get('time'), r.get('distance'), ('標高差' + r['elevation'].lstrip('+')) if r.get('elevation') else None) if x]
    course = ('代表コース（%s）は%s' % (r['name'], '・'.join(bits))) if bits and r.get('name') else ''
    _, a_long = access(m)
    it = intent_of(m)
    head = '%s（標高%sm・%s）' % (name, format(m['elevation'], ','), m.get('area') or '')
    ld = LEVEL_DESC.get(lv, '')
    if it == '初心者':
        s = head + ('は初心者でも登りやすい山（難易度%s）。' % lv if lv in EASY else 'は初心者には厳しい山（難易度%s・%s）。' % (lv, ld))
        s += (course + '。') if course else ''
    elif it == '日帰り':
        s = head + ('は、登れる期間中なら日帰りで登れます' if (day and summit_season(m)) else 'は日帰りで登れます' if day else 'は山小屋泊が基本です') + ('（歩行%s・難易度%s）。' % (ct, lv) if ct else '（難易度%s）。' % lv)
        s += (course + '。') if course else ''
    elif it == '時間':
        s = (head + 'のコースタイムは、代表コース（%s）で%s。' % (r['name'], '・'.join(bits))) if course else head + 'の登山ガイド。'
        s += '難易度は%s（%s）。' % (lv, ld)
    elif it == 'アクセス':
        s = head + ('へは、' + a_long + '。' if a_long else 'の登山ガイド。')
        s += ('難易度は%s。' % lv) + ((course + '。') if course else '')
        a_long = ''
    else:
        s = head + 'の難易度は%s（%s）。' % (lv, ld)
        s += (course + '。') if course else ''
    if a_long:
        s += a_long + '。'
    if it != '日帰り':
        s += '日帰りできます。' if day else '山小屋泊がおすすめです。'
    ss = summit_season(m)
    if ss:
        s += '山頂まで登れるのは決まった期間だけです（%d年は%s〜%s。期間外は登れません）。' % ss
    one = re.split(r'(?<=。)', (m.get('description') or '').strip())[0].rstrip('。')
    if one and len(one) <= 60:
        s += one + '。'
    return s + '駐車場・装備・天気も掲載。'


def main():
    write = '--write' in sys.argv
    D = json.load(open(P, encoding='utf-8'))
    nt = nd = 0
    for m in D:
        t = build_title(m)
        if m.get('metaTitle') != t:
            nt += 1
        auto = True          # 説明文は全山を、その山でいちばん多い疑問に答える形で作る（手で書いてあった文は metaDescriptionManual に残す）
        if not m.get('metaAuto') and not m.get('metaDescriptionManual') and write:
            m['metaDescriptionManual'] = m.get('metaDescription')
        d = build_desc(m)
        if auto and m.get('metaDescription') != d:
            nd += 1
        if not write and m['id'] in ('hotaka', 'kitadake', 'mizugaki', 'karamatsu', 'akagi', 'shirouma', 'okutama', 'ontakesan', 'tsukuba', 'takao', 'hiwadayama'):
            print(t, '（%d字）' % len(t))
            print('   ', d[:170], '（%d字）' % len(d))
        if write:
            m['metaTitle'] = t
            m['ogTitle'] = t
            if auto:
                m['metaDescription'] = d
                m['ogDescription'] = d
                m['metaAuto'] = True
    print('タイトルを変える %d 山／説明文を変える %d 山（全 %d 山）' % (nt, nd, len(D)))
    if write:
        assert len(set(m['metaTitle'] for m in D)) == len(D), 'タイトルが重複している'
        json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('data/mountains.json に書きました')


if __name__ == '__main__':
    main()
