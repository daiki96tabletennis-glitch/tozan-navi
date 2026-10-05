#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全山のデータ監査。data/audit_report.csv に mountain,route,issueType,severity,currentValue,recommendedAction を出力する。
severity: P0=安全・現地到達に影響 / P1=登山計画に大きく影響 / P2=精度・UX / P3=表記
使い方: python3 scripts/audit_data.py
"""
import json, os, re, csv, math, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(n): return json.load(open(os.path.join(ROOT, 'data', n), encoding='utf-8'))
D = load('mountains.json'); TH = load('trailheads.json'); AC = load('accesses.json')
TODAY = datetime.date.today()
rows = []
def add(m, route, typ, sev, cur, act): rows.append([m['id'] + ' ' + m['name'], route or '', typ, sev, str(cur)[:200], act])
def coords(s):
    x = re.search(r'(3\d\.\d+)(?:%2C|,)\s*(1[34]\d\.\d+)', s or '')
    return (float(x.group(1)), float(x.group(2))) if x else None
def dist(a, b): return math.hypot((a[0]-b[0])*111000, (a[1]-b[1])*111000*math.cos(math.radians(a[0])))
for m in D:
    ssot = m.get('dataModel') == 'ssot-v1'
    routes = m.get('routes') or []
    if not ssot:
        add(m, '', '未移行（旧構造）', 'P2', '山単位の登山口・アクセス', '新構造（ルート→登山口→アクセス）へ移行')
        cs = [r['coeff'] for r in routes if r.get('coeff') is not None]
        out = [r['name'] for r in routes if r.get('coeff') is not None and not (m['coeffMin'] <= r['coeff'] <= m['coeffMax'])]
        if out: add(m, '・'.join(out), 'コース定数が上部表示の範囲外', 'P2', f"上部{m['coeffMin']}〜{m['coeffMax']} / ルート{cs}", 'ルートの値を正として上部表示を自動生成')
        if any(r.get('coeff') is None for r in routes): add(m, '', 'ルートのコース定数なし', 'P2', [r['name'] for r in routes if r.get('coeff') is None], '時間・距離・標高差を確認して算出')
        g, b = coords(m.get('gmapUrl')), coords(m.get('mapBtnsHtml'))
        if g and b and dist(g, b) > 300: add(m, '', '地図座標の二重管理（300m以上の差）', 'P1', f'gmapUrl{g} / ボタン{b}（差{int(dist(g,b))}m）', '登山口データの座標に一本化')
        if not b: add(m, '', '地図ボタンなし', 'P2', m.get('gmapUrl'), '登山口座標を確認して生成')
        th = re.split(r'[（(]', m.get('trailhead') or '')[0]
        if th and not any(th in (r.get('name') or '') + (r.get('waypoints') or '') for r in routes):
            add(m, '', '登山口名がどのルートにも出てこない', 'P1', f"登山口:{m.get('trailhead')} / ルート:{[r['name'] for r in routes]}", 'ルートごとに登山口を紐付け（要確認）')
        tr = m.get('trainRoutes')
        if tr:
            dest = tr['routes']['shinjuku']['legs'][-1]['station']
            if th and th not in dest and re.split(r'[（(]', dest)[0] not in (m.get('trailhead') or ''):
                add(m, '', '電車ルートの終点と登山口が不一致', 'P0', f"終点:{dest} / 登山口:{m.get('trailhead')}", 'ルート別にアクセスを分ける')
            if m.get('trainInfo') and tr:
                add(m, '', '旧い自由記述（trainInfo）が残存', 'P3', m['trainInfo'][:80], '経路データから生成に切替')
        for r in routes:
            if re.search(r'\+\+|mm$', r.get('elevation') or ''): add(m, r['name'], '標高差の表記エラー', 'P3', r['elevation'], '表記を修正')
        continue
    # 新構造の整合性
    ids = [r.get('id') for r in routes]
    if m.get('representativeRouteId') not in ids: add(m, '', '代表ルートが存在しない', 'P0', m.get('representativeRouteId'), '代表ルートを設定')
    for r in routes:
        if r.get('trailheadId') not in TH: add(m, r['name'], '登山口IDが未登録', 'P0', r.get('trailheadId'), '登山口データを追加')
        if r.get('accessId') not in AC: add(m, r['name'], 'アクセスIDが未登録', 'P0', r.get('accessId'), 'アクセスデータを追加')
        if r.get('coeff') is None: add(m, r['name'], 'ルートのコース定数なし', 'P2', None, '確認して設定')
        t = TH.get(r.get('trailheadId')) or {}
        if t and (t.get('lat') is None or t.get('needsVerification')): add(m, r['name'], '登山口の座標が未確認', 'P1', f"{t.get('name')} {t.get('lat')},{t.get('lng')}", '一次情報で座標を確認')
        a = AC.get(r.get('accessId')) or {}
        if a and not a.get('trainRoutes'): add(m, r['name'], '電車・バス経路が未作成', 'P1', a.get('name'), '公式情報で経路・運賃を確認して作成')
        if a and a.get('needsVerification') and a.get('trainRoutes'): add(m, r['name'], 'アクセスに未確認項目あり', 'P1', (a.get('operation') or {}).get('note'), '運行期間などを公式情報で確認')
        if a and not a.get('sourceUrl'): add(m, r['name'], 'アクセスの出典URLなし', 'P2', a.get('name'), '出典を保存')
        opn = a.get('operation') or {}
        if opn.get('validTo') and datetime.date.fromisoformat(opn['validTo']) < TODAY:
            add(m, r['name'], '運行期間が終了（今季は利用不可・来季の再確認が必要）', 'P1', f"{opn.get('validFrom')}〜{opn['validTo']}", '来季の運行情報が出たら更新')
        lv = a.get('lastVerified')
        if lv and (TODAY - datetime.date.fromisoformat(lv)).days > 180: add(m, r['name'], '最終確認から180日超', 'P1', lv, '再確認')
    for al in m.get('alerts') or []:
        if al.get('validTo') and datetime.date.fromisoformat(al['validTo']) < TODAY and al.get('statusType') == 'temporary':
            add(m, '', '期限切れの注意表示', 'P1', al['title'], '解除を確認して削除')
out = os.path.join(ROOT, 'data', 'audit_report.csv')
with open(out, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f); w.writerow(['mountain', 'route', 'issueType', 'severity', 'currentValue', 'recommendedAction']); w.writerows(rows)
c = collections.Counter(r[3] for r in rows); t = collections.Counter((r[3], r[2]) for r in rows)
print('監査結果:', dict(sorted(c.items())), '→', out)
for (sev, typ), n in sorted(t.items()): print(f'  {sev} {typ}: {n}')
