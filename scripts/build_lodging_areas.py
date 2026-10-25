#!/usr/bin/env python3
"""前泊の宿のページ（/stay/<山ID>/。scripts/gen_stay_pages.py）で宿を探す場所を作る。

山ごとに、次の場所を mountains.json の電車・バスのデータから決める（手で選ばない）。
  - 駅：電車を降りて、登山口へのバス・ケーブルカー・タクシーに乗り換える駅（例：北岳＝甲府駅）
  - 登山口側：電車・バスの終点（例：北岳＝広河原）と、車で行く人が車を置いて乗り換える場所（driveTarget。例：芦安駐車場）
座標は次の順に、名前と山からの距離（40km以内）を照らして取る：サイトの登山口データ（data/trailheads.json。確認済みのもの）→
国土地理院の地名検索（名前が同じもの。「◯◯バスターミナル」「◯◯駅」は語尾を外した名前でも探す）→ OpenStreetMap（名前と種類が合うもの）。
あわせて、地図ボタンの行き先（車で行く人が向かう場所）も登山口側の場所に入れる（ほかの場所と1.5km以内なら同じ場所とみなす）。
照らせなかった場所は needsVerification を付け、ページには出さない（推測で座標を置かない）。
足したい場所・外したい場所は EXTRA / SKIP に書く。

楽天トラベルの「周辺のホテル・旅館」のページ（日付・空室で探せる）も場所ごとに探してリンク先にする。
  - 駅：その駅がある都道府県（国土地理院の逆ジオコーダーで座標から）の「駅・空港周辺」の一覧で、名前が同じ駅のページ
  - 駅以外：楽天トラベルの「スポット」から手で選んだページ（SPOT）。ページの見出しに、選んだスポットの名前があることを確かめる

  python3 scripts/build_lodging_areas.py            # 確認だけ（書き込まない）
  python3 scripts/build_lodging_areas.py --write    # data/lodging_areas.json に書く

宿そのものは保存しない。前泊のページを開いたときに assets/js/lodging.js が楽天トラベルの施設検索 API で探す
（楽天ウェブサービス規約：取得した情報を保存しない）。
"""
import json
import math
import os
import re
import sys
import time
import datetime

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "mountains.json")
TRAILHEADS = os.path.join(ROOT, "data", "trailheads.json")
OUT = os.path.join(ROOT, "data", "lodging_areas.json")

# 出す山（まず北岳で試作。広げるときはここに足す。唐松岳・奥穂高岳・立山は 2026-10-25 に場所を確かめ済み）
TARGET = ["kitadake"]

# 探す半径（km。楽天の上限は3.0）
RADIUS = {"station": 1.0, "trailhead": 3.0, "parking": 3.0}

# データから決まらない・足したい場所：{山ID: [{"name":..., "kind":..., "q": OSMで探す語}]}
EXTRA = {}
# 外したい場所：{山ID: [場所の名前]}
SKIP = {}
# 駅以外の場所の、楽天トラベルのスポットのページ（手で選ぶ。場所の近くの宿が載っているものだけ）
# {山ID: {場所の名前: (スポット名, URL)}}
SPOT = {
    "kitadake": {"芦安駐車場": ("芦安温泉郷", "https://travel.rakuten.co.jp/yado/spot/yamanashi/S19002138.html")},
}
# 都道府県コード → 楽天トラベルの URL の都道府県名
PREF_SLUG = {
    "01": "hokkaido", "02": "aomori", "03": "iwate", "04": "miyagi", "05": "akita", "06": "yamagata", "07": "fukushima",
    "08": "ibaraki", "09": "tochigi", "10": "gunma", "11": "saitama", "12": "chiba", "13": "tokyo", "14": "kanagawa",
    "15": "niigata", "16": "toyama", "17": "ishikawa", "18": "fukui", "19": "yamanashi", "20": "nagano", "21": "gifu",
    "22": "shizuoka", "23": "aichi", "24": "mie", "25": "shiga", "26": "kyoto", "27": "osaka", "28": "hyogo",
}

# 乗り物の線名から、鉄道以外（バス・ケーブルカーなど）を見分ける語。
# データの icon は当てにならない（バスに train が付いている山がある）ので線名で見る
NON_RAIL = re.compile(r"バス|交通「|交通$|シャトル|乗合|タクシー|ロープウェイ|ケーブル|ゴンドラ|リフト")

UA = {"User-Agent": "tozan-navi.com lodging-areas (https://tozan-navi.com/)"}
OK_TYPES = {  # OpenStreetMap の種類
    "station": {"station", "halt", "stop", "train_station"},
    "trailhead": {"bus_stop", "bus_station", "station", "platform", "stop", "parking", "aerialway_station", "locality", "hamlet", "isolated_dwelling", "village"},
    "parking": {"parking", "bus_stop", "bus_station", "station", "locality", "hamlet", "village"},
}


def clean(name):
    """「広河原（マイカー規制）」→「広河原」"""
    return re.sub(r"[（(].*?[）)]", "", name or "").strip()


def is_rail(leg):
    line = ((leg.get("method") or {}).get("line")) or ""
    return bool(line) and not NON_RAIL.search(line)


def km(a, b):
    r = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def places(m):
    """山の電車・バスのデータから、宿を探す場所を決める"""
    out = []

    def add(name, kind, via):
        n = clean(name)
        if not n or any(p["name"] == n for p in out):
            return
        out.append({"name": n, "kind": kind, "via": via, "raw": name})

    routes = ((m.get("trainRoutes") or {}).get("routes") or {})
    for dep in ("shinjuku", "omiya", "yokohama"):
        legs = (routes.get(dep) or {}).get("legs") or []
        # 鉄道の区間のあとに、最初に鉄道以外へ乗り換える駅
        for i, leg in enumerate(legs[:-1]):
            if not is_rail(leg) and i > 0 and is_rail(legs[i - 1]):
                add(leg.get("station"), "station", "%s行きのバスなどに乗り換える駅" % clean(legs[-1].get("station")))
                break
    for dep in ("shinjuku", "omiya", "yokohama"):
        legs = (routes.get(dep) or {}).get("legs") or []
        if legs:
            add(legs[-1].get("station"), "trailhead", "電車・バスで行ける終点")
    if m.get("driveTarget"):
        add(m["driveTarget"], "parking", "車で行くときに車を置いて、バスなどに乗り換える場所")
    for e in EXTRA.get(m["id"], []):
        add(e["name"], e["kind"], e.get("via", "手で追加"))
    skip = set(SKIP.get(m["id"], []))
    return [p for p in out if p["name"] not in skip]


def center(m):
    """山のおおよその位置（地図ボタンの座標、無ければ山の座標）"""
    g = re.search(r"query=([\d.]+)%2C([\d.]+)", m.get("gmapUrl") or "")
    if g:
        return float(g.group(1)), float(g.group(2))
    if m.get("lat") and m.get("lng"):
        return float(m["lat"]), float(m["lng"])
    return None


SUFFIX = re.compile(r"(バスターミナル|バス停|駐車場|駅)$")


def alt_names(p):
    names = [p["name"]]
    for x in re.findall(r"[（(](.*?)[）)]", p.get("raw") or ""):
        if re.search(r"バスターミナル|駐車場|駅|バス停", x):
            names.append(x)
    for n in list(names):
        b = SUFFIX.sub("", n)
        if b and b != n:
            names.append(b)
    out = []
    for n in names:
        if n not in out:
            out.append(n)
    return out


def from_trailheads(p, c, ths):
    for t in ths:
        if t.get("needsVerification") or t.get("lat") is None:
            continue
        if clean(t.get("name")) in (p["name"], clean(p.get("raw") or "")) and km((t["lat"], t["lng"]), c) <= 40:
            return {"lat": t["lat"], "lng": t["lng"], "source": "サイトの登山口データ（%s）" % t["id"], "matchedName": t["name"]}
    return None


def from_gsi(p, c):
    for n in alt_names(p):
        try:
            res = requests.get("https://msearch.gsi.go.jp/address-search/AddressSearch", params={"q": n}, headers=UA, timeout=20).json()
        except Exception:  # noqa
            res = []
        time.sleep(0.5)
        hits = []
        for f in res:
            title = (f.get("properties") or {}).get("title") or ""
            lng, lat = f["geometry"]["coordinates"][:2]
            if title == n and km((lat, lng), c) <= 40:
                hits.append((lat, lng))
        if hits and all(km(hits[0], h) <= 1.0 for h in hits[1:]):
            return {"lat": round(hits[0][0], 6), "lng": round(hits[0][1], 6), "source": "国土地理院 地名検索", "matchedName": n}
    return None


def from_osm(p, c):
    box = "%f,%f,%f,%f" % (c[1] - 0.5, c[0] + 0.5, c[1] + 0.5, c[0] - 0.5)
    for n in alt_names(p):
        params = {"q": n, "format": "json", "limit": 10, "countrycodes": "jp", "viewbox": box, "bounded": 1}
        try:
            res = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=UA, timeout=20).json()
        except Exception:  # noqa
            res = []
        time.sleep(1.2)
        ok = []
        for r in res:
            if r.get("type") not in OK_TYPES[p["kind"]]:
                continue
            pt = (float(r["lat"]), float(r["lon"]))
            if km(pt, c) <= 40:
                ok.append((pt, r))
        if ok and all(km(ok[0][0], o[0]) <= 1.0 for o in ok[1:]):
            r = ok[0][1]
            return {"lat": round(ok[0][0][0], 6), "lng": round(ok[0][0][1], 6), "source": "OpenStreetMap（%s/%s・%s）" % (r.get("osm_type"), r.get("osm_id"), r.get("type")), "matchedName": n}
    return None


def lookup(p, c, ths):
    if c is None:
        return None, "山の座標が無い"
    for f in (lambda: from_trailheads(p, c, ths), lambda: from_gsi(p, c), lambda: from_osm(p, c)):
        g = f()
        if g:
            return g, None
    return None, "名前が合う場所が見つからない（探した名前：%s）" % "・".join(alt_names(p))


_PAGES = {}


def get(url):
    if url not in _PAGES:
        try:
            r = requests.get(url, headers=UA, timeout=20)
            r.encoding = r.apparent_encoding if r.encoding in (None, "ISO-8859-1") else r.encoding
            _PAGES[url] = r.text if r.ok else ""
        except Exception:  # noqa
            _PAGES[url] = ""
        time.sleep(2)
    return _PAGES[url]


def title_of(html):
    t = re.search(r"<title>(.*?)</title>", html, flags=re.S)
    return re.sub(r"\s+", " ", t.group(1)).strip() if t else ""


def pref_code(lat, lng):
    try:
        r = requests.get("https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress", params={"lat": lat, "lon": lng}, headers=UA, timeout=20).json()
        time.sleep(0.5)
        return (r.get("results") or {}).get("muniCd", "")[:2].zfill(2)
    except Exception:  # noqa
        return ""


def rakuten_page(mid, row):
    """楽天トラベルの「周辺のホテル・旅館」のページ。見つからなければ None"""
    if row["kind"] == "station":
        slug = PREF_SLUG.get(pref_code(row["lat"], row["lng"]))
        if not slug:
            return None
        html = get("https://travel.rakuten.co.jp/yado/traffic/%s/" % slug)
        hrefs = set(re.findall(r'<a[^>]+href="(//travel\.rakuten\.co\.jp/yado/traffic/%s/\d+\.html)"[^>]*>\s*%s\s*</a>' % (slug, re.escape(row["name"])), html))
        if len(hrefs) != 1:
            return None
        url = "https:" + hrefs.pop()
        label = row["name"]
    else:
        sp = SPOT.get(mid, {}).get(row["name"])
        if not sp:
            return None
        label, url = sp
    t = title_of(get(url))
    if label not in t:
        print("  × 楽天トラベルのページの見出しに「%s」が無い：%s" % (label, t))
        return None
    return {"url": url, "label": label, "title": t}


def main():
    write = "--write" in sys.argv
    ms = json.load(open(DATA, encoding="utf-8"))
    ms = ms if isinstance(ms, list) else ms["mountains"]
    by = {m["id"]: m for m in ms}
    old = {}
    if os.path.exists(OUT):
        old = json.load(open(OUT, encoding="utf-8")).get("mountains", {})
    today = datetime.date.today().isoformat()
    th = json.load(open(TRAILHEADS, encoding="utf-8"))
    th = th.get("trailheads", th) if isinstance(th, dict) else th
    ths = list(th.values()) if isinstance(th, dict) else th
    result = {}
    for mid in TARGET:
        m = by[mid]
        c = center(m)
        rows = []
        for p in places(m):
            prev = next((a for a in old.get(mid, {}).get("areas", []) if a["name"] == p["name"] and a.get("lat")), None)
            if prev:
                geo, why = {k: prev[k] for k in ("lat", "lng", "source", "matchedName") if k in prev}, None
            else:
                geo, why = lookup(p, c, ths)
            row = {"name": p["name"], "kind": p["kind"], "via": p["via"], "radiusKm": RADIUS[p["kind"]]}
            if geo:
                row.update(geo)
                row["lastVerified"] = prev.get("lastVerified", today) if prev else today
            else:
                row["needsVerification"] = True
                row["why"] = why
            if geo:
                rk = rakuten_page(mid, row)
                if rk:
                    row["rakuten"] = rk
            rows.append(row)
            print("%s\t%s\t%s\t%s" % (m["name"], p["kind"], p["name"], ("%.5f,%.5f %s %s" % (geo["lat"], geo["lng"], geo["source"], geo.get("matchedName"))) if geo else "× " + why))
        # 地図ボタンの行き先（車で行く人が向かう場所）。ほかの場所と1.5km以内なら入れない
        if c and not any(r.get("lat") and km((r["lat"], r["lng"]), c) <= 1.5 for r in rows):
            label = clean(m.get("mapTargetName") or m.get("trailhead") or "")
            if label:
                rows.append({"name": label, "kind": "parking", "via": "地図ボタンの行き先（車で向かう場所）", "radiusKm": RADIUS["parking"],
                             "lat": c[0], "lng": c[1], "source": "サイトの地図ボタンの座標", "matchedName": label, "lastVerified": today})
                print("%s\tparking\t%s\t%.5f,%.5f 地図ボタン" % (m["name"], label, c[0], c[1]))
        result[mid] = {"name": m["name"], "areas": rows}
    if write:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"_note": "scripts/build_lodging_areas.py が作る（手で編集しない）。宿は保存しない", "mountains": result}, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("書き込み:", OUT)


if __name__ == "__main__":
    main()
