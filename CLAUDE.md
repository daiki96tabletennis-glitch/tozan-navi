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
- `check_pages.py` は14セクション。9〜14（ルートの他山コピー／所要時間・legs不一致／記事の駅名／定数の異常値／規制中の山の掲載／特急の「自由席」）は過去に実際に見つかった誤りの再発防止用
- セクション10・11のうち調査待ちのレガシーは `scripts/check_known_issues.json`（ベースライン）に登録済みで件数に含めない。新規の指摘のみ異常として数える。解消したら `python3 scripts/check_pages.py --update-baseline` でベースラインを更新する
- アクセス表の注記（`trainRoutes.note` / `summaryNote`）は、`render_transit_routes.py` が「。」「※」で区切って箇条書き（`ul.ts-note-list`）に自動整形する。書くときは1文1項目を意識し、1文を長くしない
- 規制中の山は `status.level: "restricted"` を付ける。トップの一覧・診断では自動で末尾に回るが、検索ページ・記事の「おすすめカード」からは手動で外す（セクション13で検出）
- `routes[]` の各ルートには `coeff`（ルート別コース定数）がある。`scripts/calc_route_coeff.py` で time/distance/elevation から再計算する（山全体の coeffMin/coeffMax は別管理）
- 電車・バス・運賃を変更したら、管理表 `yamatch_kensho_kanri (3).xlsx`（経路・運賃・時間データ一覧／修正履歴データ管理表／検証チェックリスト／バス情報整合性チェック）も同時に更新する

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
