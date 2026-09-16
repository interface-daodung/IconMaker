"""View tab Xuất ảnh: 1 ảnh vào → radio jpg/png/webp/ico → lưu vào output/export/."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from core.formats import READABLE_IMAGE_EXTENSIONS
from core.paths import OUTPUT_EXPORT
from gui.base_tool import ToolTab
from gui.widgets import FileRow, ImagePreview
from service import convert
from tools.export_tool.controller import (
    ALL_SIZES_LABEL,
    DEFAULT_FMT,
    DEFAULT_QUALITY,
    EXPORT_FORMATS,
    parse_quality,
    parse_sizes,
    preview_export,
    run_export,
)

_LOSSLESS_NO_SLIDER = (".png", ".ico")


class Tab(ToolTab):
    title = "Xuất ảnh"

    def build(self) -> None:
        self._img: Image.Image | None = None

        self.row_src = FileRow(
            self,
            "Ảnh vào:",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")],
            dialog_title="Chọn ảnh cần xuất",
        )
        self.row_src.pack(fill="x", padx=10, pady=4)
        self.row_src.var.trace_add("write", lambda *_a: self._on_source_changed())

        self.fmt_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.fmt_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(self.fmt_frame, text="Xuất ra:", width=90, anchor="w").pack(
            side="left"
        )
        self.fmt_var = ctk.StringVar(value=DEFAULT_FMT)
        for ext in EXPORT_FORMATS:
            ctk.CTkRadioButton(
                self.fmt_frame,
                text=ext,
                variable=self.fmt_var,
                value=ext,
                command=self._on_fmt_change,
            ).pack(side="left", padx=6)

        opt_frame = ctk.CTkFrame(self, fg_color="transparent")
        opt_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(opt_frame, text="Kích thước:", width=90, anchor="w").pack(
            side="left"
        )
        self.size_var = ctk.StringVar(value=ALL_SIZES_LABEL)
        choices = [str(s) for s in convert.get_default_sizes()] + [ALL_SIZES_LABEL]
        self.size_menu = ctk.CTkOptionMenu(opt_frame, variable=self.size_var, values=choices)
        self.size_menu.pack(side="left", padx=6)

        self.q_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.q_frame.pack(fill="x", padx=10, pady=4)
        self.q_label = ctk.CTkLabel(
            self.q_frame,
            text=f"Chất lượng: {DEFAULT_QUALITY}%",
            width=90,
            anchor="w",
        )
        self.q_label.pack(side="left")
        self.q_slider = ctk.CTkSlider(
            self.q_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            command=self._on_slider,
        )
        self.q_slider.set(DEFAULT_QUALITY)
        self.q_slider.pack(side="left", fill="x", expand=True, padx=6)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(
            actions, text="Xem trước", width=110, command=self._update_preview
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            actions, text="Xuất & Lưu", width=110, command=self._save
        ).pack(side="right")

        self.hint = ctk.CTkLabel(
            self,
            text=f"Xuất 1 định dạng mỗi lần, lưu vào {OUTPUT_EXPORT}/.",
            anchor="w",
            wraplength=600,
        )
        self.hint.pack(fill="x", padx=10, pady=(4, 0))

        self.preview = ImagePreview(self)
        self.preview.pack(fill="both", expand=True, padx=10, pady=4)
        self._on_fmt_change()

    def _current_fmt(self) -> str:
        return self.fmt_var.get() or DEFAULT_FMT

    def _current_quality(self) -> int:
        return max(1, min(100, int(round(self.q_slider.get()))))

    def _on_source_changed(self) -> None:
        source = self.row_src.get()
        if not source:
            self._close_img()
            return
        try:
            ext = Path(source).suffix.lower()
            if ext not in READABLE_IMAGE_EXTENSIONS:
                raise ValueError("Không phải ảnh hỗ trợ (png/jpg/jpeg/webp)")
            img = Image.open(source)
        except (OSError, ValueError) as exc:
            self._close_img()
            self.hint.configure(text=f"Lỗi đọc ảnh: {exc}")
            self.set_status("Sẵn sàng")
            return
        self._close_img()
        self._img = img
        self.hint.configure(text="")
        self._update_preview()

    def _on_fmt_change(self) -> None:
        fmt = self._current_fmt()
        if fmt == ".ico":
            self.size_menu.configure(state="normal")
            self.q_slider.configure(state="disabled")
            self.q_label.configure(text="ICO đa size (không nén)")
        elif fmt == ".png":
            self.size_menu.configure(state="disabled")
            self.q_slider.configure(state="disabled")
            self.q_label.configure(text="PNG không nén (lossless)")
        else:
            self.size_menu.configure(state="disabled")
            self.q_slider.configure(state="normal")
            self._sync_quality_label()
        self._update_preview()

    def _sync_quality_label(self) -> None:
        self.q_label.configure(text=f"Chất lượng: {self._current_quality()}%")

    def _on_slider(self, _value: float) -> None:
        self._sync_quality_label()
        self._update_preview()

    def _update_preview(self) -> None:
        if self._img is None:
            return
        fmt = self._current_fmt()
        if fmt == ".ico":
            self.preview.set_before(self._img)
            self.preview.set_after(self._img)
            self.set_status("ICO giữ nguyên ảnh gốc, resize khi lưu")
            return
        quality = self._current_quality() if fmt not in _LOSSLESS_NO_SLIDER else DEFAULT_QUALITY
        try:
            after = preview_export(self._img, fmt, quality)
        except (ValueError, OSError) as exc:
            self.set_status(f"Lỗi xem trước: {exc}", "red")
            return
        self.preview.set_before(self._img)
        self.preview.set_after(after)
        after.close()
        if fmt == ".png":
            self.set_status("Xem trước PNG (lossless, không mất chi tiết)")
        else:
            self.set_status(f"Xem trước {fmt} ở chất lượng {quality}%")

    def _close_img(self) -> None:
        if self._img is not None:
            self._img.close()
            self._img = None

    def _save(self) -> None:
        source = self.row_src.get()
        if not source:
            messagebox.showwarning("Thiếu file", "Hãy chọn ảnh trước.")
            return
        fmt = self._current_fmt()
        try:
            quality = parse_quality(str(self._current_quality()))
            sizes = parse_sizes(self.size_var.get()) if fmt == ".ico" else None
        except ValueError as exc:
            self.fail("Lỗi tham số", exc)
            return
        self.set_status("Đang xuất...")
        try:
            dest = run_export(
                source, out_dir=OUTPUT_EXPORT, fmt=fmt, quality=quality, sizes=sizes
            )
        except (ValueError, FileNotFoundError, OSError) as exc:
            self.fail("Lỗi xuất ảnh", exc)
            return
        self.done(f"Xong: {Path(dest).name}")
        self.hint.configure(text=f"Đã lưu: {dest}")
        messagebox.showinfo("Hoàn tất", f"Đã lưu:\n{dest}")
