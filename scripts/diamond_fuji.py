"""山頂から見たダイヤモンド富士（太陽が富士山頂に重なる日と時刻）の計算（2026-11-12）

- 富士山頂（剣ヶ峰 北緯35.360556・東経138.727222・3,776m）の方位と仰角を、山頂の座標・標高から出す
  （地球の丸みと大気差。大気差の係数 k=0.13）
- 太陽の位置は sun_calc.py。太陽の見かけの高度は大気差（Saemundsson の式）を足す
- 毎日、太陽の方位が富士山頂の方位と同じになる時刻に、太陽の中心と山頂の高さの差を見る。
  差が太陽の半径（0.27°）以内なら、その日は太陽が山頂に重なる（ダイヤモンド富士）
- 地形で富士山が隠れるかは計算していない（富士山が見えると出典で確かめた山だけに使う）
国土交通省 関東地方整備局「関東の富士見百景」の一覧と照らした結果は check()（main の最後）
"""
import datetime
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sun_calc  # noqa: E402

FUJI = (35.360556, 138.727222, 3776.0)
R = 6371000.0
K = 0.13
SUN_R = 0.27
JST = sun_calc.JST


def _dist_az(lat1, lng1, lat2, lng2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lng2 - lng1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    d = 2 * R * math.asin(math.sqrt(a))
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return d, (math.degrees(math.atan2(y, x)) + 360) % 360


def fuji_view(lat, lng, elev):
    """山頂から見た富士山頂の距離（km）・方位（度）・見かけの仰角（度）"""
    d, az = _dist_az(lat, lng, FUJI[0], FUJI[1])
    alt = math.degrees(math.atan2(FUJI[2] - elev, d) - d / (2 * R) * (1 - K))
    return d / 1000, az, alt


def refraction(alt):
    """見かけの高度にするために足す大気差（度）。Saemundsson の式"""
    return 1.02 / math.tan(math.radians(alt + 10.3 / (alt + 5.11))) / 60


def _time_at_az(lat, lng, date, az, morning):
    base = datetime.datetime(date.year, date.month, date.day, tzinfo=JST)
    lo, hi = (base + datetime.timedelta(hours=4), base + datetime.timedelta(hours=11, minutes=30)) if morning else \
        (base + datetime.timedelta(hours=12, minutes=30), base + datetime.timedelta(hours=20))
    f = lambda t: sun_calc.sun_position(lat, lng, t)[0] - az
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(40):
        mid = lo + (hi - lo) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return lo + (hi - lo) / 2


def daily(lat, lng, elev, start=datetime.date(2026, 12, 1), days=366):
    """毎日の [(日付, 太陽の方位が富士山頂と同じになる時刻, 太陽の中心−山頂の高さの差（度）)]"""
    dkm, az, falt = fuji_view(lat, lng, elev)
    morning = az < 180
    out = []
    for i in range(days):
        d = start + datetime.timedelta(days=i)
        t = _time_at_az(lat, lng, d, az, morning)
        if not t:
            continue
        g = sun_calc.sun_position(lat, lng, t)[1]
        out.append((d, t, g + refraction(g) - falt))
    return out


NEAR = 0.6  # 太陽の中心が山頂からこれ以内を通る日は「ほぼ重なる」（大気差の日ごとの違いで重なることがある）


def events(lat, lng, elev, start=datetime.date(2026, 12, 1), days=366):
    """ダイヤモンド富士の日。[{'date', 'time', 'diff', 'kind', 'from', 'to', 'morning'}]
    - 太陽が山頂を通り過ぎる（前の日と次の日で上下が入れ替わる）とき：差の小さいほうの日。kind は 'hit'
    - 入れ替わらず、差がいちばん小さくなる日（冬至・夏至のころ）：差が太陽の半径以内なら 'hit'、NEAR 以内なら 'near'（山頂をかすめる）
    from / to：差が太陽の半径以内の日の幅（'near' はその日だけ）"""
    rows = daily(lat, lng, elev, start, days)
    morning = fuji_view(lat, lng, elev)[1] < 180
    out = []

    def span(i):
        j = k = i
        while j - 1 >= 0 and abs(rows[j - 1][2]) <= SUN_R and (rows[j][0] - rows[j - 1][0]).days == 1:
            j -= 1
        while k + 1 < len(rows) and abs(rows[k + 1][2]) <= SUN_R and (rows[k + 1][0] - rows[k][0]).days == 1:
            k += 1
        return rows[j][0], rows[k][0]

    for i in range(1, len(rows)):
        a, b = rows[i - 1], rows[i]
        if (b[0] - a[0]).days != 1:
            continue
        if a[2] == 0 or (a[2] < 0) != (b[2] < 0):
            idx = i - 1 if abs(a[2]) <= abs(b[2]) else i
            r = rows[idx]
            f, t = span(idx) if abs(r[2]) <= SUN_R else (r[0], r[0])
            out.append({'date': r[0], 'time': r[1], 'diff': r[2], 'kind': 'hit', 'from': f, 'to': t, 'morning': morning})
    for i in range(1, len(rows) - 1):
        a, b, c = rows[i - 1], rows[i], rows[i + 1]
        if abs(b[2]) <= abs(a[2]) and abs(b[2]) < abs(c[2]) and (a[2] < 0) == (b[2] < 0) == (c[2] < 0) and abs(b[2]) <= NEAR:
            if abs(b[2]) <= SUN_R:
                f, t = span(i)
                out.append({'date': b[0], 'time': b[1], 'diff': b[2], 'kind': 'hit', 'from': f, 'to': t, 'morning': morning})
            else:
                out.append({'date': b[0], 'time': b[1], 'diff': b[2], 'kind': 'near', 'from': b[0], 'to': b[0], 'morning': morning})
    out.sort(key=lambda e: e['date'])
    return out


if __name__ == '__main__':
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SC = json.load(open(os.path.join(root, 'data', 'summit_coords.json'), encoding='utf-8'))['mountains']
    M = {m['id']: m for m in json.load(open(os.path.join(root, 'data', 'mountains.json'), encoding='utf-8'))}
    # 関東地方整備局「関東の富士見百景」ダイヤモンド富士の一覧（標高を考えない計算）と照らす
    KTR = {'takao': '12/17〜26 日没', 'nokogiriyama_chiba': '4/18〜19・8/23〜24 日没',
           'koubousan': '3/24・9/18 日没', 'ohnoyama': '3/18〜19・9/24〜25 日没'}
    for k, v in KTR.items():
        c = SC.get(k) or {}
        lat, lng = c.get('lat') or M[k]['lat'], c.get('lng') or M[k]['lng']
        elev = c.get('ele') or M[k]['elevation']
        dkm, az, alt = fuji_view(lat, lng, elev)
        ev = events(lat, lng, elev)
        print(M[k]['name'], '%.0fkm 方位%.1f 仰角%.2f' % (dkm, az, alt), ' / '.join(
            '%d/%d %s %s(%.2f) %s〜%s' % (e['date'].month, e['date'].day, sun_calc.hm(e['time']), e['kind'], e['diff'], e['from'].strftime('%m/%d'), e['to'].strftime('%m/%d')) for e in ev), '| 整備局', v)
