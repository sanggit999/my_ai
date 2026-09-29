# Phase 2: Dynamic list_models() Cho Từng Provider

## 1. Mục tiêu (Objective)
Thực hiện truy vấn danh sách models động từ API chính thức của từng provider (OpenAI, Google Gemini, Anthropic Claude) thay vì hard-code danh sách tĩnh. Điều này giúp công cụ luôn cập nhật các model mới nhất, tự động nhận diện model deprecated hoặc preview.

---

## 2. Tài liệu chính thức & Đặc tả API (Official Documentation)

### 2.1 OpenAI
- **Official Docs**: [OpenAI Models Guide](https://platform.openai.com/docs/models)
- **API Reference**: [OpenAI Models API](https://platform.openai.com/docs/api-reference/models)
- **Cơ chế**: Endpoint `GET /v1/models`
- **Python SDK**:
  ```python
  from openai import OpenAI
  client = OpenAI()
  response = client.models.list()
  # response.data là danh sách Model objects: id, created, owned_by
  ```
- **Lưu ý nghiệp vụ**:
  - Danh sách trả về chứa cả model embedding, audio, tts, image (DALL-E) và chat.
  - Cần bộ lọc (filter) để giữ lại các model chat thông dụng (ví dụ: các model có tiền tố `gpt-`, `o1-`, `o3-`, `chatgpt-`) hoặc phân loại theo capability.

### 2.1.1 Groq (OpenAI-Compatible 3rd-Party & Free Tier)
- **Official Docs**: [Groq API Documentation](https://console.groq.com/docs/quickstart)
- **Models API**: `GET https://api.groq.com/openai/v1/models`
- **Chat Endpoint**: `POST https://api.groq.com/openai/v1/chat/completions`
- **Free Plan Models**: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `deepseek-r1-distill-llama-70b`, `meta-llama/llama-prompt-guard-2-22m`, `gemma2-9b-it`.
- **Python SDK**:
  ```python
  from groq import Groq
  client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
  models = client.models.list()
  ```
  *(Có thể dùng cả SDK `openai` với `base_url="https://api.groq.com/openai/v1"`)*.

- **Bảng giới hạn Free Plan chính thức (Free Plan Limits)**:

| MODEL ID | RPM | RPD | TPM | TPD | ASH | ASD |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `canopylabs/orpheus-arabic-saudi` | 10 | 100 | 1.2K | 3.6K | - | - |
| `canopylabs/orpheus-v1-english` | 10 | 100 | 1.2K | 3.6K | - | - |
| `meta-llama/llama-prompt-guard-2-22m` | 30 | 14.4K | 15K | 500K | - | - |
| `meta-llama/llama-prompt-guard-2-86m` | 30 | 14.4K | 15K | 500K | - | - |
| `openai/gpt-oss-120b` | 30 | 1K | 8K | 200K | - | - |
| `openai/gpt-oss-20b` | 30 | 1K | 8K | 200K | - | - |
| `openai/gpt-oss-safeguard-20b` | 30 | 1K | 8K | 200K | - | - |
| `qwen/qwen3.8-27b` | 30 | 1K | 8K | 200K | - | - |
| `whisper-large-v3` | 20 | 2K | - | - | 7.2K | 28.8K |
| `whisper-large-v3-turbo` | 20 | 2K | - | - | 7.2K | 28.8K |

> *RPM: Requests/Phút \| RPD: Requests/Ngày \| TPM: Tokens/Phút \| TPD: Tokens/Ngày \| ASH: Giây Audio/Giờ \| ASD: Giây Audio/Ngày*

### 2.2 Google Gemini
- **Official Docs**: [Gemini Models Guide](https://ai.google.dev/gemini-api/docs/models)
- **API Reference**: [Gemini Models API](https://ai.google.dev/api/models)
- **Endpoint**: `GET https://generativelanguage.googleapis.com/v1beta/models`
- **Python SDK** (sử dụng SDK mới `google-genai`):
  ```python
  from google import genai
  client = genai.Client()
  models = client.models.list()
  ```
- **Metadata trả về**:
  - `name`: Tên định danh (dạng `models/gemini-2.5-flash` hoặc `gemini-2.5-flash`)
  - `baseModelId`: Model gốc
  - `version`: Phiên bản
  - `displayName`: Tên hiển thị người dùng (vd: "Gemini 2.5 Flash")
  - `description`: Mô tả năng lực và ứng dụng
  - `inputTokenLimit`: Giới hạn context window đầu vào
  - `outputTokenLimit`: Giới hạn tokens đầu ra
  - `supportedGenerationMethods`: Mảng các phương thức (vd: `["generateContent", "countTokens"]`)
- **Lưu ý nghiệp vụ**:
  - Lọc model dùng cho chat bằng điều kiện: `"generateContent" in model.supported_generation_methods`.
  - Chuẩn hóa ID model bằng cách bỏ tiền tố `models/` nếu có.

### 2.3 Anthropic Claude
- **Official Docs**: [Anthropic Models Overview](https://docs.anthropic.com/en/docs/about-claude/models/overview)
- **API Reference**: [Anthropic Models List API](https://docs.anthropic.com/en/api/models-list)
- **Endpoint**: `GET /v1/models`
- **Python SDK**:
  ```python
  import anthropic
  client = anthropic.Anthropic()
  response = client.models.list()
  # Hỗ trợ pagination: has_more, next_page_token, after_id
  ```
- **Metadata trả về**:
  - `id`: Tên mã model (vd: `claude-3-7-sonnet-20250219`, `claude-3-5-haiku-20241022`)
  - `display_name`: Tên model hiển thị (vd: "Claude 3.7 Sonnet")
  - `type`: "model"
  - `created_at`: Thời gian tạo
- **Lưu ý nghiệp vụ**:
  - Xử lý phân trang (pagination) lặp nếu danh sách model vượt qua giới hạn một trang (`limit=20` mặc định).

---

## 3. Kiến trúc Interface `BaseProvider`

Định nghĩa interface chuẩn trong `providers/base.py`:

```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import List, Any

class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Tên của provider: 'openai', 'gemini', 'anthropic'."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Kiểm tra xem provider này đã có API Key hợp lệ chưa."""
        pass

    @abstractmethod
    def list_models(self) -> List[Any]:
        """Gọi API của provider và trả về danh sách model thô từ API."""
        pass
```

---

## 4. Chi tiết triển khai cho từng Provider

### 4.1 OpenAI Provider
```python
# providers/openai_provider.py
from openai import OpenAI
from providers.base import BaseProvider

class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key) if api_key else None

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def list_models(self):
        if not self.is_configured():
            raise ValueError("OpenAI API Key chưa được cấu hình.")
        raw_list = self.client.models.list()
        # Lọc các model chat tiêu biểu
        chat_models = [
            m for m in raw_list.data 
            if any(prefix in m.id for prefix in ["gpt-", "o1", "o3", "chatgpt"])
        ]
        # Sắp xếp theo tên hoặc ngày tạo
        return sorted(chat_models, key=lambda m: m.id)
```

### 4.2 Gemini Provider
```python
# providers/gemini_provider.py
from google import genai
from providers.base import BaseProvider

class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key) if api_key else None

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def list_models(self):
        if not self.is_configured():
            raise ValueError("Gemini API Key chưa được cấu hình.")
        raw_list = self.client.models.list()
        # Chỉ lấy các model hỗ trợ generateContent
        chat_models = []
        for m in raw_list:
            supported = getattr(m, "supported_generation_methods", []) or []
            if "generateContent" in supported:
                chat_models.append(m)
        return chat_models
```

### 4.3 Anthropic Provider
```python
# providers/anthropic_provider.py
import anthropic
from providers.base import BaseProvider

class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def list_models(self):
        if not self.is_configured():
            raise ValueError("Anthropic API Key chưa được cấu hình.")
        all_models = []
        # Xử lý pagination
        page = self.client.models.list(limit=50)
        all_models.extend(page.data)
        while page.has_more:
            page = self.client.models.list(limit=50, after_id=page.last_id)
            all_models.extend(page.data)
        return all_models
```

---

## 5. Xử lý Exception & Edge Cases
1. **Network Error / Timeout**: Wrap cuộc gọi API với try-except bắt các lỗi `APIConnectionError`, `RateLimitError`, `AuthenticationError`.
2. **Key không hợp lệ**: Ném lỗi rõ ràng: `AuthenticationError: Invalid API Key for {provider}`.
3. **Caching tạm thời (In-memory Cache)**: Vì danh sách model ít khi thay đổi trong vài phút, có thể cache kết quả gọi `list_models()` với TTL 5-10 phút để tránh spam API và tăng tốc độ CLI.

---

## 6. Tiêu chí hoàn thành (Definition of Done)
- [ ] Interface `BaseProvider` có phương thức trừu tượng `list_models()`.
- [ ] 3 class `OpenAIProvider`, `GeminiProvider`, `AnthropicProvider` gọi đúng API lấy model.
- [ ] Lọc bỏ các model không phải chat (embedding, tts, v.v.).
- [ ] Xử lý phân trang cho Anthropic API.
- [ ] Kiểm thử thành công hàm gọi thực tế khi có API Key.
