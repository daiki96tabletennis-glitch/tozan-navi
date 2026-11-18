"""外部の監査（ChatGPT。2026-11-18 に運営者から）を公式・現地の情報で確かめて直す（運営者の指示「これを元に調査して適宜改善して」）

確かめて直したもの（何度流しても同じ結果）：
- 丹沢山：よくある質問の難易度の答えに「大倉から塔ノ岳を経由する…往復7〜8時間程度」が残っていた。
  コース一覧（YAMAP）は大倉からの往復 10時間49分。数字をコース一覧に合わせる
- 大倉駐車場：塔ノ岳だけ「約80台・500円」で、丹沢山・蛭ヶ岳・鍋割山・三ノ塔と食い違っていた。
  県立秦野戸川公園の公式（https://www.kanagawa-park.or.jp/hadanotokawa/access.html）：普通車150台、
  土日祝・夏季・年末年始は当日最大800円、ほかの平日は当日最大500円（30分未満無料）、入庫6:30〜21:00。5山を同じ文にする
- 美ヶ原：ビーナスラインなどの冬期通行止め（長野県「令和8年度 冬期通行止め予定」2026-10-21 作成の一覧：
  美ヶ原公園東餅屋線・美ヶ原公園沖線・松本和田線など R8.11.18 11:00〜R9.4.20 11:00）を annualItems の closure に足す
- 冬の絶景（winter_specials.json の views）：
  西吾妻山を「雪山入門の候補」から「冬山の経験者向け」へ（12月は冬山装備、1〜3月はスノーシュー等の時期で、
  天元台の冬の案内は「ゲレンデ・コース以外はすべて立入禁止区域（管理区域外）」。無雪期の3時間36分を冬に当てはめない）
  赤城山：2026-27年の冬ダイヤは関越交通が 2026-11-13 に発表済み（12/1〜3/31。土日祝は前橋駅から直通、平日は富士見温泉で乗り換え）
  入笠山：冬はゴンドラ山頂駅から山頂までスノーシューで往復約3時間（富士見パノラマリゾート）。無雪期の2時間1分と分けて書く
- ダイヤモンド富士（diamond）：
  七面山の計算地点を山頂（1,989m）から敬慎院（随身門のあたり）に（ダイヤモンド富士を見る場所は山頂近くの敬慎院の随身門。
  位置は国土地理院の地名検索「敬慎院」、標高は国土地理院の標高API（1m メッシュ）で 1,717.7m）
  塔ノ岳・石割山・竜ヶ岳の注記：暗い時間の登り下り
- 温泉・サウナの記事（onsen_sauna.json）：安達太良山のロープウェイは、2026年は11月8日まで毎日、
  11月29日までは土日祝だけの運行（あだたら高原リゾートの公式サイト 2026-11-18）。冬はこのコースを使えないことを書く
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(rel):
    return json.load(open(os.path.join(ROOT, rel), encoding='utf-8'))


def save(rel, d):
    p = os.path.join(ROOT, rel)
    nl = open(p, encoding='utf-8').read().endswith('\n')   # 前のファイルの終わりの改行に合わせる
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        if nl:
            f.write('\n')


def once(s, a, b):
    if b in s:
        return s
    if s.count(a) != 1:
        raise SystemExit('置き換え元が1か所でない：' + a[:40])
    return s.replace(a, b)


OKURA = '大倉駐車場（県立秦野戸川公園・普通車150台・土日祝は当日最大800円・平日は当日最大500円・入庫6:30〜21:00）'
OKURA_IDS = ('tanzawa', 'tonosaki', 'hirugata', 'nabewari', 'sannotou')


def mountains():
    ms = load('data/mountains.json')
    by = {m['id']: m for m in ms}
    # 丹沢山のよくある質問
    f = by['tanzawa']['faq'][0]
    f['answer'] = once(f['answer'],
                       '大倉から塔ノ岳を経由する縦走路はブナ林が美しく道自体は迷いにくいですが、標高差が大きく行動時間が長め（往復7〜8時間程度）になるため、日の出後すぐの早出が安心です。',
                       '大倉から塔ノ岳を経由する道はブナ林が美しく道自体は迷いにくいですが、標高差が大きく、大倉からの往復は10時間49分（休憩を含まないコースタイム）と長いため、山小屋に泊まる計画か、日の出の前後に歩き始める計画にしましょう。')
    # 大倉駐車場
    for i in OKURA_IDS:
        if not (by[i].get('parking') or '').startswith('大倉駐車場'):
            raise SystemExit('大倉駐車場でない：' + i)
        by[i]['parking'] = OKURA
    # 美ヶ原の冬期通行止め
    u = by['utsukushigahara']
    items = u.setdefault('annualItems', [])
    label = 'ビーナスラインなどの冬期通行止め（扉峠〜美ヶ原・美ヶ原〜和田峠・武石峠など）'
    if not any(a.get('label') == label for a in items):
        items.append({
            'kind': 'closure', 'label': label,
            'validFrom': '2026-11-18', 'validTo': '2027-04-20', 'seasonYear': '2026〜27',
            'sourceUrl': 'https://www.pref.nagano.lg.jp/michikanri/infra/doro/joho/hiroba/documents/r8tokiheisa.pdf',
            'lastVerified': '2026-11-18',
            'note': '11/18 11時〜4/20 11時の予定。長和町からの県道178号（美ヶ原和田線）はこの一覧に無い。冬に車で行くときは冬用タイヤと現地の道路情報を確かめる',
        })
    save('data/mountains.json', ms)


def winter():
    w = load('data/winter_specials.json')
    v = {x['id']: x for x in w['views']['mountains']}
    a = v['azuma']
    a['category'] = 'expert'
    a['winterAccess'] = ('天元台ロープウェイ（8:00〜17:00）と冬のリフトで北望台へ。北望台行きのリフトの最終は15:00。2026-27年は11月28日から冬の営業（点検の運休日あり）。'
                         '12月は冬山装備、1〜3月は深い雪でスノーシューなどが要る時期で、天元台はゲレンデ・コースの外を管理区域外としている。'
                         '代表コースの3時間36分は雪の無い時期の時間')
    k = v['akagi']
    k['winterAccess'] = ('前橋駅からのバスは2026年12月1日〜2027年3月31日が冬ダイヤ（関越交通。2026-11-13 発表）。'
                         '土日祝は前橋駅から赤城山への急行バス（直通）、平日は富士見温泉で乗り換え（富士見温泉から山頂方面は1日4本）')
    k['winterLinks'] = [
        {'label': '冬ダイヤの時刻表（土日祝）', 'url': 'https://kan-etsu.net/files/libs/14686/202611131729401095.pdf'},
        {'label': '冬ダイヤの時刻表（平日）', 'url': 'https://kan-etsu.net/files/libs/14685/202611131729328577.pdf'},
        {'label': '関越交通（赤城山）', 'url': 'https://kan-etsu.net/pages/42/'},
    ]
    k['winterShort'] = 'バスは12/1〜3/31が冬ダイヤ（平日は富士見温泉で乗り換え）'
    n = v['nyukasayama']
    n['winterAccess'] = once(n['winterAccess'], '富士見駅からの無料送迎バスも冬は毎日（9:15・10:00発、予約不要）',
                             '富士見駅からの無料送迎バスも冬は毎日（9:15・10:00発、予約不要）。冬はゴンドラ山頂駅から山頂までスノーシューで往復約3時間（雪の無い時期の2時間1分より長い）。11月16日〜12月11日はゴンドラが動かない')
    D = w['diamond']
    D['viewpoints']['nanaitsurasan'] = {
        'name': '敬慎院の随身門のあたり',
        'lat': 35.376471, 'lng': 138.355749, 'ele': 1717.7,
        'why': 'ダイヤモンド富士を見る場所は、山頂（1,989m）ではなく山頂近くの敬慎院の随身門のため（身延山久遠寺の案内）。山頂で計算すると日がずれる',
        'source': '国土地理院の地名検索「敬慎院」の位置と、その地点の標高（国土地理院の標高API・1mメッシュ）',
    }
    D['note']['tonosaki'] = ('日没のあと大倉へ下ると、暗い道を長く歩くことになります。2月は軽アイゼン等の時期で、凍った道を暗い中で下るのは危険です。'
                             '山頂の尊仏山荘（予約）に泊まる計画をおすすめします')
    D['note']['ishiwariyama'] = '1月は軽アイゼン等の時期です。日没のあと、雪や凍結の残る道を暗い中で下ることになるので、早めに下りられる計画にしましょう'
    D['note']['ryugatake'] = once(D['note']['ryugatake'], 'という登山記録があります。',
                                  'という登山記録があります。日の出に間に合うよう暗いうちに歩き始めることになるので、ヘッドランプを持ち、冬（12〜2月）は軽アイゼン等を持っていきましょう。')
    save('data/winter_specials.json', w)


def onsen():
    o = load('data/onsen_sauna.json')
    p = next(x for x in o['plans'] if x['id'] == 'adatara')
    f = next(x for x in p['facilities'] if x['key'] == 'okudake')
    f['note'] = ('ロープウェイは2026年は11月8日まで毎日、11月29日までは土日祝だけの運行です（あだたら高原リゾート）。'
                 'それより後の冬はこのコースを使えず、山は冬山装備が要る雪山になります')
    save('data/onsen_sauna.json', o)


if __name__ == '__main__':
    mountains()
    winter()
    onsen()
    print('ok')
