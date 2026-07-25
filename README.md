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
- **Instagramリンクカードあり**：11/13ブランド（AKU・LOWAのみ未設定）※JS埋め込みは廃止し、
  静的リンクカード方式に変更済み（詳細は本ファイル末尾を参照）

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

## シューズ・バックパック・ウェアのアイコンをAI生成PNGに変更（今回、重要）
手描きSVGでの登山靴アイコンの精度に限界があったため、Gemini生成の線画アイコン（背景白・
ロゴなし）に切り替えました。
- 背景を透過処理し、余白をトリミング、240x240pxのPNGとして`images/icons/`に配置
- `render_category_icon()`関数を、この3カテゴリのみPNG画像を返すよう変更（それ以外の
  レインウェア・アクセサリー・キャップ・ポールは引き続き自作SVGのまま）
- 実サイズ（24px〜64px）で表示確認済み。線が潰れず、靴・バックパック・ウェアと
  はっきり分かる仕上がり
- ロゴ・ブランド名は写っておらず、汎用的なギアの線画のため著作権面でも問題なし

商品カード・カテゴリタイル・ギアタイプ帯など、アイコンが使われる全箇所に自動的に反映
されます。

## 商品の実写真を5点に導入 + 残りの取得方法を確立（今回、重要）
「商品ビジュアルが分からないとギアライブラリの役割を果たしていない」というFBを受け、
実写真を正規に取得する方法を確立しました。

**発見した方法**：楽天市場・各ブランドの日本公式ストア（Shopify製サイトが多い）の商品
ページには、SNSシェア用の`meta-og:image`タグに実際の商品写真URLが公開情報として
含まれています。これを`web_fetch`で取得すれば、Amazon画像のような著作権グレーな
手法を使わずに、正規の商品写真を表示できます。

**今回実装した5点**（`gear-items.json`の`images`フィールドに実URLを設定済み）：
- Hyperlite Junction 40（楽天「Founder」店）
- Hyperlite Pod（楽天「Americana」店）
- Klättermusen Mithril Jacket（Klättermusen Japan公式）— 価格・重量も実データに
  修正（¥49,500・467g）
- Pa'lante Joey（Pa'lante Japan公式）— 24L・405gに修正
- Pa'lante V2（Pa'lante Japan公式）— 31L/37L・¥44,000に修正

商品カードのビジュアル欄は、写真がある場合は正方形に近い比率（4:3）、ない場合は
アイコンバッジ表示、と自動的に切り替わる仕組みになっています。

**残り25商品への展開方法**：同じ手順（各商品の日本公式ストアの商品ページURLを
`web_fetch`→`meta-og:image`の値を抽出→`images`フィールドに設定）を繰り返せば
対応可能です。すでに`japanUrl`が設定されている商品は多くが対応可能なはずです。
BLACKYAK（BUYMA経由）等、公式ストアがない商品は今まで通りアイコン表示のままになります。

※このサンドボックス環境は外部画像サーバーへの直接アクセスができないため、実際の
表示確認は本番環境（tozan-navi.com）で行ってください。URLは実在するものです。

## BLACKYAKに購入可能サイト(BUYMA)を追加（今回）
BLACKYAKは公式の日本語通販サイトがないため、これまで購入リンクを設定していませんでした。
BUYMA（大手の個人輸入代行サービス、運営：エニグモ株式会社・東証プライム上場）に公式
ブランドページがあり、うちで紹介している商品（Public Climbing 2L Gore-Tex WSP Jacket）と
完全に一致する出品も確認できたため、追加しました。
- BUYMAは「公式代理店」ではなく個人輸入代行マーケットプレイスのため、他ブランドの
  「日本公式サイトへ」とは区別して**「BLACKYAKをBUYMAで見る（個人輸入代行）」**という
  ラベルに変更（誤解を招かないよう明記）
- Public Climbing 2L Gore-Tex WSP Jacketは実際の出品価格（¥32,100）に更新
- ラベルを個別に指定できる`japanUrlLabel`フィールドを追加（ブランド・商品どちらにも設定可）

## 「公式サイト」ボタンが海外サイトのままだった問題を修正（今回、重要）
CAYL・Hyperlite・Klättermusen・NORRØNA・Houdini・AKUの6ブランドで、ブランド紹介文には
「日本正規代理店あり」等と書きながら、実際の「公式サイトへ」ボタンは英語/韓国語の海外
本国サイトにリンクしていました。実在する日本の代理店・取扱店を調査し、修正しました。

| ブランド | 日本語サイト（今回追加） |
|---|---|
| CAYL | techcountry.jp（国内セレクトショップ） |
| Hyperlite Mountain Gear | techcountry.jp |
| Klättermusen | klattermusen.jp（日本正規輸入総販売代理店） |
| NORRØNA | norrona.jp（フルマークス運営） |
| Houdini | fullmarksstore.jp |
| AKU | ishii-sports.com（石井スポーツ、30年以上の正規代理店） |

- ブランド詳細ページのメインCTAボタンを、日本語サイトがある場合はそちらを主導線に変更
  （海外本国サイトは「海外本国サイトはこちら」という補助リンクに降格）
- 該当ブランドの商品カードにも「日本正規代理店で見る」リンクを追加（15商品）
- Cotopaxi・Fjällräven・Rab・Merrell・LOWAはもともと`officialUrl`が日本語サイトだったため
  変更なし。BLACKYAKのみ引き続き公式の日本語サイトなし（個人輸入代行が中心である旨は
  既に明記済み）

## Instagram実装方式について（重要な変更）
当初、Instagram公式の`<blockquote class="instagram-media">` + `embed.js`によるJS埋め込みを
実装していましたが、実機確認でビジュアルカードが描画されずフォールバックのテキストリンクしか
表示されない問題が発覚しました。調査の結果、2020年以降Meta側の埋め込み仕様が不安定化して
おり（広告ブロッカー・CSP設定・ログイン要求等で頻繁に失敗）、JS依存の埋め込みは本質的に
信頼性が低いことが判明しました。

そのため、**Meta側のAPIやスクリプトに一切依存しない、独自SVGアイコン＋ブランドカラーの
静的リンクカード方式**に切り替えました。見た目はシンプルになりましたが、確実に表示され、
サイトの他のオリジナルアイコンとのデザイン統一性も高まっています。

## 既知の未対応・次にやること
1. **AKU・LOWAのInstagramリンク**：確度の高い投稿URLがまだ見つかっていません
2. **山ページ側への「おすすめギア」統合**：`mountain-gear-links.json`は生成済みですが、
   155の山ページへの一括挿入は横断検索・全数検証が必要な作業のため未着手です
3. **Pa'lante・Klättermusen・NORRØNA・Houdini・Rab・BLACKYAK・AKUのヒーロー画像**：
   まだ専用画像がありません
4. **楽天リンクのアフィリエイトラッピング**：公開前にA8.net等で変換が必要
5. **商品詳細ページ・フィルターUI付き商品一覧**：データ構造は対応済みですが、
   専用ページ・UIは未実装（Phase 2として提案済み）
6. **ウェア/シューズカテゴリアイコンのブラッシュアップ**：現在調整中。大サイズで
   設計したジャケットアイコンの座標データは`/tmp`に一時保存されており、承認され次第
   本実装に反映予定
