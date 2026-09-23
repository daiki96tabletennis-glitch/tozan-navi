#!/usr/bin/env python3
"""
Phase 2: 新レンダラー(render_transit_routes.render_ts_section)の出力が
既存 trainAccessHtml と視覚的に同等か、全131山で自動検証する。
data/mountains.json は変更しない。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_transit_routes import parse_train_access_html
from render_transit_routes import render_ts_section

SITE_ROOT = Path(__file__).resolve().parent.parent
MOUNTAINS_JSON = SITE_ROOT / "data" / "mountains.json"
OUT_JSON = SITE_ROOT / "scripts" / "_phase2_compare_review.json"


def diff_parsed(orig, new, mid):
    problems = []
    if (orig.get("badge") is None) != (new.get("badge") is None):
        problems.append("badge presence differs")
    elif orig.get("badge"):
        for k in ("label", "type"):
            if orig["badge"].get(k) != new["badge"].get(k):
                problems.append(f"badge.{k}: {orig['badge'].get(k)!r} != {new['badge'].get(k)!r}")
    if orig.get("lineName") != new.get("lineName"):
        problems.append(f"lineName: {orig.get('lineName')!r} != {new.get('lineName')!r}")
    if orig.get("note") != new.get("note"):
        problems.append(f"note: {orig.get('note')!r} != {new.get('note')!r}")
    if orig.get("summaryNote") != new.get("summaryNote"):
        problems.append(f"summaryNote: {orig.get('summaryNote')!r} != {new.get('summaryNote')!r}")

    orig_links = [(l["label"], l["url"]) for l in orig.get("links", [])]
    new_links = [(l["label"], l["url"]) for l in new.get("links", [])]
    if orig_links != new_links:
        problems.append(f"links: {orig_links!r} != {new_links!r}")

    for dep in ("shinjuku", "yokohama", "omiya"):
        r_orig = orig["routes"].get(dep)
        r_new = new["routes"].get(dep)
        if (r_orig is None) != (r_new is None):
            problems.append(f"route[{dep}] presence differs")
            continue
        if r_orig is None:
            continue
        legs_orig = [(l.get("station"), (l.get("method") or {}).get("line"), l.get("durationMin")) for l in r_orig["legs"]]
        legs_new = [(l.get("station"), (l.get("method") or {}).get("line"), l.get("durationMin")) for l in r_new["legs"]]
        if legs_orig != legs_new:
            problems.append(f"route[{dep}] legs differ:\n  orig={legs_orig}\n  new ={legs_new}")

    # summaryの表示文字列（ts-time-val/ts-fare-val）は、新レンダラーでは
    # trainTimeXxx/fareXxxから再構成している。元のHTML中の値と一致するかチェック。
    for dep in ("shinjuku", "yokohama", "omiya"):
        ov = (orig.get("_summary_time_val") or {}).get(dep)
        nv = (new.get("_summary_time_val") or {}).get(dep)
        if ov != nv:
            problems.append(f"time_val[{dep}]: orig={ov!r} new(from trainTimeXxx)={nv!r}")
        of = (orig.get("_summary_fare_val") or {}).get(dep)
        nf = (new.get("_summary_fare_val") or {}).get(dep)
        if of != nf:
            problems.append(f"fare_val[{dep}]: orig={of!r} new(from fareXxx)={nf!r}")

    return problems


def main():
    mountains = json.loads(MOUNTAINS_JSON.read_text(encoding="utf-8"))
    results = {}
    ok_count = 0
    problem_count = 0

    for m in mountains:
        mid = m["id"]
        html = m.get("trainAccessHtml")
        if not html:
            continue
        parsed_orig, err = parse_train_access_html(html)
        if err:
            continue

        new_html = render_ts_section(parsed_orig, m)
        parsed_new, err2 = parse_train_access_html(new_html)
        if err2:
            results[mid] = {"error": f"re-parse of rendered html failed: {err2}"}
            problem_count += 1
            continue

        problems = diff_parsed(parsed_orig, parsed_new, mid)
        if problems:
            results[mid] = {"problems": problems}
            problem_count += 1
        else:
            ok_count += 1

    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"一致: {ok_count}")
    print(f"差分あり: {problem_count}")
    for mid, r in results.items():
        print(f"\n=== {mid} ===")
        for p in r.get("problems", [r.get("error")]):
            print(" -", p)
    print(f"\n詳細: {OUT_JSON}")


if __name__ == "__main__":
    main()
