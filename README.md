# ギアライブラリ機能 一式（最新版）

## 現在の状態
- **13ブランド**：CAYL・Pa'lante Packs・Hyperlite Mountain Gear・Klättermusen・NORRØNA・
  Cotopaxi・Fjällräven・Houdini・Rab・BLACKYAK・Merrell・AKU・LOWA
- **30商品**
- **ページ数**：29ページ（ハブ1・ブランド一覧1・ブランド詳細13・カテゴリ5・コレクション4
  + サイトルートindex.html更新）
- **カテゴリ**：バックパック／レインウェア／シューズ／ウェア（その他）／アクセサリー
  （シューズはMerrell・AKU・LOWA追加により稼働中）
- **コレクション（SEOロングテール）**：ULバックパック／韓国登山ブランド／30Lバックパック／
  軽量レインウェア
- **ヒーロー画像あり**：CAYL・Fjällräven・Cotopaxi・Hyperlite・Merrell・LOWA（6ブランド）
- **Instagram公式埋め込みあり**：11/13ブランド（AKU・LOWAのみ未設定）

## ディレクトリ構成
```
gear_feature/
├ index.html                 サイトルート(ハンバーガーメニューに「🎒 登山ギアを探す」導線あり)
├ sitemap.xml                 ギア関連29ページを含む完全版
├ data/
│  ├ gear-brands.json         ブランドマスタ(13件)
│  ├ gear-items.json          商品マスタ(30件)
│  ├ gear-categories.json     カテゴリ定義
│  ├ gear-collections.json    コレクション(条件保存型SEOページ)
│  ├ mountains-lookup.json    山との相互リンク用データ抜粋
│  └ mountain-gear-links.json 【生成物】山→ギアの逆引き(山ページ未統合、次フェーズ用)
├ gear/                       【生成物】公開するHTML一式
│  ├ index.html                 ハブページ(ヒーロー画像+ギアタイプアイコン帯+カテゴリ+コレクション)
│  ├ brands/index.html          ブランド一覧
│  ├ brands/{id}/index.html     ブランド詳細×13
│  ├ category/{id}/index.html   カテゴリページ×5
│  └ collections/{id}/index.html コレクションページ×4
├ images/gear/                 ヒーロー画像一式(Gemini生成、透かし除去済み)
└ scripts/
   └ gen_gear_pages.py        全ページを再生成するスクリプト
```

## 使い方
1. `data/gear-brands.json` または `gear-items.json` にエントリを追加
2. `python3 scripts/gen_gear_pages.py` を実行
3. `gear/` と `data/mountain-gear-links.json` が全て再生成される

ブランドに`relatedMountainIds`を追加すれば「おすすめの山」セクションと逆引きデータに自動反映。
`heroImage`を追加すればヒーロー画像・OGP画像に、`instagramUrl`を追加すればInstagram埋め込みに、
それぞれ自動反映されます。

## デザインの要点
- **ロゴ・アイコンは全てオリジナル**：実在ブランドのロゴ・商標は一切使用せず、円形バッジ＋
  モノグラム文字（ブランドごとの固有カラー）で表現
- **商品カテゴリアイコン**：バックパック／レインウェア／ウェア／シューズ／アクセサリー／
  キャップ／ポールを独自の線画SVGで表現。ハブページのギアタイプアイコン帯にも使用
- **ヒーロー画像**：AI生成画像を使用。実在ブランドのロゴ・商標的シルエット（Kånkenの箱型、
  Cotopaxi Del Díaの多色パッチワーク等）が写り込んでいないか毎回確認したうえで採用

## 購入導線
- **Amazon/楽天の実リンクあり**：Hyperlite・Klättermusen・NORRØNA(一部)。既存サイトと同じ
  `tag=amazonafdaiki-22`のAmazonアソシエイトタグを使用。楽天リンクはA8.net等の
  アフィリエイトトラッキングコード未付与のため、公開前に御社のASP管理画面でラッピングが必要
- **日本正規代理店リンクあり**：Pa'lante(palantepacks.jp)、Rab(rab-equipment.jp)、
  Merrell(merrell.jp)、AKU(石井スポーツ)、LOWA(イワタニ・プリムス)
- **BLACKYAKのみ公式の日本語通販サイトなし**：BUYMA等の個人輸入代行サービス経由が中心と
  正直に明記

## SEO対応
- 全ページに`BreadcrumbList`構造化データ
- ブランド詳細ページに`Brand`構造化データ
- カテゴリ・コレクションページに`ItemList`構造化データ
- `sitemap.xml`にギア関連29ページを登録済み

## 既知の未対応・次にやること
1. **AKU・LOWAのInstagram埋め込み**：確度の高い投稿URLがまだ見つかっていません
2. **山ページ側への「おすすめギア」統合**：`mountain-gear-links.json`は生成済みですが、
   155の山ページへの一括挿入は横断検索・全数検証が必要な作業のため未着手です
3. **Pa'lante・Klättermusen・NORRØNA・Houdini・Rab・BLACKYAK・AKUのヒーロー画像**：
   まだ専用画像がありません
4. **楽天リンクのアフィリエイトラッピング**：公開前にA8.net等で変換が必要
5. **商品詳細ページ・フィルターUI付き商品一覧**：データ構造は対応済みですが、
   専用ページ・UIは未実装（Phase 2として提案済み）
