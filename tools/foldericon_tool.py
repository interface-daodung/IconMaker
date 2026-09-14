"""Tool đặt icon cho thư mục Windows. View là Tab, logic gọi core.foldericon."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core import foldericon
from gui.base_tool import ToolTab
from gui.widgets import FileRow


def run_apply(icon_path: str | Path, folder_path: str | Path) -> str:
    """Copy icon vào thư viện ổn định rồi đặt cho thư mục; trả về desktop.ini."""
    installed = foldericon.install_icon(icon_path)
    return foldericon.set_folder_icon(folder_path, installed)


class Tab(ToolTab):
    title = "Icon thư mục"

    def build(self) -> None:
        self.row_icon = FileRow(
            self,
            "File ICO:",
            filetypes=[("ICO icons", "*.ico"), ("All files", "*.*")],
            dialog_title="Chọn file ICO",
        )
        self.row_icon.pack(fill="x", padx=10, pady=4)
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

    def _run(self) -> None:
        icon = self.row_icon.get()
        folder = self.row_folder.get()
        if not icon or not folder:
            messagebox.showwarning(
                "Thiếu thông tin", "Hãy chọn cả file ICO và thư mục."
            )
            return
        if Path(icon).suffix.lower() != ".ico":
            messagebox.showerror("Sai định dạng", "File icon phải là .ico.")
            return
        self.set_status("Đang đặt icon...")
        try:
            ini = run_apply(icon, folder)
        except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
            self.fail("Lỗi đặt icon", exc)
            return
        self.done(f"Đã đặt icon: {ini}")
        messagebox.showinfo(
            "Hoàn tất",
            f"Đã đặt icon cho:\n{folder}\n\n(chấp nhận nếu Explorer chưa cập nhật ngay)",
        )
