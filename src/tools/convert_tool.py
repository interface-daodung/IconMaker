"""Tool chuyển PNG → ICO. View là Tab, logic gọi core.convert."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core import convert
from core.file_utils import resolve_output_path
from gui.base_tool import ToolTab
from gui.widgets import FileRow

ALL_SIZES_LABEL = "Tất cả"


def parse_sizes(selection: str) -> list[int]:
    """Chuyển lựa chọn combo thành list kích thước hợp lệ cho converter."""
    if selection == ALL_SIZES_LABEL:
        return convert.get_default_sizes()
    return [int(selection)]


def run_conversion(
    source: str | Path,
    out_dir: str | Path | None = None,
    sizes: list[int] | None = None,
) -> str:
    """Chuyển PNG thành ICO, trả về đường dẫn file .ico."""
    dest = resolve_output_path(source, out_dir, ".ico")
    return convert.convert_png_to_ico(source, dest, sizes)


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
