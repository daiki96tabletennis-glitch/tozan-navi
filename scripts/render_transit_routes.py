#!/usr/bin/env python3
"""
Phase 2: 構造化データ(trainRoutes相当)から .ts-section HTML を再生成するレンダラー（Python版）。

render_ts_section(parsed, mountain) が旧来の trainAccessHtml と「視覚的に同等」な
HTMLを返す。合計所要時間・運賃は Phase 1 の検証結果に基づき、構造化データ側の
レグ合計からではなく、mountain の trainTimeXxx/fareXxx/transfersXxx（既存の
正データ）から埋め込む。

このスクリプト単体は data/mountains.json を変更しない。
"""
import html as html_escape_mod
import re

DEP_LABELS = {"shinjuku": "新宿発", "yokohama": "横浜発", "omiya": "大宮発"}
DEP_ORDER = ["shinjuku", "omiya", "yokohama"]  # 既存HTMLでの出現順(新宿→大宮→横浜)に合わせる

ICON_SVG = {
    "train": '<svg width="14" height="14" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><path d="M2 7 H14 L20 11.5 V17 H2 Z" fill="currentColor"/><rect x="4" y="9.5" width="3" height="3" fill="white"/><rect x="9" y="9.5" width="3" height="3" fill="white"/><line x1="1" y1="19.5" x2="21" y2="19.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    "bus": '<svg width="14" height="14" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><rect x="1.5" y="7" width="21" height="9.5" rx="1.5" fill="currentColor"/><rect x="3.5" y="9" width="4" height="4" fill="white"/><rect x="9" y="9" width="4" height="4" fill="white"/><rect x="15" y="9" width="5" height="4" fill="white"/><circle cx="6" cy="18.5" r="2.3" fill="currentColor"/><circle cx="17" cy="18.5" r="2.3" fill="currentColor"/></svg>',
    "walk": '<svg width="14" height="14" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="13" cy="4" r="1.8" fill="currentColor"/><path d="M11 21 L13 15 L10 12 L11 8 L15 10 L17 13 M13 15 L16 20 M11 8 L8 11"/></svg>',
    "ropeway": '<svg width="14" height="14" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><rect x="1.5" y="7" width="21" height="9.5" rx="1.5" fill="currentColor"/><rect x="3.5" y="9" width="4" height="4" fill="white"/><rect x="9" y="9" width="4" height="4" fill="white"/><rect x="15" y="9" width="5" height="4" fill="white"/><circle cx="6" cy="18.5" r="2.3" fill="currentColor"/><circle cx="17" cy="18.5" r="2.3" fill="currentColor"/></svg>',
    "taxi": '<svg width="14" height="14" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><rect x="1.5" y="7" width="21" height="9.5" rx="1.5" fill="currentColor"/><rect x="3.5" y="9" width="4" height="4" fill="white"/><rect x="9" y="9" width="4" height="4" fill="white"/><rect x="15" y="9" width="5" height="4" fill="white"/><circle cx="6" cy="18.5" r="2.3" fill="currentColor"/><circle cx="17" cy="18.5" r="2.3" fill="currentColor"/></svg>',
}

TITLE_ICON_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px"><path d="M2 7 H14 L20 11.5 V17 H2 Z" fill="currentColor"/><rect x="4" y="9.5" width="3" height="3" fill="white"/><rect x="9" y="9.5" width="3" height="3" fill="white"/><line x1="1" y1="19.5" x2="21" y2="19.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'

BADGE_CHECK_SVG = '<svg class="rec-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
BADGE_WARN_SVG = '<svg width="13" height="13" viewBox="0 0 24 24" style="vertical-align:-2px;margin-right:3px" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 L22 20 H2 Z"/><line x1="12" y1="9" x2="12" y2="14"/><line x1="12" y1="17" x2="12" y2="17.1"/></svg>'


def esc(s):
    if s is None:
        return ""
    return html_escape_mod.escape(str(s), quote=True)


def format_duration(minutes):
    if minutes is None:
        return None
    h, m = divmod(int(minutes), 60)
    if h and m:
        return f"約{h}時間{m}分"
    if h:
        return f"約{h}時間"
    return f"約{m}分"


def render_badge(badge):
    if not badge:
        return ""
    if badge.get("type"):
        cls = f'ts-badge ts-badge-{esc(badge["type"])}'
        style_attr = ""
        icon_svg = BADGE_CHECK_SVG
    else:
        cls = "ts-badge"
        style_attr = f' style="{esc(badge.get("style") or "")}"' if badge.get("style") else ""
        icon_svg = BADGE_WARN_SVG if badge.get("icon") == "warn" else BADGE_CHECK_SVG
    return f'<span class="{cls}"{style_attr}>{icon_svg}{esc(badge.get("label"))}</span>'


def render_leg(leg, is_last):
    station = esc(leg.get("station"))
    node_cls = "ts-node ts-node-last" if is_last else "ts-node"
    parts = [f'<div class="ts-step"><div class="{node_cls}"><div class="ts-station">{station}</div></div>']
    method = leg.get("method")
    if method:
        icon_svg = ICON_SVG.get(method.get("icon"), ICON_SVG["train"])
        line = esc(method.get("line"))
        dur_text = format_duration(leg.get("durationMin"))
        dur_span = f'<span class="ts-duration">{esc(dur_text)}</span>' if dur_text else ""
        parts.append(
            f'<div class="ts-arrow"><span class="ts-method">{icon_svg}{line}　{dur_span}</span></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def render_route(legs):
    return "".join(render_leg(leg, i == len(legs) - 1) for i, leg in enumerate(legs))


def render_link(link):
    href = esc(link.get("url"))
    label = esc(link.get("label"))
    link_type = link.get("type")
    cls = "ts-link"
    icon_svg = ICON_SVG["train"]
    if link_type == "bus":
        cls += " ts-link-bus"
        icon_svg = ICON_SVG["bus"]
    else:
        cls += " ts-link-yahoo"
        icon_svg = ICON_SVG["train"]
    return f'<a href="{href}" target="_blank" rel="noopener" class="{cls}">{icon_svg}{label}</a>'


def render_ts_section(parsed, mountain):
    """
    parsed: parse_transit_routes.parse_train_access_html() の戻り値 (badge/lineName/routes/note/summaryNote/links)
    mountain: mountains.json の1エントリ(dict)。trainTimeXxx/fareXxx/transfersXxxを使う。
    """
    routes = parsed["routes"]
    available_deps = [d for d in DEP_ORDER if routes.get(d)]
    if not available_deps:
        return ""

    header = (
        '<div class="ts-header">'
        f'<div class="ts-title">{TITLE_ICON_SVG}電車・バスでのアクセス</div>'
        f'{render_badge(parsed.get("badge"))}'
        "</div>"
    )

    line_name_html = ""
    if parsed.get("lineName"):
        line_name_html = f'<div class="ts-line-name">{esc(parsed["lineName"])}</div>'

    route_divs = []
    default_dep = available_deps[0]
    for dep in available_deps:
        legs = routes[dep]["legs"]
        display = "" if dep == default_dep else ' style="display:none"'
        route_divs.append(
            f'<div class="ts-route ts-route-{dep}"{display}>{render_route(legs)}</div>'
        )

    summary_html = ""
    field_map = {
        "shinjuku": ("trainTimeShinjuku", "fareShinjuku"),
        "yokohama": ("trainTimeYokohama", "fareYokohama"),
        "omiya": ("trainTimeOmiya", "fareOmiya"),
    }
    has_time_data = any(mountain.get(field_map[d][0]) is not None for d in available_deps)
    if has_time_data:
        toggle_btns = "".join(
            f'<button type="button" class="ts-dep-btn{" active" if d == default_dep else ""}" '
            f'data-key="{d}" onclick="changeDepTrain(\'{d}\')">{DEP_LABELS[d]}</button>'
            for d in available_deps
        )
        time_attrs = "".join(
            f' data-{d}="{esc(format_duration(mountain.get(field_map[d][0])))}"'
            for d in available_deps if mountain.get(field_map[d][0]) is not None
        )
        default_time = esc(format_duration(mountain.get(field_map[default_dep][0])))
        fare_attrs = "".join(
            f' data-{d}="{esc(format_fare(mountain.get(field_map[d][1])))}"'
            for d in available_deps if mountain.get(field_map[d][1]) is not None
        )
        default_fare = esc(format_fare(mountain.get(field_map[default_dep][1])))
        summary_note_html = (
            f'<div class="ts-summary-note">{esc(parsed["summaryNote"])}</div>'
            if parsed.get("summaryNote") else ""
        )
        summary_html = (
            '<div class="ts-summary">'
            f'<div class="ts-dep-toggle">{toggle_btns}</div>'
            f'<span class="ts-time-val"{time_attrs}>{default_time}</span>'
            f'<span class="ts-fare-val"{fare_attrs}>{default_fare}</span>'
            f'{summary_note_html}'
            "</div>"
        )

    note_html = f'<div class="ts-note">{esc(parsed["note"])}</div>' if parsed.get("note") else ""

    links_html = ""
    if parsed.get("links"):
        links_html = '<div class="ts-links">' + "".join(render_link(l) for l in parsed["links"]) + "</div>"

    return (
        '<div class="ts-section">'
        f'{header}'
        f'{line_name_html}'
        f'{"".join(route_divs)}'
        f'{summary_html}'
        f'{note_html}'
        f'{links_html}'
        "</div>"
    )


def format_fare(yen):
    if yen is None:
        return None
    return f"片道約{yen:,}円"


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from parse_transit_routes import parse_train_access_html

    site_root = Path(__file__).resolve().parent.parent
    mountains = json.loads((site_root / "data" / "mountains.json").read_text(encoding="utf-8"))
    m = next(x for x in mountains if x["id"] == (sys.argv[1] if len(sys.argv) > 1 else "kumotori"))
    parsed, err = parse_train_access_html(m["trainAccessHtml"])
    print(render_ts_section(parsed, m))
