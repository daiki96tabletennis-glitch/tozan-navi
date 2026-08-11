(function () {
  'use strict';

  var match = location.pathname.match(/^\/mountains\/([^/]+)/);
  if (!match) return;

  fetch('/data/image-credits.json')
    .then(function (response) { return response.ok ? response.json() : {}; })
    .then(function (allCredits) {
      var photos = allCredits[match[1]];
      if (!Array.isArray(photos) || !photos.length) return;

      var details = document.createElement('details');
      details.className = 'ym-photo-credits';
      details.style.cssText = 'max-width:680px;margin:12px auto;padding:10px 14px;background:#f7f6f2;border:1px solid #e1ddd4;border-radius:8px;font-size:12px;line-height:1.7;color:#4a463f';

      var summary = document.createElement('summary');
      summary.textContent = '写真クレジット（' + photos.length + '枚）';
      summary.style.cssText = 'cursor:pointer;font-weight:700';
      details.appendChild(summary);

      var list = document.createElement('ol');
      list.style.cssText = 'margin:8px 0 0;padding-left:22px';
      photos.forEach(function (photo) {
        var item = document.createElement('li');
        item.style.margin = '5px 0';
        item.appendChild(document.createTextNode((photo.author || '作者不明') + ' / '));

        if (photo.licenseUrl) {
          var license = document.createElement('a');
          license.textContent = photo.license || 'ライセンス';
          license.href = photo.licenseUrl;
          license.target = '_blank';
          license.rel = 'noopener';
          item.appendChild(license);
        } else {
          item.appendChild(document.createTextNode(photo.license || (photo.source === 'own' ? 'YAMATCH自前写真' : 'ライセンス不明')));
        }

        var sourceUrl = photo.commonsPageUrl || photo.sourcePageUrl;
        if (sourceUrl) {
          item.appendChild(document.createTextNode(' / '));
          var source = document.createElement('a');
          source.textContent = photo.source === 'wikimedia_commons' ? 'Wikimedia Commonsの元画像' : '元画像';
          source.href = sourceUrl;
          source.target = '_blank';
          source.rel = 'noopener';
          item.appendChild(source);
        } else if (photo.source === 'own') {
          item.appendChild(document.createTextNode(' / YAMATCH撮影写真'));
        }

        if (photo.modifications) {
          item.appendChild(document.createTextNode(' / 変更: ' + photo.modifications));
        }
        list.appendChild(item);
      });
      details.appendChild(list);

      var anchor = document.querySelector('.hero-new') || document.querySelector('main') || document.body;
      anchor.insertAdjacentElement('afterend', details);
    })
    .catch(function () {
      /* クレジットデータ取得失敗で山ページ本体を止めない */
    });
})();
