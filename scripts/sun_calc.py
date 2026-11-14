"""太陽の位置と日の出・日の入りの計算（2026-11-12。冬の記事のために作った）

NOAA の Solar Calculator と同じ式（Jean Meeus『Astronomical Algorithms』の簡略版）。
- sunrise_sunset(lat, lng, date, elev_m=0)：日の出・日の入りの時刻（日本時間の datetime）
  elev_m=0 のときは国立天文台の暦と同じ定義（太陽の上の縁が地平線に接する。大気差 35'08" と視半径 16'）。
  elev_m を渡すと、その高さから見た海の水平線（見かけの伏角 1.76'×√m）まで下げた時刻を出す（山頂の日の出の目安）。
  手前に山があればそれより遅くなる。
- sun_position(lat, lng, dt)：方位角（北から東回り）と高度（度、大気差なし）
国立天文台の暦と照らした結果は、このファイルの下の main に書いた。
"""
import datetime
import math

JST = datetime.timezone(datetime.timedelta(hours=9))


def _jd(dt):
    dt = dt.astimezone(datetime.timezone.utc)
    y, m = dt.year, dt.month
    d = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def _sun(jd):
    """太陽の赤緯（度）と均時差（分）"""
    t = (jd - 2451545.0) / 36525
    l0 = (280.46646 + t * (36000.76983 + 0.0003032 * t)) % 360
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    mr = math.radians(m)
    c = (math.sin(mr) * (1.914602 - t * (0.004817 + 0.000014 * t)) + math.sin(2 * mr) * (0.019993 - 0.000101 * t)
         + math.sin(3 * mr) * 0.000289)
    true_long = l0 + c
    omega = 125.04 - 1934.136 * t
    lam = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    eps0 = 23 + (26 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60) / 60
    eps = eps0 + 0.00256 * math.cos(math.radians(omega))
    decl = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lam))))
    yv = math.tan(math.radians(eps / 2)) ** 2
    l0r = math.radians(l0)
    eqt = 4 * math.degrees(yv * math.sin(2 * l0r) - 2 * e * math.sin(mr) + 4 * e * yv * math.sin(mr) * math.cos(2 * l0r)
                           - 0.5 * yv * yv * math.sin(4 * l0r) - 1.25 * e * e * math.sin(2 * mr))
    return decl, eqt


def sun_position(lat, lng, dt):
    """方位角（北0°・東90°）と高度（度。大気差を含まない幾何学的な高度）"""
    decl, eqt = _sun(_jd(dt))
    u = dt.astimezone(datetime.timezone.utc)
    minutes = u.hour * 60 + u.minute + u.second / 60
    tst = (minutes + eqt + 4 * lng) % 1440
    ha = tst / 4 - 180
    la, de, h = math.radians(lat), math.radians(decl), math.radians(ha)
    cz = math.sin(la) * math.sin(de) + math.cos(la) * math.cos(de) * math.cos(h)
    zen = math.degrees(math.acos(max(-1, min(1, cz))))
    az = math.degrees(math.atan2(math.sin(h), math.cos(h) * math.sin(la) - math.tan(de) * math.cos(la))) + 180
    return az % 360, 90 - zen


def _event(lat, lng, date, alt, rising):
    """太陽の中心の高度が alt（度）になる時刻を二分法で探す"""
    base = datetime.datetime(date.year, date.month, date.day, tzinfo=JST)
    lo, hi = (base + datetime.timedelta(hours=3), base + datetime.timedelta(hours=12)) if rising else \
        (base + datetime.timedelta(hours=12), base + datetime.timedelta(hours=21))
    f = lambda t: sun_position(lat, lng, t)[1] - alt
    if rising and not (f(lo) < 0 < f(hi)):
        return None
    if not rising and not (f(lo) > 0 > f(hi)):
        return None
    for _ in range(40):
        mid = lo + (hi - lo) / 2
        if (f(mid) < 0) == rising:
            lo = mid
        else:
            hi = mid
    return lo + (hi - lo) / 2


def horizon_alt(elev_m=0):
    """日の出・日の入りのときの太陽の中心の幾何学的な高度（度）"""
    return -(35 / 60 + 8 / 3600) - 16 / 60 - 1.76 / 60 * math.sqrt(max(elev_m, 0))


def sunrise_sunset(lat, lng, date, elev_m=0):
    a = horizon_alt(elev_m)
    return _event(lat, lng, date, a, True), _event(lat, lng, date, a, False)


def hm(dt):
    """秒を四捨五入して 時:分"""
    if dt is None:
        return None
    dt = (dt + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0)
    return '%d:%02d' % (dt.hour, dt.minute)


if __name__ == '__main__':
    # 国立天文台「暦計算室」の値と照らす（東京＝北緯35°39'・東経139°44'、標高0m）
    for d in ['2027-01-01', '2026-06-21', '2026-12-22']:
        r, s = sunrise_sunset(35.65, 139.7333, datetime.date.fromisoformat(d))
        print(d, hm(r), hm(s))
