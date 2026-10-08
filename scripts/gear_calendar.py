#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""季節別装備カレンダー（4区分＋月途中の切替）の共通処理。

gearCalendar は12か月の配列。各月は次のどちらか。
  - 文字列：no_crampons / light_crampons / winter_gear / closed
  - 月の途中で変わる月だけ：{"split": true, "before": <区分>, "after": <区分>, "changeDate": <after が始まる日>}
「closed（入山不可）」は装備の段階ではなく、登山道閉鎖などで登れない期間。
"""
import calendar
import datetime
import html

KEYS = ('no_crampons', 'light_crampons', 'winter_gear', 'closed')
LABEL = {'no_crampons': 'アイゼン不要', 'light_crampons': '軽アイゼン等', 'winter_gear': '冬山装備', 'closed': '入山不可'}
SUB = {'light_crampons': 'チェーンスパイク・6本爪アイゼン等', 'winter_gear': '12本爪アイゼン・ピッケル等'}
# 色は既存のカレンダー（s-ok / s-gear / s-hard / s-closed）と同じ
CLS = {'no_crampons': 's-ok', 'light_crampons': 's-gear', 'winter_gear': 's-hard', 'closed': 's-closed'}
COLOR = {'no_crampons': '#9cb088', 'light_crampons': '#d4c19a', 'winter_gear': '#b08868', 'closed': '#d9d5cf'}
FROM_CLS = {v: k for k, v in CLS.items()}
FROM_GEAR = {'normal': 'no_crampons', 'snow_caution': 'light_crampons', 'winter': 'winter_gear'}
NOTE = ('※装備区分は例年の目安です。積雪・凍結状況は年や時期によって大きく変わります。'
        '出発前に直近の登山記録・現地情報・天気を確認してください。「入山不可」は登山道閉鎖等の情報に基づきます。')
HINT = '月をタップすると、その月の区分を表示します。'


def from_legacy(season_calendar):
    """旧 seasonCalendar（s-ok など12個）→ gearCalendar"""
    return [FROM_CLS[c] for c in season_calendar]


def from_ssot(gear_monthly, trail_periods):
    """新構造：装備の月別（gearMonthly）と登山道の閉鎖期間（trailPeriods）→ gearCalendar。
    閉鎖が月の途中で始まる／終わる月は split にする。月の中ほどだけ閉鎖など2色で表せない月は例外にする。"""
    out = []
    for i in range(12):
        month = i + 1
        gear = FROM_GEAR[gear_monthly[i]]
        closed_days = set()
        ndays = 31
        for p in trail_periods or []:
            if p.get('status') != 'closed':
                continue
            a = datetime.date.fromisoformat(p['from'])
            b = datetime.date.fromisoformat(p['to'])
            ndays = calendar.monthrange(a.year, month)[1]
            for d in range(1, ndays + 1):
                if a <= datetime.date(a.year, month, d) <= b:
                    closed_days.add(d)
        if not closed_days:
            out.append(gear)
        elif len(closed_days) >= ndays:
            out.append('closed')
        elif closed_days == set(range(1, max(closed_days) + 1)):
            out.append({'split': True, 'before': 'closed', 'after': gear, 'changeDate': max(closed_days) + 1})
        elif closed_days == set(range(min(closed_days), ndays + 1)):
            out.append({'split': True, 'before': gear, 'after': 'closed', 'changeDate': min(closed_days)})
        else:
            raise ValueError(f'{month}月：閉鎖期間が月の中ほどにあり、2色では表せない')
    return out


def validate(cal):
    """問題点の文字列を返す（無ければ空のリスト）"""
    probs = []
    if not isinstance(cal, list) or len(cal) != 12:
        return ['gearCalendar が12か月分ない']
    for i, e in enumerate(cal):
        if isinstance(e, str):
            if e not in KEYS:
                probs.append(f'{i+1}月の区分が不正（{e}）')
        elif isinstance(e, dict):
            if e.get('split') is not True or e.get('before') not in KEYS or e.get('after') not in KEYS:
                probs.append(f'{i+1}月の切替データが不正')
            elif e['before'] == e['after']:
                probs.append(f'{i+1}月：切替の前後が同じ区分')
            elif not isinstance(e.get('changeDate'), int) or not (2 <= e['changeDate'] <= 31):
                probs.append(f'{i+1}月：切替日（changeDate）が不正')
        else:
            probs.append(f'{i+1}月の区分が未設定')
    return probs


def _full(key):
    return LABEL[key] + (f'（{SUB[key]}）' if key in SUB else '')


def detail_text(month, entry):
    """タップしたときに出す1行"""
    if isinstance(entry, str):
        return f'{month}月　{_full(entry)}'
    d = entry['changeDate']
    return f'{month}月　{month}/1〜{month}/{d - 1} {_full(entry["before"])}　／　{month}/{d}〜 {_full(entry["after"])}'


def render_calendar(cal):
    """カレンダー本体＋凡例＋タップ時の表示欄＋注意書き（カードの中身）"""
    cells = []
    for i, e in enumerate(cal):
        tip = html.escape(detail_text(i + 1, e), quote=True)
        if isinstance(e, str):
            cls, style = 'cal-b ' + CLS[e], ''
        else:
            cls = 'cal-b cal-split'
            style = f' style="--ga:{COLOR[e["before"]]};--gb:{COLOR[e["after"]]}"'
        cells.append(f'<div class="cal-m"><div class="cal-l">{i+1}</div>'
                     f'<button type="button" class="{cls}"{style} data-tip="{tip}" aria-label="{tip}"></button></div>')
    legend = ''.join(
        f'<div class="leg"><div class="leg-dot" style="background:{COLOR[k]}"></div>{LABEL[k]}'
        + (f'<small>{SUB[k]}</small>' if k in SUB else '') + '</div>'
        for k in KEYS)
    return (f'    <div class="calendar gcal">{"".join(cells)}</div>\n'
            f'    <div class="cal-detail" aria-live="polite">{HINT}</div>\n'
            f'    <div class="cal-legend">\n  {legend}\n</div>\n'
            f'    <p class="cal-note">{NOTE}</p>\n')
