#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新構造（dataModel: ssot-v1）の山について、旧フィールドを新構造から生成する。

新構造の「正」:
  mountains.json : representativeRouteId / routes[].{id,trailheadId,accessId,coeff,status} / conditions / alerts
  trailheads.json: 登山口・アクセス拠点（座標はここだけに持つ）
  accesses.json  : 電車・バス経路、運賃、運行期間、出典、最終確認日（複数の山で共有）

ここで生成する旧フィールド（手で編集しない）:
  trailhead, lat, lng, parking, gmapUrl, amapUrl, mapBtnsHtml,
  trainRoutes, trainAccessHtml, trainAccess*, trainTime*, fare*, transfers*, busLinks, busScheduleLinks, trainInfo,
  coeffMin, coeffMax, courseCoefficient, courseCoefficientRange（＋本文中の「定数◯〜◯」）,
  seasonCalendar, calLegend, seasonNoGear, season6Crampons, warnBanner

使い方: python3 scripts/build_derived.py [--check]   （--check は書き込まず差分の有無だけ返す）
"""
import json, os, re, sys, copy, datetime, urllib.parse
import gear_calendar
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section

def load(name):
    return json.load(open(os.path.join(ROOT, 'data', name), encoding='utf-8'))

def hm(x):
    h, m = divmod(int(x), 60)
    return f'約{h}時間{m}分' if h and m else (f'約{h}時間' if h else f'約{m}分')

def md(d):
    y, m, dd = d.split('-'); return f'{int(m)}/{int(dd)}'

def legs_text(legs):
    parts = []
    for l in legs[:-1]:
        parts.append(l['station'])
        line = (l.get('method') or {}).get('line') or ''
        d = l.get('durationMin')
        parts.append(line + (hm(d) if d else ''))
    parts.append(legs[-1]['station'])
    return '→'.join(p for p in parts if p)

def map_urls(t):
    """登山口・拠点データから地図URLを作る（座標が未確認なら名称検索）"""
    name = re.sub(r'（.*?）', '', t['name'])
    q = urllib.parse.quote(name, safe='')
    if t.get('lat') is not None and t.get('lng') is not None:
        lat, lng = t['lat'], t['lng']
        g = f'https://www.google.com/maps/search/?api=1&query={lat}%2C{lng}'
        a = f'https://maps.apple.com/?ll={lat},{lng}&q={q}'
    else:
        g = f'https://www.google.com/maps/search/?api=1&query={q}'
        a = f'https://maps.apple.com/?q={q}'
    btn = ('<div class="map-btns">\n'
           f'      <a href="{g}" target="_blank" class="map-btn-link">Googleマップ</a>\n'
           f'      <a href="{a}" target="_blank" class="map-btn-link">Apple Maps</a>\n'
           '    </div>')
    return g, a, btn

def month_span(d_from, d_to, year):
    """期間が各月を「全部覆う=full / 半分以上=most / 一部=part / 無し=none」で返す（12要素）"""
    out = []
    f = datetime.date.fromisoformat(d_from) if d_from else datetime.date(year, 1, 1)
    t = datetime.date.fromisoformat(d_to) if d_to else datetime.date(year, 12, 31)
    for mth in range(1, 13):
        ms = datetime.date(year, mth, 1)
        me = (datetime.date(year + (mth == 12), mth % 12 + 1, 1) - datetime.timedelta(days=1))
        if t < ms or f > me: out.append('none'); continue
        days = (min(t, me) - max(f, ms)).days + 1
        total = (me - ms).days + 1
        out.append('full' if days == total else ('most' if days * 2 >= total else 'part'))
    return out

def monthly_status(mt, access):
    """月別の3ステータス（登山道 / 公共交通 / 装備）を作る"""
    year = 2026
    cond = mt.get('conditions') or {}
    trail = ['open'] * 12
    for p in cond.get('trailPeriods') or []:
        if p.get('status') != 'closed': continue
        for i, s in enumerate(month_span(p.get('from'), p.get('to'), year)):
            if s in ('full', 'most'): trail[i] = 'closed'
            elif s == 'part' and trail[i] == 'open': trail[i] = 'partial'
    transport = ['unknown'] * 12
    if access and access.get('trainRoutes'):
        opn = access.get('operation') or {}
        if opn.get('mode') == 'year': transport = ['ok'] * 12
        elif opn.get('validFrom') or opn.get('validTo'):
            transport = [{'full': 'ok', 'most': 'partial', 'part': 'partial', 'none': 'none'}[s]
                         for s in month_span(opn.get('validFrom'), opn.get('validTo'), year)]
    elif access is not None and not access.get('trainRoutes'):
        transport = ['unknown'] * 12
    gear = list(cond.get('gearMonthly') or ['normal'] * 12)
    return trail, transport, gear

LEGEND = {'s-ok': 'アイゼン不要', 's-gear': '軽アイゼン等', 's-hard': '冬山装備', 's-closed': '入山不可'}
def ranges(months):
    if not months: return '不可'
    out, s, p = [], months[0], months[0]
    for x in months[1:] + [None]:
        if x is not None and x == p + 1: p = x; continue
        out.append(f'{s}月〜{p}月' if s != p else f'{s}月')
        s = p = x
    return '・'.join(out)

def derive(mt, TH, AC):
    routes = mt['routes']
    by_id = {r['id']: r for r in routes}
    rep = by_id[mt['representativeRouteId']]
    th = TH[rep['trailheadId']]
    ac = AC.get(rep.get('accessId'))
    # 登山口・地図
    mt['trailhead'] = th['name']
    # lat / lng は「山の位置」（トップの地図表示用）。登山口の座標では上書きしない
    target = TH[(ac or {}).get('mapTargetId') or rep['trailheadId']]
    mt['gmapUrl'], mt['amapUrl'], mt['mapBtnsHtml'] = map_urls(target)
    mt['mapTargetName'] = target['name']
    mt['address'] = target.get('address') or ''
    mt['trailheadAddress'] = th.get('address') or ''
    if ac and ac.get('car') and ac['car'].get('parking'):
        mt['parking'] = ac['car']['parking']
    elif ac and ac.get('car') and ac['car'].get('restriction'):
        mt['parking'] = ac['car']['restriction']
    else:
        mt['parking'] = '確認中（最新の情報は公式サイトで確認してください）'
    # 電車・バス：代表ルートのアクセス。無ければ経路データを持つ別ルートのアクセスを、ルート名を明示して使う
    tr_route, tr_ac = rep, ac
    if not (ac and ac.get('trainRoutes')):
        for r in routes:
            a2 = AC.get(r.get('accessId'))
            if a2 and a2.get('trainRoutes'):
                tr_route, tr_ac = r, a2; break
        else:
            tr_route, tr_ac = None, None
    if tr_ac:
        mt['trainRoutes'] = copy.deepcopy(tr_ac['trainRoutes'])
        mt['trainAccessLabel'] = tr_ac['name']
        mt['trainAccessRouteId'] = tr_route['id']
        R = mt['trainRoutes']['routes']
        for dep, K in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
            mt['fare' + K] = (tr_ac.get('fares') or {}).get(dep)
            legsum = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
            t = (tr_ac.get('trainTimes') or {}).get(dep)
            mt['trainTime' + K] = t if (t and t >= legsum) else legsum
            mt['transfers' + K] = (tr_ac.get('transfers') or {}).get(dep)
        mt['trainAccess'] = legs_text(R['shinjuku']['legs'])
        mt['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
        mt['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
        mt['busLinks'] = tr_ac.get('busLinks'); mt['busScheduleLinks'] = tr_ac.get('busScheduleLinks')
        mt['trainAccessHtml'] = render_ts_section(mt['trainRoutes'], mt)
    mt['trainAccessOperation'] = (tr_ac or {}).get('operation')
    mt['routeTrailheads'] = {r['id']: TH[r['trailheadId']]['name'] for r in routes if r.get('trailheadId') in TH}
    mt['trainInfo'] = None  # 旧い自由記述は使わない（経路データと食い違うため）
    trail, transport, gear = monthly_status(mt, tr_ac)
    cls_pre = ['s-closed' if trail[i] == 'closed' else {'normal': 's-ok', 'snow_caution': 's-gear', 'winter': 's-hard'}[gear[i]] for i in range(12)]
    # コース定数：ルートの値だけを正とする
    cs = [r['coeff'] for r in routes if r.get('coeff') is not None]
    # コース定数の上部表示をルートの値から作るのは、ルートの時間・距離・累積標高差を一次情報で照合済みの山だけ
    # （coeffFromRoutes: true）。未照合の山は従来の表示値を変えない（低く出る誤りを避けるため）
    if cs and mt.get('coeffFromRoutes'):
        old = mt.get('courseCoefficientRange')
        lo, hi = min(cs), max(cs)
        new = str(lo) if lo == hi else f'{lo}〜{hi}'
        mt['coeffMin'], mt['coeffMax'], mt['courseCoefficient'], mt['courseCoefficientRange'] = lo, hi, [lo, hi], new
        mt['representativeCoeff'] = rep.get('coeff')
        pat = re.compile(r'((?:コース)?定数\s*)\d+(?:〜\d+)?')
        def fix(v):
            if isinstance(v, str): return pat.sub(lambda m_: m_.group(1) + new, v)
            if isinstance(v, list): return [fix(x) for x in v]
            if isinstance(v, dict): return {k: fix(x) for k, x in v.items()}
            return v
        for k in ('metaTitle', 'metaDescription', 'ogTitle', 'ogDescription', 'introHtml', 'faq', 'description', 'dlNoteHtml'):
            if mt.get(k): mt[k] = fix(mt[k])
    # 本文：代表ルートの数値・アクセス・シーズンはデータから作る（手書きの古い値を残さない）
    rep_txt = f"{rep['name']}は所要{rep['time']}/{rep['distance']}/標高差{rep['elevation']}"
    if mt.get('introHtml'):
        mt['introHtml'] = re.sub(r'代表コース（[^）]*(?:（[^）]*）)?[^）]*）は所要[^。]*。', '代表コース（' + rep['name'] + '）は所要' + rep['time'] + '/' + rep['distance'] + '/標高差' + rep['elevation'] + '。', mt['introHtml'])
        mt['introHtml'] = re.sub(r'公共交通機関でのアクセス可（[^。]*。', '', mt['introHtml'])
    if mt.get('dlNoteHtml'):
        mt['dlNoteHtml'] = re.sub(r'代表コースの[^。]*?は[^。]*?標高差[^。]*。', '代表コースの' + rep['name'] + 'は' + rep['time'] + '・' + rep['distance'] + '・標高差' + rep['elevation'] + '。', mt['dlNoteHtml'])
    for q in mt.get('faq') or []:
        if 'アクセス' in q['question']:
            parts = []
            if tr_ac:
                parts.append(f"{tr_ac['name']}：新宿から{hm(mt['trainTimeShinjuku'])}（{mt['fareShinjuku']:,}円）、"
                             f"大宮から{hm(mt['trainTimeOmiya'])}（{mt['fareOmiya']:,}円）、横浜から{hm(mt['trainTimeYokohama'])}（{mt['fareYokohama']:,}円）が目安です。")
                opn = tr_ac.get('operation') or {}
                if opn.get('validFrom') and opn.get('validTo'):
                    parts.append(f"{opn.get('seasonYear')}年の運行（利用）期間は{md(opn['validFrom'])}〜{md(opn['validTo'])}です。")
                if opn.get('reservation'): parts.append(opn['reservation'] + '。')
            else:
                parts.append('電車・バスの経路は確認中です。')
            car = (ac or {}).get('car') or {}
            if car.get('restriction'): parts.append('車の場合：' + car['restriction'] + '。')
            if tr_route is not None and tr_route is not rep:
                parts.append(f"代表ルート（{rep['name']}）の登山口は{th['name']}で、電車・バスの経路は確認中です。")
            q['answer'] = ''.join(parts)
        elif 'シーズン' in q['question']:
            parts = [f"通常の登山装備で登りやすいのは{ranges([i + 1 for i in range(12) if cls_pre[i] == 's-ok'])}が目安です。"]
            for pz in (mt.get('conditions') or {}).get('trailPeriods') or []:
                parts.append(f"{md(pz['from'])}〜{md(pz['to'])}は{pz.get('label')}です。")
            parts.append('残雪や凍結の状況は年によって変わるため、直前に最新情報を確認してください。')
            q['answer'] = ''.join(parts)
    # 季節：登山道・公共交通・装備の3層 → 旧カレンダーへ
    cls = cls_pre
    mt['seasonCalendar'] = cls
    mt['calLegend'] = [LEGEND[c] for c in ('s-ok', 's-gear', 's-hard', 's-closed') if c in cls]
    mt['seasonNoGear'] = ranges([i + 1 for i in range(12) if cls[i] == 's-ok'])
    mt['season6Crampons'] = ranges([i + 1 for i in range(12) if cls[i] == 's-gear'])
    mt['monthlyStatus'] = {'trail': trail, 'transport': transport, 'gear': gear}
    # 装備カレンダー（4区分＋月途中の切替）。閉鎖期間の開始・終了が月の途中なら2色にする
    mt['gearCalendar'] = gear_calendar.from_ssot((mt.get('conditions') or {}).get('gearMonthly') or ['normal'] * 12,
                                                 (mt.get('conditions') or {}).get('trailPeriods'))
    # 注意表示
    al = mt.get('alerts') or []
    if al:
        a = al[0]
        mt['warnBanner'] = {'type': a.get('level', 'yellow'), 'title': a['title'], 'text': a['text'],
                            'url': a.get('sourceUrl'), 'linkText': a.get('linkText', '公式情報')}
    return mt

def main():
    check = '--check' in sys.argv
    D = load('mountains.json'); TH = load('trailheads.json'); AC = load('accesses.json')
    before = json.dumps(D, ensure_ascii=False, sort_keys=True)
    n = 0
    for mt in D:
        if mt.get('dataModel') == 'ssot-v1':
            derive(mt, TH, AC); n += 1
    after = json.dumps(D, ensure_ascii=False, sort_keys=True)
    if check:
        print(f'対象 {n} 山 / 差分{"あり（build_derived.py を実行してください）" if before != after else "なし"}')
        sys.exit(1 if before != after else 0)
    json.dump(D, open(os.path.join(ROOT, 'data', 'mountains.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'派生フィールドを更新: {n} 山')

if __name__ == '__main__':
    main()
