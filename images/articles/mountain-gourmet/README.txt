記事「山の茶屋・山小屋グルメ」（/articles/mountain-gourmet/）の写真の置き場所です。

1. 写真をこのフォルダに入れる（ファイル名は data/mountain_gourmet.json の各項目の key に合わせる。例：nabewari.jpg、tateyama-mikuri.jpg）
2. data/mountain_gourmet.json の その項目の image.src に "/images/articles/mountain-gourmet/<key>.jpg"、
   image.credit に撮影者・出典（例："撮影：Yamatch" や "提供：◯◯山荘"）を入れる
3. python3 scripts/gen_gourmet_article.py で記事を作り直す（ファイルがある項目だけ写真が出る）

横3：縦2 で表示します（はみ出す分は切り取られます）。幅1200px程度・JPEG がおすすめです。
山小屋・茶屋の写真をお店の公式サイトから無断で使わないでください（提供を受けたものか、自分で撮ったものだけ）。
