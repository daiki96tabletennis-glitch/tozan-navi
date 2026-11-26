"""GA4 で月100回以上見られている山に、天気の欄（hasWeatherWidget）を付ける（2026-11-26。運営者の指示）。

GA4 の山ページの表示回数（直近30日＝2026-10-27〜11-25。.claude/ga4_mountain_pv_30d_2026_11_26.json）が
100回以上の30山のうち、天気の欄が無かった7山：
  金時山 243・古賀志山 175・明神ヶ岳 159・天城山 130・鋸山 115・日向山 112・安達太良山 100
天気は山頂の座標（lat / lng）と標高で読む（_weather_widget_block.html）。何度流しても同じ結果。
そのあと gen_mountain_pages.py --id <山ID>。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "data", "mountains.json")
IDS = ["kintoki", "kogashiyama", "myojingatake", "amagi", "nokogiriyama_chiba", "hinata", "adatara"]

D = json.load(open(PATH, encoding="utf-8"))
found = 0
changed = 0
for m in D:
    if m.get("id") in IDS:
        found += 1
        if not (m.get("lat") and m.get("lng")):
            raise SystemExit("座標がありません: " + m["id"])
        if m.get("hasWeatherWidget") is not True:
            m["hasWeatherWidget"] = True
            changed += 1
if found != len(IDS):
    raise SystemExit("見つからない山があります: %d / %d" % (found, len(IDS)))
json.dump(D, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("天気の欄を付けた山: %d（対象 %d）" % (changed, len(IDS)))
