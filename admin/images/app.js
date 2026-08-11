(function () {
  'use strict';

  const OWNER = 'daiki96tabletennis-glitch';
  const REPO = 'tozan-navi';
  const COMMONS_API = 'https://commons.wikimedia.org/w/api.php';
  const WIKIDATA_API = 'https://www.wikidata.org/w/api.php';
  const CACHE_KEY = 'ym_image_candidate_cache_v2';
  const CACHE_TTL = 7 * 24 * 60 * 60 * 1000;
  const PHOTO_MAX_EDGE = 2400;
  const PHOTO_QUALITY = 0.9;

  const state = {
    mountains: [],
    credits: {},
    currentId: null,
    candidates: [],
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
    const hasRequiredLinks = Boolean(safeUrl(item.licenseUrl) && safeUrl(item.commonsPageUrl));

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

  function scoreCandidate(item, mountain, englishName) {
    let score = item.method === 'wikidata_p18' ? 50 : 0;
    const ja = String(mountain.name || '').toLowerCase();
    const en = String(englishName || '').toLowerCase();
    const text = (item.fileName + ' ' + item.description + ' ' + item.categories).toLowerCase();
    if (ja && text.includes(ja)) score += 25;
    if (en && text.includes(en)) score += 15;
    if (/summit|mountain|peak|山頂|頂上|山岳|峰|岳/.test(text)) score += 8;
    if (/shrine|temple|station|train|railway|map|神社|寺|駅|電車|鉄道|地図/.test(text)) score -= 18;
    if (item.width > item.height) score += 10;
    if (item.width >= 1200) score += 10;
    if (item.width && item.width < 800) score -= 10;
    const distance = distanceKm(coordinate(mountain), item.coordinate);
    if (distance != null && distance <= 1) score += 20;
    else if (distance != null && distance <= 3) score += 10;
    item.distanceKm = distance;
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
      colimit: 10
    }, params));
    return (((data || {}).query || {}).pages || [])
      .filter((page) => page.imageinfo)
      .map((page) => candidateFromPage(page, method));
  }

  function wikidataEntityScore(entity, searchHit, mountain) {
    let score = 0;
    const labelJa = (((entity.labels || {}).ja || {}).value || '').trim();
    const description = [
      searchHit && searchHit.description,
      ((entity.descriptions || {}).ja || {}).value,
      ((entity.descriptions || {}).en || {}).value
    ].filter(Boolean).join(' ').toLowerCase();
    if (labelJa === String(mountain.name || '').trim()) score += 35;
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

  async function findWikidataMountain(mountain) {
    const search = await api(WIKIDATA_API, {
      action: 'wbsearchentities',
      search: mountain.name,
      language: 'ja',
      uselang: 'ja',
      limit: 6
    });
    const hits = search.search || [];
    if (!hits.length) return null;

    const entitiesResult = await api(WIKIDATA_API, {
      action: 'wbgetentities',
      ids: hits.map((hit) => hit.id).join('|'),
      props: 'labels|descriptions|claims',
      languages: 'ja|en'
    });
    const entities = entitiesResult.entities || {};
    const ranked = hits.map((hit) => ({
      hit,
      entity: entities[hit.id],
      score: entities[hit.id] ? wikidataEntityScore(entities[hit.id], hit, mountain) : -999
    })).sort((a, b) => b.score - a.score);

    if (!ranked[0] || ranked[0].score < 25) return null;
    return ranked[0].entity;
  }

  function readCandidateCache() {
    try { return JSON.parse(localStorage.getItem(CACHE_KEY) || '{}'); }
    catch (_) { return {}; }
  }

  function cachedCandidates(id) {
    const entry = readCandidateCache()[id];
    if (!entry || Date.now() - entry.savedAt > CACHE_TTL || !Array.isArray(entry.items)) return null;
    return entry.items;
  }

  function saveCandidateCache(id, items) {
    const cache = readCandidateCache();
    cache[id] = { savedAt: Date.now(), items };
    const newest = Object.entries(cache)
      .sort((a, b) => (b[1].savedAt || 0) - (a[1].savedAt || 0))
      .slice(0, 25);
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(Object.fromEntries(newest))); }
    catch (_) { /* 容量超過時はキャッシュなしで継続 */ }
  }

  async function getCandidates(forceRefresh) {
    const mountain = currentMountain();
    if (!mountain) return;
    const cached = !forceRefresh && cachedCandidates(mountain.id);
    if (cached) {
      state.candidates = cached;
      renderCandidates();
      setStatus(cached.length + '件の保存済み候補を表示しました。再検索する場合はもう一度ボタンを押してください。', 'ok');
      $('find').textContent = '候補を再取得';
      return;
    }

    $('find').disabled = true;
    $('find').textContent = '検索中…';
    setStatus('Wikidata / Wikimedia Commonsを検索しています…', 'ok');
    try {
      let all = [];
      let englishName = '';
      const entity = await findWikidataMountain(mountain);
      if (entity) {
        englishName = (((entity.labels || {}).en || {}).value || '').trim();
        const p18 = (((entity.claims || {}).P18 || [])[0] || {}).mainsnak;
        const fileName = p18 && p18.datavalue && p18.datavalue.value;
        if (fileName) all.push(...await commonsFiles({ titles: 'File:' + fileName }, 'wikidata_p18'));
      }

      all.push(...await commonsFiles({
        generator: 'search',
        gsrsearch: mountain.name,
        gsrnamespace: 6,
        gsrlimit: 10
      }, 'commons_name'));

      if (englishName) {
        all.push(...await commonsFiles({
          generator: 'search',
          gsrsearch: englishName,
          gsrnamespace: 6,
          gsrlimit: 8
        }, 'commons_english_name'));
      }

      const center = coordinate(mountain);
      if (center) {
        all.push(...await commonsFiles({
          generator: 'geosearch',
          ggsnamespace: 6,
          ggscoord: center.lat + '|' + center.lng,
          ggsradius: 5000,
          ggslimit: 8
        }, 'commons_geosearch'));
      }

      const unique = {};
      all.forEach((item) => {
        const key = item.fileName.toLowerCase();
        if (!unique[key] || item.method === 'wikidata_p18') unique[key] = item;
      });
      const result = Object.values(unique).map((item) => {
        item.score = scoreCandidate(item, mountain, englishName);
        item.licenseCheck = evaluateLicense(item);
        return item;
      }).sort((a, b) => b.score - a.score);

      state.candidates = result;
      saveCandidateCache(mountain.id, result);
      renderCandidates();
      const usable = result.filter((item) => evaluateLicense(item).ok).length;
      setStatus(result.length + '件取得しました（自動チェックOK：' + usable + '件）。', 'ok');
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
      commons_name: '山名検索',
      commons_english_name: '英語名検索',
      commons_geosearch: '山頂付近検索'
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

  function renderCandidates() {
    const mountain = currentMountain();
    $('candidate-title').textContent = mountain ? mountain.name + ' の画像候補' : 'Wikimedia Commonsから探す';
    const container = $('candidates');
    container.innerHTML = '';
    if (!state.candidates.length) return;
    const draft = ensureDraft(state.currentId);

    state.candidates.forEach((item) => {
      const check = evaluateLicense(item);
      const added = draft.some((selected) => sameImage(selected, item));
      const pageUrl = safeUrl(item.commonsPageUrl);
      const imageUrl = safeUrl(item.thumbnailUrl);
      const card = document.createElement('article');
      card.className = 'candidate-card' + (added ? ' is-added' : '');
      card.innerHTML =
        '<img src="' + esc(imageUrl) + '" alt="' + esc(item.fileName) + '" loading="lazy">' +
        '<div class="candidate-body">' +
          '<div class="badges">' +
            '<span class="badge">' + esc(item.score) + '点</span>' +
            '<span class="badge">' + esc(methodLabel(item.method)) + '</span>' +
            '<span class="badge ' + (check.ok ? 'ok' : 'warn') + '">' + esc(check.label) + '</span>' +
          '</div>' +
          '<p><strong>' + esc(item.fileName) + '</strong></p>' +
          '<p>作者：' + esc(item.author) + '</p>' +
          '<p>ライセンス：' + esc(item.license) + '</p>' +
          '<p>解像度：' + esc(item.width || '?') + ' × ' + esc(item.height || '?') + ' px</p>' +
          '<p class="small">' + esc(check.reason) + '</p>' +
          (pageUrl ? '<a class="source-link" href="' + esc(pageUrl) + '" target="_blank" rel="noopener">元画像ページを開く ↗</a>' : '') +
          '<button type="button" ' + (!check.ok || added ? 'disabled' : '') + '>' +
            (added ? '採用画像に追加済み' : check.ok ? '採用画像に追加' : '採用できません') +
          '</button>' +
        '</div>';
      card.querySelector('button').addEventListener('click', () => addCandidate(item));
      container.appendChild(card);
    });
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

  function loadImage(file) {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(file);
      const image = new Image();
      image.onload = () => {
        URL.revokeObjectURL(url);
        resolve(image);
      };
      image.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error(file.name + 'を画像として読み込めませんでした。JPEG・PNG・WebPをお試しください。'));
      };
      image.src = url;
    });
  }

  async function resizeOwnPhoto(file) {
    if (file.size > 50 * 1024 * 1024) throw new Error(file.name + 'は50MBを超えているため追加できません。');
    const image = await loadImage(file);
    let width = image.naturalWidth;
    let height = image.naturalHeight;
    if (!width || !height) throw new Error(file.name + 'のサイズを確認できませんでした。');
    const scale = Math.min(1, PHOTO_MAX_EDGE / Math.max(width, height));
    width = Math.max(1, Math.round(width * scale));
    height = Math.max(1, Math.round(height * scale));
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d');
    context.fillStyle = '#ffffff';
    context.fillRect(0, 0, width, height);
    context.drawImage(image, 0, 0, width, height);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', PHOTO_QUALITY));
    if (!blob) throw new Error(file.name + 'をJPEGへ変換できませんでした。');
    return { blob, width, height };
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
    const draft = ensureDraft(mountain.id);
    for (const file of files) {
      try {
        const converted = await resizeOwnPhoto(file);
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
          fileName: file.name.replace(/\.[^.]+$/, '') + '.jpg',
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
          mimeType: 'image/jpeg',
          contentHash,
          selectedAt: new Date().toISOString(),
          modifications: '最大2400pxのJPEGにリサイズ'
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
    const message = added + '枚を採用画像の末尾に追加しました。' + (errors.length ? '\n追加できなかった写真：' + errors.join(' / ') : '');
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
    return file ? decodeBase64(file.content) : null;
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
      sourceId: commonsIdentity(item) || null,
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
      setStatus('GitHubトークンがありません。先に通常の管理者画面でGitHubトークンを保存してください。スマートフォンの場合も、その端末で一度保存が必要です。', 'err', 'publish-status');
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
        const blob = item.source === 'own'
          ? state.ownFiles[item.ownFileKey]
          : await downloadCommonsImage(item);
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
  $('dedupe').addEventListener('click', dedupeCurrentDraft);
  $('reset').addEventListener('click', resetCurrentDraft);
  $('publish').addEventListener('click', publishChanges);
  $('own-author').value = localStorage.getItem('ym_own_photo_author') || '';

  initialize();
})();
