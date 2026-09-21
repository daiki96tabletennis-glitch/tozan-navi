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
//
// Amazon優先順位: 商品別amazonUrl → 商品別amazonAsin → 商品名から検索URL生成
// 楽天優先順位  : 商品別rakutenUrl → 商品名から検索URL生成
// （個別指定が無い商品はこれまでと全く同じ検索URLになる）

window.YMGear = (function () {
  var DEFAULT_CONFIG = {
    amazonTag: "amazonafdaiki-22",
    rakutenId: "57384242.53497bb8.57384243.366083eb"
  };
  var DEFAULT_PRODUCTS = {
    "メレル MOAB 3 ミッド GTX": {
      amazonAsin: "B09BP11RNG",
      amazonUrl: "",
      rakutenUrl: ""
    }
  };

  var config = DEFAULT_CONFIG;
  var products = DEFAULT_PRODUCTS;
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
        if (data && data.products) {
          products = Object.assign({}, DEFAULT_PRODUCTS, data.products);
        }
      })
      .catch(function () {
        // 取得失敗時はデフォルト値のまま継続（表示は壊さない）
      });
    return loadPromise;
  }

  function amazonUrl(productName) {
    var clean = normalizeProductName(productName);
    var p = products[clean];
    if (p && p.amazonUrl) {
      return p.amazonUrl;
    }
    if (p && p.amazonAsin) {
      return "https://www.amazon.co.jp/dp/" + p.amazonAsin + "?tag=" + config.amazonTag;
    }
    return "https://www.amazon.co.jp/s?k=" + encodeURIComponent(clean) + "&tag=" + config.amazonTag;
  }

  function rakutenUrl(productName) {
    var clean = normalizeProductName(productName);
    var p = products[clean];
    if (p && p.rakutenUrl) {
      return p.rakutenUrl;
    }
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
