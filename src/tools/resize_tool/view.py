"""View tab resize ảnh vuông thành nhiều cỡ icon."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from core.formats import READABLE_IMAGE_EXTENSIONS
from core.paths import OUTPUT_RESIZE
from gui.base_tool import ToolTab
from gui.widgets import FileRow
from service.resize import RESIZE_NAMES, RESIZE_SIZES
from tools.resize_tool.controller import DEFAULT_FORMAT, run_resize


class Tab(ToolTab):
    title = "Resize icon"

    def build(self) -> None:
        self.row_src = FileRow(
            self,
            "Ảnh vào:",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")],
            dialog_title="Chọn ảnh cần resize",
        )
        self.row_src.pack(fill="x", padx=10, pady=4)

        opt = ctk.CTkFrame(self, fg_color="transparent")
        opt.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(opt, text="Đuôi output:", width=90, anchor="w").pack(
            side="left"
        )
        self.ext_var = ctk.StringVar(value=DEFAULT_FORMAT)
        ctk.CTkEntry(opt, textvariable=self.ext_var, width=80).pack(
            side="left", padx=6
        )
        ctk.CTkButton(opt, text="Resize & Lưu", width=110, command=self._save).pack(
            side="right"
        )

        info = ctk.CTkLabel(
            self,
            text="Tạo 3 ảnh vuông: icon16 (16x16), icon48 (48x48), icon128 (128x128)",
            anchor="w",
        )
        info.pack(fill="x", padx=10, pady=(8, 4))

        self.result_label = ctk.CTkLabel(self, text="", anchor="w", wraplength=600)
        self.result_label.pack(fill="x", padx=10, pady=4)

    def _save(self) -> None:
        source = self.row_src.get()
        if not source:
            messagebox.showwarning("Thiếu file", "Hãy chọn ảnh trước.")
            return
        ext = self.ext_var.get().strip() or DEFAULT_FORMAT
        self.set_status("Đang resize...")
        try:
            results = run_resize(source, out_dir=OUTPUT_RESIZE, ext=ext)
        except (ValueError, FileNotFoundError, OSError) as exc:
            self.fail("Lỗi resize", exc)
            return
        names = ", ".join(Path(p).name for p in results)
        self.done(f"Xong: {len(results)} file")
        self.result_label.configure(text=f"Đã lưu: {names}")
        messagebox.showinfo("Hoàn tất", f"Đã lưu {len(results)} file:\n{names}")
