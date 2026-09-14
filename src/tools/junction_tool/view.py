"""View tab tạo Junction Point."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from gui.base_tool import ToolTab
from gui.widgets import FileRow
from tools.junction_tool.controller import join_link_path, parse_inputs, run_create


class Tab(ToolTab):
    title = "Junction"

    def build(self) -> None:
        self.row_parent = FileRow(
            self,
            "OneDrive:",
            mode="dir",
            dialog_title="Chọn thư mục cha sẽ CHỨA đường dẫn ảo (vd một thư mục trong OneDrive)",
        )
        self.row_parent.pack(fill="x", padx=10, pady=4)
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(name_frame, text="Tên ảo:", width=90, anchor="w").pack(
            side="left"
        )
        self.name_var = ctk.StringVar()
        ctk.CTkEntry(
            name_frame,
            textvariable=self.name_var,
            placeholder_text="tên junction mới (chưa tồn tại) — hoặc paste thẳng đường dẫn đủ vào ô trên",
        ).pack(side="left", fill="x", expand=True, padx=6)
        self.row_target = FileRow(
            self,
            "Ổ thật:",
            mode="dir",
            dialog_title="Chọn thư mục THẬT ở ổ mới (nguồn dữ liệu)",
        )
        self.row_target.pack(fill="x", padx=10, pady=4)
        self.readonly_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self,
            text="attrib +r <ảo> /l (cần để Explorer hiển thị icon tuỳ chỉnh)",
            variable=self.readonly_var,
        ).pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkButton(self, text="Tạo Junction", command=self._run).pack(
            padx=10, pady=6, anchor="e"
        )

    def _run(self) -> None:
        try:
            link = join_link_path(self.row_parent.get(), self.name_var.get())
            link, target = parse_inputs(link, self.row_target.get())
        except ValueError as exc:
            messagebox.showwarning("Thiếu thông tin", str(exc))
            return
        if Path(link).exists():
            messagebox.showerror(
                "Đã tồn tại",
                f"Đường dẫn ảo đã có sẵn:\n{link}\n\nXoá hoặc đổi tên trước khi tạo.",
            )
            return
        self.set_status("Đang tạo junction...")
        try:
            created = run_create(link, target, self.readonly_var.get())
        except (
            ValueError,
            FileExistsError,
            FileNotFoundError,
            RuntimeError,
            OSError,
        ) as exc:
            self.fail("Lỗi tạo junction", exc)
            return
        self.done(f"Đã tạo: {created}")
        messagebox.showinfo(
            "Hoàn tất",
            f"Junction đã tạo:\n{created}\n\n→ trỏ về\n{target}",
        )
