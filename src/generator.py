"""データ → HTML 生成エンジン。

責務ごとに関数を分割（テストでフラグメント単位の存在確認をしやすくするため）:

    load_data(path)            : YAML/JSON を dict で読み込む
    render_hero(doc)           : hero（タイトル＋統計＋ルート）HTML 断片
    render_section(section)    : 1日分のセクション HTML 断片
    render_item(item, ...)     : タイムライン1アイテム HTML 断片
    render_card(card)          : 宿泊強調カード HTML 断片
    render_summary(summary)    : 集計（横棒グラフ）HTML 断片
    render_document(doc)       : 単一 HTML（CSS/JS インライン）全体

いずれも Jinja2 のマクロを薄くラップする。テンプレートは ``templates/`` 配下。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import theme as theme_mod
from .schema import Document, Section, Item, LodgingCard, Summary, parse_document

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"


# --------------------------------------------------------------------------- #
# 入力読み込み
# --------------------------------------------------------------------------- #
def load_data(path: str) -> Dict[str, Any]:
    """拡張子から YAML / JSON を判別して dict で返す。"""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(text)
    elif p.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        # 拡張子不明: まず YAML として試す（JSON は YAML のスーパーセットでない点に注意）
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError:
            data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: ルートはマッピングである必要があります")
    return data


def load_document(path: str) -> Document:
    """読み込み＋検証まで一括。"""
    return parse_document(load_data(path))


# --------------------------------------------------------------------------- #
# Jinja2 環境（autoescape で XSS 対策）
# --------------------------------------------------------------------------- #
_env: Optional[Environment] = None


def build_env() -> Environment:
    global _env
    if _env is None:
        _env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "xml", "j2", "html.j2"], default_for_string=True),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    return _env


def _macros():
    """マクロモジュール（Python から個別マクロを呼べる）。"""
    return build_env().get_template("macros.html.j2").module


# --------------------------------------------------------------------------- #
# フラグメント描画関数（テスト・部分生成用）
# --------------------------------------------------------------------------- #
def render_hero(doc: Document) -> str:
    return str(_macros().hero(doc))


def render_section(section: Section, no: int = 1) -> str:
    return str(_macros().section(section, no))


def render_item(item: Item, sec_slug: str = "day-x", idx: int = 0) -> str:
    return str(_macros().timeline_item(item, sec_slug, idx))


def render_card(card: LodgingCard) -> str:
    return str(_macros().lodging_card(card))


def render_summary(summary: Summary) -> str:
    return str(_macros().cost_summary(summary))


# --------------------------------------------------------------------------- #
# ドキュメント全体
# --------------------------------------------------------------------------- #
def _slugify(text: str) -> str:
    s = re.sub(r"[^0-9A-Za-z\-]+", "-", text).strip("-").lower()
    return s or "doc"


def _photo_exists(path: Optional[str]) -> bool:
    """写真パスがリポジトリ直下から見て実在するか（相対パスのみ対象）。"""
    if not path:
        return False
    if path.startswith(("http://", "https://", "data:")):
        return True
    return (ROOT / path).exists()


def resolve_photos(doc: Document) -> None:
    """存在しない写真参照を None 化（壊れ画像を出さない）。in-place で更新。"""
    if not _photo_exists(doc.meta.hero_photo):
        doc.meta.hero_photo = None
    if doc.meta.map and doc.meta.map.get("image") and not _photo_exists(doc.meta.map["image"]):
        doc.meta.map.pop("image", None)
    for sec in doc.sections:
        for it in sec.items:
            if not _photo_exists(it.photo):
                it.photo = None
            if it.card:
                if not _photo_exists(it.card.photo):
                    it.card.photo = None
                if it.card.photos:
                    it.card.photos = [p for p in it.card.photos if _photo_exists(p)] or None


def render_document(doc: Document) -> str:
    """単一 HTML（CSS/JS インライン）を文字列で返す。"""
    resolve_photos(doc)
    env = build_env()
    tmpl = env.get_template("base.html.j2")
    return tmpl.render(
        doc=doc,
        theme_css_vars=theme_mod.theme_css_vars(doc.theme),
        font_css_url=theme_mod.FONT_CSS_URL,
        store_key=_slugify(doc.meta.title),
    )


def build(input_path: str) -> str:
    """入力パス → 完成 HTML 文字列（読み込み・検証・描画を一括）。"""
    return render_document(load_document(input_path))
