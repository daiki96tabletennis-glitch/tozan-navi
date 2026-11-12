"""季節運行の印があるのに運行期間が入っていなかった6山の、電車・バスの運行期間を入れる（2026-11-11。運営者の指示）

運行期間（validFrom / validTo）があると、山ページの FAQ・季節の表（build_derived.py）、期限の見張り（check_annual_updates.py）、
アクセス難易度（build_access_tier.py）、月ごとの数え方（transit_months.py）がその期間で動く。

- 至仏山（accesses.json の hatomachi-toge）：戸倉〜鳩待峠の乗合バス・乗合タクシー 2026-04-18〜11-03
    群馬県「2026年 尾瀬国立公園の交通対策のお知らせ」（PDF）「乗合バス・タクシー運行予定 2026年4月18日（土）〜2026年11月3日（火祝）」
- 燧ヶ岳（oze-miike）：会津バス 檜枝岐線（会津田島駅〜尾瀬御池）2026-05-01〜10-25
    会津バスのお知らせ（2026-04-23「2026年5月1日 田島・山口管内 路線バスダイヤ改正」）と「尾瀬を越えて行こう」
    （檜枝岐線 2026年5月23日〜10月25日。5月23日までは会津田島駅〜尾瀬御池のみの運行）
- 常念岳（ichinosawa）：林道一ノ沢線をタクシーで崩落箇所の手前まで行ける期間 2026-04-17〜11-26
    冬期通行止めの解除 2026-04-17 13時（安曇野市山岳サポーターズ・市民タイムス）、冬期通行止め 2026-11-27 10時から（安曇野市）。
    崩落箇所から一ノ沢登山口まで約1.5kmは歩く（復旧工事の竣工予定は2027年1月末＝安曇野市）
- 雁坂嶺（annualItems）：山梨交通 西沢渓谷線の西沢渓谷入口まで行く便 2026-04-25〜11-23
    山梨交通「西沢渓谷入口通過時刻表」（運転日：R8.4/25〜11/23の土曜・休日と4/30、5/1、7/21〜8/31、10/1〜11/13のみ）
- 木曽駒ヶ岳（senjojiki）：バス・ロープウェイは通年（夏ダイヤ・冬ダイヤ）。季節運行ではない（mode: year）。データは変えない。
  build_access_tier.py・transit_months.py が mode: year を季節運行と数えないように直した
- 飯豊山（annualItems）：山都駅〜川入の飯豊山登山アクセスバスの2026年の運行を確かめられない。喜多方市の「地域公共交通 総合パンフレット」
  （令和8年9月作成）に載っておらず、2025年以降は走っていない可能性がある。期間は入れず needsVerification を付け、注記を直した

何度流しても同じ結果。このあと build_derived.py → build_access_tier.py --write → gen_mountain_pages.py（6山）→ check_pages.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MP = os.path.join(ROOT, 'data', 'mountains.json')
AP = os.path.join(ROOT, 'data', 'accesses.json')
DAY = '2026-11-11'

ACCESS = {
    'hatomachi-toge': {
        'operation': {'validFrom': '2026-04-18', 'validTo': '2026-11-03',
                      'note': '戸倉〜鳩待峠の乗合バス・乗合タクシー（関越交通など）。道路開通日の4/17と11/4〜5の便はない'},
        'sourceUrl': 'https://www.pref.gunma.jp/uploaded/attachment/697963.pdf',
    },
    'oze-miike': {
        'operation': {'validFrom': '2026-05-01', 'validTo': '2026-10-25',
                      'note': '会津バス 檜枝岐線（会津田島駅〜尾瀬御池）。5月23日までは尾瀬御池止まり。11月1日からは檜枝岐止まり'},
        'sourceUrl': 'https://www.aizubus.com/travel/oze/',
    },
    'ichinosawa': {
        'operation': {'statusType': 'annual', 'mode': 'seasonal', 'validFrom': '2026-04-17', 'validTo': '2026-11-26',
                      'note': '林道一ノ沢線の冬期通行止めの解除（4/17）〜冬期通行止め（11/27から）。崩落の復旧工事中で、'
                              'タクシーだけが崩落箇所の手前まで入れ、登山口まで約1.5km歩く（竣工予定は2027年1月末）'},
        'sourceUrl': 'https://www.city.azumino.nagano.jp/soshiki/32/66871.html',
    },
}

KARISAKA = {
    'validFrom': '2026-04-25', 'validTo': '2026-11-23', 'seasonYear': 2026,
    'sourceUrl': 'https://ykbus.jp/wp/wp-content/themes/yamako/pdf/timetable/220001.pdf',
    'note': '西沢渓谷入口まで行く便の運転日：4/25〜11/23の土曜・休日と、4/30、5/1、7/21〜8/31、10/1〜11/13（ほかは窪平止まり）',
}
IIDE_NOTE = ('山都駅〜川入の飯豊山登山アクセスバスの2026年の運行を確かめられない（喜多方市の地域公共交通 総合パンフレット・令和8年9月作成に載っていない）。'
             '山都駅からタクシーを使う')


def main():
    A = json.load(open(AP, encoding='utf-8'))
    for k, v in ACCESS.items():
        a = A[k]
        op = a.setdefault('operation', {})
        op.update(v['operation'])
        op['seasonYear'] = 2026
        a['sourceUrl'] = v['sourceUrl']
        a['lastVerified'] = DAY
        a.pop('needsVerification', None)
    json.dump(A, open(AP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    M = json.load(open(MP, encoding='utf-8'))
    by = {m['id']: m for m in M}
    hit = 0
    for it in by['karisaka'].get('annualItems') or []:
        if it.get('kind') == 'transport':
            it.update(KARISAKA)
            it['lastVerified'] = DAY
            hit += 1
    assert hit == 1, hit
    hit = 0
    for it in by['iide'].get('annualItems') or []:
        if it.get('kind') == 'transport':
            it['needsVerification'] = True
            it['note'] = IIDE_NOTE
            it['lastVerified'] = DAY
            hit += 1
    assert hit == 1, hit
    by['iide']['trainRoutes']['note'] = '山都駅〜川入のアクセスバスは2026年の運行を確かめられない。山都駅からタクシーを使う'
    json.dump(M, open(MP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('運行期間を入れた：至仏山・燧ヶ岳・常念岳（accesses.json）、雁坂嶺（annualItems）。飯豊山は要確認のまま')


if __name__ == '__main__':
    main()
