#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""管理画面の「分析」タブの数字を作る。Search Console・GA4・Firebase（お気に入り数など）から集めて、
Firebase のデータベースの /adminDash/latest に書く（運営者のアカウントだけが読めるルール。scripts/firebase_rules.json）。

  python3 scripts/admin_dashboard.py              # 集めて Firebase に書く（GitHub Actions：.github/workflows/admin-dashboard.yml）
  python3 scripts/admin_dashboard.py --dry-run    # 書かずに .claude/admin_dash.json に保存して中身を確かめる

- 数字は公開のファイル（data/ など）には書かない。リポジトリもサイトも誰でも読めるため
- 読み取りの鍵：環境変数 GOOGLE_READER_KEY（鍵の JSON の中身）か、~/.config/yamatch/google-key.json
- 書き込みの鍵：環境変数 FIREBASE_DB_URL・FIREBASE_SERVICE_ACCOUNT（山小屋の通知と同じもの）
- 計算はデータの値だけ。AIは使わない。目安のクリック率の曲線は一般的な値で、並べる順番を付けるためだけに使う
"""
import argparse, datetime, json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://tozan-navi.com/'
GA4_PROPERTY = '528250629'
SC_URL = 'https://searchconsole.googleapis.com/webmasters/v3/sites/https%3A%2F%2Ftozan-navi.com%2F/searchAnalytics/query'
GA_URL = 'https://analyticsdata.googleapis.com/v1beta/properties/' + GA4_PROPERTY + ':runReport'
# 掲載順位ごとの目安のクリック率（1〜10位。それより下は 1%）
CTR_CURVE = [0.28, 0.15, 0.10, 0.07, 0.055, 0.045, 0.035, 0.03, 0.025, 0.02]

# ページの種類（パスの頭で分ける）
GROUPS = [('/mountains/', '山ページ'), ('/recommend/', '登山タイプ診断'), ('/search/', '検索ページ'), ('/huts/', '山小屋'),
          ('/gear/', '海外ギア'), ('/articles/', '記事'), ('/mypage/', 'マイページ'), ('/type/', '登山タイプの結果'), ('/find/', '山選び診断')]


def group_of(path):
    p = re.sub(r'^https?://[^/]+', '', path or '')
    if p in ('', '/', '/index.html'):
        return 'トップ'
    for pre, name in GROUPS:
        if p.startswith(pre):
            return name
    return 'その他'


def expected_ctr(pos):
    i = int(round(pos)) - 1
    return CTR_CURVE[i] if 0 <= i < len(CTR_CURVE) else 0.01


def session(scopes):
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    raw = os.environ.get('GOOGLE_READER_KEY')
    if raw:
        cred = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=scopes)
    else:
        cred = service_account.Credentials.from_service_account_file(os.path.expanduser('~/.config/yamatch/google-key.json'), scopes=scopes)
    return AuthorizedSession(cred)


def post(s, url, body, tries=3):
    for i in range(tries):
        r = s.post(url, json=body, timeout=60)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 400:
            return {'_error': r.json().get('error', {}).get('message', '')[:200]}
        time.sleep(3 * (i + 1))
    r.raise_for_status()


# ---------- Search Console ----------
def sc_rows(s, start, end, dims=None, row_limit=5000, filters=None):
    body = {'startDate': str(start), 'endDate': str(end), 'rowLimit': row_limit}
    if dims:
        body['dimensions'] = dims
    if filters:
        body['dimensionFilterGroups'] = filters
    return post(s, SC_URL, body).get('rows', [])


def sc_total(rows):
    r = rows[0] if rows else {}
    return {'clicks': int(r.get('clicks', 0)), 'impressions': int(r.get('impressions', 0)),
            'ctr': round(r.get('ctr', 0), 4), 'position': round(r.get('position', 0), 1)}


def search_console(s, today):
    end = today - datetime.timedelta(days=3)           # Search Console は2〜3日遅れて確定する
    cur = (end - datetime.timedelta(days=27), end)
    prev = (cur[0] - datetime.timedelta(days=28), cur[0] - datetime.timedelta(days=1))
    out = {'range': [str(cur[0]), str(cur[1])], 'prevRange': [str(prev[0]), str(prev[1])]}
    out['total'] = sc_total(sc_rows(s, *cur))
    out['prevTotal'] = sc_total(sc_rows(s, *prev))

    daily = sc_rows(s, end - datetime.timedelta(days=89), end, ['date'])
    out['daily'] = [[r['keys'][0], int(r['clicks']), int(r['impressions'])] for r in daily]

    pages = sc_rows(s, *cur, dims=['page'])
    pages_prev = {r['keys'][0]: r for r in sc_rows(s, *prev, dims=['page'])}
    queries = sc_rows(s, *cur, dims=['query'])
    queries_prev = {r['keys'][0]: r for r in sc_rows(s, *prev, dims=['query'])}
    qp = sc_rows(s, *cur, dims=['query', 'page'], row_limit=10000)
    best_page = {}
    for r in qp:
        q, p = r['keys']
        if q not in best_page or r['impressions'] > best_page[q][1]:
            best_page[q] = (p, r['impressions'])

    # ページの種類ごと
    g = {}
    for r in pages:
        k = group_of(r['keys'][0])
        a = g.setdefault(k, {'clicks': 0, 'impressions': 0, 'prevClicks': 0})
        a['clicks'] += int(r['clicks']); a['impressions'] += int(r['impressions'])
    for p, r in pages_prev.items():
        g.setdefault(group_of(p), {'clicks': 0, 'impressions': 0, 'prevClicks': 0})['prevClicks'] += int(r['clicks'])
    out['groups'] = sorted([dict(v, name=k) for k, v in g.items()], key=lambda x: -x['clicks'])

    # あと一歩の検索語：4〜15位で表示が多い。取りこぼし（表示 ×（目安 − 実際））の大きい順
    near = []
    for r in queries:
        pos, imp = r['position'], r['impressions']
        if 3.5 <= pos <= 15.5 and imp >= 20:
            lost = imp * max(0.0, expected_ctr(min(pos, 3)) - r['ctr'])
            near.append({'query': r['keys'][0], 'impressions': int(imp), 'clicks': int(r['clicks']), 'ctr': round(r['ctr'], 4),
                         'position': round(pos, 1), 'page': short(best_page.get(r['keys'][0], ('',))[0]), 'lost': round(lost, 1)})
    out['nearMiss'] = sorted(near, key=lambda x: -x['lost'])[:20]

    # クリック率が低いページ：表示が多いのに、順位の目安よりクリック率が低い（見出し・説明文の見直し候補）
    low = []
    for r in pages:
        imp, pos = r['impressions'], r['position']
        if imp < 150:
            continue
        exp = expected_ctr(pos)
        if r['ctr'] < exp * 0.6:
            low.append({'page': short(r['keys'][0]), 'impressions': int(imp), 'clicks': int(r['clicks']), 'ctr': round(r['ctr'], 4),
                        'position': round(pos, 1), 'lost': round(imp * (exp - r['ctr']), 1)})
    out['lowCtr'] = sorted(low, key=lambda x: -x['lost'])[:15]

    # 伸びた・落ちた（クリックの差）
    def movers(cur_rows, prev_map, key):
        rows = []
        seen = set()
        for r in cur_rows:
            k = r['keys'][0]; seen.add(k)
            pc = int(prev_map[k]['clicks']) if k in prev_map else 0
            rows.append({key: short(k) if key == 'page' else k, 'clicks': int(r['clicks']), 'prevClicks': pc, 'diff': int(r['clicks']) - pc,
                         'position': round(r['position'], 1)})
        for k, r in prev_map.items():
            if k not in seen and r['clicks'] > 0:
                rows.append({key: short(k) if key == 'page' else k, 'clicks': 0, 'prevClicks': int(r['clicks']), 'diff': -int(r['clicks']),
                             'position': None})
        up = sorted([x for x in rows if x['diff'] > 0], key=lambda x: -x['diff'])[:10]
        down = sorted([x for x in rows if x['diff'] < 0], key=lambda x: x['diff'])[:10]
        return {'up': up, 'down': down}
    out['pageMovers'] = movers(pages, pages_prev, 'page')
    out['queryMovers'] = movers(queries, queries_prev, 'query')
    out['topQueries'] = [{'query': r['keys'][0], 'clicks': int(r['clicks']), 'impressions': int(r['impressions']),
                          'position': round(r['position'], 1)} for r in sorted(queries, key=lambda r: -r['clicks'])[:20]]
    return out


def short(url):
    return re.sub(r'^https?://[^/]+', '', url or '')


# ---------- GA4 ----------
def ga(s, body):
    res = post(s, GA_URL, body)
    if '_error' in res:
        return None, res['_error']
    rows = []
    for r in res.get('rows', []):
        rows.append([d['value'] for d in r.get('dimensionValues', [])] + [float(m['value']) for m in r.get('metricValues', [])])
    return rows, None


def ga4(s, names):
    cur = {'startDate': '28daysAgo', 'endDate': 'yesterday'}
    prev = {'startDate': '56daysAgo', 'endDate': '29daysAgo'}
    out = {}
    mets = ['activeUsers', 'newUsers', 'sessions', 'screenPageViews', 'userEngagementDuration', 'engagedSessions']
    for key, rng in (('total', cur), ('prevTotal', prev)):
        rows, _ = ga(s, {'dateRanges': [rng], 'metrics': [{'name': m} for m in mets]})
        v = rows[0] if rows else [0] * len(mets)
        t = dict(zip(mets, [int(x) for x in v]))
        t['engagementSecPerUser'] = round(t['userEngagementDuration'] / t['activeUsers']) if t['activeUsers'] else 0
        t['engagementRate'] = round(t['engagedSessions'] / t['sessions'], 3) if t['sessions'] else 0
        out[key] = t

    rows, _ = ga(s, {'dateRanges': [{'startDate': '89daysAgo', 'endDate': 'yesterday'}], 'dimensions': [{'name': 'date'}],
                     'metrics': [{'name': 'activeUsers'}, {'name': 'screenPageViews'}], 'orderBys': [{'dimension': {'dimensionName': 'date'}}]})
    out['daily'] = [[r[0][:4] + '-' + r[0][4:6] + '-' + r[0][6:], int(r[1]), int(r[2])] for r in (rows or [])]

    for key, dim in (('newVsReturning', 'newVsReturning'), ('device', 'deviceCategory'), ('channel', 'sessionDefaultChannelGroup')):
        rows, _ = ga(s, {'dateRanges': [cur], 'dimensions': [{'name': dim}], 'metrics': [{'name': 'activeUsers'}, {'name': 'sessions'}]})
        out[key] = sorted([{'name': r[0] or '(不明)', 'users': int(r[1]), 'sessions': int(r[2])} for r in (rows or [])], key=lambda x: -x['users'])

    # ページの表示（種類ごと・山ページの上位）
    rows, _ = ga(s, {'dateRanges': [cur], 'dimensions': [{'name': 'pagePath'}], 'metrics': [{'name': 'screenPageViews'}, {'name': 'activeUsers'}],
                     'limit': 10000})
    views = {}
    for r in rows or []:
        views[r[0]] = views.get(r[0], 0) + int(r[1])
    rows_p, _ = ga(s, {'dateRanges': [prev], 'dimensions': [{'name': 'pagePath'}], 'metrics': [{'name': 'screenPageViews'}], 'limit': 10000})
    views_prev = {}
    for r in rows_p or []:
        views_prev[r[0]] = views_prev.get(r[0], 0) + int(r[1])

    # アフィリエイトのリンクのクリック（gear_affiliate_click）
    ev = {'filter': {'fieldName': 'eventName', 'stringFilter': {'value': 'gear_affiliate_click'}}}
    rows, _ = ga(s, {'dateRanges': [cur], 'dimensions': [{'name': 'pagePath'}], 'metrics': [{'name': 'eventCount'}], 'dimensionFilter': ev, 'limit': 10000})
    clicks = {}
    for r in rows or []:
        clicks[r[0]] = clicks.get(r[0], 0) + int(r[1])
    rows, _ = ga(s, {'dateRanges': [prev], 'dimensions': [{'name': 'pagePath'}], 'metrics': [{'name': 'eventCount'}], 'dimensionFilter': ev, 'limit': 10000})
    clicks_prev = {}
    for r in rows or []:
        clicks_prev[r[0]] = clicks_prev.get(r[0], 0) + int(r[1])

    g = {}
    for p, v in views.items():
        a = g.setdefault(group_of(p), {'views': 0, 'prevViews': 0, 'aff': 0, 'prevAff': 0})
        a['views'] += v
    for p, v in views_prev.items():
        g.setdefault(group_of(p), {'views': 0, 'prevViews': 0, 'aff': 0, 'prevAff': 0})['prevViews'] += v
    for p, v in clicks.items():
        g.setdefault(group_of(p), {'views': 0, 'prevViews': 0, 'aff': 0, 'prevAff': 0})['aff'] += v
    for p, v in clicks_prev.items():
        g.setdefault(group_of(p), {'views': 0, 'prevViews': 0, 'aff': 0, 'prevAff': 0})['prevAff'] += v
    for k, a in g.items():
        a['affPer1000'] = round(a['aff'] * 1000.0 / a['views'], 1) if a['views'] else 0
    out['groups'] = sorted([dict(v, name=k) for k, v in g.items()], key=lambda x: -x['views'])

    def label(p):
        m = re.match(r'^/mountains/([^/]+)/', p)
        return names.get(m.group(1), p) if m else p
    out['affTotal'] = sum(clicks.values())
    out['affPrevTotal'] = sum(clicks_prev.values())
    out['affPages'] = [{'page': p, 'label': label(p), 'clicks': c, 'views': views.get(p, 0),
                        'per1000': round(c * 1000.0 / views[p], 1) if views.get(p) else None}
                       for p, c in sorted(clicks.items(), key=lambda x: -x[1])[:15]]
    mt = [(p, v) for p, v in views.items() if p.startswith('/mountains/')]
    out['topMountains'] = [{'page': p, 'label': label(p), 'views': v, 'prevViews': views_prev.get(p, 0), 'aff': clicks.get(p, 0)}
                           for p, v in sorted(mt, key=lambda x: -x[1])[:15]]
    # 表示が多いのにリンクが押されていない山ページ（装備カードの見直し候補）
    out['mountainsNoAff'] = [{'page': p, 'label': label(p), 'views': v} for p, v in sorted(mt, key=lambda x: -x[1])
                             if v >= 100 and clicks.get(p, 0) == 0][:10]

    # Amazon・楽天別、商品別（GA4 にカスタム ディメンションを登録したあとから分かれる）
    out['affBy'] = {}
    for key, dim in (('platform', 'customEvent:platform'), ('product', 'customEvent:product_name'), ('pageType', 'customEvent:page_type')):
        rows, err = ga(s, {'dateRanges': [cur], 'dimensions': [{'name': dim}], 'metrics': [{'name': 'eventCount'}], 'dimensionFilter': ev,
                           'orderBys': [{'metric': {'metricName': 'eventCount'}, 'desc': True}], 'limit': 20})
        out['affBy'][key] = {'missing': True} if err else {'rows': [{'name': r[0] or '(なし)', 'clicks': int(r[1])} for r in rows]}

    # 機能ごとの表示
    feats = [('/huts/', '山小屋まとめ'), ('/gear/', '海外ギア'), ('/mypage/', 'マイページ'), ('/recommend/', '登山タイプ診断'), ('/find/', '山選び診断'), ('/articles/', '記事')]
    out['features'] = [{'name': n, 'views': sum(v for p, v in views.items() if p.startswith(pre)),
                        'prevViews': sum(v for p, v in views_prev.items() if p.startswith(pre))} for pre, n in feats]
    return out


# ---------- Firebase ----------
def firebase_token():
    from google.oauth2 import service_account
    import google.auth.transport.requests as tr
    sa = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
    cred = service_account.Credentials.from_service_account_info(
        sa, scopes=['https://www.googleapis.com/auth/firebase.database', 'https://www.googleapis.com/auth/userinfo.email'])
    cred.refresh(tr.Request())
    return cred.token


def fb(method, path, body=None, token=None):
    import requests
    db = os.environ['FIREBASE_DB_URL'].rstrip('/')
    r = requests.request(method, db + path + '.json', headers={'Authorization': 'Bearer ' + token},
                         data=None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8'), timeout=60)
    r.raise_for_status()
    return r.json()


def firebase_stats(token, names):
    out = {}
    counts = fb('GET', '/counts', token=token) or {}
    fav = sum(int(v.get('fav', 0) or 0) for v in counts.values() if isinstance(v, dict))
    climbed = sum(int(v.get('climbed', 0) or 0) for v in counts.values() if isinstance(v, dict))
    top = sorted(counts.items(), key=lambda kv: -int((kv[1] or {}).get('fav', 0) or 0))[:10]
    out['counts'] = {'fav': fav, 'climbed': climbed,
                     'topFav': [{'id': k, 'label': names.get(k, k), 'fav': int((v or {}).get('fav', 0) or 0),
                                 'climbed': int((v or {}).get('climbed', 0) or 0)} for k, v in top]}
    push = fb('GET', '/hutPush', token=token) or {}
    out['push'] = {'devices': len(push), 'alerts': sum(len((v or {}).get('alerts') or []) for v in push.values() if isinstance(v, dict))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    names = {}
    try:
        for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8')):
            names[m.get('id')] = m.get('name')
    except Exception:
        pass
    today = datetime.date.today()
    s = session(['https://www.googleapis.com/auth/webmasters.readonly', 'https://www.googleapis.com/auth/analytics.readonly'])
    data = {'generatedAt': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M'),
            'sc': search_console(s, today), 'ga': ga4(s, names)}
    token = None
    if os.environ.get('FIREBASE_DB_URL') and os.environ.get('FIREBASE_SERVICE_ACCOUNT'):
        token = firebase_token()
        try:
            data['fb'] = firebase_stats(token, names)
        except Exception as e:
            data['fb'] = {'error': str(e)[:120]}
    if a.dry_run or not token:
        p = os.path.join(ROOT, '.claude', 'admin_dash.json')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('書き込まずに保存しました：' + p + ('（Firebase の設定が無いため）' if not token else ''))
        return
    fb('PUT', '/adminDash/latest', data, token=token)
    # 週ごとの要約を残す（あとで推移を見るため）
    t = data['sc']['total']; g = data['ga']['total']
    fb('PUT', '/adminDash/history/' + str(today), {'scClicks': t['clicks'], 'scImpressions': t['impressions'], 'scPosition': t['position'],
                                                   'users': g['activeUsers'], 'views': g['screenPageViews'], 'aff': data['ga']['affTotal']}, token=token)
    print('Firebase に書きました：/adminDash/latest（' + data['generatedAt'] + '）')


if __name__ == '__main__':
    main()
