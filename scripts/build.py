#!/usr/bin/env python3
"""HTML ビルド: データ(YAML/JSON) → 単一 HTML を dist/ に出力。

使い方:
    python scripts/build.py                         # data/shikoku.yaml → dist/index.html
    python scripts/build.py data/foo.yaml           # 入力を指定
    python scripts/build.py data/foo.yaml out.html  # 出力先も指定

公開用に index.html をリポジトリ直下にもコピーしたい場合は --root を付与:
    python scripts/build.py --root
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# src/ をインポートパスに追加（リポジトリ直下から実行する想定）
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.generator import build  # noqa: E402
from src.schema import ValidationError  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="構造化データから単一 HTML を生成")
    ap.add_argument("input", nargs="?", default=str(ROOT / "data" / "shikoku.yaml"), help="入力 YAML/JSON")
    ap.add_argument("output", nargs="?", default=str(ROOT / "dist" / "index.html"), help="出力 HTML パス")
    ap.add_argument("--root", action="store_true", help="リポジトリ直下にも index.html を出力（Pages 公開用）")
    args = ap.parse_args()

    try:
        html = build(args.input)
    except ValidationError as e:
        print("✗ データ検証エラー:", file=sys.stderr)
        for err in e.errors:
            print(f"   - {err}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print(f"✗ 入力ファイルが見つかりません: {args.input}", file=sys.stderr)
        return 2

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    size_kb = len(html.encode("utf-8")) / 1024
    print(f"✓ HTML 生成: {out}  ({size_kb:.1f} KB)")

    # 出力先が ROOT 以外なら assets/ を隣にコピー（相対パス参照を成立させる：dist/・_site/ 用）
    import shutil
    assets = ROOT / "assets"
    if assets.is_dir() and out.parent.resolve() != ROOT.resolve():
        shutil.copytree(assets, out.parent / "assets", dirs_exist_ok=True)
        print(f"✓ assets コピー: {out.parent / 'assets'}")

    if args.root:
        root_index = ROOT / "index.html"
        root_index.write_text(html, encoding="utf-8")
        print(f"✓ 公開用コピー: {root_index}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
