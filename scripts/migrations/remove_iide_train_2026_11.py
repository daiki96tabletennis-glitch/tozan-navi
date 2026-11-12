"""飯豊山を「電車で行けない山（車だけ）」にする（2026-11-11。運営者の指示「電車アクセス外して。裏データには残して表には全て電車バス関連のデータ消して」）

山都駅〜川入の飯豊山登山アクセスバスの2026年の運行を確かめられなかった（喜多方市の地域公共交通 総合パンフレット・令和8年9月作成に載っていない。
2025年以降は走っていない可能性）。電車・バスの項目は、ページに出ない `archivedTrainAccess`（理由・日付・前の値）に移し、
表に出る項目は車だけの山（武尊山など）と同じ形（null・空の一覧）にする。よくある質問のアクセスの答えは車だけにし、
関連するまとめの「電車で行ける日帰り登山一覧」のリンクも外す。

運行が確かめられたら、archivedTrainAccess.fields の値を戻し、期間（annualItems）を入れて build_access_tier.py などを流す。
何度流しても同じ結果。このあと mark_train_routes_2026_11.py → build_access_tier.py --write → build_meta.py --write
→ gen_mountain_pages.py --id iide → check_pages.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
DAY = '2026-11-11'
NULL_KEYS = ['trainAccess', 'trainAccessOmiya', 'trainAccessYokohama', 'trainAccessHtml', 'trainRoutes',
             'trainTimeShinjuku', 'trainTimeOmiya', 'trainTimeYokohama', 'fareShinjuku', 'fareOmiya', 'fareYokohama',
             'transfersShinjuku', 'transfersOmiya', 'transfersYokohama', 'fareCheckedAt']
LIST_KEYS = ['busLinks', 'busScheduleLinks']
ACCESS_Q = '飯豊山へのアクセス方法'
ACCESS_A = ('登山口の川入（御沢）へは車で行くのが基本です。新宿から車で約4時間35分が目安で、'
            '川入キャンプ場駐車場（約100台・無料）に停めて歩き始めます。')
TRAIN_LINK = re.compile(r'\s*<a href="/search/train-daytrip/" class="related-link-item">.*?</a>', re.S)


def main():
    M = json.load(open(PATH, encoding='utf-8'))
    m = [x for x in M if x['id'] == 'iide'][0]
    if 'archivedTrainAccess' not in m:
        fields = {k: m.get(k) for k in NULL_KEYS + LIST_KEYS}
        fields['annualItemsTransport'] = [a for a in m.get('annualItems') or [] if a.get('kind') == 'transport']
        fields['faqAccessAnswer'] = next((f['answer'] for f in m.get('faq') or [] if f['question'].startswith(ACCESS_Q)), None)
        fields['verifyNotes'] = m.get('verifyNotes')
        m['archivedTrainAccess'] = {
            'archivedAt': DAY,
            'reason': '山都駅〜川入の飯豊山登山アクセスバスの2026年の運行を確かめられない（喜多方市の地域公共交通 総合パンフレット・令和8年9月作成に載っていない）。運営者の指示で電車アクセスを外した',
            'sourceUrl': 'https://www.city.kitakata.fukushima.jp/uploaded/attachment/58161.pdf',
            'fields': fields,
        }
    for k in NULL_KEYS:
        m[k] = None
    for k in LIST_KEYS:
        m[k] = []
    m.pop('accessTier', None)
    m['annualItems'] = [a for a in m.get('annualItems') or [] if a.get('kind') != 'transport']
    m.pop('verifyNotes', None)
    hit = 0
    for f in m.get('faq') or []:
        if f['question'].startswith(ACCESS_Q):
            f['question'] = '飯豊山へのアクセス方法は？'
            f['answer'] = ACCESS_A
            hit += 1
    assert hit == 1, hit
    m['relatedLinksHtml'] = TRAIN_LINK.sub('', m.get('relatedLinksHtml') or '')
    assert 'train-daytrip' not in m['relatedLinksHtml']
    for r in m.get('routes') or []:
        r.pop('byTrain', None)
    m['mountainUpdated'] = DAY
    json.dump(M, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('飯豊山：電車・バスの項目を archivedTrainAccess に移しました')


if __name__ == '__main__':
    main()
