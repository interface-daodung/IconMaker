"""Entry point GUI IconMaker — mở được trực tiếp bằng shortcut `pythonw src/main.py`.

Không phụ thuộc PYTHONPATH: tự thêm thư mục `src/` vào sys.path nên chạy được
từ bất kỳ thư mục làm việc nào. Mọi đường dẫn input/output neo theo file này.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _bootstrap() -> Path:
    """Thêm `src/` vào sys.path và neo cwd về gốc project, trả về gốc project."""
    src_dir = Path(__file__).resolve().parent
    root = src_dir.parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    os.chdir(root)
    return root


def main() -> None:
    _bootstrap()
    from gui.main_window import MainWindow
    from gui.theme import apply_default_theme

    apply_default_theme()
    MainWindow().mainloop()


if __name__ == "__main__":
    main()
