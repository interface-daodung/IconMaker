"""Tool build ICO chất lượng cao từ sprite. View là Tab, logic gọi core.icons."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core import icons
from core.paths import OUTPUT_ICONS, OUTPUT_SPRITES
from gui.base_tool import ToolTab
from gui.widgets import FileRow


def run_build(sprites_dir: str | Path, icon_dir: str | Path) -> list[str]:
    """Mọi PNG trong `sprites_dir` → ICO trong `icon_dir`, trả về danh sách đã ghi."""
    if not Path(sprites_dir).is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục sprite: {sprites_dir}")
    written = icons.build_from_sprites(sprites_dir, icon_dir)
    if not written:
        raise ValueError(f"Không có sprite PNG nào trong {sprites_dir}")
    return [str(p) for p in written]


class Tab(ToolTab):
    title = "Sprite → ICO"

    def build(self) -> None:
        self.row_in = FileRow(
            self, "Thư mục sprite:", mode="dir", dialog_title="Chọn thư mục sprite"
        )
        self.row_in.set(str(OUTPUT_SPRITES))
        self.row_in.pack(fill="x", padx=10, pady=4)
        self.row_out = FileRow(
            self, "Thư mục ICO:", mode="dir", dialog_title="Chọn thư mục chứa ICO"
        )
        self.row_out.set(str(OUTPUT_ICONS))
        self.row_out.pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(self, text="Build ICO", command=self._run).pack(
            padx=10, pady=6, anchor="e"
        )

    def _run(self) -> None:
        if not self.row_in.get() or not self.row_out.get():
            messagebox.showwarning(
                "Thiếu thông tin", "Hãy chọn cả thư mục sprite và thư mục ICO."
            )
            return
        self.set_status("Đang build ICO...")
        self.update_idletasks()
        try:
            written = run_build(self.row_in.get(), self.row_out.get())
        except (ValueError, FileNotFoundError, OSError) as exc:
            self.fail("Lỗi build ICO", exc)
            return
        self.done(f"Xong: {len(written)} icon → {self.row_out.get()}")
        messagebox.showinfo(
            "Hoàn tất", f"Đã tạo {len(written)} icon vào:\n{self.row_out.get()}"
        )
