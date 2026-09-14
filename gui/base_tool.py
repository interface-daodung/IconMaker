"""Lớp nền cho mọi tab tool: khung trong suốt + dòng trạng thái chung."""

from __future__ import annotations

from abc import ABC, abstractmethod
from tkinter import messagebox

import customtkinter as ctk


class ToolTab(ctk.CTkFrame, ABC):
    """Base class mọi tool. Subclass chỉ cần đặt `title` và viết `build()`."""

    title = "Tool"

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color="transparent")
        self.status = ctk.CTkLabel(self, text="Sẵn sàng", anchor="w")
        self.build()
        self.status.pack(fill="x", padx=10, pady=(4, 8))

    @abstractmethod
    def build(self) -> None:
        """Dựng widget của tab (status đã tạo sẵn, pack cuối)."""

    def set_status(self, text: str, color: str = "gray") -> None:
        self.status.configure(text=text, text_color=color)

    def done(self, text: str) -> None:
        self.set_status(text, "green")

    def fail(self, title: str, exc: Exception) -> None:
        self.set_status("Thất bại", "red")
        messagebox.showerror(title, str(exc))
