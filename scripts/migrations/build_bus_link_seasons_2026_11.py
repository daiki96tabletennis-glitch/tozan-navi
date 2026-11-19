"""電車・バスの欄のバスの時刻表のボタン（.ts-link-bus）を、そのバスが走る期間だけ見せるための対応表を作る（2026-11-19。運営者の指示
「バスの時刻表リンクが機能していない間はリンクは見えない様にして欲しい（次のダイヤが出て運行期間前でも見れるようにする）見えないだけで裏では持っておく」）

data/bus_link_seasons.json：{山ID: {リンクのURL: annualItems の label か "operation"（新しい形の山の代表コースのアクセスの運行期間）}}。
gen_mountain_pages.py の bus_link_periods が、その期間（validFrom・validTo）をリンクの data-bus-from / data-bus-to に書き、
mountain-engine.js が、開いた日が validTo を過ぎていたらリンクを隠す。次のダイヤが出て annualItems の期間を来季に直すと、
運行期間の前でも見えるようになる。リンクそのもの（trainRoutes.links）は消さない。

入れていない（いつも見せる）リンク：通年走るバスの時刻表（唐松岳の長野－白馬線・那須岳の関東バスの路線一覧・西吾妻山の山交バス・
乗鞍岳の乗鞍高原線・光岳の信南交通 遠山郷線・三頭山の西東京バス・越後駒ヶ岳の南越後交通・白馬岳・木曽駒ヶ岳）、
季節ダイヤ（transitSeasons）の山（入笠山・赤城山・谷川岳。季節ごとに時刻表を差し替える）、林道の状況の案内（常念岳）、
季節の期間をデータに持っていないリンク（鳳凰山の広河原線・雁坂嶺の山梨市のバス・富士山の富士急バス・日光白根山の関越交通）。
何度流しても同じ結果。このあと gen_mountain_pages.py --all
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OP = 'operation'
KAMIKOCHI = '松本〜新島々〜上高地の路線バス'
SAWAYAKA = 'https://www.alpico.co.jp/traffic/sawayaka/route/kamikochi/shinjuku/'
SHIN = 'https://www.alpico.co.jp/traffic/local/kamikochi/shinshimashima/'
HIRO = ('https://ykbus.jp/travel/hirogawara/', '甲府駅〜広河原の南アルプス登山バス')
NAKABUSA = ('https://nan-an.co.jp/nakabusa/', '穂高駅〜中房温泉の定期バス')
OGI = ('https://www.alpico.co.jp/traffic/local/hakuba/ogizawa/', '信濃大町駅〜扇沢の路線バス')
TF = ('https://www.t-forest.com/alpsinfo/bus/', '畑薙第一ダム〜椹島の送迎バス')
ARI = ('https://www.chitetsu.co.jp/?page_id=741', '富山駅〜折立の夏山バス')
URA = ('https://uraginzabus.com/', '信濃大町駅〜七倉の裏銀座登山バス')
DAIBO = ('https://eiwa-kotsu.jp/root.html', '甲斐大和駅〜上日川峠のバス')
MAP = {
    # 新しい形の山（代表コースのアクセスの運行期間）
    'okutama': {'https://eiwa-kotsu.jp/root.html': OP},
    'kinpusan': {'https://eiwa-kotsu.jp/oodarumi.html': OP},
    'yatsugatake': {'https://www.alpico.co.jp/traffic/local/suwa/': OP},
    'komagatake': {'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_jikokuhyo.html': OP},
    'senjogatake': {'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_jikokuhyo.html': OP},
    'yari': {SAWAYAKA: OP, SHIN: OP},
    'hotaka': {SAWAYAKA: OP, SHIN: OP},
    'shibutsu': {'https://kan-etsu.net/pages/43/': OP},
    'hiuchigatake': {'https://www.aizubus.com/': OP},
    'hiuchi': {'https://myokotourism.jp/access/': OP},
    # 旧い形の山（annualItems の乗り物）
    'kitadake': dict([HIRO]), 'ainodake': dict([HIRO]), 'noutori': dict([HIRO]),
    'keirisan': {'https://www.alpico.co.jp/traffic/local/suwa/': '茅野駅〜蓼科山登山口方面のバス（蓼科高原ラウンドバス）'},
    'kirigamine': {'https://www.alpico.co.jp/traffic/local/suwa/': '上諏訪駅〜霧ヶ峰の路線バス（霧ヶ峰線）'},
    'tateyama': {'https://www.alpen-route.com/timetable/': '立山黒部アルペンルート'},
    'tsurugi': {'https://www.alpen-route.com/timetable/': '立山黒部アルペンルート'},
    'aizu_koma': {'https://www.aizubus.com/rosen': '会津高原尾瀬口駅〜檜枝岐のバス（滝沢登山口まで）'},
    'kayagatake': {'http://cus4.kyohoku.jp/routebus/kayagatakemizugakidenen-bus/schedule-fukadakoenline/': '韮崎駅〜深田記念公園のバス（韮崎深田公園線）'},
    'yakedake': {SAWAYAKA: '松本〜新島々〜上高地の路線バス（中の湯経由）', SHIN: '松本〜新島々〜上高地の路線バス（中の湯経由）'},
    'chogatake': {SAWAYAKA: KAMIKOCHI, SHIN: KAMIKOCHI},
    'kashimayari': dict([OGI]), 'harinokidake': dict([OGI]),
    'koganzan': dict([DAIBO]),
    'shirasunayama': {'https://www.town.nakanojo.gunma.jp/soshiki/4/3615.html': '長野原草津口駅〜野反湖の六合地区路線バス'},
    'arasawadake': {'https://minamiechigo.co.jp/pdf/koide/jikoku/weekday/okutadamiR6-4-all-w.pdf': '浦佐駅〜銀山平・奥只見ダムの急行バス'},
    'arikayama': dict([NAKABUSA]), 'otenshoudake': dict([NAKABUSA]), 'tsubakurodake': dict([NAKABUSA]),
    'echigokoma': {'https://www.iine-uonuma.jp/31055/': '大湯公園・白銀の湯〜枝折峠の「うおぬま滝雲シャトルバス」'},
    'amakazari': {'https://www.vill.otari.nagano.jp/soshiki/kankochiikishinko-kankoshoko/gyomu/9/1/163.html': '南小谷駅〜雨飾高原の村営バス'},
    'takatsuma': {'https://www.alpico.co.jp/traffic/express/express_togakushi/': '長野駅〜戸隠キャンプ場の観光特急戸隠線（予約制）'},
    'ontakesan': {'https://ontakekotsu.com/regular': '木曽福島駅〜田の原のバス（田の原線）'},
    'utsukushigahara': {'https://www.utsukushigahara-bus.net/': '松本駅〜美ヶ原自然保護センターの直行バス'},
    'shiomidake': {'https://www.ibgr.jp/general-route/torikura_off2/': '伊那大島駅〜鳥倉登山口の登山バス（鳥倉線）'},
    'arakawadake': dict([TF]), 'akaisidake': dict([TF]), 'hijiridade': dict([TF]),
    'terkari': {'https://tohyamago.com/archives/3681': '道の駅遠山郷〜易老渡の予約制タクシー'},
    'yakushidake': dict([ARI]), 'kurobegorodam': dict([ARI]),
    'hakusan': {'https://www.hokutetsu.co.jp/tourism-bus/': '金沢駅〜市ノ瀬の白山登山バス'},
    'nokogiriyama': {'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_jikokuhyo.html': '茅野駅〜戸台パークの南アルプスジオライナー'},
    'eboshidake_kita': dict([URA]), 'noguchigoro': dict([URA]),
    'tengudake': {'https://www.alpico.co.jp/traffic/local/suwa/shibunoyu/': '茅野駅〜渋の湯のバス（奥蓼科渋の湯線）'},
}

M = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
for mid, links in MAP.items():
    m = M[mid]
    urls = {l.get('url') for l in (m.get('trainRoutes') or {}).get('links') or []}
    labels = {a.get('label') for a in m.get('annualItems') or [] if a.get('kind') == 'transport'}
    for url, ref in links.items():
        assert url in urls, (mid, url)
        assert ref == OP and m.get('dataModel') == 'ssot-v1' or ref in labels, (mid, ref)
out = {'_note': '電車・バスの欄のバスの時刻表のボタンを、そのバスが走る期間だけ見せる対応表（scripts/migrations/build_bus_link_seasons_2026_11.py が作る。手で編集しない）。'
                '値は annualItems の label か operation（新しい形の山の代表コースのアクセスの運行期間）'}
out.update({k: MAP[k] for k in sorted(MAP)})
open(os.path.join(ROOT, 'data', 'bus_link_seasons.json'), 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
print('ok', len(MAP))
