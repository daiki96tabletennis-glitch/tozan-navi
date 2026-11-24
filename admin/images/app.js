(function () {
  'use strict';

  const OWNER = 'daiki96tabletennis-glitch';
  const REPO = 'tozan-navi';
  const COMMONS_API = 'https://commons.wikimedia.org/w/api.php';
  const WIKIDATA_API = 'https://www.wikidata.org/w/api.php';
  const CACHE_KEY = 'ym_image_candidate_cache_v3';
  const CACHE_TTL = 7 * 24 * 60 * 60 * 1000;
  // 写真はサイトに載せる前に、長辺1600pxの WebP にそろえる（2026-11-05〜。サイト全体のデータ量を増やさないため）
  // 自前の写真も Commons の写真も同じ。WebP にできない端末では JPEG（品質0.82）にする
  const PHOTO_MAX_EDGE = 1600;
  const WEBP_QUALITY = 80;
  const JPEG_QUALITY = 0.82;
  // HEIC（iPhone の写真）をブラウザが読めないとき（Chrome・Windows など）だけ読み込む
  const HEIC_LIB = 'https://cdn.jsdelivr.net/npm/heic-to@1.6.6/dist/iife/heic-to.js';
  // Safari は canvas から WebP を作れないので、そのときだけ WebP の変換器（Squoosh の libwebp）を読み込む
  const WEBP_ENC = 'https://cdn.jsdelivr.net/npm/@jsquash/webp@1.5.0/codec/enc/webp_enc.js';
  const WEBP_OPTIONS = { quality: WEBP_QUALITY, target_size: 0, target_PSNR: 0, method: 4, sns_strength: 50, filter_strength: 60, filter_sharpness: 0, filter_type: 1, partitions: 0, segments: 4, pass: 1, show_compressed: 0, preprocessing: 0, autofilter: 0, partition_limit: 0, alpha_compression: 1, alpha_filtering: 1, alpha_quality: 100, lossless: 0, exact: 0, image_hint: 0, emulate_jpeg_size: 0, thread_level: 0, low_memory: 0, near_lossless: 100, use_delta_palette: 0, use_sharp_yuv: 0 };

  const state = {
    mountains: [],
    credits: {},
    currentId: null,
    candidates: [],
    excluded: [],
    showExcluded: false,
    drafts: {},
    originalPaths: {},
    ownFiles: {},
    hashScans: {},
    lastApiRequestAt: 0
  };

  const $ = (id) => document.getElementById(id);
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function clean(html) {
    if (!html) return '';
    const box = document.createElement('div');
    box.innerHTML = String(html);
    return (box.textContent || '').replace(/\s+/g, ' ').trim();
  }

  function safeUrl(url) {
    if (!url) return '';
    try {
      const parsed = new URL(url, location.href);
      return ['http:', 'https:', 'blob:'].includes(parsed.protocol) ? parsed.href : '';
    } catch (_) {
      return '';
    }
  }

  function setStatus(text, type, target) {
    const element = $(target || 'status');
    if (!element) return;
    element.textContent = text || '';
    element.className = text ? 'status ' + (type || 'ok') : '';
  }

  function currentMountain() {
    return state.mountains.find((mountain) => String(mountain.id) === String(state.currentId));
  }

  function photoCount(mountain) {
    return Array.isArray(mountain && mountain.photos) ? mountain.photos.length : 0;
  }

  function coordinate(mountain) {
    if (!mountain) return null;
    const lat = Number(mountain.lat ?? mountain.latitude);
    const lng = Number(mountain.lng ?? mountain.longitude ?? mountain.lon);
    if (Number.isFinite(lat) && Number.isFinite(lng)) return { lat, lng };
    const match = String(mountain.gmapUrl || mountain.mapUrl || '').match(/@(-?[\d.]+),(-?[\d.]+)/);
    return match ? { lat: Number(match[1]), lng: Number(match[2]) } : null;
  }

  function distanceKm(a, b) {
    if (!a || !b) return null;
    const rad = (value) => value * Math.PI / 180;
    const earth = 6371;
    const dLat = rad(b.lat - a.lat);
    const dLng = rad(b.lng - a.lng);
    const h = Math.sin(dLat / 2) ** 2
      + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
    return earth * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
  }

  async function api(url, params, attempt) {
    const retry = attempt || 0;
    const elapsed = Date.now() - state.lastApiRequestAt;
    if (elapsed < 220) await wait(220 - elapsed);
    state.lastApiRequestAt = Date.now();

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const query = new URLSearchParams(Object.assign({}, params, { format: 'json', origin: '*' }));
      const response = await fetch(url + '?' + query.toString(), {
        signal: controller.signal,
        headers: { Accept: 'application/json' }
      });
      if (!response.ok) {
        if ((response.status === 429 || response.status >= 500) && retry < 2) {
          await wait(800 * (retry + 1));
          return api(url, params, retry + 1);
        }
        throw new Error('APIエラー ' + response.status);
      }
      return response.json();
    } catch (error) {
      if (retry < 2 && (error.name === 'AbortError' || error instanceof TypeError)) {
        await wait(800 * (retry + 1));
        return api(url, params, retry + 1);
      }
      if (error.name === 'AbortError') throw new Error('APIが時間内に応答しませんでした');
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  function evaluateLicense(item) {
    if (item.source === 'own') {
      if (!String(item.author || '').trim()) {
        return { ok: false, label: '撮影者名が必要', reason: '自前写真には撮影者名を入力してください。' };
      }
      return { ok: true, label: '自前写真', reason: '自分で撮影した写真として登録します。' };
    }

    const license = String(item.license || '').trim();
    const normalized = license.toUpperCase().replace(/[‐‑‒–—]/g, '-');
    const author = String(item.author || '').trim();
    const authorUnknown = !author || /AUTHOR_UNKNOWN|UNKNOWN|作者不明/i.test(author);
    const hasRequiredLinks = Boolean(safeUrl(item.licenseUrl) && safeUrl(item.commonsPageUrl || item.sourcePageUrl));

    if (!license || /LICENSE_UNKNOWN|UNKNOWN|不明/i.test(license)) {
      return { ok: false, label: 'ライセンス不明', reason: 'ライセンス情報が取得できないため採用できません。' };
    }
    if (/ALL RIGHTS RESERVED|ARR|著作権者に無断/i.test(normalized)) {
      return { ok: false, label: '採用不可', reason: '再利用を許可するライセンスではありません。' };
    }
    if (/(^|[-\s])NC($|[-\s\d])|NON.?COMMERCIAL/i.test(normalized)) {
      return { ok: false, label: '非営利限定', reason: 'NC（非営利限定）のためYAMATCHでは採用しません。' };
    }
    if (/(^|[-\s])ND($|[-\s\d])|NO.?DERIV/i.test(normalized)) {
      return { ok: false, label: '加工不可', reason: 'ND（改変禁止）のため、縮小や切り抜きを行うサイトでは採用しません。' };
    }

    const isCc0 = /\bCC\s*0\b|CREATIVE COMMONS ZERO/i.test(normalized);
    const isPublicDomain = /PUBLIC DOMAIN|PUBLIC-DOMAIN|\bPDM\b|パブリックドメイン/i.test(normalized);
    const isBy = /\bCC\s+BY(?:-SA)?\b|CREATIVE COMMONS ATTRIBUTION/i.test(normalized);

    if (!isCc0 && !isPublicDomain && !isBy) {
      return { ok: false, label: '要確認・採用不可', reason: 'YAMATCHの自動許可対象（CC0・PDM・CC BY・CC BY-SA）ではありません。' };
    }
    if (authorUnknown) {
      return { ok: false, label: '作者不明', reason: 'クレジット表示に必要な作者名が取得できません。' };
    }
    if (!hasRequiredLinks) {
      return { ok: false, label: '情報不足', reason: 'ライセンスURLまたは元画像ページが取得できません。' };
    }
    return {
      ok: true,
      label: '自動チェックOK',
      reason: '商用利用可能な許可ライセンス・作者・ライセンスURL・元ページを取得済みです。'
    };
  }

  function normalizeIdentity(value) {
    let text = String(value || '');
    try { text = decodeURIComponent(text); } catch (_) { /* 既にデコード済み */ }
    return text.normalize('NFKC').replace(/^File:/i, '').replace(/[_\s]+/g, ' ').trim().toLowerCase();
  }

  function commonsIdentity(item) {
    if (item.sourceId && String(item.sourceId).startsWith('commons:')) return String(item.sourceId);
    const pageUrl = String(item.commonsPageUrl || item.sourcePageUrl || '');
    const isCommons = item.source === 'wikimedia_commons' || /commons\.wikimedia\.org/i.test(pageUrl);
    if (!isCommons) return '';
    let title = item.fileName || '';
    if (pageUrl) {
      try {
        const decodedPath = decodeURIComponent(new URL(pageUrl).pathname);
        const match = decodedPath.match(/\/wiki\/(?:File:)?(.+)$/i);
        if (match && match[1]) title = match[1];
      } catch (_) { /* fileNameへフォールバック */ }
    }
    const normalized = normalizeIdentity(title);
    return normalized ? 'commons:' + normalized : '';
  }

  function imageIdentityKeys(item) {
    const keys = [];
    const sourceKey = commonsIdentity(item);
    if (sourceKey) keys.push(sourceKey);
    else if (item.sourceId) keys.push(String(item.sourceId));
    if (item.contentHash) keys.push('sha256:' + String(item.contentHash).toLowerCase());
    return keys;
  }

  function sameImage(first, second) {
    const firstKeys = new Set(imageIdentityKeys(first));
    return imageIdentityKeys(second).some((key) => firstKeys.has(key));
  }

  function duplicateAnalysis(items) {
    const seen = new Map();
    const extras = new Set();
    const matches = [];
    items.forEach((item, index) => {
      const keys = imageIdentityKeys(item);
      const originalIndex = keys.map((key) => seen.get(key)).find((value) => value !== undefined);
      if (originalIndex !== undefined) {
        extras.add(index);
        matches.push({ originalIndex, duplicateIndex: index });
      }
      keys.forEach((key) => {
        if (!seen.has(key)) seen.set(key, originalIndex !== undefined ? originalIndex : index);
      });
    });
    return { extras, matches };
  }

  // ---- 候補を集める（2026-11-24 見直し。運営者の指示「見つからない山も、ほかのサイトも使っていろんな候補を。関係ない画像・画質の悪い画像は出さない」）
  // 前は山名をそのまま1回だけ検索していて、「天覧山・多峯主山」「大山（丹沢）」のような名前では1件も当たらなかった
  const OPENVERSE_API = 'https://api.openverse.org/v1/images/';
  const JAWIKI_API = 'https://ja.wikipedia.org/w/api.php';
  const MIN_LONG_EDGE = 1000;
  const MIN_SHORT_EDGE = 560;
  const MIN_FILE_BYTES = 60 * 1024;
  // 写っているものが山ではないことがはっきりしている画像（山名が書いてあっても出さない）
  const HARD_NG = /\.(svg|pdf|djvu|tiff?|gif|ogg|webm)$|地図|ロゴ|\blogo\b|\bmap\b|locator|location map|diagram|図版|路線図|駅跡|ラーメン|ramen|料理|menu|メニュー|NDL\d|CADAL|crater \d|tournament|book cover|banner|看板の文字/i;
  // 山ではないものが主役のことが多い画像（山名が無ければ出さない。山名があっても点を下げる）
  const SOFT_NG = /station|駅|train|電車|鉄道|列車|\bbus\b|バス|school|学校|shrine|神社|temple|寺|museum|博物館|portrait|people|festival|祭|insect|昆虫|butterfly|蝶|bird|鳥|flower|花|food|食|car\b|自動車|interior|室内|sign|標識|案内板/i;
  const LANDSCAPE = /view|scenery|landscape|panorama|sunrise|sunset|autumn|snow|forest|眺め|景色|風景|パノラマ|紅葉|雪|朝日|夕日|日の出|樹林|森/i;
  const MOUNTAIN_WORD = /summit|mountain|mount|\bmt\b|peak|ridge|trail|hiking|山頂|頂上|山岳|稜線|登山|尾根|展望|眺望|山並み|峰|岳/i;

  const KANA = { きゃ:'kya',きゅ:'kyu',きょ:'kyo',しゃ:'sha',しゅ:'shu',しょ:'sho',ちゃ:'cha',ちゅ:'chu',ちょ:'cho',にゃ:'nya',にゅ:'nyu',にょ:'nyo',ひゃ:'hya',ひゅ:'hyu',ひょ:'hyo',みゃ:'mya',みゅ:'myu',みょ:'myo',りゃ:'rya',りゅ:'ryu',りょ:'ryo',ぎゃ:'gya',ぎゅ:'gyu',ぎょ:'gyo',じゃ:'ja',じゅ:'ju',じょ:'jo',びゃ:'bya',びゅ:'byu',びょ:'byo',ぴゃ:'pya',ぴゅ:'pyu',ぴょ:'pyo',
    あ:'a',い:'i',う:'u',え:'e',お:'o',か:'ka',き:'ki',く:'ku',け:'ke',こ:'ko',さ:'sa',し:'shi',す:'su',せ:'se',そ:'so',た:'ta',ち:'chi',つ:'tsu',て:'te',と:'to',な:'na',に:'ni',ぬ:'nu',ね:'ne',の:'no',は:'ha',ひ:'hi',ふ:'fu',へ:'he',ほ:'ho',ま:'ma',み:'mi',む:'mu',め:'me',も:'mo',や:'ya',ゆ:'yu',よ:'yo',ら:'ra',り:'ri',る:'ru',れ:'re',ろ:'ro',わ:'wa',を:'o',ん:'n',
    が:'ga',ぎ:'gi',ぐ:'gu',げ:'ge',ご:'go',ざ:'za',じ:'ji',ず:'zu',ぜ:'ze',ぞ:'zo',だ:'da',ぢ:'ji',づ:'zu',で:'de',ど:'do',ば:'ba',び:'bi',ぶ:'bu',べ:'be',ぼ:'bo',ぱ:'pa',ぴ:'pi',ぷ:'pu',ぺ:'pe',ぽ:'po',ゔ:'vu' };

  function romaji(kana) {
    const text = String(kana || '').replace(/[ァ-ヶ]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0x60));
    let out = '';
    for (let i = 0; i < text.length; i += 1) {
      const two = text.slice(i, i + 2);
      if (KANA[two]) { out += KANA[two]; i += 1; continue; }
      const ch = text[i];
      if (ch === 'っ') { const next = KANA[text.slice(i + 1, i + 3)] || KANA[text[i + 1]] || ''; out += next.charAt(0); continue; }
      if (ch === 'ー') { out += out.slice(-1); continue; }
      out += KANA[ch] || '';
    }
    return out.replace(/ou/g, 'o').replace(/uu/g, 'u');
  }

  // 山名の言い方を集める：「・」で分けた峰、かっこの中の峰の名前（赤岳）や地域（丹沢）、YAMAP の山名、読みのローマ字
  function nameVariants(mountain) {
    const ja = [];
    const context = [];
    const add = (list, value) => { const v = String(value || '').trim(); if (v.length >= 2 && !list.includes(v)) list.push(v); };
    String(mountain.name || '').split('・').forEach((part) => {
      const m = part.match(/^(.*?)（(.*?)）$/);
      if (m) {
        add(ja, m[1]);
        if (/[山岳峰]$/.test(m[2])) add(ja, m[2]); else add(context, m[2].replace(/^北ア$/, '北アルプス'));
      } else add(ja, part);
    });
    add(ja, mountain.yamapName);
    String(mountain.area || '').split(/[・、\s]/).forEach((v) => add(context, v.replace(/[都道府県]$/, '')));
    const roman = [];
    String(mountain.kana || '').split('・').forEach((part) => {
      const r = romaji(part.replace(/（.*?）|\(.*?\)/g, ''));
      if (r.length >= 4) {
        const base = r.replace(/(yama|san|dake|take|zan)$/, '');
        if (base.length >= 3 && !roman.some((x) => x.base === base)) roman.push({ full: r, base });
      }
    });
    // 「大山」「丸山」のように同じ名前の山が多い名前は、位置か地域の言葉が合うものだけにする
    const generic = ja.length > 0 && (ja[0].length <= 2 || /^(丸山|二子山|大山|高山|富士山|城山|愛宕山|権現山|三ツ峠山)$/.test(ja[0]));
    return { ja, context, roman, generic };
  }

  function nameHit(text, variants) {
    const lower = String(text || '').toLowerCase();
    if (variants.ja.some((v) => lower.includes(v.toLowerCase()))) return 'ja';
    for (const r of variants.roman) {
      const re = new RegExp('(\\bmt\\.?\\s*|\\bmount\\s+)' + r.base + '|' + r.base + '[-\\s]?(yama|san|dake|take|zan)\\b|' + r.full, 'i');
      if (re.test(lower)) return 'roman';
    }
    return '';
  }

  function qualityProblem(item) {
    const longEdge = Math.max(item.width || 0, item.height || 0);
    const shortEdge = Math.min(item.width || 0, item.height || 0);
    if (item.mimeType && !/^image\/(jpeg|png|webp)$/i.test(item.mimeType)) return '写真の形式ではない（' + item.mimeType + '）';
    if (!longEdge) return '大きさが分からない';
    if (longEdge < MIN_LONG_EDGE || shortEdge < MIN_SHORT_EDGE) return '画質が低い（' + item.width + '×' + item.height + 'px）';
    if (item.fileSize && item.fileSize < MIN_FILE_BYTES) return 'ファイルが小さすぎる（' + Math.round(item.fileSize / 1024) + 'KB）';
    const ratio = longEdge / shortEdge;
    if (ratio > 3.2) return '極端に細長い（' + item.width + '×' + item.height + 'px）';
    return '';
  }

  function relevanceProblem(item, mountain, variants) {
    const text = [item.fileName, item.description, item.categories, item.tags].join(' ');
    if (HARD_NG.test(text)) return '山の写真ではない（地図・図・文書・料理など）';
    const hit = nameHit(text, variants);
    const distance = item.distanceKm;
    const trusted = ['wikidata_p18', 'wikidata_category', 'wikipedia_article'].includes(item.method);
    const near = distance != null && distance <= 2.5;
    const contextHit = variants.context.some((c) => c && text.includes(c));
    if (variants.generic && !trusted && !near && !contextHit && (distance == null || distance > 8)) {
      return '同じ名前の別の山の可能性（位置・地域が合わない）';
    }
    if (distance != null && distance > 25 && !trusted) return '山から' + Math.round(distance) + 'km離れた場所の写真';
    if (trusted || hit || near) {
      // 山名が書かれていない写真（山頂付近・カテゴリ・記事から来たもの）は、山や景色の写真だと分かるものだけ（自転車レース・学校・町並みなどを除く）
      // カテゴリ名（「栃木県の山」など）は写っているものを表さないので、ファイル名・説明・タグだけで見る
      const core = [item.fileName, item.description, item.tags].join(' ');
      // 山名があっても、駅・学校・神社などが主役で山や景色の言葉が無い写真は出さない（「丸山駅」「◯◯神社」など）
      if (item.method !== 'wikidata_p18' && SOFT_NG.test(core) && !MOUNTAIN_WORD.test(core) && !LANDSCAPE.test(core)) return '山以外のもの（駅・学校・神社など）の写真';
      if (!hit && item.method !== 'wikidata_p18') {
        if (SOFT_NG.test(core) && !MOUNTAIN_WORD.test(core)) return '山の近くだが、山以外のものの写真';
        if (!MOUNTAIN_WORD.test(core) && !LANDSCAPE.test(core)) return '山の近くで撮られたが、山や景色の写真か分からない';
      }
      return '';
    }
    return '山名が書かれていない・山の近くで撮られていない';
  }

  function scoreCandidate(item, mountain, variants) {
    let score = { wikidata_p18: 50, wikidata_category: 30, wikipedia_article: 30 }[item.method] || 0;
    const text = [item.fileName, item.description, item.categories, item.tags].join(' ');
    const hit = nameHit(text, variants);
    if (hit === 'ja') score += 25;
    if (hit === 'roman') score += 15;
    if (MOUNTAIN_WORD.test(text)) score += 8;
    if (SOFT_NG.test(text)) score -= 18;
    if (item.width > item.height) score += 10;
    if (Math.max(item.width, item.height) >= 1600) score += 10;
    const distance = item.distanceKm;
    if (distance != null && distance <= 1) score += 20;
    else if (distance != null && distance <= 3) score += 10;
    return score;
  }

  function candidateFromPage(page, method) {
    const info = (page.imageinfo || [])[0] || {};
    const meta = info.extmetadata || {};
    const title = page.title || '';
    const pageCoordinate = (page.coordinates || [])[0];
    const thumbnail = info.thumburl || info.url || '';
    return {
      id: 'commons:' + title.replace(/^File:/, ''),
      fileName: title.replace(/^File:/, ''),
      thumbnailUrl: thumbnail.replace(/\?.*$/, ''),
      imageUrl: (info.url || '').replace(/\?.*$/, ''),
      commonsPageUrl: 'https://commons.wikimedia.org/wiki/' + encodeURIComponent(title.replace(/ /g, '_')),
      author: clean(meta.Artist && meta.Artist.value) || 'author_unknown',
      license: clean(meta.LicenseShortName && meta.LicenseShortName.value) || 'license_unknown',
      licenseUrl: clean(meta.LicenseUrl && meta.LicenseUrl.value) || null,
      description: clean(meta.ImageDescription && meta.ImageDescription.value),
      categories: clean(meta.Categories && meta.Categories.value),
      width: Number(info.width) || 0,
      height: Number(info.height) || 0,
      mimeType: info.mime || '',
      fileSize: Number(info.size) || 0,
      coordinate: pageCoordinate ? { lat: Number(pageCoordinate.lat), lng: Number(pageCoordinate.lon) } : null,
      method,
      source: 'wikimedia_commons',
      sourceName: 'Wikimedia Commons',
      sourceId: 'commons:' + normalizeIdentity(title),
      acquiredAt: new Date().toISOString(),
      status: 'pending'
    };
  }

  async function commonsFiles(params, method) {
    const data = await api(COMMONS_API, Object.assign({
      action: 'query',
      formatversion: 2,
      prop: 'imageinfo|coordinates|categories',
      iiprop: 'url|size|mime|extmetadata',
      iiurlwidth: 1600,
      colimit: 50
    }, params));
    return (((data || {}).query || {}).pages || [])
      .filter((page) => page.imageinfo)
      .map((page) => candidateFromPage(page, method));
  }

  // ファイル名の一覧から Commons の情報をまとめて取る（50件ずつ）
  async function commonsByTitles(titles, method) {
    const list = Array.from(new Set(titles.map((t) => 'File:' + String(t).replace(/^(File|ファイル|画像):/i, ''))));
    let out = [];
    for (let i = 0; i < list.length; i += 40) {
      out = out.concat(await commonsFiles({ titles: list.slice(i, i + 40).join('|') }, method));
    }
    return out;
  }

  function wikidataEntityScore(entity, searchHit, mountain, name) {
    let score = 0;
    const labelJa = (((entity.labels || {}).ja || {}).value || '').trim();
    const description = [
      searchHit && searchHit.description,
      ((entity.descriptions || {}).ja || {}).value,
      ((entity.descriptions || {}).en || {}).value
    ].filter(Boolean).join(' ').toLowerCase();
    if (labelJa === String(name || '').trim()) score += 35;
    if (/山|岳|峰|mountain|mount|peak|summit|hill/.test(description)) score += 30;
    if (/駅|station|railway|学校|school|人|person|company|企業/.test(description)) score -= 60;

    const claim = (((entity.claims || {}).P625 || [])[0] || {}).mainsnak;
    const value = claim && claim.datavalue && claim.datavalue.value;
    const entityCoordinate = value ? { lat: Number(value.latitude), lng: Number(value.longitude) } : null;
    const distance = distanceKm(coordinate(mountain), entityCoordinate);
    if (distance != null && distance <= 5) score += 100;
    else if (distance != null && distance <= 20) score += 45;
    else if (distance != null && distance > 100) score -= 100;
    if (entityCoordinate && entityCoordinate.lat >= 20 && entityCoordinate.lat <= 46
      && entityCoordinate.lng >= 122 && entityCoordinate.lng <= 154) score += 10;
    return score;
  }

  async function findWikidataMountain(mountain, name) {
    const search = await api(WIKIDATA_API, {
      action: 'wbsearchentities',
      search: name,
      language: 'ja',
      uselang: 'ja',
      limit: 8
    });
    const hits = search.search || [];
    if (!hits.length) return null;

    const entitiesResult = await api(WIKIDATA_API, {
      action: 'wbgetentities',
      ids: hits.map((hit) => hit.id).join('|'),
      props: 'labels|descriptions|claims|sitelinks',
      languages: 'ja|en'
    });
    const entities = entitiesResult.entities || {};
    const ranked = hits.map((hit) => ({
      hit,
      entity: entities[hit.id],
      score: entities[hit.id] ? wikidataEntityScore(entities[hit.id], hit, mountain, name) : -999
    })).sort((a, b) => b.score - a.score);

    // 位置の合わない同じ名前の山を取らない（座標が5km以内か、名前と「山」の説明の両方が合うもの）
    if (!ranked[0] || ranked[0].score < 65) return null;
    return ranked[0].entity;
  }

  function claimValue(entity, prop) {
    const snak = (((entity.claims || {})[prop] || [])[0] || {}).mainsnak;
    return snak && snak.datavalue && snak.datavalue.value;
  }

  // Openverse：Flickr などの CC ライセンスの写真をまとめて探せる（鍵なし・ブラウザから使える）。商用利用と改変ができるものだけ
  const OV_LICENSE = { by: 'CC BY', 'by-sa': 'CC BY-SA', cc0: 'CC0', pdm: 'Public Domain Mark' };
  async function openverseSearch(query) {
    const params = new URLSearchParams({ q: query, license_type: 'commercial,modification', page_size: '20', mature: 'false' });
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(OPENVERSE_API + '?' + params.toString(), { signal: controller.signal, headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error('Openverse ' + response.status);
      return (await response.json()).results || [];
    } finally {
      clearTimeout(timer);
    }
  }

  function candidateFromOpenverse(r) {
    const license = (OV_LICENSE[r.license] || String(r.license || '').toUpperCase()) + (r.license_version && !/cc0|pdm/.test(r.license) ? ' ' + r.license_version : '');
    return {
      id: 'flickr:' + r.id,
      fileName: r.title || '(無題)',
      thumbnailUrl: r.url,
      imageUrl: r.url,
      commonsPageUrl: null,
      sourcePageUrl: r.foreign_landing_url,
      author: r.creator || 'author_unknown',
      license,
      licenseUrl: r.license_url || null,
      description: r.title || '',
      categories: '',
      tags: (r.tags || []).map((t) => t.name).join(' '),
      width: Number(r.width) || 0,
      height: Number(r.height) || 0,
      mimeType: 'image/jpeg',
      fileSize: Number(r.filesize) || 0,
      coordinate: null,
      method: 'openverse_flickr',
      source: 'flickr',
      sourceName: 'Flickr',
      sourceId: 'flickr:' + String(r.foreign_landing_url || r.id).replace(/\/+$/, '').split('/').pop(),
      openverseId: r.id,
      acquiredAt: new Date().toISOString(),
      status: 'pending'
    };
  }

  async function refreshOpenverseLicense(item) {
    const response = await fetch(OPENVERSE_API + encodeURIComponent(item.openverseId) + '/', { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(item.fileName + 'の元画像情報を再確認できませんでした（Openverse ' + response.status + '）。');
    const latest = candidateFromOpenverse(await response.json());
    const refreshed = Object.assign({}, item, {
      author: latest.author, license: latest.license, licenseUrl: latest.licenseUrl, sourcePageUrl: latest.sourcePageUrl,
      licenseVerifiedAt: new Date().toISOString(), licenseVerification: 'automatic_metadata_check_at_publish'
    });
    const check = evaluateLicense(refreshed);
    if (!check.ok) throw new Error(item.fileName + 'は採用できません: ' + check.reason);
    return refreshed;
  }

  function readCandidateCache() {
    try { return JSON.parse(localStorage.getItem(CACHE_KEY) || '{}'); }
    catch (_) { return {}; }
  }

  function cachedCandidates(id) {
    const entry = readCandidateCache()[id];
    if (!entry || Date.now() - entry.savedAt > CACHE_TTL || !Array.isArray(entry.items)) return null;
    return entry;
  }

  function saveCandidateCache(id, items, excluded, summary) {
    const cache = readCandidateCache();
    cache[id] = { savedAt: Date.now(), items, excluded, summary };
    const newest = Object.entries(cache)
      .sort((a, b) => (b[1].savedAt || 0) - (a[1].savedAt || 0))
      .slice(0, 20);
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(Object.fromEntries(newest))); }
    catch (_) { /* 容量超過時はキャッシュなしで継続 */ }
  }

  async function getCandidates(forceRefresh) {
    const mountain = currentMountain();
    if (!mountain) return;
    const cached = !forceRefresh && cachedCandidates(mountain.id);
    if (cached) {
      state.candidates = cached.items;
      state.excluded = cached.excluded || [];
      renderCandidates();
      setStatus(cached.items.length + '件の保存済み候補を表示しました（除外 ' + state.excluded.length + '件）。再検索する場合はもう一度ボタンを押してください。', 'ok');
      $('find').textContent = '候補を再取得';
      return;
    }

    $('find').disabled = true;
    $('find').textContent = '検索中…';
    const variants = nameVariants(mountain);
    const center = coordinate(mountain);
    const counts = {};
    const failures = [];
    let all = [];
    // 1つの検索元が失敗しても、ほかの検索元の候補は出す
    const step = async (label, fn) => {
      setStatus(label + 'を検索しています…', 'ok');
      try {
        const got = await fn();
        counts[label] = (counts[label] || 0) + got.length;
        all = all.concat(got);
      } catch (error) {
        failures.push(label + '（' + error.message + '）');
      }
    };
    try {
      const entities = [];
      for (const name of variants.ja.slice(0, 3)) {
        await step('Wikidata', async () => {
          const entity = await findWikidataMountain(mountain, name);
          if (!entity || entities.some((e) => e.id === entity.id)) return [];
          entities.push(entity);
          const got = [];
          const p18 = claimValue(entity, 'P18');
          if (p18) got.push(...await commonsFiles({ titles: 'File:' + p18 }, 'wikidata_p18'));
          const category = claimValue(entity, 'P373');
          if (category) {
            got.push(...await commonsFiles({ generator: 'categorymembers', gcmtitle: 'Category:' + category, gcmtype: 'file', gcmlimit: 40 }, 'wikidata_category'));
          }
          return got;
        });
      }
      await step('Wikipedia', async () => {
        const titles = entities.map((e) => ((e.sitelinks || {}).jawiki || {}).title).filter(Boolean);
        variants.ja.slice(0, 3).forEach((v) => { if (!titles.includes(v)) titles.push(v); });
        const data = await api(JAWIKI_API, { action: 'query', titles: titles.join('|'), prop: 'images', imlimit: 60, redirects: 1 });
        const pages = Object.values(((data || {}).query || {}).pages || {});
        const files = [];
        pages.forEach((p) => (p.images || []).forEach((im) => { if (/\.(jpe?g|png|webp)$/i.test(im.title)) files.push(im.title); }));
        return files.length ? commonsByTitles(files, 'wikipedia_article') : [];
      });
      const queries = [];
      variants.ja.forEach((v) => { queries.push(v); queries.push(v + ' 山頂'); });
      variants.roman.forEach((r) => { queries.push('Mount ' + r.base); queries.push(r.full); });
      if (variants.generic) variants.context.slice(0, 2).forEach((c) => variants.ja.forEach((v) => queries.push(v + ' ' + c)));
      for (const q of Array.from(new Set(queries)).slice(0, 8)) {
        await step('Commons', () => commonsFiles({ generator: 'search', gsrsearch: q, gsrnamespace: 6, gsrlimit: 20 }, 'commons_name'));
      }
      if (center) {
        await step('Commons（山頂付近）', () => commonsFiles({
          generator: 'geosearch', ggsnamespace: 6, ggscoord: center.lat + '|' + center.lng, ggsradius: 3000, ggslimit: 30
        }, 'commons_geosearch'));
      }
      const ovQueries = variants.ja.slice(0, 3).concat(variants.roman.slice(0, 2).map((r) => 'Mt ' + r.base));
      for (const q of ovQueries) {
        await step('Openverse', async () => {
          const results = await openverseSearch(q);
          const flickr = results.filter((r) => r.source === 'flickr').map(candidateFromOpenverse);
          // Openverse にある Commons の写真は、Commons から作者・ライセンスを取り直す
          const commonsTitles = results.filter((r) => r.source === 'wikimedia' && r.foreign_landing_url)
            .map((r) => { try { return decodeURIComponent(new URL(r.foreign_landing_url).pathname.split('/').pop()); } catch (_) { return ''; } })
            .filter((t) => /^File:/i.test(t));
          const commons = commonsTitles.length ? await commonsByTitles(commonsTitles, 'openverse_commons') : [];
          return flickr.concat(commons);
        });
      }

      const unique = {};
      const rank = { wikidata_p18: 5, wikidata_category: 4, wikipedia_article: 3, commons_geosearch: 2 };
      all.forEach((item) => {
        const key = item.sourceId || item.fileName.toLowerCase();
        const prev = unique[key];
        if (!prev || (rank[item.method] || 0) > (rank[prev.method] || 0)) unique[key] = item;
      });
      const kept = [];
      const excluded = [];
      Object.values(unique).forEach((item) => {
        item.distanceKm = distanceKm(center, item.coordinate);
        item.score = scoreCandidate(item, mountain, variants);
        item.licenseCheck = evaluateLicense(item);
        const reason = relevanceProblem(item, mountain, variants) || qualityProblem(item)
          || (item.licenseCheck.ok ? '' : 'ライセンス：' + item.licenseCheck.label);
        if (reason) { item.excludedReason = reason; excluded.push(item); } else kept.push(item);
      });
      kept.sort((a, b) => b.score - a.score);
      // 連番の同じような写真（「…route 6 (66753).jpg」など）は2枚まで。残りは除外に回す
      const series = {};
      for (let i = kept.length - 1; i >= 0; i -= 1) {
        const key = kept[i].fileName.toLowerCase().replace(/\.[a-z]+$/, '').replace(/[\s_-]*[(（]?\d+[)）]?$/, '').replace(/\d{3,}/g, '#');
        series[key] = (series[key] || []).concat([i]);
      }
      Object.values(series).forEach((idx) => {
        idx.sort((a, b) => a - b).slice(2).forEach((i) => { kept[i].excludedReason = '同じような連番の写真（3枚目以降）'; });
      });
      kept.filter((item) => item.excludedReason).forEach((item) => excluded.push(item));
      for (let i = kept.length - 1; i >= 0; i -= 1) if (kept[i].excludedReason) kept.splice(i, 1);
      excluded.sort((a, b) => b.score - a.score);

      state.candidates = kept;
      state.excluded = excluded;
      saveCandidateCache(mountain.id, kept, excluded.slice(0, 60));
      renderCandidates();
      const bySource = {};
      kept.forEach((item) => { bySource[item.sourceName] = (bySource[item.sourceName] || 0) + 1; });
      const summary = Object.entries(bySource).map(([k, v]) => k + ' ' + v + '件').join('・') || 'なし';
      setStatus('使える候補 ' + kept.length + '件（' + summary + '）。関係ない・画質が低い・ライセンスが合わない ' + excluded.length + '件は除外しました。'
        + (failures.length ? '\n取得できなかった検索元：' + failures.join('、') : ''), kept.length ? 'ok' : 'warn');
      $('find').textContent = '候補を再取得';
    } catch (error) {
      setStatus('取得に失敗しました。時間をおいて再度お試しください。\n' + error.message, 'err');
      $('find').textContent = '画像候補を取得';
    } finally {
      $('find').disabled = false;
    }
  }

  function methodLabel(method) {
    return {
      wikidata_p18: 'Wikidata代表画像',
      wikidata_category: 'Commonsの山のカテゴリ',
      wikipedia_article: 'Wikipediaの記事',
      commons_name: 'Commons検索',
      commons_english_name: '英語名検索',
      commons_geosearch: '山頂付近（3km以内）',
      openverse_flickr: 'Flickr（Openverse）',
      openverse_commons: 'Commons（Openverse）'
    }[method] || method || '取得元不明';
  }

  function ensureDraft(id) {
    if (state.drafts[id]) return state.drafts[id];
    const mountain = state.mountains.find((item) => String(item.id) === String(id));
    const paths = Array.isArray(mountain && mountain.photos) ? mountain.photos.slice() : [];
    const creditItems = Array.isArray(state.credits[id]) ? state.credits[id] : [];
    const draft = paths.map((path, index) => {
      const credit = creditItems.find((item) => item.localPath === path) || creditItems[index] || {};
      return Object.assign({}, credit, {
        id: 'published:' + path,
        localPath: path,
        thumbnailUrl: path,
        imageUrl: path,
        fileName: credit.fileName || path.split('/').pop(),
        author: credit.author || 'クレジット未登録',
        license: credit.license || (credit.source === 'own' ? '自前写真' : 'license_unknown'),
        source: credit.source || 'existing',
        status: 'published'
      });
    });
    state.drafts[id] = draft;
    state.originalPaths[id] = paths;
    return draft;
  }

  function draftFingerprint(id) {
    return ensureDraft(id).map((item) => item.status === 'published' ? item.localPath : item.id);
  }

  function hasChanges(id) {
    if (!id) return false;
    return JSON.stringify(draftFingerprint(id)) !== JSON.stringify(state.originalPaths[id] || []);
  }

  function updateControls() {
    const hasMountain = Boolean(currentMountain());
    const analysis = hasMountain ? duplicateAnalysis(ensureDraft(state.currentId)) : { extras: new Set() };
    const duplicateCount = analysis.extras.size;
    $('find').disabled = !hasMountain;
    $('publish').disabled = !hasMountain || !hasChanges(state.currentId) || duplicateCount > 0;
    $('reset').disabled = !hasMountain || !hasChanges(state.currentId);
    $('dedupe').hidden = duplicateCount === 0;
    $('dedupe').disabled = duplicateCount === 0;
    if (duplicateCount) {
      setStatus('同じ写真が' + duplicateCount + '枚重複しています。「重複を整理」を押すと、先頭の1枚だけを残します。', 'warn', 'duplicate-notice');
    } else {
      setStatus('', 'ok', 'duplicate-notice');
    }
    const mountain = currentMountain();
    if (mountain) {
      const published = photoCount(mountain);
      const after = ensureDraft(mountain.id).length;
      $('mountain-summary').textContent = 'サイト採用中 ' + published + '枚　→　変更後 ' + after + '枚';
    }
  }

  function renderMountainOptions() {
    const selected = state.currentId;
    $('mountain').innerHTML = '';
    state.mountains.forEach((mountain) => {
      const option = document.createElement('option');
      option.value = mountain.id;
      option.textContent = mountain.name + '（採用中 ' + photoCount(mountain) + '枚）';
      if (String(mountain.id) === String(selected)) option.selected = true;
      $('mountain').appendChild(option);
    });
    $('mountain').disabled = false;
  }

  function candidateCard(item, draft, excludedView) {
    const check = evaluateLicense(item);
    const added = draft.some((selected) => sameImage(selected, item));
    const pageUrl = safeUrl(item.commonsPageUrl || item.sourcePageUrl);
    const imageUrl = safeUrl(item.thumbnailUrl);
    const usable = check.ok && !excludedView;
    const card = document.createElement('article');
    card.className = 'candidate-card' + (added ? ' is-added' : '') + (excludedView ? ' is-excluded' : '');
    card.innerHTML =
      '<img src="' + esc(imageUrl) + '" alt="' + esc(item.fileName) + '" loading="lazy" referrerpolicy="no-referrer">' +
      '<div class="candidate-body">' +
        '<div class="badges">' +
          '<span class="badge">' + esc(item.score) + '点</span>' +
          '<span class="badge">' + esc(methodLabel(item.method)) + '</span>' +
          (excludedView ? '<span class="badge warn">除外：' + esc(item.excludedReason || '') + '</span>'
            : '<span class="badge ' + (check.ok ? 'ok' : 'warn') + '">' + esc(check.label) + '</span>') +
        '</div>' +
        '<p><strong>' + esc(item.fileName) + '</strong></p>' +
        '<p>作者：' + esc(item.author) + '</p>' +
        '<p>ライセンス：' + esc(item.license) + '</p>' +
        '<p>解像度：' + esc(item.width || '?') + ' × ' + esc(item.height || '?') + ' px'
          + (item.distanceKm != null ? '・山頂から' + esc(item.distanceKm.toFixed(1)) + 'km' : '') + '</p>' +
        (pageUrl ? '<a class="source-link" href="' + esc(pageUrl) + '" target="_blank" rel="noopener">元画像ページを開く（' + esc(item.sourceName || 'Wikimedia Commons') + '）↗</a>' : '') +
        (excludedView ? '' : '<button type="button" ' + (!usable || added ? 'disabled' : '') + '>' +
          (added ? '採用画像に追加済み' : usable ? '採用画像に追加' : '採用できません') + '</button>') +
      '</div>';
    const button = card.querySelector('button');
    if (button) button.addEventListener('click', () => addCandidate(item));
    return card;
  }

  function renderCandidates() {
    const mountain = currentMountain();
    $('candidate-title').textContent = mountain ? mountain.name + ' の写真の候補' : '写真の候補を探す';
    const container = $('candidates');
    container.innerHTML = '';
    if (!state.candidates.length && !state.excluded.length) return;
    const draft = ensureDraft(state.currentId);
    state.candidates.forEach((item) => container.appendChild(candidateCard(item, draft, false)));
    if (state.excluded.length) {
      const toggle = document.createElement('div');
      toggle.className = 'excluded-toggle';
      toggle.innerHTML = '<button type="button" class="secondary">' + (state.showExcluded ? '除外した候補を隠す' : '除外した候補を見る（' + state.excluded.length + '件）') + '</button>';
      toggle.querySelector('button').addEventListener('click', () => { state.showExcluded = !state.showExcluded; renderCandidates(); });
      container.appendChild(toggle);
      if (state.showExcluded) state.excluded.forEach((item) => container.appendChild(candidateCard(item, draft, true)));
    }
  }

  function addCandidate(item) {
    const check = evaluateLicense(item);
    if (!check.ok) {
      setStatus(check.reason, 'err');
      return;
    }
    const draft = ensureDraft(state.currentId);
    if (draft.some((selected) => sameImage(selected, item))) {
      setStatus('この写真はすでに採用画像に入っています。同じ元画像は重複登録できません。', 'warn');
      return;
    }
    draft.push(Object.assign({}, item, {
      id: 'candidate:' + item.fileName + ':' + Date.now(),
      status: 'pending',
      selectedAt: new Date().toISOString(),
      licenseVerifiedAt: new Date().toISOString(),
      licenseVerification: 'automatic_metadata_check'
    }));
    renderSelected();
    renderCandidates();
    setStatus('採用画像の末尾に追加しました。表示順を確認してください。', 'ok');
  }

  function renderSelected() {
    const container = $('selected');
    container.innerHTML = '';
    const mountain = currentMountain();
    if (!mountain) {
      container.innerHTML = '<div class="empty-state">山を選択してください。</div>';
      return;
    }
    const draft = ensureDraft(mountain.id);
    const duplicates = duplicateAnalysis(draft);
    if (!draft.length) {
      container.innerHTML = '<div class="empty-state">採用画像はありません。下の候補または自分の写真から追加できます。</div>';
      updateControls();
      return;
    }

    draft.forEach((item, index) => {
      const card = document.createElement('article');
      const sourceLabel = item.source === 'own' ? '自前写真' : item.status === 'published' ? '公開中' : 'Commonsから追加';
      const sourceClass = item.source === 'own' ? 'own' : item.status === 'published' ? 'published' : 'ok';
      const isDuplicate = duplicates.extras.has(index);
      card.className = 'selected-card' + (index === 0 ? ' is-main' : '') + (isDuplicate ? ' is-duplicate' : '');
      card.innerHTML =
        '<img src="' + esc(safeUrl(item.thumbnailUrl || item.localPath)) + '" alt="' + esc(item.fileName || '') + '">' +
        '<div class="order-label">' + (index === 0 ? '1枚目・メイン画像' : (index + 1) + '枚目') + '</div>' +
        '<div class="badges"><span class="badge ' + sourceClass + '">' + sourceLabel + '</span>' +
          (isDuplicate ? '<span class="badge warn">同じ写真・重複</span>' : '') + '</div>' +
        '<div class="filename">' + esc(item.fileName || item.localPath || '') + '</div>' +
        '<div class="order-buttons">' +
          '<button class="move-up" type="button" ' + (index === 0 ? 'disabled' : '') + '>← 前へ</button>' +
          '<button class="move-down" type="button" ' + (index === draft.length - 1 ? 'disabled' : '') + '>後ろへ →</button>' +
          '<button class="remove" type="button">この1枚を削除</button>' +
        '</div>';
      card.querySelector('.move-up').addEventListener('click', () => moveItem(index, -1));
      card.querySelector('.move-down').addEventListener('click', () => moveItem(index, 1));
      card.querySelector('.remove').addEventListener('click', () => removeItem(index));
      container.appendChild(card);
    });
    updateControls();
  }

  function moveItem(index, direction) {
    const draft = ensureDraft(state.currentId);
    const next = index + direction;
    if (next < 0 || next >= draft.length) return;
    [draft[index], draft[next]] = [draft[next], draft[index]];
    renderSelected();
    setStatus('表示順を変更しました。GitHubへ反映するとサイトに反映されます。', 'ok', 'publish-status');
  }

  function removeItem(index) {
    const draft = ensureDraft(state.currentId);
    const item = draft[index];
    if (!item) return;
    const message = item.status === 'published'
      ? 'この公開中の写真を削除予定にしますか？\n「GitHubへ反映」を押すまで実際のサイトからは削除されません。'
      : 'この追加予定の写真を取り消しますか？';
    if (!window.confirm(message)) return;
    draft.splice(index, 1);
    if (item.ownFileKey && state.ownFiles[item.ownFileKey]) {
      URL.revokeObjectURL(item.previewUrl || item.thumbnailUrl);
      delete state.ownFiles[item.ownFileKey];
    }
    renderSelected();
    renderCandidates();
    setStatus('1枚を削除予定にしました。確定するにはGitHubへ反映してください。', 'warn', 'publish-status');
  }

  function dedupeCurrentDraft() {
    const draft = ensureDraft(state.currentId);
    const analysis = duplicateAnalysis(draft);
    if (!analysis.extras.size) return;
    if (!window.confirm('同じ写真を先頭の1枚だけ残し、重複分を削除予定にしますか？\nGitHubへ反映するまでサイトは変更されません。')) return;
    [...analysis.extras].sort((a, b) => b - a).forEach((index) => {
      const item = draft[index];
      draft.splice(index, 1);
      if (item && item.ownFileKey && state.ownFiles[item.ownFileKey]) {
        URL.revokeObjectURL(item.previewUrl || item.thumbnailUrl);
        delete state.ownFiles[item.ownFileKey];
      }
    });
    renderSelected();
    renderCandidates();
    setStatus('重複写真を整理しました。確定するにはGitHubへ反映してください。', 'warn', 'publish-status');
  }

  function resetCurrentDraft() {
    const id = state.currentId;
    if (!id || !hasChanges(id)) return;
    if (!window.confirm('この山で行った追加・削除・並べ替えをすべて元に戻しますか？')) return;
    (state.drafts[id] || []).forEach((item) => {
      if (item.ownFileKey && state.ownFiles[item.ownFileKey]) {
        URL.revokeObjectURL(item.previewUrl || item.thumbnailUrl);
        delete state.ownFiles[item.ownFileKey];
      }
    });
    delete state.drafts[id];
    delete state.originalPaths[id];
    delete state.hashScans[id];
    ensureDraft(id);
    renderSelected();
    renderCandidates();
    scanCurrentImageHashes(id);
    setStatus('変更を元に戻しました。', 'ok', 'publish-status');
  }

  async function sha256Blob(blob) {
    if (!window.crypto || !window.crypto.subtle) throw new Error('このブラウザでは写真の重複確認を利用できません。ブラウザを最新版に更新してください。');
    const digest = await window.crypto.subtle.digest('SHA-256', await blob.arrayBuffer());
    return Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, '0')).join('');
  }

  async function scanCurrentImageHashes(id) {
    if (!id) return;
    if (state.hashScans[id]) return state.hashScans[id];
    state.hashScans[id] = (async () => {
      const draft = ensureDraft(id);
      for (const item of draft) {
        if (item.contentHash || item.status !== 'published' || !item.localPath) continue;
        try {
          const response = await fetch(item.localPath, { cache: 'force-cache' });
          if (!response.ok) continue;
          item.contentHash = await sha256Blob(await response.blob());
        } catch (_) {
          /* 取得できない既存画像はCommons元画像IDで重複判定を継続 */
        }
      }
      if (String(state.currentId) === String(id)) renderSelected();
    })();
    return state.hashScans[id];
  }

  function mb(bytes) {
    return (bytes / 1024 / 1024).toFixed(bytes < 1024 * 1024 ? 2 : 1) + 'MB';
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const tag = document.createElement('script');
      tag.src = src;
      tag.onload = resolve;
      tag.onerror = () => reject(new Error('変換の部品を読み込めませんでした（通信を確かめてください）'));
      document.head.appendChild(tag);
    });
  }

  function loadImage(blob) {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(blob);
      const image = new Image();
      image.onload = () => {
        URL.revokeObjectURL(url);
        resolve(image);
      };
      image.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error('画像として読み込めませんでした'));
      };
      image.src = url;
    });
  }

  function looksHeic(blob, name) {
    return /image\/hei[cf]/i.test(blob.type || '') || /\.(heic|heif)$/i.test(name || '');
  }

  // ブラウザで読める形なら そのまま、読めない HEIC は JPEG に直してから読む
  async function decodeImage(blob, name) {
    try {
      if (window.createImageBitmap) return await createImageBitmap(blob, { imageOrientation: 'from-image' });
    } catch (error) { /* 次の方法で読む */ }
    try {
      return await loadImage(blob);
    } catch (error) { /* HEIC なら変換して読む */ }
    let heic = looksHeic(blob, name);
    if (!heic) {
      // 拡張子が無くても中身が HEIC のことがある（ftyp の heic / heix / mif1 など）
      const head = new Uint8Array(await blob.slice(0, 16).arrayBuffer());
      const brand = String.fromCharCode.apply(null, Array.prototype.slice.call(head, 4, 12));
      heic = /^ftyp(hei|hev|mif1|msf1|avif)/.test(brand);
    }
    if (!heic) throw new Error(name + 'を画像として読み込めませんでした（JPEG・PNG・WebP・HEIC に対応）');
    if (!window.HeicTo) await loadScript(HEIC_LIB);
    const jpeg = await window.HeicTo({ blob, type: 'image/jpeg', quality: 0.95 });
    return loadImage(jpeg);
  }

  let webpEncoder = null;
  async function encodeWebpWasm(imageData) {
    if (!webpEncoder) {
      webpEncoder = import(WEBP_ENC).then((mod) => mod.default({ noInitialRun: true }));
    }
    const module = await webpEncoder;
    const result = module.encode(imageData.data, imageData.width, imageData.height, WEBP_OPTIONS);
    if (!result) throw new Error('WebP に変換できませんでした');
    return new Blob([result], { type: 'image/webp' });
  }

  // 長辺1600pxに縮め、WebP にする（大きくなるときは縮めるだけ）。自前の写真・Commons の写真の両方で使う
  async function optimizePhoto(blob, name) {
    if (blob.size > 50 * 1024 * 1024) throw new Error(name + 'は50MBを超えているため追加できません。');
    const image = await decodeImage(blob, name);
    let width = image.naturalWidth || image.width;
    let height = image.naturalHeight || image.height;
    if (!width || !height) throw new Error(name + 'のサイズを確認できませんでした。');
    const scale = Math.min(1, PHOTO_MAX_EDGE / Math.max(width, height));
    width = Math.max(1, Math.round(width * scale));
    height = Math.max(1, Math.round(height * scale));
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d');
    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, width, height);
    context.imageSmoothingQuality = 'high';
    context.drawImage(image, 0, 0, width, height);
    if (image.close) image.close();
    let out = await new Promise((resolve) => canvas.toBlob(resolve, 'image/webp', WEBP_QUALITY / 100));
    if (!out || out.type !== 'image/webp') {
      try {
        out = await encodeWebpWasm(context.getImageData(0, 0, width, height));
      } catch (error) {
        out = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY));
      }
    }
    if (!out) throw new Error(name + 'を変換できませんでした。');
    const format = out.type === 'image/webp' ? 'WebP' : 'JPEG';
    return {
      blob: out,
      width,
      height,
      format,
      note: '長辺' + PHOTO_MAX_EDGE + 'pxの' + format + 'に変換',
      summary: name + '：' + mb(blob.size) + ' → ' + mb(out.size) + '（' + width + '×' + height + '・' + format + '）'
    };
  }

  function selectedOwnFiles() {
    return [...$('own-files').files, ...$('camera-file').files];
  }

  async function addOwnPhotos() {
    const mountain = currentMountain();
    if (!mountain) return setStatus('先に山を選択してください。', 'err', 'own-status');
    const files = selectedOwnFiles();
    if (!files.length) return setStatus('写真ライブラリまたはカメラから写真を選んでください。', 'err', 'own-status');
    const author = $('own-author').value.trim();
    if (!author) return setStatus('クレジット表示に使う撮影者名を入力してください。', 'err', 'own-status');
    localStorage.setItem('ym_own_photo_author', author);
    $('add-own').disabled = true;
    setStatus(files.length + '枚をサイト用に調整しています…', 'ok', 'own-status');

    let added = 0;
    const errors = [];
    const summaries = [];
    const draft = ensureDraft(mountain.id);
    for (const file of files) {
      try {
        const converted = await optimizePhoto(file, file.name);
        summaries.push(converted.summary);
        const contentHash = await sha256Blob(converted.blob);
        if (draft.some((item) => sameImage(item, { contentHash }))) {
          errors.push(file.name + 'はすでに採用画像に入っている同じ写真です。');
          continue;
        }
        const key = 'own-' + Date.now() + '-' + Math.random().toString(16).slice(2);
        const preview = URL.createObjectURL(converted.blob);
        state.ownFiles[key] = converted.blob;
        draft.push({
          id: key,
          ownFileKey: key,
          fileName: file.name.replace(/\.[^.]+$/, '') + (converted.format === 'WebP' ? '.webp' : '.jpg'),
          thumbnailUrl: preview,
          imageUrl: preview,
          previewUrl: preview,
          author,
          license: 'YAMATCH自前写真',
          licenseUrl: null,
          commonsPageUrl: null,
          source: 'own',
          status: 'pending',
          width: converted.width,
          height: converted.height,
          mimeType: converted.blob.type,
          contentHash,
          selectedAt: new Date().toISOString(),
          modifications: converted.note
        });
        added += 1;
      } catch (error) {
        errors.push(error.message);
      }
    }
    $('own-files').value = '';
    $('camera-file').value = '';
    $('add-own').disabled = false;
    renderSelected();
    const message = added + '枚を採用画像の末尾に追加しました（下の「この山の変更をGitHubへ反映」を押すとサイトに載ります）。'
      + (summaries.length ? '\n' + summaries.join('\n') : '') + (errors.length ? '\n追加できなかった写真：' + errors.join(' / ') : '');
    setStatus(message, errors.length ? 'warn' : 'ok', 'own-status');
  }

  function encodeBase64(text) {
    const bytes = new TextEncoder().encode(text);
    let binary = '';
    const size = 0x8000;
    for (let i = 0; i < bytes.length; i += size) {
      binary += String.fromCharCode(...bytes.subarray(i, i + size));
    }
    return btoa(binary);
  }

  function decodeBase64(text) {
    const binary = atob(String(text || '').replace(/\n/g, ''));
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return new TextDecoder().decode(bytes);
  }

  async function blobBase64(blob) {
    const bytes = new Uint8Array(await blob.arrayBuffer());
    let binary = '';
    const size = 0x8000;
    for (let i = 0; i < bytes.length; i += size) {
      binary += String.fromCharCode(...bytes.subarray(i, i + size));
    }
    let extension = '.jpg';
    if (blob.type === 'image/png') extension = '.png';
    else if (blob.type === 'image/webp') extension = '.webp';
    else if (blob.type === 'image/gif') extension = '.gif';
    return { content: btoa(binary), extension };
  }

  function githubHeaders(token) {
    return {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28'
    };
  }

  function githubUrl(path) {
    const encoded = path.split('/').map(encodeURIComponent).join('/');
    return 'https://api.github.com/repos/' + OWNER + '/' + REPO + '/contents/' + encoded;
  }

  async function getRepoFile(path, token, allowMissing) {
    const response = await fetch(githubUrl(path), { headers: githubHeaders(token) });
    if (allowMissing && response.status === 404) return null;
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(path + 'の取得に失敗しました（' + response.status + '）' + (detail.message ? ': ' + detail.message : ''));
    }
    return response.json();
  }

  async function getRepoText(path, token, allowMissing) {
    const file = await getRepoFile(path, token, allowMissing);
    if (!file) return null;
    // 1MBを超えるファイル（mountains.json など）は content が空で返るので、生のまま取り直す
    if (file.encoding === 'none' || (!file.content && file.size > 0)) {
      const response = await fetch(githubUrl(path), {
        headers: Object.assign({}, githubHeaders(token), { Accept: 'application/vnd.github.raw+json' }),
        cache: 'no-store'
      });
      if (!response.ok) throw new Error(path + 'の取得に失敗しました（' + response.status + '）');
      return response.text();
    }
    return decodeBase64(file.content);
  }

  async function putRepoFile(path, content, message, token, attempt) {
    attempt = attempt || 1;
    const MAX_ATTEMPTS = 3;
    try {
      const existing = await getRepoFile(path, token, true);
      const body = { message, content };
      if (existing && existing.sha) body.sha = existing.sha;
      const response = await fetch(githubUrl(path), {
        method: 'PUT',
        headers: Object.assign({}, githubHeaders(token), { 'Content-Type': 'application/json' }),
        body: JSON.stringify(body)
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        const retryable = response.status >= 500 || response.status === 429 || response.status === 0;
        if (retryable && attempt < MAX_ATTEMPTS) {
          await wait(800 * attempt);
          return putRepoFile(path, content, message, token, attempt + 1);
        }
        throw new Error(path + 'の保存に失敗しました（' + response.status + '）' + (detail.message ? ': ' + detail.message : ''));
      }
      return response.json();
    } catch (error) {
      if (error instanceof TypeError && attempt < MAX_ATTEMPTS) {
        // ネットワーク断・タイムアウトなど(fetch自体が例外を投げるケース)は再試行する
        await wait(800 * attempt);
        return putRepoFile(path, content, message, token, attempt + 1);
      }
      throw error;
    }
  }

  async function deleteRepoFile(path, message, token) {
    const existing = await getRepoFile(path, token, true);
    if (!existing) return;
    const response = await fetch(githubUrl(path), {
      method: 'DELETE',
      headers: Object.assign({}, githubHeaders(token), { 'Content-Type': 'application/json' }),
      body: JSON.stringify({ message, sha: existing.sha })
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(path + 'の画像ファイル削除に失敗しました' + (detail.message ? ': ' + detail.message : ''));
    }
  }

  async function downloadCommonsImage(item) {
    const urls = [item.thumbnailUrl, item.imageUrl].map(safeUrl).filter(Boolean);
    let lastError = null;
    for (const url of urls) {
      try {
        const response = await fetch(url, { referrerPolicy: 'no-referrer' });
        if (!response.ok) throw new Error('画像取得 ' + response.status);
        return response.blob();
      } catch (error) {
        lastError = error;
      }
    }
    throw new Error(item.fileName + 'のダウンロードに失敗しました' + (lastError ? ': ' + lastError.message : ''));
  }

  async function refreshCommonsLicense(item) {
    const latest = await commonsFiles({ titles: 'File:' + item.fileName }, item.method || 'commons_name');
    if (!latest.length) throw new Error(item.fileName + 'の元画像情報を再確認できませんでした。');
    const refreshed = Object.assign({}, item, latest[0], {
      id: item.id,
      status: 'pending',
      selectedAt: item.selectedAt,
      licenseVerifiedAt: new Date().toISOString(),
      licenseVerification: 'automatic_metadata_check_at_publish'
    });
    const check = evaluateLicense(refreshed);
    if (!check.ok) throw new Error(item.fileName + 'は採用できません: ' + check.reason);
    return refreshed;
  }

  function creditFromItem(item) {
    return {
      fileName: item.fileName,
      localPath: item.localPath,
      author: item.author,
      license: item.license,
      licenseUrl: item.licenseUrl || null,
      commonsPageUrl: item.commonsPageUrl || null,
      sourcePageUrl: item.commonsPageUrl || item.sourcePageUrl || null,
      source: item.source,
      sourceName: item.sourceName || null,
      sourceId: commonsIdentity(item) || item.sourceId || null,
      contentHash: item.contentHash || null,
      licenseVerification: item.source === 'own' ? 'own_photo' : (item.licenseVerification || 'automatic_metadata_check'),
      licenseVerifiedAt: item.licenseVerifiedAt || new Date().toISOString(),
      selectedAt: item.selectedAt || new Date().toISOString(),
      modifications: item.modifications || (item.source === 'wikimedia_commons' ? 'Wikimedia Commonsの1600pxサムネイルを使用' : null)
    };
  }

  function makeImagePath(mountainId, extension) {
    const stamp = new Date().toISOString().replace(/\D/g, '').slice(0, 17);
    const random = Math.random().toString(36).slice(2, 7);
    return 'images/mountains/' + mountainId + '/image-' + stamp + '-' + random + extension;
  }

  async function ensureCreditScriptTag(mountainId, token) {
    const pagePath = 'mountains/' + mountainId + '/index.html';
    const html = await getRepoText(pagePath, token, false);
    const tag = '<script defer src="/scripts/photo-credits.js"></script>';
    if (html.includes('/scripts/photo-credits.js')) return;
    const updated = html.includes('</head>') ? html.replace('</head>', tag + '\n</head>') : tag + '\n' + html;
    await putRepoFile(pagePath, encodeBase64(updated), '[images] 写真クレジット表示を追加', token);
  }

  async function publishChanges() {
    const mountain = currentMountain();
    if (!mountain || !hasChanges(mountain.id)) return;
    const token = localStorage.getItem('ym_gh_token');
    if (!token) {
      setStatus('GitHub トークンがこの端末にありません。開いた画面で設定すると、続けて反映します。', 'err', 'publish-status');
      window.YmGhToken.open({ reason: 'この端末にトークンがありません。保存すると、続けて反映します。', onSaved: publishChanges });
      return;
    }

    $('publish').disabled = true;
    $('mountain').disabled = true;
    const draft = ensureDraft(mountain.id);
    const warnings = [];
    try {
      await scanCurrentImageHashes(mountain.id);
      if (duplicateAnalysis(draft).extras.size) {
        throw new Error('同じ写真が重複しています。先に「重複を整理」を押してください。');
      }
      setStatus('GitHub上の最新データを確認しています…', 'ok', 'publish-status');
      const mountainText = await getRepoText('data/mountains.json', token, false);
      const creditText = await getRepoText('data/image-credits.json', token, true);
      const remoteMountains = JSON.parse(mountainText);
      const remoteCredits = creditText ? JSON.parse(creditText) : {};
      const remoteMountain = remoteMountains.find((item) => String(item.id) === String(mountain.id));
      if (!remoteMountain) throw new Error(mountain.name + 'がGitHub上の山データに見つかりません。');
      const remotePaths = Array.isArray(remoteMountain.photos) ? remoteMountain.photos : [];
      if (JSON.stringify(remotePaths) !== JSON.stringify(state.originalPaths[mountain.id] || [])) {
        throw new Error('この画面を開いた後にGitHub側の画像が更新されています。ページを再読み込みして、最新状態からやり直してください。');
      }

      setStatus('追加画像のライセンスを再確認しています…', 'ok', 'publish-status');
      for (let index = 0; index < draft.length; index += 1) {
        const item = draft[index];
        if (item.status !== 'pending') continue;
        if (item.source === 'wikimedia_commons') {
          draft[index] = await refreshCommonsLicense(item);
        } else if (item.source === 'flickr') {
          draft[index] = await refreshOpenverseLicense(item);
        } else if (item.source === 'own') {
          if (!state.ownFiles[item.ownFileKey]) throw new Error(item.fileName + 'を再選択してください。ページを閉じると未反映の自前写真は消えます。');
          const check = evaluateLicense(item);
          if (!check.ok) throw new Error(check.reason);
        }
      }

      if (duplicateAnalysis(draft).extras.size) {
        throw new Error('同じCommons元画像が重複しています。先に「重複を整理」を押してください。');
      }

      setStatus('追加画像の内容が重複していないか確認しています…', 'ok', 'publish-status');
      const preparedUploads = [];
      for (let index = 0; index < draft.length; index += 1) {
        const item = draft[index];
        if (item.status !== 'pending') continue;
        let blob = item.source === 'own' ? state.ownFiles[item.ownFileKey] : null;
        if (!blob) {
          // Commons の写真も長辺1600pxの WebP にしてから保存する（2026-11-05〜）
          const converted = await optimizePhoto(await downloadCommonsImage(item), item.fileName);
          blob = converted.blob;
          item.modifications = (item.sourceName || 'Wikimedia Commons') + 'の画像を' + converted.note;
          item.contentHash = null;
        }
        item.contentHash = item.contentHash || await sha256Blob(blob);
        const binary = await blobBase64(blob);
        preparedUploads.push({ item, binary });
      }
      if (duplicateAnalysis(draft).extras.size) {
        renderSelected();
        throw new Error('画像内容が同じ写真を検出しました。「重複を整理」を押してから反映してください。');
      }

      setStatus('新しい画像をGitHubへ保存しています…', 'ok', 'publish-status');
      for (const prepared of preparedUploads) {
        const item = prepared.item;
        const binary = prepared.binary;
        const path = makeImagePath(mountain.id, binary.extension);
        await putRepoFile(path, binary.content, '[images] ' + mountain.name + 'の写真を追加', token);
        item.localPath = '/' + path;
        item.thumbnailUrl = '/' + path;
        item.imageUrl = '/' + path;
        item.status = 'published';
      }

      const finalPaths = draft.map((item) => item.localPath);
      const removedPaths = (state.originalPaths[mountain.id] || []).filter((path) => !finalPaths.includes(path));
      remoteMountain.photos = finalPaths;
      remoteCredits[mountain.id] = draft.map(creditFromItem);

      setStatus('山データを更新しています…', 'ok', 'publish-status');
      await putRepoFile('data/mountains.json', encodeBase64(JSON.stringify(remoteMountains, null, 2)), '[images] ' + mountain.name + 'の画像順を更新', token);
      setStatus('写真クレジットを更新しています…', 'ok', 'publish-status');
      await putRepoFile('data/image-credits.json', encodeBase64(JSON.stringify(remoteCredits, null, 2)), '[images] ' + mountain.name + 'の写真クレジットを更新', token);
      try {
        await ensureCreditScriptTag(mountain.id, token);
      } catch (error) {
        warnings.push('クレジット表示タグ: ' + error.message);
      }

      for (const localPath of removedPaths) {
        const repoPath = String(localPath).replace(/^\//, '');
        const allowedPrefix = 'images/mountains/' + mountain.id + '/';
        const usedElsewhere = remoteMountains.some((item) => String(item.id) !== String(mountain.id)
          && Array.isArray(item.photos) && item.photos.includes(localPath));
        if (!repoPath.startsWith(allowedPrefix) || usedElsewhere) continue;
        try {
          await deleteRepoFile(repoPath, '[images] ' + mountain.name + 'の不要画像を削除', token);
        } catch (error) {
          warnings.push(error.message);
        }
      }

      draft.forEach((item) => {
        if (item.ownFileKey && state.ownFiles[item.ownFileKey]) {
          URL.revokeObjectURL(item.previewUrl || item.thumbnailUrl);
          delete state.ownFiles[item.ownFileKey];
        }
        item.id = 'published:' + item.localPath;
        item.ownFileKey = null;
        item.previewUrl = null;
        item.status = 'published';
        item.thumbnailUrl = item.localPath;
        item.imageUrl = item.localPath;
      });
      mountain.photos = finalPaths.slice();
      state.credits[mountain.id] = remoteCredits[mountain.id];
      state.originalPaths[mountain.id] = finalPaths.slice();
      renderMountainOptions();
      renderSelected();
      renderCandidates();
      const finalMessage = 'GitHubへ反映しました。公開サイトの更新には通常1〜2分かかります。'
        + (warnings.length ? '\n画像データの反映は完了しましたが、次を確認してください：\n' + warnings.join('\n') : '');
      setStatus(finalMessage, warnings.length ? 'warn' : 'ok', 'publish-status');
    } catch (error) {
      if (/（401）/.test(error.message)) {
        setStatus('GitHub トークンの期限が切れています。開いた画面で更新すると、続けて反映します（写真の選び直しは不要です）。', 'err', 'publish-status');
        window.YmGhToken.paint('expired');
        window.YmGhToken.open({ reason: 'トークンの期限が切れています。更新すると、続けて反映します。', onSaved: publishChanges });
        return;
      }
      setStatus('反映に失敗しました。\n' + error.message + '\n\n※画像ファイル自体は保存済みの可能性があります。もう一度「この山の変更をGitHubへ反映」を押してください（写真の選び直しは不要です）。', 'err', 'publish-status');
    } finally {
      $('mountain').disabled = false;
      updateControls();
    }
  }

  async function fetchJson(path, fallback) {
    const response = await fetch(path, { cache: 'no-store' });
    if (!response.ok) {
      if (fallback !== undefined) return fallback;
      throw new Error(path + 'を読み込めませんでした（' + response.status + '）');
    }
    return response.json();
  }

  async function initialize() {
    try {
      const values = await Promise.all([
        fetchJson('../../data/mountains.json'),
        fetchJson('../../data/image-credits.json', {})
      ]);
      if (!Array.isArray(values[0])) throw new Error('mountains.jsonの形式が正しくありません。');
      state.mountains = values[0];
      state.credits = values[1] || {};
      state.currentId = state.mountains[0] && state.mountains[0].id;
      renderMountainOptions();
      ensureDraft(state.currentId);
      renderSelected();
      renderCandidates();
      scanCurrentImageHashes(state.currentId);
      $('find').disabled = false;
      setStatus('', 'ok', 'load-status');
    } catch (error) {
      setStatus('山データの読み込みに失敗しました。公開サイトの管理者画面から開いてください。\n' + error.message, 'err', 'load-status');
    }
  }

  $('mountain').addEventListener('change', () => {
    state.currentId = $('mountain').value;
    state.candidates = [];
    state.excluded = [];
    state.showExcluded = false;
    $('candidates').innerHTML = '';
    $('find').textContent = '画像候補を取得';
    setStatus('', 'ok');
    setStatus('', 'ok', 'publish-status');
    ensureDraft(state.currentId);
    renderSelected();
    renderCandidates();
    scanCurrentImageHashes(state.currentId);
  });
  $('find').addEventListener('click', () => getCandidates($('find').textContent.includes('再取得')));
  $('add-own').addEventListener('click', addOwnPhotos);
  // 写真を選んだら、撮影者名が入っていればそのまま追加する（前は「追加」ボタンを押し忘れると採用されなかった）
  ['own-files', 'camera-file'].forEach((id) => {
    $(id).addEventListener('change', () => {
      if (!$(id).files.length) return;
      if ($('own-author').value.trim()) addOwnPhotos();
      else setStatus('撮影者名を入れてから「選んだ自前写真を追加」を押してください。', 'warn', 'own-status');
    });
  });
  $('dedupe').addEventListener('click', dedupeCurrentDraft);
  $('reset').addEventListener('click', resetCurrentDraft);
  $('publish').addEventListener('click', publishChanges);
  $('own-author').value = localStorage.getItem('ym_own_photo_author') || '';

  initialize();
})();
