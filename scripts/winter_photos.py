#!/usr/bin/env python3
"""冬の特集記事（初日の出登山・ダイヤモンド富士・冬の絶景）の山のカードの写真を選ぶツール（2026-11-12。運営者の指示「記事にあった山の写真を選びたい」）

  python3 scripts/winter_photos.py all
      記事ごとの山について、候補を集めて（2回目からは保存した候補を使う。--refresh で集め直す）見比べ用のページ（.claude/winter_photos/index.html）を作る
      S番号＝サイトにあるその山の写真（image-credits.json に記録のあるもの）
      C番号＝Wikimedia Commons で、記事の中身（日の出・富士山・樹氷など）の語で探した写真（商用で使えるライセンスだけ）
  python3 scripts/winter_photos.py apply <記事> <山ID> <S1|C3 など>
      選んだ写真を data/winter_specials.json の photos（記事→山ID）に書く。Commons の写真は
      images/articles/<記事のスラッグ>/<山ID>.webp（長辺1600px）に保存し、作者・ライセンスも書く
  python3 scripts/winter_photos.py apply-text < 選んだ内容.txt
      候補のページの「これにする」で選び「選んだ内容をコピー」した文を、まとめて apply する
  python3 scripts/winter_photos.py clear <記事> <山ID>
      選んだ写真を外す（その山の1枚目の写真に戻る）
記事は hatsuhinode / diamond / views。選ぶのは人（写っている山・景色を Commons のページで確かめてから apply）。
apply のあとは python3 scripts/gen_winter_specials.py
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'winter_specials.json')
WORK = os.path.join(ROOT, '.claude', 'winter_photos')
API = 'https://commons.wikimedia.org/w/api.php'
UA = 'YamatchPhotoTool/1.0 (https://tozan-navi.com/)'
OK_LICENSE = re.compile(r'^(CC0( 1\.0)?|Public domain|PD|CC BY(-SA)?( [0-9.]+)?( [a-z]{2,3})?)$', re.I)
SLUG = {'hatsuhinode': 'hatsuhinode-hiking', 'diamond': 'diamond-fuji', 'views': 'winter-views'}
TITLE = {'hatsuhinode': '初日の出登山', 'diamond': 'ダイヤモンド富士', 'views': '冬にしか見られない絶景'}

# 山の英語の名前（Commons は英語の題が多い）
EN = {
    'takao': 'Mount Takao', 'mitakesan': 'Mount Mitake', 'hinodesaan': 'Mount Hinode', 'tsukuba': 'Mount Tsukuba',
    'oyama': 'Mount Oyama Kanagawa', 'nokogiriyama_chiba': 'Mount Nokogiri', 'ryugatake': 'Ryugatake',
    'ishiwariyama': 'Mount Ishiwari', 'tonosaki': 'Tonodake', 'nanaitsurasan': 'Mount Shichimen', 'ohnoyama': 'Mount Ono Yamakita',
    'koubousan': 'Kobosan Hadano', 'zaosan': 'Zao', 'azuma': 'Nishi-Azuma', 'kitayokodake': 'Kitayokodake',
    'nyukasayama': 'Nyukasa', 'okutama': 'Daibosatsu', 'akagi': 'Mount Akagi',
}
# 冬の絶景の山は、景色そのものの語で探す
VIEWS_Q = {
    'zaosan': ['蔵王 樹氷', 'Zao snow monsters', 'Zao juhyo'],
    'azuma': ['西吾妻山 樹氷', '天元台 樹氷', 'Nishi-Azuma snow'],
    'kitayokodake': ['北横岳 冬', '北八ヶ岳ロープウェイ 冬', 'Kitayokodake winter'],
    'nyukasayama': ['入笠山 冬', '入笠湿原 雪', 'Nyukasa winter'],
    'okutama': ['大菩薩嶺 冬', '大菩薩 霧氷', 'Daibosatsu winter'],
    'akagi': ['赤城山 冬', '赤城 大沼 結氷', 'Akagi Onuma winter'],
}

BAR = """<div id="bar"><span id="cnt">選んだ写真：0件</span><button type="button" id="copy">選んだ内容をコピー</button><button type="button" id="reset">全部取り消す</button>
<textarea id="out" readonly></textarea></div>
<script>
(function(){
  var KEY='ym_winter_photo_picks_v2', P={};
  try{ P=JSON.parse(localStorage.getItem(KEY)||'{}'); }catch(e){}
  function save(){ try{ localStorage.setItem(KEY, JSON.stringify(P)); }catch(e){} }
  function draw(){
    document.querySelectorAll('.c[data-k]').forEach(function(c){
      var on = P[c.getAttribute('data-k')] === c.getAttribute('data-p');
      c.classList.toggle('on', on);
      c.querySelector('.pick').textContent = on ? '選んだ（押すと取り消し）' : 'これにする';
    });
    document.querySelectorAll('[data-sel]').forEach(function(s){
      var v = P[s.getAttribute('data-sel')]; s.textContent = v ? '→ ' + v + ' を選択' : '';
    });
    document.getElementById('cnt').textContent = '選んだ写真：' + Object.keys(P).length + '件';
  }
  function text(){
    return '冬の特集の写真\\n' + Object.keys(P).map(function(k){ return k + ' ' + P[k]; }).join('\\n');
  }
  document.addEventListener('click', function(e){
    var b = e.target.closest('.pick'); if(!b) return;
    var c = b.closest('.c'), k = c.getAttribute('data-k'), p = c.getAttribute('data-p');
    if(P[k] === p) delete P[k]; else P[k] = p;
    save(); draw();
  });
  document.getElementById('reset').onclick = function(){ if(confirm('選んだ写真をすべて取り消しますか？')){ P={}; save(); draw(); } };
  document.getElementById('copy').onclick = function(){
    var t = text(), o = document.getElementById('out'), btn = this;
    o.value = t;
    function done(){ o.style.display = 'none'; btn.textContent = 'コピーしました。チャットに貼ってください'; setTimeout(function(){ btn.textContent = '選んだ内容をコピー'; }, 3000); }
    function fallback(){
      o.style.display = 'block'; o.focus(); o.select();
      var ok = false; try{ ok = document.execCommand('copy'); }catch(e){}
      if(ok) done(); else btn.textContent = '下の文を選んでコピーしてください';
    }
    if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(t).then(done, fallback); } else { fallback(); }
  };
  draw();
})();
</script>"""


def api(params):
    params = dict(params, format='json')
    req = urllib.request.Request(API + '?' + urllib.parse.urlencode(params), headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def strip_html(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or '')).strip()


def E(s):
    return str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def load():
    return json.load(open(DATA, encoding='utf-8'))


def mountains():
    return {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}


def targets(W):
    return ([('hatsuhinode', x['id']) for x in W['hatsuhinode']['mountains']]
            + [('diamond', x['id']) for x in W['diamond']['include']]
            + [('views', x['id']) for x in W['views']['mountains']])


def queries(art, mid, name):
    base = re.sub(r'（.*?）', '', name)
    en = EN.get(mid, '')
    if art == 'hatsuhinode':
        return [base + ' 日の出', en + ' sunrise', base, en]
    if art == 'diamond':
        return [base + ' 富士山', en + ' Fuji', base, en]
    return VIEWS_Q.get(mid, []) + [base, en]


def site_photos(mid, M):
    cr = {c['localPath']: c for c in (json.load(open(os.path.join(ROOT, 'data', 'image-credits.json'), encoding='utf-8')).get(mid) or [])}
    out = []
    for p in M[mid].get('photos') or []:
        c = cr.get(p)
        if c:
            out.append({'src': p, 'author': c.get('author'), 'license': c.get('license'), 'pageUrl': c.get('commonsPageUrl'),
                        'title': c.get('fileName')})
    return out


# 山の名前（Commons の題・説明・カテゴリーでの書き方）。撮った位置の分からない写真は、この名前がある写真だけ残す
NAMES = {
    'takao': ['高尾山', 'Takao'], 'mitakesan': ['御岳山', '武蔵御嶽', 'Mitake'], 'hinodesaan': ['日の出山', 'Hinode'],
    'tsukuba': ['筑波山', 'Tsukuba'], 'oyama': ['阿夫利', '丹沢大山', 'Afuri', 'Ōyama (Kanagawa', 'Oyama (Kanagawa', 'Mount Ōyama', 'Mount Oyama'],
    'nokogiriyama_chiba': ['鋸山', 'Nokogiri', '日本寺', 'Nihon-ji', 'Nihonji'], 'ryugatake': ['竜ヶ岳', '竜ケ岳', 'Ryugatake', 'Ryūgatake'],
    'ishiwariyama': ['石割山', 'Ishiwari'], 'tonosaki': ['塔ノ岳', '塔ヶ岳', 'Tonodake', 'Tōnodake', 'Tonotake'],
    'nanaitsurasan': ['七面山', 'Shichimen'], 'ohnoyama': ['大野山', 'Ōnoyama', 'Onoyama'], 'koubousan': ['弘法山', 'Kōbōyama', 'Kobosan', 'Kobo-yama'],
    'zaosan': ['蔵王', 'Zaō', 'Zao'], 'azuma': ['西吾妻', '天元台', 'Nishi-Azuma', 'Nishiazuma', 'Tengendai'],
    'kitayokodake': ['北横岳', 'Kitayoko', '北八ヶ岳ロープウェイ'], 'nyukasayama': ['入笠', 'Nyukasa', 'Nyūkasa'],
    'okutama': ['大菩薩嶺', '大菩薩峠', '大菩薩連嶺', 'Daibosatsu'], 'akagi': ['赤城', 'Akagi'],
}
# 同じ名前の別の場所（位置の分からない写真で取り違えやすいもの）
NOT = {'nokogiriyama_chiba': ['奥多摩', 'okutama', '大岳'], 'okutama': ['shinpen', '清荒神', 'bodhisattva', '菩薩像'], 'zaosan': ['権現'], 'mitakesan': ['Ontake', '木曽', '長野県'], 'oyama': ['鳥取', 'Daisen', 'Tottori'], 'akagi': ['赤城神社 (新宿']}
# 名前だけでは別の場所と取り違える山は、撮った位置の分からない写真に、この地名のどれかも書いてあることを求める
REGION = {
    'ryugatake': ['本栖', 'motosu', '山梨', 'yamanashi', '富士河口湖', 'fujikawaguchiko', '端足'],
    'nanaitsurasan': ['身延', 'minobu', '早川', 'hayakawa', '山梨', 'yamanashi', '敬慎院', 'keishin', '羽衣', '赤沢', 'akasawa'],
    'ohnoyama': ['山北', 'yamakita', '神奈川', 'kanagawa', '丹沢', 'tanzawa'],
    'koubousan': ['秦野', 'hadano', '神奈川', 'kanagawa'],
    'zaosan': ['山形', 'yamagata', '宮城', 'miyagi', '樹氷', 'juhyo', '熊野岳', 'kumano', '刈田', 'katta', 'okama', 'お釜'],
    'okutama': ['峠', 'toge', 'touge', 'pass', '嶺', 'rei', '甲州', 'koshu', '山梨', 'yamanashi', 'kurodake', 'takigo'],
    'akagi': ['群馬', 'gunma', '大沼', 'onuma', '黒檜', 'kurobi', '覚満', 'kakuman'],
    'nokogiriyama_chiba': ['千葉', 'chiba', '富津', 'futtsu', '鋸南', 'kyonan', '金谷', 'kanaya', '日本寺', 'nihon-ji', 'nihonji'],
    'mitakesan': ['東京', 'tokyo', '青梅', 'ome', '御嶽神社', 'mitake shrine', 'musashi'],
    'takao': ['八王子', 'hachioji', '東京', 'tokyo', 'mount takao', 'mt. takao', 'mt.takao', 'takaosan', 'takao-san', '高尾山'],
}
# 植物・虫・鳥などの写真（山の写真ではない）
NOT_SUBJECT = ['inaturalist', 'flora', 'fauna', 'insect', 'beetle', 'butterfl', 'moth', 'birds', 'fungi', 'mushroom',
               'plants', 'flowers', 'species', '植物', '昆虫', 'iss0', 'from space', 'view of japan']
# 記事の中身に合う語
TOPIC = {
    'hatsuhinode': ['日の出', '朝日', '初日の出', 'ご来光', '御来光', '夜明け', '朝焼け', 'sunrise', 'dawn', 'daybreak', 'first sunrise'],
    # 地名の「富士」（富士河口湖町・富士芝桜まつり・富士見など）で数えないよう、富士山そのものの書き方だけ
    'diamond': ['富士山', 'mount fuji', 'mt. fuji', 'mt.fuji', 'mt fuji', 'fujisan', 'fuji-san', 'fujiyama', 'ダイヤモンド富士', 'diamond fuji'],
    'views': ['樹氷', '霧氷', '雪', '冬', '氷', '結氷', 'snow', 'winter', 'rime', 'frost', 'frozen', 'icy', 'juhyo', 'monster'],
}
TOPIC_NAME = {'hatsuhinode': '日の出', 'diamond': '富士山', 'views': '冬・雪'}
# 写真の位置で「この山の写真」とみなす半径（km）。冬の絶景は見どころが山頂から離れていることがある（蔵王の地蔵山頂駅など）
NEAR_KM = {'hatsuhinode': 1.5, 'diamond': 1.5, 'views': 7.0}
SKIP_WORDS = ['map', '地図', '路線図', 'logo', 'diagram', 'chart', 'timetable', '時刻表']
PROPS = {'prop': 'imageinfo|categories|coordinates', 'iiprop': 'url|size|extmetadata|mime', 'iiurlwidth': 1600,
         'clshow': '!hidden', 'cllimit': 'max', 'colimit': 'max'}


def dist_km(a, b):
    import math
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def pool(params, pages, how):
    """generator（search / geosearch）で写真を集める。題・説明・カテゴリー・撮った位置まで読む"""
    cont = {}
    for _ in range(8):
        q = dict(params)
        q.update(PROPS)
        q.update(cont)
        res = api(q)
        time.sleep(1)
        for pid, p in ((res.get('query') or {}).get('pages') or {}).items():
            x = pages.setdefault(pid, {'title': p['title'], 'cats': [], 'how': how})
            if p.get('imageinfo'):
                x['ii'] = p['imageinfo'][0]
            x['cats'] += [c['title'][9:] for c in p.get('categories') or []]
            if p.get('coordinates'):
                x['coord'] = (p['coordinates'][0]['lat'], p['coordinates'][0]['lon'])
        if 'continue' not in res:
            break
        cont = res['continue']


def commons(art, mid, center, qs):
    pages = {}
    pool({'action': 'query', 'generator': 'geosearch', 'ggscoord': '%f|%f' % center, 'ggsradius': int(NEAR_KM[art] * 1000),
          'ggsnamespace': 6, 'ggslimit': 500}, pages, 'geo')
    for w in qs:
        if w.strip():
            pool({'action': 'query', 'generator': 'search', 'gsrnamespace': 6, 'gsrsearch': w, 'gsrlimit': 40}, pages, 'search')
    names = [n.lower() for n in NAMES.get(mid, [])]
    nots = [n.lower() for n in NOT.get(mid, [])]
    topic = [t.lower() for t in TOPIC[art]]
    cands = []
    for x in pages.values():
        ii = x.get('ii') or {}
        if ii.get('mime') not in ('image/jpeg', 'image/png', 'image/webp') or (ii.get('width') or 0) < 800:
            continue
        md = ii.get('extmetadata') or {}
        lic = strip_html((md.get('LicenseShortName') or {}).get('value'))
        if not OK_LICENSE.match(lic) or strip_html((md.get('Restrictions') or {}).get('value')):
            continue
        desc = strip_html((md.get('ImageDescription') or {}).get('value'))
        text = ' '.join([x['title'][5:], desc] + x['cats']).lower()
        if any(w in x['title'].lower() for w in SKIP_WORDS) or any(w in text for w in NOT_SUBJECT):
            continue
        name_hit = next((n for n in names if n in text), None)
        if x.get('coord'):
            d = dist_km(center, x['coord'])
            # 位置の分かる写真は、山の近く（NEAR_KM）か、名前があって15km以内（山を遠くから撮った写真）だけ
            if not (d <= NEAR_KM[art] or (name_hit and d <= 15)):
                continue
            where = '撮影地は山頂から%.1fkm' % d if d <= NEAR_KM[art] else '題・説明に「%s」・撮影地は山頂から%.0fkm' % (name_hit, d)
        else:
            if not name_hit or any(n in text for n in nots):
                continue
            if mid in REGION and not any(r in text for r in REGION[mid]):
                continue
            d = None
            where = '題・説明に「%s」' % name_hit
        date = strip_html((md.get('DateTimeOriginal') or {}).get('value'))[:10]
        # 山の名前・地名の「日の出」（日の出山・日の出町）は日の出の写真の印にしない
        ttext = re.sub(r'日の出(山|町|村|屋|乃)', '', text)
        hit = next((t for t in topic if t in ttext), None)
        why = '%s：「%s」' % (TOPIC_NAME[art], hit) if hit else None
        if not hit and art == 'views':
            mm = re.match(r'(\d{4})[-:/.](\d{1,2})', date)
            # 撮った月だけで冬とみなすのは、山の近くで撮った写真だけ
            in_title = any(n in x['title'].lower() for n in names)
            if mm and int(mm.group(2)) in (12, 1, 2, 3) and ((d is not None and d <= NEAR_KM[art]) or (d is None and in_title)):
                why = '冬・雪：%s月に撮影' % int(mm.group(2))
        cands.append({'title': x['title'], 'license': lic, 'licenseUrl': strip_html((md.get('LicenseUrl') or {}).get('value')),
                      'author': strip_html((md.get('Artist') or {}).get('value')) or '作者不明', 'description': desc[:200],
                      'date': date, 'width': ii.get('width'), 'height': ii.get('height'),
                      'thumb': ii.get('thumburl') or ii.get('url'), 'pageUrl': ii.get('descriptionurl'),
                      'why': why, 'where': where, 'dist': d})
    cands.sort(key=lambda c: (c['why'] is None, c['dist'] if c['dist'] is not None else 99, -(c['width'] or 0)))
    top = [c for c in cands if c['why']][:40]
    rest = [c for c in cands if not c['why']][:24]
    return top + rest


def cmd_all():
    W, M = load(), mountains()
    SC = json.load(open(os.path.join(ROOT, 'data', 'summit_coords.json'), encoding='utf-8'))['mountains']
    os.makedirs(WORK, exist_ok=True)
    body, nav = [], []
    chosen = W.get('photos') or {}
    for art, mid in targets(W):
        name = M[mid]['name']
        key = art + '_' + mid
        qs = queries(art, mid, name)
        f = os.path.join(WORK, key + '.json')
        old = json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}
        if old.get('v') == 2 and '--refresh' not in sys.argv:
            cands = old['commons']
        else:
            sc = SC.get(mid) or {}
            cands = commons(art, mid, (sc.get('lat') or M[mid]['lat'], sc.get('lng') or M[mid]['lng']), qs)
        sp = site_photos(mid, M)
        fl = old.get('flickr') or []   # Flickr の候補（winter_photos_flickr.py が足す）は残す
        json.dump({'v': 2, 'site': sp, 'commons': cands, 'flickr': fl, 'stock': old.get('stock') or []}, open(os.path.join(WORK, key + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('%-12s %-20s サイト %d 枚・Commons %d 件（記事に合う %d）' % (art, name, len(sp), len(cands), len([c for c in cands if c['why']])))
        now = (chosen.get(art) or {}).get(mid)
        cards = []
        for i, s in enumerate(sp, 1):
            cards.append('<div class="c s" data-k="%s" data-p="S%d"><b>S%d</b> サイトの写真%s<img src="https://tozan-navi.com%s" loading="lazy"><small>%s ／ %s</small>'
                         '<button type="button" class="pick">これにする</button></div>' % (
                key, i, i, '（いまの1枚目）' if i == 1 else '', E(s['src']), E(s['author']), E(s['license'])))
        first_rest = True
        for i, c in enumerate(cands, 1):
            if not c['why'] and first_rest:
                first_rest = False
                cards.append('<h3>この山の写真（%sとは書かれていない）</h3>' % TOPIC_NAME[art])
            elif i == 1:
                cards.append('<h3>記事に合う写真（%s）</h3>' % TOPIC_NAME[art])
            cards.append('<div class="c" data-k="%s" data-p="C%d"><b>C%d</b> %s<img src="%s" loading="lazy">'
                         '<div class="why">%s</div><small>%s ／ %s ／ %s<br>%s</small>'
                         '<a href="%s" target="_blank">Commons のページ</a><button type="button" class="pick">これにする</button></div>' % (
                             key, i, i, E(c['title'][5:80]), E(re.sub(r'/\d+px-', '/500px-', c['thumb'])),
                             E(' ／ '.join(x for x in (c['why'], c['where']) if x)), E(c['author'][:40]), E(c['license']), E(c['date']),
                             E(c['description']), E(c['pageUrl'])))
        if fl:
            cards.insert(len(sp), '<h3>Flickr の写真（記事に合うもの）</h3>' + ''.join(
                '<div class="c f" data-k="%s" data-p="F%d"><b>F%d</b> %s<img src="%s" loading="lazy"><div class="why">%s</div><small>%s ／ %s ／ %s<br>%s</small>'
                '<a href="%s" target="_blank">Flickr のページ</a><button type="button" class="pick">これにする</button></div>' % (
                    key, i, i, E(c['title'][7:80]), E(c['thumb']), E(' ／ '.join(x for x in (c['why'], c['where']) if x)),
                    E(c['author'][:40]), E(c['license']), E(c['date']), E(c['description']), E(c['pageUrl']))
                for i, c in enumerate(fl, 1)))
        st = old.get('stock') or []   # ぱくたそ・写真AC の候補（winter_photos_stock.json から add-stock で足す）
        for tag, label in (('pakutaso', 'P'), ('photoac', 'A')):
            lst = [c for c in st if c['src'] == tag]
            if not lst:
                continue
            cards.insert(len(sp), '<h3>%s の写真</h3>' % ('ぱくたそ（無料・商用可・表示不要）' if tag == 'pakutaso' else '写真AC（無料・商用可・表示不要。ダウンロードは会員が手で行う）') + ''.join(
                '<div class="c p" data-k="%s" data-p="%s%d"><b>%s%d</b> %s<img src="%s" loading="lazy">%s<a href="%s" target="_blank">写真のページ</a>'
                '<button type="button" class="pick">これにする</button></div>' % (
                    key, label, i, label, i, E(c['title']), E(c['thumb']),
                    '<div class="why">%s</div>' % E(c['note']) if c.get('note') else '', E(c['page']))
                for i, c in enumerate(lst, 1)))
        nav.append('<a href="#%s">%s・%s</a>' % (key, TITLE[art], E(name)))
        body.append('<h2 id="%s" data-name="%s・%s">%s ― %s <span class="sel" data-sel="%s"></span></h2><p class="cmd">いま：%s</p>%s' % (
            key, TITLE[art], E(name), TITLE[art], E(name), key, E((now or {}).get('pick') or 'その山の1枚目の写真'),
            ''.join(cards) or '<p>候補なし</p>'))
    out = os.path.join(WORK, 'index.html')
    open(out, 'w', encoding='utf-8').write(
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>冬の特集の写真の候補</title>'
        '<style>body{font-family:sans-serif;margin:16px;background:#f0ede5}h2{border-top:2px solid #4e6535;padding-top:12px;margin-top:28px}'
        'nav a{display:inline-block;margin:3px 8px 3px 0;font-size:13px}'
        '.c{display:inline-block;vertical-align:top;width:300px;margin:6px;padding:8px;background:#fff;border:1px solid #ddd;font-size:13px}'
        '.c.p{border:2px solid #c0563a}.c.f{border:2px solid #0063dc}.c.s{border:2px solid #4e6535}.c img{display:block;width:100%;height:200px;object-fit:cover;background:#eee;margin:6px 0}'
        '.c.on{outline:4px solid #c0563a;background:#fff4ee}.pick{display:block;width:100%;margin-top:8px;padding:10px;font-size:15px;font-weight:bold;'
        'border:0;border-radius:8px;background:#4e6535;color:#fff;cursor:pointer}.c.on .pick{background:#c0563a}.sel{font-size:14px;color:#c0563a}'
        '#bar{position:fixed;left:0;right:0;bottom:0;background:#2a3e2a;color:#fff;padding:8px 12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;z-index:9}'
        '#bar button{padding:8px 12px;font-size:14px;font-weight:bold;border:0;border-radius:8px;cursor:pointer}#copy{background:#f2b07a}'
        '.why{color:#c0563a;font-weight:bold;margin-bottom:4px}h3{font-size:15px;margin:14px 6px 2px;color:#4e6535}#out{width:100%;height:56px;display:none;font-size:12px}body{padding-bottom:90px}</style>'
        '<h1>冬の特集記事の写真の候補</h1><p>S＝サイトにある写真、P＝ぱくたそ、A＝写真AC、F＝Flickr、C＝Wikimedia Commons（どちらも商用で使えて加工してよいライセンスだけ）。'
        '使う写真の「これにする」を押し（もう一度押すと取り消し）、最後に下の「選んだ内容をコピー」を押してチャットに貼ってください。選んだ内容はこの端末に残ります。</p><nav>'
        + ''.join(nav) + '</nav>' + ''.join(body) + BAR)
    print('見比べ用のページ：' + os.path.relpath(out, ROOT))


def cmd_apply(art, mid, pick):
    W, M = load(), mountains()
    data = json.load(open(os.path.join(WORK, art + '_' + mid + '.json'), encoding='utf-8'))
    kind, n = pick[0].upper(), int(pick[1:])
    if kind == 'S':
        s = data['site'][n - 1]
        rec = {'pick': pick, 'src': s['src']}
    elif kind in ('P', 'A'):
        c = [x for x in data['stock'] if x['src'] == ('pakutaso' if kind == 'P' else 'photoac')][n - 1]
        d = os.path.join(ROOT, 'images', 'articles', SLUG[art])
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, mid + '.webp')
        from PIL import Image
        if kind == 'P':
            tmp = os.path.join(d, mid + '.tmp')
            open(tmp, 'wb').write(urllib.request.urlopen(urllib.request.Request(c['full'], headers={'User-Agent': 'Mozilla/5.0'}), timeout=120).read())
        else:
            # 写真AC は会員がブラウザで手でダウンロードする決まり（ソフトでのダウンロードは規約で禁止）。置いたファイルを使う
            tmp = os.path.join(WORK, 'photoac', c['id'] + '.jpg')
            if not os.path.exists(tmp):
                # ダウンロードのフォルダに、写真の番号が名前に入ったファイルがあれば使う
                import glob
                dl = sorted(glob.glob(os.path.expanduser('~/Downloads/*%s*' % c['id'])), key=os.path.getmtime)
                dl = [f for f in dl if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                if dl:
                    tmp = dl[-1]
            if not os.path.exists(tmp):
                print('写真AC の写真は手でダウンロードしてください：%s を開いてダウンロードし、%s に置いてから、もう一度流す' % (c['page'], os.path.relpath(tmp, ROOT)))
                return
        im = Image.open(tmp).convert('RGB')
        im.thumbnail((1600, 1600))
        im.save(out, 'WEBP', quality=80)
        if kind == 'P':
            os.remove(tmp)
        rec = {'pick': pick, 'src': '/images/articles/%s/%s.webp' % (SLUG[art], mid), 'source': c['src'], 'pageUrl': c['page'],
               'sourceTitle': c['title'], 'modifications': '長辺1600pxのWebPに変換'}
    else:
        c = data['flickr' if kind == 'F' else 'commons'][n - 1]
        d = os.path.join(ROOT, 'images', 'articles', SLUG[art])
        os.makedirs(d, exist_ok=True)
        tmp = os.path.join(d, mid + '.tmp')
        out = os.path.join(d, mid + '.webp')
        open(tmp, 'wb').write(urllib.request.urlopen(urllib.request.Request(c.get('full') or c['thumb'], headers={'User-Agent': UA}), timeout=60).read())
        from PIL import Image
        im = Image.open(tmp).convert('RGB')
        im.thumbnail((1600, 1600))
        im.save(out, 'WEBP', quality=80)
        os.remove(tmp)
        rec = {'pick': pick, 'src': '/images/articles/%s/%s.webp' % (SLUG[art], mid), 'credit': c['author'], 'license': c['license'],
               'licenseUrl': c['licenseUrl'], 'pageUrl': c['pageUrl'], 'source': 'flickr' if kind == 'F' else 'wikimedia_commons',
               'sourceTitle': c['title'], 'modifications': '長辺1600pxのWebPに変換'}
    W.setdefault('photos', {}).setdefault(art, {})[mid] = rec
    json.dump(W, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('%s・%s ← %s %s' % (TITLE[art], M[mid]['name'], pick, rec['src']))


def cmd_clear(art, mid):
    W = load()
    (W.get('photos') or {}).get(art, {}).pop(mid, None)
    json.dump(W, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['all']:
        cmd_all()
    elif a[:1] == ['apply'] and len(a) == 4:
        cmd_apply(a[1], a[2], a[3])
    elif a[:1] == ['apply-text']:
        # 候補のページの「選んだ内容をコピー」の文をそのまま渡す（標準入力）。1行「<記事>_<山ID> <S1|C3>」
        for line in sys.stdin.read().splitlines():
            mm = re.match(r'^\s*(hatsuhinode|diamond|views)_(\S+)\s+([SCFPA]\d+)\s*$', line)
            if mm:
                cmd_apply(mm.group(1), mm.group(2), mm.group(3))
    elif a[:1] == ['clear'] and len(a) == 3:
        cmd_clear(a[1], a[2])
    else:
        sys.exit(__doc__)
