#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""木曽駒ヶ岳（千畳敷へのアクセス）：運賃を事業者の運賃表で引き直す（2026-10-08）。
旧額 8,400／8,930／9,020円は、高速バスの最安額（4,200円）にバス・ロープウェイの「往復」セット額（4,200円）を足したもので、片道の合計になっていなかった。
出典：
- 中央アルプス駒ヶ岳ロープウェイ「2026年度 運賃カレンダー」
  https://www.chuo-alps.com/wp-content/uploads/2026/01/【基本】R8年度運賃カレンダー.pdf
  路線バス 駒ヶ根駅前〜しらび平 片道1,050円。ロープウェイ片道 A1,640／B1,510／C1,370／D1,300／E1,230円（日によって区分が変わる）
- 京王バス 新宿〜伊那飯田線 運賃表（2025年9月1日現在）駒ヶ根 月〜木4,600円／金・祝前日・土日祝4,800円／繁忙日5,000円
- 表示は「月〜木の高速バス＋C運賃」の片道合計：4,600＋1,050＋1,370＝7,020円。大宮＋528円、横浜＋616円（JR・IC）
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'accesses.json')
AC = json.load(open(P, encoding='utf-8'))
a = AC['senjojiki']
assert a['fares'] == {'shinjuku': 8400, 'omiya': 8930, 'yokohama': 9020}
a['fares'] = {'shinjuku': 7020, 'omiya': 7548, 'yokohama': 7636}
tr = a['trainRoutes']
tr['note'] = (tr['note'].rstrip('。') + '。'
              '運賃は日によって変わる。'
              'ロープウェイの片道は1,230〜1,640円（2026年度はA〜Eの5区分で、夏の土日やお盆・紅葉期が高い）。'
              '路線バス（駒ヶ根駅前〜しらび平）は片道1,050円。'
              '高速バス（新宿〜駒ヶ根）の窓口運賃は月〜木4,600円、金・祝前日・土日祝4,800円、繁忙日5,000円')
tr['summaryNote'] = ('※表示の運賃は片道で、月〜木の高速バスとロープウェイC運賃（1,370円）の場合。土日や繁忙期は数百円高くなる。'
                     '菅の台バスセンター以降は路線バス（マイカー規制のため）＋ロープウェイの乗り継ぎが必須')
a['sourceUrl'] = 'https://www.chuo-alps.com/fare/'
a['lastVerified'] = '2026-10-08'
json.dump(AC, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(a['fares'])
