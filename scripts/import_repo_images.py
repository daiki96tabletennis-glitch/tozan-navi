#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""管理画面の「山画像を管理」が GitHub に直接書いた変更を、作業フォルダ（Desktop）に取り込む。公開のコピーの前に必ず実行する。
画像ツールは GitHub のリポジトリに、写真のファイル（images/mountains/<山ID>/）・data/mountains.json の photos・data/image-credits.json を書く。
作業フォルダには入らないので、そのままコピーすると写真の追加・削除・並べ替えが古い内容で上書きされて消える（2026-08〜09 に13山で起きた）。

  python3 scripts/import_repo_images.py            取り込む（前回から増えた [images] のコミットの山だけ）
  python3 scripts/import_repo_images.py --dry-run  何を取り込むかだけ表示

取り込むもの：その山の photos（リポジトリの値に合わせる）、data/image-credits.json のその山の分、写真のファイル（増えたものだけ。消さない）。
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
    for line in log.split('\n') if log else []:
        h, s = line.split('|', 1)
        m = re.match(r'\[images\] (.+?)の(写真|画像|不要画像|写真クレジット)', s)
        if m:
            names.add(m.group(1))
    if not names:
        print('取り込む画像の変更はありません')
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
    if not dry:
        json.dump({'commit': head}, open(STATE, 'w'))


if __name__ == '__main__':
    main()
