"""View tab đặt icon thư mục (1 thư mục hoặc hàng loạt `*<tên>`)."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core.file_utils import newest_file
from gui.base_tool import ToolTab
from gui.widgets import FileRow
from tools.foldericon_tool.controller import (
    default_search_root,
    extra_drives,
    icons_default_dir,
    is_batch_input,
    parse_batch_name,
    parse_new_name,
    run_apply,
    run_apply_many,
    run_search,
)


class Tab(ToolTab):
    title = "Icon thư mục"

    def build(self) -> None:
        icons_dir = icons_default_dir()
        self.row_icon = FileRow(
            self,
            "File ICO:",
            filetypes=[("ICO icons", "*.ico"), ("All files", "*.*")],
            dialog_title="Chọn file ICO trong output/icons",
            initialdir=icons_dir,
        )
        latest = newest_file(icons_dir, ".ico")
        self.row_icon.set(str(latest) if latest else icons_dir)
        self.row_icon.pack(fill="x", padx=10, pady=4)
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(name_frame, text="Tên mới:", width=90, anchor="w").pack(
            side="left"
        )
        self.name_var = ctk.StringVar()
        self._last_stem = ""
        if latest is not None:
            self._last_stem = latest.stem
            self.name_var.set(latest.stem)
        self.row_icon.var.trace_add("write", lambda *_: self._sync_name_from_icon())
        ctk.CTkEntry(
            name_frame,
            textvariable=self.name_var,
            placeholder_text="mặc định = tên gốc, sửa nhanh nếu cần",
        ).pack(side="left", fill="x", expand=True, padx=6)
        self.row_folder = FileRow(
            self,
            "Thư mục:",
            mode="dir",
            dialog_title="Chọn thư mục cần đổi icon",
        )
        self.row_folder.pack(fill="x", padx=10, pady=4)
        hint = ctk.CTkLabel(
            self,
            text="Gõ *<tên> (vd *MyApp) để tìm mọi thư mục trùng tên rồi đặt hàng loạt.",
            anchor="w",
        )
        hint.pack(fill="x", padx=10, pady=(0, 2))
        self._build_batch_frame()
        self.row_folder.var.trace_add("write", lambda *_: self._on_folder_input())
        self._on_folder_input()
        ctk.CTkButton(self, text="Đặt icon cho thư mục", command=self._run).pack(
            padx=10, pady=6, anchor="e"
        )

    def _build_batch_frame(self) -> None:
        self.batch_frame = ctk.CTkFrame(self)
        top = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=(6, 2))
        self.batch_info = ctk.CTkLabel(top, text="", anchor="w")
        self.batch_info.pack(side="left", fill="x", expand=True)
        self.search_btn = ctk.CTkButton(
            top, text="Tìm", width=90, command=self._search
        )
        self.search_btn.pack(side="left", padx=(6, 0))
        self.drives_frame = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        self.drives_frame.pack(fill="x", padx=8, pady=2)
        ctk.CTkLabel(
            self.drives_frame, text="Quét thêm ổ đĩa:", anchor="w"
        ).pack(side="left", padx=(0, 6))
        self._drive_vars: dict[str, ctk.BooleanVar] = {}
        try:
            drives = extra_drives()
        except OSError:
            drives = []
        if not drives:
            ctk.CTkLabel(
                self.drives_frame, text="(không có ổ đĩa khác)", anchor="w"
            ).pack(side="left")
        for drive in drives:
            var = ctk.BooleanVar(value=False)
            self._drive_vars[drive] = var
            ctk.CTkCheckBox(self.drives_frame, text=drive, variable=var).pack(
                side="left", padx=4
            )
        sel_row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        sel_row.pack(fill="x", padx=8, pady=2)
        self.result_count = ctk.CTkLabel(sel_row, text="Chưa tìm.", anchor="w")
        self.result_count.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            sel_row, text="Chọn hết", width=80, command=lambda: self._toggle_all(True)
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            sel_row, text="Bỏ hết", width=70, command=lambda: self._toggle_all(False)
        ).pack(side="left", padx=2)
        self.results_box = ctk.CTkScrollableFrame(self.batch_frame, height=140)
        self.results_box.pack(fill="both", expand=True, padx=8, pady=(2, 8))
        self._result_vars: list[tuple[str, ctk.BooleanVar]] = []

    def _on_folder_input(self) -> None:
        batch = is_batch_input(self.row_folder.get())
        if batch:
            try:
                name = parse_batch_name(self.row_folder.get())
            except ValueError:
                name = self.row_folder.get().strip()
            self.batch_info.configure(
                text=f"Tìm mọi thư mục tên '{name}' trong {default_search_root()}"
            )
            if not self.batch_frame.winfo_ismapped():
                self.batch_frame.pack(fill="both", expand=True, padx=10, pady=4)
        else:
            self.batch_frame.pack_forget()

    def _toggle_all(self, value: bool) -> None:
        for _, var in self._result_vars:
            var.set(value)

    def _selected_folders(self) -> list[str]:
        return [path for path, var in self._result_vars if var.get()]

    def _search(self) -> None:
        try:
            name = parse_batch_name(self.row_folder.get())
        except ValueError as exc:
            messagebox.showerror("Tên tìm không hợp lệ", str(exc))
            return
        extras = [d for d, var in self._drive_vars.items() if var.get()]
        self.search_btn.configure(state="disabled")
        self.result_count.configure(text=f"Đang quét '{name}'...")
        self.set_status("Đang quét thư mục...")
        threading.Thread(
            target=self._search_worker, args=(name, extras), daemon=True
        ).start()

    def _search_worker(self, name: str, extras: list[str]) -> None:
        try:
            found = run_search(name, extras)
        except (ValueError, OSError) as exc:
            self.after(0, lambda: self._search_failed(str(exc)))
        else:
            self.after(0, lambda: self._search_done(name, found))

    def _search_failed(self, detail: str) -> None:
        self.search_btn.configure(state="normal")
        self.set_status("Tìm thất bại", "red")
        messagebox.showerror("Tìm thư mục thất bại", detail)

    def _search_done(self, name: str, found: list[str]) -> None:
        self.search_btn.configure(state="normal")
        for child in self.results_box.winfo_children():
            child.destroy()
        self._result_vars = []
        for path in found:
            var = ctk.BooleanVar(value=True)
            self._result_vars.append((path, var))
            ctk.CTkCheckBox(self.results_box, text=path, variable=var).pack(
                anchor="w", padx=4, pady=1
            )
        if found:
            self.result_count.configure(text=f"Tìm thấy {len(found)} thư mục.")
            self.done(f"Tìm thấy {len(found)} thư mục tên '{name}'.")
        else:
            self.result_count.configure(text="Không tìm thấy thư mục nào.")
            self.set_status("Không tìm thấy thư mục nào.", "gray")

    def _sync_name_from_icon(self) -> None:
        icon = Path(self.row_icon.get())
        if icon.suffix.lower() != ".ico":
            return
        if self.name_var.get().strip() in ("", self._last_stem):
            self.name_var.set(icon.stem)
        self._last_stem = icon.stem

    def _run(self) -> None:
        icon = self.row_icon.get()
        folder = self.row_folder.get()
        if not icon or not folder:
            messagebox.showwarning(
                "Thiếu thông tin", "Hãy chọn cả file ICO và thư mục."
            )
            return
        if Path(icon).is_dir():
            messagebox.showerror(
                "Chưa chọn file", "Hãy mở output/icons và chọn 1 file .ico cụ thể."
            )
            return
        if Path(icon).suffix.lower() != ".ico":
            messagebox.showerror("Sai định dạng", "File icon phải là .ico.")
            return
        try:
            new_name = parse_new_name(self.name_var.get())
        except ValueError as exc:
            messagebox.showerror("Tên mới không hợp lệ", str(exc))
            return
        if is_batch_input(folder):
            self._run_batch(icon, new_name)
            return
        self.set_status("Đang đặt icon...")
        try:
            ini = run_apply(icon, folder, new_name)
        except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
            self.fail("Lỗi đặt icon", exc)
            return
        self.done(f"Đã đặt icon: {ini}")
        messagebox.showinfo(
            "Hoàn tất",
            f"Đã đặt icon cho:\n{folder}\n\n(chấp nhận nếu Explorer chưa cập nhật ngay)",
        )

    def _run_batch(self, icon: str, new_name: str | None) -> None:
        try:
            parse_batch_name(self.row_folder.get())
        except ValueError as exc:
            messagebox.showerror("Tên tìm không hợp lệ", str(exc))
            return
        selected = self._selected_folders()
        if not selected:
            messagebox.showwarning(
                "Chưa có thư mục",
                "Hãy bấm 'Tìm' rồi tick chọn ít nhất 1 thư mục cần đổi.",
            )
            return
        self.set_status(f"Đang đặt icon cho {len(selected)} thư mục...")
        try:
            ok, failed = run_apply_many(icon, selected, new_name)
        except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
            self.fail("Lỗi đặt icon hàng loạt", exc)
            return
        if failed:
            self.set_status(f"Xong: {len(ok)} ok, {len(failed)} lỗi.", "red")
            detail = "\n".join(f"{path}: {err}" for path, err in list(failed.items())[:10])
            messagebox.showwarning(
                "Xong một phần",
                f"Thành công {len(ok)}/{len(selected)} thư mục.\n\nLỗi:\n{detail}",
            )
        else:
            self.done(f"Đã đặt icon cho {len(ok)} thư mục.")
            messagebox.showinfo(
                "Hoàn tất",
                f"Đã đặt icon cho {len(ok)} thư mục.\n\n(chấp nhận nếu Explorer chưa cập nhật ngay)",
            )
