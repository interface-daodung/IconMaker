# Plan 007 — Đặt icon cho thư mục (desktop.ini)

**Trạng thái:** ✅ Hoàn thành (2026-09-14) — quyết định [D13], [D14].

## Yêu cầu

- GUI cho phép chọn **1 file ICO** + **1 thư mục**, bấm nút để đổi icon thư mục.
- Cơ chế: ghi file **ẩn** `desktop.ini` (`[.ShellClassInfo] IconResource=<ico>,0`)
  + `attrib +h +s` cho ini, `attrib +r` cho thư mục, `ie4uinit.exe -show` refresh.
- **Ràng buộc quan trọng:** đường dẫn trong `desktop.ini` là tuyệt đối, nên icon
  phải được copy vào **thư viện icon ổn định** `~/OneDrive/Pictures/Icon`
  (không nằm trong app) trước khi trỏ tới — di chuyển app không hỏng icon.

## Thiết kế (`src/iconmaker/foldericon.py`)

- `icon_store_dir()` — resolve thư viện theo thứ tự: env `ICONMAKER_ICON_STORE`
  → `Icon` đã tồn tại trong Pictures (OneDrive trước) → mặc định.
- `install_icon(icon, store=None)` — copy `.ico` vào store; trùng nội dung thì
  tái dùng, trùng tên khác nội dung thì hậu tố ` (n)`; reject không phải `.ico`.
- `make_ini_content(icon)` — sinh nội dung desktop.ini, đường dẫn resolve tuyệt đối.
- `set_folder_icon(folder, icon)` — bỏ `-h -s -r` ini cũ, ghi mới, ẩn lại,
  `+r` folder, refresh Explorer. `shell=False` cho mọi lệnh attrib.
- CLI: `python -m iconmaker.foldericon <icon.ico> <thu_muc> [--store <dir>]`.
  `make foldericon ICON=... FOLDER=...`.
- GUI (`gui.py`): hàm thuần `apply_folder_icon(icon, folder)` = install + set;
  khu vực riêng dưới separator với 2 hàng chọn ICO/thư mục + nút
  "Đặt icon cho thư mục".

## Đã kiểm chứng

- 12 test `tests/test_foldericon.py`: copy/dedup/đụng tên/lỗi input; nội dung
  ini; trên Windows thật: atrib Hidden+System của ini, ReadOnly của folder,
  ghi đè ini cũ. 1 test chain GUI trong `test_gui_logic.py`. **71/71 pass.**
- `make foldericon` trên thật: icon vào `C:\Users\inter\OneDrive\Pictures\Icon\`,
  `desktop.ini` đúng nội dung + đúng thuộc tính.
