"""Giao diện Tkinter cho IconMaker.

Logic dễ hỏng (suy tên file đích, parse sizes, gọi chuyển đổi) tách thành
hàm thuần để test được mà không cần mở cửa sổ.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from iconmaker import converter, foldericon

PNG_EXTENSIONS = {".png"}
ICO_EXTENSIONS = foldericon.ICO_EXTENSIONS
ALL_SIZES_LABEL = "Tất cả"


def parse_sizes(selection: str) -> list[int]:
    """Chuyển lựa chọn combo của GUI thành list kích thước hợp lệ."""
    if selection == ALL_SIZES_LABEL:
        return converter.get_default_sizes()
    return [int(selection)]


def resolve_output_path(source: str | Path, out_dir: str | Path | None = None) -> str:
    """Tên file .ico tương ứng từ file nguồn, trong `out_dir` hoặc cạnh nguồn."""
    src = Path(source)
    target_dir = Path(out_dir) if out_dir else src.parent
    return str(target_dir / (src.stem + ".ico"))


def run_conversion(
    source: str | Path,
    out_dir: str | Path | None = None,
    sizes: list[int] | None = None,
) -> str:
    """Gọi thẳng converter với tham số kiểu GUI, trả về đường dẫn .ico."""
    dest = resolve_output_path(source, out_dir)
    return converter.convert_png_to_ico(source, dest, sizes)


def apply_folder_icon(icon_path: str | Path, folder_path: str | Path) -> str:
    """Copy icon vào thư viện ổn định rồi đặt cho thư mục; trả về đường dẫn desktop.ini."""
    installed = foldericon.install_icon(icon_path)
    return foldericon.set_folder_icon(folder_path, installed)


class IconMakerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("IconMaker")
        self.geometry("500x330")
        self.resizable(False, False)

        self.source_var = tk.StringVar()
        self.out_dir_var = tk.StringVar()
        self.size_var = tk.StringVar(value=ALL_SIZES_LABEL)
        self.icon_var = tk.StringVar()
        self.folder_var = tk.StringVar()

        self._build()

    def _build(self) -> None:
        pad = {"padx": 8, "pady": 4}

        frm_src = tk.Frame(self)
        frm_src.pack(fill="x", **pad)
        tk.Label(frm_src, text="Ảnh PNG:").pack(side="left")
        tk.Entry(frm_src, textvariable=self.source_var, width=40).pack(
            side="left", fill="x", expand=True, padx=4
        )
        tk.Button(frm_src, text="Chọn...", command=self._pick_source).pack(side="left")

        frm_out = tk.Frame(self)
        frm_out.pack(fill="x", **pad)
        tk.Label(frm_out, text="Thư mục lưu:").pack(side="left")
        tk.Entry(frm_out, textvariable=self.out_dir_var, width=40).pack(
            side="left", fill="x", expand=True, padx=4
        )
        tk.Button(frm_out, text="Chọn...", command=self._pick_out_dir).pack(side="left")

        frm_size = tk.Frame(self)
        frm_size.pack(fill="x", **pad)
        tk.Label(frm_size, text="Kích thước:").pack(side="left")
        choices = [str(s) for s in converter.get_default_sizes()] + [ALL_SIZES_LABEL]
        tk.OptionMenu(frm_size, self.size_var, *choices).pack(side="left", padx=4)

        self.btn_convert = tk.Button(self, text="Convert", command=self._convert)
        self.btn_convert.pack(pady=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=8, pady=6)

        frm_icon = tk.Frame(self)
        frm_icon.pack(fill="x", **pad)
        tk.Label(frm_icon, text="File ICO:").pack(side="left")
        tk.Entry(frm_icon, textvariable=self.icon_var, width=40).pack(
            side="left", fill="x", expand=True, padx=4
        )
        tk.Button(frm_icon, text="Chọn...", command=self._pick_icon).pack(side="left")

        frm_folder = tk.Frame(self)
        frm_folder.pack(fill="x", **pad)
        tk.Label(frm_folder, text="Thư mục:").pack(side="left")
        tk.Entry(frm_folder, textvariable=self.folder_var, width=40).pack(
            side="left", fill="x", expand=True, padx=4
        )
        tk.Button(frm_folder, text="Chọn...", command=self._pick_folder).pack(side="left")

        self.btn_apply = tk.Button(
            self, text="Đặt icon cho thư mục", command=self._apply_folder_icon
        )
        self.btn_apply.pack(pady=6)

        self.status = tk.Label(self, text="Sẵn sàng", anchor="w", fg="gray")
        self.status.pack(fill="x", padx=8, pady=2)

    def _pick_source(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn ảnh PNG",
            filetypes=[("PNG images", "*.png"), ("All files", "*.*")],
        )
        if path:
            self.source_var.set(path)

    def _pick_out_dir(self) -> None:
        path = filedialog.askdirectory(title="Chọn thư mục lưu")
        if path:
            self.out_dir_var.set(path)

    def _pick_icon(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file ICO",
            filetypes=[("ICO icons", "*.ico"), ("All files", "*.*")],
        )
        if path:
            self.icon_var.set(path)

    def _pick_folder(self) -> None:
        path = filedialog.askdirectory(title="Chọn thư mục cần đổi icon")
        if path:
            self.folder_var.set(path)

    def _convert(self) -> None:
        source = self.source_var.get().strip()
        if not source:
            messagebox.showwarning("Thiếu file", "Hãy chọn ảnh PNG trước.")
            return
        if Path(source).suffix.lower() not in PNG_EXTENSIONS:
            messagebox.showerror("Sai định dạng", "File được chọn không phải PNG.")
            return
        try:
            sizes = parse_sizes(self.size_var.get())
        except ValueError:
            messagebox.showerror("Lỗi", f"Kích thước không hợp lệ: {self.size_var.get()!r}")
            return
        self.status.config(text="Đang chuyển...", fg="black")
        try:
            dest = run_conversion(
                source, self.out_dir_var.get().strip() or None, sizes
            )
        except (ValueError, FileNotFoundError, OSError) as exc:
            self.status.config(text="Thất bại", fg="red")
            messagebox.showerror("Lỗi chuyển đổi", str(exc))
            return
        self.status.config(text=f"Xong: {dest}", fg="green")
        messagebox.showinfo("Hoàn tất", f"Đã tạo icon:\n{dest}")

    def _apply_folder_icon(self) -> None:
        icon = self.icon_var.get().strip()
        folder = self.folder_var.get().strip()
        if not icon or not folder:
            messagebox.showwarning("Thiếu thông tin", "Hãy chọn cả file ICO và thư mục.")
            return
        if Path(icon).suffix.lower() not in ICO_EXTENSIONS:
            messagebox.showerror("Sai định dạng", "File icon phải là .ico.")
            return
        self.status.config(text="Đang đặt icon...", fg="black")
        try:
            ini = apply_folder_icon(icon, folder)
        except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
            self.status.config(text="Thất bại", fg="red")
            messagebox.showerror("Lỗi đặt icon", str(exc))
            return
        self.status.config(text=f"Đã đặt icon: {ini}", fg="green")
        messagebox.showinfo(
            "Hoàn tất",
            f"Đã đặt icon cho:\n{folder}\n\n(chấp nhận nếu Explorer chưa cập nhật ngay)",
        )


def main() -> None:
    IconMakerApp().mainloop()


if __name__ == "__main__":
    main()