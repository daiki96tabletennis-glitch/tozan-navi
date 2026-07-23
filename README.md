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
