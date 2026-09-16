"""View tab build launcher tray (.exe) cho 1 thư mục server."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core.file_utils import newest_file
from gui.base_tool import ToolTab
from gui.widgets import FileRow
from tools.launcher_tool.controller import (
    default_server_root,
    icons_default_dir,
    run_build,
    suggest_name,
)


class Tab(ToolTab):
    title = "Build Launcher"

    def build(self) -> None:
        self.row_server = FileRow(
            self,
            "Thư mục:",
            mode="dir",
            dialog_title="Chọn thư mục server (chứa app chạy make run)",
            initialdir=default_server_root(),
        )
        self.row_server.pack(fill="x", padx=10, pady=4)
        icons_dir = icons_default_dir()
        self.row_icon = FileRow(
            self,
            "File ICO:",
            filetypes=[("ICO icons", "*.ico"), ("All files", "*.*")],
            dialog_title="Chọn icon cho launcher (sẽ copy lên thư viện Icon)",
            initialdir=icons_dir,
        )
        latest = newest_file(icons_dir, ".ico")
        self.row_icon.set(str(latest) if latest else icons_dir)
        self.row_icon.pack(fill="x", padx=10, pady=4)
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(name_frame, text="Tên launcher:", width=90, anchor="w").pack(
            side="left"
        )
        self.name_var = ctk.StringVar()
        self._last_suggest = ""
        ctk.CTkEntry(
            name_frame,
            textvariable=self.name_var,
            placeholder_text="vd MyServer (bỏ trống = lấy tên thư mục)",
        ).pack(side="left", fill="x", expand=True, padx=6)
        self.row_server.var.trace_add("write", lambda *_: self._sync_name())
        ctk.CTkLabel(
            self,
            text="Icon được copy vào thư viện Icon rồi mới build; file .exe ra output/launchers/.",
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 2))
        self.build_btn = ctk.CTkButton(
            self, text="Build Launcher", command=self._run
        )
        self.build_btn.pack(padx=10, pady=6, anchor="e")
        self.log_box = ctk.CTkTextbox(self, height=150, state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 4))

    def _sync_name(self) -> None:
        suggest = suggest_name(self.row_server.get())
        if self.name_var.get().strip() in ("", self._last_suggest):
            self.name_var.set(suggest)
        self._last_suggest = suggest

    def _run(self) -> None:
        server = self.row_server.get()
        icon = self.row_icon.get()
        name = self.name_var.get().strip() or suggest_name(server)
        if not server:
            messagebox.showwarning(
                "Thiếu thông tin", "Hãy chọn thư mục server cần build launcher."
            )
            return
        if not icon or Path(icon).is_dir():
            messagebox.showwarning(
                "Thiếu thông tin", "Hãy chọn 1 file .ico làm icon launcher."
            )
            return
        if Path(icon).suffix.lower() != ".ico":
            messagebox.showerror("Sai định dạng", "File icon phải là .ico.")
            return
        if not name:
            messagebox.showwarning(
                "Thiếu thông tin", "Hãy nhập tên launcher (vd MyServer)."
            )
            return
        self.build_btn.configure(state="disabled")
        self.set_status("Đang build launcher (mất vài phút)...")
        self._clear_log()
        threading.Thread(
            target=self._worker, args=(server, icon, name), daemon=True
        ).start()

    def _clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _append_log(self, line: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", line + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _worker(self, server: str, icon: str, name: str) -> None:
        try:
            exe = run_build(
                server, icon, name, on_output=lambda line: self.after(0, self._append_log, line)
            )
        except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
            self.after(0, lambda: self._failed(str(exc)))
        else:
            self.after(0, lambda: self._succeeded(exe))

    def _failed(self, detail: str) -> None:
        self.build_btn.configure(state="normal")
        self.set_status("Thất bại", "red")
        messagebox.showerror("Build launcher thất bại", detail)

    def _succeeded(self, exe: str) -> None:
        self.build_btn.configure(state="normal")
        self.done(f"Đã build: {exe}")
        messagebox.showinfo("Hoàn tất", f"Launcher đã build:\n{exe}")
