# Yamatch（tozan-navi.com）開発ルール

関東圏の電車アクセス登山情報サイト。GitHub Pages静的サイト（バニラJS＋一部React/Babel CDN）。
`/data/mountains.json` を全ページがfetchする構成。**このファイルが正**。

## 作業ルール
- 確認の質問は減らし、合理的に判断して進める（不可逆な変更・方針が分かれる場合のみ確認）
- 設計決定が確定する前に実装を始めない
- こまめにgitコミットする（1グループ・1テーマごと）。作業前に `git status` で未コミットの変更がないか確認
- 完了時はスクリーンショットやGIFを出さず、変更ファイルと結果を簡潔に報告
- バグ発見時は影響範囲を正直に報告する（小さく見せない）

## コーディングルール（厳守）
- ネストしたテンプレートリテラル禁止（iOS Safari互換）
- スプレッド演算子禁止 → `Object.assign` を使う
- 置換前にgrepで対象を確認、置換後も残存がないことをgrepで確認
- 影響範囲が広い変更は、全関連箇所をgrepで洗い出してからまとめて修正
- 文字列の切り出しに `str.find()` や手動インデックスを使わない（日本語混在で破損）。`re.sub()` を使う
- `re.subn` でマッチ数とファイル数の一致を確認。不一致はエラー扱い
- 処理後に `</html>` 終端とdivの開閉数を確認
- `node --check` でJS構文チェック（LD+JSONは除外）

## デザイン基準
- ヘッダー色：`#4e6535`
- 背景色：`#f0ede5`
- 診断バナー色：`#c8d4b8`
- フォント：Outfit / Zen Kaku Gothic New / Noto Serif JP
- 正解例（日和田山ページ）から実際にgrepで抽出してから作業する。アイコン・色を推測で作らない

## データ整合性
- `mountains/data/mountains.json` は作らない（削除済みの重複ファイル）
- JSON修正後は、HTMLの `data-*` 属性・個別ページJSと同期しているか機械的に検証（0件ミスマッチ）
- 山ページ修正時は `<div class="mountain-updated">最終更新: YYYY-MM-DD</div>` を更新
- 季節4フィールド（`seasonCalendar` / `calLegend` / `seasonNoGear` / `season6Crampons`）は必ず同期
- 所要時間フィールドは2系統ある：`driveTime*`（トップのフィルタ用）と `drive*`（個別ページ `applyDep` 用）
- 運賃は個別に公式情報で裏取りする。概算・按分は禁止。同じゲートウェイ駅の山同士で比較して欠落を検出
- 横浜・大宮発は新宿発と経路・金額が大きく異なることが多い
- 同じバグパターンは全ファイル横断で検索し、他の山に旧構造が残っていないか確認
- VIBES・紹介文・FAQは山ごとに固有の内容にする（テンプレ使い回し禁止）
- 「近くて似た山」リンクの色クラスはリンク先の `category` に対応（百名山→`rc-blue`、その他→`rc-green`）

## 電車・バスアクセスデータの整合性（重要・頻発バグ）
- `trainRoutes` を新規構築・編集したら、以下3種の legacy フィールドを必ず同期させる（さもないと check_pages.py の8セクション中で検出される）
  - `trainAccessHtml`：`scripts/render_transit_routes.py` の `render_ts_section(train_routes, mountain)` を呼んで生成する（手書き禁止）。`trainRoutes` はあるのに `trainAccessHtml` が無いと「想定外の組み合わせ」として検出される
  - `trainAccess` / `trainAccessOmiya` / `trainAccessYokohama`：矢印区切りのプレーンテキスト（例: `新宿駅 --[中央線]--> 大月駅 --[富士急行線]--> 河口湖駅`）。`trainAccess` が truthy なのに Omiya/Yokohama 版が欠けていると検出される
  - `trainTimeShinjuku/Omiya/Yokohama`・`fareShinjuku/Omiya/Yokohama`：`trainRoutes.routes.{dep}.legs` の `durationMin` 合計（legsum）と必ず一致させる。手動でずれることが多いので毎回再計算して確認する
- 電車アクセスが無い（マイカーのみ）山は `trainAccess: false` または `null`。ただし「本当にアクセス手段が無いか」を毎回一次情報で検証すること。trainAccess=false のまま放置されていたが実際は季節運行バス・予約制シャトル等が存在するケースが過去の検証で25山中18山発見された（サイト全体で同様の見落としがある可能性が高い）
- FAQ「アクセス方法」の回答文には、`fareShinjuku`/`fareOmiya`/`fareYokohama` の3つの正式運賃額**のみ**を記載する。区間ごとの内訳運賃（例：バスのみの料金）を書くと、check_pages.py セクション6の運賃整合性チェックで「不一致（stray）」として検出される
- `check_pages.py` は `--id` オプション非対応。個別山の確認はサイト全体を実行してから該当IDでgrepする
- `check_pages.py` は16セクション（15は新構造の整合性、16は装備カレンダー）。9〜14（ルートの他山コピー／所要時間・legs不一致／記事の駅名／定数の異常値／規制中の山の掲載／特急の「自由席」）は過去に実際に見つかった誤りの再発防止用
- セクション10・11のうち調査待ちのレガシーは `scripts/check_known_issues.json`（ベースライン）に登録済みで件数に含めない。新規の指摘のみ異常として数える。解消したら `python3 scripts/check_pages.py --update-baseline` でベースラインを更新する
- アクセス表の注記（`trainRoutes.note` / `summaryNote`）は、`render_transit_routes.py` が「。」「※」で区切って箇条書き（`ul.ts-note-list`）に自動整形する。書くときは1文1項目を意識し、1文を長くしない
- 規制中の山は `status.level: "restricted"` を付ける。トップの一覧・診断では自動で末尾に回るが、検索ページ・記事の「おすすめカード」からは手動で外す（セクション13で検出）
- `routes[]` の各ルートには `coeff`（ルート別コース定数）がある。`scripts/calc_route_coeff.py` で time/distance/elevation から再計算する（山全体の coeffMin/coeffMax は別管理）
- 電車・バス・運賃を変更したら、管理表 `yamatch_kensho_kanri (3).xlsx`（経路・運賃・時間データ一覧／修正履歴データ管理表／検証チェックリスト／バス情報整合性チェック）も同時に更新する

## 新データ構造（ssot-v1・2026-10-05〜段階移行中）
山 → ルート → 登山口 → アクセス → 季節条件 の順に紐付ける。`dataModel: "ssot-v1"` の山が移行済み（19山。一覧は `dataModel` で確認）。
- 正のデータ
  - `data/mountains.json`：`representativeRouteId` / `routes[].{id,trailheadId,accessId,coeff,status}` / `conditions`（装備の月別・登山道の閉鎖期間）/ `alerts`（現在のアクセス注意）
  - `data/trailheads.json`：登山口・アクセス拠点（座標はここだけに持つ。`type`: trailhead / accessHub）
  - `data/accesses.json`：電車・バス経路、運賃、運行期間（`operation.validFrom/validTo/statusType`）、`sourceUrl`、`lastVerified`。複数の山で共有する（例：北沢峠＝甲斐駒ヶ岳・仙丈ヶ岳）
- 移行済みの山では、次の旧フィールドを**手で編集しない**。`python3 scripts/build_derived.py` が新構造から生成する：
  `trailhead` `lat` `lng` `parking` `address` `gmapUrl` `amapUrl` `mapBtnsHtml` `trainRoutes` `trainAccessHtml` `trainAccess*` `trainTime*` `fare*` `trainInfo` `coeffMin` `coeffMax` `courseCoefficient` `courseCoefficientRange` `seasonCalendar` `calLegend` `seasonNoGear` `season6Crampons` `warnBanner`、およびFAQ（アクセス・シーズン）と本文中の「定数◯〜◯」「代表コース…」
- 手順：新構造を編集 → `build_derived.py` → `gen_mountain_pages.py --id <id>` → `check_pages.py`（セクション15が新構造の整合性）
- コース定数は `routes[].coeff` だけが正。山の上部表示・FAQ・metaはそこから作る
- 「登山口（歩き始める場所）」と「アクセス拠点（駐車場・バスやロープウェイに乗る場所）」を分ける。地図ボタンの行き先は `accesses[].mapTargetId`
- 季節は「登山道／公共交通／装備」を別々に持つ。公共交通の運行終了を登山不可として表示しない。閉鎖期間を装備区分（アイゼン等）で表現しない
- 確認できない値は推測で埋めず `null` ＋ `needsVerification: true`。出典（`sourceUrl`）と最終確認日（`lastVerified`）を必ず残す
- 全山の監査：`python3 scripts/audit_data.py` → `data/audit_report.csv`（P0〜P3）
- 旧フィールドは削除しない（全山の移行と新旧比較が終わってから廃止）

## 毎年変わるデータの見張り（2026-10-06〜）
季節バス・林道バス・マイカー規制・閉鎖期間・開山期間・災害の通行止めは、期限と出典をデータとして持たせる。
- 新構造の山：`accesses.json` の `operation.validTo` と `sourceUrl`、`alerts[].validTo`、`conditions.trailPeriods`
- 旧構造の山：`mountains.json` の `annualItems[]`（`kind` / `label` / `validFrom` / `validTo` / `seasonYear` / `sourceUrl` / `lastVerified` / `note`）。期間つきの項目は電車・バス欄の上に表示される。期間なし（災害の通行止めなど）は表示せず、出典の見張りだけに使う
- 期限を過ぎると、山ページが自動で「◯年のこの期間は終了しました」と注記する（`mountain-engine.js`。`data-valid-to` 属性を見る）
- `python3 scripts/check_annual_updates.py`：期限切れ・30日以内に期限・出典ページの変更・リンク切れ・未登録の山を一覧にする。**データは書き換えない**
- `.github/workflows/annual-data-check.yml` が毎月1日に上を実行し、対応が必要なら Issue を作る
- 反映は人が確認してから行う。出典ページを読んで新しい期間を入れ、`lastVerified` を更新する（自動で書き換えない）
- 季節運行の経路を新しく書くときは、必ず `validTo` と `sourceUrl` を入れる（「例年◯月〜」の文章だけにしない）

## 装備カレンダー（4区分・2026-10-08〜）
- 表示の正は `gearCalendar`（12か月）。区分は `no_crampons`（アイゼン不要）/ `light_crampons`（軽アイゼン等）/ `winter_gear`（冬山装備）/ `closed`（入山不可）
- 月の途中で変わる月だけ `{"split": true, "before": 区分, "after": 区分, "changeDate": 後の区分が始まる日}`。ページでは斜め2色になり、タップで切替日が出る
- 「入山不可」は装備の段階ではなく、登山道閉鎖などで登れない期間。推測で付けない（出典のある閉鎖だけ）
- 「6本アイゼン」「12本アイゼン」と断定する表記は使わない（軽アイゼン等＝チェーンスパイク・6本爪アイゼン等／冬山装備＝12本爪アイゼン・ピッケル等）
- 旧構造の山：`gearCalendar` を直接編集する。新構造の山：`conditions.gearMonthly` と `conditions.trailPeriods` を編集 → `build_derived.py` が `gearCalendar` を作る
- 新構造の山で装備の区分が月の途中で変わる月は `conditions.gearSplits`（例：`{"10": {"before": "light_crampons", "after": "winter_gear", "changeDate": 11}}`）に書く
- 共通処理は `scripts/gear_calendar.py`（表示・検証・変換）。旧フィールド（`seasonCalendar` など）はトップの絞り込み用に残してあり、`gearCalendar` と食い違うと `check_pages.py` セクション16で検出される
- 区分・切替日が分からない山は推測で埋めず、要確認として報告する
- 「雪が降ったあとの数日だけ滑り止めが要る」のは例外として扱い、軽アイゼン等を付けない（都内でも起きるため）。冬のあいだ雪や凍結が続くのが普通の山だけ付ける。関東の低山は標高1,200mが目安
- トップの絞り込み（アイゼン不要／軽アイゼン等まで）・バッジ・月の表示も `gearCalendar` で判定する。`seasonNoGear` などの月の文字は古い表示用で、判定には使わない
- 入山不可の月は、山ページの装備カードを出さず（`data-gear-closed`）、診断では結果の末尾に回す

## ヒーロー時間表示
- 60分未満は分のみ（例: 55+分〜）、60分以上は小数時間（例: 100分→1.7+時間〜、末尾 `.0` は省略）
- `ymFormatHeroTime(raw)` で hero-time / hero-unit を動的更新

## 作業後の総合チェック（毎回スクリプトで0件確認）
1. `&#\d+;` エンティティ残存（📍は除く）
2. Unicode絵文字残存（💡📍⚠️🚫は許容）
3. `ymFormatHeroTime` の変換漏れ
4. 汎用Vibes文言の残存
5. `rw` の順序
6. gear旧配色（オレンジ／赤）
7. headerロゴ旧式
8. FAQ `h3` 残存
9. まとめ直リンク混入

## スクリプト（`scripts/` 配下）
- ページ再生成：`scripts/gen_mountain_pages.py --id <id>`（全件は `--all`、書き込まず確認は `--dry-run`）
- 検証：`scripts/check_pages.py`（0件になるまで修正を繰り返す）
- 電車・バスアクセスHTML生成：`scripts/render_transit_routes.py`（`render_ts_section`）
- 装備カード：`gen_mountain_pages.py` が枠（`gear-cards-scroll`）を出力し、中身は `assets/js/mountain.js` ＋ `assets/js/gear-common.js` が `data/gear-data.json` から描画。診断用の月別JSON（`data/recommend-gear/*.json`）は `scripts/gen_recommend_gear.py` で生成（手動編集禁止）

## 外部設定
- アフィリエイトは楽天の直接フォーマットを使用（A8.net経由は使わない）
- ブランド公式サイトの画像はホットリンクしない
- 天気APIはJMA seamless。座標は `weatherLat` / `weatherLng`（登山口座標）
