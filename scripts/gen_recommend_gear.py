#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_recommend_gear.py

data/gear-data.json（正本）から、/recommend/ 診断結果用の月別軽量JSON
（data/recommend-gear/1.json 〜 12.json）を生成するスクリプト。

- data/recommend-gear/*.json は派生データであり、手動編集禁止。
  内容を変えたい場合は必ず data/gear-data.json を編集してから
  本スクリプトを再実行すること。
- 診断ページは gear-data.json（約2MB）を直接読み込むと重いため、
  現在月分だけを取得できるよう月ごとに分割する。
- 診断側では商品説明文（r）は不要なため、c/i/p のみを出力する
  （データ量を絞ってfetchを軽くするため）。

使い方:
    python scripts/gen_recommend_gear.py
"""

import json
import os

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEAR_DATA_PATH = os.path.join(SITE_ROOT, "data", "gear-data.json")
OUT_DIR = os.path.join(SITE_ROOT, "data", "recommend-gear")


def generate():
    with open(GEAR_DATA_PATH, encoding="utf-8") as f:
        gear_data = json.load(f)

    os.makedirs(OUT_DIR, exist_ok=True)

    written = []
    for month in range(1, 13):
        month_key = str(month)
        out = {}
        for mid, months in gear_data.items():
            items = months.get(month_key)
            if not items:
                continue
            out[mid] = [
                {"c": it.get("c"), "i": it.get("i"), "p": it.get("p")}
                for it in items
            ]
        out_path = os.path.join(OUT_DIR, f"{month}.json")
        tmp_path = out_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp_path, out_path)
        written.append(out_path)

    return written


def main():
    written = generate()
    print(f"生成完了: {len(written)} ファイル ({OUT_DIR})")


if __name__ == "__main__":
    main()
