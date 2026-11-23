"""冬の山選び診断（/find/winter/）のデータ data/winter_find.json を作る（2026-11-17〜。運営者の指示「冬登山に特化した山選び診断」）。
手で編集しない。mountains.json・gear-data.json・accesses.json・winter_specials.json・onsen_sauna.json・saunachelin_hiking.json から作る。

- 11月〜3月（2026年11月〜2027年3月）の月ごとに：装備の区分（gearCalendar）、ピッケルのカード（gear-data.json の axe）、
  電車・バスで行けるか／車で行けるか（ok／part＝月の一部だけ／no）と、その理由（期間つき）
  - 電車・バス：季節運行の乗り物（build_access_tier.py の seasons()。月日で見る＝毎年同じ時期に走る前提）が走っていない日は行けない。
    期間の分からない季節運行は「走っていない」とする。閉鎖（closure）の名前にロープウェイ・ゴンドラ・バスなどがあれば、その期間も行けない
  - 道路の閉鎖（closure）の期間は、電車・バスの経路にバス・タクシーの区間があれば電車・バスでも行けない（磐梯山の八方台へのタクシーなど）
  - 車：閉鎖（annualItems の closure）の期間は行けない。期間の無い閉鎖は、名前に「冬期」「冬季」があれば12〜3月は閉鎖とみる。
    解除の日が無い閉鎖は3月末まで閉鎖とみる。冬山装備の月は、コースがその乗り物に頼っているので、季節運行の乗り物が止まる日も車で行けない
  - 月の1日・8日・15日・22日・末日で見る
- コース（泊を含まないもの）：時間・技術の難しさ（routes[].tech.grade）・鎖場・岩場・電車の印・種類
- 冬の特集：ダイヤモンド富士の日（記事と同じ計算。記事の山は gen_winter_specials.diamond_list＝観賞地点の指定つき、
  ほかに特徴の文に富士山の眺めが書いてある山すべてを山頂で計算）、冬の絶景の区分（views）
- 駐車場の標高とノーマルタイヤで行ける目安（road。data/winter_road.json＝scripts/build_winter_road.py）
- 下山後に寄れそうな温泉・サウナ（onsenNear。data/onsen_near_mountains.json＝scripts/build_onsen_near.py）
- 特徴の文・紹介文に温泉・サウナ（onsenText）、霧氷・樹氷（iceText）が書いてある山の印
- 下山後の楽しみ：温泉・サウナの記事のプラン（onsen_sauna.json）、サウナシュランの記事（saunachelin_hiking.json）
- 冬山装備の月の、冬の登山口までの道の確認：冬の絶景の記事で冬の行き方を確かめた山と VERIFIED だけ「確認済み」。ほかは「未確認」
mountains.json などを直したら流し直す（古いと check_pages.py セクション26で止まる）。--check は書かずに同じかを見る。
"""
import calendar
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from build_access_tier import season_groups  # noqa: E402
import gen_winter_specials as GW  # noqa: E402
import sun_calc  # noqa: E402
import diamond_fuji  # noqa: E402

OUT = os.path.join(ROOT, 'data', 'winter_find.json')
MONTHS = [(2026, 11), (2026, 12), (2027, 1), (2027, 2), (2027, 3)]
# 冬山装備の月に、冬も登山口まで行けることを公式の情報で確かめた山（冬の絶景の記事で確かめた山は自動で入る）
#  kisokoma：中央アルプス駒ヶ岳ロープウェイと、しらび平へのバスは通年（山のデータの経路の札「通年運行（冬ダイヤ・点検運休あり）」）
VERIFIED = {'kisokoma': '駒ヶ岳ロープウェイとバスは通年運行（冬ダイヤ・点検の運休あり）'}
LIFT_WORDS = re.compile(r'ロープウェイ|ゴンドラ|ケーブル|リフト|バス|シャトル')
WINTER_WORDS = re.compile(r'冬期|冬季')
FOOD = re.compile(r'温泉|茶屋|食堂|名物|そば|うどん|売店|カフェ|ごはん|ご飯|定食|だんご|団子|山小屋|山荘')
FUJI = re.compile(r'富士山[^。]{0,20}(見|望|眺|展望|正面|パノラマ|ながめ)|(見|望|眺|展望|正面|パノラマ)[^。]{0,12}富士山')
STAY = re.compile(r'泊')
ONSEN = re.compile(r'温泉|サウナ')
ICE = re.compile(r'霧氷|樹氷')


def mins(s):
    if not s:
        return None
    h = re.search(r'(\d+)時間', s)
    mi = re.search(r'(\d+)分', s)
    v = (int(h.group(1)) if h else 0) * 60 + (int(mi.group(1)) if mi else 0)
    return v or None


def accesses():
    raw = json.load(open(os.path.join(ROOT, 'data', 'accesses.json'), encoding='utf-8'))
    if isinstance(raw, dict) and 'accesses' in raw:
        raw = raw['accesses']
    return {a['id']: a for a in raw} if isinstance(raw, list) else raw


def gear_on(cal, d):
    e = cal[d.month - 1]
    if isinstance(e, str):
        return e
    return e['after'] if d.day >= e['changeDate'] else e['before']


def sample_days(y, mo):
    last = calendar.monthrange(y, mo)[1]
    return [datetime.date(y, mo, d) for d in (1, 8, 15, 22, last)]


def md_in(f, t, d):
    a, b, x = f[5:], t[5:], d.strftime('%m-%d')
    return a <= x <= b if a <= b else (x >= a or x <= b)


def jd(s):
    y, m, d = s.split('-')
    return '%d/%d' % (int(m), int(d))


def closures(m):
    out = []
    for a in m.get('annualItems') or []:
        if a.get('kind') not in ('closure', 'suspension'):
            continue  # suspension＝点検などで乗り物が止まる期間（木曽駒ヶ岳のロープウェイ。2026-11-19〜）
        f, t = a.get('validFrom'), a.get('validTo')
        if not f and not t and not WINTER_WORDS.search(a.get('label') or ''):
            continue  # 期間の無い閉鎖（災害の通行止めなど）は冬の判定に使わない
        out.append(a)
    return out


def closure_on(a, d):
    f, t = a.get('validFrom'), a.get('validTo')
    if not f and not t:
        return d.month in (12, 1, 2, 3)  # 期間の分からない冬期閉鎖は11月には数えない（大菩薩嶺の県道は12月中旬から）
    fd = datetime.date.fromisoformat(f) if f else datetime.date(2026, 11, 1)
    td = datetime.date.fromisoformat(t) if t else datetime.date(2027, 3, 31)
    return fd <= d <= td


def closure_text(a):
    f, t = a.get('validFrom'), a.get('validTo')
    if f and t:
        span = '（%s〜%s）' % (jd(f), jd(t))
    elif f:
        span = '（%sから）' % jd(f)
    else:
        span = '（冬のあいだ）'
    return re.sub(r'（[^）]*）$', '', a.get('label') or '') + span


def month_access(m, A, y, mo, winter_gear):
    sea = season_groups(m, A)
    cls = closures(m)
    road = uses_road(m)
    tr_ok, car_ok, why = [], [], []
    for d in sample_days(y, mo):
        t_ok = bool(m.get('trainAccess'))
        c_ok = True
        for per, label, _nv in sea:
            run = any(f and t and md_in(f, t, d) for f, t in per)
            if not run:
                if t_ok:
                    t_ok = False
                spans = ['%s〜%s' % (jd(f), jd(t)) for f, t in per if f and t]
                txt = (label or '季節運行の乗り物') + ('（%s）' % '・'.join(spans) if spans and len(spans) == len(per) else '（運行期間が不明）')
                if txt not in why:
                    why.append(txt)
                if winter_gear:
                    c_ok = False
        for a in cls:
            if closure_on(a, d):
                c_ok = False
                if road or LIFT_WORDS.search(a.get('label') or ''):
                    t_ok = False
                txt = closure_text(a)
                if txt not in why:
                    why.append(txt)
        tr_ok.append(t_ok)
        car_ok.append(c_ok)

    def st(xs):
        return 'ok' if all(xs) else ('no' if not any(xs) else 'part')
    return {'train': st(tr_ok) if m.get('trainAccess') else 'no', 'car': st(car_ok), 'why': why}


def uses_road(m):
    """電車・バスの経路にバス・タクシーの区間がある（道路の閉鎖で、その区間も通れなくなる）"""
    for r in ((m.get('trainRoutes') or {}).get('routes') or {}).values():
        for l in (r or {}).get('legs') or []:
            meth = l.get('method') or {}
            if (meth.get('icon') or '') in ('bus', 'taxi') or re.search(r'バス|タクシー', meth.get('line') or ''):
                return True
    return False


def axe_of(G, mid, mo):
    for c in (G.get(mid) or {}).get(str(mo)) or []:
        if c.get('c') == 'axe':
            return c.get('i')
    return None


def lift_of(m):
    for r in ((m.get('trainRoutes') or {}).get('routes') or {}).values():
        for l in (r or {}).get('legs') or []:
            if ((l.get('method') or {}).get('icon') or '') == 'ropeway':
                return True
    return False


def ev_month(ev):
    out = {}
    for e in ev:
        for mo in sorted({e['from'].month, e['to'].month, e['date'].month}):
            if mo in (11, 12, 1, 2, 3):
                out.setdefault(str(mo), []).append(GW.ev_text(e))
    return out


def build():
    Mby, SC, W = GW.load()
    A = accesses()
    G = json.load(open(os.path.join(ROOT, 'data', 'gear-data.json'), encoding='utf-8'))
    ON = json.load(open(os.path.join(ROOT, 'data', 'onsen_sauna.json'), encoding='utf-8'))
    SA = json.load(open(os.path.join(ROOT, 'data', 'saunachelin_hiking.json'), encoding='utf-8'))
    dia = {x['m']['id']: x for x in GW.diamond_list(Mby, SC, W)}
    views = {x['id']: x for x in W['views']['mountains']}
    road = json.load(open(os.path.join(ROOT, 'data', 'winter_road.json'), encoding='utf-8'))['mountains']
    near_onsen = json.load(open(os.path.join(ROOT, 'data', 'onsen_near_mountains.json'), encoding='utf-8'))['mountains']
    onsen = {}
    for p in ON['plans']:
        onsen.setdefault(p['id'], []).extend(f['name'] for f in p.get('facilities') or [])
    sauna = {}
    for s in SA['saunas']:
        for mm in s.get('mountains') or []:
            sauna.setdefault(mm['id'], []).append(s['name'])
    out = []
    for mid, m in Mby.items():
        cal = m.get('gearCalendar')
        if not cal or len(cal) != 12:
            continue
        routes = []
        for i, r in enumerate(m.get('routes') or []):
            t = mins(r.get('time'))
            if not t or STAY.search(r.get('name') or ''):
                continue
            routes.append({'i': i + 1, 'n': r.get('name'), 'min': t, 'tech': ((r.get('tech') or {}).get('grade') or ''),
                           'chain': bool(r.get('chains')), 'rock': bool(r.get('rocks')), 'train': bool(r.get('byTrain')),
                           'type': r.get('courseType'),
                           # 冬に使えないコース（routes[].winter。2026-11-19〜）：st＝closed／car_only／unknown、f・t＝MM-DD
                           'w': ({'st': r['winter']['state'], 'f': r['winter'].get('from') or r['winter'].get('closeFrom'), 't': r['winter'].get('to') or r['winter'].get('trainTo') or ('03-31' if r['winter'].get('closeFrom') else None)}
                                 if r.get('winter') else None)})
        if not routes:
            continue
        fp = m.get('featurePoints') or []
        fptext = ' '.join((p.get('label') or '') + ' ' + (p.get('text') or '') for p in fp)
        tags = list(m.get('vibes') or [])
        for p in fp:
            if p.get('tag') and p['tag'] not in tags:
                tags.append(p['tag'])
        g, ax, acc = {}, {}, {}
        for y, mo in MONTHS:
            e = cal[mo - 1]
            g[str(mo)] = e if isinstance(e, str) else {'b': e['before'], 'a': e['after'], 'd': e['changeDate']}
            wg = any(gear_on(cal, d) == 'winter_gear' for d in sample_days(y, mo))
            ax[str(mo)] = axe_of(G, mid, mo)
            acc[str(mo)] = month_access(m, A, y, mo, wg)
        fuji = [p.get('text') for p in fp if FUJI.search((p.get('label') or '') + (p.get('text') or ''))]
        v = views.get(mid)
        d = dia.get(mid)
        dia_ev = d['ev'] if d else None
        if not dia_ev and fuji:
            # ダイヤモンド富士：記事に載せた山だけでなく、特徴の文に富士山の眺めが書いてある山すべてで、記事と同じ計算をする（山頂で計算。2026-11-17 運営者の指示「記事で特集されている山だけが出やすくなる選択肢がある」）
            lat, lng, ele = GW.summit(m, SC)
            dia_ev = diamond_fuji.events(lat, lng, ele)
        text_all = fptext + ' ' + (m.get('description') or '') + ' ' + (m.get('recommendReason') or '')
        ver = None
        if v and v.get('winterAccess'):
            ver = v.get('winterShort') or v.get('winterAccess')
        elif mid in VERIFIED:
            ver = VERIFIED[mid]
        item = {
            'id': mid, 'name': m['name'], 'area': m.get('area'), 'ele': m.get('elevation'), 'diff': m.get('difficulty'),
            'cat': m.get('category'), 'day': bool(m.get('daytrip')), 'coeff': m.get('coeffMin') or m.get('coeffMax') or 0,
            'rest': ((m.get('status') or {}).get('level') == 'restricted'),
            'tt': {'shinjuku': m.get('trainTimeShinjuku'), 'omiya': m.get('trainTimeOmiya'), 'yokohama': m.get('trainTimeYokohama')},
            'dt': {'shinjuku': m.get('driveTimeShinjuku') or m.get('driveTime'), 'omiya': m.get('driveTimeOmiya') or m.get('driveTime'),
                   'ofuna': m.get('driveOfuna') or m.get('driveTime')},
            'train': bool(m.get('trainAccess')), 'lift': lift_of(m),
            'g': g, 'axe': ax, 'acc': acc, 'routes': routes, 'tags': tags,
            'fp': [{'t': p.get('tag'), 'l': p.get('label'), 'x': p.get('text')} for p in fp[:5]],
            'fuji': bool(fuji), 'food': bool(FOOD.search(fptext)),
        }
        if m.get('volcanoCodes'):
            item['volcanoCodes'] = m['volcanoCodes']
            if m.get('volcanoScope'):
                item['volcanoScope'] = m['volcanoScope']
        if onsen.get(mid):
            item['onsen'] = onsen[mid]
        if sauna.get(mid):
            item['sauna'] = sauna[mid]
        if dia_ev:
            dm = ev_month(dia_ev)
            if dm:
                item['dia'] = dm
        if 'view' in (m.get('vibes') or []):
            item['pano'] = True  # ホームの絞り込みの「絶景」（厳選。山頂・稜線からの特別な展望）
        if ONSEN.search(text_all):
            item['onsenText'] = True
        rd = road.get(mid)
        if rd:
            item['road'] = {'e': rd.get('elev'), 'nt': {k: v for k, v in rd['normal'].items() if str(k) in g}}
            if rd.get('note'):
                item['road']['note'] = rd['note']
        if mid in near_onsen:
            item['onsenNear'] = near_onsen[mid].get('near') or True
        if ICE.search(text_all):
            item['iceText'] = True
        if v:
            item['view'] = {'cat': v.get('category'), 'what': v.get('what'), 'season': v.get('season')}
        if ver:
            item['winterOk'] = ver
        out.append(item)
    out.sort(key=lambda x: x['id'])
    meta = {'_note': 'scripts/build_winter_find.py が作る（手で編集しない）。冬の山選び診断（/find/winter/）のデータ',
            'months': ['%d-%02d' % ym for ym in MONTHS], 'hatsuhinodePublished': W['hatsuhinode'].get('publish') is not False}
    return {'meta': meta, 'mountains': out}


def dump(d):
    return json.dumps(d, ensure_ascii=False, separators=(',', ':'), sort_keys=False) + '\n'


def main():
    s = dump(build())
    if '--check' in sys.argv:
        cur = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if cur != s:
            print('data/winter_find.json が古い：python3 scripts/build_winter_find.py を流す')
            sys.exit(1)
        print('data/winter_find.json は最新')
        return
    open(OUT, 'w', encoding='utf-8').write(s)
    d = json.loads(s)
    print('書いた：data/winter_find.json（%d山・%dKB）' % (len(d['mountains']), len(s.encode('utf-8')) // 1024))


if __name__ == '__main__':
    main()
