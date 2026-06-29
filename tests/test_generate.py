"""HTML 生成（src.generator）のスナップショット的テスト：主要要素の存在確認。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import generator as G  # noqa: E402
from src.schema import parse_document  # noqa: E402

DATA = ROOT / "data" / "shikoku.yaml"


def _doc():
    return parse_document(G.load_data(str(DATA)))


def test_full_document_self_contained():
    html = G.render_document(_doc())
    # 自己完結性
    assert "<img" not in html, "画像は使用しない方針"
    assert "color-scheme: light" in html
    assert "print-color-adjust: exact" in html
    # 主要セクション
    assert "四国の旅" in html
    assert 'class="toc' in html
    assert 'class="summary reveal"' in html
    # JS 機能
    assert "IntersectionObserver" in html
    assert "window.print()" in html
    assert "localStorage" in html


def test_hero_fragment():
    h = G.render_hero(_doc())
    assert "四国の旅" in h
    assert "ルート概要" in h


def test_section_and_item_fragments():
    doc = _doc()
    sec = doc.sections[0]
    s = G.render_section(sec, 1)
    # 章扉に編集見出し（headline）とリード文が出る
    assert (sec.headline or sec.leg) in s
    if sec.lede:
        assert sec.lede in s
    assert 'class="timeline"' in s

    item = sec.items[0]
    it = G.render_item(item, sec.slug, 0)
    assert item.title in it
    assert 'data-type="' in it


def test_card_fragment_has_spring_and_price():
    doc = _doc()
    # 最初の宿泊カードを探す
    card = next(it.card for s in doc.sections for it in s.items if it.card)
    c = G.render_card(card)
    assert card.name in c
    if card.spring:
        assert card.spring in c
    assert "¥" in c


def test_summary_fragment_has_bars():
    doc = _doc()
    sm = G.render_summary(doc.summary)
    assert "bar-fill" in sm
    assert "費用集計" in sm


def test_xss_autoescape():
    """autoescape が効いていること（タイトルにタグを入れても素通りしない）。"""
    raw = {
        "meta": {"title": "<script>alert(1)</script>"},
        "sections": [{"label": "1日目", "items": [{"title": "x", "type": "sight"}]}],
    }
    html = G.render_document(parse_document(raw))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
