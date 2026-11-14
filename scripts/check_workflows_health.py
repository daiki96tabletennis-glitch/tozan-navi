#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定期実行（GitHub Actions）が予定どおり動いているかを見る（2026-11-15〜。運営者の指示「通知や見張りの仕組みの改善」）

GitHub の定期実行は、遅れたり止まったりすることがある（リポジトリに60日動きが無いと止まる・GitHub 側の都合で飛ばされる）。
見張りや通知の仕組みが止まっても、お知らせは出ないので気づけない。そこで毎日、それぞれの定期実行の最後の実行の日時と結果を
GitHub の API で読み、予定より長く動いていない・失敗が続いているものを報告する。サイトのデータは触らない。

  python3 scripts/check_workflows_health.py --out health_report.md
  （GitHub Actions では GITHUB_TOKEN と GITHUB_REPOSITORY を使う。手元では公開の API で読む）
終了コード：知らせるものがあれば 1、無ければ 0
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request

REPO = os.environ.get('GITHUB_REPOSITORY') or 'daiki96tabletennis-glitch/tozan-navi'
# ファイル名：(名前, 何時間動いていなければ知らせるか)。予定の間隔に、遅れの分の余裕を足した長さ
WATCH = {
    'huts-update.yml': ('山小屋の定期更新（毎日）', 50),
    'huts-push.yml': ('山小屋の予約開始の通知（毎朝）', 50),
    'article-rank.yml': ('記事一覧の並び順（毎日）', 50),
    'site-check.yml': ('サイトの検証（毎週月曜・プッシュのたび）', 8 * 24 + 12),
    'admin-dashboard.yml': ('管理画面の分析（毎週月曜）', 8 * 24 + 12),
    'annual-data-check.yml': ('年次データの確認（毎月1日）', 32 * 24 + 12),
    'restriction-watch.yml': ('規制・閉鎖と定期実行の見張り（毎日）', 50),   # サイトの検証（毎週・プッシュのたび）からも見る
}
FAIL_STREAK = 2   # 予定の実行がこの回数続けて失敗したら知らせる
FAIL_RECENT = 3   # 直近10回のうち、この回数以上失敗していたら知らせる（成功と失敗が交互に続くのを見逃さないため。山小屋の定期更新が 2026-10〜11 にそうだった）


def api(path):
    req = urllib.request.Request('https://api.github.com/repos/%s/%s' % (REPO, path),
                                 headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'yamatch-health-check'})
    tok = os.environ.get('GITHUB_TOKEN')
    if tok:
        req.add_header('Authorization', 'Bearer ' + tok)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc)
    stale, failing, errors = [], [], []
    for f, (name, hours) in WATCH.items():
        try:
            runs = api('actions/workflows/%s/runs?per_page=10&event=schedule' % f).get('workflow_runs') or []
        except Exception as e:
            errors.append('%s：記録を読めなかった（%s）' % (name, str(e)[:60]))
            continue
        done = [r for r in runs if r.get('status') == 'completed']
        if not runs:
            # まだ一度も予定の実行が無い（作ったばかり）。知らせない
            continue
        last = datetime.datetime.fromisoformat(runs[0]['created_at'].replace('Z', '+00:00'))
        age = (now - last).total_seconds() / 3600
        jst = (last + datetime.timedelta(hours=9)).strftime('%m/%d %H:%M')
        if age > hours:
            stale.append('%s：最後の実行が %s（%d時間前）。止まっているかもしれない' % (name, jst, age))
        streak = 0
        for r in done:
            if r.get('conclusion') == 'failure':
                streak += 1
            else:
                break
        recent = sum(1 for r in done[:10] if r.get('conclusion') == 'failure')
        if streak >= FAIL_STREAK:
            failing.append('%s：予定の実行が%d回続けて失敗（最後 %s）— %s' % (name, streak, jst, done[0].get('html_url', '')))
        elif recent >= FAIL_RECENT:
            last_fail = next(r for r in done if r.get('conclusion') == 'failure')
            failing.append('%s：直近%d回のうち%d回失敗（最後の失敗 %s）— %s' % (
                name, min(10, len(done)), recent,
                (datetime.datetime.fromisoformat(last_fail['created_at'].replace('Z', '+00:00')) + datetime.timedelta(hours=9)).strftime('%m/%d'),
                last_fail.get('html_url', '')))
    jst_now = (now + datetime.timedelta(hours=9)).strftime('%Y-%m-%d')
    out = ['# 定期実行の見張り（%s）' % jst_now, '',
           '## 予定より長く動いていない定期実行', ''] + (['- ' + s for s in stale] or ['- なし']) + [
           '', '## 失敗が続いている定期実行', ''] + (['- ' + s for s in failing] or ['- なし']) + [
           '', '## 記録を読めなかった', ''] + (['- ' + s for s in errors] or ['- なし']) + ['']
    open(a.out, 'w', encoding='utf-8').write('\n'.join(out))
    print('\n'.join(out))
    sys.exit(1 if (stale or failing) else 0)


if __name__ == '__main__':
    main()
