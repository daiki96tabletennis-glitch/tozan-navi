#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋まとめ（β）ページ huts/index.html を data/huts.json から作る。使い方：python3 scripts/gen_huts_page.py
作るページ：一覧 /huts/、山ごと /huts/<山ID>/、山小屋ごと /huts/<小屋ID>/（予約の開始も方法も分からない小屋は noindex）。sitemap.xml の /huts/ 以下も入れ直す。
以前の /huts/?m=山ID は、山ごとのページへ送る。"""
import html, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = lambda s: html.escape(str(s or ''), quote=True)
d = json.load(open(os.path.join(ROOT, 'data', 'huts.json'), encoding='utf-8'))
ML = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
M = {m['id']: m for m in ML}
H = d['huts']
NA = '<span class="na">公式サイトで確認</span>'


def split_note(text):
    """「本文（補足）」→ (本文, 補足)。長い補足を小さい字に回して、要点を読みやすくする"""
    # 文の最後にある括弧だけを補足にする（途中の括弧「夏山（5/25〜11/23泊）は…」で切らない）
    text = text or ''
    if not text.endswith('）'):
        return (text or None, None)
    depth = 0
    for i in range(len(text) - 1, -1, -1):
        if text[i] == '）':
            depth += 1
        elif text[i] == '（':
            depth -= 1
            if depth == 0:
                return (text[:i], text[i + 1:-1]) if i >= 2 else (text, None)
    return (text, None)


def fact(label, main, sub=None, cls=''):
    return '<div class="fact %s"><div class="fl">%s</div><div class="fv">%s</div>%s</div>' % (
        cls, label, main, ('<div class="fs">%s</div>' % sub) if sub else '')


regions = []
for h in H:
    if h['region'] not in regions:
        regions.append(h['region'])
cards = []
count = {}
card_of = {}
info = {}
for h in H:
    au = h.get('auto') or {}
    stale = h.get('bookingStale')
    # 公式サイト・予約サイトから自動で読み取れた値を優先する
    start = (au.get('bookingStart') or {}).get('value') or (None if stale else h.get('bookingStart'))
    # 予約サイトの「予約開始のお知らせ」の日時：手で確認した値が無いとき、または手の値より新しい年のときに使う
    web = au.get('bookingStartWeb') or {}
    if web and not (au.get('bookingStart') or {}).get('value'):
        yrs = [int(x) for x in re.findall(r'(20\d\d)年', start or '')]
        if not start or (yrs and max(yrs) < web.get('year', 0)):
            start = web['value']
    # 手で確認した値が無い小屋は、予約サイトに登録されている「何日前から予約できるか」を使う
    start = start or (au.get('bookingWindow') or {}).get('value')
    none = None if stale else h.get('bookingNone')
    cap = (au.get('capacity') or {}).get('value') or h.get('capacity')
    methods = None if stale else h.get('bookingMethods')
    ids = h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]
    for i in ids:
        count[i] = count.get(i, 0) + 1
    # 予約の開始
    if none:
        s_html = fact('予約の開始', '予約不要', '予約の受付がない小屋です')
    elif start:
        a, b = split_note(start)
        s_html = fact('予約の開始', E(a), E(b))
        if h.get('officialChanged') and not au.get('bookingStart'):
            s_html = fact('予約の開始', E(a), E((b + '。' if b else '') + '公式サイトの記載に変更あり。最新は公式サイトで確認'))
    elif stale:
        s_html = fact('予約の開始', '<span class="na">確認中</span>', '出典の記載が変わりました')
    elif h.get('bookingStartUnstated'):
        s_html = fact('予約の開始', '<span class="na">記載なし</span>', '公式サイトに、いつから予約できるかの記載がありません。予約先で確認')
    else:
        s_html = fact('予約の開始', NA)
    # 予約方法
    if none:
        m_html = fact('予約方法', '<span class="mt">予約なし</span>', E(none))
    elif methods:
        tags = ''.join('<span class="mt">%s</span>' % E(split_note(x)[0]) for x in methods)
        subs = '／'.join(E(split_note(x)[1]) for x in methods if split_note(x)[1])
        m_html = fact('予約方法', tags, subs or None)
    else:
        m_html = fact('予約方法', NA)
    # 規模
    ref = h.get('capacityRef')
    if cap:
        c_html = fact('規模（定員）', '%s人' % E(cap), ('参考：以前の収容人数は%s人' % ref) if isinstance(ref, int) and ref != cap else None)
    elif isinstance(ref, int):
        c_html = fact('規模（定員）', '約%s人' % ref, '山と溪谷オンラインの記載。現在の定員は公式サイトで確認')
    elif ref:
        c_html = fact('規模（定員）', E(ref), '山と溪谷オンラインの記載')
    else:
        c_html = fact('規模（定員）', '<span class="na">確認中</span>')
    # 営業期間：公式・予約サイトの値があればそれ、無ければ出典の記載
    season = (au.get('season') or {}).get('value')
    raw = h.get('openText') or ''
    season_main = season or re.sub(r'^2026年の営業：', '', raw) or '—'
    season_sub = '公式・予約サイトの記載' if season else None
    if h.get('officialNote'):
        season_sub = '公式サイトの記載：' + h['officialNote']
    mts = ''.join('<a class="mc" href="/mountains/%s/">%s</a>' % (E(i), E(M[i]['name'])) for i in h['mountainIds'])
    oth = ''.join('<a class="mc mc2" href="/mountains/%s/">%s<small>%s</small></a>' % (E(o['id']), E(M[o['id']]['name']), E(o['relation'])) for o in h.get('otherMountains') or [])
    links = []
    if h.get('officialUrl'):
        links.append('<a class="btn" href="%s" target="_blank" rel="noopener">公式サイト</a>' % E(h['officialUrl'].strip()))
    if h.get('bookingSourceUrl') and h['bookingSourceUrl'] != h.get('officialUrl') and 'yamatan.net' in h['bookingSourceUrl']:
        links.append('<a class="btn btn2" href="%s" target="_blank" rel="noopener">予約サイト</a>' % E(h['bookingSourceUrl']))
    detail = []
    if h.get('location'):
        detail.append('<div><b>場所</b>%s</div>' % E(h['location']))
    if h.get('tel'):
        detail.append('<div><b>電話</b>%s</div>' % E(h['tel']))
    if raw and season:
        detail.append('<div><b>一覧の出典の記載</b>%s</div>' % E(raw))
    elif raw and raw != season_main:
        detail.append('<div><b>出典の記載</b>%s</div>' % E(raw))
    cards.append(
        '<article class="hut" id="%s" data-region="%s" data-m="%s" data-key="%s">\n'
        '  <div class="hh"><h2><a href="/huts/%s/">%s</a></h2><span class="rg">%s</span>%s</div>\n'
        '  <div class="facts">%s%s%s</div>\n'
        '  <div class="season"><span class="sl">営業期間</span><span class="sv">%s</span>%s</div>\n'
        '  <div class="mrow"><span class="sl">対応する山</span><span class="mcs">%s%s</span></div>\n'
        '  <div class="foot">%s%s</div>\n'
        '</article>' % (
            E(h['id']), E(h['region']), E(' '.join(ids)), E(h['name'] + ' ' + ' '.join(M[i]['name'] for i in ids)),
            E(h['id']), E(h['name']), E(h['region']), '<span class="req">予約必須</span>' if h['bookingRequired'] else '',
            s_html, m_html, c_html, E(season_main), ('<span class="ss">%s</span>' % E(season_sub)) if season_sub else '',
            mts, oth, ''.join(links),
            ('<details><summary>くわしく</summary>%s</details>' % ''.join(detail)) if detail else ''))
    card_of[h['id']] = cards[-1]
    info[h['id']] = {'start': None if none else start, 'none': none, 'methods': None if none else methods, 'season': season_main,
                     'cap': cap or (ref if isinstance(ref, int) else None), 'capExact': bool(cap)}
# 「山から探す」：小屋のある山を、県・山域の順に並べる
mt_btns = []
for m in ML:
    if m['id'] in count:
        mt_btns.append('<a class="mb" href="/huts/%s/" data-m="%s" data-name="%s">%sの山小屋<span>%d</span></a>' % (E(m['id']), E(m['id']), E(m['name']), E(m['name']), count[m['id']]))
chips = '<button class="chip on" data-r="">すべて</button>' + ''.join('<button class="chip" data-r="%s">%s</button>' % (E(r), E(r)) for r in regions)
_u = sorted(h['sourceUpdated'] for h in H if h.get('sourceUpdated'))
upd = '%d年%d〜%d月' % (int(_u[0][:4]), int(_u[0][5:7]), int(_u[-1][5:7])) if _u else ''
page = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>山小屋の予約開始日・予約方法まとめ【__YEAR__年】北アルプス・南アルプス・八ヶ岳・富士山ほか__N__軒 | Yamatch</title>
<meta name="description" content="北アルプス・南アルプス・八ヶ岳・富士山・奥秩父・丹沢・尾瀬などの山小屋__N__軒について、__YEAR__年の予約開始日・予約方法（Web・電話）・定員・営業期間を一覧にまとめました。登る山から山小屋を探せます。">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<meta property="og:title" content="山小屋の予約開始日・予約方法まとめ【__YEAR__年】__N__軒 | Yamatch">
<meta property="og:description" content="山小屋__N__軒の予約開始日・予約方法・定員・営業期間の一覧。登る山から探せます。">
<meta property="og:type" content="website">
<meta property="og:url" content="https://tozan-navi.com/huts/">
<link rel="canonical" href="https://tozan-navi.com/huts/">
__HEADCOMMON__
__LD__
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Zen Kaku Gothic New',-apple-system,BlinkMacSystemFont,'Hiragino Sans',sans-serif;background:#f0ede5;color:#2f2b26;line-height:1.6}
header{background:#4e6535;padding:14px 16px}
.hi{max-width:760px;margin:0 auto;display:flex;align-items:center}
.logo{color:#fff;font-size:20px;font-weight:800;text-decoration:none}
.back{margin-left:auto;color:rgba(255,255,255,.9);font-size:12px;text-decoration:none;background:rgba(255,255,255,.15);padding:5px 12px;border-radius:20px}
main{max-width:760px;margin:0 auto;padding:16px}
h1{font-size:22px;font-weight:800;color:#2a3820;margin-bottom:4px}
.beta{font-size:11px;background:#c8d4b8;color:#2a3820;border-radius:4px;padding:2px 7px;margin-left:6px;vertical-align:middle}
.sub{font-size:13px;color:#6a6258;margin-bottom:12px}
.about{background:#fff;border:1px solid #e0dbd4;border-radius:10px;padding:10px 14px;margin-bottom:14px;font-size:12.5px;color:#4a4540}
.about summary{cursor:pointer;font-weight:700;color:#4e6535}
.about li{margin:6px 0 0 18px}
.tabs{display:flex;background:#e2ddd2;border-radius:10px;padding:3px;margin-bottom:12px}
.tab{flex:1;border:none;background:none;padding:9px 6px;font-size:14px;font-weight:700;color:#6a6258;border-radius:8px;cursor:pointer}
.tab.on{background:#fff;color:#2a3820;box-shadow:0 1px 3px rgba(0,0,0,.12)}
#q{width:100%;padding:11px 12px;border:1px solid #d0cbc2;border-radius:10px;font-size:15px;margin-bottom:8px;background:#fff}
.chips{display:flex;gap:6px;margin-bottom:10px;overflow-x:auto;padding-bottom:4px}
.chip{flex-shrink:0;border:1px solid #c8c2b8;background:#fff;border-radius:999px;padding:6px 12px;font-size:12.5px;cursor:pointer;color:#3a3530}
.chip.on{background:#4e6535;color:#fff;border-color:#4e6535}
.mgrid{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.mb{text-decoration:none;border:1px solid #c8c2b8;background:#fff;border-radius:8px;padding:7px 10px;font-size:13.5px;cursor:pointer;color:#2f2b26;display:flex;align-items:center;gap:6px}
.mb span{font-size:11px;background:#e9efe0;color:#4e6535;border-radius:999px;padding:0 6px;font-weight:700}
.mb.on{background:#4e6535;color:#fff;border-color:#4e6535}.mb.on span{background:rgba(255,255,255,.25);color:#fff}
#picked{display:none;background:#e9efe0;border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:14px;font-weight:700;color:#2a3820;align-items:center;gap:10px;flex-wrap:wrap}
#picked a{font-size:12px;font-weight:400;color:#4e6535}
#picked button{margin-left:auto;border:none;background:#fff;border-radius:999px;padding:4px 12px;font-size:12px;cursor:pointer;color:#4e6535}
#cnt{font-size:12px;color:#7a7068;margin-bottom:8px}
.hut{background:#fff;border:1px solid #e0dbd4;border-radius:12px;padding:14px;margin-bottom:12px}
.hh{display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;margin-bottom:10px}
.hh h2{font-size:17px;font-weight:800;color:#2a3820}.hh h2 a{color:inherit;text-decoration:none}
.rg{font-size:11px;color:#6a6258;background:#f0ede5;border-radius:4px;padding:1px 7px}
.req{font-size:11px;font-weight:700;background:#fdf0d8;color:#8a5a10;border-radius:4px;padding:1px 7px}
.facts{display:grid;grid-template-columns:1.4fr 1fr .8fr;gap:8px;margin-bottom:10px}
.fact{background:#f7f5ef;border-radius:8px;padding:8px 10px;min-width:0}
.fl{font-size:10.5px;color:#7a7068;font-weight:700;letter-spacing:.03em;margin-bottom:2px}
.fv{font-size:14.5px;font-weight:700;color:#2f2b26;line-height:1.45;word-break:break-word}
.fs{font-size:11px;color:#7a7068;margin-top:3px;line-height:1.5}
.mt{display:inline-block;background:#fff;border:1px solid #d5cfc4;border-radius:5px;padding:0 7px;margin:0 4px 3px 0;font-size:13px;font-weight:700}
.na{color:#a09888;font-size:12.5px;font-weight:400}
.season,.mrow{display:flex;gap:10px;font-size:13.5px;padding:7px 0;border-top:1px solid #f0ede5;align-items:baseline;flex-wrap:wrap}
.sl{flex-shrink:0;width:5.2em;font-size:11px;color:#7a7068;font-weight:700}
.sv{flex:1;min-width:10em}
.ss{flex-basis:100%;padding-left:calc(5.2em + 10px);font-size:11px;color:#7a7068}
.mcs{flex:1;display:flex;flex-wrap:wrap;gap:5px}
.mc{display:inline-block;background:#e9efe0;color:#2a3820;border-radius:6px;padding:2px 9px;font-size:13px;font-weight:700;text-decoration:none}
.mc2{background:#f3f1ea;color:#5a544a;font-weight:400}.mc2 small{display:block;font-size:10.5px;color:#7a7068}
.foot{display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap;padding-top:8px;border-top:1px solid #f0ede5}
.btn{display:inline-block;background:#4e6535;color:#fff;border-radius:8px;padding:6px 14px;font-size:13px;font-weight:700;text-decoration:none}
.btn2{background:#fff;color:#4e6535;border:1px solid #4e6535}
.foot details{flex:1;min-width:12em;font-size:12px;color:#5a544a}
.foot summary{cursor:pointer;color:#7a7068;padding:6px 0;text-align:right}
.foot details div{padding:3px 0}.foot details b{display:inline-block;min-width:7.5em;color:#7a7068;font-weight:700;font-size:11px}
.src{font-size:11.5px;color:#7a7068;margin-top:14px;line-height:1.8}.src a{color:#4e6535}
.bc{font-size:11.5px;color:#7a7068;margin-bottom:10px}.bc a{color:#4e6535;text-decoration:none}
.lead{font-size:13.5px;color:#3a3530;margin-bottom:12px}
.upd{font-size:11.5px;color:#7a7068;margin-bottom:12px}
.cmp{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e0dbd4;border-radius:10px;font-size:12.5px;margin-bottom:14px}
.cmp th,.cmp td{padding:7px 9px;border-bottom:1px solid #f0ede5;text-align:left;vertical-align:top}
.cmp th{font-size:11px;color:#7a7068;background:#f7f5ef}.cmp td:first-child{min-width:7em}.cmp td:last-child{min-width:4.5em}.cmp a{color:#2a3820;font-weight:700}
.sec{font-size:17px;font-weight:800;color:#2a3820;margin:22px 0 10px}
.faq{background:#fff;border:1px solid #e0dbd4;border-radius:10px;padding:12px 14px;margin-bottom:8px}
.faq dt{font-size:14px;font-weight:700;color:#2a3820;margin-bottom:4px}.faq dd{font-size:13px;color:#3a3530}
.rel{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
footer{text-align:center;padding:20px 16px;font-size:12px;color:#a09888;border-top:1px solid #e8e4dc;margin-top:8px}footer a{color:#6a8055}
@media(max-width:560px){.facts{grid-template-columns:1fr 1fr}.facts .fact:first-child{grid-column:1/-1}}
</style>
</head>
<body>
<header><div class="hi"><a href="/" class="logo">Yamatch</a><a href="/" class="back">← 山を検索する</a></div></header>
<main>
<nav class="bc" aria-label="パンくず"><a href="/">Yamatch</a> › 山小屋まとめ</nav>
<h1>山小屋の予約開始日・予約方法まとめ<span class="beta">β版</span></h1>
<p class="sub">__N__軒の、予約の開始・予約方法・規模・営業期間（__YEAR__年シーズン）</p>
<p class="lead">北アルプス・南アルプス・中央アルプス・八ヶ岳・富士山・奥秩父・丹沢・尾瀬などの山小屋について、「いつから予約できるか」「どうやって予約するか」を山小屋ごとにまとめています。登る山を選ぶと、その山で使える山小屋だけを表示します。</p>
<p class="upd">最終確認：<time datetime="__VERIFIED__">__VERIFIED_JA__</time></p>
<details class="about"><summary>このページの見方・出典</summary>
<ul>
<li>「対応する山」は、当サイトで紹介しているルートの登山口・途中・山頂にある小屋です。別のルートや縦走で使う小屋は、灰色で関係を添えています。</li>
<li>「予約の開始」「予約方法」は、各山小屋の公式サイト・予約サイト・出典の一覧に書かれているものだけを載せています。見つからなかった小屋は「公式サイトで確認」としています。</li>
<li>「規模」は、公式サイト・予約サイトで確認できた定員です。確認できなかった小屋は、山と溪谷オンラインの山小屋情報の収容人数を「約◯人」として載せています（今は定員を減らしている小屋があります）。</li>
<li>富士山・白山・上信越・尾瀬・東北の山小屋の営業期間は「例年」の値です。</li>
<li>営業期間や予約の受付は変わることがあります。予約の前に、必ず各山小屋の公式サイトで確認してください。</li>
</ul>
</details>
<div class="tabs"><button class="tab on" data-v="mt">山から探す</button><button class="tab" data-v="all">山小屋の一覧</button></div>
<div id="v-mt">
<input id="mq" type="search" placeholder="山名でさがす（例：槍ヶ岳）" style="width:100%;padding:11px 12px;border:1px solid #d0cbc2;border-radius:10px;font-size:15px;margin-bottom:8px;background:#fff">
<div class="mgrid" id="mgrid">__MTS__</div>
</div>
<div id="v-all" style="display:none">
<input id="q" type="search" placeholder="山小屋名・山名でさがす（例：涸沢）">
<div class="chips">__CHIPS__</div>
</div>
<div id="cnt"></div>
<div id="list">
__CARDS__
</div>
<p class="src">出典：<a href="https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/sotaikyo/yamagoya/yamagoya.html" target="_blank" rel="noopener">長野県 山小屋情報ポータルサイト</a>（__UPD__更新分）／山と溪谷オンライン <a href="https://www.yamakei-online.com/yama-ya/detail.php?id=2535" target="_blank" rel="noopener">北アルプス山小屋リスト2026</a>・<a href="https://www.yamakei-online.com/yama-ya/detail.php?id=2556" target="_blank" rel="noopener">中央・南アルプス山小屋リスト2026</a>・山小屋情報の各ページ／予約サイト「やまたん」／各山小屋の公式サイト</p>
<h2 class="sec">山小屋の予約でよくある質問</h2>
<dl>
__FAQ__
</dl>
</main>
__FOOTER__
<script>
(function(){
  var view='mt', region='', huts=document.querySelectorAll('.hut');
  var q=document.getElementById('q'), mq=document.getElementById('mq'), cnt=document.getElementById('cnt');
  var list=document.getElementById('list');
  var mbs=document.querySelectorAll('.mb'), i;
  // 以前の形式 /huts/?m=山ID は、山ごとのページへ送る
  var m0=(location.search.match(/[?&]m=([a-z0-9_]+)/)||[])[1];
  if(m0){ for(i=0;i<mbs.length;i++){ if(mbs[i].getAttribute('data-m')===m0){ location.replace('/huts/'+m0+'/'); return; } } }
  function apply(){
    var k=q.value.replace(/\\s+/g,''), n=0, h, ok;
    for(i=0;i<huts.length;i++){
      h=huts[i];
      ok=(!region||h.getAttribute('data-region')===region)&&(!k||h.getAttribute('data-key').indexOf(k)>-1);
      h.style.display=ok?'':'none'; if(ok)n++;
    }
    list.style.display=view==='mt'?'none':'';
    cnt.textContent=view==='mt'?'山を選ぶと、その山の山小屋のページを開きます':n+'軒を表示';
  }
  mq.addEventListener('input',function(){ var k=mq.value.replace(/\\s+/g,''); for(var j=0;j<mbs.length;j++){ mbs[j].style.display=(!k||mbs[j].getAttribute('data-name').indexOf(k)>-1)?'':'none'; } });
  q.addEventListener('input',apply);
  var chips=document.querySelectorAll('.chip');
  for(i=0;i<chips.length;i++){ chips[i].addEventListener('click',function(){ for(var j=0;j<chips.length;j++)chips[j].className='chip'; this.className='chip on'; region=this.getAttribute('data-r'); apply(); }); }
  var tabs=document.querySelectorAll('.tab');
  for(i=0;i<tabs.length;i++){ tabs[i].addEventListener('click',function(){ for(var j=0;j<tabs.length;j++)tabs[j].className='tab'; this.className='tab on'; view=this.getAttribute('data-v'); document.getElementById('v-mt').style.display=view==='mt'?'':'none'; document.getElementById('v-all').style.display=view==='all'?'':'none'; apply(); }); }
  // /huts/#hut-xxxx で開いたときは、一覧に切り替えてその小屋を見せる
  if(location.hash && document.getElementById(location.hash.slice(1))){ tabs[1].click(); document.getElementById(location.hash.slice(1)).scrollIntoView(); }
  else { apply(); }
})();
</script>
</body>
</html>
'''
# ---------- SEO：共通の部品 ----------
BASE = 'https://tozan-navi.com'
YEAR = d['seasonYear']
VERIFIED = max(h['lastVerified'] for h in H if h.get('lastVerified'))
VERIFIED_JA = '%d年%d月%d日' % tuple(int(x) for x in VERIFIED.split('-'))
HEADCOMMON = """<meta property="og:site_name" content="Yamatch">
<meta property="og:locale" content="ja_JP">
<meta property="og:image" content="https://tozan-navi.com/ogp.png">
<meta name="twitter:card" content="summary_large_image">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-TMTVVTEEGF"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-TMTVVTEEGF');
</script>
<link rel="apple-touch-icon" sizes="180x180" href="/icon-180.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon.ico">
<link rel="manifest" href="/manifest.json">"""
FOOTER = """<footer>
<p>Yamatch — 出発地から登る山を探せる登山サーチ</p>
<p style="margin-top:6px"><a href="/">山を検索する</a> <span style="margin:0 8px;opacity:0.4">|</span> <a href="/huts/">山小屋まとめ</a> <span style="margin:0 8px;opacity:0.4">|</span> <a href="/terms/">利用規約</a> <span style="margin:0 8px;opacity:0.4">|</span> <a href="/privacy/">プライバシーポリシー</a> <span style="margin:0 8px;opacity:0.4">|</span> <a href="/about/">運営者</a></p>
<p style="margin-top:8px;opacity:0.6;">© 2026 Yamatch. All rights reserved.</p>
</footer>"""
CSS = re.search(r'<style>(.*?)</style>', page, flags=re.S).group(1)
by_id = {h['id']: h for h in H}


def ld(*objs):
    return '\n'.join('<script type="application/ld+json">%s</script>' % json.dumps(o, ensure_ascii=False) for o in objs)


def crumbs(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': BASE + u} for i, (n, u) in enumerate(items)]}


def lodging(h):
    o = {'@type': 'LodgingBusiness', 'name': h['name'], 'url': BASE + '/huts/%s/' % h['id']}
    if h.get('tel'):
        o['telephone'] = h['tel']
    if h.get('officialUrl'):
        o['sameAs'] = h['officialUrl'].strip()
    return o


def faq_ld(qa):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in qa]}


def faq_html(qa):
    return '\n'.join('<div class="faq"><dt>%s</dt><dd>%s</dd></div>' % (E(q), E(a)) for q, a in qa)


def methods_text(ms):
    return '・'.join(split_note(x)[0] for x in ms) if ms else None


def huts_of(mid):
    """その山の小屋：ルート上の小屋 → 別ルート・縦走の小屋 の順"""
    a = [h for h in H if mid in h['mountainIds']]
    b = [h for h in H if any(o['id'] == mid for o in h.get('otherMountains') or [])]
    return a, b


def write(path, text):
    assert text.rstrip().endswith('</html>') and text.count('<div') == text.count('</div>'), path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)


SHELL = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="%(robots)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:type" content="article">
<meta property="og:url" content="%(url)s">
<link rel="canonical" href="%(url)s">
%(head)s
%(ld)s
<style>%(css)s</style>
</head>
<body>
<header><div class="hi"><a href="/" class="logo">Yamatch</a><a href="/huts/" class="back">← 山小屋まとめ</a></div></header>
<main>
%(body)s
</main>
%(footer)s
</body>
</html>
"""

# ---------- 一覧ページ ----------
n_start = sum(1 for x in info.values() if x['start'])
n_none = [by_id[k]['name'] for k, x in info.items() if x['none']]
n_web = sum(1 for x in info.values() if x['methods'] and any(re.search(r'Web|LINE|ネット', m) for m in x['methods']))
n_tel_only = sum(1 for x in info.values() if x['methods'] and all('電話' in m for m in x['methods']))
n_req = sum(1 for h in H if h['bookingRequired'])
n_year = sum(1 for h in H if '通年' in (info[h['id']]['season'] or ''))


def example(name):
    h = next((x for x in H if x['name'] == name), None)
    v = info[h['id']]['start'] if h else None
    return '%sは「%s」' % (name, v) if v else None


ex_rel = [e for e in (example('槍ヶ岳山荘'), example('雲取山荘')) if e]
ex_fix = [e for e in (example('燕山荘'), example('白山室堂')) if e]
MAIN_FAQ = [
    ('山小屋の予約はいつから始まりますか？',
     '山小屋によって違い、大きく2つの決め方があります。1つは「宿泊日の◯か月前・◯日前から」という決め方' + ('（例：' + '、'.join(ex_rel) + '）' if ex_rel else '')
     + '、もう1つは「毎年決まった日にシーズン分をまとめて受け付ける」決め方です' + ('（例：' + '、'.join(ex_fix) + '）' if ex_fix else '')
     + '。このページでは%d軒のうち、予約の開始が確認できた%d軒の日付・ルールを載せています。' % (len(H), n_start)),
    ('予約なしで泊まれる山小屋はありますか？',
     '掲載している%d軒のうち、予約の受付がない小屋（避難小屋など）は%d軒です（%s）。一方、出典に「予約必須」「完全予約制」と書かれている小屋は%d軒あります。それ以外の小屋も、定員や食事の準備があるため事前の予約が基本です。'
     % (len(H), len(n_none), '、'.join(n_none), n_req)),
    ('Web（インターネット）で予約できる山小屋はどれくらいありますか？',
     '予約方法が確認できた小屋のうち、Web・予約サイト・LINEなどオンラインで予約できる小屋は%d軒、電話だけで受け付けている小屋は%d軒です。各小屋のカードの「予約方法」で確認できます。' % (n_web, n_tel_only)),
    ('山小屋の営業期間はどこで確認できますか？',
     '各小屋のカードに%d年の営業期間を載せています。通年営業の小屋は%d軒です。営業期間は残雪や天候で変わることがあるので、出発前に各山小屋の公式サイトで確認してください。' % (YEAR, n_year)),
]
main_ld = ld(
    crumbs([('Yamatch', '/'), ('山小屋まとめ', '/huts/')]),
    {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': '山小屋の予約開始日・予約方法まとめ（%d年）' % YEAR, 'url': BASE + '/huts/',
     'dateModified': VERIFIED, 'inLanguage': 'ja',
     'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(H), 'itemListElement': [
         {'@type': 'ListItem', 'position': i + 1, 'url': BASE + '/huts/%s/' % h['id'], 'name': h['name']} for i, h in enumerate(H)]}},
    faq_ld(MAIN_FAQ))
page = (page.replace('__N__', str(len(H))).replace('__YEAR__', str(YEAR)).replace('__UPD__', upd)
        .replace('__HEADCOMMON__', HEADCOMMON).replace('__LD__', main_ld).replace('__FAQ__', faq_html(MAIN_FAQ)).replace('__FOOTER__', FOOTER)
        .replace('__VERIFIED_JA__', VERIFIED_JA).replace('__VERIFIED__', VERIFIED)
        .replace('__CHIPS__', chips).replace('__MTS__', ''.join(mt_btns)).replace('__CARDS__', '\n'.join(cards)))
write(os.path.join(ROOT, 'huts', 'index.html'), page)
print('huts/index.html', len(H), '軒／山', len(mt_btns))

# ---------- 山ごとのページ /huts/<山ID>/ ----------
made = set()
for m in ML:
    mid = m['id']
    if mid not in count:
        continue
    a, b = huts_of(mid)
    hs = a + b
    names = '・'.join(h['name'] for h in hs[:3]) + ('など' if len(hs) > 3 else '')
    title = '%sの山小屋%d軒｜予約開始日・予約方法・営業期間【%d年】| Yamatch' % (m['name'], len(hs), YEAR)
    desc = '%s（標高%sm）の登山で使える山小屋%d軒（%s）の、%d年の予約開始日・予約方法・定員・営業期間を一覧で比較できます。各山小屋の公式サイトへのリンク付き。' % (
        m['name'], '{:,}'.format(m['elevation']), len(hs), names, YEAR)
    rows = []
    for h in hs:
        x = info[h['id']]
        st = '予約不要' if x['none'] else (E(x['start']) if x['start'] else '公式サイトで確認')
        rows.append('<tr><td><a href="#%s">%s</a></td><td>%s</td><td>%s</td></tr>' % (
            E(h['id']), E(h['name']), st, '予約なし' if x['none'] else E(methods_text(x['methods']) or '公式サイトで確認')))
    lead = '%s（%s・標高%sm）で使える山小屋は%d軒です。' % (E(m['name']), E(m.get('area') or ''), '{:,}'.format(m['elevation']), len(hs))
    if a and b:
        lead += '当サイトで紹介しているルートの登山口・途中・山頂にある小屋が%d軒、別のルートや縦走で使う小屋が%d軒あります。' % (len(a), len(b))
    # 関連：同じ小屋を使う山
    rel = []
    for h in hs:
        for i in h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]:
            if i != mid and i not in rel:
                rel.append(i)
    rel_html = ''.join('<a class="mb" href="/huts/%s/">%sの山小屋<span>%d</span></a>' % (E(i), E(M[i]['name']), count[i]) for i in rel[:12])
    body = (
        '<nav class="bc" aria-label="パンくず"><a href="/">Yamatch</a> › <a href="/huts/">山小屋まとめ</a> › %s</nav>\n' % E(m['name'])
        + '<h1>%sの山小屋（%d軒）｜予約開始日・予約方法</h1>\n' % (E(m['name']), len(hs))
        + '<p class="lead">%s予約がいつから始まるか、予約方法、定員、%d年の営業期間をまとめました。</p>\n' % (lead, YEAR)
        + '<p class="upd">最終確認：<time datetime="%s">%s</time>　<a href="/mountains/%s/" style="color:#4e6535">%sの登山情報（アクセス・コース）を見る →</a></p>\n' % (VERIFIED, VERIFIED_JA, E(mid), E(m['name']))
        + '<table class="cmp"><thead><tr><th>山小屋</th><th>予約の開始</th><th>予約方法</th></tr></thead><tbody>%s</tbody></table>\n' % ''.join(rows)
        + '<div id="list">\n%s\n</div>\n' % '\n'.join(card_of[h['id']] for h in hs)
        + ('<h2 class="sec">近くの山・同じ山小屋を使う山</h2>\n<div class="rel">%s</div>\n' % rel_html if rel_html else '')
        + '<p class="src">営業期間や予約の受付は変わることがあります。予約の前に、必ず各山小屋の公式サイトで確認してください。出典は<a href="/huts/">山小屋まとめ</a>のページにまとめています。</p>')
    write(os.path.join(ROOT, 'huts', mid, 'index.html'), SHELL % {
        'title': E(title), 'desc': E(desc), 'robots': 'index,follow,max-snippet:-1,max-image-preview:large', 'url': BASE + '/huts/%s/' % mid,
        'head': HEADCOMMON, 'css': CSS, 'body': body, 'footer': FOOTER,
        'ld': ld(crumbs([('Yamatch', '/'), ('山小屋まとめ', '/huts/'), (m['name'] + 'の山小屋', '/huts/%s/' % mid)]),
                 {'@context': 'https://schema.org', '@type': 'ItemList', 'name': '%sの山小屋' % m['name'], 'numberOfItems': len(hs),
                  'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'item': lodging(h)} for i, h in enumerate(hs)]})})
    made.add(mid)

# ---------- 山小屋ごとのページ /huts/<小屋ID>/ ----------
noindex = 0
for h in H:
    x = info[h['id']]
    name = h['name']
    mts = [M[i]['name'] for i in h['mountainIds']] + [M[o['id']]['name'] for o in h.get('otherMountains') or []]
    mts_txt = '・'.join(mts[:3])
    s_main, s_sub = split_note(x['start']) if x['start'] else (None, None)
    mt_txt = methods_text(x['methods'])
    # タイトル：答え（予約の開始）を先に見せる
    if x['none']:
        title = '%sは予約不要｜営業期間・定員・利用方法【%d年】| Yamatch' % (name, YEAR)
    elif s_main and len(s_main) <= 24:
        title = '%sの予約はいつから？%s【%d年】予約方法・営業期間 | Yamatch' % (name, s_main, YEAR)
    elif s_main:
        title = '%sの予約はいつから？予約開始日・予約方法・営業期間【%d年】| Yamatch' % (name, YEAR)
    else:
        title = '%sの予約方法・営業期間・定員【%d年】| Yamatch' % (name, YEAR)
    if len(title) > 48:
        # 長い名前・長い答えのときは、後ろの決まり文句を落として答えが切れないようにする
        title = title.replace('予約方法・営業期間 | Yamatch', '| Yamatch')
    parts = []
    if x['none']:
        parts.append('%s（%s）は予約の受付がない小屋です。%s' % (name, mts_txt, x['none'].rstrip('。') + '。'))
    else:
        if x['start']:
            parts.append('%s（%s）の予約は、%s。' % (name, mts_txt, x['start']))
        else:
            parts.append('%s（%s）の予約情報。' % (name, mts_txt))
        if mt_txt:
            parts.append('予約方法は%s。' % mt_txt)
    if x['season'] and x['season'] != '—':
        parts.append('営業期間は%s。' % x['season'])
    if x['cap']:
        parts.append('定員は%s%s人。' % ('' if x['capExact'] else '約', x['cap']))
    desc = ''.join(parts)
    desc = desc if len(desc) <= 150 else desc[:149] + '…'
    qa = []
    if x['none']:
        qa.append(('%sは予約が必要ですか？' % name, '予約は不要です。%s' % x['none']))
    elif x['start']:
        qa.append(('%sの予約はいつからできますか？' % name, '%s。最新の受付状況は公式サイトで確認してください。' % x['start']))
    if mt_txt:
        qa.append(('%sの予約方法は？' % name, '%sで受け付けています。%s' % (mt_txt, '予約は必須です。' if h['bookingRequired'] else '')))
    if x['season'] and x['season'] != '—':
        qa.append(('%sの営業期間は？' % name, '%s（%d年シーズンの情報）。天候や残雪で変わることがあります。' % (x['season'], YEAR)))
    thin = not (x['none'] or x['start'] or mt_txt)
    noindex += thin
    if x['none']:
        ans = '<div class="fv" style="font-size:20px">予約不要</div><div class="fs">%s</div>' % E(x['none'])
    elif s_main:
        ans = '<div class="fv" style="font-size:18px">%s</div>%s' % (E(s_main), ('<div class="fs">%s</div>' % E(s_sub)) if s_sub else '')
    else:
        ans = '<div class="fv"><span class="na">予約の開始時期は確認できていません。公式サイトで確認してください</span></div>'
    sib = []
    for i in h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]:
        for o in sum(huts_of(i), []):
            if o['id'] != h['id'] and o not in sib:
                sib.append(o)
    own = card_of[h['id']].replace('<h2><a href="/huts/%s/">%s</a></h2>' % (E(h['id']), E(name)), '<h2>%s</h2>' % E(name))
    body = (
        '<nav class="bc" aria-label="パンくず"><a href="/">Yamatch</a> › <a href="/huts/">山小屋まとめ</a>%s › %s</nav>\n' % (
            (' › <a href="/huts/%s/">%sの山小屋</a>' % (E(h['mountainIds'][0]), E(M[h['mountainIds'][0]]['name']))) if h['mountainIds'] else '', E(name))
        + '<h1>%s｜%s（%d年）</h1>\n' % (E(name), '予約不要・利用方法' if x['none'] else '予約開始日・予約方法', YEAR)
        + '<div class="fact" style="background:#e9efe0;margin-bottom:12px"><div class="fl">%s</div>%s</div>\n' % ('予約' if x['none'] else '予約はいつから？', ans)
        + '<p class="upd">最終確認：<time datetime="%s">%s</time></p>\n' % (h.get('lastVerified') or VERIFIED, VERIFIED_JA)
        + '<div id="list">\n%s\n</div>\n' % own
        + '<h2 class="sec">この山小屋を使う山</h2>\n<div class="rel">%s</div>\n' % ''.join(
            '<a class="mb" href="/huts/%s/">%sの山小屋<span>%d</span></a>' % (E(i), E(M[i]['name']), count[i])
            for i in h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []])
        + ('<h2 class="sec">同じ山のほかの山小屋</h2>\n<div class="rel">%s</div>\n' % ''.join(
            '<a class="mb" href="/huts/%s/">%s</a>' % (E(o['id']), E(o['name'])) for o in sib[:16]) if sib else '')
        + ('<h2 class="sec">よくある質問</h2>\n<dl>\n%s\n</dl>\n' % faq_html(qa) if qa else '')
        + '<p class="src">営業期間や予約の受付は変わることがあります。予約の前に、必ず公式サイトで確認してください。出典は<a href="/huts/">山小屋まとめ</a>のページにまとめています。</p>')
    lds = [crumbs([('Yamatch', '/'), ('山小屋まとめ', '/huts/')]
                  + ([(M[h['mountainIds'][0]]['name'] + 'の山小屋', '/huts/%s/' % h['mountainIds'][0])] if h['mountainIds'] else [])
                  + [(name, '/huts/%s/' % h['id'])]),
           dict({'@context': 'https://schema.org'}, **lodging(h))]
    if qa:
        lds.append(faq_ld(qa))
    write(os.path.join(ROOT, 'huts', h['id'], 'index.html'), SHELL % {
        'title': E(title), 'desc': E(desc), 'robots': 'noindex,follow' if thin else 'index,follow,max-snippet:-1,max-image-preview:large',
        'url': BASE + '/huts/%s/' % h['id'], 'head': HEADCOMMON, 'css': CSS, 'body': body, 'footer': FOOTER, 'ld': ld(*lds)})
    if not thin:
        made.add(h['id'])
    else:
        made.add('!' + h['id'])
# 無くなった山・小屋のページを消す（このスクリプトが作った huts/<ID>/index.html だけ）
keep = set(x.lstrip('!') for x in made)
for name in os.listdir(os.path.join(ROOT, 'huts')):
    dp = os.path.join(ROOT, 'huts', name)
    if os.path.isdir(dp) and name not in keep and os.listdir(dp) == ['index.html']:
        os.remove(os.path.join(dp, 'index.html'))
        os.rmdir(dp)
# サイトマップ：/huts/ 以下を入れ直す（検索に出さないページは入れない）
sp = os.path.join(ROOT, 'sitemap.xml')
sm = open(sp, encoding='utf-8').read()
sm, n_old = re.subn(r'<url><loc>https://tozan-navi\.com/huts/[^<]*</loc>.*?</url>\n?', '', sm, flags=re.S)
urls = ['<url><loc>%s/huts/</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>' % (BASE, VERIFIED)]
urls += ['<url><loc>%s/huts/%s/</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>%s</priority></url>' % (
    BASE, k, VERIFIED, '0.7' if k in M else '0.6') for k in sorted(x for x in made if not x.startswith('!'))]
assert sm.count('</urlset>') == 1
open(sp, 'w', encoding='utf-8').write(sm.replace('</urlset>', '\n'.join(urls) + '\n</urlset>'))
print('山ごと %d ページ／山小屋ごと %d ページ（うち検索に出さない %d）／sitemap %d 件' % (len(count), len(H), noindex, len(urls)))
