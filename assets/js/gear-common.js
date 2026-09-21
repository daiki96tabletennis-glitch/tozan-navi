// YAMATCH 装備データ共通処理
//
// 役割：商品名の正規化・アフィリエイトURL取得のみ。
// HTML描画は山ページ（mountain.js）と診断結果（recommend/index.html）で
// それぞれ異なるため、ここでは共通化しない。
//
// アフィリエイトURLの正本は /data/gear-affiliate.json。
// 山ページ・診断ページの両方がこのファイル経由でURLを取得することで、
// URLの変更を一箇所（gear-affiliate.json）だけで完結させる。
//
// 取得前や取得失敗時も表示が壊れないよう、これまで山ページで使われていた
// 値をデフォルトとして保持しておく（fetch前でも同じ結果になる）。

window.YMGear = (function () {
  var DEFAULT_CONFIG = {
    amazonTag: "amazonafdaiki-22",
    rakutenId: "57384242.53497bb8.57384243.366083eb"
  };
  var DEFAULT_DIRECT_ASIN = {
    "メレル MOAB 3 ミッド GTX": "B09BP11RNG"
  };

  var config = DEFAULT_CONFIG;
  var directAsin = DEFAULT_DIRECT_ASIN;
  var loadPromise = null;

  function normalizeProductName(name) {
    if (!name) return name;
    return String(name)
      .replace(/\(来月分\)$/, "")
      .replace(/（来月分）$/, "");
  }

  function loadAffiliateData() {
    if (loadPromise) return loadPromise;
    loadPromise = fetch("/data/gear-affiliate.json")
      .then(function (r) {
        if (!r.ok) throw new Error("gear-affiliate fetch failed");
        return r.json();
      })
      .then(function (data) {
        if (data && data.config) {
          config = Object.assign({}, DEFAULT_CONFIG, data.config);
        }
        if (data && data.directAsin) {
          directAsin = Object.assign({}, DEFAULT_DIRECT_ASIN, data.directAsin);
        }
      })
      .catch(function () {
        // 取得失敗時はデフォルト値のまま継続（表示は壊さない）
      });
    return loadPromise;
  }

  function amazonUrl(productName) {
    var clean = normalizeProductName(productName);
    if (directAsin[clean]) {
      return "https://www.amazon.co.jp/dp/" + directAsin[clean] + "?tag=" + config.amazonTag;
    }
    return "https://www.amazon.co.jp/s?k=" + encodeURIComponent(clean) + "&tag=" + config.amazonTag;
  }

  function rakutenUrl(productName) {
    var clean = normalizeProductName(productName);
    var searchUrl = "https://search.rakuten.co.jp/search/mall/" + encodeURIComponent(clean) + "/";
    var pcValue = encodeURIComponent(searchUrl);
    return "https://hb.afl.rakuten.co.jp/hgc/" + config.rakutenId + "/?pc=" + pcValue + "&m=" + pcValue;
  }

  function getAffiliate(productName) {
    if (!productName) return { amazonUrl: "", rakutenUrl: "" };
    return {
      amazonUrl: amazonUrl(productName),
      rakutenUrl: rakutenUrl(productName)
    };
  }

  return {
    normalizeProductName: normalizeProductName,
    loadAffiliateData: loadAffiliateData,
    getAffiliate: getAffiliate
  };
})();
