#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""季節別装備カレンダー（4区分＋月途中の切替）の共通処理。

gearCalendar は12か月の配列。各月は次のどちらか。
  - 文字列：no_crampons / light_crampons / winter_gear / closed
  - 月の途中で変わる月だけ：{"split": true, "before": <区分>, "after": <区分>, "changeDate": <after が始まる日>}
「closed（入山不可）」は装備の段階ではなく、登山道閉鎖などで登れない期間。

スノーシュー（2026-11-17〜。運営者の指示「スノーシューが要る山と月はそう表示したい。区分は6区分」）：
データは gearCalendar の4区分のまま、山の snowshoeMonths（スノーシュー・ワカン等が要る月の番号のリスト）を別に持ち、
表示のときに組み合わせる（冬山装備＋その月 → snowshoe_winter「冬山装備＋スノーシュー」、軽アイゼン等・アイゼン不要＋その月 → snowshoe「スノーシュー等」）。
4区分を使うトップの絞り込み・診断・持ち物などは今までどおり動く。新しい2区分の凡例は、その区分がある山にだけ出す
"""
import calendar
import datetime
import html

KEYS = ('no_crampons', 'light_crampons', 'winter_gear', 'closed')
SNOW_KEYS = ('snowshoe', 'snowshoe_winter')   # 表示だけの区分（snowshoeMonths と組み合わせて作る）
LABEL = {'no_crampons': 'アイゼン不要', 'light_crampons': '軽アイゼン等', 'winter_gear': '冬山装備', 'closed': '入山不可',
         'snowshoe': 'スノーシュー等', 'snowshoe_winter': '冬山装備＋スノーシュー'}
SUB = {'light_crampons': 'チェーンスパイク・6本爪アイゼン等', 'winter_gear': '12本爪アイゼン・ピッケル等',
       'snowshoe': 'スノーシュー・ワカン等', 'snowshoe_winter': '12本爪アイゼン・ピッケル＋スノーシュー・ワカン等'}
# 色は既存のカレンダー（s-ok / s-gear / s-hard / s-closed）と同じ
CLS = {'no_crampons': 's-ok', 'light_crampons': 's-gear', 'winter_gear': 's-hard', 'closed': 's-closed',
       'snowshoe': 's-snow', 'snowshoe_winter': 's-snowh'}
COLOR = {'no_crampons': '#9cb088', 'light_crampons': '#d4c19a', 'winter_gear': '#b08868', 'closed': '#d9d5cf',
         'snowshoe': '#a8c4d8', 'snowshoe_winter': '#6e88a6'}
FROM_CLS = {v: k for k, v in CLS.items() if k in KEYS}
FROM_GEAR = {'normal': 'no_crampons', 'snow_caution': 'light_crampons', 'winter': 'winter_gear'}
NOTE = ('※装備区分は例年の目安です。積雪・凍結状況は年や時期によって大きく変わります。'
        '出発前に直近の登山記録・現地情報・天気を確認してください。「入山不可」は登山道閉鎖等の情報に基づきます。')
HINT = '月をタップすると、その月の区分を表示します。'


def from_legacy(season_calendar):
    """旧 seasonCalendar（s-ok など12個）→ gearCalendar"""
    return [FROM_CLS[c] for c in season_calendar]


def from_ssot(gear_monthly, trail_periods, gear_splits=None):
    """新構造：装備の月別（gearMonthly）と登山道の閉鎖期間（trailPeriods）→ gearCalendar。
    閉鎖が月の途中で始まる／終わる月は split にする。月の中ほどだけ閉鎖など2色で表せない月は例外にする。
    gear_splits（conditions.gearSplits）：装備の区分が月の途中で変わる月。{"10": {"before": .., "after": .., "changeDate": ..}}"""
    gear_splits = gear_splits or {}
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
            sp = gear_splits.get(str(month))
            out.append({'split': True, 'before': sp['before'], 'after': sp['after'], 'changeDate': sp['changeDate']} if sp else gear)
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


def with_snow(key, snow):
    """4区分の値と、その月にスノーシューが要るか → 表示の区分"""
    if not snow or key == 'closed':
        return key
    return 'snowshoe_winter' if key == 'winter_gear' else 'snowshoe'


def display_calendar(cal, snow_months=()):
    """gearCalendar と snowshoeMonths → 表示用の12か月（区分は6つ）"""
    sm = set(int(x) for x in (snow_months or ()))
    out = []
    for i, e in enumerate(cal):
        snow = (i + 1) in sm
        if isinstance(e, str):
            out.append(with_snow(e, snow))
        else:
            b, a = with_snow(e['before'], snow), with_snow(e['after'], snow)
            out.append(b if b == a else dict(e, before=b, after=a))
    return out


def validate_snow(cal, snow_months):
    probs = []
    for x in snow_months or ():
        if not isinstance(x, int) or not 1 <= x <= 12:
            probs.append(f'snowshoeMonths の月が不正（{x}）')
        elif cal[x - 1] == 'closed':
            probs.append(f'snowshoeMonths：{x}月は入山不可の月')
    return probs


def _full(key):
    return LABEL[key] + (f'（{SUB[key]}）' if key in SUB else '')


def detail_text(month, entry):
    """タップしたときに出す1行"""
    if isinstance(entry, str):
        return f'{month}月　{_full(entry)}'
    d = entry['changeDate']
    return f'{month}月　{month}/1〜{month}/{d - 1} {_full(entry["before"])}　／　{month}/{d}〜 {_full(entry["after"])}'


def render_calendar(cal, snow_months=()):
    """カレンダー本体＋凡例＋タップ時の表示欄＋注意書き（カードの中身）。snow_months はスノーシューが要る月"""
    cal = display_calendar(cal, snow_months)
    used = set()
    for e in cal:
        used.update([e] if isinstance(e, str) else [e['before'], e['after']])
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
        for k in KEYS + tuple(k for k in SNOW_KEYS if k in used))   # スノーシューの2区分は、その区分がある山だけ
    return (f'    <div class="calendar gcal">{"".join(cells)}</div>\n'
            f'    <div class="cal-detail" aria-live="polite">{HINT}</div>\n'
            f'    <div class="cal-legend">\n  {legend}\n</div>\n'
            f'    <p class="cal-note">{NOTE}</p>\n')
