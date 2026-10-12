#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋の営業期間の文（例：「2026/4/27～11/3」「例年 7/上～10/中」「通年」）を、営業中かどうかを判定できる形にする。
ページ側（assets/js/huts-status.js）が、開いた日の日付と比べて「営業中／まもなく終了／期間外」を出す。

返す形（判定できない文は None）：
  {"all": true, "caveat": bool}                          … 通年営業（caveat：不定休・冬季は要確認などの但し書きあり）
  {"closed": true}                                       … 今季は休業
  {"y": 2026 または null, "r": [[開始の月, 日の早い側, 日の遅い側, 終了の月, 日の早い側, 日の遅い側], …]}
    日付がはっきり書いてあれば早い側＝遅い側。「上旬」は1〜10日、「中旬」は11〜20日、「下旬・末」は21日〜月末として幅を持たせる
    （幅の中の日は「営業中」とも「期間外」とも言い切らない）。y が null なのは「例年」の値。
"""
import calendar, re

ZEN = str.maketrans('０１２３４５６７８９／', '0123456789/')
JUN = {'上': (1, 10), '初': (1, 10), '中': (11, 20), '下': (21, 31), '末': (21, 31)}
D = r'(\d{1,2})\s*(?:/|月)\s*(?:(\d{1,2})日?|(上|初|中|下|末)旬?)'
RANGE = re.compile(D + r'[^\d～〜~\-－―か]{0,8}(?:[～〜~\-－―]|から)\s*' + D)


def _day(month, day, jun):
    if day:
        return int(day), int(day)
    a, b = JUN[jun]
    return a, min(b, calendar.monthrange(2001, month)[1])


def parse(text):
    t = (text or '').translate(ZEN)
    if not t or t == '—':
        return None
    if re.search(r'休業予定|今季休業|営業休止|休業中', t) and not RANGE.search(t):
        return {'closed': True}
    if re.match(r'\s*(?:20\d\d年(?:は|の営業：)?\s*)?(?:例年\s*)?(?:通年|年中無休)', t):
        return {'all': True, 'caveat': bool(re.search(r'不定|要確認|土・日|冬季|冬期|完全予約|休業日', t))}
    years = [int(x) for x in re.findall(r'(20\d\d)', t)]
    head = re.sub(r'（[^）]*）', '', t)                      # 括弧の中の日付（予約開始日など）は営業期間として読まない
    head = re.split(r'[＊※]|予約|テント|冬季|冬期|年末年始', head)[0]
    head = re.sub(r'20\d\d\s*(?:/|年(?:の営業)?[：:]?)\s*', '', head)     # 年の数字を月と読み違えない
    rs = []
    for m in RANGE.finditer(head):
        m1, m2 = int(m.group(1)), int(m.group(4))
        if not (1 <= m1 <= 12 and 1 <= m2 <= 12):
            continue
        a1, b1 = _day(m1, m.group(2), m.group(3))
        a2, b2 = _day(m2, m.group(5), m.group(6))
        if (m2, b2) < (m1, a1):                              # 年をまたぐ期間はここでは扱わない
            continue
        if [m1, a1, b1, m2, a2, b2] not in rs:
            rs.append([m1, a1, b1, m2, a2, b2])
    if not rs:
        return None
    return {'y': years[0] if years and not t.startswith('例年') else None, 'r': rs}
