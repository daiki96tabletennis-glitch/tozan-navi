# YAMATCH 保守スクリプト運用ガイド

`data/mountains.json`（＋`data/gear-data.json`）を唯一の正本とし、
`gen_mountain_pages.py`が`mountains/<id>/index.html`を毎回フル再生成する。
**山固有情報（地域・標高・難易度・コース定数・運賃・アクセス・FAQ・警告バナー等）
は`mountains/`配下のHTMLへ直接手入力しない。** 必ず`data/mountains.json`
（必要に応じ`data/gear-data.json`）を編集し、`gen_mountain_pages.py`を実行すること。

2026-09-18のリファクタリングにより、旧来の「共通部分だけをHTMLへパッチする」
複数スクリプト（`sync_mountain_assets.py`/`gen_mountain_engine.py`/
`sync_mountain_faq.py`）は廃止し、`scripts/deprecated/`へ移動した。
これらが担っていた処理はすべて`gen_mountain_pages.py`のページ全体再生成に
統合されている。**通常運用でこれらを実行する必要はない。**

## データの正本と役割分担

| ファイル | 役割 |
|---|---|
| `data/mountains.json` | 山の正本データ（地域・標高・難易度・コース定数・運賃・アクセス・FAQ・警告バナー・編集文章の一部等） |
| `data/gear-data.json` | 月別ギア推奨データ（`data-gear-variants`属性の構造化版） |
| `assets/css/mountain.css` | 全山共通CSS（外部参照） |
| `assets/js/mountain.js` | 全山共通JS（外部参照） |
| `assets/js/mountain-engine.js` | 全山共通エンジンJS（`window.YM_MOUNTAIN_INIT`で山固有値を受け取る、外部参照） |
| `scripts/_base_mountain_style.css` | 生成ページに埋め込む共通インラインCSS（156山のstyle和集合） |
| `scripts/_weather_widget_block.html` | 天気ウィジェットの共通HTML/JSテンプレート（`__MID__`をID置換） |
| `scripts/_hero_photo_script.html` | ヒーロー写真カルーセル機能の共通スクリプト（対象8山のみ、`__MID__`をID置換） |
| 検索ページ内の掲載山ID・並び順・intro・FAQ・カード紹介文 | 各`search/<slug>/index.html`に直接記述（未JSON化、対象外） |

### mountains.json内の「編集文章として保持」フィールド（オパーク扱い）

以下は数式・条件分岐では安全に再現できないと判断し、既存HTMLから**抽出した
文字列をそのまま出力する**（生成時にHTMLとして解釈・再構築しない）フィールド。
中身を変える場合はHTMLではなくこのJSONフィールドを直接編集する。

`vibesHtml` / `introHtml` / `dlNoteHtml` / `dlReasonsHtml` / `trainAccessHtml` /
`relatedLinksHtml` / `mapBtnsHtml` / `routeCautionHtml`（2山のみ）/
`metaTitle` / `metaDescription` / `ogTitle` / `ogDescription`

### 山ごとに現状のUI差異を保存しているフラグ（統一しなかったもの）

以下は「どちらかが正解」と断定できない実デザイン差分だったため、多数決で
強制統一せず、現状のページ表示をそのまま維持するフラグとして`mountains.json`
に保存した。

- `climbedBtnStyle`（`"flat"` 111山 / `"rounded"` 45山）：登頂記録ボタンの
  角丸・枠線色・アイコン（SVG or 絵文字）が2系統存在。`rounded`側は
  プロジェクト設計色`#c8d4b8`を使っており最新デザインの可能性があるため、
  どちらかへ統一するかはユーザー判断待ち。
- `weatherBeforeIntro`（true 28山 / false 46山、天気ウィジェット搭載74山中）：
  天気カードを「こんな人におすすめ」の直後（山紹介・難易度カードより前）に
  置くか、通常位置（難易度カードの後）に置くか。中〜上級/上級山に`true`が
  多い傾向はあるが完全な相関ではないため個別フラグとして保存。

## 山データを更新したときにやること

```bash
# 1. data/mountains.json（必要なら data/gear-data.json）を編集する

# 2. 該当ページを再生成する
python3 scripts/gen_mountain_pages.py --id <山id>
# まとめて全山再生成する場合
python3 scripts/gen_mountain_pages.py --all
# 内容に差分がある場合のみ書き換わる（同一なら無変更）

# 3. 公開前チェックを実行する
python3 scripts/check_pages.py

# 4. 実ブラウザ（Playwright等）で見た目・挙動を確認してからデプロイする
```

## 新しい山ページを追加したときにやること

```bash
# 1. data/mountains.json に新しいエントリを追加する
#    （必要な必須フィールドが欠けていると gen_mountain_pages.py が
#     GenError で停止し、途中生成物で既存HTMLを壊すことはない）
# 2. 生成する
python3 scripts/gen_mountain_pages.py --id <新id>
# 3. 公開前チェック
python3 scripts/check_pages.py
```

## スクリプト一覧

| スクリプト | 役割 | べき等性 |
|---|---|---|
| `gen_mountain_pages.py` | `data/mountains.json`等の正本から`mountains/<id>/index.html`をフル再生成する。単一山指定・全山一括の両対応。生成失敗時は`.tmp`書き込み→比較→`os.replace`で、既存HTMLを壊れた状態で上書きしない。必須データ欠損時は`GenError`で停止 | 済（内容が同一なら無変更） |
| `check_pages.py` | 画像/リンク切れ・必須データ欠損・title系欠損/重複・JSON-HTML不一致・交通情報欠損を検査する。実装のみで壊れず、何度実行してもよい | - |
| `sync_search_pages.py` | 検索ページの山カードスタッツ・本文中のコース定数言及を`mountains.json`基準に同期する（山個別ページの生成方式移行後も、検索ページ側は別スコープのため継続使用） | 済 |
| `deprecated/sync_mountain_assets.py` | **廃止**。旧：共通CSS/JS参照への統一パッチ。`gen_mountain_pages.py`が生成時から統一済みの参照を出力するため不要 | - |
| `deprecated/gen_mountain_engine.py` | **廃止**。旧：エンジンJSの`mountain-engine.js`+`YM_MOUNTAIN_INIT`への統一パッチ。`gen_mountain_pages.py`が生成時から出力するため不要 | - |
| `deprecated/sync_mountain_faq.py` | **廃止**。旧：`faq`フィールドからFAQPage JSON-LD・可視FAQへの同期パッチ。`gen_mountain_pages.py`が生成時から出力するため不要 | - |

## 例外ページ（`gen_mountain_pages.py`の対象外）

- **`tanzawa`**：`EXCLUDED_IDS`で除外。`@graph`/`TouristAttraction`型の
  旧JSON-LD構造・旧HTMLコメント・share-section統合等、他155山と根本的に
  異なる`<head>`/セクション構成を持つ唯一のページ（156山中1山のみ該当を
  `grep`で確認済み）。自動生成に含めると構造を破壊するため、既存HTMLを
  そのまま保持している。移行するかは別途判断が必要。
- **`daibosatsurei` / `nikko_nantai` / `shirane_nikko` / `takao-hiking`**：
  `EXCLUDED_DIRS`。`mountains.json`に対応エントリが存在しない非正規ページ
  （`mountains/`配下には存在するが156山のマスタ対象外）。ノータッチ。

## 既知の残課題（今回のスコープ外・要フォローアップ）

- **6山12件の電車アクセス欠損**（`kinpusan`/`kayagatake`/`hinata`/`nakawarayama`/
  `yarigatake2`/`gozenyama`の`trainAccessYokohama`/`trainAccessOmiya`）：
  従来から既知の欠損。裏取りできる情報がなく未補完。
- **`azuma`/`mitakesan`の交通情報チェック新規検出**：`check_pages.py`の
  「`ts-fare-val`/`ts-time-val`クラスがHTMLに実在するか」チェックで、この2山の
  `trainAccessHtml`（既存HTMLから抽出した編集文章そのまま）が旧式マークアップ
  （該当クラスを含まない形式）であることが判明。今回のリファクタリングで
  新たに生じた問題ではなく、抽出元の既存HTML自体が元々この形式だったことを
  移行前後のバイト同一性検証で確認済み。表示自体は問題なく行われるため
  機能面の実害はないが、`check_pages.py`のこのチェック観点からは要フォロー。
- **山ページUI差異の統一保留2件**：上記「山ごとに現状のUI差異を保存している
  フラグ」の`climbedBtnStyle`・`weatherBeforeIntro`。どちらか一方の見た目へ
  統一するかはユーザーの意思決定が必要なため、今回は現状維持（フラグで
  個別再現）とした。
- **検索ページのintro文・FAQ・カード紹介文**：`search/`配下に直書きのまま。
  JSON化は未着手。
