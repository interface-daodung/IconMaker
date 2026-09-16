"""Đăng ký các tool hiển thị thành tab trong cửa sổ chính."""

from __future__ import annotations

from dataclasses import dataclass

from gui.base_tool import ToolTab
from tools import (
    export_tool,
    foldericon_tool,
    icons_tool,
    junction_tool,
    launcher_tool,
    resize_tool,
    rounded_tool,
    sprites_tool,
)


@dataclass(frozen=True)
class ToolSpec:
    title: str
    tab_class: type[ToolTab]


def get_tools() -> list[ToolSpec]:
    """Danh sách tool theo thứ tự tab hiển thị."""
    return [
        ToolSpec(export_tool.Tab.title, export_tool.Tab),
        ToolSpec(rounded_tool.Tab.title, rounded_tool.Tab),
        ToolSpec(resize_tool.Tab.title, resize_tool.Tab),
        ToolSpec(sprites_tool.Tab.title, sprites_tool.Tab),
        ToolSpec(icons_tool.Tab.title, icons_tool.Tab),
        ToolSpec(foldericon_tool.Tab.title, foldericon_tool.Tab),
        ToolSpec(junction_tool.Tab.title, junction_tool.Tab),
        ToolSpec(launcher_tool.Tab.title, launcher_tool.Tab),
    ]
