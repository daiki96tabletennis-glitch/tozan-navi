/* 山小屋ページの地図。window.YM_HUT_PTS（[{n:名前, la:緯度, lo:経度, u:ページ, s:予約の開始}]）を #hmap に描く。
   地図の部品（Leaflet）は、地図が画面に入るか YMHutsMap.show() が呼ばれるまで読み込まない。 */
(function () {
  var CSS = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css';
  var JS = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js';
  var el = document.getElementById('hmap');
  var pts = window.YM_HUT_PTS || [];
  var map = null, loading = false;
  if (!el || !pts.length) { return; }

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function draw() {
    var L = window.L, i, p, m, group = [];
    map = L.map(el, { scrollWheelZoom: false });
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', {
      minZoom: 5, maxZoom: 18,
      attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル</a>｜山小屋の位置 &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
    }).addTo(map);
    for (i = 0; i < pts.length; i++) {
      p = pts[i];
      m = L.circleMarker([p.la, p.lo], { radius: 8, color: '#fff', weight: 2, fillColor: '#4e6535', fillOpacity: 1 });
      m.bindPopup('<b>' + (p.u ? '<a href="' + esc(p.u) + '">' + esc(p.n) + '</a>' : esc(p.n)) + '</b>'
        + (p.s ? '<br><span style="font-size:12px;color:#6a6258">予約：' + esc(p.s) + '</span>' : ''));
      m.bindTooltip(esc(p.n), { direction: 'top', offset: [0, -6] });
      m.addTo(map);
      group.push([p.la, p.lo]);
    }
    if (group.length === 1) { map.setView(group[0], 14); }
    else { map.fitBounds(group, { padding: [24, 24], maxZoom: 14 }); }
    // 地図をタップしたあとだけ、ホイールで拡大できるようにする（ページのスクロールを邪魔しない）
    map.on('click', function () { map.scrollWheelZoom.enable(); });
  }

  function load() {
    if (map) { map.invalidateSize(); return; }
    if (loading) { return; }
    loading = true;
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = CSS;
    document.head.appendChild(link);
    var s = document.createElement('script');
    s.src = JS;
    s.onload = draw;
    s.onerror = function () { el.innerHTML = '<p style="padding:16px;font-size:13px;color:#7a7068">地図を読み込めませんでした。</p>'; };
    document.head.appendChild(s);
  }

  window.YMHutsMap = { show: load };
  if (el.getAttribute('data-lazy') === 'manual') {
    // タブを開いたときに呼ばれる。この時点ですでに見えていれば（/huts/#map で開いた場合）すぐ描く
    if (el.offsetParent !== null) { load(); }
    return;
  }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (ents) {
      for (var i = 0; i < ents.length; i++) {
        if (ents[i].isIntersecting) { io.disconnect(); load(); }
      }
    }, { rootMargin: '300px' });
    io.observe(el);
  } else {
    load();
  }
})();
