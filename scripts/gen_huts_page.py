#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山小屋まとめ（β）ページ huts/index.html を data/huts.json から作る。使い方：python3 scripts/gen_huts_page.py"""
import html, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = lambda s: html.escape(str(s or ''), quote=True)
d = json.load(open(os.path.join(ROOT, 'data', 'huts.json'), encoding='utf-8'))
M = {m['id']: m['name'] for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
H = d['huts']
regions = []
for h in H:
    if h['region'] not in regions:
        regions.append(h['region'])
cards = []
for h in H:
    mts = '、'.join('<a href="/mountains/%s/">%s</a>' % (E(i), E(M[i])) for i in h['mountainIds'])
    # 別のルート・縦走で使う山は、関係を添えて分けて出す
    oth = '、'.join('<a href="/mountains/%s/">%s</a><span class="rel">（%s）</span>' % (E(o['id']), E(M[o['id']]), E(o['relation'])) for o in h.get('otherMountains') or [])
    if oth:
        mts = (mts + '<br>' if mts else '') + '<span class="rel-h">別ルート・縦走：</span>' + oth
    name = '<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(h['officialUrl']), E(h['name'])) if h['officialUrl'] else E(h['name'])
    au = h.get('auto') or {}
    stale = h.get('bookingStale')
    # 公式サイト・予約サイトから自動で読み取れた値があれば、それを優先する
    if au.get('bookingStart'):
        h = dict(h, bookingStart=au['bookingStart']['value'], officialChanged=None)
        stale = False
    if au.get('capacity'):
        h = dict(h, capacity=au['capacity']['value'])
    start = E(h['bookingStart']) if (h['bookingStart'] and not stale) else '<span class="na">公式サイトで確認</span>'
    meth = E('・'.join(h['bookingMethods'])) if (h['bookingMethods'] and not stale) else '<span class="na">公式サイトで確認</span>'
    if stale:
        start = '<span class="na">出典の記載が変わったため確認中（下の原文を見てください）</span>'
    elif h.get('officialChanged') and h['bookingStart']:
        start += '<br><span class="rel">公式サイトの予約の記載に変更あり（%s に検知）。最新は公式サイトで確認</span>' % E(h['officialChanged'])
    # 規模：公式サイト・予約サイトで確認できた定員を優先。無ければ山と溪谷オンラインの山小屋情報の収容人数を参考として出す
    ref = h.get('capacityRef')
    ref_txt = ('%s人' % ref) if isinstance(ref, int) else (E(ref) if ref else '')
    if h.get('capacity'):
        cap = E(h['capacity']) + '人'
        if isinstance(ref, int) and ref != h['capacity']:
            cap += '<span class="rel">（公式・予約サイトの定員。山と溪谷オンラインの記載は%s）</span>' % ref_txt
    elif ref_txt:
        cap = ref_txt + '<span class="rel">（山と溪谷オンラインの記載。現在の定員は公式サイトで確認）</span>'
    else:
        cap = '<span class="na">確認中</span>'
    raw = E(h.get('openText')) or '—'
    if au.get('season'):
        raw = '<span class="rel">公式・予約サイト：</span>' + E(au['season']['value']) + '<br><span class="rel">一覧の出典：</span>' + raw
    if h.get('officialNote'):
        raw += '<br><span class="rel">公式サイトの記載：' + E(h['officialNote']) + '</span>'
    key = E(h['name'] + ' ' + ' '.join(M[i] for i in h['mountainIds'] + [o['id'] for o in h.get('otherMountains') or []]))
    cards.append(
        '<div class="hut" data-region="%s" data-key="%s">\n'
        '  <div class="hut-name">%s%s</div>\n'
        '  <div class="hut-sub">%s%s</div>\n'
        '  <dl><dt>対応する山</dt><dd>%s</dd><dt>予約の開始</dt><dd>%s</dd><dt>予約方法</dt><dd>%s</dd><dt>規模</dt><dd>%s</dd>'
        '<dt>営業・予約<br>（出典の記載）</dt><dd>%s</dd><dt>電話</dt><dd>%s</dd></dl>\n'
        '</div>' % (E(h['region']), key, name, '<span class="req">予約必須</span>' if h['bookingRequired'] else '',
                    E(h['region']), (' ／ ' + E(h['location'])) if h.get('location') else '', mts, start, meth, cap, raw, E(h.get('tel')) or '—'))
chips = '<button class="chip on" data-r="">すべて</button>' + ''.join('<button class="chip" data-r="%s">%s</button>' % (E(r), E(r)) for r in regions)
_u = sorted(h['sourceUpdated'] for h in H if h['sourceUpdated'])
upd = '%d年%d月〜%d月' % (int(_u[0][:4]), int(_u[0][5:7]), int(_u[-1][5:7])) if _u[0][5:7] != _u[-1][5:7] else '%d年%d月' % (int(_u[0][:4]), int(_u[0][5:7]))
page = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>山小屋まとめ（β）｜予約の開始・予約方法・営業期間 | Yamatch</title>
<meta name="description" content="北アルプス・南アルプス・中央アルプス・八ヶ岳などの山小屋__N__軒の、予約の開始時期・予約方法・営業期間をまとめた一覧（β版）。対応する山のページへもリンク。">
<meta property="og:title" content="山小屋まとめ（β）| Yamatch">
<meta property="og:description" content="山小屋__N__軒の予約の開始時期・予約方法・営業期間の一覧（β版）。">
<meta property="og:type" content="website">
<meta property="og:url" content="https://tozan-navi.com/huts/">
<link rel="canonical" href="https://tozan-navi.com/huts/">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Zen Kaku Gothic New',-apple-system,BlinkMacSystemFont,'Hiragino Sans',sans-serif;background:#f0ede5;color:#3a3530}
header{background:#4e6535;padding:14px 16px}
.hi{max-width:720px;margin:0 auto;display:flex;align-items:center}
.logo{color:#fff;font-size:20px;font-weight:800;text-decoration:none}
.back{margin-left:auto;color:rgba(255,255,255,.85);font-size:12px;text-decoration:none;background:rgba(255,255,255,.15);padding:5px 12px;border-radius:20px}
main{max-width:720px;margin:0 auto;padding:16px}
h1{font-size:22px;font-weight:800;color:#2a3820;margin-bottom:8px}
.beta{font-size:11px;background:#c8d4b8;color:#2a3820;border-radius:4px;padding:2px 7px;margin-left:6px;vertical-align:middle}
.lead{font-size:13px;line-height:1.8;color:#4a4540;background:#fff;border:1px solid #e0dbd4;border-radius:12px;padding:14px;margin-bottom:12px}
.lead li{margin-left:18px}
#q{width:100%;padding:10px 12px;border:1px solid #d0cbc2;border-radius:10px;font-size:14px;margin-bottom:8px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.chip{border:1px solid #c8c2b8;background:#fff;border-radius:999px;padding:5px 12px;font-size:12px;cursor:pointer;color:#3a3530}
.chip.on{background:#4e6535;color:#fff;border-color:#4e6535}
.hut{background:#fff;border:1px solid #e0dbd4;border-radius:12px;padding:14px;margin-bottom:10px}
.hut-name{font-size:16px;font-weight:800}.hut-name a{color:#2a3820}
.req{font-size:10px;font-weight:700;background:#f8f0e0;color:#7a6020;border-radius:4px;padding:2px 6px;margin-left:8px}
.hut-sub{font-size:11px;color:#8a8078;margin:3px 0 8px}
dl{display:grid;grid-template-columns:8.5em 1fr;gap:4px 10px;font-size:13px;line-height:1.6}
dt{color:#7a7068;font-size:11.5px;padding-top:2px}dd a{color:#4e6535}
.na{color:#a09888;font-size:12px}
.rel{color:#7a7068;font-size:11.5px}.rel-h{color:#7a7068;font-size:11.5px}
#cnt{font-size:12px;color:#7a7068;margin-bottom:8px}
</style>
</head>
<body>
<header><div class="hi"><a href="/" class="logo">Yamatch</a><a href="/" class="back">← 山を検索する</a></div></header>
<main>
<h1>山小屋まとめ<span class="beta">β版</span></h1>
<div class="lead">
<ul>
<li>__YEAR__年シーズンの情報です。山小屋__N__軒を載せています。出典は、長野県「山小屋情報ポータルサイト」（__UPD__ 更新分）、山と溪谷オンライン「山小屋リスト2026」、各山小屋の公式サイトです。</li>
<li>「対応する山」は、当サイトで紹介しているルートの登山口・途中・山頂にある小屋です。別のルートや縦走で使う小屋は「別ルート・縦走」として分けています。</li>
<li>「予約の開始」「予約方法」は、出典に書かれているものだけを載せています。書かれていない小屋は「公式サイトで確認」としています。</li>
<li>規模（収容人数）は、公式サイト・予約サイトで確認できた定員を載せています。確認できなかった小屋は、山と溪谷オンラインの山小屋情報の収容人数を参考として載せています（現在は定員を減らしている小屋があります）。富士山・白山・上信越・尾瀬・東北の山小屋は、営業期間が「例年」の値です。今年の日程と予約は公式サイトで確認してください。</li>
<li>営業期間や予約の受付は変わることがあります。予約の前に、必ず各山小屋の公式サイトで確認してください。</li>
</ul>
</div>
<input id="q" type="search" placeholder="山小屋名・山名でさがす（例：槍ヶ岳、涸沢）">
<div class="chips">__CHIPS__</div>
<div id="cnt"></div>
__CARDS__
<p class="lead" style="margin-top:12px">出典：<a href="https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/sotaikyo/yamagoya/yamagoya.html" target="_blank" rel="noopener">長野県 山小屋情報ポータルサイト</a>／<a href="https://www.yamakei-online.com/yama-ya/detail.php?id=2535" target="_blank" rel="noopener">山と溪谷オンライン 北アルプス山小屋リスト2026</a>／<a href="https://www.yamakei-online.com/yama-ya/detail.php?id=2556" target="_blank" rel="noopener">同 中央・南アルプス山小屋リスト2026</a>／各山小屋の公式サイト</p>
</main>
<script>
(function(){
  var q=document.getElementById('q'), region='', huts=document.querySelectorAll('.hut'), cnt=document.getElementById('cnt');
  function apply(){
    var k=q.value.replace(/\\s+/g,''), n=0;
    for(var i=0;i<huts.length;i++){
      var h=huts[i], ok=(!region||h.getAttribute('data-region')===region)&&(!k||h.getAttribute('data-key').indexOf(k)>-1);
      h.style.display=ok?'':'none'; if(ok)n++;
    }
    cnt.textContent=n+'軒を表示';
  }
  q.addEventListener('input',apply);
  var chips=document.querySelectorAll('.chip');
  for(var i=0;i<chips.length;i++){ chips[i].addEventListener('click',function(){ for(var j=0;j<chips.length;j++)chips[j].className='chip'; this.className='chip on'; region=this.getAttribute('data-r'); apply(); }); }
  apply();
})();
</script>
</body>
</html>
'''
page = page.replace('__N__', str(len(H))).replace('__YEAR__', str(d['seasonYear'])).replace('__UPD__', upd).replace('__CHIPS__', chips).replace('__CARDS__', '\n'.join(cards))
os.makedirs(os.path.join(ROOT, 'huts'), exist_ok=True)
open(os.path.join(ROOT, 'huts', 'index.html'), 'w', encoding='utf-8').write(page)
print('huts/index.html', len(H), '軒')
