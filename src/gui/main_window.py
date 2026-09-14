"""Cửa sổ chính: tiêu đề + nút đổi theme + tab cho mỗi tool đã đăng ký."""

from __future__ import annotations

import customtkinter as ctk

from core.paths import app_icon_path
from gui import theme
from tools import registry


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("IconMaker")
        self.geometry("640x600")
        self.resizable(False, False)
        self._apply_app_icon()

        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        self._build_header()
        self._build_tabs()

    def _apply_app_icon(self) -> None:
        try:
            icon = app_icon_path()
            if icon.is_file():
                self.iconbitmap(str(icon))
        except Exception:
            pass

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(header, text="IconMaker", font=("Segoe UI", 20, "bold")).pack(
            side="left"
        )
        self.btn_theme = ctk.CTkButton(
            header, text="", width=130, command=self.toggle_theme
        )
        self.btn_theme.pack(side="right")
        self.refresh_theme_button()

    def _build_tabs(self) -> None:
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=12, pady=6)
        for tool in registry.get_tools():
            tabs.add(tool.title)
            tool.tab_class(tabs.tab(tool.title)).pack(fill="both", expand=True)

    def toggle_theme(self) -> None:
        mode = theme.next_theme(ctk.get_appearance_mode())
        ctk.set_appearance_mode(mode)
        self.theme_var.set(mode)
        self.refresh_theme_button()

    def refresh_theme_button(self) -> None:
        if self.theme_var.get() == theme.THEME_DARK:
            self.btn_theme.configure(text="Đổi sang Sáng")
        else:
            self.btn_theme.configure(text="Đổi sang Tối")
