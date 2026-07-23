# ギア機能 MVP（Phase 1）納品物

## ディレクトリ構成
```
gear_feature/
├ data/
│  ├ gear-brands.json          ブランドマスタ(5件・relatedMountainIdsで山と紐付け)
│  ├ gear-items.json           商品マスタ(10件・categoryIdでカテゴリ紐付け)
│  ├ gear-categories.json      カテゴリ定義(backpack/rainwear/shoes/apparel/accessory)
│  ├ gear-collections.json     SEOロングテール用の条件保存(ULバックパック等)
│  ├ mountains-lookup.json     相互リンク用の山データ抜粋(15山・mountains.jsonから自動抽出)
│  └ mountain-gear-links.json  【生成物】山→ギアの逆引き(山ページ統合の下準備。まだ山ページには未反映)
├ gear/                        【生成物】実際に公開するHTML一式
│  ├ index.html                 ハブページ
│  ├ brands/index.html          ブランド一覧
│  ├ brands/{id}/index.html     ブランド詳細×5(代表商品+おすすめの山を含む)
│  ├ category/{id}/index.html   カテゴリページ×5(backpack/rainwear稼働、shoes等は準備中表示)
│  └ collections/{id}/index.html コレクションページ×4(ULバックパック/韓国登山ブランド/30Lバックパック/軽量レインウェア)
└ scripts/
   └ gen_gear_pages.py         上記JSONから gear/ と data/mountain-gear-links.json を再生成するスクリプト
```

## 使い方（ブランド・商品を追加するとき）
1. `data/gear-brands.json` または `data/gear-items.json` にエントリを追加
2. `python3 scripts/gen_gear_pages.py` を実行
3. `gear/` 以下が全て再生成される（HTMLは手で書かない）

新しい山と紐付けたい場合は `gear-brands.json` の `relatedMountainIds` に山IDを追加するだけで、
「おすすめの山」セクションと `mountain-gear-links.json` の両方に自動反映されます。

## データ修正：Pa'lanteは日本正規代理店ありでした（今回）
前回までPa'lanteを「国内正規代理店なし・個人輸入中心」としていましたが、確認したところ
**日本正規代理店（palantepacks.jp、運営：nomadics）が存在**していました。moonlight gear
各店（東京・大阪・福岡）でも取扱いがあります。以下を修正しています。
- ブランド情報に`japanUrl`を追加、ブランド詳細ページに「日本正規代理店サイト」ボタンを表示
- Joey・V2に`japanUrl`（palantepacks.jpの商品ページ）を追加、商品カードに「日本正規代理店で見る」
  ボタンを表示（Amazon/楽天ボタンと同じ導線）
- 「Simple Pack (DCF)」は現行ラインナップではV2に統合され販売終了していたため、現行モデル
  「ultralight」（¥44,000、25L）の情報に差し替え

## Instagram公式埋め込みを追加（今回）
各ブランド詳細ページに、ブランド公式Instagramの投稿を1件ずつ公式embed機能で埋め込みました。
- 実装方式：Instagramの「埋め込みコードを取得」機能と同じ`<blockquote class="instagram-media">`
  + `embed.js`方式。画像はYamatchのサーバーに一切保存せず、常にInstagram側から読み込みます
- 8ブランド全ての公式アカウントを検索で確認し、実在する投稿URLを設定済み（`gear-brands.json`の
  `instagramUrl`）。Klättermusen・NORRØNA・Cotopaxi・Fjällrävenは日本語アカウントがある場合は
  そちらを優先しています
- スクリプトが読み込めない場合のフォールバックとして「Instagramで見る」テキストリンクも
  同梱（投稿削除時やJS無効環境でもリンク切れになりません）
- 新しい投稿に差し替えたい場合は`gear-brands.json`の`instagramUrl`を書き換えてスクリプト再実行

## ヒーロー画像を追加（今回）
`/gear/`ハブページの最上部にAI生成のギア一式フラットレイ画像を追加しました。
- 配置先：`images/gear/gear-hero.jpg`（既存のPNGから軽量なJPEGに変換・約188KB）
- 用途：ハブページのビジュアル、OGP画像（SNSシェア時に表示される画像）としても使用
- 注意：背景の山はマッターホルン（スイス）です。関東圏の実在の山を紹介する記事等では、
  特定の山と紐付けて使わないようご注意ください。あくまで「ギア全体の雰囲気」を伝える
  汎用カットとしての使用を想定しています。

## ブランド・商品を拡充（今回追加）
「CAYL価格帯で買いやすい・日本語サイトがある海外ブランド」という基準で3ブランドを追加しました。

| ブランド | 国 | 価格帯 | 日本公式サイト |
|---|---|---|---|
| Cotopaxi | アメリカ | 1.3〜2万円台 | cotopaxi.jp |
| POLER | アメリカ | 1.3〜1.6万円台 | polerstuff.jp |
| Fjällräven | スウェーデン | 1.3万円前後〜 | fjallraven.jp |

いずれも実売価格・実在商品を検索で確認したうえでデータ化しています（Amazon/楽天の実リンクは
既存5ブランドと同様、確認できたものにのみ設定。今回の3ブランドは公式サイトへのリンクのみ）。

商品も既存5ブランド分に1点ずつ追加し、10商品→22商品、5ブランド→8ブランドに拡充しました。
- CAYL: Juheul（Mari Roll Topの発展形）
- Pa'lante: V2（現行フラッグシップ）
- Hyperlite: Windrider 40（もう1つの定番モデル）
- Klättermusen: Gjalp 18L Backpack
- NORRØNA: lofoten Gore-Tex Jacket

ブランド数・商品数が増えたことで、`/gear/collections/ul-backpack/`や`/gear/category/backpack/`
などのフィルター結果も自動的に増えています（コード変更不要、JSONに追加するだけで反映される
設計になっているため）。sitemap.xmlにも新規3ブランドページを追加済みです。

## SEO対応（今回追加）
- `sitemap.xml`にギア関連15ページを追加（`/gear/category/shoes/`は準備中コンテンツのため意図的に除外）
- 全ページに`BreadcrumbList`構造化データを追加
- ブランド詳細ページに`Brand`構造化データを追加（創業年・国・概要）
- カテゴリ・コレクションページに`ItemList`構造化データを追加（掲載商品を検索エンジンに明示）
- `/gear/category/shoes/`（準備中プレースホルダー）に`noindex,follow`を設定し、薄いコンテンツとしてインデックスされるのを防止。商品が揃ったらこの制御は自動的に外れます（`gear-categories.json`の`status`を`active`に変更してスクリプト再実行するだけ）

## 画像・購入リンクについて（今回追加）
FBを受けて、5ブランドを「イラストのみ」と「実商品購入リンク付き」に分けました。

- **Hyperlite Mountain Gear / Klättermusen / NORRØNA**（国内正規取扱いあり）
  → 実在するAmazon.co.jp商品ページ（ASIN確認済み）・楽天市場の商品ページへのリンクを追加。
  Amazonは既存サイトと同じ`tag=amazonafdaiki-22`を使った正規のアソシエイトリンクです。
  楽天リンクは商品ページの実URLですが、**A8.net経由のアフィリエイト用トラッキングコードは
  未付与**です（既存サイトの楽天リンクはA8.net経由の`a8mat`パラメータで管理されており、
  新規商品ごとに正しいコードを生成するには御社のA8.net管理画面での操作が必要なため）。
  公開前にA8.netでラッピングしてください。
- **CAYL / Pa'lante Packs**（国内正規代理店なし・Amazon/楽天に商品なし）
  → 引き続きオリジナルイラストのみ。将来ブランドから画像提供を受けられた場合や、
    国内代理店ができた場合に切り替え可能です。

### 商品画像について（要対応）
Amazonはロボット型アクセスを禁止しており、商品画像を自動取得することはできませんでした
（Amazon Product Advertising APIの正規利用にはAPI認証情報が必要です）。
`gear-items.json`の各商品に`images`配列を追加済みなので、以下のいずれかで画像を用意し、
配列に画像URLを1つ追加してスクリプトを再実行すれば、自動的にイラストから実写真表示に
切り替わります。
1. Amazon Product Advertising APIを申請し、画像URLを取得する
2. Associateとして購入した商品を自分で撮影する
3. ブランドに直接問い合わせて画像提供を受ける

## 今回やったこと（FBを受けての方向転換）
- ブランドを主役から「カテゴリ／コレクションの一要素」に格下げ
- `/gear/category/{backpack, rainwear, shoes...}/` を新設（SEOの主戦場）
- `/gear/collections/{ul-backpack, korea-brands, 30l-backpack, light-rainwear}/` を新設
  （条件をJSONで保存する方式なので、商品が増えても追加開発なしで自動的に該当商品が並ぶ）
- ブランド側に `relatedMountainIds` を持たせ、ブランド詳細ページに「おすすめの山」を表示
- 山→ギアの逆引き `mountain-gear-links.json` を生成（**まだ山ページ側には未統合**。155ページへの
  一括挿入は横断検索・全数検証が必要な作業のため、次のタスクとして切り出すことを推奨）

## あえてやらなかったこと（次フェーズ）
- 山ページ（`mountains/{id}/index.html`）への「おすすめギア」セクション追加
  → `mountain-gear-links.json` は用意済みなので、次回このデータを読み込んで挿入するだけで着手可能
- 商品詳細ページ（`/gear/items/{id}/`）とフィルターUI付き商品一覧
  → データ構造（capacityL/weightG/priceRange等）は既に対応済みなので、今回のcollectionsの
    フィルターロジックをそのままUI化すれば作れます
