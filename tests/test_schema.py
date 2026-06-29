"""データ検証（src.schema）のユニットテスト。"""
import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.schema import ValidationError, parse_document  # noqa: E402


def _valid_raw():
    return {
        "meta": {"title": "テスト旅程"},
        "theme": "onsen",
        "sections": [
            {
                "label": "1日目",
                "date": "7/6",
                "weekday": "月",
                "dist_km": 100,
                "items": [
                    {"time": "9:00", "type": "meal", "title": "朝食", "cost": 1000},
                    {
                        "time": "17:00",
                        "type": "lodging",
                        "title": "宿",
                        "rating": 4.2,
                        "card": {"name": "温泉", "spring": "単純泉", "price": 10000, "discount": -1000},
                    },
                ],
            }
        ],
        "summary": {"total": 10000, "breakdown": [{"label": "宿", "amount": 11000}, {"label": "割引", "amount": -1000}]},
    }


def test_valid_document_parses():
    doc = parse_document(_valid_raw())
    assert doc.meta.title == "テスト旅程"
    assert len(doc.sections) == 1
    assert doc.item_count == 2
    assert doc.lodging_count == 1


def test_missing_title_fails():
    raw = _valid_raw()
    del raw["meta"]["title"]
    with pytest.raises(ValidationError) as ei:
        parse_document(raw)
    assert any("meta.title" in e for e in ei.value.errors)


def test_no_sections_fails():
    raw = _valid_raw()
    raw["sections"] = []
    with pytest.raises(ValidationError) as ei:
        parse_document(raw)
    assert any("sections" in e for e in ei.value.errors)


def test_bad_type_fails():
    raw = _valid_raw()
    raw["sections"][0]["items"][0]["type"] = "spaceship"
    with pytest.raises(ValidationError) as ei:
        parse_document(raw)
    assert any("type" in e for e in ei.value.errors)


def test_summary_total_mismatch_fails():
    raw = _valid_raw()
    raw["summary"]["total"] = 999  # 内訳合計と不一致
    with pytest.raises(ValidationError) as ei:
        parse_document(raw)
    assert any("一致しません" in e for e in ei.value.errors)


def test_bad_cost_type_fails():
    raw = _valid_raw()
    raw["sections"][0]["items"][0]["cost"] = "たくさん"
    with pytest.raises(ValidationError):
        parse_document(raw)


def test_empty_section_flagged():
    raw = _valid_raw()
    raw["sections"][0]["items"] = []
    with pytest.raises(ValidationError) as ei:
        parse_document(raw)
    assert any("items が空" in e for e in ei.value.errors)


def test_net_price_and_highlight():
    doc = parse_document(_valid_raw())
    lodging = doc.sections[0].items[1]
    assert lodging.is_highlight is True
    assert lodging.card.net_price == 9000
