"""Theme sáng/tối của GUI. Logic thuần để test được mà không cần mở cửa sổ."""

from __future__ import annotations

import customtkinter as ctk

THEME_DARK = "Dark"
THEME_LIGHT = "Light"


def next_theme(current: str) -> str:
    """Theme kế tiếp cho nút đổi giao diện tối/sáng."""
    return THEME_LIGHT if current == THEME_DARK else THEME_DARK


def apply_default_theme() -> None:
    """Theme mặc định khi mở app."""
    ctk.set_appearance_mode(THEME_DARK)
    ctk.set_default_color_theme("blue")
