#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋の Instagram の投稿の文を、Meta の公式の読み取り（Instagram Graph API の Business Discovery）で読む。
ログインした画面を自動で読むのではなく、運営者の Instagram プロアカウントに Meta が発行した鍵を使う（利用規約の範囲内）。

使うもの（GitHub の Secrets。どちらかが無いあいだは何もしない）：
  IG_USER_ID   … 運営者の Instagram プロアカウントの ID（数字）
  IG_TOKEN     … 読み取り用の鍵（アクセストークン）
読む相手：data/huts_sns.json（公式サイトに載っている、山小屋の Instagram のアカウント）

読めるのは、ビジネス・クリエイター設定の公開アカウントの投稿だけ。個人設定のアカウントは読めない（報告に出す）。
読んだ投稿の文は、公式サイトの文と同じように huts_patterns.py の型に当て、huts_auto.py の確認
（年が今年か来年・前の日付から45日以内・候補が1つ）を通ったものだけを使う。

  python3 scripts/huts_instagram.py <ユーザー名>     1アカウントの最近の投稿を表示する（鍵の確認用）
"""
import datetime, json, os, re, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://graph.facebook.com/v21.0/'
_cache = {}
problems = []          # 読めなかったアカウントと理由（huts_auto.py が報告に出す）


def enabled():
    return bool(os.environ.get('IG_USER_ID') and os.environ.get('IG_TOKEN'))


def posts(username, limit=25):
    """アカウントの最近の投稿：[{'text', 'date', 'url'}]。読めなければ []（理由は problems に積む）"""
    if not enabled():
        return []
    if username in _cache:
        return _cache[username]
    fields = 'business_discovery.username(%s){username,media.limit(%d){caption,timestamp,permalink}}' % (username, limit)
    url = API + os.environ['IG_USER_ID'] + '?' + urllib.parse.urlencode({'fields': fields, 'access_token': os.environ['IG_TOKEN']})
    out = []
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            d = json.load(r)
        for m in (((d.get('business_discovery') or {}).get('media') or {}).get('data') or []):
            if m.get('caption'):
                out.append({'text': m['caption'], 'date': (m.get('timestamp') or '')[:10], 'url': m.get('permalink') or ''})
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get('error', {}).get('message', '')
        except Exception:
            msg = ''
        problems.append((username, '%s %s' % (e.code, msg[:120])))      # 個人設定のアカウント・名前の変更・鍵の期限切れなど
    except Exception as e:
        problems.append((username, str(e)[:120]))
    _cache[username] = out
    return out


def hut_lines(hut_id, today=None, days=240):
    """その小屋のアカウントの、最近（days 日以内）の投稿の文を行に分けたもの：[(行, 投稿のURL)]"""
    if not enabled():
        return []
    path = os.path.join(ROOT, 'data', 'huts_sns.json')
    if not os.path.exists(path):
        return []
    info = json.load(open(path, encoding='utf-8'))['huts'].get(hut_id) or {}
    today = today or datetime.date.today()
    out = []
    for name in info.get('instagram') or []:
        for p in posts(name):
            try:
                if (today - datetime.date.fromisoformat(p['date'])).days > days:
                    continue
            except ValueError:
                pass
            for line in re.split(r'[\r\n]+', p['text']):
                line = line.strip()
                if line:
                    out.append((line, p['url']))
    return out


if __name__ == '__main__':
    if not enabled():
        print('IG_USER_ID と IG_TOKEN が未設定です')
        sys.exit(1)
    for p in posts(sys.argv[1], limit=10):
        print(p['date'], p['url'])
        print('   ', p['text'][:200].replace('\n', ' / '))
    for u, why in problems:
        print('読めませんでした：', u, why)
