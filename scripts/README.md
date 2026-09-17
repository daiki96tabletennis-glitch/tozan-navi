# YAMATCH 保守スクリプト運用ガイド

`mountains.json` を唯一の正本とし、以下のスクリプトで各種HTMLへ反映する。
**山データ（地域・標高・難易度・コース定数・運賃・アクセス・FAQ等）は
`mountains/`配下や`search/`配下のHTMLへ直接手入力しない。** 必ず
`data/mountains.json`を編集し、対応する同期スクリプトを実行すること。

## データの正本と役割分担

| ファイル | 役割 |
|---|---|
| `data/mountains.json` | 山そのものの正本（地域・標高・難易度・コース定数・運賃・アクセス・FAQ等） |
| `assets/css/mountain.css` | 全山共通CSS（山ごとの個別差分だけがHTML内に残る） |
| `assets/js/mountain.js` | 全山共通JS（標高カウントアップ・FAQ開閉・nearbyバー等、山固有データを持たない部分） |
| `assets/js/mountain-engine.js` | 全山共通エンジンJS（`window.YM_MOUNTAIN_INIT`で山固有値を受け取る） |
| 検索ページ内の掲載山ID・並び順・intro・FAQ・カード紹介文 | 各`search/<slug>/index.html`に直接記述（現時点ではJSON化されていない。将来`search-pages.json`として切り出す余地あり） |

## 山データを更新したときにやること

```bash
# 1. data/mountains.json を編集する

# 2. 変更した山のFAQ・エンジン初期値・検索ページ表示を同期する
python3 scripts/sync_mountain_faq.py <山id>          # faqフィールドを編集した場合
python3 scripts/gen_mountain_engine.py <山id>        # driveOfuna等の車アクセス時間を編集した場合
python3 scripts/sync_search_pages.py --all           # 地域・標高・難易度・コース定数を編集した場合
                                                       # （どの検索ページに載っているか事前に把握しなくても
                                                       #   全ページ走査して差分があるものだけ書き換える）

# 3. 公開前チェックを実行する
python3 scripts/check_pages.py

# 4. 実ブラウザでの見た目確認（Playwright等）を行ってからデプロイする
```

いずれのスクリプトも**既に正本と一致していれば自動でスキップ**するため、
「とりあえず`--all`を通す」運用で問題ない（差分がないページは書き換えない）。

## 新しい山ページを追加したときにやること

```bash
# 1. data/mountains.json に新しいエントリを追加する
# 2. mountains/<新id>/index.html を作成する（既存の近いページをコピーして
#    name/id/データを差し替えるのが手早い）
# 3. 共通アセット・共通エンジンへ寄せる
python3 scripts/sync_mountain_assets.py <新id>
python3 scripts/gen_mountain_engine.py <新id>
python3 scripts/sync_mountain_faq.py <新id>

# 4. 公開前チェック
python3 scripts/check_pages.py
```

## スクリプト一覧

| スクリプト | 役割 | べき等性 |
|---|---|---|
| `check_pages.py` | 画像/リンク切れ・必須データ欠損・title系欠損/重複・JSON-HTML不一致・交通情報欠損を検査する。実装のみで壊れず、何度実行してもよい | - |
| `sync_mountain_assets.py` | 山ページの共通CSS/JSを`assets/css/mountain.css`・`assets/js/mountain.js`参照に統一する | 済（既に統一済みならスキップ） |
| `gen_mountain_engine.py` | 山ページの個別エンジンJSを`assets/js/mountain-engine.js` + `YM_MOUNTAIN_INIT`に統一する | 済 |
| `sync_mountain_faq.py` | `mountains.json`の`faq`をFAQPage JSON-LD・可視FAQへ反映する | 済 |
| `sync_search_pages.py` | 検索ページの山カードスタッツ・本文中のコース定数言及を`mountains.json`基準に同期する | 済 |

## 既知の残課題（このスクリプト群の対象外）

- **6山12件の電車アクセス欠損**（`kinpusan`/`kayagatake`/`hinata`/`nakawarayama`/
  `yarigatake2`/`gozenyama`の`trainAccessYokohama`/`trainAccessOmiya`）：
  全山とも`fareYokohama`/`fareOmiya`（運賃）は算出済みだが、経路の説明文だけが
  未執筆。奥多摩方面等で経路パターンが類似する他山と比較検証したが、新宿駅ー
  各方面間の所要時間表記が山ごとに一貫しておらず、裏取りなしに合成すると誤情報に
  なるリスクが高いため、今回は補完していない。個別の時刻表確認が必要な既知課題
  として残す（`check_pages.py`のカテゴリ3で継続して検出される想定）。
- **`trainTimeShinjuku`/`trainTimeYokohama`/`trainTimeOmiya`フィールド**：
  当初「どこからも参照されない孤立フィールド」と報告したが誤りで、実際には
  `index.html`（トップページ）の出発駅切り替え（新宿・横浜・大宮）による
  並び替え・フィルタ・「アクセス難易度ティア」判定で使用されている。削除不可。
  個別ページの`ts-time-val`（所要時間表示）との間に見られた差異が、意味的な違い
  （電車のみの時間 vs バス・徒歩を含む総所要時間）によるものか、単純なdriftか
  は未調査。`check_pages.py`への同期チェック追加は、影響範囲の精査が済むまで
  見送る。
- **`mountains.json`の`courseCoefficient`配列フィールド**：当初「`coeffMin`/
  `coeffMax`と重複し無参照」と報告したが誤りで、実際には`index.html`内の
  ソート・★評価・`CourseMeter`/`CourseBadge`コンポーネント等8箇所で使用されて
  いる。`coeffMin`/`coeffMax`とは全156山で完全一致しdrift実績はないため実害は
  ないが、削除するには本番トップページ（React/JSX）8箇所の書き換えが必要で
  リスクに対して優先度が低いと判断し、今回は変更しない。
- **検索ページのintro文・FAQ・カード紹介文**：現状`search/`配下のHTMLに直接
  記述されたままで、JSON化（`search-pages.json`）はまだ行っていない。将来的に
  一元化する場合は掲載山ID・並び順の抽出ロジックから設計する必要がある。
- **12種類あるCSSテンプレート差分**：検索ページのCSS/レイアウトは意図的に
  現状維持している（データ面の一元化のみ実施）。見た目の統一は別タスク。
- **`mountains.json`の`courseCoefficient`配列フィールド**：`coeffMin`/`coeffMax`と
  完全に重複しており、どのHTML/スクリプトからも参照されていない。削除しても実害は
  ないが今回のスコープ外のため未対応。

## 変更履歴（判明した不具合と対応）

- 画像切れ2件を修正：`articles/coeff-10`の美ヶ原写真参照（`01.jpg`は実在せず、
  正式にライセンス確認済みの`04.jpg`のみ実在。`mountains.json`の`photos`配列も
  5件中4件が存在しない状態だったため、実在する1件のみに整理）。`gear/index.html`
  の`shoes.png`参照（正しいファイル名は`shoe.webp`、単数形・webp）。
- `mountains.json`の必須データ欠損21件を全件確認・分類。3山
  （`kobotokeshiroyama`/`kusatoriyama`/`nakimushiyama`）の`description`/
  `season`/`trailhead`は、該当ページのHTML本文・`seasonNoGear`等に既に実在する
  内容を抽出して補完（新規作成ではない）。残り6山12件（電車アクセス欠損）は
  裏取りできる情報が無く、上記の既知課題として保留。
- `check_pages.py`の運賃チェックに`break`の配置ミスがあり、新宿発の値を確認した
  時点でループを抜けてしまい、横浜発・大宮発の不一致が実質検査されていなかった。
  修正済み（3方面とも検査する）。この修正により`tanzawa`/`tanigawa`/`nasu`/
  `bandai`/`shirane_gunma`の運賃不一致（計9件）を新たに発見し、`mountains.json`
  基準に修正済み。
- 29山（`kannokura`等）でFAQの質問見出しが`<h2 class="faq-q">`ではなく
  `<div class="faq-q">`になっており、可視FAQブロックとして認識できず
  `sync_mountain_faq.py`が同期をスキップしていた。全て`<h2>`に統一し解消済み。
