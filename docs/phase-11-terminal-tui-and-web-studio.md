# Phase 11: Hybrid UI/UX — Terminal TUI & Local Web Studio Dashboard

## 🎯 Mục Tiêu
Nâng cấp trải nghiệm tương tác (UI/UX) khi nhận kết quả từ AI theo mô hình Hybrid (Cả Hai):
1. **Terminal TUI (Text User Interface)**: Hiển thị hộp khung viền tròn (Rounded Box), bảng điều khiển màu sắc sống động, render Markdown có phân tách khối mã (Syntax Highlight), và banner cảnh báo cứu hộ khẩn cấp rực rỡ (`Active-Survivor Failover Alert`).
2. **Local Web Studio Dashboard (`web/`)**:
   - Giao diện Web SPA hiện đại chuẩn Dark Mode & Glassmorphism tại `http://localhost:8000`.
   - **Sơ đồ luồng 3 chặng tương tác trực quan**: `[ĐẦU]` ➔ `[THÂN]` ➔ `[CUỐI]` ➔ `[Final Answer]`.
   - **Tự động phục hồi trực quan**: Khi 1 chặng chết (429/400/503), node chớp đỏ và hiện mũi tên cứu hộ vàng rực khi AI còn sống nhảy vào thay thế.
   - **Markdown & Code Highlighting**: Render định dạng, copy code 1 chạm.
   - **Tùy biến chặng**: Modal click chuột đổi Provider/Model tức thì.
   - **Zero-Dependency**: Chạy thuần Python standard library `http.server`, không cần cài thêm npm/pip!

---

## 🏗️ Cấu Trúc Thành Phần

```text
d:\my_ai\
├── ui/
│   ├── __init__.py
│   └── tui.py               # Bộ engine render Terminal TUI (Colors, box, markdown, alerts)
├── web/
│   ├── __init__.py
│   ├── server.py            # Zero-dependency Threading HTTP Server & REST API
│   └── static/
│       ├── index.html       # Single Page Application Dashboard
│       ├── app.css          # Glassmorphism Dark Mode Design System
│       └── app.js           # Client Logic, Pipeline Runner, Markdown Renderer
├── test_web_server.py       # Script kiểm thử tự động Web Studio Server
└── main.py                  # Tích hợp cờ --web và tùy chọn menu 6
```

---

## 🚀 Cách Sử Dụng

### 1. Trải nghiệm Terminal TUI
Khởi động menu chính và chọn mục **5**:
```powershell
python main.py
# Nhập 5
```
Giao diện Terminal sẽ hiển thị khung viền tròn bo góc, thanh tiến trình màu sắc và banner cứu hộ rực rỡ khi có AI gặp sự cố.

### 2. Trải nghiệm Web Studio Dashboard trên trình duyệt
- **Cách 1**: Khởi động trực tiếp bằng cờ `--web`:
  ```powershell
  python main.py --web
  ```
- **Cách 2**: Khởi động `python main.py` và chọn mục **`6. 🌐 Mở Web UI Studio Dashboard`**.
- Trình duyệt sẽ tự động mở trang: **`http://localhost:8000`**.
