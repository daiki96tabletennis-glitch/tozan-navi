"""写真の仕上げ（明るさ・色味・彩度。運営者が選んだ「仕上げA（しっかり）」。2026-11-05〜）

- 元の写真はそのまま残し、仕上げた写真を /images/graded/<元のパス> に作る（例：/images/graded/mountains/takao/01.jpg）
- どの写真を仕上げたかは data/photo_graded.json（元のパス → 仕上げたパス）。ページはこれを見て差し替える（いまはアイゼン不要の記事だけ）
- クレジット（assets/js/card-photo-credits.js）は、仕上げた写真を元の写真の記録で引き、CC BY / CC BY-SA には「加工あり」を付ける
- 中身：白の偏り／かすみ取り／明るさの幅／S字のコントラスト／明瞭さ（強い輪郭では抑える）／鮮やかさ／空の青／明るい所を除いたあたたかみ／影を少し持ち上げる／周辺を少し暗く／細部のシャープ
- 手元で流す（numpy と Pillow が要る）。使い方：python3 scripts/grade_photos.py <元のパス>...（例：/images/mountains/takao/01.jpg）
- 出典の記録（data/image-credits.json）が無い写真は仕上げない（加工してよいライセンスか分からないため）
"""
import datetime
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'data', 'photo_graded.json')
PRESET_A = dict(wb=0.06, dehaze=0.10, stretch=1.35, curve=0.35, vib=0.30, sat=1.06, warm=0.015, clarity=0.6, vignette=0.10, lift=0.0, sky=0.10)
LUM = np.array([0.299, 0.587, 0.114], np.float32)



def grade(im, p):
    a = np.asarray(im.convert('RGB')).astype(np.float32) / 255.0
    # 1) 白の偏り（グレーワールド。上限あり）
    flat = a.reshape(-1, 3)
    l0 = flat @ LUM
    mean = flat[(l0 > 0.1) & (l0 < 0.85)].mean(0) if ((l0 > 0.1) & (l0 < 0.85)).any() else flat.mean(0)
    gain = np.clip(mean.mean() / np.maximum(mean, 1e-3), 1 - p['wb'], 1 + p['wb'])
    a = a * gain
    # 2) かすみを取る（いちばん明るい所の色を少し差し引く）
    lum = a @ LUM
    A = np.percentile(a.reshape(-1, 3), 99.5, axis=0)
    k = p['dehaze']
    a = np.clip((a - k * A) / (1 - k), 0, 1)
    # 3) 明るさの幅を広げる（白飛び・黒つぶれは避ける）
    lum = a @ LUM
    lo, hi = np.percentile(lum, 0.7), np.percentile(lum, 99.6)
    scale = min(1.0 / max(hi - lo, 1e-3), p['stretch'])
    a = np.clip((a - lo) * scale, 0, 1)
    # 4) 暗い写真は中間を持ち上げる
    m = float((a @ LUM).mean())
    if m < 0.46:
        a = a ** max(0.72, min(1.0, 0.46 / max(m, 0.2) * 0.82))
    # 5) S字のコントラスト（中間の締まり）
    c = p['curve']
    a = np.clip(a + c * (a - 0.5) * (1 - np.abs(2 * a - 1)) * 0.9, 0, 1)
    # 6) 明瞭さ（大きな形の明暗を強める。強い輪郭では効きを抑えて、白いにじみを出さない）
    lum = a @ LUM
    base = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255.0
    detail = np.clip(lum - base, -0.05, 0.05)
    a = np.clip(a + (p['clarity'] * detail)[..., None], 0, 1)
    # 7) 鮮やかさ（色の薄い所ほど強く）＋全体の彩度
    lum = (a @ LUM)[..., None]
    satv = np.abs(a - lum).max(-1, keepdims=True)
    boost = (1.0 + p['vib'] * (1.0 - np.clip(satv * 2.2, 0, 1))) * p['sat']
    a = np.clip(lum + (a - lum) * boost, 0, 1)
    # 8) 空の青を深く（明るく青っぽい所だけ、少し暗く・青く）
    lum = a @ LUM
    skym = np.clip((lum - 0.55) * 4, 0, 1) * np.clip((a[..., 2] - a[..., 0]) * 8, 0, 1)
    a = a * (1 - p['sky'] * 0.45 * skym)[..., None]
    a[..., 2] = np.clip(a[..., 2] + p['sky'] * 0.12 * skym, 0, 1)
    # 9) あたたかみ（赤を少し上げ、青を少し下げる）＋影を少しだけ持ち上げる
    lum = a @ LUM
    mid = (1 - np.clip((lum - 0.65) * 4, 0, 1))  # 明るい所（雲・雪）には色をのせない
    a[..., 0] = a[..., 0] * (1 + p['warm'] * mid)
    a[..., 2] = a[..., 2] * (1 - p['warm'] * 0.6 * mid)
    # 暗い所をつぶさない（影を少し持ち上げる）
    a = a + (p['lift'] + 0.05 * (1 - np.clip(lum * 3, 0, 1)) ** 2)[..., None] * (1 - a)
    # 10) 周辺を少し暗く（ビネット）
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.414
    a = a * (1 - p['vignette'] * np.clip(r, 0, 1) ** 2)[..., None]
    out = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    return out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=60, threshold=3))




def credited(path):
    cr = json.load(open(os.path.join(ROOT, 'data', 'image-credits.json')))
    return any(c.get('localPath') == path for v in cr.values() for c in v)


def main(paths):
    m = json.load(open(MAP)) if os.path.exists(MAP) else {'_note': '元の写真のパス → 仕上げた写真のパス（scripts/grade_photos.py が作る）', 'preset': 'A', 'photos': {}}
    for path in paths:
        if not credited(path):
            print('出典の記録が無いので飛ばす:', path)
            continue
        src = os.path.join(ROOT, path.lstrip('/'))
        out_rel = '/images/graded/' + path.lstrip('/').replace('images/', '', 1)
        dst = os.path.join(ROOT, out_rel.lstrip('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im = Image.open(src).convert('RGB')
        im.thumbnail((1600, 1600))  # 記事の枠（幅728px）の2倍あれば足りる
        if dst.lower().endswith('.webp'):
            grade(im, PRESET_A).save(dst, 'WEBP', quality=80, method=6)
        else:
            grade(im, PRESET_A).save(dst, 'JPEG', quality=86, optimize=True, progressive=True)
        m['photos'][path] = {'graded': out_rel, 'preset': 'A', 'at': datetime.date.today().isoformat()}
        print(path, '->', out_rel)
    with open(MAP, 'w') as f:
        json.dump(m, f, ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main(sys.argv[1:])
