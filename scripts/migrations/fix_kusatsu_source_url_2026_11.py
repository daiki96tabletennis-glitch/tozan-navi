"""草津白根山の規制の出典（草津町）のURLが変わった（2026-11-19。マイページのお知らせ「出典ページを取得できなかった」から）

旧 https://www.town.kusatsu.gunma.jp/www/contents/1779431376046/index.html は301で
新 https://www.town.kusatsu.gunma.jp/s001/110/060/1779431376046/index.html へ移る。中身は同じ（最終更新日 2026年5月22日。
湯釜火口から500mの立入規制・白根レストハウスと山頂駐車場は当面利用できない）ので、URLだけ替える。
草津温泉〜白根火山のバス（ジェイアールバス関東）も 2026-11-19 に「全便運休」のまま。何度流しても同じ結果。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD = 'https://www.town.kusatsu.gunma.jp/www/contents/1779431376046/index.html'
NEW = 'https://www.town.kusatsu.gunma.jp/s001/110/060/1779431376046/index.html'
path = os.path.join(ROOT, 'data', 'mountains.json')
raw = open(path, encoding='utf-8').read()
n = raw.count(OLD)
raw = raw.replace(OLD, NEW)
M = json.loads(raw)
m = next(x for x in M if x['id'] == 'shirane_gunma')
for a in m.get('annualItems') or []:
    if a.get('sourceUrl') == NEW:
        a['lastVerified'] = '2026-11-19'
json.dump(M, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('replaced', n)
