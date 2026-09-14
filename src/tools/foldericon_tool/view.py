"""View tab đặt icon thư mục."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core.file_utils import newest_file
from gui.base_tool import ToolTab
from gui.widgets import FileRow
from tools.foldericon_tool.controller import (
    icons_default_dir,
    parse_new_name,
    run_apply,
)


class Tab(ToolTab):
    title = "Icon thư mục"

    def build(self) -> None:
        icons_dir = icons_default_dir()
        self.row_icon = FileRow(
            self,
            "File ICO:",
            filetypes=[("ICO icons", "*.ico"), ("All files", "*.*")],
            dialog_title="Chọn file ICO trong output/icons",
            initialdir=icons_dir,
        )
        latest = newest_file(icons_dir, ".ico")
        self.row_icon.set(str(latest) if latest else icons_dir)
        self.row_icon.pack(fill="x", padx=10, pady=4)
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(name_frame, text="Tên mới:", width=90, anchor="w").pack(
            side="left"
        )
        self.name_var = ctk.StringVar()
        self._last_stem = ""
        if latest is not None:
            self._last_stem = latest.stem
            self.name_var.set(latest.stem)
        self.row_icon.var.trace_add("write", lambda *_: self._sync_name_from_icon())
        ctk.CTkEntry(
            name_frame,
            textvariable=self.name_var,
            placeholder_text="mặc định = tên gốc, sửa nhanh nếu cần",
        ).pack(side="left", fill="x", expand=True, padx=6)
        self.row_folder = FileRow(
            self,
            "Thư mục:",
            mode="dir",
            dialog_title="Chọn thư mục cần đổi icon",
        )
        self.row_folder.pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(self, text="Đặt icon cho thư mục", command=self._run).pack(
            padx=10, pady=6, anchor="e"
        )

    def _sync_name_from_icon(self) -> None:
        icon = Path(self.row_icon.get())
        if icon.suffix.lower() != ".ico":
            return
        if self.name_var.get().strip() in ("", self._last_stem):
            self.name_var.set(icon.stem)
        self._last_stem = icon.stem

    def _run(self) -> None:
        icon = self.row_icon.get()
        folder = self.row_folder.get()
        if not icon or not folder:
            messagebox.showwarning(
                "Thiếu thông tin", "Hãy chọn cả file ICO và thư mục."
            )
            return
        if Path(icon).is_dir():
            messagebox.showerror(
                "Chưa chọn file", "Hãy mở output/icons và chọn 1 file .ico cụ thể."
            )
            return
        if Path(icon).suffix.lower() != ".ico":
            messagebox.showerror("Sai định dạng", "File icon phải là .ico.")
            return
        try:
            new_name = parse_new_name(self.name_var.get())
        except ValueError as exc:
            messagebox.showerror("Tên mới không hợp lệ", str(exc))
            return
        self.set_status("Đang đặt icon...")
        try:
            ini = run_apply(icon, folder, new_name)
        except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
            self.fail("Lỗi đặt icon", exc)
            return
        self.done(f"Đã đặt icon: {ini}")
        messagebox.showinfo(
            "Hoàn tất",
            f"Đã đặt icon cho:\n{folder}\n\n(chấp nhận nếu Explorer chưa cập nhật ngay)",
        )
