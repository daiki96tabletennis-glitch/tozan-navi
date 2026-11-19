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
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MP = os.path.join(ROOT, 'data', 'mountains.json')
AP = os.path.join(ROOT, 'data', 'accesses.json')
DAY = '2026-11-19'
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
    ('shirouma', [2], L, '11-27', '04-23',
     '長野県が猿倉への県道（白馬岳線の猿倉〜二股）を冬期通行止めにする予定（11/27 10時〜4/23 10時）で、猿倉へ行けません',
     [src('長野県 冬期通行止め予定（令和8年度）', 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf')], None),
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
            w.update({'text': text, 'sources': sources, 'lastVerified': DAY})
            if alt:
                w['alt'] = alt
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
