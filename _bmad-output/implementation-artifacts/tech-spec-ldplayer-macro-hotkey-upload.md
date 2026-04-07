---
title: 'Trigger LDPlayer macro bằng phím tắt cho bước upload Shorts'
slug: 'ldplayer-macro-hotkey-upload'
created: '2026-03-22'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['python', 'uiautomator2', 'gdown', 'pytest', 'python-dotenv', 'pywinauto']
files_to_modify: ['main.py', 'src/android_auto.py', 'src/ldplayer_macro.py', 'requirements.txt', 'tests/test_ldplayer_macro.py']
code_patterns: ['Modular CLI', 'Single-threaded loop', 'Best-effort UI selectors + fallbacks', 'SQLite-based deduplication']
test_patterns: ['pytest']
---

# Tech-Spec: Trigger LDPlayer macro bằng phím tắt cho bước upload Shorts

**Created:** 2026-03-22

## Overview

### Problem Statement

Luồng upload Shorts hiện tại dùng `uiautomator2` để click/selector UI trên YouTube app. Các selector/text có thể thay đổi theo phiên bản YouTube/locale, khiến flow dễ “lệch” hoặc kém ổn định. Người dùng muốn chuyển phần thao tác upload (từ nút Create/+) sang chạy **macro built-in của LDPlayer**, và kích hoạt macro bằng **phím tắt** để tăng độ ổn định.

### Solution

Giữ nguyên phần **mở YouTube app bằng `uiautomator2`** như hiện tại. Tại điểm bắt đầu upload (bấm Create/+), tool sẽ **focus đúng cửa sổ LDPlayer (window title: `LDPlayer`)** và **gửi hotkey `Ctrl+F5`** để LDPlayer chạy macro upload. Macro chịu trách nhiệm chọn **ảnh mới nhất** trong gallery và hoàn tất các bước upload (bao gồm cài duration ~5 giây theo macro).

### Scope

**In Scope:**
- Tích hợp cơ chế trigger macro LDPlayer qua hotkey `Ctrl+F5`.
- Bảo đảm focus đúng cửa sổ emulator (window title = `LDPlayer`) trước khi gửi hotkey.
- Xác định rõ “điểm bàn giao” giữa code và macro: macro bắt đầu từ bước bấm Create (+) trong YouTube.
- Logging rõ ràng: khi nào đã focus window, khi nào đã gửi hotkey.

**Out of Scope:**
- Thiết kế/record macro trong LDPlayer (giả định user đã có macro hoạt động và gán hotkey).
- Tự động vượt CAPTCHA/2FA.
- Chạy nhiều instance LDPlayer song song.

## Context for Development

### Codebase Patterns

- **Modular env-driven runner**: `main.py` điều phối tuần tự (single-thread) các bước: lấy ảnh → dedup DB → automation upload → GC file. Cấu hình lấy từ ENV/.env (không dùng CLI args).
- **ADB / uiautomator2**: kết nối thiết bị ở `src/device.py:27` (`connect_device(...)` có retry + healthcheck).
- **Uploader kiểu “all-in-one method”**: `src/android_auto.py:52` có `upload_short(...)` hiện đang làm cả luồng UI; sẽ là anchor point để cắt luồng và chuyển sang “macro trigger mode”.
- **Dedup bằng SQLite**: `src/db_manager.py` lưu SHA-256 hash, đảm bảo không upload trùng.
- **Input ảnh**: lấy từ Drive (`src/drive_sync.py`) hoặc local (`src/local_scan.py`), đều sort theo tên file.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `main.py` | Env loader + control loop + DB mark/GC. Đọc cấu hình từ ENV/.env và điều phối backend upload (uiauto vs ld-macro). |
| `src/device.py` | Kết nối uiautomator2 + retry/healthcheck. Giữ nguyên để đảm bảo YouTube được mở bằng ADB trước khi chạy macro. |
| `src/android_auto.py` | `YouTubeUploader.upload_short(...)` hiện làm full flow. Cần refactor để: (1) mở YouTube, (2) dừng ở trạng thái sẵn sàng bấm Create (+), (3) trigger macro LDPlayer qua hotkey. |
| `src/drive_sync.py` | Download/filter ảnh từ Drive. Không liên quan trực tiếp macro nhưng ảnh hưởng input pipeline. |
| `src/local_scan.py` | Scan ảnh local; hiện sort theo tên, không phải “mới nhất”. Macro yêu cầu “chọn ảnh mới nhất” -> cần quyết định chiến lược đặt file vào Android để “mới nhất” thật sự là ảnh current. |
| `src/db_manager.py` | Dedup/mark_success.
| `tests/test_db_manager.py` | Pattern test hiện tại dùng `pytest`.
| `requirements.txt` | Chỗ thêm dependency cho Windows window-focus + hotkey (đề xuất `pywinauto`). |

### Technical Decisions

- **Trigger hotkey trên Windows**: repo hiện chưa có thư viện focus window/send keys. Hướng phù hợp: dùng `pywinauto` (UIA backend) để:
  - tìm window theo title `LDPlayer` (ưu tiên exact match, nhưng cho phép cấu hình title nếu LDPlayer đổi tên)
  - bring-to-foreground + set focus
  - verify foreground window đúng LDPlayer trước khi send
  - send `Ctrl+F5`
  - retry focus+send tối đa N lần (vd 3) nếu detect foreground window không đúng
- **Điểm bàn giao (handoff) rõ ràng**: uiautomator2 chỉ chịu trách nhiệm mở YouTube và đưa app về state ổn định; macro bắt đầu từ Create (+) và tự xử lý chọn ảnh mới nhất + upload + set duration ~5s.
- **“Ảnh mới nhất” trong macro** phụ thuộc vào cách ảnh xuất hiện trong gallery/file picker.
  - Vấn đề thực tế: khi upload trên LDPlayer đôi khi UI picker “nhảy” sang folder khác (ví dụ `NguyenBao`) nếu dựa vào shared folder Windows.
  - Quyết định: tool sẽ **không dựa vào path Windows**. Thay vào đó luôn `d.push(...)` ảnh vào **Android path cố định**: `/sdcard/Download/auto_upload_latest.jpg` (xóa cũ → push mới) để:
    - ảnh hiện tại luôn là item mới nhất trong Downloads/Recent
    - giảm rủi ro bị “nhảy folder” trong quá trình chọn ảnh

## Implementation Plan

### Tasks

- [ ] Task 1: Thêm module trigger macro LDPlayer (Windows)
  - File: `src/ldplayer_macro.py` (new)
  - Action:
    - Tạo API tối thiểu để dùng từ flow upload:
      - `focus_ldplayer_window(window_title: str) -> None`
      - `send_hotkey_ctrl_f5() -> None` (cố định theo yêu cầu hiện tại)
      - `trigger_ldplayer_macro(window_title: str = "LDPlayer") -> None` (gọi 2 hàm trên)
    - Dùng `pywinauto` (UIA backend) để tìm window theo title chính xác `LDPlayer`, bring-to-foreground, set focus, rồi gửi hotkey.
    - Nếu không tìm thấy window → raise error rõ ràng (để caller quyết định fail ảnh hiện tại).
  - Notes:
    - Đây là tích hợp **Windows-only** (vì điều khiển window focus + send keys).
    - Quy ước: window title phải đúng `LDPlayer` (user đã xác nhận).

- [ ] Task 2: Bổ sung dependency cho Windows automation
  - File: `requirements.txt`
  - Action: Thêm `pywinauto`.
  - Notes: Không thêm thêm framework automation khác nếu không cần.

- [ ] Task 3: Refactor uploader để hỗ trợ “macro backend” + fix tình trạng picker “nhảy folder” khi upload
  - File: `src/android_auto.py`
  - Action:
    - Tách luồng hiện tại trong `YouTubeUploader.upload_short(...)` thành các mảnh có thể tái dùng:
      1) `push_image_to_device(image_path: str, device_path: str) -> None`
      2) `open_youtube_and_settle() -> bool` (app_start + wait settle + handle_popups)
      3) `wait_for_upload_success(timeout_s: int) -> bool` (dựa trên indicator text như hiện tại)
    - Với backend macro: **không dùng shared folder Windows** (vì dễ bị nhảy sang folder khác như `NguyenBao`).
    - Thêm method mới chạy theo thiết kế “handoff”:
      - `upload_short_via_ldplayer_macro(image_path: str, window_title: str = "LDPlayer", macro_timeout_s: int = 180) -> bool`
        - Chuẩn bị ảnh trên device sao cho macro “chọn ảnh mới nhất” đúng ảnh current:
          - Dùng device path cố định: `/sdcard/Download/auto_upload_latest.jpg`
          - Trước khi push: xóa file cũ ở đúng path (nếu có)
          - Push ảnh mới vào đúng path (để timestamp mới nhất)
          - (Optional nhưng khuyến nghị) dọn các file `auto_upload_*` cũ trong `/sdcard/Download/` để Recent không nhiễu
        - Gọi `open_youtube_and_settle()` để đảm bảo YouTube đang ở home feed
        - Gọi `trigger_ldplayer_macro(window_title)` (Task 1)
        - Chờ tối đa `macro_timeout_s` để phát hiện thành công qua `wait_for_upload_success(...)`
        - Nếu success: xóa file `/sdcard/Download/auto_upload_latest.jpg` trên device
    - Giữ lại `upload_short(...)` cũ làm backend fallback (nếu muốn).
  - Notes:
    - Macro bắt đầu từ bước **Create (+)**, nên code **không click Create** nữa.

- [ ] Task 4: Chuyển cấu hình sang ENV (.env) thay vì CLI
  - File: `main.py`
  - Action:
    - Dùng `python-dotenv` để load `.env` (nếu có) ngay khi start.
      - Quy ước: **ENV hệ thống thắng `.env`** (không override biến đã set sẵn trong OS).
    - **Loại bỏ `argparse`** và toàn bộ CLI flags.
    - Đọc cấu hình từ ENV (tên biến đề xuất):
      - Parse quy ước:
        - Boolean: chấp nhận `true/false/1/0/yes/no` (case-insensitive)
        - Int: bắt buộc là số nguyên dương (nếu parse lỗi → exit với message rõ ràng)

      - Input:
        - `DRIVE_URL` (optional nếu có `LOCAL_DIR`)
        - `LOCAL_DIR` (optional nếu có `DRIVE_URL`)
          - Ví dụ đường dẫn đúng của bạn: `C:\Users\Admin\OneDrive\Tài liệu\XuanZhi9\Pictures`
        - `MAX_FILES` (optional, int; default = 5)
      - Android / uploader:
        - `ADB_SERIAL` (required)
        - `TARGET_SECONDS` (optional, int; default 5)
        - `DRY_RUN` (optional, bool; default false)
      - Upload backend:
        - `UPLOAD_BACKEND` (optional: `uiauto` | `ld-macro`, default `ld-macro`)
        - `LD_WINDOW_TITLE` (optional, string; default `LDPlayer`)
        - `LD_MACRO_TIMEOUT` (optional, int; default 180)
    - Validate cấu hình:
      - Nếu thiếu `ADB_SERIAL` → exit với message rõ ràng
      - Nếu thiếu cả `DRIVE_URL` và `LOCAL_DIR` → exit với message rõ ràng
      - Nếu `UPLOAD_BACKEND` không thuộc `{uiauto, ld-macro}` → exit với message rõ ràng
      - Nếu `UPLOAD_BACKEND=ld-macro` và `DRY_RUN=true` → exit với message rõ ràng
    - Wiring `MAX_FILES`:
      - Nếu `LOCAL_DIR` → truyền `max_files` vào `scan_local_images(..., max_files=MAX_FILES)`
      - Nếu `DRIVE_URL` → truyền `max_files` vào `download_and_filter(..., max_files=MAX_FILES)`
    - Trong loop, chọn backend:
      - `ld-macro` → `upload_short_via_ldplayer_macro(...)`
      - `uiauto` → `upload_short(...)`
    - Quy tắc DB/GC giữ nguyên:
      - Chỉ `mark_success(hash)` khi `upload_success=True` và `DRY_RUN=false`
      - Chỉ xóa file local khi `upload_success=True`
  - Notes:
    - Người dùng chạy tool bằng cách set ENV hoặc tạo file `.env`, rồi chạy `python main.py`.

- [ ] Task 5: Bổ sung unit test cho module macro (mock)
  - File: `tests/test_ldplayer_macro.py` (new)
  - Action:
    - Mock `pywinauto` để test:
      - không tìm thấy window → raise đúng error
      - tìm thấy window → gọi set_focus + send_keys đúng thứ tự
    - Test “wiring-level” tối thiểu: `trigger_ldplayer_macro("LDPlayer")` gọi các bước focus + send hotkey.

### Acceptance Criteria

- [ ] AC1: Given LDPlayer đang chạy và có cửa sổ title đúng là `LDPlayer`, when đến bước upload với backend `ld-macro`, then tool bring-to-foreground window đó, **verify foreground đúng LDPlayer**, và gửi hotkey **Ctrl+F5** (retry focus+send tối đa 3 lần nếu foreground không đúng), và log có dòng thể hiện `window_title` đã dùng.

- [ ] AC2: Given YouTube app đã được mở (home feed) bằng `uiautomator2`, when tool trigger macro, then macro bắt đầu từ bước **Create (+)** và thực hiện upload dựa trên việc **chọn ảnh mới nhất** trong picker.

- [ ] AC3: Given tool đang xử lý ảnh X, when backend `ld-macro` chuẩn bị ảnh, then ảnh X được push lên device tại `/sdcard/Download/auto_upload_latest.jpg` (xóa file cũ trước nếu có) để đảm bảo ảnh X là “mới nhất” cho picker và tránh tình trạng bị “nhảy” sang folder khác (ví dụ `NguyenBao`).

- [ ] AC4: Given không tìm thấy cửa sổ `LDPlayer`, when tool trigger macro, then ảnh hiện tại bị coi là fail với error rõ ràng, **không ghi DB success**, và tool tiếp tục ảnh kế tiếp.

- [ ] AC5: Given đã gửi hotkey nhưng sau `LD_MACRO_TIMEOUT` giây không phát hiện được indicator thành công, when timeout, then ảnh hiện tại bị coi là fail, **không ghi DB success**, và tool tiếp tục ảnh kế tiếp.

- [ ] AC6: Given `UPLOAD_BACKEND=ld-macro` và `DRY_RUN=true`, when start tool, then tool dừng và báo rõ: dry-run không hỗ trợ cho macro backend.

- [ ] AC7: Given macro đã được cấu hình duration ~5 giây trong LDPlayer, when upload thành công, then video Shorts tạo ra có thời lượng xấp xỉ 5 giây (manual verification).

## Additional Context

### Dependencies

- Python 3.9+
- `uiautomator2` (kết nối ADB để mở YouTube + quan sát indicator)
- `gdown` (Drive sync)
- `sqlite3` (built-in) (dedup)
- `pytest` (tests)
- `pywinauto` (Windows focus window + send hotkey)

### Testing Strategy

- **Unit tests (pytest):**
  - `tests/test_ldplayer_macro.py`: mock pywinauto để kiểm tra behavior khi tìm/không tìm thấy window.
  - Test logic normalize/emit hotkey Ctrl+F5 (nếu có layer chuyển đổi).
- **Manual E2E (Windows + LDPlayer):**
  1) Mở LDPlayer, đảm bảo window title hiển thị là `LDPlayer`
  2) Mở YouTube và đăng nhập
  3) Cấu hình macro LDPlayer, gán hotkey `Ctrl+F5`, macro bắt đầu từ Create (+) và upload 1 short
  4) Tạo file `.env` và set tối thiểu:
     - `UPLOAD_BACKEND=ld-macro`
     - `LD_WINDOW_TITLE=LDPlayer`
     - `LD_MACRO_TIMEOUT=180`
     - `ADB_SERIAL=...`
     - `LOCAL_DIR=C:\Users\Admin\OneDrive\Tài liệu\XuanZhi9\Pictures` (hoặc `DRIVE_URL=...`)
  5) Chạy `python main.py`
  6) Xác nhận log: focus window + send hotkey + detect success (hoặc timeout/fail đúng như AC)

### Notes

- Backend `ld-macro` sẽ **chiếm focus** của desktop để gửi phím tắt → trong lúc chạy không nên thao tác máy.
- Nếu có nhiều cửa sổ/instance LDPlayer, tìm theo title `LDPlayer` có thể không đủ chính xác; bản MVP này **out of scope**.
- Success detection hiện phụ thuộc indicator UI trong app YouTube (qua uiautomator2); nếu YouTube đổi wording UI, cần update selector/từ khóa.
