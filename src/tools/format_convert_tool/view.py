"""View tab đổi định dạng ảnh png/jpg/webp kèm nén + preview."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from core.formats import READABLE_IMAGE_EXTENSIONS
from core.paths import OUTPUT_CONVERT_FORMAT
from gui.base_tool import ToolTab
from gui.widgets import FileRow, ImagePreview
from tools.format_convert_tool.controller import (
    DEFAULT_QUALITY,
    options_for,
    parse_quality,
    preview_format,
    run_format_convert,
)

_LOSSLESS_FMT = ".png"


class Tab(ToolTab):
    title = "Đổi định dạng"

    def build(self) -> None:
        self._img: Image.Image | None = None
        self._radio_widgets: list[ctk.CTkRadioButton] = []

        self.row_src = FileRow(
            self,
            "Ảnh vào:",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")],
            dialog_title="Chọn ảnh cần đổi định dạng",
        )
        self.row_src.pack(fill="x", padx=10, pady=4)
        self.row_src.var.trace_add("write", lambda *_a: self._on_source_changed())

        self.fmt_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.fmt_frame.pack(fill="x", padx=10, pady=4)
        self.fmt_label = ctk.CTkLabel(
            self.fmt_frame, text="Đổi sang:", width=90, anchor="w"
        )
        self.fmt_label.pack(side="left")
        self.fmt_var = ctk.StringVar(value="")

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
            actions, text="Đổi & Lưu", width=110, command=self._save
        ).pack(side="right")

        self.hint = ctk.CTkLabel(
            self,
            text="Chọn ảnh vào để hiện định dạng đích.",
            anchor="w",
            wraplength=600,
        )
        self.hint.pack(fill="x", padx=10, pady=(4, 0))

        self.preview = ImagePreview(self)
        self.preview.pack(fill="both", expand=True, padx=10, pady=4)

    def _on_source_changed(self) -> None:
        source = self.row_src.get()
        if not source:
            self._close_img()
            self._rebuild_radios([])
            return
        try:
            ext = Path(source).suffix.lower()
            if ext not in READABLE_IMAGE_EXTENSIONS:
                raise ValueError("Không phải ảnh hỗ trợ (png/jpg/jpeg/webp)")
            img = Image.open(source)
        except (OSError, ValueError) as exc:
            self._close_img()
            self._rebuild_radios([])
            self.hint.configure(text=f"Lỗi đọc ảnh: {exc}")
            self.set_status("Sẵn sàng")
            return
        self._close_img()
        self._img = img
        options = options_for(source)
        self._rebuild_radios(options)
        self.hint.configure(text="")
        self._update_preview()

    def _rebuild_radios(self, options: list[str]) -> None:
        for widget in self._radio_widgets:
            widget.destroy()
        self._radio_widgets.clear()
        self.fmt_var.set("")
        if not options:
            return
        for ext in options:
            radio = ctk.CTkRadioButton(
                self.fmt_frame,
                text=ext,
                variable=self.fmt_var,
                value=ext,
                command=self._on_fmt_change,
            )
            radio.pack(side="left", padx=6)
            self._radio_widgets.append(radio)
        self.fmt_var.set(options[0])
        self._on_fmt_change()

    def _current_fmt(self) -> str | None:
        return self.fmt_var.get() or None

    def _current_quality(self) -> int:
        return max(1, min(100, int(round(self.q_slider.get()))))

    def _on_fmt_change(self) -> None:
        fmt = self._current_fmt()
        if fmt is None:
            self.q_slider.configure(state="disabled")
            return
        if fmt == _LOSSLESS_FMT:
            self.q_slider.configure(state="disabled")
            self.q_label.configure(text="PNG không nén (lossless)")
        else:
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
        if not fmt:
            return
        quality = self._current_quality() if fmt != _LOSSLESS_FMT else DEFAULT_QUALITY
        try:
            after = preview_format(self._img, fmt, quality)
        except (ValueError, OSError) as exc:
            self.set_status(f"Lỗi xem trước: {exc}", "red")
            return
        self.preview.set_before(self._img)
        self.preview.set_after(after)
        after.close()
        if fmt == _LOSSLESS_FMT:
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
        if not fmt:
            messagebox.showwarning("Thiếu định dạng", "Hãy chọn định dạng đích.")
            return
        try:
            quality = parse_quality(str(self._current_quality()))
        except ValueError as exc:
            self.fail("Lỗi chất lượng", exc)
            return
        self.set_status("Đang đổi định dạng...")
        try:
            dest = run_format_convert(
                source, out_dir=OUTPUT_CONVERT_FORMAT, fmt=fmt, quality=quality
            )
        except (ValueError, FileNotFoundError, OSError) as exc:
            self.fail("Lỗi đổi định dạng", exc)
            return
        self.done(f"Xong: {Path(dest).name}")
        self.hint.configure(text=f"Đã lưu: {dest}")
        messagebox.showinfo("Hoàn tất", f"Đã lưu:\n{dest}")