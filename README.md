# Multi-AI Python CLI & Unified Multi-Provider SDK

Hệ thống AI CLI và thư viện Python chuyên nghiệp kết nối tới 4 nền tảng AI hàng đầu (**OpenAI**, **Groq LPU**, **Google Gemini**, **Anthropic Claude**) với khả năng tự động khám phá danh mục model (Dynamic Model Discovery), phản hồi streaming thời gian thực, chuẩn hóa dữ liệu thống nhất và lưu trữ phiên hội thoại đa lượt.

---

## 🌟 Tính năng nổi bật theo từng Phase

1. **Phase 1: Quản lý Cấu hình & API Key riêng biệt** (`providers/`, `config/`)
   - Mỗi provider có thư mục độc lập (`providers/openai`, `providers/groq`, `providers/gemini`, `providers/anthropic`).
   - Tự động nạp file `.env`, che dấu key an toàn khi hiển thị (`sk-...ZRgA`), zero-dependency fallback (chạy không cần cài thêm pip).
2. **Phase 2: Khám phá Catalog Model Động** (`list_models()`)
   - Không hardcode danh sách model. Tự động lấy trực tiếp từ API của từng hãng.
   - Hỗ trợ bảng giới hạn Free Plan (RPM, RPD, TPM, TPD) cho Groq.
3. **Phase 3: Chuẩn hóa ModelInfo Schema** (`models/model_info.py`)
   - Chuẩn hóa hơn 149 model thành cùng một định dạng: Context window, Output token limit, Capabilities (chat, vision, reasoning), Rate limits.
4. **Phase 4: Menu Điều Hướng & Tìm Kiếm Model** (`cli/selector.py`)
   - Tương tác chọn Provider -> Model với hỗ trợ tìm kiếm `/filter <từ khóa>` hoặc fuzzy search (hỗ trợ cả questionary và console chuẩn).
5. **Phase 5: Sinh phản hồi Streaming thời gian thực** (`generate_stream()`)
   - Hỗ trợ Server-Sent Events (SSE) streaming mượt mà từng chunk văn bản ra màn hình.
6. **Phase 6: Phản hồi chuẩn hóa UnifiedResponse** (`models/unified_response.py`)
   - Đo lường chính xác thời gian thực thi (Latency tính bằng ms) và thống kê số lượng Token tiêu thụ (Input, Output, Total).
7. **Phase 7: Quản lý Hội thoại Đa Lượt & Lưu Phiên** (`models/chat.py`, `session/storage.py`)
   - Tự động cắt tỉa ngữ cảnh cũ (Sliding Window context pruning).
   - Lưu và tải lại phiên hội thoại dưới dạng file JSON trong thư mục `.sessions/`.
8. **Phase 8: Multi-Model Orchestration & Synthesis** (`orchestrator/`, `cli/orchestrator_view.py`)
   - Mô hình điều phối song song (Concurrent Fan-out) tới OpenAI, Claude, Gemini, Groq.
   - AI Synthesizer (Meta-Judge) phân tích, đối chiếu và tổng hợp thành **Final Answer** toàn diện, khách quan và chính xác nhất.
9. **Phase 9: Multi-Persona Role Assignment & Sequential Pipeline** (`orchestrator/personas.py`, `cli/role_orchestrator_view.py`)
   - **Hội đồng Chuyên gia (Council of Experts)**: Phân vai chuyên môn (Kỹ thuật, An ninh mạng, Phân tích kinh doanh) và tổng hợp thành Bản kế hoạch chiến lược cấp cao (Executive Plan).
   - **Dây chuyền Tuần tự (Sequential Pipeline Chain)**: Quy trình chuyền tay tự động (Planner ➔ Coder ➔ Reviewer/Auditor).
10. **Phase 9.1: Per-API Model Switcher** (`config/active_models.py`, `cli/model_switcher.py`)
   - Cho phép người dùng chuyển đổi (switch) model đang hoạt động độc lập cho từng API (Groq, Gemini, OpenAI, Claude).
   - Tự động lưu vào `config/active_models.json` và đồng bộ tức thì sang toàn bộ hệ thống (Single Chat, Orchestrator, Hội đồng chuyên gia).
11. **Phase 10: Dây chuyền 3 chặng ĐẦU ➔ THÂN ➔ CUỐI Tự Phục Hồi (Active-Survivor Failover)** (`orchestrator/pipeline_engine.py`, `cli/pipeline_view.py`)
   - **Mô hình dây chuyền khép kín**: ĐẦU (Kiến trúc & Dàn ý) ➔ THÂN (Triển khai code & nội dung cốt lõi) ➔ CUỐI (Kiểm toán bảo mật, tối ưu & trau chuốt).
   - **Cơ chế "Con nào chết thì con còn sống nhảy vào gánh"**: Bắt lỗi độc lập từng chặng (429 Hết quota, 400 Hết tiền credit, 503 Server quá tải, timeout). Tự động điều động các AI còn sống (Groq, Gemini,...) tiếp quản ngay tức khắc mà không làm gián đoạn dây chuyền.
   - **Tùy biến linh hoạt**: Lệnh `/setup` cho phép cấu hình model cho từng chặng và lưu cấu hình vĩnh viễn trong `config/pipeline_stages.json`. Lệnh `/view` giúp soi chi tiết kết quả từng chặng.
12. **Phase 11: Hybrid UI/UX — Terminal TUI & Local Web Studio Dashboard** (`ui/tui.py`, `web/`)
   - **Terminal TUI**: Khung hộp bo góc viền kép, gradient màu sắc, render Markdown có chia khối mã nguồn (Syntax Highlighting) và banner cảnh báo cứu hộ khẩn cấp rực rỡ.
   - **Local Web Studio Dashboard (`web/`)**: Giao diện SPA Dark Mode Glassmorphism hiện đại tại `http://localhost:8000`, sơ đồ tương tác luồng 3 chặng trực quan, tự động mở trình duyệt qua cờ `python main.py --web` hoặc menu phím 6. Chạy zero-dependency thuần thư viện chuẩn Python!

---

## 📁 Cấu trúc Thư mục Dự án

```text
D:\my_ai\
├── .env                       # File cấu hình API Keys cá nhân
├── .env.example               # Mẫu hướng dẫn điền API Keys
├── .sessions/                 # Thư mục lưu trữ lịch sử các phiên chat JSON (Phase 7)
├── cli/
│   ├── chat_loop.py           # REPL tương tác hội thoại đa lượt + streaming (Phases 4-7)
│   ├── model_switcher.py      # Trình quản lý & đổi model cho từng API (Phase 9.1)
│   ├── orchestrator_view.py   # Giao diện tương tác Multi-Model Synthesis (Phase 8)
│   ├── pipeline_view.py       # Giao diện Dây chuyền 3 chặng ĐẦU - THÂN - CUỐI Tự Phục Hồi (Phase 10)
│   ├── role_orchestrator_view.py # Giao diện Hội đồng Chuyên gia & Pipeline (Phase 9)
│   └── selector.py            # Menu điều hướng chọn Provider & Model (Phase 4)
├── config/
│   ├── active_models.py       # Quản lý & lưu trữ model đang dùng cho từng API (Phase 9.1)
│   ├── active_models.json     # Cấu hình model đang chọn lưu vĩnh viễn
│   ├── pipeline_stages.py     # Quản lý cấu hình 3 chặng ĐẦU - THÂN - CUỐI (Phase 10)
│   ├── pipeline_stages.json   # Lưu trữ thiết lập ĐẦU, THÂN, CUỐI vĩnh viễn
│   └── env_loader.py          # Bộ nạp biến môi trường thông minh chuẩn stdlib
├── docs/                      # Tài liệu kỹ thuật chi tiết từng Phase 1 -> 10
├── models/
│   ├── chat.py                # ChatMessage & ChatSession (Phase 7)
│   ├── model_info.py          # ModelInfo schema chuẩn hóa (Phase 3)
│   └── unified_response.py    # UnifiedResponse & TokenUsage (Phase 6)
├── orchestrator/              # Bộ điều phối trung tâm & AI Synthesis (Phases 8, 9 & 10)
│   ├── engine.py              # AIOrchestrator (Broadcast, Synthesis, Roles, Pipeline)
│   ├── models.py              # ProviderExecutionResult, SynthesizerResult, RoleAssignment, PipelineStep
│   ├── personas.py            # Built-in personas (Tech Lead, Security, Business, Devil's Advocate)
│   └── pipeline_engine.py     # ThreeStagePipeline với Active-Survivor Failover (Phase 10)
├── providers/
│   ├── anthropic/             # Provider Anthropic Claude
│   ├── gemini/                # Provider Google Gemini
│   ├── groq/                  # Provider Groq (OpenAI-compatible siêu tốc)
│   ├── openai/                # Provider OpenAI Official
│   ├── base.py                # BaseConfig & BaseProvider abstract interfaces
│   └── __init__.py            # Provider registry & dynamic factory
├── session/
│   └── storage.py             # Session JSON persistence (Phase 7)
├── main.py                    # Menu bảng điều khiển chính
├── test_model_info.py         # Kiểm thử chuẩn hóa ModelInfo (Phase 3)
├── test_phases_4_to_7.py      # Kiểm thử toàn diện tích hợp Phases 4, 5, 6, 7
├── test_orchestration_synthesis.py # Kiểm thử Multi-Model Synthesis (Phase 8)
├── test_phase_9_roles.py      # Kiểm thử Hội đồng Chuyên gia & Dây chuyền tuần tự (Phase 9)
├── test_phase_9_1_model_switcher.py # Kiểm thử Switch Model từng API (Phase 9.1)
└── test_phase_10_resilient_pipeline.py # Kiểm thử Dây chuyền 3 chặng Tự Phục Hồi (Phase 10)
```




---

## 📖 Hướng Dẫn Sử Dụng Chi Tiết (Tutorial A - Z)

### 1. Khởi động nhanh (Quick Start)

#### Bước 1: Chuẩn bị môi trường
- Yêu cầu **Python 3.10+** (đã tích hợp sẵn bộ thư viện chuẩn `urllib`, `json`, `dataclasses`, `concurrent.futures`).
- **Zero-Dependency**: Bạn có thể chạy hệ thống ngay lập tức mà **không cần `pip install`** bất kỳ thư viện bên ngoài nào!

#### Bước 2: Thiết lập API Keys
Hệ thống hỗ trợ 4 nhà cung cấp AI. Bạn chỉ cần ít nhất 1 key (khuyến nghị **Groq** hoặc **Gemini** miễn phí) là có thể sử dụng:
- Cách 1: Tạo/chỉnh sửa file `.env` tại thư mục gốc `D:\my_ai\.env`:
  ```env
  GROQ_API_KEY=gsk_...
  GEMINI_API_KEY=AIzaSy...
  OPENAI_API_KEY=sk-...
  ANTHROPIC_API_KEY=sk-ant-...
  ```
- Cách 2: Nhập trực tiếp từ giao diện bảng điều khiển: Khởi động chương trình và chọn mục **`8. 🔑 Nhập / Cập nhật API Key trực tiếp`**.

#### Bước 3: Khởi chạy bảng điều khiển
```powershell
cd D:\my_ai
python main.py
```

---

### 2. Hướng dẫn chi tiết từng chế độ hoạt động

```text
============================================================
          BẢNG ĐIỀU KHIỂN CHÍNH (MAIN MENU)
============================================================
  1. 🚀 Chat Đơn Lẻ với 1 Model (Phases 4, 5, 6, 7)
  2. 🧠 Multi-Model Orchestration & Synthesis (Phase 8)
  3. 🎭 Multi-Persona Role Orchestration & Pipeline (Phase 9)
  4. 🔄 Quản Lý & Chuyển Đổi Model Cho Từng API (Phase 9.1)
  5. ⛓️ Dây Chuyền 3 Chặng ĐẦU ➔ THÂN ➔ CUỐI (Tự Phục Hồi - Phase 10)
  6. 📋 So sánh Model Catalog chuẩn hóa (Phase 3)
  7. 🔍 Kiểm tra trạng thái các Provider & Keys (Phase 1)
  8. 🔑 Nhập / Cập nhật API Key trực tiếp
  9. ⚡ Test Groq Models & Chat (OpenAI-compatible / Free)
 10. 🌟 Test Google Gemini Models & Chat
 11. 🧠 Test OpenAI Official Models
 12. 🎭 Test Anthropic Claude Models
  0. 🚪 Thoát
============================================================
```

---

#### 🌟 Chế độ 5: Dây Chuyền 3 Chặng ĐẦU ➔ THÂN ➔ CUỐI (Tự Phục Hồi - Phase 10)
> **Khuyên dùng nhất**: Đây là chế độ mạnh mẽ nhất, giải quyết trọn vẹn bài toán model bị lỗi/hết tiền giữa chừng.

1. **Nguyên lý hoạt động**:
   - **Chặng 1: ĐẦU (Architect & Planner)**: Bóc tách yêu cầu, lập dàn ý kỹ thuật và đề cương kiến trúc.
   - **Chặng 2: THÂN (Core Implementer)**: Nhận dàn ý từ ĐẦU, triển khai mã nguồn hoặc nội dung chuyên sâu hoàn chỉnh.
   - **Chặng 3: CUỐI (Auditor & Polisher)**: Nhận bản thảo từ THÂN, kiểm toán rà soát lỗi bảo mật, tối ưu hiệu năng và trau chuốt xuất bản phiên bản đỉnh cao.
   - **🛡️ Cơ chế Tự Phục Hồi (Active-Survivor Failover)**:
     Nếu bất kỳ chặng nào gặp sự cố (ví dụ OpenAI hết tiền `429 Quota`, Groq quá tải `503`, hoặc hết credit `400`), **AI còn sống (Groq, Gemini,...) sẽ lập tức nhảy vào gánh chặng đó**, đảm bảo dây chuyền không bao giờ bị đứt đoạn.

2. **Cách thao tác**:
   - Nhập `5` từ menu chính để vào phòng điều khiển dây chuyền.
   - **Gõ câu hỏi/prompt bình thường**: Dây chuyền sẽ tự động kích hoạt tuần tự 3 chặng và in tiến độ thời gian thực với định dạng khung bo góc TUI và màu sắc chuẩn.
   - **Các lệnh điều khiển đặc biệt**:
     - `/setup` : Tùy chỉnh con nào làm ĐẦU, THÂN, CUỐI. Cấu hình sẽ tự lưu vĩnh viễn vào `config/pipeline_stages.json`.
     - `/view`  : Soi chi tiết từng chặng (xem đề cương của ĐẦU, code của THÂN, thẩm định của CUỐI).
     - `/reset` : Khôi phục cài đặt 3 chặng về mặc định ban đầu.
     - `/exit`  : Quay trở lại Menu chính.

---

#### 🌐 Chế độ 6: Mở Web UI Studio Dashboard (Trình duyệt - Phase 11)
> **Trải nghiệm trực quan đỉnh cao**: Mở giao diện Single Page Application (SPA) trên trình duyệt web, theo dõi sơ đồ luồng thời gian thực.

1. **Cách khởi động**:
   - **Cách 1 (Nhanh nhất)**: Gõ `python main.py --web` trong terminal.
   - **Cách 2**: Chạy `python main.py` và chọn phím **`6`**.
   - Trình duyệt mặc định sẽ tự động mở trang: **`http://localhost:8000`**.
2. **Tính năng độc quyền trên Web Studio**:
   - **Sơ đồ luồng tương tác (Interactive Flow Nodes)**: Hiển thị trực quan 3 chặng ĐẦU ➔ THÂN ➔ CUỐI. Khi đang chạy, node sẽ phát sáng (pulse); khi có lỗi, node chớp đỏ và kích hoạt mũi tên cứu hộ vàng rực khi AI còn sống nhảy vào gánh.
   - **Render Markdown & Code Highlighting**: Hỗ trợ copy code 1-chạm, đọc bảng biểu, danh sách chuyên nghiệp.
   - **Tabs Soi Chi Tiết**: Chuyển đổi linh hoạt giữa *Final Synthesized Answer*, *Chặng 1 (ĐẦU)*, *Chặng 2 (THÂN)*, *Chặng 3 (CUỐI)* và *Nhật ký cứu hộ (Events Table)*.
   - **Đổi Model 1-Click**: Click chuột vào từng node trên sơ đồ để mở modal cấu hình đổi AI ngay trên web mà không cần gõ lệnh CLI.

---

#### 🔄 Chế độ 4: Quản Lý & Chuyển Đổi Model Cho Từng API (Per-API Switcher - Phase 9.1)
Cho phép bạn linh hoạt thay đổi model active mặc định của từng hãng:
1. Nhập `4` từ menu chính.
2. Màn hình sẽ hiển thị model đang được chọn của 4 API:
   - `GROQ` ➔ `openai/gpt-oss-120b`
   - `GEMINI` ➔ `gemini-3.1-flash-lite`
   - `OPENAI` ➔ `gpt-4o-mini`
   - `ANTHROPIC` ➔ `claude-3-5-haiku-20241022`
3. Nhập số tương ứng với API muốn đổi (ví dụ `1` để đổi model Groq).
4. Hệ thống tải trực tiếp danh sách model khả dụng từ server API và cho phép bạn chọn hoặc lọc theo từ khóa (`/filter qwen`, `/filter gpt`).
5. Lựa chọn được lưu tự động vào `config/active_models.json` và đồng bộ tức thì sang toàn bộ hệ thống.

---

#### 🧠 Chế độ 2: Tổng Hợp Đa Mô Hình (Multi-Model Synthesis - Phase 8)
1. Nhập `2` từ menu chính.
2. Gõ một câu hỏi phức tạp (ví dụ: *"So sánh kiến trúc Microservices và Monolithic, khi nào nên dùng?"*).
3. Hệ thống sẽ:
   - **Broadcast song song**: Gửi câu hỏi đồng thời tới tất cả các API đã cấu hình key.
   - **Thu thập phản hồi**: Đo lường chính xác độ trễ (latency ms) của từng con.
   - **Thẩm phán AI (Meta-Judge Synthesizer)**: Phân tích các góc nhìn, loại bỏ điểm sai lệch, tổng hợp thành một câu trả lời duy nhất sâu sắc và chuẩn xác nhất.

---

#### 🎭 Chế độ 3: Hội Đồng Chuyên Gia & Dây Chuyền Phân Vai (Phase 9)
1. Nhập `3` từ menu chính.
2. Chọn 1 trong 2 hình thức:
   - **Lựa chọn 1: Hội đồng Chuyên gia (Council of Experts)**:
     - AI 1 đóng vai **Kỹ Sư Trưởng (Tech Lead)**: Đánh giá kiến trúc, khả năng mở rộng.
     - AI 2 đóng vai **Chuyên Gia An Ninh (Security Auditor)**: Soi lỗ hổng bảo mật, rủi ro tuân thủ.
     - AI 3 đóng vai **Giám Đốc Chiến Lược (Business Strategist)**: Đánh giá chi phí, ROI và vận hành.
     - **Synthesizer** tổng hợp thành Bản Kế Hoạch Chiến Lược Cấp Cao (**Executive Plan**).
   - **Lựa chọn 2: Dây chuyền tuần tự (Sequential Pipeline Chain)**:
     - Planner lập dàn ý ➔ Coder viết mã nguồn ➔ Reviewer kiểm toán chất lượng.

---

#### 🚀 Chế độ 1: Chat Đơn Lẻ với 1 Model (Phases 4 - 7)
Trải nghiệm chat chuyên sâu với streaming từng chữ và lưu phiên:
1. Nhập `1` từ menu chính.
2. Chọn Provider (Groq, Gemini, OpenAI, Claude).
3. Chọn Model trong danh sách (hỗ trợ gõ `/filter <từ khóa>` để tìm nhanh).
4. Vào phòng chat trực tiếp với các lệnh tiện ích:
   - `/switch` hoặc `/model` : Đổi sang model khác ngay trong phiên mà không mất ngữ cảnh.
   - `/system <prompt>`     : Cập nhật System Prompt điều khiển phong cách AI.
   - `/history`             : Xem lại toàn bộ câu hỏi và trả lời từ đầu phiên.
   - `/clear`               : Xóa sạch bộ nhớ tạm của phiên hiện tại.
   - `/save [tên_file]`     : Lưu phiên trò chuyện thành file JSON vào `.sessions/`.
   - `/load`                : Tải lại một phiên trò chuyện cũ từ đĩa.
   - `/exit`                : Thoát phòng chat.

---

### 3. Danh mục Lệnh Kiểm Thử Tự Động (Automated Test Suite)

Tất cả các phase đều có script kiểm thử độc lập để bạn xác thực độ tin cậy của mã nguồn:

| File Kiểm Thử | Mục Tiêu Kiểm Thử | Lệnh Thực Thi |
| :--- | :--- | :--- |
| `test_web_server.py` | Kiểm thử khởi động và định tuyến Web Studio Server (Phase 11) | `python test_web_server.py` |
| `test_phase_10_resilient_pipeline.py` | Kiểm thử Dây chuyền 3 chặng & cơ chế **Con nào chết con sống nhảy vào gánh** | `python test_phase_10_resilient_pipeline.py` |
| `test_phase_9_1_model_switcher.py` | Kiểm thử Switch model từng API và tính bền bỉ lưu file JSON | `python test_phase_9_1_model_switcher.py` |
| `test_phase_9_roles.py` | Kiểm thử Hội đồng Chuyên gia và Dây chuyền phân vai | `python test_phase_9_roles.py` |
| `test_orchestration_synthesis.py` | Kiểm thử Fan-out song song và AI Meta-Judge Synthesis | `python test_orchestration_synthesis.py` |
| `test_phases_4_to_7.py` | Kiểm thử Selector, Streaming, UnifiedResponse, Sliding Window & Storage | `python test_phases_4_to_7.py` |
| `test_model_info.py` | Kiểm thử chuẩn hóa Schema ModelInfo từ 4 hãng | `python test_model_info.py` |

---

### 4. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

- **Lỗi `429 Too Many Requests / Quota Exceeded`**:
  - *Nguyên nhân*: Tài khoản OpenAI/Groq miễn phí bị chạm giới hạn lượt gọi trong phút hoặc hết tiền.
  - *Giải pháp*: Trong Phase 10, hệ thống **tự động phát hiện lỗi 429 và điều động AI khác còn sống nhảy vào gánh**. Ngoài ra bạn có thể vào menu `4` để chuyển sang model khác của Groq hoặc dùng Gemini miễn phí.
- **Lỗi `503 Service Unavailable`**:
  - *Nguyên nhân*: Model của nhà cung cấp đang bị quá tải tạm thời.
  - *Giải pháp*: Hệ thống sẽ tự động bắt lỗi và kích hoạt quy tắc Failover sang model dự phòng.
- **Lỗi Font Tiếng Việt trên Windows Command Prompt**:
  - Tất cả các script CLI đã được cấu hình tự động `sys.stdout.reconfigure(encoding="utf-8")`. Nếu chạy PowerShell cũ, bạn có thể gõ `chcp 65001` trước khi chạy.

