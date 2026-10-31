"""サンプルの index.html に共通の演出（fx.js）を差し込む。何度流しても同じ結果になる。

使い方:
  python scripts/sample-fx/enhance.py <リポジトリのフォルダ> --accent "#c8922a" [--mode rise|drift] [--light] [--file index.html]
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
START = '<!-- kfx:start -->'
END = '<!-- kfx:end -->'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--accent', required=True)
    ap.add_argument('--mode', default='drift', choices=['rise', 'drift'])
    ap.add_argument('--light', action='store_true')
    ap.add_argument('--file', default='index.html')
    a = ap.parse_args()

    path = pathlib.Path(a.folder) / a.file
    html = path.read_text(encoding='utf-8')
    fx = (HERE / 'fx.js').read_text(encoding='utf-8')

    block = (
        f'{START}\n'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js" integrity="sha384-g4NTh/Iv5PPU4xPyhEWqPcwtNXOvdaDI8LLnyYfyNZOjKJeYQyjzQ9X5275eBjpt" crossorigin="anonymous"></script>\n'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js" integrity="sha384-Z3REaz79l2IaAZqJsSABtTbhjgOUYyV3p90XNnAPCSHg3EMTz1fouunq9WZRtj3d" crossorigin="anonymous"></script>\n'
        f'<script>window.KFX={{accent:"{a.accent}",mode:"{a.mode}",light:{"true" if a.light else "false"}}};</script>\n'
        f'<script>\n{fx}\n</script>\n'
        f'{END}\n'
    )

    html = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n?', '', html, flags=re.S)
    if '</body>' not in html:
        sys.exit('</body> が見つかりません')
    html = html.replace('</body>', block + '</body>', 1)
    path.write_text(html, encoding='utf-8', newline='')
    print('OK', path)


if __name__ == '__main__':
    main()
