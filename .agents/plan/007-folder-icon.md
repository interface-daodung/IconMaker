# Plan 007 — Đặt icon cho thư mục (desktop.ini)

**Trạng thái:** ✅ Hoàn thành (2026-09-14) — quyết định [D13], [D14].
Bổ sung 2026-09-14 [D23]: tab "Icon thư mục" mở dialog thẳng `output/icons`
(prefill ICO mới nhất qua `newest_file`), thêm ô "Tên mới" (trống = giữ tên
gốc) chuẩn hoá bằng `sanitize_icon_name` rồi `install_icon(..., new_name)`
trước khi `set_folder_icon`; CLI thêm `--name`, `make foldericon NAME=... STORE=...

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

## Bổ sung 2026-09-14 — tìm hàng loạt `*<tên>` (GUI)

- Ô "Thư mục" gõ `*<tên>` (vd `*MyApp`) → hiện khung hàng loạt: nút **Tìm**,
  1 checkbox cho mỗi ổ đĩa ngoài ổ home, list kết quả tick chọn từng dòng
  (+ "Chọn hết"/"Bỏ hết"), nút "Đặt icon" áp dụng 1 lần cho mọi thư mục đã tick.
- `src/service/folder_search.py`: `is_batch_input`/`parse_batch_name`
  (khớp tên chính xác, case-insensitive); `find_folders_by_name` quét home
  (`Path.home()`) + roots phụ, luôn cắt cây TEMP/TMP/AppData/LocalAppData,
  cắt nhánh có phần bắt đầu `.` dưới home (ngoài home cho phép `.`),
  bỏ qua thư mục ẩn/system (Windows), không follow symlink/junction;
  `skip_dirs=None` = mặc định hệ thống, `[]` = tắt (cho test dưới %TEMP%).
- `tools/foldericon_tool/controller.py`: `is_batch_input`, `parse_batch_name`,
  `default_search_root`, `extra_drives`, `run_search`, `run_apply_many`
  (cài icon 1 lần rồi đặt cho từng thư mục, trả về `(ok, {folder: lỗi})`).
- Quét chạy trong thread nền để không treo GUI; batch là tính năng GUI,
  CLI `python -m service.foldericon` giữ nguyên 1 thư mục.
- 16 test `tests/test_folder_search.py` (parse, khớp chính xác, dot, skip
  TEMP/AppData, apply_many cài 1 lần + gom lỗi).
