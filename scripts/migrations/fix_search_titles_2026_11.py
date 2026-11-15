#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CTR の低いまとめ5ページの検索の見出し・説明文を、検索語とページの中身に合わせる（2026-11-15。運営者の指示「小さい作業から」）。
根拠：Search Console 直近28日（2026-10-16〜11-12）で CTR 2〜5%（作り直した中央線・小田急線は14%）。
前の見出し・説明文には、ページに載っていない山（飯能＝伊豆ヶ岳、高尾駅＝高尾山、丹沢＝丹沢山・蛭ヶ岳）や「コース定数付き」「【2026年最新】」があった。
数字は data/mountains.json の値（代表コースの歩く時間）。何度流しても同じ結果。前のページは .claude/backup/search_titles_2026_11_15/"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAGES = {
    'okutama-station-hiking': ('奥多摩の登山・ハイキング5選｜初心者の日帰りコースから雲取山まで【奥多摩駅から】',
        '奥多摩で登れる山5選。初心者でも日帰りしやすい御岳山（歩く時間2時間52分）・大岳山から、川苔山・鷹ノ巣山、山小屋泊が基本の雲取山まで。難易度・コースタイム・電車とバスのアクセスを比べられます。'),
    'takao-hiking': ('高尾山の次に登る山4選｜高尾駅・高尾山口駅から景信山・陣馬山・小仏城山・草戸山',
        '高尾山の近くで次に登りたい山4選。高尾駅・高尾山口駅から行ける景信山（歩く時間2時間32分）・小仏城山・陣馬山・草戸山を、難易度・コースタイム・バスの乗り方で比べられます。どれも日帰りできます。'),
    'hanno-hiking': ('飯能の登山・山登り3選｜初心者向けの天覧山・日和田山と棒ノ折山',
        '飯能で登れる山3選。初心者向けの天覧山・多峯主山（歩く時間2時間56分）・日和田山（1時間16分）と、少し歩きごたえのある棒ノ折山（5時間20分）。難易度・コースタイム・電車とバスのアクセスを比べられます。'),
    'takao-jinba-hiking': ('高尾山〜陣馬山の縦走と高尾・陣馬の山5選｜難易度・コース・電車アクセス',
        '高尾山から小仏城山・景信山・陣馬山への縦走と、草戸山を含む高尾・陣馬の山5選。どれも日帰りでき、初級の高尾山（歩く時間3時間12分）から選べます。難易度・コースタイム・電車とバスのアクセスを比べられます。'),
    'tanzawa-hiking': ('丹沢の日帰り登山5選｜塔ノ岳・大山・鍋割山・三ノ塔・弘法山を難易度で比較',
        '丹沢で日帰りできる山5選。初級の弘法山（歩く時間2時間36分）から、大山・三ノ塔、中級の塔ノ岳（6時間）・鍋割山（7時間25分）まで。新宿・横浜から電車とバスで行けるコースの難易度・コースタイムを比べられます。'),
}
E = lambda s: s.replace('&', '&amp;').replace('"', '&quot;')
for slug, (title, desc) in PAGES.items():
    p = os.path.join(ROOT, 'search', slug, 'index.html')
    s = open(p, encoding='utf-8').read()
    for pat, rep in [(r'<title>[^<]*</title>', '<title>%s | Yamatch</title>' % title),
                     (r'(<meta property="og:title" content=")[^"]*(")', r'\g<1>%s | Yamatch\2' % E(title)),
                     (r'(<meta name="description" content=")[^"]*(")', r'\g<1>%s\2' % E(desc)),
                     (r'(<meta property="og:description" content=")[^"]*(")', r'\g<1>%s\2' % E(desc))]:
        s, n = re.subn(pat, lambda m, rep=rep: m.expand(rep) if '\\' in rep else rep, s)
        if n != 1:
            sys.exit('%s: %s が %d 件' % (slug, pat, n))
    open(p, 'w', encoding='utf-8').write(s)
    print('ok', slug)
