# -*- coding: utf-8 -*-
"""冬に使えないコース（routes[].winter）を、金峰山の試作の形でほかの山に広げる（2026-11-19。運営者の指示「この形で広げる」）

決まり（CLAUDE.md の「冬に使えないコース」）
- closed：冬は登山口へ行けない（道路・林道の冬期閉鎖、マイカー規制の道でバス・ロープウェイが止まる、登山道の閉山）。
  コースに印と、はじめは閉じた「冬の詳細と出典」を出す。期間（from・to）があれば、期間中は電車のバッジを隠し、
  代表コースなら alt のコースを代表にする。期間が発表されていない閉鎖は from・to を入れない（印と詳細だけ）
- car_only：冬は電車・バスでは行けない（季節運行の乗り物が止まる）。印は出さず、期間中だけ電車のバッジを隠す。
  期間は、データの運行期間（annualItems の transport か accesses.json の operation）の終わりの翌日から、
  その年の運行開始の前日まで（来季の開始は未発表なので2026年の日付で数える）。運行期間を直したらこのスクリプトを流し直す
- 道路の閉鎖を公式で確かめられていないコースは closed にしない（推測で入れない）。出典はデータの sourceUrl と、県の冬期通行止めの一覧
  （長野県「令和8年度 冬期通行止め予定」・群馬県の冬期閉鎖のページ）。白山の別当出合・折立（有峰林道）・笹ヶ峰・田の原・鳥倉林道・易老渡・蓼科山の七合目は、
  今冬の閉鎖を公式で確かめられず car_only のまま（2026-11-19）
- 金峰山は add_route_winter_kinpusan_2026_11.py（ここでは触らない）
- 代表コースが closed の期間に代表にするコース（alt）：甲斐駒ヶ岳＝黒戸尾根（竹宇駒ヶ岳神社）、槍ヶ岳＝新穂高温泉。
  どちらも登山口が通年行ける集落・温泉地。間ノ岳の奈良田からのコース3は終わりが広河原（冬は行けない）なので選ばない。ほかの山は、冬に行ける別の登山口を確かめられない（大菩薩嶺の丸川峠入口は県道201号の閉鎖区間＝裂石から上、
  仙丈ヶ岳の柏木・乗鞍岳の三本滝・常念岳の三股は冬の道路が未確認）か、別の登山口が無い。奥穂高岳は通年行けるのが西穂高岳からの縦走（ジャンダルム）だけなので選ばない
- 季節ダイヤ（transitSeasons）の山（赤城山・入笠山・西吾妻山・谷川岳）と、冬もゴンドラ・ロープウェイが動く山（唐松岳・五竜岳・日光白根山）は、
  冬の運行の日付が出ていないので入れていない
何度流しても同じ結果。このあと gen_mountain_pages.py（対象の山）→ build_winter_find.py → gen_find_winter.py → check_pages.py
"""
import datetime
import json
import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MP = os.path.join(ROOT, 'data', 'mountains.json')
AP = os.path.join(ROOT, 'data', 'accesses.json')
DAY = '2026-11-19'
DAY3 = '2026-11-23'
L = '冬は通行止め'


def src(label, url):
    return {'label': label, 'url': url}


# 道路・林道の閉鎖・閉山（closed）。(山, [コースの番号], 印, from, to, 文, 出典, alt)
CLOSED = [
    ('okutama', [1, 3], L, '12-14', '04-17',
     '上日川峠へのバス（栄和交通）は2026年は12月13日まで。県道も冬期閉鎖で（甲州市：例年、塩山側の県道201号は12月中旬〜4月中旬、'
     '大和側の県道218号は1月上旬〜4月中旬）、冬は上日川峠へ行けません。期間は2026年のバスの運行から数えた目安です',
     [src('栄和交通', 'https://eiwa-kotsu.jp/root.html'), src('甲州市（県道の冬期閉鎖）', 'https://www.city.koshu.yamanashi.jp/faq/2012033100570/')], None),
    ('nasu', [1, 2, 3], L, '12-14', '03-26',
     '栃木県が県道那須高原線（大丸温泉〜峠の茶屋）を冬期通行止めにする予定（12/14 11時〜3/26 11時）で、峠の茶屋へ行けません。'
     'ロープウェイ行きのバスも11月30日までで、冬は大丸温泉で折り返します',
     [src('栃木県 通行規制', 'https://www.pref.tochigi.lg.jp/h57/system/desaki/desaki/tusukoukisei/zyuutai7.html'),
      src('関東自動車', 'https://www.kantobus.co.jp/topics/topics.php?id=1416')], None),
    ('komagatake', [1], L, '11-04', '05-31',
     '北沢峠へは南アルプス林道を一般車が通れず、林道バスは2026年は6月1日〜11月3日でした。期間外は北沢峠へ行けません',
     [src('伊那市 南アルプス林道バス', 'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_jikokuhyo.html')], 'kuroto-roundtrip'),
    ('senjogatake', [1], L, '11-04', '05-31',
     '北沢峠へは南アルプス林道を一般車が通れず、林道バスは2026年は6月1日〜11月3日でした。期間外は北沢峠へ行けません',
     [src('伊那市 南アルプス林道バス', 'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_jikokuhyo.html')], None),
    ('tateyama', [1, 2], L, '12-01', '04-14',
     '立山黒部アルペンルートは2026年は4月15日〜11月30日の運行で、冬は室堂へ行けません',
     [src('立山黒部アルペンルート', 'https://www.alpen-route.com/timetable/')], None),
    ('tsurugi', [1, 3], L, '12-01', '04-14',
     '立山黒部アルペンルートは2026年は4月15日〜11月30日の運行で、冬は室堂へ行けません',
     [src('立山黒部アルペンルート', 'https://www.alpen-route.com/timetable/')], None),
    ('yari', [1], L, '11-16', '04-16',
     '上高地へは一年じゅう一般車が入れず（マイカー規制）、バスは2026年は4月17日〜11月15日でした。期間外は上高地へバス・車で行けません',
     [src('アルピコ交通 上高地線', 'https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/'), src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], 'hidazawa-roundtrip'),
    ('hotaka', [1, 2], L, '11-16', '04-16',
     '上高地へは一年じゅう一般車が入れず（マイカー規制）、バスは2026年は4月17日〜11月15日でした。期間外は上高地へバス・車で行けません',
     [src('アルピコ交通 上高地線', 'https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/'), src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('yakedake', [2], L, '11-16', '04-16',
     '上高地へは一年じゅう一般車が入れず（マイカー規制）、バスは2026年は4月17日〜11月15日でした。期間外は上高地へバス・車で行けません',
     [src('アルピコ交通 上高地線', 'https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/'), src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('chogatake', [1], L, '11-16', '04-16',
     '上高地へは一年じゅう一般車が入れず（マイカー規制）、バスは2026年は4月17日〜11月15日でした。期間外は上高地へバス・車で行けません',
     [src('アルピコ交通 上高地線', 'https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/'), src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('norikura', [1], L, '11-01', '06-30',
     '畳平へは一般車が入れず（マイカー規制）、シャトルバスは2026年は7月1日〜10月31日でした。期間外は畳平へ行けません',
     [src('アルピコ交通 乗鞍線', 'https://www.alpico.co.jp/traffic/local/kamikochi/echoline/')], None),
    ('fuji', [1, 3], '閉山中', '09-11', '07-09',
     '富士山の登山道は夏の開山期間（静岡県側の富士宮・須走ルートは2026年は7月10日〜9月10日）のほかは閉鎖です',
     [src('静岡県 富士山の登山期間', 'https://www.pref.shizuoka.jp/machizukuri/doro/fujisandoro/1029179.html')], None),
    ('fuji', [2], '閉山中', '09-11', '06-30',
     '富士山の吉田ルートは夏の開山期間（2026年は7月1日〜9月10日）のほかは閉鎖です',
     [src('山梨県 富士登山', 'https://www.pref.yamanashi.jp/fujisan/annzenn/documents/r8fujitozan.html')], None),
    ('kitadake', [1, 2, 3], L, '11-04', '06-25',
     '広河原へは一般車が入れず（マイカー規制）、南アルプス登山バスは2026年は6月26日〜11月3日でした。期間外は広河原へ行けません',
     [src('南アルプス観光 登山バス', 'https://minami-alpskankou.jp/?page_id=6542')], None),
    ('ainodake', [1, 2], L, '11-04', '06-25',
     '広河原へは一般車が入れず（マイカー規制）、南アルプス登山バスは2026年は6月26日〜11月3日でした。期間外は広河原へ行けません',
     [src('南アルプス観光 登山バス', 'https://minami-alpskankou.jp/?page_id=6542')], None),
    ('noutori', [2], L, '11-04', '06-25',
     '広河原へは一般車が入れず（マイカー規制）、南アルプス登山バスは2026年は6月26日〜11月3日でした。期間外は広河原へ行けません',
     [src('南アルプス観光 登山バス', 'https://minami-alpskankou.jp/?page_id=6542')], None),
    ('arakawadake', [1, 2], L, '10-13', '07-10',
     '椹島へは一般車が入れず、畑薙第一ダムからの送迎バス（山小屋の宿泊者だけ）は2026年は7月11日〜10月12日でした。期間外は椹島へ行けません',
     [src('特種東海フォレスト', 'https://www.t-forest.com/alpsinfo/bus/')], None),
    ('akaisidake', [1, 2], L, '10-13', '07-10',
     '椹島へは一般車が入れず、畑薙第一ダムからの送迎バス（山小屋の宿泊者だけ）は2026年は7月11日〜10月12日でした。期間外は椹島へ行けません',
     [src('特種東海フォレスト', 'https://www.t-forest.com/alpsinfo/bus/')], None),
    ('hijiridade', [1, 2, 3], L, '10-13', '07-10',
     '聖沢登山口・椹島へは一般車が入れず、畑薙第一ダムからの送迎バス（山小屋の宿泊者だけ）は2026年は7月11日〜10月12日でした。期間外は登山口へ行けません',
     [src('特種東海フォレスト', 'https://www.t-forest.com/alpsinfo/bus/')], None),
    ('shirasunayama', [1, 2, 3], L, '11-25', '04-21',
     '群馬県が国道405号（和光原〜野反湖）を冬期閉鎖にする予定（11/25 15時〜4/21 10時）で、野反湖の登山口へ行けません。'
     '野反湖へのバスも10月20日までです',
     [src('群馬県 冬期閉鎖', 'https://www.pref.gunma.jp/06/h2810053.html'),
      src('中之条町 六合地区路線バス', 'https://www.town.nakanojo.gunma.jp/uploaded/life/13968_25974_misc.pdf')], None),
    ('utsukushigahara', [1, 2, 3], L, '11-18', '04-20',
     '長野県がビーナスライン・美ヶ原公園線など美ヶ原への道を冬期通行止めにする予定（11/18 11時〜4/20 11時）で、登山口へ車で行けません。'
     '直行バスも10月12日までです',
     [src('長野県 冬期通行止め予定', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('kitayokodake', [1, 2, 3], 'ロープウェイ運休', '11-24', '12-18',
     '北八ヶ岳ロープウェイが整備点検で運休し（2026年11月24日〜12月18日）、山頂駅へ行けません',
     [src('北八ヶ岳ロープウェイ', 'https://www.kitayatu.jp/ropeway/')], None),
    ('jonengatake', [1], L, '11-27', '04-16',
     '一ノ沢への林道は冬は通行止めで、タクシーで入れるのは2026年は4月17日〜11月26日でした（安曇野市）。期間外は一ノ沢へ行けません',
     [src('安曇野市', 'https://www.city.azumino.nagano.jp/soshiki/32/66871.html')], None),
    # 2026-11-19 の2回目：県の冬期通行止めの一覧で確かめた登山口（長野県「令和8年度 冬期通行止め予定」2026-10-21 作成・群馬県の冬期閉鎖のページ）
    ('tsubakurodake', [1, 2], L, '12-01', '04-23',
     '長野県が中房温泉への県道（槍ヶ岳矢村線の中房温泉〜宮城ゲート）を冬期通行止めにする予定（12/1 15時〜4/23 12時）で、中房温泉へ行けません。バスも11月3日までです',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('otenshoudake', [1, 2, 3], L, '12-01', '04-23',
     '長野県が中房温泉への県道（槍ヶ岳矢村線の中房温泉〜宮城ゲート）を冬期通行止めにする予定（12/1 15時〜4/23 12時）で、中房温泉へ行けません。バスも11月3日までです',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('arikayama', [2], L, '12-01', '04-23',
     '長野県が中房温泉への県道（槍ヶ岳矢村線の中房温泉〜宮城ゲート）を冬期通行止めにする予定（12/1 15時〜4/23 12時）で、有明荘へ行けません。バスも11月3日までです',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('yari', [3], L, '12-01', '04-23',
     '長野県が中房温泉への県道（槍ヶ岳矢村線の中房温泉〜宮城ゲート）を冬期通行止めにする予定（12/1 15時〜4/23 12時）で、歩き始めの中房温泉へ行けません',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('kashimayari', [1, 3], L, '12-01', '04-14',
     '長野県が扇沢への県道（扇沢大町線の扇沢〜日向山）を冬期通行止めにする予定（12/1 10時から。解除は4月中旬）で、扇沢へ行けません。扇沢へのバスも11月30日までです',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('kashimayari', [2], L, '11-27', '03-31',
     '長野県が大谷原への県道（白馬岳大町線の大谷原〜鹿島黒沢高原入口）を冬期通行止めにする予定（11/27 10時〜3/31 10時）で、大谷原へ車で行けません',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('harinokidake', [1, 2, 3], L, '12-01', '04-14',
     '長野県が扇沢への県道（扇沢大町線の扇沢〜日向山）を冬期通行止めにする予定（12/1 10時から。解除は4月中旬）で、扇沢へ行けません。扇沢へのバスも11月30日までです',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('eboshidake_kita', [1, 2], L, '11-27', '04-16',
     '長野県が七倉への県道（槍ヶ岳線の七倉〜葛温泉上）を冬期通行止めにする予定（11/27 10時〜4/16 10時）で、七倉・高瀬ダムへ行けません。七倉へのバスも10月25日までです',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('noguchigoro', [1, 2], L, '11-27', '04-16',
     '長野県が七倉への県道（槍ヶ岳線の七倉〜葛温泉上）を冬期通行止めにする予定（11/27 10時〜4/16 10時）で、七倉・高瀬ダムへ行けません。七倉へのバスも10月25日までです',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('shirouma', [2], L, '11-19', '04-23',
     '長野県が猿倉への県道（白馬岳線の猿倉〜二股）を冬期通行止めにしています（2026年11/19 17時〜4/23 10時の予定。降雪予報で11/27から早まりました）。猿倉へ行けません',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf'), src('長野県大町建設事務所（11/19 開始に変更）', 'https://www.pref.nagano.lg.jp/omachiken/index.html')], None),
    ('norikura', [2, 3], L, '11-13', '04-09',
     '長野県が乗鞍岳線（三本滝〜国民休暇村）を冬期通行止めにする予定（11/13 18時〜4/9 11時）で、三本滝へ車で行けません（三本滝から上は10/31〜4/27）',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('yakedake', [1, 3], L, '11-13', '04-09',
     '長野県が国道158号の旧道（中の湯の1号カーブ〜11号カーブ）を冬期通行止めにする予定（11/13 15時〜4/9 9時）で、新中の湯登山口へ行けません',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('amakazari', [1], L, '11-27', '04-15',
     '長野県が小谷温泉から上の県道（川尻小谷糸魚川線の小谷温泉上〜林道入口）を冬期通行止めにする予定（11/27 15時〜4/15 12時）で、雨飾高原へ行けません。村営バスも11月30日までです',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('shibutsu', [1, 2], L, '11-05', '04-16',
     '群馬県が鳩待峠への県道（尾瀬ヶ原土出線の津奈木橋〜鳩待峠）を冬期閉鎖にする予定（11/5 14時〜4/16 10時）で、鳩待峠へ行けません。戸倉からのバスも11月3日までです',
     [src('群馬県 冬期閉鎖', 'https://www.pref.gunma.jp/06/h2810053.html')], None),
    # 今冬の期間が未発表だが、前季の閉鎖が公式で確かめられた登山口（期間は2026年のバスの運行から数えた目安）
    ('hiuchigatake', [1, 2, 3], L, '10-26', '04-30',
     '冬は国道352号（七入橋〜御池）が冬期規制になり、御池へ行けません（前季は2025年11月4日〜2026年4月24日。今冬の期間は未発表。福島県）。'
     '御池へのバスは2026年は10月25日まででした。期間はバスの運行から数えた目安です',
     [src('福島県 山口土木事務所', 'https://www.pref.fukushima.lg.jp/sec/41361a/road.html')], None),
    ('koganzan', [1], L, '12-14', '04-17',
     '上日川峠へのバスは2026年は12月13日まで。小屋平を通る県道218号も冬期閉鎖で（甲州市：例年1月上旬〜4月中旬）、冬は小屋平へ行けません。期間は2026年のバスの運行から数えた目安です',
     [src('栄和交通', 'https://eiwa-kotsu.jp/root.html'), src('甲州市（県道の冬期閉鎖）', 'https://www.city.koshu.yamanashi.jp/faq/2012033100570/')], None),
    # 今冬の期間がまだ発表されていない閉鎖（from・to なし）
    ('hinata', [1, 3], L, None, None,
     '矢立石登山口への林道（雨乞尾白川線）は冬期閉鎖です。今季の期間は未発表（前季は2025年12月10日〜2026年4月24日。山梨県）',
     [src('山梨県 林道の通行規制', 'https://www.pref.yamanashi.jp/rindoujyouhou/')], None),
    ('bandai', [1], L, None, None,
     '福島県が磐梯山ゴールドラインを11月13日17時から冬期通行止めにしていて、八方台へ行けません。解除は2027年4月下旬ごろの予定です',
     [src('福島県', 'https://www.pref.fukushima.lg.jp/sec/41351a/sv-gl-ll-closed-for-winter.html')], None),
    ('echigokoma', [1, 2], L, None, None,
     '新潟県が国道352号（駒ノ湯入口〜銀山平。枝折峠を含む）を11月4日から冬期通行止めにしていて、枝折峠・銀山平へ行けません。'
     '解除は例年6月下旬で、今季の日は未発表です',
     [src('新潟県 魚沼地域整備部', 'https://www.pref.niigata.lg.jp/site/uonuma-seibi/352toukiheisa.html')], None),
    ('arasawadake', [1, 2], L, None, None,
     '冬は奥只見シルバーラインが閉鎖され、銀山平へ行けません（2026年は3月20日に解除。今冬の閉鎖の開始は未発表。魚沼市）。'
     '銀山平へのバスも11月3日までです',
     [src('魚沼市', 'https://www.city.uonuma.lg.jp/page/1022378.html')], None),
    ('zaosan', [1, 3], L, None, None,
     '冬は蔵王エコーラインが閉鎖され、刈田岳・大黒天へ車で行けません（前季は2024年11月5日〜2025年4月25日。今冬の日付は未発表。宮城県）',
     [src('宮城県', 'https://www.pref.miyagi.jp/documents/35909/r7zaoecholine.pdf')], None),
]

# 代わりのコースの登山口への行き方を、アクセス欄に出すときに使うほかの山（同じ登山口から登る山。2026-11-19）。
# 甲斐駒ヶ岳の竹宇駒ヶ岳神社は、同じ登山口の山が無い（日向山の経路は矢立石まで）ので行き方は出さない
ALT_FROM = {'yari': 'kasagatake'}

# 季節運行の乗り物が止まる期間は電車・バスで行けない（car_only）。(山, [コースの番号], 乗り物の見つけ方)
# 見つけ方：annualItems の transport の label に含まれる語、または 'op'（コースのアクセスの operation）
CAR_ONLY = [
    ('mizugaki', [1, 3], '韮崎瑞牆線'), ('yatsugatake', [2], 'op'), ('kirigamine', [4], '霧ヶ峰線'),
    ('aizu_koma', [1, 2, 3], '檜枝岐'), ('kayagatake', [1, 2, 3], '韮崎深田公園線'),
    ('hiuchi', [1, 2], 'op'), ('takatsuma', [1, 2], '戸隠'),
    ('ontakesan', [1], '田の原'), ('shiomidake', [1, 2], '鳥倉'), ('terkari', [1], '易老渡'), ('yakushidake', [1], '折立'),
    ('kurobegorodam', [1, 3], '折立'), ('hakusan', [1, 2], '市ノ瀬'), ('karisaka', [1, 2, 3], '西沢渓谷'),
    ('nokogiriyama', [1], 'ジオライナー'), ('mitosaan', [1, 2], '都民の森'), ('tengudake', [1, 3], '渋の湯'),
]


# 3回目（2026-11-23。運営者の指示「33山を調べて」）：冬山装備の月があるのに冬の印が無かった33山を、県の冬期通行止めの一覧などで確かめた
GUNMA_R8 = src('群馬県 冬期閉鎖（令和8年度）', 'https://www.pref.gunma.jp/site/houdou/779146.html')
CLOSED += [
    ('nikko_shirane', [2], L, '12-25', '04-23',
     '群馬県が国道120号（金精道路の金精トンネル〜丸沼スキー場入口）を冬期閉鎖にする予定（12/25 12時〜4/23 12時）で、菅沼へ行けません',
     [GUNMA_R8], None),
    ('shirane_gunma', [1], L, '11-11', '04-21',
     '群馬県が国道292号（志賀草津道路の天狗山ゲート〜渋峠）を冬期閉鎖にしていて（11/11 13時〜4/21 10時の予定）、弓池へ行けません',
     [GUNMA_R8], None),
    ('azuma', [3], L, '11-04', '04-30',
     '県道の西吾妻スカイバレーが2026年11月4日から冬期通行止めで、白布峠へ行けません。解除は2027年4月下旬ごろの予定です',
     [src('福島県 猪苗代土木事務所', 'https://www.pref.fukushima.lg.jp/sec/41351a/sv-gl-ll-closed-for-winter.html')], None),
    ('hiragadake', [1, 2], L, '11-04', '06-30',
     '国道352号が2026年11月4日から冬期通行止めで（新潟側は駒ノ湯入口〜銀山平・銀山平〜県境、福島側は県境〜御池）、登山口へ行けません。解除は例年6月下旬です',
     [src('新潟県 魚沼地域振興局', 'https://www.pref.niigata.lg.jp/site/uonuma-seibi/352toukiheisa.html'),
      src('福島県 山口土木事務所', 'https://www.pref.fukushima.lg.jp/sec/41361a/road.html')], None),
    ('nishihotaka', [3], L, '11-16', '04-16',
     '上高地へは一年じゅう一般車が入れず（マイカー規制）、バスは2026年は4月17日〜11月15日でした。期間外は上高地へバス・車で行けません',
     [src('アルピコ交通 上高地線', 'https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/'),
      src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
    ('yarigatake2', [3], L, '10-13', '07-10',
     '椹島へは一般車が入れず、畑薙第一ダムからの送迎バス（山小屋の宿泊者だけ）は2026年は7月11日〜10月12日でした。期間外は椹島へ行けません',
     [src('特種東海フォレスト', 'https://www.t-forest.com/alpsinfo/bus/')], None),
    ('karamatsu', [3], L, '11-19', '04-23',
     '下山口の猿倉への県道（白馬岳線の猿倉〜二股）を長野県が冬期通行止めにしています（2026年11/19 17時〜4/23 10時の予定。降雪予報で11/27から早まりました）。猿倉から帰れません',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf'), src('長野県大町建設事務所（11/19 開始に変更）', 'https://www.pref.nagano.lg.jp/omachiken/index.html')], None),
]
NEW33 = {('nikko_shirane', 2), ('shirane_gunma', 1), ('azuma', 3), ('hiragadake', 1), ('hiragadake', 2), ('nishihotaka', 3), ('yarigatake2', 3), ('karamatsu', 3)}
# 車は通年で行けるが、電車・バスは行けない（annualItems に項目が無いので期間を直接書く）
CAR_ONLY_FIXED = {
    ('houou', 1): None,
    ('houou', 3): None,
}
HOUOU_CAR = {
    'state': 'car_only', 'label': '冬は電車・バスで行けない', 'from': '11-04', 'to': '06-25',
    'text': '夜叉神峠を通るバスは2026年は6月26日〜11月3日です。夜叉神までの林道は山梨県の案内で通年通行できるので、車では行けます',
    'sources': [src('山梨県 南アルプスマイカー規制', 'https://www.pref.yamanashi.jp/minami-alps-ks/50915161945.html')],
}
# 公式の案内で冬に行けるか確かめられなかったコース。推測で「行ける」「行けない」にしない
UNKNOWN = {
    'kobushigatake': [1, 2, 3], 'houou': [2], 'keirisan': [1, 2, 3], 'asama': [1, 2, 3], 'nikko_shirane': [1, 3],
    'takeson': [1, 2, 3], 'myoko': [1, 2, 3], 'makihata': [1, 2, 3], 'iide': [1, 2, 3], 'shirane_gunma': [2],
    'iwasugesan': [1, 2, 3], 'iizunasan': [1, 2, 3], 'kurohimesan': [1, 2, 3], 'nakawarayama': [1, 2], 'yarigatake2': [1, 2],
    'gakedake': [1, 2], 'adatara': [1, 2, 3], 'azuma': [2], 'naeba': [1, 2, 3], 'sukai': [1, 2], 'utsugi': [1, 2, 3],
    'enasan': [1, 2, 3], 'minamikomagatake': [1, 2], 'tairappyo': [1, 2, 3], 'azumayasan': [1, 2, 3], 'sennokurayama': [1, 2],
}
UNKNOWN_NOTE = {
    ('adatara', 1): 'あだたら山ロープウェイの登山向けの運行は2026年は11月8日まで毎日、11月29日まで土日祝だけで、このコースは冬は使えません。',
}


def unknown_winter(mid, n, route):
    start = re.split('〜', route.get('name') or '')[0]
    text = UNKNOWN_NOTE.get((mid, n), '') + start + 'へ行く道路やバスが冬に使えるかは、公式の案内で確かめられていません。出かける前に自治体・宿・バス会社に確かめてください'
    return {'state': 'unknown', 'label': '冬の道路は未確認', 'text': text, 'lastVerified': DAY3}


# 4回目（2026-11-23。MUSE の調査結果を、出典のページを開いて確かめたものだけ）
NAGANO_R8 = src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')
NIIGATA_352 = src('新潟県 魚沼地域振興局', 'https://www.pref.niigata.lg.jp/site/uonuma-seibi/352toukiheisa.html')
YUZAWA = src('湯沢町 登山情報', 'https://www.town.yuzawa.lg.jp/soshikikarasagasu/kikkakusangyoukankoubu/kankyonorinka/9/2/3/1029.html')
OKUWA = src('大桑村 登山情報のお知らせ', 'https://www.vill.okuwa.lg.jp/kanko/miru-asobu/chuoalpstozan/chuuouarupusutozanntozannjouhounooshirase.html')
ZAO = src('蔵王町観光物産協会', 'https://www.zao-machi.com/news/257.html')
TOYAMA = src('富山県 有峰林道', 'https://www.pref.toyama.jp/documents/58006/ariminerinndouitizu.pdf')
INAGAWA = '2026年6月28日の法面崩落で、伊奈川専用林道が歩行者も含めて全面通行止めです。復旧の目途は立っておらず、大桑村側から登れません'
# (山, コース, 印, from, to, 文, 出典, 追加の項目)。解除日が未発表なら from・to は入れず、closeFrom と電車・バスで行けない期間を持つ
M4 = [
    ('keirisan', [1], L, '11-20', '06-20', '佐久市が林道大河原線・唐沢線（蓼科スカイライン）を2026年11月20日正午から通行止めにし、立科町の町道夢の平線も通行止めで、七合目登山口へ行けません。解除は2027年6月中旬ごろの予定です',
     [src('佐久市 林道の通行', 'https://www.city.saku.nagano.jp/machizukuri/ringyo/chui/rinndoutuukou.html')], {}),
    ('hiuchi', [1, 2], L, '11-06', '04-30', '県道39号妙高高原公園線が2026年11月6日14時から冬季通行止めで、迂回路が無く笹ヶ峰へ行けません。解除は2027年4月下旬の予定です',
     [src('妙高観光局', 'https://myokotourism.jp/news/%e3%80%90%e9%80%9a%e8%a1%8c%e6%ad%a2%e3%82%81%e3%80%91%e7%ac%b9%e3%83%b6%e5%b3%b0%e3%81%b8%e3%81%ae%e9%81%93%e8%b7%af%e5%86%ac%e5%ad%a3%e9%96%89%e9%8e%96%e3%81%ae%e3%81%8a%e7%9f%a5%e3%82%89%e3%81%9b/')], {'trainFrom': '10-26', 'trainTo': '07-10'}),
    ('zaosan', [1, 3], L, '11-04', '04-23', '蔵王エコーライン・ハイラインが2026年11月4日17時から2027年4月23日11時（予定）まで冬期通行止めで、車で行けません', [ZAO], {}),
    ('arasawadake', [1, 2], L, None, None, '国道352号の冬期通行止め（2026年11月4日から）の区間の外で、銀山平へは奥只見シルバーラインで車で行けます（11月23日時点）。シルバーラインも冬は閉鎖されますが、今冬の開始は未発表です。銀山平へのバスは11月3日までです', [src('魚沼市 通行止めのお知らせ', 'https://www.city.uonuma.lg.jp/page/1022378.html')], {'trainFrom': '11-04', 'trainTo': '05-31'}),
    ('echigokoma', [1], L, '11-04', '06-30', '国道352号（駒ノ湯入口〜石抱橋。枝折峠を含む）が2026年11月4日9時から冬期通行止めで、枝折峠へ行けません。解除は例年6月下旬です', [NIIGATA_352], {}),
    ('echigokoma', [2], L, None, None, '国道352号の冬期通行止め（2026年11月4日から）の区間の外で、石抱橋へは奥只見シルバーラインで車で行けます（11月23日時点）。シルバーラインも冬は閉鎖されますが、今冬の開始は未発表です', [src('魚沼市 通行止めのお知らせ', 'https://www.city.uonuma.lg.jp/page/1022378.html')], {}),
    ('bandai', [1], L, '11-13', '04-30', '磐梯山ゴールドラインが2026年11月13日17時から冬期通行止めで、八方台へ行けません。解除は2027年4月下旬ごろの予定です',
     [src('福島県 猪苗代土木事務所', 'https://www.pref.fukushima.lg.jp/sec/41351a/sv-gl-ll-closed-for-winter.html')], {}),
    ('ontakesan', [1], L, None, None, '村道41号線（八海山〜田の原）が2026年11月5日から冬期全面通行止めで、田の原へ行けません。来春の解除日はこのサイトでは確かめられていません',
     [src('御嶽山ビジターセンター', 'https://ontake-vc.jp/yamanews/20261029/')], {'closeFrom': '11-05', 'trainFrom': '10-19', 'trainTo': '07-03'}),
    ('yakushidake', [1], L, None, None, '有峰林道が2026年11月13日から冬期閉鎖で、折立へ行けません。来季の開通日は未発表です', [TOYAMA], {'closeFrom': '11-13', 'trainFrom': '09-28', 'trainTo': '07-10'}),
    ('kurobegorodam', [1, 3], L, None, None, '有峰林道が2026年11月13日から冬期閉鎖で、折立へ行けません。来季の開通日は未発表です', [TOYAMA], {'closeFrom': '11-13', 'trainFrom': '09-28', 'trainTo': '07-10'}),
    ('hakusan', [1, 2], L, None, None, '白山公園線（白峰の風嵐〜別当出合）が2026年11月18日から冬季閉鎖で、市ノ瀬・別当出合へ行けません。例年春ごろまでで、来春の解除日は未発表です',
     [src('白山市 観光サイト', 'https://www.urara-hakusanbito.com/topic/detail_142.html')], {'closeFrom': '11-18', 'trainFrom': '10-14', 'trainTo': '07-03'}),
    ('naeba', [1], L, None, None, '祓川登山口の駐車場までの道路が2026年11月20日から通行止めです。来春の解除日は未発表です', [YUZAWA], {'closeFrom': '11-20', 'trainFrom': '11-20', 'trainTo': '03-31'}),
    ('naeba', [3], L, None, None, '町道赤湯線（苗場スキー場〜小日橋）が2026年11月9日から冬期通行止めで、小日橋まで車で行けません。赤湯温泉山口館も今年度の営業を終えました。来春の解除日は未発表です', [YUZAWA], {'closeFrom': '11-09'}),
    ('enasan', [2], L, None, None, '神坂峠へ通じる林道大谷霧ヶ原線を、中津川市が2026年11月20日に通行止めにしました。来春の解除日は未発表です',
     [src('中津川市 林道の通行', 'https://www.city.nakatsugawa.lg.jp/life/rt/5/1/25452.html')], {'closeFrom': '11-20'}),
    ('adatara', [1], '冬はロープウェイなし', '11-24', '04-10', 'あだたら山ロープウェイの通常の運行は2026年は4月11日〜11月23日です。来季の開始日は未発表で、期間は2026年の運行から数えた目安です',
     [src('あだたら高原リゾート', 'https://www.adatara-resort.com/green/about/index.html')], {}),
    ('makihata', [1, 2, 3], '冬は桜坂へ車で行けない', None, None, '新潟県警の冬山情報によると、冬は清水集落から桜坂駐車場まで積雪で車が通れず、清水集落にも駐車場がありません',
     [src('新潟県警察 冬山情報（巻機山）', 'https://www.pref.niigata.lg.jp/site/kenkei/osirase-anzen-ansin-mizuyamajsetugaijiko-sangaku-huyuyama-jouhou-makihata-makihata.html')], {}),
    ('minamikomagatake', [1, 2], '災害で通行止め', '01-01', '12-31', INAGAWA, [OKUWA], {}),
    ('utsugi', [3], '災害で通行止め', '01-01', '12-31', INAGAWA, [OKUWA], {}),
]
# 公式の運行・通行の案内を確かめたので「未確認」の印を外すコース
CONFIRMED_OPEN = {'asama': [1, 2], 'myoko': [1, 3], 'iizunasan': [1, 2, 3], 'tairappyo': [1, 2, 3], 'sennokurayama': [1],
                  'kobushigatake': [3], 'nakawarayama': [2]}


def mmdd(d, delta):
    x = datetime.date.fromisoformat(d) + datetime.timedelta(days=delta)
    return x.strftime('%m-%d')


def main():
    raw = open(MP, encoding='utf-8').read()
    M = json.loads(raw)
    A = json.load(open(AP, encoding='utf-8'))
    by = {m['id']: m for m in M}
    want = {}
    for mid, nums, label, f, t, text, sources, alt in CLOSED:
        for n in nums:
            w = {'state': 'closed', 'label': label}
            if f and t:
                w.update({'from': f, 'to': t})
            w.update({'text': text, 'sources': sources, 'lastVerified': DAY3 if (mid, n) in NEW33 else DAY})
            if alt:
                w['alt'] = alt
                if ALT_FROM.get(mid):
                    w['altAccessFrom'] = ALT_FROM[mid]
            want[(mid, n)] = w
    for mid, nums, key in CAR_ONLY:
        m = by[mid]
        for n in nums:
            r = m['routes'][n - 1]
            assert r.get('byTrain'), (mid, n, '電車のバッジが無いコース')
            if key == 'op':
                a = A[r['accessId']]
                op = a['operation']
                vf, vt, name, url = op['validFrom'], op['validTo'], a['name'], a.get('sourceUrl')
            else:
                its = [x for x in m.get('annualItems') or [] if x.get('kind') == 'transport' and key in x.get('label', '')]
                assert len(its) == 1, (mid, key, len(its))
                vf, vt, name, url = its[0]['validFrom'], its[0]['validTo'], its[0]['label'], its[0].get('sourceUrl')
            assert vf and vt, (mid, n)
            assert (mid, n) not in want, (mid, n)
            want[(mid, n)] = {'state': 'car_only', 'label': '冬は電車・バスで行けない', 'from': mmdd(vt, 1), 'to': mmdd(vf, -1),
                              'text': '%sは2026年は%s〜%s（期間外は電車・バスで行けない。来季の開始は未発表なので2026年の日付で数えた）' % (
                                  name, vf, vt),
                              'sources': [src(name, url)] if url else [], 'lastVerified': DAY}
    for key in CAR_ONLY_FIXED:
        assert key not in want, key
        assert by[key[0]]['routes'][key[1] - 1].get('byTrain'), key
        want[key] = dict(HOUOU_CAR, lastVerified=DAY3)
    for mid, nums in UNKNOWN.items():
        for n in nums:
            assert (mid, n) not in want, (mid, n)
            want[(mid, n)] = unknown_winter(mid, n, by[mid]['routes'][n - 1])
    for mid, nums, label, f, t, text, sources, more in M4:
        for n in nums:
            w = {'state': 'closed', 'label': label}
            if f and t:
                w.update({'from': f, 'to': t})
            w.update(more)
            w.update({'text': text, 'sources': sources, 'lastVerified': DAY3})
            want[(mid, n)] = w
    for mid, nums in CONFIRMED_OPEN.items():
        for n in nums:
            assert want[(mid, n)]['state'] == 'unknown', (mid, n)
            del want[(mid, n)]
    # このスクリプトで入れた分を入れ直す（金峰山は別のスクリプト）
    changed = set()
    targets = {mid for mid, _ in want}
    for m in M:
        if m['id'] == 'kinpusan':
            continue
        for i, r in enumerate(m.get('routes') or [], start=1):
            w = want.get((m['id'], i))
            if r.get('winter') != w:
                if w is None:
                    if 'winter' in r:
                        del r['winter']
                        changed.add(m['id'])
                else:
                    r['winter'] = w
                    changed.add(m['id'])
    for mid in changed:
        by[mid]['mountainUpdated'] = max(by[mid].get('mountainUpdated') or '', DAY)
    open(MP, 'w', encoding='utf-8').write(json.dumps(M, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
    print('対象', len(targets), '山', len(want), 'コース。変えた山', len(changed))
    print(' '.join(sorted(changed)))


if __name__ == '__main__':
    main()
