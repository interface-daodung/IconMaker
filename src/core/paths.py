"""Đường dẫn mặc định của app: input/ là đầu vào, output/<tool>/ là đầu ra."""

from __future__ import annotations

from pathlib import Path

INPUT_DIR = Path("input")
OUTPUT_ROOT = Path("output")
OUTPUT_ROUNDED = OUTPUT_ROOT / "rounded"
OUTPUT_SPRITES = OUTPUT_ROOT / "sprites"
OUTPUT_ICONS = OUTPUT_ROOT / "icons"
OUTPUT_RESIZE = OUTPUT_ROOT / "resize"
OUTPUT_EXPORT = OUTPUT_ROOT / "export"
OUTPUT_LAUNCHER = OUTPUT_ROOT / "launchers"
APP_ICON = Path("assets/icons/IconMaker.ico")


def app_icon_path() -> Path:
    """Đường dẫn tuyệt đối tới icon của app GUI.

    Neo theo vị trí file này (src/core/paths.py) nên đúng dù chạy
    từ thư mục nào (make run, pythonw, launcher).
    """
    root = Path(__file__).resolve().parents[2]
    return root / APP_ICON
