"""View tab tách sprite."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from core.paths import INPUT_DIR, OUTPUT_SPRITES
from gui.base_tool import ToolTab
from gui.widgets import FileRow
from tools.sprites_tool.controller import run_split


class Tab(ToolTab):
    title = "Tách sprite"

    def build(self) -> None:
        self.row_in = FileRow(
            self, "Thư mục vào:", mode="dir", dialog_title="Chọn thư mục chứa ảnh nền đen"
        )
        self.row_in.set(str(INPUT_DIR))
        self.row_in.pack(fill="x", padx=10, pady=4)
        self.row_out = FileRow(
            self, "Thư mục ra:", mode="dir", dialog_title="Chọn thư mục chứa sprite"
        )
        self.row_out.set(str(OUTPUT_SPRITES))
        self.row_out.pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(self, text="Tách sprite", command=self._run).pack(
            padx=10, pady=6, anchor="e"
        )

    def _run(self) -> None:
        if not self.row_in.get() or not self.row_out.get():
            messagebox.showwarning(
                "Thiếu thông tin", "Hãy chọn cả thư mục vào và thư mục ra."
            )
            return
        self.set_status("Đang tách sprite (có thể lâu nếu chạy OCR)...")
        self.update_idletasks()
        try:
            written = run_split(self.row_in.get(), self.row_out.get())
        except (ValueError, FileNotFoundError, OSError) as exc:
            self.fail("Lỗi tách sprite", exc)
            return
        self.done(f"Xong: {len(written)} sprite → {self.row_out.get()}")
        messagebox.showinfo(
            "Hoàn tất", f"Đã tách {len(written)} sprite vào:\n{self.row_out.get()}"
        )
