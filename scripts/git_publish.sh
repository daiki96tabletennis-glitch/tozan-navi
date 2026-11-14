#!/usr/bin/env bash
# 定期実行（GitHub Actions）が、変えたファイルをコミットして送る（2026-11-15〜）
#
#   bash scripts/git_publish.sh "<コミットの題>" "<お知らせを作り直すコマンド（無ければ空）>" <ファイル・フォルダ>...
#
# 前は「コミット → git pull --rebase → push」だったが、複数の定期実行が同じ朝に data/admin_notices.json の同じ行
# （updatedAt）を書き換えるため、取り込みがぶつかって止まっていた（山小屋の定期更新が 2026-10〜11 に35回中20回失敗）。
# また、公開のコピーで同じファイル（data/article_rank.json など）が古い版で送られると、そこでもぶつかった。
# そこで、送る前に GitHub の最新の状態を取り直し、その上に自分の変更を乗せ直す（同じファイルをほかの人も変えていたら3方向で合わせる）。
# お知らせのファイル（data/admin_notices.json）は退避せず、最新のものの上に、渡されたコマンドで作り直す
# （ほかの定期実行が書いたお知らせを消さないため）。送れなければ、少し待って5回までやり直す。
set -u
msg="$1"; regen="$2"; shift 2
NOTICE=data/admin_notices.json
branch=$(git rev-parse --abbrev-ref HEAD)
base=$(git rev-parse HEAD)   # 取り出したときの状態（ほかの人が同じファイルを変えたかを見るため）
tmp=$(mktemp -d)
# 自分の変更を退避する（お知らせのファイルは除く）
for p in "$@"; do
  if [ "$p" != "$NOTICE" ] && [ -e "$p" ]; then
    mkdir -p "$tmp/$(dirname "$p")"
    cp -a "$p" "$tmp/$p"
  fi
done
git config user.name >/dev/null || git config user.name "yamatch-actions"
git config user.email >/dev/null || git config user.email "actions@users.noreply.github.com"
for i in 1 2 3 4 5; do
  git fetch -q origin "$branch" || { sleep 10; continue; }
  git reset -q --hard "origin/$branch"
  # 自分の変更を乗せ直す。ファイルは、取り出したあとにほかの人も変えていたら（公開のコピーでサイトマップが変わったなど）
  # 3方向で合わせる（両方の変更を入れる）。合わせられないときは自分の版を使い、そのことを書き出す。フォルダはそのまま上書き
  for p in "$@"; do
    [ "$p" = "$NOTICE" ] && continue
    [ -e "$tmp/$p" ] || continue
    if [ -d "$tmp/$p" ]; then mkdir -p "$p"; cp -a "$tmp/$p/." "$p/"; continue; fi
    if [ -f "$p" ] && git cat-file -e "$base:$p" 2>/dev/null && ! git diff --quiet "$base" HEAD -- "$p"; then
      git show "$base:$p" > "$tmp/.base"
      if git merge-file -p "$tmp/$p" "$tmp/.base" "$p" > "$tmp/.merged" 2>/dev/null; then
        cp "$tmp/.merged" "$p"; echo "合わせた：$p（ほかの変更も入れた）"
      else
        cp -a "$tmp/$p" "$p"; echo "合わせられなかったので自分の版を使った：$p"
      fi
    else
      mkdir -p "$(dirname "$p")"; cp -a "$tmp/$p" "$p"
    fi
  done
  if [ -n "$regen" ]; then bash -c "$regen" || echo "お知らせの作り直しに失敗（続けます）"; fi
  for p in "$@"; do
    if [ -e "$p" ]; then git add -A "$p"; fi
  done
  if git diff --cached --quiet; then echo "変化なし"; exit 0; fi
  git commit -q -m "$msg"
  if git push -q origin "HEAD:$branch"; then echo "送りました（${i}回目）"; exit 0; fi
  echo "送れなかったので取り直してやり直します（${i}回目）"
  sleep $((RANDOM % 20 + 10))
done
echo "5回やり直しても送れませんでした"
exit 1
