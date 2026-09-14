"""Entry point: mở GUI IconMaker (chạy bằng pythonw để không hiện console)."""

from __future__ import annotations

from gui.main_window import MainWindow
from gui.theme import apply_default_theme


def main() -> None:
    apply_default_theme()
    MainWindow().mainloop()


if __name__ == "__main__":
    main()
