"""Widget tái sử dụng cho các tab tool: chọn file/thư mục, xem trước ảnh."""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk
from PIL import Image


class FileRow(ctk.CTkFrame):
    """Một hàng: nhãn + ô đường dẫn + nút Chọn (file hoặc thư mục)."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        label: str,
        mode: str = "file",
        filetypes: list[tuple[str, str]] | None = None,
        dialog_title: str = "Chọn",
        initialdir: str | None = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._mode = mode
        self._filetypes = filetypes or [("All files", "*.*")]
        self._dialog_title = dialog_title
        self._initialdir = initialdir
        self.var = ctk.StringVar()

        ctk.CTkLabel(self, text=label, width=90, anchor="w").pack(side="left")
        ctk.CTkEntry(self, textvariable=self.var).pack(
            side="left", fill="x", expand=True, padx=6
        )
        ctk.CTkButton(self, text="Chọn...", width=80, command=self._browse).pack(
            side="left"
        )

    def _browse(self) -> None:
        if self._mode == "dir":
            path = filedialog.askdirectory(
                title=self._dialog_title, initialdir=self._initialdir
            )
        else:
            path = filedialog.askopenfilename(
                title=self._dialog_title,
                filetypes=self._filetypes,
                initialdir=self._initialdir,
            )
        if path:
            self.var.set(path)

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str) -> None:
        self.var.set(value)


class ImagePreview(ctk.CTkFrame):
    """Hai khung xem trước Trước/Sau cho tool xử lý ảnh."""

    def __init__(self, master: ctk.CTkBaseClass, max_size: int = 200) -> None:
        super().__init__(master, fg_color="transparent")
        self._max_size = max_size
        self._images: list = []
        self._before = ctk.CTkLabel(self, text="Trước\n(chưa có ảnh)")
        self._before.pack(side="left", expand=True)
        self._after = ctk.CTkLabel(self, text="Sau\n(chưa có ảnh)")
        self._after.pack(side="left", expand=True)

    def _fit(self, img: Image.Image) -> Image.Image:
        thumb = img.copy()
        thumb.thumbnail((self._max_size, self._max_size))
        return thumb

    def _show(self, slot: ctk.CTkLabel, img: Image.Image) -> None:
        thumb = self._fit(img.convert("RGBA"))
        photo = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=thumb.size)
        self._images.append(photo)
        slot.configure(image=photo, text="")

    def set_before(self, img: Image.Image) -> None:
        self._show(self._before, img)

    def set_after(self, img: Image.Image) -> None:
        self._show(self._after, img)
