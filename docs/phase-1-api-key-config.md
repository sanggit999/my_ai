# Phase 1: API Key & Configuration Management

## 1. Mục tiêu (Objective)
Xây dựng hệ thống quản lý cấu hình tập trung và nạp API Key an toàn cho nhiều nhà cung cấp AI (Multi-Provider: OpenAI, Google Gemini, Anthropic Claude). Hệ thống cần hỗ trợ nạp từ biến môi trường (`.env` hoặc hệ thống), kiểm tra tính hợp lệ sơ bộ, và xác định được provider nào đang khả dụng (ready).

---

## 2. Các Provider & Biến môi trường tương ứng

| Provider | Tên biến môi trường tiêu chuẩn | Link lấy API Key | Ghi chú SDK mặc định |
| :--- | :--- | :--- | :--- |
| **OpenAI** | `OPENAI_API_KEY` | [OpenAI API Keys](https://platform.openai.com/api-keys) | Tự động đọc `OPENAI_API_KEY` |
| **Google Gemini** | `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) | SDK `google-genai` ưu tiên `GEMINI_API_KEY` |
| **Anthropic** | `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/settings/keys) | SDK `anthropic` tự động đọc `ANTHROPIC_API_KEY` |

> [!NOTE]
> Có thể hỗ trợ thêm các biến tùy chọn như `OPENAI_BASE_URL`, `ANTHROPIC_BASE_URL` khi người dùng dùng qua proxy hoặc dịch vụ tương thích.

---

## 3. Kiến trúc Config Module đề xuất

### 3.1 Cấu trúc thư mục (Folder riêng cho từng Provider / API Key)
```text
D:\my_ai/
├── .env.example              # Mẫu khai báo biến môi trường
├── .env                      # Chứa API Key thực tế (KHÔNG commit vào git)
├── .gitignore                # Bỏ qua .env, cache, venv
├── requirements.txt          # Các thư viện phụ thuộc
├── config/
│   ├── __init__.py
│   └── env_loader.py         # Nạp file .env thông minh (tự động fallback stdlib)
├── providers/
│   ├── __init__.py           # Tập hợp và kiểm tra toàn bộ provider
│   ├── base.py               # BaseConfig & BaseProvider interface chuẩn
│   ├── openai/               # Thư mục riêng cho OpenAI
│   │   ├── __init__.py
│   │   └── config.py         # OpenAIConfig (OPENAI_API_KEY, base_url, org)
│   ├── gemini/               # Thư mục riêng cho Google Gemini
│   │   ├── __init__.py
│   │   └── config.py         # GeminiConfig (GEMINI_API_KEY, GOOGLE_API_KEY)
│   └── anthropic/            # Thư mục riêng cho Anthropic Claude
│       ├── __init__.py
│       └── config.py         # AnthropicConfig (ANTHROPIC_API_KEY, base_url)
├── main.py                   # Entrypoint kiểm tra trạng thái Phase 1
└── docs/                     # Tài liệu thiết kế các Phase
```

### 3.2 File mẫu `.env.example`
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...

# Google Gemini Configuration
GEMINI_API_KEY=AIzaSy...

# Anthropic Claude Configuration
ANTHROPIC_API_KEY=sk-ant-...

# General App Settings (Tùy chọn)
DEFAULT_PROVIDER=gemini
APP_TIMEOUT_SECONDS=30
```

---

## 4. Thiết kế mã nguồn (Reference Implementation)

Sử dụng thư viện `python-dotenv` hoặc `pydantic-settings` để quản lý config.

```python
# config.py
import os
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv

# Tự động nạp file .env từ thư mục gốc
load_dotenv()

@dataclass(frozen=True)
class ProviderCredentials:
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

class AppConfig:
    def __init__(self):
        self.credentials = ProviderCredentials(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
        self.timeout = int(os.getenv("APP_TIMEOUT_SECONDS", "30"))

    def get_available_providers(self) -> List[str]:
        """Trả về danh sách các provider có API Key hợp lệ được thiết lập."""
        available = []
        if self.credentials.openai_api_key:
            available.append("openai")
        if self.credentials.gemini_api_key:
            available.append("gemini")
        if self.credentials.anthropic_api_key:
            available.append("anthropic")
        return available

    def is_provider_configured(self, provider_name: str) -> bool:
        return provider_name.lower() in self.get_available_providers()

    @staticmethod
    def mask_key(key: Optional[str]) -> str:
        """Che bớt ký tự API key khi log ra màn hình để bảo mật."""
        if not key:
            return "<Chưa cấu hình>"
        if len(key) <= 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"

    def print_status(self):
        """Hiển thị trạng thái các Provider trên CLI."""
        print("=== Multi-AI Provider Config Status ===")
        print(f"- OpenAI:    {self.mask_key(self.credentials.openai_api_key)}")
        print(f"- Gemini:    {self.mask_key(self.credentials.gemini_api_key)}")
        print(f"- Anthropic: {self.mask_key(self.credentials.anthropic_api_key)}")
        print(f"Các Provider sẵn sàng: {', '.join(self.get_available_providers()) or 'Chưa có'}")
```

---

## 5. Xử lý lỗi & Bảo mật (Error Handling & Security)

1. **Không log toàn bộ API Key**: Luôn sử dụng hàm che giấu (`mask_key`) hiển thị 4 ký tự đầu và 4 ký tự cuối.
2. **Gitignore**: Đảm bảo file `.gitignore` chứa `.env` và `*.env.local` ngay từ đầu:
   ```gitignore
   .env
   .env.*
   !*.example
   ```
3. **Graceful Degradation**: Nếu người dùng chỉ có key của Gemini, chương trình vẫn chạy bình thường với Gemini mà không báo lỗi crash hệ thống đối với OpenAI hoặc Claude.
4. **Validation sớm**: Khi người dùng chọn provider nào, kiểm tra ngay key của provider đó trước khi thực hiện cuộc gọi mạng.

---

## 6. Tiêu chí hoàn thành (Definition of Done)
- [ ] File `.env.example` được tạo với đầy đủ hướng dẫn comment.
- [ ] Module `config.py` đọc thành công biến môi trường từ cả `.env` lẫn environment của OS.
- [ ] Hàm `get_available_providers()` trả về đúng danh sách các provider đã nhập key.
- [ ] Báo lỗi rõ ràng kèm hướng dẫn khi người dùng cố gọi một provider chưa được cấu hình key.
- [ ] Đảm bảo `.env` nằm trong `.gitignore`.
