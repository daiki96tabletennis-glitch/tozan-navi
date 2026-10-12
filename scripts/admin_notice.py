#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""運営者向けのお知らせ（data/admin_notices.json）を作る。GitHub Actions の3つの定期実行から呼ぶ。

  python3 scripts/admin_notice.py --kind annual    --report annual_report.md --code 1
  python3 scripts/admin_notice.py --kind huts      --report huts_report.md
  python3 scripts/admin_notice.py --kind sitecheck --report check_pages_report.txt --code 0

- 種類ごとに最新の1件だけを持つ（annual＝毎月の年次データ確認／huts＝山小屋の定期更新／sitecheck＝サイトの検証）
- 報告の文を、見出しと箇条書きに分けてそのまま入れる（要約・書き換えはしない。AIは使わない）
- 中身が前回と同じなら書き換えない（毎回コミットが出るのを防ぐ）。書き換えたときは終了コード0で「更新」と出す
- 表示はマイページ（assets/js/admin-notices.js）。運営者の端末だけに出すが、このファイル自体は公開されるので、
  保守の情報（期限切れ・確認待ち・検証の異常）以外は入れない
"""
import argparse, datetime, hashlib, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'admin_notices.json')
TITLE = {'annual': '毎月の年次データ確認', 'huts': '山小屋の定期更新', 'sitecheck': 'サイトの検証'}
NEXT = {'annual': 'Claude のアプリで「月次更新して」と伝えてください。',
        'huts': '候補や変更のあった小屋を公式サイトで確かめ、Claude のアプリで反映を頼んでください。',
        'sitecheck': 'Claude のアプリで「check_pages.py の異常を直して」と伝えてください。'}
EMPTY = re.compile(r'^(?:-\s*)?(?:なし|異常なし|変化はありませんでした|（--no-fetch のため未確認）)$')
MAX_LINES, MAX_CHARS = 60, 240


def parse(text, kind):
    """報告の文 → [{heading, lines}]。中身の無い見出し・（0件）の見出し・参考の見出しは落とす"""
    secs, cur = [], {'heading': '', 'lines': []}
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith('# ') and not secs and not cur['lines']:
            continue                                   # 報告の題名
        if line.startswith('## '):
            secs.append(cur)
            cur = {'heading': line[3:].strip(), 'lines': []}
        elif re.match(r'^\s*[-・]\s+', line) and not line.startswith(' '):
            cur['lines'].append(re.sub(r'^\s*[-・]\s+', '', line))
        elif cur['lines'] and line.startswith(' '):
            cur['lines'][-1] += ' ／ ' + line.strip()    # 箇条書きの続きの行（前：… 今：…）
        else:
            cur['lines'].append(line.strip())
    secs.append(cur)
    out = []
    for s in secs:
        lines = [l for l in s['lines'] if not EMPTY.match(l)]
        if not lines or '（0件）' in s['heading'] or s['heading'].startswith('参考'):
            continue
        if kind == 'sitecheck' and not re.match(r'^\d+\.', s['heading']):
            continue                                   # 件数の一覧など、セクション以外は入れない
        out.append({'heading': s['heading'], 'lines': [l[:MAX_CHARS] for l in lines]})
    n = 0
    for s in out:                                      # 長すぎる報告は切り、切ったことを書く
        room = max(0, MAX_LINES - n)
        if len(s['lines']) > room:
            rest = len(s['lines']) - room
            s['lines'] = s['lines'][:room] + ['ほか%d件（全文は実行結果のページ）' % rest]
        n += len(s['lines'])
    return [s for s in out if s['lines']]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kind', required=True, choices=sorted(TITLE))
    ap.add_argument('--report', required=True)
    ap.add_argument('--code', type=int, default=None, help='確認スクリプトの終了コード（0＝異常なし）')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    if not os.path.exists(a.report):
        print('報告のファイルがありません（今回は実行なし）：' + a.report)
        return
    secs = parse(open(a.report, encoding='utf-8', errors='replace').read(), a.kind)
    if a.kind == 'huts':
        # 「集中して見に行った小屋」だけの報告は、知らせる中身が無い
        real = [s for s in secs if [l for l in s['lines'] if not l.startswith('集中して見に行った小屋')]]
        if not real:
            print('山小屋：知らせる変化はありません（前のお知らせを残します）')
            return
        needs = True
    else:
        needs = bool(a.code) if a.code is not None else bool(secs)
        if not needs:
            secs = []
    data = {'items': []}
    if os.path.exists(a.out):
        data = json.load(open(a.out, encoding='utf-8'))
    old = [i for i in data['items'] if i['kind'] == a.kind]
    body = json.dumps([needs, secs], ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha1(body.encode('utf-8')).hexdigest()[:10]
    if old and old[0].get('digest') == digest:
        print('%s：前回と同じ内容です（書き換えません）' % TITLE[a.kind])
        return
    today = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d')
    item = {'id': a.kind + '-' + today + '-' + digest, 'kind': a.kind, 'title': TITLE[a.kind], 'date': today,
            'needsAction': needs, 'digest': digest, 'sections': secs,
            'next': NEXT[a.kind] if needs else None, 'url': None}
    if os.environ.get('GITHUB_REPOSITORY') and os.environ.get('GITHUB_RUN_ID'):
        item['url'] = '%s/%s/actions/runs/%s' % (os.environ.get('GITHUB_SERVER_URL', 'https://github.com'),
                                                 os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_RUN_ID'])
    order = ['annual', 'huts', 'sitecheck']
    data['items'] = sorted([i for i in data['items'] if i['kind'] != a.kind] + [item], key=lambda i: order.index(i['kind']))
    data['updatedAt'] = today
    json.dump(data, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%s：お知らせを更新しました（%s・%d項目）' % (TITLE[a.kind], '対応が必要' if needs else '異常なし', sum(len(s['lines']) for s in secs)))


if __name__ == '__main__':
    main()
