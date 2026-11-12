"""トップの「アクセス難易度」（電車・バスで行くときの、良好／ふつう／要計画）を山ごと・出発地ごとに作る（2026-11-11。運営者の指示）

前はトップのページ（index.html の getAccessTier）がその場で決めていたが、
- 乗り換え回数を古い項目 transfersShinjuku など（約90山で経路と食い違い、空の山は0回扱い）から読んでいた
- 注意のバナー（warnBanner）があるだけで「要計画」にしていた（車の規制・閉鎖・クマなど、電車・バスの行きやすさと関係のないものも含む）
- 季節運行かどうかを trainAccess の矢印の文から探していて、ほぼ見つからなかった
ので、電車・バスの経路（trainRoutes）と、運行期間・注記のデータから決め、mountains.json の accessTier に入れる。
トップはそれを読むだけ。経路・注記・運行期間（annualItems・accesses.json）を変えたら流す（check_pages.py セクション25 が食い違いを見張る）。

決まり（出発地ごと）
- 要計画：次のどれか
  - 合計の時間が4時間（240分）を超える
  - 乗り換えが3回以上（経路の乗り物の数−1。歩く区間は数えない）
  - 予約しないと乗れない乗り物がある（注記・路線名に「予約制」「要予約」「完全予約」「予約優先」「予約が要る」「予約しておく」。
    「〜もある」と書いた別の行き方の文は見ない。「予約がおすすめ」だけの特急は入れない）
  - バスが無くタクシーを使う区間がある（経路のタクシーの区間、「バスは無く」）
  - バスの本数が1日3本（便・往復）以下（「バス」「便」のある文の「1日◯本」）
  - 季節運行の乗り物を使い、合計が3時間（180分）を超える（奥の登山口へ季節のバスで行く山。運行日・時刻を調べて組む必要がある）
- 良好：上のどれでもなく、合計2時間30分（150分）以内・乗り換え1回まで・季節運行の乗り物を使わない
- ふつう：それ以外（季節運行の乗り物を使う・2時間30分を超える・乗り換え2回・バスの走る曜日が限られる＝「平日のみ」「土日祝のみ」「全便運休」など）
- 季節運行：annualItems の kind=transport（「ダイヤ」の切り替えだけの項目は除く）、新しい形の山は代表コースのアクセスの
  operation.statusType が annual / temporary（mode が year＝通年は除く）、または経路の札（badge）の文に「季節」「夏季限定」「◯月は運休」
  （前は札の「運休」だけで季節運行にしていて、通年運行の木曽駒ヶ岳（「点検運休あり」）を季節運行と数えていた。2026-11-11 に直した）
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MPATH = os.path.join(ROOT, 'data', 'mountains.json')
APATH = os.path.join(ROOT, 'data', 'accesses.json')
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
LABEL = {'easy': '良好', 'normal': 'ふつう', 'plan': '要計画'}

RESERVE = re.compile(r'予約制|要予約|完全予約|予約優先|予約が要る|予約しておく')
FEW = re.compile(r'1日(\d+)(本|便|往復)')
LIMITED = re.compile(r'全便運休|平日の朝だけ|平日のみ|平日だけ|土日祝のみ|土日祝だけ|土休日のみ|所定日だけ')


def sentences(text):
    return [s for s in re.split(r'[。※\n]', text or '') if s.strip()]


def legs_of(m, dep):
    tr = m.get('trainRoutes') or {}
    R = tr.get('routes') if isinstance(tr.get('routes'), dict) else {}
    return (R.get(dep) or {}).get('legs') or []


def seasons(m, A):
    """電車・バスの経路で使う季節運行の乗り物の運行期間 [(validFrom, validTo, 名前, 要確認か)]。
    旧い形の山は annualItems の kind=transport（「ダイヤ」の切り替えだけの項目は除く）、
    新しい形の山は代表コースのアクセスの operation（mode が year＝通年のものは除く）。期間が分からないものは (None, None, …)"""
    out = []
    for a in m.get('annualItems') or []:
        if a.get('kind') == 'transport' and 'ダイヤ' not in (a.get('label') or ''):
            out.append((a.get('validFrom'), a.get('validTo'), a.get('label'), bool(a.get('needsVerification'))))
    if m.get('dataModel') == 'ssot-v1':
        rep = [r for r in m.get('routes') or [] if r.get('id') == m.get('representativeRouteId')]
        for r in rep:
            ac = A.get(r.get('accessId')) or {}
            op = ac.get('operation') or {}
            if op.get('statusType') in ('annual', 'temporary') and op.get('mode') != 'year':
                out.append((op.get('validFrom'), op.get('validTo'), ac.get('name') or r.get('accessId'), bool(ac.get('needsVerification'))))
    return out


def seasonal(m, A):
    if seasons(m, A):
        return True
    b = ((m.get('trainRoutes') or {}).get('badge') or {}).get('label') or ''
    return bool(re.search(r'季節|夏季限定|月は運休', b))


def tier_for(m, dep, cap, A):
    t = m.get('trainTime' + cap)
    if not isinstance(t, (int, float)):
        return None
    legs = legs_of(m, dep)
    tr = m.get('trainRoutes') or {}
    veh = [l for l in legs if l.get('method') and (l['method'].get('icon') or '') != 'walk']
    transfers = max(len(veh) - 1, 0)
    text = ' '.join(str(tr.get(k) or '') for k in ('note', 'summaryNote'))
    text += '。' + ((tr.get('badge') or {}).get('label') or '')
    text += '。' + '。'.join((l.get('method') or {}).get('line') or '' for l in legs)
    sents = [s for s in sentences(text) if 'もある' not in s]
    plan, normal = [], []
    if t > 240:
        plan.append('4時間を超える')
    if transfers >= 3:
        plan.append('乗り換え%d回' % transfers)
    if any(RESERVE.search(s) for s in sents):
        plan.append('予約が要る乗り物がある')
    if any((l.get('method') or {}).get('icon') == 'taxi' for l in legs) or any('バスは無く' in s for s in sents):
        plan.append('タクシーを使う区間がある')
    few = [int(x.group(1)) for s in sents if ('バス' in s or '便' in s) for x in FEW.finditer(s)]
    if few and min(few) <= 3:
        plan.append('バスが1日%d本' % min(few))
    if any(('バス' in s or '便' in s) and LIMITED.search(s) for s in sents):
        normal.append('バスの走る曜日が限られる')
    if seasonal(m, A):
        if t > 180:
            plan.append('季節運行の乗り物を使い、3時間を超える')
        else:
            normal.append('季節運行の乗り物を使う')
    if 150 < t <= 240 and not (seasonal(m, A) and t > 180):
        normal.append('2時間30分を超える')
    if transfers == 2:
        normal.append('乗り換え2回')
    if plan:
        return {'tier': 'plan', 'reasons': plan + normal}
    if normal:
        return {'tier': 'normal', 'reasons': normal}
    return {'tier': 'easy', 'reasons': []}


def compute(M, A):
    out = {}
    for m in M:
        v = {}
        for dep, cap in DEPS:
            x = tier_for(m, dep, cap, A)
            if x:
                v[dep] = x
        out[m['id']] = v or None
    return out


def main():
    write = '--write' in sys.argv
    M = json.load(open(MPATH, encoding='utf-8'))
    A = json.load(open(APATH, encoding='utf-8'))
    new = compute(M, A)
    changed = 0
    import collections
    cnt = collections.Counter()
    for m in M:
        v = new[m['id']]
        if v:
            cnt[v.get('shinjuku', {}).get('tier')] += 1
        if m.get('accessTier') != v:
            changed += 1
            if v is None:
                m.pop('accessTier', None)
            else:
                m['accessTier'] = v
    print('新宿発：' + ' / '.join('%s %d' % (LABEL.get(k, k), cnt[k]) for k in ('easy', 'normal', 'plan')))
    print('変わる山：%d' % changed)
    if write and changed:
        json.dump(M, open(MPATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('書き込みました')


if __name__ == '__main__':
    main()
