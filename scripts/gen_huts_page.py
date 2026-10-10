#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋まとめ（β）ページ huts/index.html を data/huts.json から作る。使い方：python3 scripts/gen_huts_page.py
画面は2つの見方を切り替える：「山から探す」（山を選ぶと、その山の小屋だけ出る。/huts/?m=山ID でも開ける）と「一覧」（山域・名前で絞り込み）。"""
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
    m = re.match(r'^([^（]{2,})（(.+)）$', text or '')
    return (m.group(1), m.group(2)) if m else (text, None)


def fact(label, main, sub=None, cls=''):
    return '<div class="fact %s"><div class="fl">%s</div><div class="fv">%s</div>%s</div>' % (
        cls, label, main, ('<div class="fs">%s</div>' % sub) if sub else '')


regions = []
for h in H:
    if h['region'] not in regions:
        regions.append(h['region'])
cards = []
count = {}
for h in H:
    au = h.get('auto') or {}
    stale = h.get('bookingStale')
    # 公式サイト・予約サイトから自動で読み取れた値を優先する
    start = (au.get('bookingStart') or {}).get('value') or (None if stale else h.get('bookingStart'))
    cap = (au.get('capacity') or {}).get('value') or h.get('capacity')
    methods = None if stale else h.get('bookingMethods')
    ids = h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]
    for i in ids:
        count[i] = count.get(i, 0) + 1
    # 予約の開始
    if start:
        a, b = split_note(start)
        s_html = fact('予約の開始', E(a), E(b))
        if h.get('officialChanged') and not au.get('bookingStart'):
            s_html = fact('予約の開始', E(a), E((b + '。' if b else '') + '公式サイトの記載に変更あり。最新は公式サイトで確認'))
    elif stale:
        s_html = fact('予約の開始', '<span class="na">確認中</span>', '出典の記載が変わりました')
    else:
        s_html = fact('予約の開始', NA)
    # 予約方法
    if methods:
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
        '<article class="hut" data-region="%s" data-m="%s" data-key="%s">\n'
        '  <div class="hh"><h2>%s</h2><span class="rg">%s</span>%s</div>\n'
        '  <div class="facts">%s%s%s</div>\n'
        '  <div class="season"><span class="sl">営業期間</span><span class="sv">%s</span>%s</div>\n'
        '  <div class="mrow"><span class="sl">対応する山</span><span class="mcs">%s%s</span></div>\n'
        '  <div class="foot">%s%s</div>\n'
        '</article>' % (
            E(h['region']), E(' '.join(ids)), E(h['name'] + ' ' + ' '.join(M[i]['name'] for i in ids)),
            E(h['name']), E(h['region']), '<span class="req">予約必須</span>' if h['bookingRequired'] else '',
            s_html, m_html, c_html, E(season_main), ('<span class="ss">%s</span>' % E(season_sub)) if season_sub else '',
            mts, oth, ''.join(links),
            ('<details><summary>くわしく</summary>%s</details>' % ''.join(detail)) if detail else ''))
# 「山から探す」：小屋のある山を、県・山域の順に並べる
mt_btns = []
for m in ML:
    if m['id'] in count:
        mt_btns.append('<button class="mb" data-m="%s" data-name="%s">%s<span>%d</span></button>' % (E(m['id']), E(m['name']), E(m['name']), count[m['id']]))
chips = '<button class="chip on" data-r="">すべて</button>' + ''.join('<button class="chip" data-r="%s">%s</button>' % (E(r), E(r)) for r in regions)
_u = sorted(h['sourceUpdated'] for h in H if h.get('sourceUpdated'))
upd = '%d年%d〜%d月' % (int(_u[0][:4]), int(_u[0][5:7]), int(_u[-1][5:7])) if _u else ''
page = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>山小屋まとめ（β）｜予約の開始・予約方法・営業期間 | Yamatch</title>
<meta name="description" content="北アルプス・南アルプス・八ヶ岳・富士山などの山小屋__N__軒の、予約の開始時期・予約方法・規模・営業期間をまとめた一覧（β版）。登る山から山小屋を探せます。">
<meta property="og:title" content="山小屋まとめ（β）| Yamatch">
<meta property="og:description" content="山小屋__N__軒の予約の開始時期・予約方法・規模・営業期間の一覧（β版）。山から探せます。">
<meta property="og:type" content="website">
<meta property="og:url" content="https://tozan-navi.com/huts/">
<link rel="canonical" href="https://tozan-navi.com/huts/">
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
.mb{border:1px solid #c8c2b8;background:#fff;border-radius:8px;padding:7px 10px;font-size:13.5px;cursor:pointer;color:#2f2b26;display:flex;align-items:center;gap:6px}
.mb span{font-size:11px;background:#e9efe0;color:#4e6535;border-radius:999px;padding:0 6px;font-weight:700}
.mb.on{background:#4e6535;color:#fff;border-color:#4e6535}.mb.on span{background:rgba(255,255,255,.25);color:#fff}
#picked{display:none;background:#e9efe0;border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:14px;font-weight:700;color:#2a3820;align-items:center;gap:10px;flex-wrap:wrap}
#picked a{font-size:12px;font-weight:400;color:#4e6535}
#picked button{margin-left:auto;border:none;background:#fff;border-radius:999px;padding:4px 12px;font-size:12px;cursor:pointer;color:#4e6535}
#cnt{font-size:12px;color:#7a7068;margin-bottom:8px}
.hut{background:#fff;border:1px solid #e0dbd4;border-radius:12px;padding:14px;margin-bottom:12px}
.hh{display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;margin-bottom:10px}
.hh h2{font-size:17px;font-weight:800;color:#2a3820}
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
@media(max-width:560px){.facts{grid-template-columns:1fr 1fr}.facts .fact:first-child{grid-column:1/-1}}
</style>
</head>
<body>
<header><div class="hi"><a href="/" class="logo">Yamatch</a><a href="/" class="back">← 山を検索する</a></div></header>
<main>
<h1>山小屋まとめ<span class="beta">β版</span></h1>
<p class="sub">__N__軒の、予約の開始・予約方法・規模・営業期間（__YEAR__年シーズン）</p>
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
<div id="picked"><span id="pname"></span><a id="plink" href="#">山のページを見る →</a><button id="pclear">選び直す</button></div>
<div id="cnt"></div>
<div id="list">
__CARDS__
</div>
<p class="src">出典：<a href="https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/sotaikyo/yamagoya/yamagoya.html" target="_blank" rel="noopener">長野県 山小屋情報ポータルサイト</a>（__UPD__更新分）／山と溪谷オンライン <a href="https://www.yamakei-online.com/yama-ya/detail.php?id=2535" target="_blank" rel="noopener">北アルプス山小屋リスト2026</a>・<a href="https://www.yamakei-online.com/yama-ya/detail.php?id=2556" target="_blank" rel="noopener">中央・南アルプス山小屋リスト2026</a>・山小屋情報の各ページ／予約サイト「やまたん」／各山小屋の公式サイト</p>
</main>
<script>
(function(){
  var view='mt', region='', mt='', huts=document.querySelectorAll('.hut');
  var q=document.getElementById('q'), mq=document.getElementById('mq'), cnt=document.getElementById('cnt');
  var picked=document.getElementById('picked'), list=document.getElementById('list'), mgrid=document.getElementById('mgrid');
  function apply(){
    var k=q.value.replace(/\\s+/g,''), n=0, i, h, ok;
    for(i=0;i<huts.length;i++){
      h=huts[i];
      if(view==='mt'){ ok = mt && (' '+h.getAttribute('data-m')+' ').indexOf(' '+mt+' ')>-1; }
      else { ok=(!region||h.getAttribute('data-region')===region)&&(!k||h.getAttribute('data-key').indexOf(k)>-1); }
      h.style.display=ok?'':'none'; if(ok)n++;
    }
    list.style.display=(view==='mt'&&!mt)?'none':'';
    mgrid.style.display=(view==='mt'&&mt)?'none':'';
    mq.style.display=(view==='mt'&&mt)?'none':'';
    picked.style.display=(view==='mt'&&mt)?'flex':'none';
    cnt.textContent=(view==='mt'&&!mt)?'山を選ぶと、その山の山小屋を表示します':n+'軒を表示';
  }
  function pick(id,name){
    mt=id;
    if(id){ document.getElementById('pname').textContent=name+'の山小屋'; document.getElementById('plink').href='/mountains/'+id+'/'; }
    try{ history.replaceState(null,'',id?('?m='+id):location.pathname); }catch(e){}
    apply(); if(id) window.scrollTo(0,0);
  }
  var mbs=document.querySelectorAll('.mb'), i;
  for(i=0;i<mbs.length;i++){ mbs[i].addEventListener('click',function(){ pick(this.getAttribute('data-m'),this.getAttribute('data-name')); }); }
  document.getElementById('pclear').addEventListener('click',function(){ pick('',''); });
  mq.addEventListener('input',function(){ var k=mq.value.replace(/\\s+/g,''); for(var j=0;j<mbs.length;j++){ mbs[j].style.display=(!k||mbs[j].getAttribute('data-name').indexOf(k)>-1)?'':'none'; } });
  q.addEventListener('input',apply);
  var chips=document.querySelectorAll('.chip');
  for(i=0;i<chips.length;i++){ chips[i].addEventListener('click',function(){ for(var j=0;j<chips.length;j++)chips[j].className='chip'; this.className='chip on'; region=this.getAttribute('data-r'); apply(); }); }
  var tabs=document.querySelectorAll('.tab');
  for(i=0;i<tabs.length;i++){ tabs[i].addEventListener('click',function(){ for(var j=0;j<tabs.length;j++)tabs[j].className='tab'; this.className='tab on'; view=this.getAttribute('data-v'); document.getElementById('v-mt').style.display=view==='mt'?'':'none'; document.getElementById('v-all').style.display=view==='all'?'':'none'; apply(); }); }
  // /huts/?m=山ID で、その山の山小屋を直接開く
  var m0=(location.search.match(/[?&]m=([a-z0-9_]+)/)||[])[1];
  if(m0){ for(i=0;i<mbs.length;i++){ if(mbs[i].getAttribute('data-m')===m0){ pick(m0,mbs[i].getAttribute('data-name')); } } }
  apply();
})();
</script>
</body>
</html>
'''
page = (page.replace('__N__', str(len(H))).replace('__YEAR__', str(d['seasonYear'])).replace('__UPD__', upd)
        .replace('__CHIPS__', chips).replace('__MTS__', ''.join(mt_btns)).replace('__CARDS__', '\n'.join(cards)))
os.makedirs(os.path.join(ROOT, 'huts'), exist_ok=True)
open(os.path.join(ROOT, 'huts', 'index.html'), 'w', encoding='utf-8').write(page)
print('huts/index.html', len(H), '軒／山', len(mt_btns))
