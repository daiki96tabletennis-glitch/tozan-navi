#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-26〜31 に足した13山の装備カード（data/gear-data.json）を作る（2026-11-02。運営者「最近追加した山は装備欄が空欄」）。

- アイゼン・冬靴・ピッケルは、その山の gearCalendar から決める（月の途中で変わる月は前の区分＋来月分の準備）
- 防寒・保温ボトル・ポール・熊鈴を出す月は、装備カレンダーを借りた近くの山（REF）と同じにする
- 熊鈴は REF が同じ登山道・山域の山だけ（仙ノ倉山＝平標山）。それ以外は出典が無いので付けない
- 数字は代表コースの値（距離は0.1km、標高差は50m単位）。ポールは登りが500m未満なら出さない
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GP = os.path.join(ROOT, 'data', 'gear-data.json')
MP = os.path.join(ROOT, 'data', 'mountains.json')

# 山ID: (参照の山, 雪の無い時期の靴, 冬にピッケル)
NEW = {
    'tsubakurodake': ('otenshoudake', 'mid', False),
    'tengudake': ('keirisan', 'mid', False),
    'kitayokodake': ('keirisan', 'low', False),
    'nyukasayama': ('kirigamine', 'low', False),
    'nishihotaka': ('kasagatake', 'rock', True),
    'myogisan': ('arafune', 'rock', False),
    'sennokurayama': ('tairappyo', 'mid', False),
    'houkyozan': ('tsukuba', 'low', False),
    'ryugatake': ('ishiwariyama', 'dist', False),
    'narukamiyama': ('hiwadayama', 'low', False),
    'bukkasan': ('ohnoyama', 'low', False),
    'dodairasan': ('jinba', 'dist', False),
    'takamatsuyama': ('jinba', 'dist', False),
}
BELL_OK = {'sennokurayama'}

RANK = {'no_crampons': 0, 'light_crampons': 1, 'winter_gear': 2}


def cls(x, part='before'):
    return x if isinstance(x, str) else x[part]


def rep_route(m):
    rs = m.get('routes') or []
    rid = m.get('representativeRouteId')
    for r in rs:
        if r.get('id') == rid:
            return r
    return rs[0]


def num(s):
    x = re.search(r'[\d.]+', str(s or '').replace(',', ''))
    return float(x.group(0)) if x else None


def shoe(kind, m, km, gain):
    hi = '（標高2500m以上、高山特有の気象変化に注意）' if m['elevation'] >= 2500 else ''
    if kind == 'low':
        return {'c': 'shoe', 'i': '必須', 'p': 'キャラバン C1-02S', 'r': '整備された歩きやすい道が中心。ローカットの軽量シューズでも対応できます。' + hi}
    if kind == 'dist':
        return {'c': 'shoe', 'i': '必須', 'p': 'キャラバン C1-02S', 'r': '距離%.1fkm・標高差%dmのコース。防水性のあるミドルカット以上のシューズがおすすめです。' % (km, gain) + hi}
    if kind == 'mid':
        return {'c': 'shoe', 'i': '必須', 'p': 'メレル MOAB 3 ミッド GTX', 'r': '長時間・標高差%dmを伴うコース。足首をしっかり固定できるミドルカットの登山靴が安心です。' % gain + hi}
    if kind == 'rock':
        return {'c': 'shoe', 'i': '必須', 'p': 'スポルティバ トランゴ テック GTX', 'r': '岩場・ガレ場を含む本格的なコースです。ソールのグリップ力と足首保護を重視した登山靴を選びましょう。' + hi}
    raise ValueError(kind)


W_SHOE = {'c': 'shoe', 'i': '必須', 'p': 'スカルパ マンタテックGTX', 'r': '本格的な積雪期です。アイゼン対応の冬季ブーツに切り替えましょう。'}
W_SHOE2 = {'c': 'shoe', 'i': '必須', 'p': 'スポルティバ ネパールエボGTX', 'r': '本格的な積雪期です。厳冬期対応のマウンテンブーツと、12本爪アイゼン・ピッケル等の冬山装備が必要です。'}
LIGHT = {'c': 'crampon', 'i': '推奨', 'p': 'エバニュー 6本爪アイゼン', 'r': '凍結・残雪が見られる時期です。チェーンスパイクや6本爪アイゼンなどの軽アイゼン等があると滑りにくく安心です。事前に最新の積雪・凍結情報を確認してください。'}
WINTER = {'c': 'crampon', 'i': '推奨', 'p': 'グリベル G12 ニュークラシック', 'r': '本格的な積雪期です。12本爪アイゼン・ピッケル等の冬山装備と、雪山の経験が必要です。事前に最新の積雪・凍結情報を確認してください。'}
LIGHT_NEXT = {'c': 'crampon_next', 'i': '推奨', 'p': 'エバニュー 6本爪アイゼン(来月分)', 'r': '来月から凍結・残雪の時期に入ります。軽アイゼンの準備がおすすめです。'}
WINTER_NEXT = {'c': 'crampon_next', 'i': '推奨', 'p': 'グリベル G12 ニュークラシック(来月分)', 'r': '来月から本格的な積雪期に入ります。12本爪アイゼン・ピッケル等の冬山装備の準備を進めましょう。'}
AXE = {'c': 'axe', 'i': '推奨', 'p': 'ブラックダイヤモンド レイブンウィズグリップ', 'r': '急な雪面・凍結した斜面ではピッケルによる滑落停止技術が必要です。冬季登山に不慣れな場合は経験者との同行をおすすめします。事前に最新の積雪・凍結情報を確認してください。'}
BELL = {'c': 'bell', 'i': '条件次第', 'p': '消音機能付き熊よけ鈴', 'r': 'この山域はツキノワグマの目撃情報があります。鈴があると心強いです。'}
BOTTLE = {'c': 'bottle', 'i': 'あると便利', 'p': 'サーモス 山専ボトル', 'r': '長時間行動や標高の高さで、温かい飲み物が恋しくなる場面があります。'}
DOWN_R = '休憩時や行動中の防寒に。標高が高いほど朝晩の冷え込みが早まります。'


def build(mid, m, ref_cards):
    ref, kind, axe = NEW[mid]
    r = rep_route(m)
    km = num(r.get('distance')) or 0
    gain = int(round((num(r.get('elevation')) or 0) / 50.0) * 50)
    cal = m['gearCalendar']
    out = {}
    for mo in range(1, 13):
        cur = cls(cal[mo - 1])
        nxt = cal[mo - 1]['after'] if not isinstance(cal[mo - 1], str) else cls(cal[mo % 12])
        refm = ref_cards[str(mo)]
        cards = []
        if cur == 'winter_gear':
            cards.append(dict(W_SHOE2 if axe else W_SHOE))
        else:
            cards.append(shoe(kind, m, km, gain))
        cards.append({'c': 'rain', 'i': '必須', 'p': 'ミレー ティフォン50000', 'r': '山の天気は平地より変わりやすく、標高%dmでも急な雨はあります。コンパクトなレインウェアは常備しておきたいところです。' % m['elevation']})
        if cur == 'light_crampons':
            cards.append(dict(LIGHT))
        elif cur == 'winter_gear':
            cards.append(dict(WINTER))
        if RANK.get(nxt, 0) > RANK.get(cur, 0):
            cards.append(dict(WINTER_NEXT if nxt == 'winter_gear' else LIGHT_NEXT))
        if cur == 'winter_gear' and axe:
            cards.append(dict(AXE))
        for c in refm:
            if c['c'] == 'down':
                cards.append({'c': 'down', 'i': c['i'], 'p': c['p'], 'r': DOWN_R})
        if mid in BELL_OK and any(c['c'] == 'bell' for c in refm):
            cards.append(dict(BELL))
        pole = [c for c in refm if c['c'] == 'pole']
        if pole and gain >= 500:
            if '累積' in pole[0]['r']:
                t = '累積標高差+%dmと大きめ。ポールがあるとひざへの負担がかなり変わります。' % gain
            else:
                t = '標高差%dm。ポールがあるとひざへの負担がかなり変わります。' % gain
            cards.append({'c': 'pole', 'i': 'あると便利', 'p': pole[0]['p'], 'r': t})
        if any(c['c'] == 'bottle' for c in refm):
            cards.append(dict(BOTTLE))
        out[str(mo)] = cards
    return out


def main():
    write = '--write' in sys.argv
    GD = json.load(open(GP, encoding='utf-8'))
    MS = {m['id']: m for m in json.load(open(MP, encoding='utf-8'))}
    for mid in NEW:
        if mid in GD and not write:
            print('既にある:', mid)
        GD[mid] = build(mid, MS[mid], GD[NEW[mid][0]])
        print(mid, MS[mid]['name'])
        for mo in range(1, 13):
            print('  %2d' % mo, ' '.join('%s(%s)' % (c['c'], c['i']) for c in GD[mid][str(mo)]))
        print('  例:', GD[mid]['7'][0]['r'])
    if write:
        with open(GP, 'w', encoding='utf-8') as f:
            json.dump(GD, f, ensure_ascii=False, indent=2)
        print('書き込みました')


if __name__ == '__main__':
    main()
