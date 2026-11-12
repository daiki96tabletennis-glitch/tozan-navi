"""代表的な登山ルートで、アクセス欄の電車・バスの行き先から歩き始めるコースに印（routes[].byTrain）を付ける（2026-11-09。運営者の指示）

山ページの「代表的な登山ルート」で、byTrain のコースのコース名の前に電車のアイコンを出す（gen_mountain_pages.py の render_routes）。
決め方：コースの登山口（trailheadName）か最初の通過点が、電車・バスの経路（trainRoutes。新宿・大宮・横浜発のどれか）の
2番目以降の停車地（乗り換え駅・バス停・行き先）と同じ場所か。名前の「駅・バス停・登山口・入口」などは外し、かっこの中も見る。
機械の照合を見直して、別の場所なのに名前が似ているコースは EXCLUDE、同じ場所なのに名前が違うコースは INCLUDE に書いた
（例：美濃戸は美濃戸口のバス停から歩いて1時間ほど先、すずらん峠は竜源橋のバス停とは別の登山口）。
ロープウェイ・ゴンドラの山頂駅から歩くコースは、アクセス欄の行き先がその乗り場なら印を付ける。
何度流しても同じ結果。コースや電車・バスの経路を直したら流し直し、gen_mountain_pages.py --all。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (山ID, コースの番号0から): 名前は似ているが別の場所
EXCLUDE = {
    ('yatsugatake', 0), ('yatsugatake', 2),        # 美濃戸（赤岳山荘）≠ 美濃戸口のバス停
    ('keirisan', 0), ('keirisan', 1), ('keirisan', 2),  # 七合目・すずらん峠 ≠ 竜源橋のバス停
    ('bandai', 2),                                   # 猪苗代登山口（スキー場）≠ 猪苗代駅
    ('kenashiyama', 1), ('kenashiyama', 2),          # 麓登山口 ≠ 朝霧高原のバス停
    ('tomisan', 2),                                  # 岩井側の駐車場 ≠ 福満寺のバス停
    ('ohnoyama', 2),                                 # つぶらの公園 ≠ 大野山入口のバス停
}
# 同じ場所なのに名前が違う
INCLUDE = {
    ('utsugi', 0),                                   # 駒ヶ根高原スキー場駐車場（菅の台バスセンターから約1.1km・歩いて15分ほど。2026-11-09 に見直し）
    ('nakawarayama', 1),                             # 造林小屋跡のコースの歩き始め（秩父湖のバス停から約1km。二瀬ダムを渡る）
    ('tonosaki', 0),                                 # 大倉尾根（大倉のバス停から。このコースは登山口・通過点のデータが無い）
    ('kazahariyama', 1),                             # 白岩（バス停）
    ('goryudake', 0), ('goryudake', 1),              # エスカルプラザからテレキャビンでアルプス平
    ('karamatsu', 0), ('karamatsu', 1), ('karamatsu', 2),  # 八方バスターミナルからゴンドラ・リフトで八方池山荘
    ('nokogiriyama', 0),                             # 戸台パーク（戸台のゲート）
    ('futagoyama_okumusa', 0), ('futagoyama_okumusa', 1),  # 芦ヶ久保駅・道の駅あしがくぼ（駅の隣）
    ('ishiwariyama', 0), ('ishiwariyama', 1),        # 山中湖平野のバス停の近くのハイキングコース入口
    ('kitayokodake', 0), ('kitayokodake', 1), ('kitayokodake', 2),  # 北八ヶ岳ロープウェイ山頂駅
    ('jinba', 2),                                    # 藤野駅（JR中央線の駅）から歩く。アクセス欄の本線は2026-11-11に高尾駅からのバスにした
}

ALIAS={'みずがき山荘':'瑞牆山荘','一ノ瀬スキー場':'一の瀬','一ノ瀬':'一の瀬','有明荘':'中房温泉','風戸':'風戸','北八ケ岳ロープウェイ山頂':'山頂','八ケ岳ロープウェイ山頂':'山頂'}
def parts(s):
    s=(s or '').strip()
    out=[]
    inner=re.findall(r'[（(]([^）)]*)[）)]',s)
    base=re.sub(r'[（(][^）)]*[）)]','',s)
    for x in [base]+inner:
        for y in re.split(r'[・、/／]',x):
            y=re.sub(r'^(JR|ＪＲ)','',y.strip())
            prev=None
            while prev!=y:
                prev=y
                y=re.sub(r'(バスターミナル|バスセンター|バス停|バスのりば|停留所|駅前|駅|登山道入口|登山口|登り口|入口|前|から.*|季節|夏季|4〜11月季節運行)$','',y)
            y=ALIAS.get(y,y)
            y=y.replace('ヶ','ケ').replace('ヵ','ケ').replace(' ','').replace('　','')
            if len(y)>=2: out.append(y)
    return out
def stops(m):
    tr=m.get('trainRoutes') or {}
    S=set()
    for dep,v in (tr.get('routes') or {}).items():
        legs=v.get('legs') or []
        for l in legs[1:]:
            if l.get('station'): S.add(l['station'])
    return S
def first_wp(r):
    w=r.get('waypoints')
    if isinstance(w,str): return w.split('→')[0].strip()
    if isinstance(w,list) and w: return w[0] if isinstance(w[0],str) else (w[0].get('name') if isinstance(w[0],dict) else '')
    return ''
def match(m,r):
    S=stops(m)
    P=[p for s in S for p in parts(s)]
    for cand in [r.get('trailheadName'), first_wp(r)]:
        for c in parts(cand):
            for p in P:
                if c==p or (len(min(c,p,key=len))>=3 and (c in p or p in c)):
                    return (cand,p)
    return None


def main():
    path = os.path.join(ROOT, 'data', 'mountains.json')
    M = json.load(open(path, encoding='utf-8'))
    n = 0
    for m in M:
        for i, r in enumerate(m.get('routes') or []):
            on = bool(m.get('trainRoutes')) and (((m['id'], i) in INCLUDE) or (match(m, r) is not None and (m['id'], i) not in EXCLUDE))
            if on:
                r['byTrain'] = True
                n += 1
            else:
                r.pop('byTrain', None)
    json.dump(M, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('電車・バスで行けるコース：%d' % n)


if __name__ == '__main__':
    main()
