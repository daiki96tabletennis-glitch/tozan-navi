#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""毎年変わるデータ（季節バス・マイカー規制・閉鎖期間・開山期間・災害の通行止め）の見張り。

やること
  1. 期限（validTo）が切れた項目、30日以内に切れる項目を一覧にする
  2. 出典ページを取得し、前回から内容が変わったものを一覧にする（日付・運行・規制に関わる行だけを比べる）
  3. 季節運行の記載があるのに、期限と出典をデータとして持っていない山を一覧にする
データは書き換えない。結果を Markdown で出力するだけ（GitHub Actions が Issue にする）。

使い方
  python3 scripts/check_annual_updates.py                     # 取得して報告（標準出力）
  python3 scripts/check_annual_updates.py --no-fetch           # 期限だけ確認
  python3 scripts/check_annual_updates.py --state state.json --out report.md
  python3 scripts/check_annual_updates.py --today 2027-04-01   # 日付を指定して試す
終了コード：対応が必要な項目があれば 1、なければ 0
"""
import argparse, datetime, hashlib, html, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEASONAL_RE = re.compile(r'季節|期間限定|夏季|運行期間|マイカー規制|冬期閉鎖|冬季閉鎖')
KEYLINE_RE = re.compile(r'年|月|日|運行|運休|通行止|規制|閉鎖|開山|料金|運賃|円|予約')
SOON_DAYS = 30


def load(name):
    return json.load(open(os.path.join(ROOT, 'data', name), encoding='utf-8'))


def collect():
    """見張る項目を全データから集める"""
    M = load('mountains.json'); AC = load('accesses.json')
    items = []
    used = {}
    for m in M:
        for r in m.get('routes') or []:
            if r.get('accessId'):
                used.setdefault(r['accessId'], []).append(m['name'])
    for aid, a in AC.items():
        op = a.get('operation') or {}
        if not (op.get('validTo') or a.get('sourceUrl')):
            continue
        items.append({'key': 'access:' + aid, 'mountains': sorted(set(used.get(aid, []))), 'label': a['name'],
                      'validTo': op.get('validTo'), 'statusType': op.get('statusType'), 'url': a.get('sourceUrl'),
                      'lastVerified': a.get('lastVerified')})
    for m in M:
        for i, al in enumerate(m.get('alerts') or []):
            items.append({'key': f'alert:{m["id"]}:{i}', 'mountains': [m['name']], 'label': al.get('title'),
                          'validTo': al.get('validTo'), 'statusType': al.get('statusType'), 'url': al.get('sourceUrl'),
                          'lastVerified': al.get('lastVerified')})
        for i, p in enumerate((m.get('conditions') or {}).get('trailPeriods') or []):
            items.append({'key': f'trail:{m["id"]}:{i}', 'mountains': [m['name']], 'label': p.get('label'),
                          'validTo': p.get('to'), 'statusType': 'annual', 'url': p.get('sourceUrl'), 'lastVerified': None})
        for i, it in enumerate(m.get('annualItems') or []):
            items.append({'key': f'item:{m["id"]}:{i}', 'mountains': [m['name']], 'label': it.get('label'),
                          'validTo': it.get('validTo'), 'statusType': 'annual' if it.get('validTo') else 'temporary',
                          'url': it.get('sourceUrl'), 'lastVerified': it.get('lastVerified')})
    # 季節運行の記載があるのに、期限つきの項目を持たない旧構造の山
    missing = []
    for m in M:
        if m.get('dataModel') == 'ssot-v1':
            continue
        if any(it.get('validTo') for it in m.get('annualItems') or []):
            continue
        tr = m.get('trainRoutes') or {}
        text = json.dumps(tr, ensure_ascii=False) + json.dumps(m.get('warnBanner') or {}, ensure_ascii=False)
        if SEASONAL_RE.search(text):
            missing.append(m['name'])
    return items, missing


def fetch_keylines(url):
    """ページを取得し、日付・運行・規制に関わる行だけを取り出す（広告や日替わりの文言で誤検知しないため）"""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; yamatch-annual-check)'})
    raw = urllib.request.urlopen(req, timeout=30).read()
    if raw[:5] == b'%PDF-':
        return 'pdf:' + hashlib.sha256(raw).hexdigest()
    for enc in ('utf-8', 'cp932', 'euc-jp'):
        try:
            text = raw.decode(enc); break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode('utf-8', 'replace')
    text = re.sub(r'(?is)<(script|style|noscript)\b.*?</\1>', ' ', text)
    text = re.sub(r'(?s)<[^>]+>', '\n', text)
    lines = [re.sub(r'\s+', ' ', html.unescape(l)).strip() for l in text.split('\n')]
    keep = [l for l in lines if 4 <= len(l) <= 300 and KEYLINE_RE.search(l)]
    return '\n'.join(sorted(set(keep)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--today'); ap.add_argument('--no-fetch', action='store_true')
    ap.add_argument('--state'); ap.add_argument('--out')
    a = ap.parse_args()
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()
    items, missing = collect()
    expired, soon = [], []
    for it in items:
        if not it['validTo']:
            continue
        d = datetime.date.fromisoformat(it['validTo'])
        if d < today:
            expired.append(it)
        elif (d - today).days <= SOON_DAYS:
            soon.append(it)
    state = {}
    if a.state and os.path.exists(a.state):
        state = json.load(open(a.state, encoding='utf-8'))
    changed, failed, first = [], [], 0
    if not a.no_fetch:
        by_url = {}
        for it in items:
            if it['url']:
                by_url.setdefault(it['url'], []).append(it)
        for url, its in sorted(by_url.items()):
            try:
                h = hashlib.sha256(fetch_keylines(url).encode('utf-8')).hexdigest()
            except Exception as e:
                failed.append((url, its, str(e)[:80])); continue
            old = state.get(url)
            if old is None:
                first += 1
            elif old != h:
                changed.append((url, its))
            state[url] = h
        if a.state:
            json.dump(state, open(a.state, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    def names(it):
        return '・'.join(it['mountains']) or '—'
    out = [f'# 年次データの確認（{today.isoformat()}）', '',
           f'見張っている項目：{len(items)}件／期限切れ：{len(expired)}件／30日以内に期限：{len(soon)}件／'
           f'出典の変更：{len(changed)}件／取得できず：{len(failed)}件／期限・出典が未登録の山：{len(missing)}山', '']
    out += ['## 出典ページの内容が変わった（来季の発表・通行止めの解除などの可能性）', '']
    out += [f'- {"、".join(sorted(set(names(i) for i in its)))}：{its[0]["label"]} — {url}' for url, its in changed] or ['- なし']
    out += ['', '## 期限が切れた（来季の情報で更新が必要）', '']
    out += [f'- {names(i)}：{i["label"]}（{i["validTo"]} まで）— {i["url"] or "出典URLなし"}' for i in sorted(expired, key=lambda x: x['validTo'])] or ['- なし']
    out += ['', f'## {SOON_DAYS}日以内に期限が切れる', '']
    out += [f'- {names(i)}：{i["label"]}（{i["validTo"]} まで）' for i in sorted(soon, key=lambda x: x['validTo'])] or ['- なし']
    out += ['', '## 出典ページを取得できなかった（URLの変更・リンク切れの可能性）', '']
    out += [f'- {"、".join(sorted(set(names(i) for i in its)))}：{url}（{err}）' for url, its, err in failed] or ['- なし']
    out += ['', '## 季節運行の記載があるのに、期限と出典をデータとして持っていない山', '',
            '、'.join(missing) or 'なし', '']
    if first:
        out += [f'※ 今回が初回の取得だった出典：{first}件（次回から変更を検知します）', '']
    report = '\n'.join(out)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(report)
    else:
        print(report)
    sys.exit(1 if (expired or changed or failed) else 0)


if __name__ == '__main__':
    main()
