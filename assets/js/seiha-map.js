// 登山制覇マップ（2026-10-25〜）
// 登った山を都道府県ごとに数え、日本地図を色分けする。同じ県で登った山が増えるほど濃くなる。
// 地図の形は data/japan_prefs_map.json（Natural Earth・パブリックドメインを簡略化）。
// 使う場所：マイページの「登った記録」（mypage/index.html）と、共有されたURLを開くページ（/seiha/）。
(function(){
  var MAP_URL = '/data/japan_prefs_map.json?v=20261025';
  var LEVELS = [
    { min: 0, color: '#dcd8ce', label: '0' },
    { min: 1, color: '#d4e3bf', label: '1' },
    { min: 2, color: '#afcb8e', label: '2〜3' },
    { min: 4, color: '#7fa25c', label: '4〜6' },
    { min: 7, color: '#4e6535', label: '7〜' }
  ];
  var mapData = null, waiters = [];

  function loadMap(cb){
    if (mapData) { cb(mapData); return; }
    waiters.push(cb);
    if (waiters.length > 1) return;
    fetch(MAP_URL).then(function(r){ return r.json(); }).then(function(d){ mapData = d; })
      .catch(function(){ mapData = null; })
      .then(function(){ var w = waiters; waiters = []; w.forEach(function(f){ f(mapData); }); });
  }

  function colorFor(n){
    var c = LEVELS[0].color;
    for (var i = 0; i < LEVELS.length; i++) { if (n >= LEVELS[i].min) c = LEVELS[i].color; }
    return c;
  }

  // 文字（「長野県北部」「東京都・埼玉県」など）から都道府県名を取り出す
  var PREF_RE = /(北海道|東京都|京都府|大阪府|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)/g;
  function prefsFromText(text){
    var out = [], m;
    var s = String(text || '');
    PREF_RE.lastIndex = 0;
    while ((m = PREF_RE.exec(s)) !== null) { if (out.indexOf(m[1]) === -1) out.push(m[1]); }
    return out;
  }

  // 山の一覧（[{prefs:[県名...]}]）から、県コードごとの山の数を作る。県境の山は、それぞれの県に1つずつ数える
  function countByPref(list, map){
    var nameToCode = {};
    (map.prefs || []).forEach(function(p){ nameToCode[p.name] = p.code; });
    var counts = {};
    list.forEach(function(m){
      (m.prefs || []).forEach(function(name){
        var code = nameToCode[name];
        if (code) counts[code] = (counts[code] || 0) + 1;
      });
    });
    return counts;
  }

  // 共有用：県コード 01〜47 の順に、山の数を1文字（0〜9・a〜z。35以上は z）で並べる
  function encode(counts){
    var s = '';
    for (var i = 1; i <= 47; i++) {
      var code = (i < 10 ? '0' : '') + i;
      var n = Math.min(35, counts[code] || 0);
      s += n.toString(36);
    }
    return s.replace(/0+$/, '');
  }
  function decode(str){
    var counts = {};
    str = String(str || '').toLowerCase().replace(/[^0-9a-z]/g, '').slice(0, 47);
    for (var i = 0; i < str.length; i++) {
      var n = parseInt(str.charAt(i), 36) || 0;
      if (n > 0) counts[(i + 1 < 10 ? '0' : '') + (i + 1)] = n;
    }
    return counts;
  }

  function prefCount(counts){ var n = 0; for (var k in counts) { if (counts[k] > 0) n++; } return n; }

  // 地図を描く。el に SVG と凡例を入れる
  function render(el, counts, opts){
    opts = opts || {};
    loadMap(function(map){
      if (!map) { el.innerHTML = '<div style="padding:20px;text-align:center;color:#8a7a6a;font-size:13px">地図を読み込めませんでした</div>'; return; }
      var vb = map.viewBox.split(' ');
      var b = map.okinawaBox;
      var svg = '<svg viewBox="' + map.viewBox + '" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="登山制覇マップ" style="width:100%;height:auto;display:block">';
      svg += '<rect x="' + b[0] + '" y="' + b[1] + '" width="' + b[2] + '" height="' + b[3] + '" rx="8" fill="none" stroke="#c9c2b4" stroke-width="2"/>';
      map.prefs.forEach(function(p){
        var n = counts[p.code] || 0;
        svg += '<path d="' + p.d + '" fill="' + colorFor(n) + '" stroke="#ffffff" stroke-width="1.6" stroke-linejoin="round" data-code="' + p.code + '"><title>' + p.name + '　' + n + '山</title></path>';
      });
      svg += '</svg>';
      var legend = '<div style="display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap;margin-top:8px;font-size:11px;color:#6a6458">';
      legend += '<span>登った山の数</span>';
      LEVELS.forEach(function(l){
        legend += '<span style="display:inline-flex;align-items:center;gap:3px"><span style="width:14px;height:14px;border-radius:3px;background:' + l.color + ';display:inline-block;border:1px solid rgba(0,0,0,0.06)"></span>' + l.label + '</span>';
      });
      legend += '</div>';
      el.innerHTML = '<div class="ym-seiha-map" style="position:relative">' + svg + '<div class="ym-seiha-tip" style="display:none;position:absolute;left:50%;top:8px;transform:translateX(-50%);background:rgba(42,56,32,0.9);color:#fff;font-size:12px;font-weight:700;padding:5px 10px;border-radius:14px;pointer-events:none"></div></div>' + legend;
      // 県を押すと、県名と山の数を出す
      var tip = el.querySelector('.ym-seiha-tip');
      var names = {}; map.prefs.forEach(function(p){ names[p.code] = p.name; });
      el.querySelector('svg').addEventListener('click', function(e){
        var t = e.target;
        if (!t || !t.getAttribute) return;
        var code = t.getAttribute('data-code');
        if (!code) { tip.style.display = 'none'; return; }
        tip.textContent = names[code] + '　' + (counts[code] || 0) + '山';
        tip.style.display = 'block';
        clearTimeout(tip._t); tip._t = setTimeout(function(){ tip.style.display = 'none'; }, 2200);
      });
      if (opts.onReady) opts.onReady(map);
    });
  }

  // 共有用の画像（正方形 1080 または 縦長 1080×1920）を作る
  function makeImage(counts, stats, tall, cb){
    loadMap(function(map){
      if (!map) { cb(null); return; }
      var W = 1080, H = tall ? 1920 : 1080;
      var cv = document.createElement('canvas'); cv.width = W; cv.height = H;
      var ctx = cv.getContext('2d');
      ctx.fillStyle = '#f0ede5'; ctx.fillRect(0, 0, W, H);
      var font = '"Hiragino Sans","Zen Kaku Gothic New","Noto Sans JP",sans-serif';
      var top = tall ? 200 : 70;
      ctx.fillStyle = '#4e6535'; ctx.font = '700 40px ' + font; ctx.textAlign = 'center';
      ctx.fillText('Yamatch', W / 2, top);
      ctx.fillStyle = '#2a3820'; ctx.font = '800 72px ' + font;
      ctx.fillText('登山制覇マップ', W / 2, top + 88);
      var vb = map.viewBox.split(' ').map(Number);
      var mapW = tall ? 920 : 640, mapH = mapW * vb[3] / vb[2];
      var mx = tall ? (W - mapW) / 2 : 70, my = top + 130;
      ctx.save(); ctx.translate(mx, my); ctx.scale(mapW / vb[2], mapW / vb[2]);
      var b = map.okinawaBox;
      ctx.strokeStyle = '#c9c2b4'; ctx.lineWidth = 2; ctx.strokeRect(b[0], b[1], b[2], b[3]);
      map.prefs.forEach(function(p){
        var path = new Path2D(p.d);
        ctx.fillStyle = colorFor(counts[p.code] || 0); ctx.fill(path);
        ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.6; ctx.stroke(path);
      });
      ctx.restore();
      var sy = my + mapH + (tall ? 110 : 30);
      var items = [[stats.prefs + '', '都道府県'], [stats.mountains + '', '登った山'], [stats.hyaku + '', '百名山']];
      if (!tall) {
        // 正方形は地図の右に数字を縦に並べる
        ctx.textAlign = 'left';
        var x0 = mx + mapW + 30, y0 = my + 200;
        items.forEach(function(it, i){
          ctx.fillStyle = '#2a3820'; ctx.font = '800 64px Outfit,' + font; ctx.fillText(it[0], x0 + 20, y0 + i * 130);
          ctx.fillStyle = '#6a6458'; ctx.font = '700 26px ' + font; ctx.fillText(it[1], x0 + 20, y0 + i * 130 + 38);
        });
        ctx.textAlign = 'center';
      } else {
        items.forEach(function(it, i){
          var cx = W / 2 + (i - 1) * 300;
          ctx.fillStyle = '#2a3820'; ctx.font = '800 84px Outfit,' + font; ctx.fillText(it[0], cx, sy);
          ctx.fillStyle = '#6a6458'; ctx.font = '700 32px ' + font; ctx.fillText(it[1], cx, sy + 50);
        });
      }
      if (stats.highest) {
        ctx.fillStyle = '#4e6535'; ctx.font = '700 ' + (tall ? 34 : 28) + 'px ' + font; ctx.textAlign = 'center';
        ctx.fillText('いちばん高い山：' + stats.highest, W / 2, tall ? sy + 140 : H - 90);
      }
      ctx.fillStyle = '#8a7a6a'; ctx.font = '500 ' + (tall ? 30 : 24) + 'px ' + font; ctx.textAlign = 'center';
      ctx.fillText('#登山制覇マップ  tozan-navi.com/seiha/', W / 2, H - (tall ? 160 : 40));
      if (cv.toBlob) cv.toBlob(function(bl){ cb(bl); }, 'image/png'); else cb(null);
    });
  }

  window.YmSeihaMap = {
    LEVELS: LEVELS, load: loadMap, render: render, prefsFromText: prefsFromText,
    countByPref: countByPref, encode: encode, decode: decode, prefCount: prefCount, makeImage: makeImage
  };
})();
