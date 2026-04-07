---
title: 'Auto Upload Shorts qua LDPlayer (ENV + Macro Hotkey)'
slug: 'auto-upload-shorts-mvp'
created: '2026-03-20'
status: 'Implementation Complete'
stepsCompleted: [1, 2, 3, 4, 5]
tech_stack: ['python', 'uiautomator2', 'gdown', 'python-dotenv', 'pywinauto']
files_to_modify: ['main.py', 'src/device.py', 'src/drive_sync.py', 'src/android_auto.py', 'src/db_manager.py', 'src/ldplayer_macro.py', 'data/titles.txt', 'tests/test_ldplayer_macro.py']
code_patterns: ['Modular ENV Runner', 'Single-threaded loop', 'Robust Error/Pop-up Handling']
test_patterns: ['pytest']
review_notes: |
  Adversarial review completed.
  Findings: 3 total, 3 fixed, 0 skipped.
  Resolution approach: Auto-fix.
---

# Đặc tả Kỹ thuật (Tech-Spec): Auto Upload Shorts qua LDPlayer (ENV + Macro Hotkey)

**Ngày tạo:** 2026-03-20

## Tổng quan (Overview)

### Tuyên bố Vấn đề (Problem Statement)
Việc tải lên thủ công hàng trăm video Shorts dạng ảnh tĩnh tốn quá nhiều thời gian và các cách upload từ máy tính (PC) hiện tại không hỗ trợ việc chèn nhạc nền xu hướng (trending music) được tích hợp sẵn trên ứng dụng YouTube di động. Người sáng tạo nội dung gặp khó khăn để "scale" (mở rộng quy mô) nếu họ muốn giữ được các đặc quyền/thuật toán của nền tảng Shorts nguyên bản.

### Giải pháp (Solution)
Một công cụ Python chạy theo cấu hình ENV/.env có khả năng quét/tải ảnh từ Google Drive hoặc thư mục local, lọc ảnh để chống trùng lặp qua DB cục bộ, và tự động hóa thao tác trên giả lập LDPlayer/Android. Công cụ kết hợp 2 backend: (1) luồng `uiautomator2` (legacy) và (2) backend LDPlayer Macro kích hoạt bằng phím tắt (Ctrl+F5) để thực thi phần upload trong UI.

### Phạm vi (Scope)

**Trong phạm vi (In Scope):**
- Tải file từ đường dẫn chia sẻ (shareable link) của Google Drive. Lọc tự động chỉ lấy đúng định dạng ảnh (ví dụ: `.png`, `.jpg`).
- Theo dõi ID ảnh cục bộ bằng mã băm (SHA-256) của file để chống trùng lặp chính xác 100%.
- Tự động hóa YouTube trên Android emulator bằng `uiautomator2` cho các bước mở app/ổn định UI; và (tuỳ backend) giao phần upload cho LDPlayer Macro kích hoạt hotkey (Ctrl+F5).
- Giao diện CLI xuất ra tiến trình log, tự động dọn dẹp file ảnh tạm (Garbage Collection) sau khi upload thành công hoặc khi xảy ra sự cố ngoại lệ.

**Nằm ngoài Phạm vi (Out of Scope):**
- Giao diện người dùng đồ họa (GUI).
- Chạy đa luồng nhiều máy ảo/emulator cùng lúc.
- Tiêu đề sinh ra bằng Trí tuệ Nhân tạo (chỉ dùng danh sách tĩnh quay vòng).
- Tự động vượt CAPTCHA nâng cao của Google nếu bị chặn.

## Bối cảnh Lập trình (Context for Development)

### Cấu trúc Mã nguồn (Codebase Patterns)
- **Kiến trúc Khởi tạo (Clean Slate Project):** Không bị trói buộc vì code cũ.
- **Kiến trúc Module hóa (Modular Architecture):** Giao diện chính nối kết tuần tự với các module độc lập như Drive Sync, Android Auto, Local DB. Vòng điều khiển (loop) chạy đơn luồng `main.py` có cơ chế `try...except` cứng cáp để bỏ qua (skip) ảnh lỗi và tiếp tục.

### Thư mục và File Tham chiếu (Files to Reference)

| File | Chức năng (Purpose) |
| ---- | ------- |
| `main.py` | Entry-point theo ENV/.env và Vòng lặp tự động hóa (Automation Loop) chính. Điều hướng logic backend (`UPLOAD_BACKEND`) và báo cáo log. |
| `src/device.py` | Kết nối `uiautomator2` qua ADB, healthcheck, auto-discovery, retry. |
| `src/drive_sync.py` | Nhúng `gdown`, có hàm tiện ích giải nén và lọc định dạng file rác (đảm bảo chỉ nhận ảnh hợp lệ). |
| `src/android_auto.py` | Điều khiển YouTube bằng `uiautomator2`, ưu tiên `resource-id`/`content-desc`, `wait(timeout)`, xử lý pop‑up. |
| `src/db_manager.py` | Quản lý `history.sqlite` (SQLite) để lưu băm SHA-256; API `is_uploaded`/`mark_success`. |
| `data/titles.txt` | Nơi chứa các mẫu Caption ngẫu nhiên sẽ được chọn khi đăng lên YouTube. |

### Quyết định Kỹ thuật (Technical Decisions)
- **Tự động hóa Thiết bị/Emulator:** Sử dụng `uiautomator2` để kết nối/điều khiển Android emulator (LDPlayer) qua ADB. Phần upload có thể chạy theo 2 backend: `uiautomator2` (legacy) hoặc LDPlayer Macro (trigger hotkey Ctrl+F5 qua `pywinauto` trên Windows).
- **Tích hợp Google Drive:** `gdown` để lấy tốc độ phát triển cực cao, khỏi mất công xin cấp phép Google OAuth phức tạp.
- **Cơ sở dữ liệu cục bộ (Local DB):** `SQLite` 1 bảng đơn giản thay vì JSON để đảm bảo ACID (tránh corrupt khi app thoát giữa chừng).

### Kết nối Thiết bị (LDPlayer qua ADB)
- **Yêu cầu:** LDPlayer đang chạy và bật ADB; YouTube app đã cài và đăng nhập.
- **Cấu hình:** Thiết lập `ADB_SERIAL` (ví dụ: `127.0.0.1:5555`).
- **Thiết lập ban đầu (1 lần):**
  1) `adb connect 127.0.0.1:<PORT>` (nếu cần)
  2) `python -m uiautomator2 init -s 127.0.0.1:<PORT>`
  3) Kiểm tra `adb devices` thấy trạng thái `device`.
- **Mẫu khởi động YouTube:**
  ```python
  import uiautomator2 as u2

  def connect(serial=None):
      d = u2.connect(serial or "127.0.0.1:<PORT>")
      d.healthcheck()
      return d

  d = connect()
  d.app_start("com.google.android.youtube")
  ```
- **Ghi chú ổn định:** Khóa hướng dọc (portrait), thêm `wait(timeout)` cho mỗi thao tác, xử lý pop‑up quyền (Allow), và dùng `d.dump_hierarchy()` để tìm `resource-id`/`content-desc` bền thay vì text thuần.

## Kế hoạch Cài đặt (Implementation Plan)

#### Checklist Thiết bị (LDPlayer)
- Mở LDPlayer và bật ADB (cổng thường là `127.0.0.1:5555`, tuỳ cấu hình).
- Đăng nhập Play Store và cài YouTube (`com.google.android.youtube`).
- Chạy `python -m uiautomator2 init -s 127.0.0.1:<PORT>`.
- Xác nhận `adb devices` hiển thị `device`.
- Nếu dùng backend macro hotkey: mở cửa sổ LDPlayer (title mặc định `LDPlayer`) và đảm bảo cửa sổ hiển thị để `pywinauto` focus.


### Các Nhiệm vụ (Tasks)

- [x] Nhiệm vụ 0: Tạo mô-đun thiết bị `src/device.py`
  - API: `connect_device(serial: Optional[str]) -> Device`
  - Logic: nếu `serial` rỗng → autodiscovery từ `adb devices` khi chỉ có 1 thiết bị; gọi `healthcheck()`; retry tối đa 3 lần với backoff khi lỗi connect.

- [x] Nhiệm vụ 1: Thiết lập cấu trúc dự án và biến cấu hình ENV/.env.
  - File: `main.py`, `requirements.txt`, `data/titles.txt`
  - Hành động: Bỏ CLI `argparse`, đọc cấu hình qua ENV/.env (`python-dotenv`). Setup log (file UTF-8 + console UTF-8). Thêm `uiautomator2`, `gdown`, `python-dotenv`, `pywinauto` vào `requirements.txt`.
- [x] Nhiệm vụ 2: Lập trình xử lý đồng bộ Google Drive.
  - File: `src/drive_sync.py`
  - Hành động: Viết hàm `download_and_filter(drive_url: str, temp_dir: str)`. Dùng gdown lấy nội dung folder. Xóa mọi thư mục/file không phải đuôi ảnh và trả về **mảng chứa Absolute Path của đúng ảnh**.
- [x] Nhiệm vụ 3: Thiết lập SQLite chống trùng lặp & Băm File.
  - File: `src/db_manager.py`
  - Hành động: Băm file ảnh thành chuỗi SHA-256. Mở kết nối SQLite lưu bảng `uploaded_history(hash_id PRIMARY KEY, uploaded_at)`. Hàm `is_uploaded()` và `mark_success()`. Đảm bảo an toàn I/O.
- [x] Nhiệm vụ 4: Kịch bản YouTube UI cứng cáp (uiautomator2 legacy) và backend LDPlayer Macro hotkey (Ctrl+F5).
  - Quy trình cập nhật: Create (+) → Create a Short → chọn image Recent → Next → chọn thời lượng (target ~5s) → Done → chọn nhạc Trending → Next → đặt tiêu đề → Lưu nháp (Save draft).
  - File: `src/android_auto.py`
  - Hành động: Sáng tạo bộ máy tương tác UI. Khởi động app YouTube. Cài đặt thao tác `try..except` kiểm tra pop-up cập nhật/ads (đóng nó lại). Tạo Short -> Chọn thư viện -> Ấn "Tiếp" -> Mặc định chọn một bài nhạc bất kỳ từ danh sách "Thịnh hành" -> Chọn Text ngẫu nhiên từ `data/titles.txt`. Bấm "Tải Short Lên". Kiểm chứng trạng thái Upload qua thanh thông báo (Toast) thành công.
- [x] Nhiệm vụ 5: Khớp nối Vòng lặp (Control Loop) & Dọn Dẹp (Garbage Collection).
  - File: `main.py`
  - Hành động: Chốt tiến trình (Workflow flow): Lấy ảnh -> Tính Hash -> Lọc DB -> Gọi Android Upload -> Báo log/Lưu DB -> **Xóa ảnh khỏi ổ cứng (`os.remove()`)** để nhường chỗ (Dọn rác). Tiếp tục ở ảnh tiếp theo.

### Tiêu chí Nghiệm thu (Acceptance Criteria)

- [x] AC 1: (Given) Cho một thư mục Drive gồm 4 ảnh và 1 file PDF rác, (When) khi chạy tool, (Then) công cụ chỉ tải về nguyên xi 4 ảnh và bỏ qua được file kia ở phân vùng `/temp`.
- [x] AC 2: (Given) Nạp vào 4 ảnh (đã up 2 ảnh vào DB SQLite bằng Hashes), (When) vòng điều hướng chính kích hoạt, (Then) Tool ngó lơ 2 file trùng dẫu tên có khác và chỉ đẩy lên 2 ảnh gốc mới toanh hoàn toàn.
- [x] AC 3: (Given) LDPlayer emulator đã bật ADB, (When) thực thi `connect_device()` và `app_start("com.google.android.youtube")`, (Then) YouTube mở thành công ≤ 15s, log hiển thị trạng thái kết nối ổn định.
- [x] AC 4: (Given) Sau khi nhấn Tải lên (Upload Short), (When) tiến trình Youtube đang tải video (~5s), (Then) kịch bản CHỜ trạng thái thông báo tải thành công rồi mới ghi "Uploaded Success" vào DB & xóa file ảnh tạm. Nếu time‑out > 60s, không được đánh dấu thành công.
- [ ] AC 5: (Robustness) Nếu mất kết nối ADB trong phiên, hệ thống tự retry reconnect tối đa N lần (ví dụ 3) trước khi bỏ qua ảnh hiện tại mà không ghi vào DB.
- [x] AC 6: Cấu hình chạy bằng ENV/.env (không còn CLI override): `ADB_SERIAL`, `DRIVE_URL`/`LOCAL_DIR`, `MAX_FILES`, `UPLOAD_BACKEND`, `LD_WINDOW_TITLE`, `LD_MACRO_TIMEOUT`, `DRY_RUN`, `TARGET_SECONDS`.

## Thông tin bổ sung (Additional Context)

### Phụ thuộc (Dependencies)
- Python 3.9+
- Thư viện: `uiautomator2`, `gdown`, `sqlite3`, `pytest`, `python-dotenv`, `pywinauto`.
- LDPlayer trên Windows; ADB_SERIAL thường là `127.0.0.1:5555` (tuỳ cấu hình).

### Chiến lược Test thử nghiệm (Testing Strategy)
- Thử nghiệm trên Channel (Kênh) Youtube nháp/trắng ở lần đầu tích hợp mạch luân phiên End-to-End.
- `pytest` cho unit tests (đặc biệt phần trigger hotkey LDPlayer với monkeypatch/mocking).
- Với backend `uiauto`: có `DRY_RUN=true` để chạy luồng mà không bấm Upload cuối.
- Với backend `ld-macro`: không hỗ trợ dry-run (vì macro là black-box).

### Chú ý (Notes)
- Giao diện của YouTube thỉnh thoảng cập nhật các text trên Label, Kỹ thuật viên (Code Agent) CẦN cố gắng sử dụng nhận diện UI có độ chịu lỗi (tolerance) bằng XPath cấu trúc lớn thay vì text cứng ở nút.
