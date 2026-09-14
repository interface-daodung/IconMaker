"""View tab bo góc ảnh."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from core.formats import READABLE_IMAGE_EXTENSIONS
from core.paths import OUTPUT_ROUNDED
from gui.base_tool import ToolTab
from gui.widgets import FileRow, ImagePreview
from service import image_ops
from tools.rounded_tool.controller import DEFAULT_RADIUS, parse_radius, run_round


class Tab(ToolTab):
    title = "Bo góc"

    def build(self) -> None:
        self.row_src = FileRow(
            self,
            "Ảnh vào:",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")],
            dialog_title="Chọn ảnh cần bo góc",
        )
        self.row_src.pack(fill="x", padx=10, pady=4)

        opt = ctk.CTkFrame(self, fg_color="transparent")
        opt.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(opt, text="Bán kính:", width=90, anchor="w").pack(side="left")
        self.radius_var = ctk.StringVar(value=str(DEFAULT_RADIUS))
        ctk.CTkEntry(opt, textvariable=self.radius_var, width=80).pack(
            side="left", padx=6
        )
        ctk.CTkButton(opt, text="Xem trước", width=110, command=self._preview).pack(
            side="left", padx=6
        )
        ctk.CTkButton(opt, text="Lưu PNG", width=110, command=self._save).pack(
            side="right"
        )

        self.preview = ImagePreview(self)
        self.preview.pack(fill="both", expand=True, padx=10, pady=4)

    def _load_source(self) -> Image.Image | None:
        source = self.row_src.get()
        if not source:
            messagebox.showwarning("Thiếu file", "Hãy chọn ảnh trước.")
            return None
        if Path(source).suffix.lower() not in READABLE_IMAGE_EXTENSIONS:
            messagebox.showerror("Sai định dạng", "File được chọn không phải ảnh hỗ trợ.")
            return None
        try:
            return Image.open(source).convert("RGBA")
        except OSError as exc:
            messagebox.showerror("Lỗi đọc ảnh", str(exc))
            return None

    def _read_radius(self, img: Image.Image) -> int | None:
        try:
            return parse_radius(self.radius_var.get(), *img.size)
        except ValueError:
            messagebox.showerror(
                "Lỗi", f"Bán kính phải là số nguyên >= 0: {self.radius_var.get()!r}"
            )
            return None

    def _preview(self) -> None:
        img = self._load_source()
        if img is None:
            return
        radius = self._read_radius(img)
        if radius is None:
            img.close()
            return
        out = image_ops.rounded_corners(img, radius)
        self.preview.set_before(img)
        self.preview.set_after(out)
        self.set_status(f"Xem trước với bán kính {radius}px")
        img.close()
        out.close()

    def _save(self) -> None:
        source = self.row_src.get()
        if not source:
            messagebox.showwarning("Thiếu file", "Hãy chọn ảnh trước.")
            return
        try:
            radius = int(self.radius_var.get())
        except ValueError:
            messagebox.showerror(
                "Lỗi", f"Bán kính phải là số nguyên >= 0: {self.radius_var.get()!r}"
            )
            return
        self.set_status("Đang bo góc...")
        try:
            dest = run_round(source, radius=radius, out_dir=OUTPUT_ROUNDED)
        except (ValueError, FileNotFoundError, OSError) as exc:
            self.fail("Lỗi bo góc", exc)
            return
        self.done(f"Xong: {dest}")
        messagebox.showinfo("Hoàn tất", f"Đã lưu ảnh bo góc:\n{dest}")
