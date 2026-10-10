#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋まとめ（β）の定期更新。AIは使わず、決まった手順だけで動く。

自動で更新するもの
  ・長野県のポータルに載っている小屋：営業期間・予約の区分（出典の原文 openText）を取り直す
  ・山と溪谷オンラインの山小屋リストに載っている小屋：営業期間を取り直す
自動では書き換えないもの（人が確認して書いた値）
  ・予約の開始日・予約方法・規模。ただし次のときは、ページ上で「確認中」に切り替える：
      - 出典の原文が、確認したときから変わった（bookingStale）
      - 予約情報を確認した公式ページの、予約・受付に関わる行が変わった（officialChanged）
    切り替わった小屋は、人が公式サイトを見て scripts の表を直し、--accept で「確認済み」に戻す。

使い方
  python3 scripts/update_huts.py            # 取り直して data/huts.json と huts/index.html を更新。変化を報告
  python3 scripts/update_huts.py --accept   # いまの内容を「確認済み」として記録する（人が確認したあとに実行）
  python3 scripts/update_huts.py --out report.md
"""
import argparse, datetime, html, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import huts_fetch as hf

HUTS = os.path.join(ROOT, 'data', 'huts.json')
VERIFIED = os.path.join(ROOT, 'data', 'huts_verified.json')
BOOK_RE = re.compile(r'予約|受付')


def yamakei_periods(url):
    """山と溪谷オンラインの山小屋リスト → {小屋名: 開設期間}"""
    raw = subprocess.run(['curl', '-s', '-L', '-m', '40', '-A', hf.UA, url], capture_output=True).stdout.decode('utf-8', 'replace')
    t = re.sub(r'(?is)<(script|style)\b.*?</\1>', '', raw)
    out = {}
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>', t, flags=re.S):
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, flags=re.S)
        if len(cells) < 4:
            continue
        name = re.sub(r'<a\b.*?</a>', '', cells[0], flags=re.S)
        name = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', name))).strip()
        period = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', cells[1]))).strip()
        if name and period and name not in ('開設期間', '山小屋'):
            out[name] = period
    return out


def booking_digest(url):
    """公式ページの、予約・受付に関わる行の要約。取得できなければ None"""
    lines = [l for l in hf.key_lines(hf.fetch_text(url)) if BOOK_RE.search(l)]
    return hf.digest(lines) if lines else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--accept', action='store_true')
    ap.add_argument('--out')
    ap.add_argument('--scheduled', action='store_true', help='毎日の定期実行用。今日やる分だけ見に行く')
    ap.add_argument('--today', help='日付を指定して試す（YYYY-MM-DD）')
    a = ap.parse_args()
    day = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()
    today = day.isoformat()
    before = {h['id']: h for h in json.load(open(HUTS, encoding='utf-8'))['huts']} if os.path.exists(HUTS) else {}
    import huts_auto
    # 見に行く頻度：毎月1日は全部。一覧の出典（長野県のポータルなど）は、更新される4〜6月だけ3日に1回。
    # 小屋ごとの公式サイトは、発表が出そうな期間だけ3日に1回（huts_auto.due_huts）。それ以外の日は何もしない。
    full = (not a.scheduled) or day.day == 1
    lists_due = full or (day.month in (4, 5, 6) and day.toordinal() % 3 == 0)
    only = None
    if not full:
        only = huts_auto.due_huts(list(before.values()), day)
        if not lists_due and not only:
            print('今日は見に行く対象がありません（%s）' % today)
            return
    if lists_due:
        # 1) 長野県のポータルを取り直して作り直す
        import build_huts_from_nagano
        build_huts_from_nagano.main()
    data = json.load(open(HUTS, encoding='utf-8'))
    huts = data['huts']
    ver = json.load(open(VERIFIED, encoding='utf-8')) if os.path.exists(VERIFIED) else {'openText': {}, 'digest': {}}
    report = []
    # 2) 山と溪谷オンラインのリストから、営業期間を取り直す
    yk = {}
    for url in (sorted({h['sourceUrl'] for h in huts if 'yamakei-online.com/yama-ya/' in (h.get('sourceUrl') or '')}) if lists_due else []):
        try:
            yk[url] = yamakei_periods(url)
        except Exception as e:
            report.append('- 山小屋リストを取得できませんでした：%s（%s）' % (url, str(e)[:60]))
    for h in huts:
        per = (yk.get(h.get('sourceUrl')) or {}).get(h['name'])
        if per and '公式サイト' not in (h.get('openText') or '') and not (h.get('openText') or '').startswith('例年'):
            h['openText'] = '2026年の営業：' + per if '2026' in h.get('openText', '') else h['openText']
            h['periodAuto'] = per
    # 3) 予約情報を確認した公式ページの変化
    urls = sorted({h['bookingSourceUrl'] for h in huts if h.get('bookingSourceUrl') and h.get('bookingStart')}) if full else []
    digests = {}
    for u in urls:
        digests[u] = booking_digest(u)
    if a.accept or not os.path.exists(VERIFIED):
        ver = {'acceptedAt': today,
               'openText': {h['id']: h.get('openText') for h in huts},
               'digest': {u: d for u, d in digests.items() if d}}
        json.dump(ver, open(VERIFIED, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        report.append('- いまの内容を「確認済み」として記録しました（%d軒）' % len(huts))
    for h in huts:
        old_text = ver['openText'].get(h['id'])
        if old_text is not None and old_text != h.get('openText'):
            report.append('- %s：出典の記載が変わりました\n    前：%s\n    今：%s' % (h['name'], old_text, h.get('openText')))
            if h.get('bookingStart') or h.get('bookingMethods'):
                h['bookingStale'] = True
        u = h.get('bookingSourceUrl')
        if u and h.get('bookingStart') and digests.get(u) and ver['digest'].get(u) and digests[u] != ver['digest'][u]:
            h['officialChanged'] = (before.get(h['id']) or {}).get('officialChanged') or today
            report.append('- %s：予約情報を確認した公式ページの記載が変わりました（%s）' % (h['name'], u))
    # 4) 公式サイト・予約サイトからの自動取得（huts_auto.py）。確認を通った値だけが入る
    report += huts_auto.run(huts, today=day, only=only, previous=before)
    if only:
        report.insert(0, '- 集中して見に行った小屋：' + '、'.join(sorted(only)))
    json.dump(data, open(HUTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'gen_huts_page.py')], check=True)
    text = '# 山小屋まとめの定期更新（%s）\n\n' % today + ('\n'.join(report) if report else '- 変化はありませんでした') + '\n'
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(text)
    print(text)


if __name__ == '__main__':
    main()
