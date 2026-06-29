"""データスキーマの定義・検証・正規化。

入力 YAML/JSON を Python の dataclass へマッピングし、

* 必須フィールド欠落
* 型不一致
* 空セクション
* 集計合計の不整合

を **ビルド前** に検出します（早期に失敗させ、壊れた HTML を出さない）。

Python 3.9 互換のため ``Optional[...]`` / ``List[...]`` 記法を使用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """入力データが不正なときに送出。``errors`` に全件をまとめて格納する。"""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("入力データの検証に失敗しました:\n" + "\n".join(f"  - {e}" for e in errors))


# 種別 → アイコンキー / 表示ラベルのマッピング（テンプレート側で使用）
ITEM_TYPES = {
    "meal": "食事",
    "sight": "観光",
    "drive": "移動",
    "ferry": "航路",
    "lodging": "宿泊",
}
DEFAULT_TYPE = "sight"


# --------------------------------------------------------------------------- #
# dataclass 群（必須=引数なし / 任意=デフォルト付き）
# --------------------------------------------------------------------------- #
@dataclass
class LodgingCard:
    """宿泊などの強調カード。温泉なら泉質・効能を持つ。"""

    name: str
    address: Optional[str] = None
    tel: Optional[str] = None
    room: Optional[str] = None
    plan: Optional[str] = None
    spring: Optional[str] = None        # 泉質
    benefits: Optional[str] = None      # 効能
    price: Optional[int] = None
    discount: Optional[int] = None      # 負数（割引）
    discount_label: Optional[str] = None

    @property
    def net_price(self) -> Optional[int]:
        if self.price is None:
            return None
        return self.price + (self.discount or 0)


@dataclass
class Item:
    title: str
    type: str = DEFAULT_TYPE
    time: Optional[str] = None
    desc: Optional[str] = None
    cost: Optional[int] = None
    cost_label: Optional[str] = None
    rating: Optional[float] = None
    card: Optional[LodgingCard] = None

    @property
    def is_highlight(self) -> bool:
        """強調表示（カード付き or 高評価）の対象か。"""
        return self.card is not None or (self.rating is not None and self.rating >= 4.0)


@dataclass
class Section:
    label: str
    date: Optional[str] = None
    weekday: Optional[str] = None
    leg: Optional[str] = None
    dist_km: Optional[int] = None
    items: List[Item] = field(default_factory=list)

    @property
    def slug(self) -> str:
        """目次アンカー用の id。"""
        return "day-" + str(self.label).replace(" ", "").replace("日目", "")


@dataclass
class SummaryRow:
    label: str
    amount: int


@dataclass
class Summary:
    total: int
    breakdown: List[SummaryRow] = field(default_factory=list)
    note: Optional[str] = None


@dataclass
class HeroStat:
    label: str
    value: str
    unit: Optional[str] = None
    icon: Optional[str] = None


@dataclass
class Meta:
    title: str
    subtitle: Optional[str] = None
    period: Optional[str] = None
    route: Optional[str] = None
    created: Optional[str] = None


@dataclass
class Document:
    meta: Meta
    sections: List[Section]
    theme: str = "onsen"
    hero_stats: List[HeroStat] = field(default_factory=list)
    summary: Optional[Summary] = None

    # ---- 派生プロパティ（テンプレート/テストから利用） ----
    @property
    def item_count(self) -> int:
        return sum(len(s.items) for s in self.sections)

    @property
    def lodging_count(self) -> int:
        return sum(1 for s in self.sections for it in s.items if it.card is not None)


# --------------------------------------------------------------------------- #
# 検証 & 正規化
# --------------------------------------------------------------------------- #
def _as_int(value: Any, where: str, errors: List[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        errors.append(f"{where}: 数値であるべき値が不正です（{value!r}）")
        return None


def _as_float(value: Any, where: str, errors: List[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{where}: 数値（評価）であるべき値が不正です（{value!r}）")
        return None


def parse_document(raw: Dict[str, Any]) -> Document:
    """生 dict → ``Document``。不正があれば ``ValidationError`` を送出する。"""
    errors: List[str] = []

    if not isinstance(raw, dict):
        raise ValidationError(["ルートはマッピング（オブジェクト）である必要があります"])

    # ---- meta（必須: title） ----
    raw_meta = raw.get("meta") or {}
    if not raw_meta.get("title"):
        errors.append("meta.title は必須です")
    meta = Meta(
        title=str(raw_meta.get("title", "（無題）")),
        subtitle=raw_meta.get("subtitle"),
        period=raw_meta.get("period"),
        route=raw_meta.get("route"),
        created=raw_meta.get("created"),
    )

    # ---- hero_stats（任意） ----
    hero_stats: List[HeroStat] = []
    for i, hs in enumerate(raw.get("hero_stats") or []):
        if not isinstance(hs, dict) or "value" not in hs or "label" not in hs:
            errors.append(f"hero_stats[{i}]: label と value は必須です")
            continue
        hero_stats.append(
            HeroStat(label=str(hs["label"]), value=str(hs["value"]), unit=hs.get("unit"), icon=hs.get("icon"))
        )

    # ---- sections（必須: 1件以上） ----
    sections: List[Section] = []
    raw_sections = raw.get("sections") or []
    if not raw_sections:
        errors.append("sections が空です（最低1セクション必要）")

    for si, rs in enumerate(raw_sections):
        if not isinstance(rs, dict):
            errors.append(f"sections[{si}]: マッピングである必要があります")
            continue
        if not rs.get("label"):
            errors.append(f"sections[{si}].label は必須です")
        items: List[Item] = []
        for ii, ri in enumerate(rs.get("items") or []):
            where = f"sections[{si}].items[{ii}]"
            if not isinstance(ri, dict):
                errors.append(f"{where}: マッピングである必要があります")
                continue
            if not ri.get("title"):
                errors.append(f"{where}.title は必須です")
            itype = ri.get("type", DEFAULT_TYPE)
            if itype not in ITEM_TYPES:
                errors.append(f"{where}.type が不正です（{itype!r}）。許可: {list(ITEM_TYPES)}")
            card = None
            if ri.get("card"):
                rc = ri["card"]
                if not isinstance(rc, dict) or not rc.get("name"):
                    errors.append(f"{where}.card.name は必須です")
                    rc = rc if isinstance(rc, dict) else {}
                card = LodgingCard(
                    name=str(rc.get("name", "")),
                    address=rc.get("address"),
                    tel=rc.get("tel"),
                    room=rc.get("room"),
                    plan=rc.get("plan"),
                    spring=rc.get("spring"),
                    benefits=rc.get("benefits"),
                    price=_as_int(rc.get("price"), f"{where}.card.price", errors),
                    discount=_as_int(rc.get("discount"), f"{where}.card.discount", errors),
                    discount_label=rc.get("discount_label"),
                )
            items.append(
                Item(
                    title=str(ri.get("title", "")),
                    type=itype if itype in ITEM_TYPES else DEFAULT_TYPE,
                    time=ri.get("time"),
                    desc=ri.get("desc"),
                    cost=_as_int(ri.get("cost"), f"{where}.cost", errors),
                    cost_label=ri.get("cost_label"),
                    rating=_as_float(ri.get("rating"), f"{where}.rating", errors),
                    card=card,
                )
            )
        if not items:
            # 空セクションは警告レベル：除外せず残すが、テンプレートで「予定なし」表示
            errors.append(f"sections[{si}]（{rs.get('label')}）: items が空です")
        sections.append(
            Section(
                label=str(rs.get("label", f"#{si + 1}")),
                date=rs.get("date"),
                weekday=rs.get("weekday"),
                leg=rs.get("leg"),
                dist_km=_as_int(rs.get("dist_km"), f"sections[{si}].dist_km", errors),
                items=items,
            )
        )

    # ---- summary（任意。あれば合計整合性を検査） ----
    summary = None
    raw_summary = raw.get("summary")
    if raw_summary:
        rows = [
            SummaryRow(label=str(r.get("label", "?")), amount=_as_int(r.get("amount"), "summary.breakdown", errors) or 0)
            for r in (raw_summary.get("breakdown") or [])
        ]
        total = _as_int(raw_summary.get("total"), "summary.total", errors)
        if total is not None and rows:
            calc = sum(r.amount for r in rows)
            if calc != total:
                errors.append(f"summary.total({total:,}) が内訳合計({calc:,})と一致しません")
        summary = Summary(total=total or 0, breakdown=rows, note=raw_summary.get("note"))

    if errors:
        raise ValidationError(errors)

    return Document(meta=meta, sections=sections, theme=str(raw.get("theme", "onsen")), hero_stats=hero_stats, summary=summary)
