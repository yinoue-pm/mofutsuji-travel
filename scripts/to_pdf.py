#!/usr/bin/env python3
"""PDF ビルド: 生成済み HTML → A4 PDF（Playwright / Chromium）。

print CSS をそのまま使い、背景色・装飾を保持して出力します。

事前準備（初回のみ）:
    pip install playwright
    python -m playwright install chromium

使い方:
    python scripts/to_pdf.py                          # dist/index.html → dist/itinerary.pdf
    python scripts/to_pdf.py dist/index.html out.pdf

代替手段（Playwright を入れたくない場合）:
    - ブラウザで dist/index.html を開き「印刷 → PDF として保存」
      ※「背景のグラフィック」を ON にすること（本テンプレートは print-color-adjust:exact 済）
    - もしくは weasyprint（pip install weasyprint）。ただし flex/grid 等の対応が限定的で
      レイアウトが簡略化されるため、忠実性は Chromium に劣る。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def to_pdf(html_path: Path, pdf_path: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "✗ Playwright 未インストール。\n"
            "    pip install playwright && python -m playwright install chromium\n"
            "  もしくはブラウザの「印刷 → PDF 保存」（背景のグラフィック ON）を利用してください。",
            file=sys.stderr,
        )
        raise SystemExit(3)

    url = html_path.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # ネットワーク（Web フォント CDN）の読み込み完了を待つ
        page.goto(url, wait_until="networkidle")
        # 出現演出を確実に確定させる（reveal を強制表示）
        page.emulate_media(media="print")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,           # 背景色・装飾を保持（最重要）
            prefer_css_page_size=True,        # @page size を尊重
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="HTML から A4 PDF を生成（Playwright/Chromium）")
    ap.add_argument("input", nargs="?", default=str(ROOT / "dist" / "index.html"), help="入力 HTML")
    ap.add_argument("output", nargs="?", default=str(ROOT / "dist" / "itinerary.pdf"), help="出力 PDF")
    args = ap.parse_args()

    html_path = Path(args.input)
    if not html_path.exists():
        print(f"✗ HTML が見つかりません: {html_path}\n  先に `python scripts/build.py` を実行してください。", file=sys.stderr)
        return 2

    pdf_path = Path(args.output)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    to_pdf(html_path, pdf_path)
    size_kb = pdf_path.stat().st_size / 1024
    print(f"✓ PDF 生成: {pdf_path}  ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
