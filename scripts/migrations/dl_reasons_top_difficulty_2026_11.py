# -*- coding: utf-8 -*-
"""山ページの「難易度」の欄の定型文（dlNoteHtml「◯◯は中級レベル（コース定数…）」）を、山ごとの理由の箇条書き（dlReasonsHtml）にする
（2026-11-25。運営者の指示「難易度の項目も定型文になっているものは直して」→「一旦、難易度検索が過去28日間で150以上ある山だけで良い」）

対象：Search Console（2026-10-26〜11-22）で「◯◯ 難易度」「◯◯ レベル」「◯◯ 初心者」の検索の表示が150回以上で、理由の欄が無かった6山。
書いたことは、同じ日によくある質問の答え（faq_difficulty_individual_2026_11.py）を書くときに出典で確かめた内容と、コースのデータ（県のグレーディング・鎖場）だけ。
li＝登りやすくする点、li.minus＝難しくする点。前の定型文は dlNoteHtmlOld に残す。鎖場のある山（八ヶ岳・皇海山）は鎖場の行を入れる（gen_mountain_pages.py の with_chain）。
何度流しても同じ結果。このあと gen_mountain_pages.py --id <山> → check_pages.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
DAY = '2026-11-25'

R = {
    'oyama': {
        'plus': ['ケーブルカーで阿夫利神社下社まで上がれ、下社から山頂までは往復約3時間25分（標高差約600m）',
                 '山頂まで自信がなければ、下社までにして景色を楽しむこともできる'],
        'minus': ['下社の上の登山口から急な階段が始まり、古い石積みの道を山頂まで登り続ける（山と溪谷オンライン）',
                  '下社から大山寺へ下る石段は急。下りにケーブルカーを使うと膝の負担を減らせる'],
        'src': ['https://www.yamakei-online.com/yama-ya/detail.php?id=2873&pg=4',
                'https://www.veltra.com/jp/yokka/article/the-charm-of-climbing-oyama/',
                'https://san-tatsu.jp/articles/268733/'],
    },
    'kogashiyama': {
        'plus': ['森林公園から北コース・南コースを回る一般の登山道なら、周回で約3時間'],
        'minus': ['中尾根・東稜などのバリエーションルートには鎖場やロープがあり、岩場に慣れていない初心者だけで入らない（山と溪谷オンライン）',
                  '2023年1月以降、転倒や滑落の事故が多い（宇都宮市）。岩場があるので登山靴とヘルメットがすすめられている',
                  '南（階段）コースは2026年1月から岩下道分岐付近が迂回ルート（旧ルートは立入禁止）。迂回路は滑りやすく、とくに下りに注意'],
        'src': ['https://www.yamakei-online.com/yama-ya/detail.php?id=956',
                'https://www.city.utsunomiya.lg.jp/citypromotion/kanko/pamphlet/1007258.html',
                'https://www.utsunomiya-cvb.org/blog/detail_151.html'],
    },
    'hinata': {
        'plus': ['山梨県の山のグレーディングでは、矢立石からの道は体力度2・技術的難易度A。往復約3時間14分',
                 'ブナの林を抜けた山頂の雁ヶ原は、白い砂が広がる開けた場所'],
        'minus': ['登り始めはぐっと高さを上げる',
                  '下山で道を間違えやすい所がある（山梨県）',
                  '矢立石までの林道は例年12月初め〜4月下旬は閉鎖され、その間は尾白川渓谷駐車場から矢立石まで片道約1時間多く歩く'],
        'src': ['https://www.pref.yamanashi.jp/documents/103416/28_hinatayama.pdf',
                'https://www.bepal.net/archives/332546',
                'https://www.yamanashi-kankou.jp/kankou/spot/p2_2225.html'],
    },
    'yatsugatake': {
        'plus': ['行者小屋・赤岳鉱泉に山小屋があり、泊まれば余裕を持って登れる。どちらの小屋でもヘルメットを借りられる'],
        'minus': ['地蔵尾根・文三郎尾根は森林限界を越えると、はしご・階段・鎖場が続く。雨の日は滑落に注意（信州 山のグレーディングで技術的難易度C）',
                  '山頂の近くは岩場。行者小屋から上ではヘルメットをかぶるのが安心',
                  'コースは8〜11時間と長い'],
        'src': ['https://yamahack.com/2410',
                'https://yamap.com/magazine/75686',
                'https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/gure-dexingu.html'],
    },
    'sukai': {
        'plus': [],
        'minus': ['群馬県側の皇海橋からの短いコースは林道の通行止めで使えず、栃木県日光市足尾の銀山平から庚申山・鋸山を越えて登る',
                  '往復約13時間49分・標高差2,000m以上と長く、1泊2日の計画が基本',
                  '庚申山から鋸山にかけて、はしごと鎖場が続く（群馬県のグレーディングで技術的難易度D）'],
        'src': ['https://www.pref.gunma.jp/01/g3500213.html',
                'https://www.yamakei-online.com/yama-ya/detail.php?id=5316'],
    },
    'hiwadayama': {
        'plus': ['日和田山登山口から山頂までの往復は約1時間16分と短い',
                 '男坂のほかに女坂がある。男坂は登りに使う人が多いので、下りは女坂がおすすめ'],
        'minus': ['男坂は樹林の中に岩が出てくる道。容易なルートを選んでも、岩場では必ず両手を使う（山と溪谷オンライン）',
                  '岩登りの練習に使われる男岩・女岩は、上から道具や人が落ちてくることがあり危ないので近づかない'],
        'src': ['https://www.yamakei-online.com/yama-ya/detail.php?id=2873&pg=3',
                'https://www.yamakei-online.com/yama-ya/detail.php?id=2214&pg=4'],
    },
}


def html(d):
    lis = ''.join('\n    <li>%s</li>' % t for t in d['plus']) + ''.join('\n    <li class="minus">%s</li>' % t for t in d['minus'])
    return '<ul class="dl-reasons">%s\n  </ul>' % lis


def main():
    raw = open(P, encoding='utf-8').read()
    M = json.loads(raw)
    by = {m['id']: m for m in M}
    n = 0
    for mid, d in R.items():
        m = by[mid]
        h = html(d)
        if any(r.get('chains') for r in m.get('routes') or []):
            assert '鎖' in h, mid
        if m.get('dlReasonsHtml') != h or m.get('dlReasonsSources') != d['src']:
            if m.get('dlNoteHtml'):
                m['dlNoteHtmlOld'] = m['dlNoteHtml']
            m['dlNoteHtml'] = None
            m['dlReasonsHtml'] = h
            m['dlReasonsSources'] = d['src']
            m['dlReasonsCheckedAt'] = DAY
            m['mountainUpdated'] = max(m.get('mountainUpdated') or '', DAY)
            n += 1
    open(P, 'w', encoding='utf-8').write(json.dumps(M, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
    print('変えた山', n, '／対象', len(R))


if __name__ == '__main__':
    main()
