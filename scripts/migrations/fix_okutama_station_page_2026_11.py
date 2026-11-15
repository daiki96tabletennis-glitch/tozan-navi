#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""奥多摩駅から登れる山のまとめ（/search/okutama-station-hiking/。手で作ったページ）の本文を、data/mountains.json に合わせる（2026-11-15。運営者の指示）。
- 鷹ノ巣山：東日原（稲村岩尾根は崩落で通行止め）→ 峰谷のバス（約36分・1日3本）と峰谷からの縦走
- 雲取山：「日帰り可」→「宿泊推奨」（daytrip が false。鴨沢からの往復 9時間56分）
- 御嶽駅は奥多摩駅の「隣」ではない（間に4駅）。新宿→奥多摩駅は 1時間51分（前は 1時間40分・「電車1本」）
- 山の紹介の文は各山の featurePoints・routes・注記に書いてあることだけにした。出典の無い「標高831m」「犬連れ」「ロックガーデンを経由するコース」、よくある質問の出典の無い時間とホリデー快速の案内を外した
何度流しても同じ結果。前のページは .claude/backup/okutama_station_2026_11_15.html"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'search', 'okutama-station-hiking', 'index.html')
SM = os.path.join(ROOT, 'sitemap.xml')
UPDATED = '2026-11-15'

INTRO = ('JR青梅線の終点・奥多摩駅は、東京を代表する登山基地。新宿から電車で約1時間51分、駅前のバスで東京都最高峰の雲取山をはじめ、'
         '川苔山・鷹ノ巣山の登山口へ向かえます。同じ青梅線の御嶽駅まで含めれば、ケーブルカーで上がれる御岳山・大岳山も選択肢に。'
         '日帰りから山小屋泊まで、レベルに応じたコースが揃います。')
DESC = {
    'mitakesan': '山頂に武蔵御嶽神社が鎮まり、江戸時代から続く御師の宿坊が並ぶ。ケーブルカーで山上まで上がれ、沢沿いのロックガーデンでは滝を見ながら歩ける。7月下旬〜8月下旬はレンゲショウマの群生地。御岳山駅からの周回は2時間52分。青梅線の御嶽駅が起点。',
    'kawanoriyama': '落差約40mの百尋ノ滝へ、沢に沿って何度も木の橋を渡りながら登る。開けた山頂からは、晴れれば雲取山が見える。川乗橋から鳩ノ巣駅へ下る縦走は7時間25分。川乗橋へのバスは朝1時間に1本ほど。',
    'otake': '特徴のある山の形で知られ、日本二百名山・花の百名山に選ばれている。道の途中に岩場や鉄ばしごがあり、山頂からは富士山を望める。御岳山駅からの往復は4時間43分で、ケーブルカーの最終に間に合うように下山する。御嶽駅が起点。',
    'takanosuyama': '東京の山の背骨・石尾根にある山で、防火帯として切り開かれた尾根は眺めがよい。晴れた日は山頂から富士山や南アルプスまで見える。峰谷・水根からの道は登りが長く、峰谷からの縦走は8時間。東日原からの稲村岩尾根は崩落で通行止め。',
    'kumotori': '東京都最高峰で日本百名山。鴨沢からの道はよく踏まれていてゆるやかな登りが続き、七ツ石山を過ぎると富士山や南アルプスを見ながら石尾根を歩く。鴨沢からの往復は9時間56分と長く、雲取山荘に泊まるのが基本。',
}
TRAIN = {
    'otake': 'JR青梅線「御嶽駅」→ケーブル下（西東京バス約10分）→御岳山ケーブルカー約6分→御岳山駅から歩く',
    'takanosuyama': 'JR青梅線「奥多摩駅」→峰谷バス停（西東京バス約36分・1日3本）→登山口',
}
FAQ = [
    ('奥多摩駅から行ける登山スポットはどこですか？',
     '川苔山（川乗橋バス停から百尋ノ滝を通って鳩ノ巣駅へ下る縦走 7時間25分）・鷹ノ巣山（峰谷バス停からの縦走 8時間）・雲取山（鴨沢バス停からの往復 9時間56分）が代表的です。同じ青梅線の御嶽駅からは、ケーブルカーで御岳山・大岳山に行けます。'),
    ('奥多摩駅から日帰りできる山はどれですか？',
     '御岳山・大岳山・川苔山・鷹ノ巣山は日帰りできます。雲取山は鴨沢からの往復でも9時間56分かかるため、雲取山荘に1泊するのが基本です。鷹ノ巣山の峰谷行きのバスは1日3本なので、時刻を確かめてから出かけてください。'),
    ('奥多摩駅へのアクセスは？',
     'JR青梅線の終点が奥多摩駅です。新宿駅からJR中央線・青梅線で約1時間51分。奥多摩駅から各登山口へは西東京バスが出ています（川乗橋 約15分・鴨沢 約35分・峰谷 約36分）。'),
]


def sub1(pat, rep, s, flags=0):
    """1件だけ置き換える（rep は文字列そのまま、または関数）"""
    f = rep if callable(rep) else (lambda m: rep)
    s2, n = re.subn(pat, f, s, flags=flags)
    if n != 1:
        sys.exit('一致が %d 件：%s' % (n, pat[:60]))
    return s2


s = open(P, encoding='utf-8').read()
# 前置きの文（intro-tips の前まで）
s = sub1(r'(<div class="page-intro">)[^<]*', lambda m: m.group(1) + INTRO + '\n      ', s)
s = sub1(r'(?:東日原|峰谷)バス停（奥多摩駅→バス約3[06]分）( 鷹ノ巣山)', lambda m: '峰谷バス停（奥多摩駅→バス約36分）' + m.group(1), s)
# 山のカード
for mid, text in DESC.items():
    m = re.search(r'<div class="mountain-card">(?:(?!<div class="mountain-card">).)*?href="/mountains/%s/".*?class="mc-link">[^<]*</a>' % mid, s, re.S)
    if not m:
        sys.exit('カードが無い：' + mid)
    c = sub1(r'(<div class="mc-desc">)[^<]*(</div>)', lambda x: x.group(1) + text + x.group(2), m.group(0))
    if mid in TRAIN:
        c = sub1(r'(<div class="mc-train">(?:<svg.*?</svg>)?\s*)[^<]*(</div>)', lambda x: x.group(1) + TRAIN[mid] + x.group(2), c, re.S)
    if mid == 'kumotori':
        c = sub1(r'<span class="sb sb-day">[^<]*</span>', '<span class="sb sb-day">宿泊推奨</span>', c)
    s = s[:m.start()] + c + s[m.end():]
# よくある質問（画面）
items = ''.join('    <div class="faq-item"><h3 class="faq-q">%s</h3><div class="faq-a"><p>%s</p></div></div>\n' % qa for qa in FAQ)
s = sub1(r'(<h2>よくある質問</h2>\n)(?:    <div class="faq-item">.*?</p></div></div>\n)+', lambda m: m.group(1) + items, s, re.S)
# よくある質問（構造化データ）
ld = '"mainEntity":[' + ','.join('{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}' % qa for qa in FAQ) + ']'
s = sub1(r'"mainEntity":\[\{"@type":"Question".*?\}\}\]', ld, s, re.S)
s = sub1(r'("@type":"Article","headline":"[^"]*","description":")[^"]*"', lambda m: m.group(1) + '奥多摩で登れる山5選。御岳山・大岳山・川苔山・鷹ノ巣山・雲取山を難易度別に紹介。"', s)
s = sub1(r'"dateModified":"[0-9-]+"', '"dateModified":"%s"' % UPDATED, s)
y, mo, d = UPDATED.split('-')
s = sub1(r'最終更新：\d{4}年\d{1,2}月\d{1,2}日', '最終更新：%d年%d月%d日' % (int(y), int(mo), int(d)), s)
open(P, 'w', encoding='utf-8').write(s)

sm = open(SM, encoding='utf-8').read()
sm = sub1(r'(<loc>https://tozan-navi\.com/search/okutama-station-hiking/</loc><lastmod>)[0-9-]+', lambda m: m.group(1) + UPDATED, sm)
open(SM, 'w', encoding='utf-8').write(sm)
print('ok')
