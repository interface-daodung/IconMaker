# Plan 002 — Giao diện Tkinter

**Trạng thái:** ✅ Hoàn thành (2026-09-13). Code: `src/iconmaker/gui.py` (chạy `python -m iconmaker.gui`, cần PYTHONPATH=src). Test logic thuần: `tests/test_gui_logic.py` (6 pass). Đã mở GUI thật kiểm chứng bằng tay qua launcher.

**2026-09-14 — CustomTkinter:** Viết lại GUI bằng `customtkinter` (thêm vào `requirements.txt`): `IconMakerApp(ctk.CTk)`, mặc định theme Dark, nút "Đổi sang Sáng/Tối" đảo `set_appearance_mode` qua hàm thuần `next_theme()` (có test). Chạy bằng `pythonw` (không console): `make gui`. Logic cũ (`parse_sizes`, `resolve_output_path`, `run_conversion`, `apply_folder_icon`) giữ nguyên chữ ký — test 8 pass, tổng 72/72 pass. Đã kiểm chứng: cửa sổ "IconMaker" hiện qua `pythonw` và qua launcher (process `pythonw3.13`).

**2026-09-14 — Icon GUI:** `MainWindow` gán icon `assets/icons/IconMaker.ico` qua `iconbitmap()` trong `_apply_app_icon()` (bỏ qua lỗi nếu thiếu file để test headless không vỡ). Đường dẫn resolve tuyệt đối trong `core/paths.py::app_icon_path()` (neo theo vị trí file, đúng mọi cwd) + test `test_app_icon_resolves_to_repo_file`. Đồng bộ `launcher/.../Assets/icon.ico` từ cùng file để exe launcher cùng icon; build pass.

## Mục tiêu

GUI đơn giản để người dùng: chọn ảnh PNG → chọn nơi lưu → bấm Convert → nhận file `.ico`.

## Trách nhiệm

- `src/iconmaker/gui.py` — lớp Tkinter thân thiện, dùng cứng `converter.convert_png_to_ico`.
- Các widget:
  - Ô nhập / nút **Browse** chọn file PNG (dùng `filedialog.askopenfilename`, filter `*.png`).
  - Ô nhập / nút **Browse** chọn thư mục đích (hoặc chọn tên file đích).
  - Combo chọn kích thước icon (16/32/48 hoặc "tất cả").
  - Nút **Convert** + thanh trạng thái / messagebox kết quả.
  - Vòng lặp `mainloop()` khi chạy trực tiếp (`__main__`).

## Điểm dễ hỏng (test có nghĩa ở đây là **logic**, không phụ thuộc hiển thị)

GUI thuần khó unit test bằng pytest → tách phần logic dễ hỏng thành hàm thuần có thể test:

- `resolve_output_path(src: str, out_dir: str | None, suffix: str) -> str` — suy tên file `.ico` từ `.png` (xử lý trùng tên, ký tự đặc biệt).
- `parse_sizes(selection: str) -> list[int]` — chuyển lựa chọn combo thành list kích thước hợp lệ cho converter.
- Toàn bộ phần "gọi converter + báo kết quả" gói trong hàm `run_conversion(src, out, sizes) -> str` để test gọi thẳng.

## Quy ước

- Nếu `python -m tkinter` không mở được trên máy setup, test GUI vẫn phải chạy được (test chỉ nhắm vào phần logic thuần).
- GUI gọi converter, không copy logic chuyển đổi.
- Window title: **IconMaker**.

## Ghi chú triển khai

(Để trống — agent triển khai điền vào sau khi xong.)