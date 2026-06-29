#!/usr/bin/env python3
"""動作確認用: HTML をモバイル幅・デスクトップ幅でスクリーンショット保存（開発補助）。

使い方:
    python scripts/screenshot.py            # dist/index.html を撮影 -> dist/shot-*.png
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    from playwright.sync_api import sync_playwright

    html = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "index.html"
    url = html.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, width in (("mobile", 390), ("desktop", 1100)):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(700)  # 出現演出の完了を待つ
            out = ROOT / "dist" / f"shot-{name}.png"
            page.screenshot(path=str(out), full_page=True)
            print(f"✓ {out}")
            page.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
