#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""管理画面の「山画像を管理」が GitHub に直接書いた変更を、作業フォルダ（Desktop）に取り込む。公開のコピーの前に必ず実行する。
画像ツールは GitHub のリポジトリに、写真のファイル（images/mountains/<山ID>/）・data/mountains.json の photos・data/image-credits.json を書く。
作業フォルダには入らないので、そのままコピーすると写真の追加・削除・並べ替えが古い内容で上書きされて消える（2026-08〜09 に13山で起きた）。

  python3 scripts/import_repo_images.py            取り込む（前回から増えた [images] のコミットの山だけ）
  python3 scripts/import_repo_images.py --dry-run  何を取り込むかだけ表示

取り込むもの：その山の photos（リポジトリの値に合わせる）、data/image-credits.json のその山の分、写真のファイル（増えたものだけ。消さない）。
管理画面の「グルメ記事の写真」（/admin/gourmet/。コミットの題が [gourmet]）の分も取り込む：data/mountain_gourmet.json の各項目の image と、
images/articles/mountain-gourmet/ の写真のファイル（無いものだけ）。取り込んだら記事を作り直す。
前回どこまで取り込んだかは .claude/repo_images_sync.json（公開のコピーには含めない）。"""
import json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = '/Users/fujita/Documents/GitHub/tozan-navi'
STATE = os.path.join(ROOT, '.claude', 'repo_images_sync.json')


def git(*a):
    return subprocess.run(['git', '-C', REPO] + list(a), capture_output=True, text=True, check=True).stdout


def main():
    dry = '--dry-run' in sys.argv
    state = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    head = git('rev-parse', 'HEAD').strip()
    since = state.get('commit')
    if not since:
        print('初回：いまの GitHub の状態を起点として記録します（過去の分は取り込みません）')
        if not dry:
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            json.dump({'commit': head}, open(STATE, 'w'))
        return
    log = git('log', '--format=%H|%s', since + '..' + head).strip()
    names = set()
    gourmet = False
    for line in log.split('\n') if log else []:
        h, s = line.split('|', 1)
        if s.startswith('[gourmet]'):
            gourmet = True
        m = re.match(r'\[images\] (.+?)の(写真|画像|不要画像|写真クレジット)', s)
        if m:
            names.add(m.group(1))
    if not names:
        print('取り込む山の画像の変更はありません')
    else:
        repo_m = {m['name']: m for m in json.loads(git('show', 'HEAD:data/mountains.json'))}
        repo_c = json.loads(git('show', 'HEAD:data/image-credits.json'))
        D = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
        C = json.load(open(os.path.join(ROOT, 'data', 'image-credits.json'), encoding='utf-8'))
        ids = []
        for m in D:
            if m['name'] in names and m['name'] in repo_m:
                rp = repo_m[m['name']].get('photos')
                print('%s：photos %s → %s' % (m['name'], len(m.get('photos') or []), len(rp or [])))
                if rp:
                    m['photos'] = rp
                else:
                    m.pop('photos', None)
                if m['id'] in repo_c:
                    C[m['id']] = repo_c[m['id']]
                ids.append(m['id'])
                src = os.path.join(REPO, 'images', 'mountains', m['id'])
                dst = os.path.join(ROOT, 'images', 'mountains', m['id'])
                for f in (os.listdir(src) if os.path.isdir(src) else []):
                    if not os.path.exists(os.path.join(dst, f)):
                        print('   写真のファイルを取り込む：', f)
                        if not dry:
                            os.makedirs(dst, exist_ok=True)
                            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        if not dry:
            json.dump(D, open(os.path.join(ROOT, 'data', 'mountains.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            json.dump(C, open(os.path.join(ROOT, 'data', 'image-credits.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            for i in ids:
                subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'gen_mountain_pages.py'), '--id', i], check=True)
    if gourmet:
        import_gourmet(dry)
    if not dry:
        json.dump({'commit': head}, open(STATE, 'w'))


def import_gourmet(dry):
    path = os.path.join(ROOT, 'data', 'mountain_gourmet.json')
    repo = {x['key']: x for x in json.loads(git('show', 'HEAD:data/mountain_gourmet.json'))['items']}
    d = json.load(open(path, encoding='utf-8'))
    changed = False
    for it in d['items']:
        r = repo.get(it['key'])
        if not r or r.get('image') == it.get('image'):
            continue
        print('グルメ記事の写真：%s %s → %s' % (it['key'], (it.get('image') or {}).get('src'), (r.get('image') or {}).get('src')))
        it['image'] = r.get('image')
        changed = True
        src = (r.get('image') or {}).get('src')
        if src:
            a, b = os.path.join(REPO, src.lstrip('/')), os.path.join(ROOT, src.lstrip('/'))
            if os.path.exists(a) and not os.path.exists(b):
                print('   写真のファイルを取り込む：', os.path.basename(b))
                if not dry:
                    os.makedirs(os.path.dirname(b), exist_ok=True)
                    shutil.copy2(a, b)
    if changed and not dry:
        json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'gen_gourmet_article.py')], check=True)
    if not changed:
        print('グルメ記事の写真：変更なし')


if __name__ == '__main__':
    main()
