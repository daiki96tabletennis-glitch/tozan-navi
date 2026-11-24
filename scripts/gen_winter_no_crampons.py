# -*- coding: utf-8 -*-
"""記事「冬でも登れる関東の山7選」（/articles/winter-no-crampons/）を作る。手で編集しない（2026-11-24〜）

運営者の指示「キーエンスの資料の考え方で作り直したらどうなるか、アイゼン不要記事で試作して」→ 試作を6回直して「反映する」。
試作は .claude/prototypes/proto_winter_no_crampons.py（--standalone で1つの HTML にもできる）。
考え方：見出しは結論・文字の階層を固定・色に意味（緑＝おすすめと次の行動／青＝時間／琥珀＝冬の注意／灰＝補足）・7山は同じ形のくり返し・最後に次の行動。
運営者の指示で外したもの：7山の説明の見出し、比較の一覧、時間を逆算する欄、冒頭の3つの数字。入れたもの：大きな山名、装備カード、コース定数、
冒頭の紹介文、おすすめ記事8本、Lucide の線画アイコン。題名（title・h1）は公開中のものを変えない（ページから読む）。チェーンスパイクは「あれば」。

値は mountains.json・gear-data.json から作る。山ごとの文は TEXTS（前の記事のカードの文。2026-11-18 の版）。
ページの head（検索の見出し・説明文・構造化データ・計測）は今のページのものを残し、style だけ入れ替える。
装備カードの描き方（GEAR_ICONS の script）は今のページから写す（add_snowshoe_ui などがページの中を直すため）。
前の作り方（scripts/migrations/update_winter_no_crampons_2026_11.py）は使わない。前の見た目の CSS は scripts/winter_specials_base.css（冬の特集の記事が使う）。
山のデータ（時間・コース・装備・写真）を直したら流す。何度流しても同じ結果。
"""
import html
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'articles', 'winter-no-crampons', 'index.html')
UPDATED = '2026-11-24'
MARK = '<!-- generated: scripts/gen_winter_no_crampons.py -->'
spec = importlib.util.spec_from_file_location('w', os.path.join(ROOT, 'scripts/migrations/update_winter_no_crampons_2026_11.py'))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
E = html.escape

# 山ごとの文（前の記事のカードの文。特徴＝どんな山？、おすすめ理由＝冬に行く理由）
TEXTS = {
    "takao": [
        "標高599mで積雪はほとんどなし。冬晴れの日は山頂から富士山が美しく見える絶好のシーズン。",
        "都心から最もアクセスしやすい山のひとつ。冬は混雑が少なく、澄んだ空気の中で富士山の眺めを楽しめます。"
    ],
    "nokogiriyama_chiba": [
        "千葉県の低山ながら、巨大な石切り場跡・日本一の大仏・絶壁「地獄のぞき」と見どころが詰まった個性派の山。ロープウェイでも登れます。",
        "標高が低く、例年は積雪が少なくて、滑り止めなしで歩ける日が多い山です。絶景スポットが多く、冬の澄んだ空気の中で東京湾越しに富士山が見えることもあります。"
    ],
    "koubousan": [
        "秦野駅・鶴巻温泉駅から歩いて登れる標高235mの低山。吾妻山・権現山・弘法山を結ぶ約4kmのなだらかな稜線歩きで、雪や凍結の心配がほとんどありません。",
        "冬は空気が澄み、権現山の展望台から富士山と丹沢の山並みがよく見えます。駅から歩けてバスの時刻を気にしなくてよく、下山後は鶴巻温泉で温まれます。"
    ],
    "tenzandake": [
        "飯能駅から歩いて登れる2つの低山。天覧山の山頂から、飯能の街と関東平野、東京スカイツリーや新宿のビル群まで見渡せます。",
        "明治天皇が山頂から演習をご覧になったのが名前の由来で、徳川綱吉の母・桂昌院が寄進した十六羅漢の石仏、常盤御前の伝説が残る「見返り坂」、多峯主山の「雨乞いの池」と歴史の見どころが続きます。駅から歩き始められ、バスの時刻を気にしなくてよい山です。"
    ],
    "jinba": [
        "標高850m台で積雪はほぼなし。冬は落葉して見通しが良く、稜線歩きが快適に楽しめます。",
        "冬は登山者が少なく静かな山歩きが楽しめます。高尾山への縦走コースと組み合わせれば充実した一日になります。"
    ],
    "tsukuba": [
        "「西の富士、東の筑波」と並び称された百名山。男体山と女体山の2つの峰があり、最高点の女体山から霞ヶ浦と関東平野を見下ろす360度の眺めが広がります。",
        "白雲橋コースは「弁慶七戻り」「胎内くぐり」「ガマ石」など、名前のついた巨岩が次々に現れて飽きません。2つの峰のあいだの御幸ヶ原にはケーブルカーの駅と食堂・売店があり、山頂の本殿では登った人だけの御朱印を受けられます。"
    ],
    "myojingatake": [
        "箱根の外輪山のひとつ。山全体がカヤとササにおおわれて空が広く、日が当たると笹が黄金色に光ります。",
        "山頂から金時山の向こうに富士山が見え、大涌谷・芦ノ湖・相模湾までぐるりと見渡せます。大雄山駅からバスで行ける最乗寺から登れ、金時山へ尾根をつないで歩くこともできます。7山の中ではいちばん高い1,169mですが、装備の区分は冬も「アイゼン不要」です。"
    ]
}
# 山ごとの「結論の見出し」（今の記事の文・featurePoints に書いてあることだけで作る）
HEAD = {
    'takao': '新宿から55分。ケーブルカーで登りを短くできる定番の山',
    'nokogiriyama_chiba': '石切り場の跡と地獄のぞき。駅から歩け、ロープウェーでも登れる',
    'koubousan': '駅から駅へ。なだらかな稜線を歩いて、下山後は温泉へ',
    'tenzandake': '飯能駅から歩ける。石仏や伝説の残る歴史の低山',
    'jinba': '落葉して見通しの良い稜線と、360度の山頂',
    'tsukuba': '名前のついた巨岩をめぐる、2つの峰の百名山',
    'myojingatake': '笹の尾根の先に、富士山と箱根の全景',
}
# 目的で選ぶ（どれも今の記事の文・データに書いてあること）
FUJI = {'takao', 'nokogiriyama_chiba', 'koubousan', 'myojingatake'}  # 記事の文に富士山の眺めが書いてある山
STATION = {'takao', 'nokogiriyama_chiba', 'koubousan', 'tenzandake'}  # 新宿から電車だけで行き、駅から歩き始める


def photo_of(m, graded):
    """山の写真（山ページと同じ順）。仕上げた版（photo_graded.json）があればそちら（前の記事と同じ。クレジットは card-photo-credits.js が元の記録で引く）"""
    out = []
    for p in m.get('photos') or []:
        g = (graded.get(p) or {}).get('graded')
        out.append(g if g and os.path.exists(os.path.join(ROOT, g.lstrip('/'))) else p)
    return out


# 写真の切り替え（山ページ・前の記事と同じ 4.5秒。動きを減らす設定の端末では切り替えない）
CAROUSEL_JS = """(function(){
  if(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.querySelectorAll('.mountain-photo-carousel').forEach(function(wrap){
    var imgs = wrap.querySelectorAll('img');
    var dots = wrap.querySelectorAll('.mountain-photo-dot');
    if(imgs.length < 2) return;
    var idx = 0;
    setInterval(function(){
      imgs[idx].classList.remove('mpc-active');
      if(dots[idx]) dots[idx].classList.remove('mpc-active');
      idx = (idx + 1) % imgs.length;
      imgs[idx].classList.add('mpc-active');
      if(dots[idx]) dots[idx].classList.add('mpc-active');
    }, 4500);
  });
})();"""


def photo_box(name, photos):
    """写真が複数あれば、山ページと同じく4.5秒ごとに切り替え、下に点で枚数を出す（2026-11-24。運営者の指示）。
    枠の class は card-photo-credits.js がクレジットを1行にまとめる mountain-photo-carousel"""
    if not photos:
        return f'<div class="mc-nophoto">{E(name)}の写真は準備中</div>'
    if len(photos) == 1:
        return f'<img class="mc-photo" src="{E(photos[0])}" alt="{E(name)}" loading="lazy">' + credit(photos[0])
    act = ' class="mpc-active"'
    imgs = ''.join(f'<img src="{E(p)}" alt="{E(name)}" loading="lazy"{act if i == 0 else ""}>' for i, p in enumerate(photos))
    dots = ''.join(f'<span class="mountain-photo-dot{" mpc-active" if i == 0 else ""}"></span>' for i in range(len(photos)))
    return (f'<div class="mountain-photo-carousel mc-photo">{imgs}<div class="mountain-photo-dots">{dots}</div></div>'
            + ''.join(credit(p) for p in photos))


def coeff(m):
    return f'{m["coeffMin"]}〜{m["coeffMax"]}' if m.get('coeffMin') != m.get('coeffMax') else str(m['coeffMin'])


def hm(n):
    return f'{n // 60}:{n % 60:02d}'


def dur(n):
    h, m = divmod(int(n), 60)
    return (f'{h}時間' if h else '') + (f'{m}分' if m else '')


CSS = r"""
:root{--bg:#f0ede5;--paper:#fff;--ink:#23201b;--sub:#5c554c;--note:#8a8078;--line:#e3ddd1;
--green:#4e6535;--green-bg:#eef2e6;--blue:#2f6690;--blue-bg:#e8f0f6;--amber:#9a6412;--amber-bg:#fbf1df;--gray-bg:#efece6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:'Zen Kaku Gothic New',system-ui,sans-serif;line-height:1.75;-webkit-text-size-adjust:100%}
a{color:var(--green)}
.num{font-family:Outfit,'Zen Kaku Gothic New',sans-serif;font-feature-settings:"tnum"}
.wrap{max-width:880px;margin:0 auto;padding:0 16px}
.proto{background:#2a2520;color:#f4efe6;font-size:12px;text-align:center;padding:6px 16px}
/* 文字の階層：ラベル → 見出し → 本文 → 注釈 */
.label{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.08em;color:var(--green);margin:0 0 6px}
.label.blue{color:var(--blue)}.label.amber{color:var(--amber)}
h1{font-size:clamp(26px,6vw,36px);line-height:1.35;margin:0 0 12px;font-weight:900;letter-spacing:.01em}
h2{font-size:clamp(21px,4.6vw,26px);line-height:1.45;margin:0 0 6px;font-weight:900}
h3{font-size:19px;line-height:1.5;margin:0 0 8px;font-weight:900}
.lead{font-size:16px;color:var(--sub);margin:0 0 18px}
.note{font-size:12px;color:var(--note);line-height:1.6}
section{padding:40px 0 8px}
.sec-sub{font-size:15px;color:var(--sub);margin:0 0 18px}
/* ヒーロー */
.hero{padding:32px 0 8px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:18px 0 12px}
.stat{background:var(--paper);border-radius:14px;padding:14px 14px 12px}
.stat .k{font-size:12px;color:var(--sub);font-weight:700}
.stat .v{font-size:clamp(20px,4.8vw,28px);font-weight:800;line-height:1.25;margin:2px 0}
.stat .v small{font-size:13px;font-weight:700}
.stat.green .v{color:var(--green)}.stat.blue .v{color:var(--blue)}
.intro{background:var(--paper);border-radius:14px;padding:14px 16px;margin:0 0 14px;font-size:15px}
.intro p{margin:0 0 8px}.intro p:last-child{margin:0}
.rel{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.rel a{display:flex;flex-direction:column;background:var(--paper);border-radius:14px;overflow:hidden;text-decoration:none;color:var(--ink)}
.rel img{width:100%;aspect-ratio:1200/630;object-fit:cover;display:block;background:#dcd6c8}
.rel .ph{aspect-ratio:1200/630;background:linear-gradient(135deg,#c9d2bb,#e7e2d5)}
.rel span{display:block;padding:10px 12px 12px;font-size:14px;font-weight:700;line-height:1.5}
.rel small{display:block;font-weight:500;color:var(--note);font-size:12px;margin-top:2px}
@media (max-width:640px){.rel{grid-template-columns:1fr 1fr;gap:10px}.rel span{font-size:13px}}
.caution{background:var(--amber-bg);color:#5a3d0c;border-radius:12px;padding:10px 14px;font-size:14px;display:flex;gap:8px;align-items:flex-start}
.caution b{color:var(--amber)}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin:14px 0 0;font-size:12px;color:var(--sub)}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}
/* 目的で選ぶ（並ぶ情報＝カード） */
.goals{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.goal{background:var(--paper);border-radius:14px;padding:16px}
.goal h3{font-size:17px;margin:0 0 4px}
.goal p{margin:0 0 10px;font-size:13px;color:var(--sub)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-block;background:var(--green-bg);color:var(--green);font-weight:700;font-size:13px;padding:4px 10px;border-radius:999px;text-decoration:none}
/* 比べる（棒で見せる） */
.cmp{background:var(--paper);border-radius:14px;padding:6px 16px}
.cmp-row{display:grid;grid-template-columns:150px 1fr 74px;gap:4px 12px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}
.cmp-row:last-child{border-bottom:none}
.cmp-name{font-weight:800;font-size:15px;text-decoration:none;color:var(--ink)}
.cmp-name small{display:block;font-weight:500;font-size:12px;color:var(--note)}
.bars{display:grid;gap:5px}
.bar{display:grid;grid-template-columns:54px 1fr;align-items:center;gap:8px;font-size:12px;color:var(--sub)}
.track{height:10px;background:var(--gray-bg);border-radius:6px;overflow:hidden}
.fill{height:100%;background:var(--blue);border-radius:6px}
.fill.walk{background:#6c93b3}
.bar b{font-size:12px;color:var(--ink);font-weight:700;margin-left:6px;white-space:nowrap}
.start{text-align:right}
.start .t{font-size:20px;font-weight:800;color:var(--blue);line-height:1.1}
.start .s{font-size:11px;color:var(--note)}
/* フロー（時間の流れ） */
.flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;align-items:stretch;gap:8px}
.step{background:var(--paper);border-radius:14px;padding:14px 12px;text-align:center}
.step .t{font-size:22px;font-weight:800;color:var(--blue);line-height:1.2}
.step .d{font-size:13px;color:var(--sub);margin-top:4px;line-height:1.5}
.step.end{background:var(--amber-bg)}.step.end .t{color:var(--amber)}
.step.goal-s{background:var(--green-bg)}.step.goal-s .t{color:var(--green)}
.arrow{align-self:center;color:var(--note);font-size:18px}
/* 前後の比較（左＝前のやり方・灰、右＝冬の計画・緑で広め） */
.ba{display:grid;grid-template-columns:2fr 3fr;gap:12px;margin-top:14px}
.ba>div{border-radius:14px;padding:14px 16px}
.ba .before{background:var(--gray-bg);color:var(--sub)}
.ba .after{background:var(--green-bg)}
.ba .k{font-size:12px;font-weight:700;margin-bottom:4px}
.ba .after .k{color:var(--green)}
.ba p{margin:0;font-size:14px}
/* 山のカード（7山とも同じ形） */
.mc{background:var(--paper);border-radius:18px;overflow:hidden;margin:0 0 22px;scroll-margin-top:12px}
.mc-head{padding:18px 18px 10px}
.mc-title{font-size:clamp(26px,6.4vw,32px);line-height:1.25;margin:0;font-weight:900;display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 10px}
.mc-title small{font-size:14px;font-weight:700;color:var(--note)}
.mc-no{color:var(--green)}
.mc-catch{font-size:16px;font-weight:700;color:var(--green);margin:8px 0 0;line-height:1.55}
.mc-name{font-size:13px;color:var(--sub);margin:4px 0 0}
.mc-photo{aspect-ratio:3/2;width:100%;max-height:380px;object-fit:cover;display:block;background:#dcd6c8}
.mountain-photo-carousel{position:relative;overflow:hidden}
.mountain-photo-carousel img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transition:opacity 1s ease}
.mountain-photo-carousel img.mpc-active{opacity:1}
.mountain-photo-dots{position:absolute;left:0;right:0;bottom:8px;display:flex;justify-content:center;gap:5px;z-index:2}
.mountain-photo-dot{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,0.5);transition:background .3s}
.mountain-photo-dot.mpc-active{background:#fff}
.mc-nophoto{aspect-ratio:3/1;background:linear-gradient(135deg,#c9d2bb,#e7e2d5);display:flex;align-items:center;justify-content:center;color:#5f6b52;font-size:13px}
.mc-body{display:grid;grid-template-columns:2fr 3fr;gap:18px;padding:16px 18px 6px}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:8px;align-content:start}
.fact{background:var(--blue-bg);border-radius:10px;padding:8px 10px}
.fact .k{font-size:11px;color:var(--blue);font-weight:700}
.fact .v{font-size:17px;font-weight:800;line-height:1.3}
.fact.coeff{background:var(--green-bg)}.fact.coeff .k{color:var(--green)}
.fact.deadline{grid-column:1/-1;background:var(--blue);color:#fff}
.fact.deadline .k{color:#d7e6f1}.fact.deadline .v{font-size:22px}
.fact.deadline .s{font-size:11px;color:#d7e6f1}
.why{font-size:14px}
.why .k{font-size:12px;font-weight:700;color:var(--green);margin:0 0 2px}
.why p{margin:0 0 12px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.tag{font-size:12px;font-weight:700;border-radius:6px;padding:2px 8px;background:var(--gray-bg);color:var(--sub)}
.tag.g{background:var(--green-bg);color:var(--green)}
.course{font-size:12px;color:var(--note);margin:0 0 12px}
.mc-cta{display:flex;justify-content:space-between;align-items:center;gap:10px;background:var(--green);color:#fff;text-decoration:none;padding:12px 18px;font-weight:700;font-size:14px}
.mc-cta span:last-child{font-size:18px}
/* 持ち物 */
.kit{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.kit .goal h3{font-size:16px}
/* よくある質問 */
details.qa{background:var(--paper);border-radius:12px;padding:12px 16px;margin:0 0 8px}
details.qa summary{font-weight:700;cursor:pointer}
details.qa p{margin:8px 0 0;font-size:14px;color:var(--sub)}
/* 結論と次の行動 */
.next{background:linear-gradient(120deg,#4e6535,#3f6f6a);color:#fff;border-radius:18px;padding:22px 20px;margin:36px 0 40px}
.next h2{color:#fff}
.next ol{margin:12px 0 16px;padding:0;list-style:none;display:grid;gap:8px;counter-reset:n}
.next li{counter-increment:n;display:flex;gap:10px;align-items:flex-start;font-size:15px}
.next li::before{content:counter(n);flex:0 0 26px;height:26px;border-radius:50%;background:#fff;color:var(--green);font-weight:800;display:flex;align-items:center;justify-content:center;font-family:Outfit,sans-serif}
.next a.btn{display:inline-block;background:#fff;color:var(--green);font-weight:800;text-decoration:none;border-radius:999px;padding:10px 18px;margin:4px 8px 0 0;font-size:14px}
@media (max-width:640px){
 .stats{grid-template-columns:1fr}
 .stat{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
 .goals,.kit{grid-template-columns:1fr}
 .cmp-row{grid-template-columns:1fr 70px}
 .cmp-row .bars{grid-column:1/-1;grid-row:2}
 .flow{grid-template-columns:1fr;gap:6px}
 .arrow{transform:rotate(90deg);justify-self:center;line-height:1}
 .ba{grid-template-columns:1fr}
 .mc-body{grid-template-columns:1fr}
}
"""


SITE = 'https://tozan-navi.com'
CREDITS = {}


def credit(path):
    """1つのファイルで見るとき（--standalone）だけ、写真の作者・ライセンスを書き込む（ふだんは card-photo-credits.js が出す）"""
    p = CREDITS.get(path)
    if not p:
        return ''
    lic = f'<a href="{E(p["licenseUrl"])}" target="_blank" rel="noopener">{E(p["license"])}</a>' if p.get('licenseUrl') else E(p.get('license') or '')
    src = f'・<a href="{E(p["commonsPageUrl"])}" target="_blank" rel="noopener">Wikimedia Commons</a>' if p.get('commonsPageUrl') else ''
    return f'<details class="note ym-photo-credit" style="padding:4px 18px 0"><summary style="cursor:pointer;color:#7a776e">写真クレジット</summary><div style="margin-top:2px">写真：{E(p.get("author") or "")}（{lic}{src}）</div></details>'


sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import ym_icons  # noqa: E402

# 線画のアイコン（Lucide。今の記事と同じ ym_icons を使う。2026-11-24 運営者の指示「今と同じく適宜lucideアイコン入れて」）
ICON_AT = [
    # (置き換える文字, アイコン, 出る数)
    ('<span class="label">選び方</span>', 'signpost', 1),
    ('<h3>駅から歩き始めたい</h3>', 'train-front', 1),
    ('<h3>乗り物で楽をしたい</h3>', 'route', 1),
    ('<h3>富士山を見たい</h3>', 'mountain-snow', 1),
    ('<h3>3時間以内で歩きたい</h3>', 'timer', 1),
    ('<div class="k">冬は何時までに歩き始める？</div>', 'clock', 7),
    ('<div class="k">歩く時間</div>', 'footprints', 7),
    ('<div class="k">新宿から電車</div>', 'train-front', 7),
    ('<div class="k">新宿から車</div>', 'car', 7),
    ('<div class="k">コース定数</div>', 'chart', 7),
    ('<div class="k">どんな山？</div>', 'mountain', 7),
    ('<div class="k">冬に行く理由</div>', 'snowflake', 7),
    ('<p class="course">代表コース：', 'route', 7),
    ('<span class="tag g">通年アイゼン不要</span>', 'snowflake', 7),
    ('<span class="tag g">駅から歩ける</span>', 'train-front', 4),
    ('<span class="label amber">持ち物</span>', 'backpack', 1),
    ('<h3>チェーンスパイク（あれば）</h3>', 'hiking-boot', 1),
    ('<h3>ヘッドランプ</h3>', 'lightbulb', 1),
    ('<h3>重ね着できる防寒着</h3>', 'down-jacket', 1),
    ('<span class="label">よくある質問</span>', 'message-circle', 1),
    ('<span class="label" style="color:#d9e6cf">まとめ</span>', 'check', 1),
    ('<span class="label">あわせて読みたい</span>', 'book-open', 1),
]
CAR = ('<svg class="ym-ic" width="1.05em" height="1.05em" viewBox="0 0 24 24" aria-hidden="true" style="vertical-align:-0.15em;margin-right:4px">'
       '<path d="M4 13l1.5-4A2 2 0 0 1 7.3 8h9.4a2 2 0 0 1 1.8 1.2L20 13z" fill="currentColor"/><rect x="2.5" y="13" width="19" height="4.5" rx="2" fill="currentColor"/>'
       '<rect x="6.5" y="9.2" width="4" height="2.8" rx="0.5" fill="white"/><rect x="11.5" y="9.2" width="6" height="2.8" rx="0.5" fill="white"/>'
       '<circle cx="6.5" cy="17.5" r="1.6" fill="#3a3530"/><circle cx="17.5" cy="17.5" r="1.6" fill="#3a3530"/></svg>')  # 車は今の記事と同じ形（Lucide に合う形が無い）


# コース定数は、サイトの記事でコース定数に使っている棒グラフ（Lucide chart-column）と同じ形
CHART = ('<svg class="ym-ic" width="1.05em" height="1.05em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true" style="vertical-align:-0.15em;margin-right:4px;flex-shrink:0">'
         '<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>')


def ic(name):
    if name == 'chart':
        return CHART
    if name == 'car':
        return CAR
    return ym_icons.svg(name, '1.05em', 'ym-ic', 'vertical-align:-0.15em;margin-right:4px;flex-shrink:0')


def add_icons(doc):
    for text, name, n in ICON_AT:
        assert doc.count(text) == n, (text, doc.count(text))
        m = re.match(r'(<[^>]+>)(.*)$', text, flags=re.S)
        doc = doc.replace(text, m.group(1) + ic(name) + m.group(2))
    # 注意の絵文字も線画に（今の記事と同じ triangle-alert）
    assert doc.count('<span>⚠️</span>') == 1
    doc = doc.replace('<span>⚠️</span>', '<span style="color:var(--amber)">' + ym_icons.svg('triangle-alert', '1.15em', 'ym-ic', 'vertical-align:-0.2em') + '</span>')
    return doc


def main(out=PAGE, standalone=False):
    if standalone:
        for lst in json.load(open(os.path.join(ROOT, 'data/image-credits.json'), encoding='utf-8')).values():
            for p in lst if isinstance(lst, list) else []:
                if p.get('localPath'):
                    CREDITS[p['localPath']] = p
    ms = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))}
    gear = json.load(open(os.path.join(ROOT, 'data/gear-data.json'), encoding='utf-8'))
    page = open(PAGE, encoding='utf-8').read()
    graded = json.load(open(os.path.join(ROOT, 'data/photo_graded.json'), encoding='utf-8')).get('photos') or {}
    header = re.search(r'<header class="ym-site-header".*?</header>', page, flags=re.S).group(0)
    faq = w.faq_items(page)
    live_title = re.search(r'<title>([^<]*)</title>', page).group(1)
    live_h1 = re.search(r'<h1 class="article-title">(.*?)</h1>', page, flags=re.S).group(1)
    # head は今のページのものを残す（style だけ入れ替え、更新日を直す）
    head = page[:page.index('</head>')]
    head = re.sub(r'<style[^>]*>.*?</style>\s*', '', head, flags=re.S).rstrip() + '\n'
    head, n = re.subn(r'"dateModified":"[0-9-]+"', '"dateModified":"' + UPDATED + '"', head)
    if n < 1:
        raise SystemExit('dateModified が無い')
    tail = ''.join(re.findall(r'<script src="/assets/js/(?:to-top|card-photo-credits|share-btn)\.js[^"]*" defer></script>\n?', page))
    if tail.count('<script') != 3:
        raise SystemExit('ページの末尾のスクリプトが見つからない')
    # 装備カードの描き方と見た目は今の記事から写す
    gear_js = next(x for x in re.findall(r'<script>(.*?)</script>', page, flags=re.S) if 'GEAR_ICONS' in x)
    mk = re.search(r'/\* gear-cards:start \*/(.*?)/\* gear-cards:end \*/', page, flags=re.S)
    gear_css = mk.group(1).strip() if mk else '\n'.join(re.findall(r'[^{}]*gear[^{}]*\{[^{}]*\}', ''.join(re.findall(r'<style[^>]*>(.*?)</style>', page, flags=re.S))))
    rows = []
    for k, mid in enumerate(w.ORDER):
        m = ms[mid]
        f, why = TEXTS[mid]
        r0 = m['routes'][0]
        walk = w.walk_min(r0['time'])
        rows.append({'k': k, 'id': mid, 'm': m, 'f': f, 'why': why, 'r0': r0, 'walk': walk,
                     'start': (w.FINISH - walk - w.MARGIN) // 10 * 10,
                     'train': int(m['trainTimeShinjuku']), 'car': int(m['driveTimeShinjuku']),
                     'photo': photo_of(m, graded)})
    tmin, tmax = min(r['train'] for r in rows), max(r['train'] for r in rows)
    smin, smax = min(r['start'] for r in rows), max(r['start'] for r in rows)
    name = {r['id']: w.LIST_NAME.get(r['id'], r['m']['name']) for r in rows}

    def chips(ids):
        return '<div class="chips">' + ''.join(f'<a class="chip" href="#m-{i}">{E(name[i])}</a>' for i in w.ORDER if i in ids) + '</div>'

    short = {r['id'] for r in rows if r['walk'] <= 180}
    goals = [
        ('駅から歩き始めたい', 'バスの時刻を気にしなくてよい', STATION),
        ('乗り物で楽をしたい', 'ケーブルカー・ロープウェーで登り下りを短くできる', set(w.LIFT) & set(w.ORDER)),
        ('富士山を見たい', '冬の澄んだ空気で眺めが良い日が多い', FUJI),
        ('3時間以内で歩きたい', '代表コースの歩く時間が3時間以内', short),
    ]
    goals_html = ''.join(f'<div class="goal"><h3>{E(t)}</h3><p>{E(s)}</p>{chips(ids)}</div>' for t, s, ids in goals)

    maxt = max(max(r['train'] for r in rows), max(r['walk'] for r in rows))
    cmp_html = ''
    for r in rows:
        cmp_html += (f'<div class="cmp-row"><a class="cmp-name" href="#m-{r["id"]}">{w.NUM[r["k"]]} {E(name[r["id"]])}'
                     f'<small>{E(w.short_area(r["m"]["area"]))}・{r["m"]["elevation"]:,}m・{E(r["m"]["difficulty"])}</small></a>'
                     '<div class="bars">'
                     f'<div class="bar"><span>電車</span><div class="track"><div class="fill" style="width:{r["train"] / maxt * 100:.0f}%"></div></div></div>'
                     f'<div class="bar"><span>歩く</span><div class="track"><div class="fill walk" style="width:{r["walk"] / maxt * 100:.0f}%"></div></div></div>'
                     '</div>'
                     f'<div class="start"><div class="t num">{hm(r["start"])}</div><div class="s">までに歩き始め</div></div></div>')
        # 棒の数値は行の下に小さく（棒だけでは読めないため）
        cmp_html = cmp_html[:-len('</div>')] + (f'<div class="note" style="grid-column:1/-1;margin-top:-2px">新宿から電車 <span class="num">{dur(r["train"])}</span>・車 <span class="num">{dur(r["car"])}</span>'
                                               f'／歩く <span class="num">{E(r["r0"]["time"])}</span>{"・" + E(w.LIFT[r["id"]]) + "あり" if r["id"] in w.LIFT else ""}</div></div>')

    cards = ''
    for r in rows:
        m, mid = r['m'], r['id']
        photo = photo_box(m['name'], r['photo'])
        tags = ['<span class="tag g">通年アイゼン不要</span>']
        if mid in STATION:
            tags.append('<span class="tag g">駅から歩ける</span>')
        if mid in w.LIFT:
            tags.append(f'<span class="tag g">{E(w.LIFT[mid])}あり</span>')
        tags.append(f'<span class="tag">難易度 {E(m["difficulty"])}</span>')
        cards += (
            f'<article class="mc" id="m-{mid}">'
            f'<div class="mc-head"><h3 class="mc-title"><span class="mc-no num">{w.NUM[r["k"]]}</span>{E(m["name"])}<small>{E(m.get("kana") or "")}</small></h3>'
            f'<p class="mc-catch">{E(HEAD[mid])}</p><p class="mc-name">{E(w.short_area(m["area"]))}・標高 <span class="num">{m["elevation"]:,}</span>m</p></div>'
            f'{photo}'
            '<div class="mc-body"><div class="facts">'
            f'<div class="fact deadline"><div class="k">冬は何時までに歩き始める？</div><div class="v num">{hm(r["start"])}まで</div>'
            '<div class="s">15:30に下山を終える場合（休憩・遅れの余裕1時間込み）</div></div>'
            f'<div class="fact"><div class="k">歩く時間</div><div class="v num">{E(r["r0"]["time"])}</div></div>'
            f'<div class="fact"><div class="k">新宿から電車</div><div class="v num">{dur(r["train"])}</div></div>'
            f'<div class="fact"><div class="k">新宿から車</div><div class="v num">{dur(r["car"])}</div></div>'
            f'<div class="fact coeff"><div class="k">コース定数</div><div class="v num">{coeff(m)}</div></div>'
            '</div><div class="why">'
            f'<div class="tags">{"".join(tags)}</div>'
            f'<div class="k">どんな山？</div><p>{E(r["f"])}</p>'
            f'<div class="k">冬に行く理由</div><p>{E(r["why"])}</p>'
            f'<p class="course">代表コース：{E(r["r0"]["name"])}</p>'
            '</div></div>'
            f'<div class="mc-gear"><div class="gear-section-label">{E(m["name"])}の装備（行く月に合わせて出ます）</div>'
            f'<div class="gear-cards-scroll" data-gear-mid="{mid}" data-gear-variants="{w.variants_attr(gear[mid])}"></div></div>'
            f'<a class="mc-cta" href="/mountains/{mid}/"><span>{E(m["name"])}の行き方・コース・装備を見る</span><span>→</span></a>'
            '</article>')

    faq_html = ''.join(f'<details class="qa"><summary>{E(q["name"])}</summary><p>{E(q["acceptedAnswer"]["text"])}</p></details>' for q in faq)
    names = '・'.join(name[i] for i in w.ORDER)
    doc = f'''{head}<style>{CSS}
/* gear-cards:start */
{gear_css}
/* gear-cards:end */
.mc-gear{{padding:0 18px 12px}}</style>
</head>
<body>
{MARK}
{header}
<main class="wrap">
<div class="hero">
 <span class="label">冬の低山ガイド 2026-27</span>
 <h1 class="article-title">{live_h1}</h1>
 <p class="lead">装備・移動時間・何時までに歩き始めるかを、1ページで比べられます。</p>
 <p class="note" style="margin:-10px 0 14px">最終更新: {UPDATED}</p>
 <div class="intro">
  <p>積雪の少ない冬の低山は、空気が澄んで眺めがよく、虫が少なく、落ち葉で見通しも良い季節です。ここで選んだ7山は、Yamatch の装備カレンダーで<b>通年「アイゼン不要」</b>の山です。</p>
  <p>駅から歩き始められる山、ケーブルカーやロープウェーで楽ができる山、富士山が見える山と、目的に合わせて選べます。電車・バスで行ける日帰りの山は<a href="/search/train-daytrip/">電車で行ける日帰り登山</a>もどうぞ。</p>
 </div>
 <div class="caution"><span>⚠️</span><span><b>雪のあとの数日は、凍結が残ることがあります。</b>日陰や木道は滑りやすいので、チェーンスパイクがあれば持っていくと安心です。</span></div>
 <div class="legend"><span><i style="background:var(--green)"></i>おすすめ・次にすること</span><span><i style="background:var(--blue)"></i>時間</span><span><i style="background:var(--amber)"></i>冬の注意</span><span><i style="background:#c9c3b8"></i>補足</span></div>
</div>

<section id="goals">
 <span class="label">選び方</span>
 <h2>目的から選べば、迷わない</h2>
 <p class="sec-sub">山名を押すと、その山の説明へ移ります。</p>
 <div class="goals">{goals_html}</div>
</section>

<section id="mountains">
 {cards}
</section>

<section id="kit">
 <span class="label amber">持ち物</span>
 <h2>いつもの日帰り装備に、冬の3つを足す</h2>
 <div class="kit">
  <div class="goal"><h3>チェーンスパイク（あれば）</h3><p>雪のあとの数日は、日の当たらない斜面や木道に凍結が残ることがあります。持っていれば入れておくと安心です。</p></div>
  <div class="goal"><h3>ヘッドランプ</h3><p>冬は日が短く、山の中は早く暗くなります。日帰りでも必ず入れます。</p></div>
  <div class="goal"><h3>重ね着できる防寒着</h3><p>汗冷えを防ぐ速乾性の肌着に、脱ぎ着しやすい防寒着を重ねます。</p></div>
 </div>
 <p class="note" style="margin-top:10px">全部の持ち物は<a href="/packing/?s=day">持ち物チェックリスト</a>で確かめられます。</p>
</section>

<section id="faq">
 <span class="label">よくある質問</span>
 <h2>迷いやすい3つの疑問</h2>
 {faq_html}
</section>

<div class="next">
 <span class="label" style="color:#d9e6cf">まとめ</span>
 <h2>冬晴れの日に、まず1山。準備は3つだけ</h2>
 <ol>
  <li>目的に合う山を1つ選ぶ（{E(names)}）</li>
  <li>前日に、直近の雪と凍結を確かめる</li>
  <li>持ち物を揃え、青い枠の時刻までに歩き始める</li>
 </ol>
 <a class="btn" href="/packing/?s=day">持ち物チェックリスト</a><a class="btn" href="/find/winter/">冬の山選び診断（9問）</a><a class="btn" href="/">条件で山を絞り込む</a>
</div>

<section id="related" style="padding:0 0 40px">
 <span class="label">あわせて読みたい</span>
 <h2>その他のおすすめ記事</h2>
 <div class="rel"><a href="/articles/winter-views/"><img src="/articles/images/hero_winter_views.jpg?v=20261115" alt="" loading="lazy"><span>冬の絶景が見られる山6選<small>樹氷・霧氷・雪原。ロープウェイで行ける山も</small></span></a><a href="/articles/diamond-fuji/"><img src="/articles/images/hero_diamond_fuji.jpg?v=20261115" alt="" loading="lazy"><span>ダイヤモンド富士が見える場所・山<small>いつ何時？2026-2027のカレンダー</small></span></a><a href="/articles/hiking-onsen-sauna/"><img src="/articles/images/hero_onsen_sauna.jpg?v=20261115b" alt="" loading="lazy"><span>登山のあとの温泉・サウナが最高な山12選<small>料金・最終受付・下山後の行き方</small></span></a><a href="/articles/saunachelin-hiking/"><img src="/articles/images/hero_saunachelin_hiking.jpg?v=20261116b" alt="" loading="lazy"><span>サウナシュラン受賞サウナに寄れる山14選<small>登山口から車30分以内・地図つき</small></span></a><a href="/search/train-daytrip/"><div class="ph"></div><span>電車で行ける日帰り登山（関東）20選<small>新宿から何分・運賃・帰りの最終バス</small></span></a><a href="/articles/tokyo-daytrip-5/"><img src="/articles/images/hero_tokyo3h.jpg" alt="" loading="lazy"><span>東京から3時間以内で行ける日帰り登山5選<small>高尾山・大山・陣馬山など</small></span></a><a href="/articles/train-access-mountains/"><img src="/articles/images/hero_train_access.jpg" alt="" loading="lazy"><span>新宿発・電車・バスで行ける登山10選<small>アクセス完全ガイド</small></span></a><a href="/articles/"><div class="ph"></div><span>記事一覧をみる<small>すべての記事・まとめ</small></span></a></div>
</section>
</main>
<script>{gear_js}</script>
<script>{CAROUSEL_JS}</script>
{tail}</body></html>
'''
    doc = add_icons(doc)
    if standalone:
        # 写真・リンクは本番サイトのアドレスにし、クレジットのスクリプトは外す（クレジットは上で書き込んだ）
        doc = re.sub(r'<script src="/assets/js/card-photo-credits[^"]*" defer></script>', '', doc)
        doc = re.sub(r'(src|href)="/(?!/)', lambda m: m.group(1) + '="' + SITE + '/', doc)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(doc)
    print('書いた', out, len(doc))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0] if args else PAGE, '--standalone' in sys.argv)
