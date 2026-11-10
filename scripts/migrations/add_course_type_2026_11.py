"""コースの種類（往復・周回・縦走）を routes[].courseType に持たせる（2026-11-10。運営者の指示「データとして持っておきたい」）

種類は、歩き始めと歩き終わりの場所で決める：
- out_and_back（往復）：同じ登山口へ、同じ道で戻る（山頂付近だけ別の道を通るもの・富士山の下山道も含む）
- loop（周回）：同じ登山口・駐車場・バス停へ、別の道で戻る
- traverse（縦走）：別の登山口・バス停・駅で終わる（近くても別の場所なら縦走。帰り方 returnAccess はこの種類だけ）

決め方：コース名の「往復」「周回」「縦走」。名前に無いコースは NAME_LESS に書く。
2026-11-10 に、YAMAP のモデルコースの線（歩き始めと終わりの距離・帰りに同じ道を通る割合）と全コースを照らし、
食い違った10コースは YAMAP の通過点で確かめた（どれもコース名のとおり。YAMAP の往復は線が片道だけのことがある）。
何度流しても同じ結果。コースを足す・名前を変えたらこれを流す（check_pages.py セクション22が見張る）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')

WORDS = (('往復', 'out_and_back'), ('ピストン', 'out_and_back'), ('周回', 'loop'), ('縦走', 'traverse'))
# コース名に種類の無いコース（山ID, コース名）→ 種類
NAME_LESS = {
    ('kintoki', '公時神社〜金時山〜矢倉沢峠'): 'traverse',  # 金時神社入口バス停 → 金時登山口バス停（環境省のコース06）
    ('kamakura_alps', '天園ハイキングコース（北鎌倉〜天園〜鎌倉）'): 'traverse',  # 北鎌倉駅 → 鎌倉（天園コース入口）
}


def course_type(mid, name):
    if (mid, name) in NAME_LESS:
        return NAME_LESS[(mid, name)]
    # 「天城縦走登山口〜…（周回）」のように地名に「縦走」を含む名前があるので、かっこの中・名前の末尾の語を優先する
    for w, t in WORDS:
        if ('（' + w) in name or ('・' + w) in name or name.endswith(w) or (w + '）') in name:
            return t
    hits = sorted((name.find(w), t) for w, t in WORDS if w in name)
    if hits:
        return hits[0][1]
    raise SystemExit('種類が決められないコース：%s %s（NAME_LESS に書く）' % (mid, name))


def main():
    M = json.load(open(PATH, encoding='utf-8'))
    n = changed = 0
    count = {}
    for m in M:
        for r in m.get('routes') or []:
            t = course_type(m['id'], r['name'])
            n += 1
            count[t] = count.get(t, 0) + 1
            if r.get('courseType') != t:
                r['courseType'] = t
                changed += 1
            if r.get('returnAccess') and t != 'traverse':
                raise SystemExit('帰り方があるのに縦走でないコース：%s %s' % (m['id'], r['name']))
    json.dump(M, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('コース %d（書き換え %d）：往復 %d・周回 %d・縦走 %d' % (n, changed, count.get('out_and_back', 0), count.get('loop', 0), count.get('traverse', 0)))


if __name__ == '__main__':
    main()
