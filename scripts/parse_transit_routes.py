#!/usr/bin/env python3
"""
Phase 1: trainAccessHtml → 構造化データ(trainRoutes)への変換パーサー（検証専用）。

このスクリプトは data/mountains.json を一切書き換えない。
全山の trainAccessHtml をパースし、構造化結果を
scripts/_phase1_parse_review.json に出力し、
durationMin 合計を既存の ts-time-val と突き合わせて自動検証する。

使い方:
    python3 scripts/parse_transit_routes.py
"""
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

SITE_ROOT = Path(__file__).resolve().parent.parent
MOUNTAINS_JSON = SITE_ROOT / "data" / "mountains.json"
OUT_JSON = SITE_ROOT / "scripts" / "_phase1_parse_review.json"

DEP_KEYS = ["shinjuku", "yokohama", "omiya"]

# アイコンsvg判定: バスは <rect ...rx=... /> を含む矩形(バス車体)＋circle(車輪)が特徴。
# 電車svgは電車アイコン(先頭が台形の path)。ロープウェイ/徒歩等は追加で文字列パターンで判定。
def guess_icon(method_text: str) -> str:
    if re.search(r'ロープウェイ|ケーブルカー|索道', method_text):
        return "ropeway"
    if re.search(r'徒歩', method_text):
        return "walk"
    if re.search(r'バス', method_text):
        return "bus"
    if re.search(r'タクシー', method_text):
        return "taxi"
    # デフォルトは電車（JR/私鉄各線名が入っているケースが大多数）
    return "train"


def parse_duration_to_min(text):
    """「約1時間35分」「約15分」「約2時間」等をintの分に変換。パース不能ならNone。
    check_pages.py の check_json_html_mismatch() で実績のあるパターンと同一。"""
    if not text:
        return None
    m = re.match(r'約(?:(\d+)時間)?(?:(\d+)分)?', text)
    if not m or (m.group(1) is None and m.group(2) is None):
        return None
    h = int(m.group(1)) if m.group(1) else 0
    mi = int(m.group(2)) if m.group(2) else 0
    return h * 60 + mi


def parse_route_legs(route_div):
    """1つの .ts-route-xxx 要素から legs 配列を作る。"""
    legs = []
    steps = route_div.select(":scope > .ts-step")
    for i, step in enumerate(steps):
        station_el = step.select_one(".ts-station")
        station = station_el.get_text(strip=True) if station_el else None
        method_el = step.select_one(".ts-method")
        leg = {"station": station}
        if method_el:
            # svgタグを除いた残りのテキストが「路線名 + 所要時間」
            duration_el = method_el.select_one(".ts-duration")
            duration_text = duration_el.get_text(strip=True) if duration_el else None
            # method_el全体のテキストからsvg内テキスト(無し)とduration_elテキストを除去して路線名を得る
            method_clone_text = method_el.get_text(" ", strip=True)
            if duration_text:
                # 末尾のduration_textを除去
                line_name = method_clone_text.replace(duration_text, "").strip()
            else:
                line_name = method_clone_text.strip()
            line_name = re.sub(r'\s+', ' ', line_name).strip()
            leg["method"] = {
                "icon": guess_icon(line_name),
                "line": line_name,
            }
            leg["durationMin"] = parse_duration_to_min(duration_text)
            leg["fareYen"] = None
        legs.append(leg)
    return legs


def parse_train_access_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    section = soup.select_one(".ts-section")
    if section is None:
        return None, "no_ts_section"

    result = {}

    badge_el = section.select_one(".ts-badge")
    if badge_el:
        badge_classes = badge_el.get("class", [])
        badge_type = None
        for c in badge_classes:
            if c.startswith("ts-badge-"):
                badge_type = c[len("ts-badge-"):]
        style = badge_el.get("style")
        # アイコン種別判定: チェックマーク(polyline)か警告三角(path M12 3 ...)かで分岐
        svg_el = badge_el.find("svg")
        icon = "check"
        if svg_el and svg_el.find("path"):
            icon = "warn"
        label = badge_el.get_text(strip=True)
        result["badge"] = {"type": badge_type, "style": style, "icon": icon, "label": label}
    else:
        result["badge"] = None

    line_name_el = section.select_one(".ts-line-name")
    result["lineName"] = line_name_el.get_text(strip=True) if line_name_el else None

    routes = {}
    for dep in DEP_KEYS:
        route_div = section.select_one(f".ts-route-{dep}")
        if route_div is None:
            routes[dep] = None
            continue
        legs = parse_route_legs(route_div)
        routes[dep] = {"legs": legs} if legs else None
    result["routes"] = routes

    note_el = section.select_one(".ts-note")
    result["note"] = note_el.get_text(strip=True) if note_el else None

    summary_note_el = section.select_one(".ts-summary-note")
    result["summaryNote"] = summary_note_el.get_text(strip=True) if summary_note_el else None

    links = []
    links_container = section.select_one(".ts-links")
    if links_container:
        for a in links_container.select("a[href]"):
            href = a.get("href", "")
            label = a.get_text(strip=True)
            link_type = "yahoo" if "transit.yahoo" in href else (
                "bus" if re.search(r'bus|バス', href + label) else "other"
            )
            links.append({"type": link_type, "label": label, "url": href})
    result["links"] = links

    # ts-summary内の ts-time-val / ts-fare-val (検証用に保持。スキーマ自体には含めない=導出値のため)
    summary_time = {}
    summary_fare = {}
    time_val = section.select_one(".ts-time-val")
    if time_val:
        for dep in DEP_KEYS:
            summary_time[dep] = time_val.get(f"data-{dep}")
    fare_val = section.select_one(".ts-fare-val")
    if fare_val:
        for dep in DEP_KEYS:
            summary_fare[dep] = fare_val.get(f"data-{dep}")
    result["_summary_time_val"] = summary_time
    result["_summary_fare_val"] = summary_fare

    return result, None


def main():
    mountains = json.loads(MOUNTAINS_JSON.read_text(encoding="utf-8"))

    all_results = {}
    stats = {
        "total": len(mountains),
        "no_ts_section": [],
        "parsed": 0,
        "duration_mismatch": [],
        "duration_match": 0,
        "duration_unverifiable": [],  # ts-time-valが無い(azuma/mitakesan等)、またはパース不能
        "leg_count_dist": {},
    }

    for m in mountains:
        mid = m["id"]
        html = m.get("trainAccessHtml")
        if not html:
            stats["no_ts_section"].append(mid)
            continue

        parsed, err = parse_train_access_html(html)
        if err:
            stats["no_ts_section"].append(mid)
            continue

        stats["parsed"] += 1
        all_results[mid] = parsed

        for dep in DEP_KEYS:
            route = parsed["routes"].get(dep)
            if route is None:
                continue
            n_legs = len(route["legs"])
            key = str(n_legs)
            stats["leg_count_dist"][key] = stats["leg_count_dist"].get(key, 0) + 1

            # durationMin合計 vs ts-time-val 突き合わせ
            html_time_str = parsed["_summary_time_val"].get(dep)
            if not html_time_str:
                stats["duration_unverifiable"].append({"id": mid, "dep": dep, "reason": "no_time_val"})
                continue
            html_min = parse_duration_to_min(html_time_str)
            if html_min is None:
                stats["duration_unverifiable"].append({"id": mid, "dep": dep, "reason": "unparseable_time_val"})
                continue

            # legsのdurationMin合計（Noneを含むlegがあれば加算不能=検証スキップ）
            leg_durations = [leg.get("durationMin") for leg in route["legs"] if "durationMin" in leg]
            if any(d is None for d in leg_durations):
                stats["duration_unverifiable"].append({"id": mid, "dep": dep, "reason": "leg_duration_unparseable"})
                continue
            computed_min = sum(leg_durations)

            if computed_min != html_min:
                stats["duration_mismatch"].append({
                    "id": mid, "dep": dep,
                    "html_time_val": html_time_str, "html_min": html_min,
                    "computed_min": computed_min,
                    "diff": computed_min - html_min,
                })
            else:
                stats["duration_match"] += 1

    OUT_JSON.write_text(
        json.dumps({"stats_summary": {
            "total_mountains": stats["total"],
            "no_ts_section_count": len(stats["no_ts_section"]),
            "no_ts_section_ids": stats["no_ts_section"],
            "parsed_count": stats["parsed"],
            "duration_match_count": stats["duration_match"],
            "duration_mismatch_count": len(stats["duration_mismatch"]),
            "duration_mismatches": stats["duration_mismatch"],
            "duration_unverifiable_count": len(stats["duration_unverifiable"]),
            "duration_unverifiable": stats["duration_unverifiable"],
            "leg_count_distribution": stats["leg_count_dist"],
        }, "parsed_routes": all_results}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"総山数: {stats['total']}")
    print(f"ts-section無し(除外): {len(stats['no_ts_section'])} -> {stats['no_ts_section']}")
    print(f"パース成功: {stats['parsed']}")
    print(f"所要時間合計 一致: {stats['duration_match']}")
    print(f"所要時間合計 不一致: {len(stats['duration_mismatch'])}")
    for x in stats["duration_mismatch"]:
        print(f"  - {x['id']} ({x['dep']}): html={x['html_time_val']}({x['html_min']}分) computed={x['computed_min']}分 diff={x['diff']}")
    print(f"検証不能(ts-time-val無し等): {len(stats['duration_unverifiable'])}")
    by_reason = {}
    for x in stats["duration_unverifiable"]:
        by_reason.setdefault(x["reason"], []).append(f"{x['id']}:{x['dep']}")
    for reason, items in by_reason.items():
        print(f"  - {reason}: {len(items)}件 {items[:10]}{'...' if len(items) > 10 else ''}")
    print(f"leg数分布: {stats['leg_count_dist']}")
    print(f"\n詳細結果: {OUT_JSON}")


if __name__ == "__main__":
    main()
