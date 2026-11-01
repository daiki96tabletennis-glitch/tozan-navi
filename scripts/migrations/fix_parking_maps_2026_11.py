#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""地図ボタンの行き先を駐車場にそろえ、バスの時刻表リンクを足す（2026-11-01。運営者の指示）。

最近足した13山の地図ボタンを、Google マップの駐車場の場所と照らした（OpenStreetMap の逆ジオコーダーでも、いまの位置に何があるかを確かめた）。
- 燕岳・大天井岳：市営第一駐車場（有料の予約制）を指していた → 中房第2駐車場（駐車場の欄の「第二・第三駐車場」に合わせる）
- 北横岳：ロープウェイの山麓駅 → 北八ヶ岳ロープウェイの駐車場
- 入笠山：ゴンドラの山麓駅 → 富士見パノラマリゾート 第1駐車場
- 西穂高岳・笠ヶ岳：バスの回転場（駐車禁止。OpenStreetMap）→ 新穂高第2駐車場（登山者用・通年）。
  駐車場の欄も、2026年版の新穂高地区駐車場マップ（2026.05更新）の値に直した。前は西穂高岳が観光用の第1駐車場の料金（800円／6時間）、
  笠ヶ岳が「第３駐車場（約400台・600円）」で、どちらも今の公式の値と違っていた
- 妙義山：妙義神社 → 妙義山 市営第1駐車場（道の駅みょうぎの隣）
- そのほか（天狗岳・仙ノ倉山・宝篋山・竜ヶ岳・鳴神山・仏果山・堂平山）は、すでに駐車場の場所だった
- 高松山は登山者用の駐車場が確かめられない（駐車場の欄にもそう書いてある）ので、高松山入口バス停のまま

時刻表のリンク：
- 仏果山：リンクが無かった → 神奈中の公式の発着時刻表（本厚木駅→仏果山登山口。790円・43分でデータと一致）
- 天狗岳：諏訪地区の一覧 → アルピコ交通の奥蓼科渋の湯線のページ
- 仙ノ倉山・平標山：南越後交通のトップ → 路線バスの時刻表の欄（PDF の名前が改正ごとに変わるため、欄へのリンク）

地図の位置は数十〜数百mしか動かないので、車の所要時間は測り直していない。

  python3 scripts/migrations/fix_parking_maps_2026_11.py
"""
import json
import os
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-11-01'

# 山ID: (緯度, 経度, 地図アプリに出す名前)。Google マップの施設の位置（2026-11-01 に確認）
MAPS = {
    'tsubakurodake': (36.3903333, 137.7486667, '中房第2駐車場'),
    'otenshoudake': (36.3903333, 137.7486667, '中房第2駐車場'),
    'kitayokodake': (36.0676128, 138.3014791, '北八ヶ岳ロープウェイ 駐車場'),
    'nyukasayama': (35.910726, 138.207607, '富士見パノラマリゾート 第1駐車場'),
    'nishihotaka': (36.2830534, 137.5750312, '新穂高第2駐車場'),
    'kasagatake': (36.2830534, 137.5750312, '新穂高第2駐車場'),
    'myogisan': (36.2994402, 138.766176, '妙義山 市営第1駐車場'),
}

SHINHOTAKA = ('新穂高第2駐車場（登山者用・85台・普通車2,000円／24時間・先着順・通年）。'
              '6〜10月は新穂高第3駐車場（無料・先着順）や、予約制の登山者用駐車場（第4・深山・鍋平）もある。'
              '路上駐車は禁止（新穂高地区駐車場マップ 2026年版）')
PARKING = {'nishihotaka': SHINHOTAKA, 'kasagatake': SHINHOTAKA}
PARKING_SRC = 'https://kitaalpsgifu.jp/dl/pmap202606.pdf'

# 山ID: [(前のURL, 新しいURL, 新しい表示名)]
LINKS = {
    'bukkasan': [(None, 'https://transfer-cloud.navitime.biz/kanachu/trips?departure-busstop=00022017&arrival-busstop=00022437',
                  '神奈中バス 本厚木駅→仏果山登山口 時刻表')],
    'tengudake': [('https://www.alpico.co.jp/traffic/local/suwa/', 'https://www.alpico.co.jp/traffic/local/suwa/shibunoyu/',
                   'アルピコ交通 奥蓼科渋の湯線 時刻表')],
    'sennokurayama': [('https://www.minamiechigo.co.jp/', 'https://www.minamiechigo.co.jp/#routebus',
                       '南越後交通バス 時刻表（湯沢駅〜西武クリスタル線）')],
    'tairappyo': [('https://www.minamiechigo.co.jp/', 'https://www.minamiechigo.co.jp/#routebus',
                   '南越後交通バス 時刻表（湯沢駅〜西武クリスタル線）')],
}


def gmap(lat, lng, q):
    g = 'https://www.google.com/maps/search/?api=1&query=%s%%2C%s' % (lat, lng)
    a = 'https://maps.apple.com/?ll=%s,%s&q=%s' % (lat, lng, quote(q))
    btn = ('<div class="map-btns"><a href="%s" target="_blank" class="map-btn-link">Googleマップ</a>\n'
           '<a href="%s" target="_blank" class="map-btn-link">Apple Maps</a>\n</div>' % (g, a))
    return g, a, btn


D = json.load(open(PATH, encoding='utf-8'))
by = dict((m['id'], m) for m in D)
done = set()
for i, (lat, lng, q) in MAPS.items():
    m = by[i]
    m['gmapUrl'], m['amapUrl'], m['mapBtnsHtml'] = gmap(lat, lng, q)
    m['mapTargetNote'] = '地図ボタンは駐車場（%s）。%s に Google マップで確認' % (q, TODAY)
    done.add(i)
for i, text in PARKING.items():
    by[i]['parking'] = text
    by[i]['parkingSource'] = PARKING_SRC
    by[i]['parkingCheckedAt'] = TODAY
    done.add(i)
for i, changes in LINKS.items():
    m = by[i]
    links = m['trainRoutes'].setdefault('links', [])
    for old, new, label in changes:
        if old is None:
            assert not any(l.get('url') == new for l in links), i
            links.append({'type': 'bus', 'label': label, 'url': new})
        else:
            hit = [l for l in links if l.get('url') == old]
            assert len(hit) == 1, (i, old)
            hit[0]['url'] = new
            hit[0]['label'] = label
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    done.add(i)
for i in done:
    by[i]['mountainUpdated'] = TODAY
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', len(done), sorted(done))
