# Multi-AI Python Tool — Project Documentation

Hệ thống tài liệu thiết kế và lộ trình phát triển cho **Multi-AI Python Tool** — công cụ dòng lệnh (CLI) và thư viện Python kết nối đa mô hình trí tuệ nhân tạo (OpenAI, Google Gemini, Anthropic Claude) theo kiến trúc đa hình (Polymorphic Provider Pattern) và lấy danh sách model động không hard-code.

---

## 1. Mục lục tài liệu theo từng Phase (Roadmap Docs)

| Phase | Tài liệu chi tiết | Trọng tâm chính |
| :---: | :--- | :--- |
| **Phase 1** | [Phase 1: API Key & Config](file:///D:/my_ai/docs/phase-1-api-key-config.md) | Quản lý biến môi trường, bảo mật key, kiểm tra provider sẵn sàng. |
| **Phase 2** | [Phase 2: list_models() Từng Provider](file:///D:/my_ai/docs/phase-2-list-models.md) | Gọi API lấy catalog model động từ OpenAI, Gemini, Anthropic. |
| **Phase 3** | [Phase 3: Chuẩn Hóa ModelInfo](file:///D:/my_ai/docs/phase-3-model-info.md) | Thống nhất dữ liệu model metadata qua Data Model chung `ModelInfo`. |
| **Phase 4** | [Phase 4: CLI Chọn Provider -> Model](file:///D:/my_ai/docs/phase-4-cli-selection.md) | Giao diện terminal tương tác, menu chọn lọc & fuzzy search. |
| **Phase 5** | [Phase 5: Chat / Generate Engine](file:///D:/my_ai/docs/phase-5-chat-generate.md) | Sinh phản hồi đồng bộ và streaming qua đa hình `generate()`. |
| **Phase 6** | [Phase 6: Unified Response](file:///D:/my_ai/docs/phase-6-unified-response.md) | Chuẩn hóa kết quả trả về, thống kê Token Usage & Latency. |
| **Phase 7** | [Phase 7: Chat History & Session](file:///D:/my_ai/docs/phase-7-chat-history.md) | Hội thoại nhiều lượt, cắt tỉa context window, lưu trữ session JSON. |
| **Phase 8** | [Phase 8: AI Orchestrator](file:///D:/my_ai/docs/phase-8-ai-orchestrator.md) | Bộ điều phối trung tâm: Song song (Arena), Tự động dự phòng (Failover), Định tuyến. |
| **Phase 9** | [Phase 9: Role Assignment & Personas](file:///D:/my_ai/docs/phase-9-role-assignment-personas.md) | Phân vai chuyên môn (Hội đồng chuyên gia, Cấu hình con nào làm việc gì, Dây chuyền tuần tự). |
| **Phase 9.1** | [Phase 9.1: Per-API Model Switcher](file:///D:/my_ai/docs/phase-9-1-model-switcher.md) | Quản lý & chuyển đổi model đang hoạt động độc lập cho từng API (Groq, Gemini, OpenAI, Claude). |
| **Phase 10** | [Phase 10: 3-Stage Pipeline (Đầu - Thân - Cuối)](file:///D:/my_ai/docs/phase-10-three-stage-pipeline.md) | Thiết lập cấu hình cố định/linh hoạt: Con ĐẦU lập dàn ý, Con THÂN triển khai, Con CUỐI trau chuốt (Active-Survivor Failover). |
| **Phase 11** | [Phase 11: Hybrid UI/UX (Terminal TUI & Web Studio)](file:///D:/my_ai/docs/phase-11-terminal-tui-and-web-studio.md) | Trải nghiệm giao diện đa nền tảng: Terminal TUI bo tròn màu sắc & Local Web Studio Dashboard (SPA Glassmorphism). |

---

## 2. Tài liệu tham khảo chính thức (Official References)

### OpenAI
- **Models Catalog**: [https://platform.openai.com/docs/models](https://platform.openai.com/docs/models)
- **Models API Reference**: [https://platform.openai.com/docs/api-reference/models](https://platform.openai.com/docs/api-reference/models)
- **Core SDK Concept**: `client.models.list()`, `client.chat.completions.create()`

### Google Gemini
- **Models Guide**: [https://ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models)
- **Models API Reference**: [https://ai.google.dev/api/models](https://ai.google.dev/api/models)
- **REST Endpoint**: `GET https://generativelanguage.googleapis.com/v1beta/models`
- **Core SDK Concept**: `client.models.list()`, `client.models.generate_content()`

### Anthropic Claude
- **API Documentation**: [https://docs.anthropic.com/en/api](https://docs.anthropic.com/en/api)
- **Models Overview**: [https://docs.anthropic.com/en/docs/about-claude/models/overview](https://docs.anthropic.com/en/docs/about-claude/models/overview)
- **Models API Reference**: [https://docs.anthropic.com/en/api/models-list](https://docs.anthropic.com/en/api/models-list)
- **Core SDK Concept**: `client.models.list()`, `client.messages.create()`

---

## 3. Kiến trúc tổng thể (Architecture)

### Triết lý cốt lõi:
1. **Dynamic Model Discovery**: Tuyệt đối không hard-code danh sách model nếu nhà cung cấp có API lấy danh mục.
2. **Provider Polymorphism**: Mọi Provider kế thừa từ `BaseProvider`, triển khai 2 phương thức cốt lõi:
   - `provider.get_models() -> List[ModelInfo]`
   - `provider.generate(model, messages, ...) -> UnifiedResponse`
3. **Decoupled Architecture**: Tầng giao diện CLI và chat engine chỉ tương tác thông qua các model chuẩn hóa (`ModelInfo`, `UnifiedResponse`, `ChatMessage`), tách biệt hoàn toàn với SDK riêng lẻ của từng nhà cung cấp.
