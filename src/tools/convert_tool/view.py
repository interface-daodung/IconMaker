"""View tab PNG → ICO."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core.paths import OUTPUT_CONVERT
from gui.base_tool import ToolTab
from gui.widgets import FileRow
from service import convert
from tools.convert_tool.controller import ALL_SIZES_LABEL, parse_sizes, run_conversion


class Tab(ToolTab):
    title = "PNG → ICO"

    def build(self) -> None:
        self.row_src = FileRow(
            self,
            "Ảnh PNG:",
            filetypes=[("PNG images", "*.png"), ("All files", "*.*")],
            dialog_title="Chọn ảnh PNG",
        )
        self.row_src.pack(fill="x", padx=10, pady=4)
        self.row_out = FileRow(
            self, "Thư mục lưu:", mode="dir", dialog_title="Chọn thư mục lưu"
        )
        self.row_out.set(str(OUTPUT_CONVERT))
        self.row_out.pack(fill="x", padx=10, pady=4)

        size_frame = ctk.CTkFrame(self, fg_color="transparent")
        size_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(size_frame, text="Kích thước:", width=90, anchor="w").pack(
            side="left"
        )
        self.size_var = ctk.StringVar(value=ALL_SIZES_LABEL)
        choices = [str(s) for s in convert.get_default_sizes()] + [ALL_SIZES_LABEL]
        ctk.CTkOptionMenu(size_frame, variable=self.size_var, values=choices).pack(
            side="left", padx=6
        )
        ctk.CTkButton(size_frame, text="Convert", width=120, command=self._convert).pack(
            side="right"
        )

    def _convert(self) -> None:
        source = self.row_src.get()
        if not source:
            messagebox.showwarning("Thiếu file", "Hãy chọn ảnh PNG trước.")
            return
        if Path(source).suffix.lower() != ".png":
            messagebox.showerror("Sai định dạng", "File được chọn không phải PNG.")
            return
        try:
            sizes = parse_sizes(self.size_var.get())
        except ValueError:
            messagebox.showerror(
                "Lỗi", f"Kích thước không hợp lệ: {self.size_var.get()!r}"
            )
            return
        self.set_status("Đang chuyển...")
        try:
            dest = run_conversion(source, self.row_out.get() or None, sizes)
        except (ValueError, FileNotFoundError, OSError) as exc:
            self.fail("Lỗi chuyển đổi", exc)
            return
        self.done(f"Xong: {dest}")
        messagebox.showinfo("Hoàn tất", f"Đã tạo icon:\n{dest}")
