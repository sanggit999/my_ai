# Phase 3: Chuẩn Hóa ModelInfo (Normalized Model Metadata)

## 1. Mục tiêu (Objective)
Mỗi nhà cung cấp (OpenAI, Gemini, Anthropic) trả về một cấu trúc object model khác nhau:
- OpenAI: `id`, `created`, `owned_by`
- Gemini: `name`, `displayName`, `description`, `inputTokenLimit`, `outputTokenLimit`, `supportedGenerationMethods`
- Anthropic: `id`, `display_name`, `created_at`, `type`

Mục tiêu của Phase 3 là xây dựng một Data Model chung duy nhất tên là `ModelInfo`. Toàn bộ hệ thống (từ CLI, router, selector đến chat engine) sẽ chỉ làm việc với `ModelInfo` chuẩn hóa này.

---

## 2. Thiết kế Schema `ModelInfo`

Sử dụng `pydantic` hoặc `dataclasses` để định nghĩa:

```python
# models/model_info.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class ModelInfo:
    provider: str                         # 'openai' | 'gemini' | 'anthropic'
    id: str                               # Model ID dùng để gửi API (vd: 'gpt-4o', 'gemini-2.5-flash')
    display_name: str                     # Tên thân thiện hiển thị trên UI/CLI
    description: Optional[str] = None     # Mô tả chức năng / thế mạnh của model
    input_token_limit: Optional[int] = None   # Context window đầu vào tối đa
    output_token_limit: Optional[int] = None  # Giới hạn output tokens tối đa
    capabilities: List[str] = field(default_factory=list) # ['chat', 'vision', 'reasoning', 'tools']
    raw_metadata: Dict[str, Any] = field(default_factory=dict) # Lưu data gốc để debug nếu cần

    @property
    def full_label(self) -> str:
        """Nhãn hiển thị đầy đủ trên giao diện CLI."""
        context_str = f" [Context: {self.input_token_limit:,}]" if self.input_token_limit else ""
        return f"[{self.provider.upper()}] {self.display_name} ({self.id}){context_str}"
```

---

## 3. Các hàm Adapter / Transformer chuẩn hóa

### 3.1 OpenAI Adapter
OpenAI không trả về trực tiếp `input_token_limit` hay `description` trong API `models.list()`, vì vậy ta áp dụng kỹ thuật heuristic hoặc tra cứu bảng mapping phụ nếu muốn hiển thị chi tiết:

```python
# adapters/openai_adapter.py
from models.model_info import ModelInfo

# Bảng tra cứu token limit cho các model phổ biến của OpenAI
OPENAI_SPECS = {
    "gpt-4o": {"context": 128000, "output": 16384, "caps": ["chat", "vision", "tools"]},
    "gpt-4o-mini": {"context": 128000, "output": 16384, "caps": ["chat", "vision", "tools"]},
    "o1": {"context": 200000, "output": 100000, "caps": ["reasoning", "tools"]},
    "o3-mini": {"context": 200000, "output": 100000, "caps": ["reasoning", "tools"]},
}

def normalize_openai_model(raw_model) -> ModelInfo:
    m_id = raw_model.id
    spec = OPENAI_SPECS.get(m_id, {"context": None, "output": None, "caps": ["chat"]})

    return ModelInfo(
        provider="openai",
        id=m_id,
        display_name=m_id,
        description=f"OpenAI model owned by {raw_model.owned_by}",
        input_token_limit=spec.get("context"),
        output_token_limit=spec.get("output"),
        capabilities=spec.get("caps", ["chat"]),
        raw_metadata={"created": getattr(raw_model, "created", None), "owned_by": raw_model.owned_by}
    )
```

### 3.2 Gemini Adapter
Gemini cung cấp metadata rất phong phú từ API chính thức:

```python
# adapters/gemini_adapter.py
from models.model_info import ModelInfo

def normalize_gemini_model(raw_model) -> ModelInfo:
    # Bỏ tiền tố "models/" nếu có trong name
    raw_name = getattr(raw_model, "name", "")
    model_id = raw_name.replace("models/", "") if raw_name.startswith("models/") else raw_name
    
    display_name = getattr(raw_model, "display_name", None) or model_id
    description = getattr(raw_model, "description", "")
    input_limit = getattr(raw_model, "input_token_limit", None)
    output_limit = getattr(raw_model, "output_token_limit", None)
    methods = getattr(raw_model, "supported_generation_methods", []) or []

    caps = ["chat"]
    if any("vision" in (desc := description.lower()) or "multimodal" in desc for desc in [description]):
        caps.append("vision")

    return ModelInfo(
        provider="gemini",
        id=model_id,
        display_name=display_name,
        description=description,
        input_token_limit=input_limit,
        output_token_limit=output_limit,
        capabilities=caps,
        raw_metadata={
            "supported_methods": methods,
            "version": getattr(raw_model, "version", None)
        }
    )
```

### 3.3 Anthropic Adapter
```python
# adapters/anthropic_adapter.py
from models.model_info import ModelInfo

ANTHROPIC_SPECS = {
    "claude-3-7-sonnet": {"context": 200000, "output": 64000, "caps": ["chat", "vision", "reasoning", "tools"]},
    "claude-3-5-sonnet": {"context": 200000, "output": 8192, "caps": ["chat", "vision", "tools"]},
    "claude-3-5-haiku": {"context": 200000, "output": 8192, "caps": ["chat", "tools"]},
}

def normalize_anthropic_model(raw_model) -> ModelInfo:
    m_id = raw_model.id
    display_name = getattr(raw_model, "display_name", m_id)

    # Tìm spec tương ứng gần đúng
    spec = {"context": 200000, "output": 8192, "caps": ["chat"]}
    for k, v in ANTHROPIC_SPECS.items():
        if k in m_id:
            spec = v
            break

    return ModelInfo(
        provider="anthropic",
        id=m_id,
        display_name=display_name,
        description=f"Anthropic Claude model ({display_name})",
        input_token_limit=spec.get("context"),
        output_token_limit=spec.get("output"),
        capabilities=spec.get("caps", ["chat"]),
        raw_metadata={"created_at": str(getattr(raw_model, "created_at", ""))}
    )
```

---

## 4. Tích hợp vào `BaseProvider`
Cập nhật phương thức trong `BaseProvider`:

```python
# providers/base.py
class BaseProvider(ABC):
    ...
    @abstractmethod
    def get_models(self) -> List[ModelInfo]:
        """Lấy danh sách model và chuẩn hóa thành List[ModelInfo]."""
        pass
```

Mỗi provider sẽ gọi `list_models()` thô rồi chạy qua hàm adapter tương ứng để trả về `List[ModelInfo]`.

---

## 5. Tiêu chí hoàn thành (Definition of Done)
- [ ] Schema `ModelInfo` bao quát đầy đủ thông tin định danh và context limit.
- [ ] Các adapter cho OpenAI, Gemini, Claude chuyển đổi chính xác các object thô sang `ModelInfo`.
- [ ] Không phụ thuộc vào cấu trúc riêng lẻ của từng SDK trong code logic cấp trên.
- [ ] Hàm `full_label` hiển thị đẹp mắt, trực quan cho bước hiển thị CLI ở Phase 4.
