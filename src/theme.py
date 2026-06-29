"""デザインテーマ（配色・フォントのトークン）。

各テーマは CSS カスタムプロパティ（``--xxx``）の値に展開され、
テンプレートの ``:root`` に流し込まれます。
白基調・高コントラストを基本とし、アクセント色だけを切り替えます。

テーマを追加したいときはこの dict に1エントリ足すだけ。
データ側 ``theme:`` キーで選択します。
"""
from __future__ import annotations

from typing import Dict

# Google Fonts CDN（本文=Noto Sans JP / 見出し=Zen Maru Gothic）。
# 読み込めない環境ではシステムフォントへ自動フォールバック（base CSS 側で指定）。
FONT_CSS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Noto+Sans+JP:wght@400;500;700&family=Zen+Maru+Gothic:wght@500;700&display=swap"
)

SYSTEM_SANS = (
    '-apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", '
    '"Hiragino Sans", "Yu Gothic", Meiryo, sans-serif'
)

# テーマトークン。キー名は CSS 変数名（先頭の `--` は付けない）。
THEMES: Dict[str, Dict[str, str]] = {
    # 温泉旅：白基調＋ぬくもりのある朱・藍
    "onsen": {
        "font-head": f'"Zen Maru Gothic", {SYSTEM_SANS}',
        "font-body": f'"Noto Sans JP", {SYSTEM_SANS}',
        "bg": "#ffffff",
        "bg-soft": "#f7f4ef",
        "surface": "#ffffff",
        "ink": "#1f2430",
        "ink-soft": "#5b6373",
        "line": "#e7e1d8",
        "accent": "#c0392b",       # 朱
        "accent-soft": "#fdecea",
        "accent-2": "#1b6ca8",     # 藍
        "accent-2-soft": "#e8f1f8",
        "gold": "#b8860b",
        "grad-from": "#c0392b",
        "grad-to": "#e67e22",
        "ok": "#2e7d32",
        "shadow": "0 6px 22px rgba(31,36,48,.08)",
    },
    # 海・しまなみ：青基調
    "ocean": {
        "font-head": f'"Zen Maru Gothic", {SYSTEM_SANS}',
        "font-body": f'"Noto Sans JP", {SYSTEM_SANS}',
        "bg": "#ffffff",
        "bg-soft": "#f1f6fa",
        "surface": "#ffffff",
        "ink": "#10233a",
        "ink-soft": "#51677e",
        "line": "#d9e6f0",
        "accent": "#0e7490",
        "accent-soft": "#e2f4f8",
        "accent-2": "#1d4ed8",
        "accent-2-soft": "#e6edfd",
        "gold": "#b8860b",
        "grad-from": "#0e7490",
        "grad-to": "#1d4ed8",
        "ok": "#2e7d32",
        "shadow": "0 6px 22px rgba(16,35,58,.10)",
    },
    # 高コントラスト・モノトーン（レポート向け）
    "mono": {
        "font-head": f'"Zen Maru Gothic", {SYSTEM_SANS}',
        "font-body": f'"Noto Sans JP", {SYSTEM_SANS}',
        "bg": "#ffffff",
        "bg-soft": "#f4f4f5",
        "surface": "#ffffff",
        "ink": "#111111",
        "ink-soft": "#555555",
        "line": "#e2e2e2",
        "accent": "#111111",
        "accent-soft": "#ededed",
        "accent-2": "#444444",
        "accent-2-soft": "#eeeeee",
        "gold": "#7a6212",
        "grad-from": "#111111",
        "grad-to": "#555555",
        "ok": "#1b5e20",
        "shadow": "0 6px 22px rgba(0,0,0,.08)",
    },
}

DEFAULT_THEME = "onsen"


def get_theme(key: str) -> Dict[str, str]:
    """テーマキーからトークン dict を取得（未知のキーは既定テーマ）。"""
    return THEMES.get(key, THEMES[DEFAULT_THEME])


def theme_css_vars(key: str) -> str:
    """``:root`` に流し込む CSS 変数文字列を生成。"""
    tokens = get_theme(key)
    return "\n".join(f"      --{name}: {value};" for name, value in tokens.items())
