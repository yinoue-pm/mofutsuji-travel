"""PDF 出力の簡易チェック（Playwright 必須。未導入なら自動スキップ）。

- PDF が生成されページ数が 1 以上
- 操作系ボタン（PDF・印刷）が印刷時に非表示
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

playwright = pytest.importorskip("playwright")  # 未導入ならスキップ
from playwright.sync_api import sync_playwright  # noqa: E402

from src import generator as G  # noqa: E402
from src.schema import parse_document  # noqa: E402
from scripts.to_pdf import to_pdf  # noqa: E402

DATA = ROOT / "data" / "shikoku.yaml"


@pytest.fixture(scope="module")
def built_html(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist") / "index.html"
    html = G.render_document(parse_document(G.load_data(str(DATA))))
    out.write_text(html, encoding="utf-8")
    return out


def _chromium_available():
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            b.close()
        return True
    except Exception:
        return False


def test_pdf_generated(built_html, tmp_path):
    if not _chromium_available():
        pytest.skip("Chromium 未インストール（python -m playwright install chromium）")
    pdf = tmp_path / "out.pdf"
    to_pdf(built_html, pdf)
    assert pdf.exists()
    assert pdf.stat().st_size > 5000  # それなりのサイズ
    assert pdf.read_bytes().startswith(b"%PDF")


def test_print_hides_controls(built_html):
    if not _chromium_available():
        pytest.skip("Chromium 未インストール")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(built_html.resolve().as_uri(), wait_until="networkidle")
        page.emulate_media(media="print")
        # .no-print 要素は印刷メディアで display:none
        hidden = page.eval_on_selector(
            "#printBtn", "el => getComputedStyle(el.closest('.no-print') || el).display"
        )
        assert hidden == "none"
        browser.close()
