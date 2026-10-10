#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋の公式ページを取得し、営業期間・予約・定員に関わる行だけを取り出す共通処理。
update_huts.py（定期更新）と、人が確認するときの下調べの両方で使う。"""
import hashlib, html, re, subprocess

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
KEY_RE = re.compile(r'予約|受付|営業|開設|定員|収容|休業|小屋開け|小屋閉め')
DATE_RE = re.compile(r'\d{1,2}\s*[月/／]\s*\d{1,2}|20\d\d年|令和\s*\d+年|\d+\s*[名人]|通年|[上中下]旬')


def fetch_text(url, timeout=25):
    """ページの本文（タグを除いた行のリスト）。取得できなければ None"""
    try:
        raw = subprocess.run(['curl', '-s', '-L', '-k', '-m', str(timeout), '-A', UA, url], capture_output=True).stdout
    except Exception:
        return None
    if not raw or raw[:5] == b'%PDF-':
        return None
    text = None
    m = re.search(br'charset=["\']?([A-Za-z0-9_\-]+)', raw[:3000])
    encs = ([m.group(1).decode('ascii', 'ignore')] if m else []) + ['utf-8', 'cp932', 'euc-jp']
    for enc in encs:
        try:
            text = raw.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if text is None:
        text = raw.decode('utf-8', 'replace')
    text = re.sub(r'(?is)<(script|style|noscript)\b.*?</\1>', ' ', text)
    text = re.sub(r'(?s)<[^>]+>', '\n', text)
    lines = [re.sub(r'\s+', ' ', html.unescape(l)).strip() for l in text.split('\n')]
    return [l for l in lines if l]


def key_lines(lines, limit=400):
    """営業・予約・定員に関わり、日付や人数を含む行だけ（重複を除く）"""
    out = []
    for l in lines or []:
        if 4 <= len(l) <= limit and KEY_RE.search(l) and DATE_RE.search(l) and l not in out:
            out.append(l)
    return out


def digest(lines):
    return hashlib.sha256('\n'.join(sorted(set(lines))).encode('utf-8')).hexdigest()[:16]
