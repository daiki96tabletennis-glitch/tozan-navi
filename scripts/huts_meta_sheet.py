#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Meta AI が毎日書き込む「山小屋の Instagram の見張り」のスプレッドシートを読み、新しい候補を運営者向けのお知らせに出す。
AIは使わない（Meta AI が書いた表を読むだけ）。データは書き換えない。

  python3 scripts/huts_meta_sheet.py --out insta_report.md     毎日（.github/workflows/huts-update.yml）

表の読み先：data/huts_meta_sheet.json の csvUrl（Google スプレッドシートを「ウェブに公開」した CSV のアドレス）。空なら何もしない。
表の列（1行目の見出し）：確認日時 / アカウント / 投稿日 / URL / 種類 / 要約 / 確度
  - 種類：予約開始 / 予約の受付状況 / 営業期間 / その他 / 該当なし（その日に該当が無かったときの1行）
  - 要約は Meta AI の要約で、原文ではない。**ここに書かれた日付をそのまま掲載に使わない**。運営者が URL を開いて原文を確かめ、
    Claude のアプリに原文を貼って登録する（huts_booking_extra.py / huts_rules.py を直す）

お知らせに出すもの（終了コード1）：
  - まだ確かめていない候補（種類が 予約開始・営業期間・予約の受付状況）で、見つけてから14日以内のもの。14日たつと出さない
  - Meta AI の記録が3日以上止まっている
確かめた候補は、data/huts_meta_seen.json の done に URL を足す（Claude のアプリで「確認済みにして」と伝える）。
"""
import argparse, csv, datetime, io, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(ROOT, 'data', 'huts_meta_sheet.json')
SEEN = os.path.join(ROOT, 'data', 'huts_meta_seen.json')
COLS = ['確認日時', 'アカウント', '投稿日', 'URL', '種類', '要約', '確度']
WANT = ('予約開始', '営業期間', '予約の受付状況')
KEEP_DAYS = 14
STALE_DAYS = 3


def jst_today():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()


def read_rows(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as r:
        text = r.read().decode('utf-8-sig', 'replace')
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return []
    head = [h.strip() for h in rows[0]]
    idx = {c: head.index(c) for c in COLS if c in head}
    if 'URL' not in idx or '種類' not in idx:
        raise ValueError('表の1行目の見出しが想定と違います（必要：%s／実際：%s）' % ('・'.join(COLS), '・'.join(head)))
    out = []
    for r in rows[1:]:
        out.append({c: (r[i].strip() if i < len(r) else '') for c, i in idx.items()})
    return out


def date_of(s):
    m = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', s or '')
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--today')
    a = ap.parse_args()
    today = datetime.date.fromisoformat(a.today) if a.today else jst_today()
    url = (json.load(open(CONF, encoding='utf-8')).get('csvUrl') or '').strip() if os.path.exists(CONF) else ''
    if not url:
        print('スプレッドシートの読み先が未設定のため、何もしません（data/huts_meta_sheet.json の csvUrl）')
        return 0
    seen = json.load(open(SEEN, encoding='utf-8')) if os.path.exists(SEEN) else {'found': {}, 'done': []}
    sns = json.load(open(os.path.join(ROOT, 'data', 'huts_sns.json'), encoding='utf-8'))['huts']
    by_acc = {}
    for v in sns.values():
        for n in v['instagram']:
            by_acc.setdefault(n.lower(), []).append(v['name'])
    lines, stale = [], None
    try:
        rows = read_rows(url)
    except Exception as e:
        lines.append('- スプレッドシートを読めませんでした：%s' % str(e)[:160])
        rows = []
    checked = [date_of(r.get('確認日時')) for r in rows if date_of(r.get('確認日時'))]
    if rows and (not checked or (today - max(checked)).days >= STALE_DAYS):
        stale = '- Meta AI の記録が止まっています（最後の記録：%s）。Meta AI の毎日の確認が動いているか確かめてください' % (max(checked) if checked else '日付なし')
    for r in rows:
        kind, u = r.get('種類', ''), r.get('URL', '')
        if kind not in WANT or not re.match(r'https://(www\.)?instagram\.com/', u):
            continue
        if u not in seen['found']:
            seen['found'][u] = today.isoformat()
    pend = []
    for r in rows:
        u = r.get('URL', '')
        if r.get('種類') not in WANT or u not in seen['found'] or u in seen['done']:
            continue
        if (today - datetime.date.fromisoformat(seen['found'][u])).days > KEEP_DAYS:
            continue
        acc = (r.get('アカウント') or '').lstrip('@').lower()
        huts = '・'.join(by_acc.get(acc, [])) or '（一覧に無いアカウント）'
        pend.append((0 if r['種類'] == '予約開始' else 1, '- 【%s】%s（@%s）投稿日 %s：%s〔%s。Meta AI の要約〕\n    %s' % (
            r['種類'], huts, acc, r.get('投稿日') or '不明', (r.get('要約') or '')[:120], r.get('確度') or '確度不明', u)))
    json.dump(seen, open(SEEN, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    pend.sort(key=lambda p: p[0])
    text = '# 山小屋の Instagram の見張り（Meta AI・%s）\n\n' % today
    if pend:
        text += '## まだ確かめていない候補（URLを開いて原文を確かめ、Claude のアプリに貼って登録）\n\n' + '\n'.join(p[1] for p in pend) + '\n\n'
    if stale or lines:
        text += '## 見張りの状態\n\n' + '\n'.join(([stale] if stale else []) + lines) + '\n'
    if not pend and not stale and not lines:
        text += '## まだ確かめていない候補\n\n- なし\n'
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(text)
    print(text)
    return 1 if (pend or stale or lines) else 0


if __name__ == '__main__':
    sys.exit(main())
