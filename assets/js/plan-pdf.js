/* マイページの登山計画を PDF のファイルにする（2026-11-01）。
   前は window.print() だけで、iPhone のホーム画面に追加したアプリでは何も起きなかった。
   いま開いている計画詳細（#detail-body）を画像にして（html2canvas）、A4 の PDF（jsPDF）にし、
   端末の共有（ファイルに保存・LINE など）か、使えなければダウンロードで渡す。
   ライブラリは押したときだけ cdnjs から読む。読めないときは前と同じ印刷に戻す。 */
(function(){
  var LIBS = [
    'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'
  ];
  var loading = null;

  function loadScript(src){
    return new Promise(function(resolve, reject){
      var s = document.createElement('script');
      s.src = src; s.async = true;
      s.onload = resolve;
      s.onerror = function(){ reject(new Error('load ' + src)); };
      document.head.appendChild(s);
    });
  }
  function loadLibs(){
    if (window.html2canvas && window.jspdf) return Promise.resolve();
    if (!loading) {
      loading = loadScript(LIBS[0]).then(function(){ return loadScript(LIBS[1]); });
      loading.catch(function(){ loading = null; });
    }
    return loading;
  }

  function txt(s){ return document.createTextNode(s); }

  // PDF 用に、計画の中身を白い紙の形に組み直す（ボタン・買い物のリンクは外し、リンクは URL を文字で出す）
  function buildSheet(title){
    var src = document.getElementById('detail-body');
    var sheet = document.createElement('div');
    sheet.style.cssText = 'position:fixed;left:-10000px;top:0;width:720px;padding:32px 36px;background:#ffffff;color:#3a3530;'
      + 'font-family:"Zen Kaku Gothic New","Hiragino Sans","Noto Sans JP",sans-serif;font-size:14px;line-height:1.6;box-sizing:border-box';
    var h = document.createElement('div');
    h.style.cssText = 'display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid #4e6535;padding-bottom:10px;margin-bottom:16px';
    var h1 = document.createElement('div');
    h1.style.cssText = 'font-size:24px;font-weight:700;color:#2a3820';
    h1.appendChild(txt('登山計画：' + title));
    var h2 = document.createElement('div');
    h2.style.cssText = 'font-size:11px;color:#8a8078;text-align:right';
    h2.appendChild(txt('Yamatch（tozan-navi.com）'));
    h.appendChild(h1); h.appendChild(h2);
    sheet.appendChild(h);

    var body = src.cloneNode(true);
    body.removeAttribute('id');
    body.style.padding = '0';
    Array.prototype.forEach.call(body.querySelectorAll('.pdf-btn, button'), function(b){ b.parentNode.removeChild(b); });
    Array.prototype.forEach.call(body.querySelectorAll('a[rel~="sponsored"]'), function(a){ a.parentNode.removeChild(a); });
    Array.prototype.forEach.call(body.querySelectorAll('input[type=checkbox]'), function(c){
      var s = document.createElement('span');
      s.style.cssText = 'display:inline-block;width:18px;font-size:15px;color:#4a5e4a';
      s.appendChild(txt(c.checked ? '☑' : '☐'));
      c.parentNode.replaceChild(s, c);
    });
    Array.prototype.forEach.call(body.querySelectorAll('a[href]'), function(a){
      var href = a.getAttribute('href') || '';
      if (!/^https?:/i.test(href)) return;
      a.textContent = href;
      a.style.wordBreak = 'break-all';
      a.style.color = '#2a5a8a';
    });
    Array.prototype.forEach.call(body.querySelectorAll('.card'), function(c){
      c.style.border = '1px solid #d8d2c8';
      c.style.boxShadow = 'none';
    });
    sheet.appendChild(body);

    var foot = document.createElement('div');
    foot.style.cssText = 'margin-top:14px;font-size:10px;color:#a09888;text-align:right';
    var d = new Date();
    foot.appendChild(txt('作成日 ' + d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2)));
    sheet.appendChild(foot);
    document.body.appendChild(sheet);
    return sheet;
  }

  // 縦に長い画像を A4 の高さで切り分けて、ページを重ねる
  function canvasToPdf(canvas){
    var JsPDF = window.jspdf.jsPDF;
    var pdf = new JsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait' });
    var pageW = 210, pageH = 297, margin = 8;
    var imgW = pageW - margin * 2;
    var pxPerMm = canvas.width / imgW;
    var sliceH = Math.floor((pageH - margin * 2) * pxPerMm);
    var y = 0, first = true;
    while (y < canvas.height) {
      var h = Math.min(sliceH, canvas.height - y);
      var part = document.createElement('canvas');
      part.width = canvas.width; part.height = h;
      var ctx = part.getContext('2d');
      ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, part.width, part.height);
      ctx.drawImage(canvas, 0, y, canvas.width, h, 0, 0, canvas.width, h);
      if (!first) pdf.addPage();
      pdf.addImage(part.toDataURL('image/jpeg', 0.92), 'JPEG', margin, margin, imgW, h / pxPerMm);
      first = false;
      y += h;
    }
    return pdf.output('blob');
  }

  var ready = null; // { key, blob, name }：作り終えたが共有を断られた PDF（もう一度押すと共有する）

  function canShareFile(file){
    return !!(file && navigator.share && navigator.canShare && navigator.canShare({ files: [file] }));
  }
  function toFile(blob, name){
    try { return new File([blob], name, { type: 'application/pdf' }); } catch(e) { return null; }
  }
  // 共有（ファイルに保存・LINE など）。共有できない端末はダウンロード
  function deliver(blob, name, key){
    var file = toFile(blob, name);
    if (!canShareFile(file)) { download(blob, name); return Promise.resolve(); }
    return navigator.share({ files: [file], title: name }).then(function(){ ready = null; }).catch(function(err){
      if (err && err.name === 'AbortError') { ready = null; return; } // 共有の画面を閉じただけ
      // iPhone は、押してから時間がたつと共有を断る（NotAllowedError）。作った PDF を残し、もう一度押してもらう
      ready = { key: key, blob: blob, name: name };
    });
  }
  function download(blob, name){
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = name; a.rel = 'noopener';
    document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(url); a.parentNode.removeChild(a); }, 4000);
  }

  function setBusy(on){
    Array.prototype.forEach.call(document.querySelectorAll('[data-plan-pdf]'), function(b){
      if (on) { if (!b.getAttribute('data-label')) b.setAttribute('data-label', b.textContent); b.textContent = 'PDFを作成中…'; b.disabled = true; }
      else { if (b.getAttribute('data-label')) b.textContent = b.getAttribute('data-label'); b.disabled = false; }
    });
  }

  function setReadyLabel(){
    Array.prototype.forEach.call(document.querySelectorAll('[data-plan-pdf]'), function(b){
      b.textContent = b.getAttribute('data-ready-label') || 'PDFができました。押して保存・共有';
    });
  }

  // 計画詳細を開いたときに先にライブラリを読んでおく（押してから共有までを短くする）
  window.ymPlanPdfPreload = function(){ ready = null; loadLibs().catch(function(){}); };

  window.ymPlanPdf = function(){
    var titleEl = document.getElementById('detail-title');
    var title = (titleEl && titleEl.textContent) || '登山計画';
    var safe = title.replace(/[\\\/:*?"<>|\s]+/g, '_');
    // 計画を開き直すと ymPlanPdfPreload が ready を消すので、開いているあいだは題名で見分ければよい
    var key = title;
    if (ready && ready.key === key) {
      var r = ready;
      return deliver(r.blob, r.name, key).then(function(){ if (!ready) setBusy(false); });
    }
    setBusy(true);
    var sheet = null;
    return loadLibs().then(function(){
      sheet = buildSheet(title);
      return window.html2canvas(sheet, { scale: 2, backgroundColor: '#ffffff', useCORS: true, logging: false });
    }).then(function(canvas){
      if (sheet) { sheet.parentNode.removeChild(sheet); sheet = null; }
      return deliver(canvasToPdf(canvas), '登山計画_' + safe + '.pdf', key);
    }).then(function(){
      setBusy(false);
      if (ready) setReadyLabel();
    }, function(){
      if (sheet && sheet.parentNode) sheet.parentNode.removeChild(sheet);
      setBusy(false);
      // PDF を作れなかったときは、前と同じ印刷の画面へ
      try { window.print(); } catch(e) {}
    });
  };
})();
