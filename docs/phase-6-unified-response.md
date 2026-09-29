# Phase 6: Unified Response

## 1. Mục tiêu (Objective)
Các SDK trả về đối tượng kết quả với cấu trúc hoàn toàn khác nhau:
- **OpenAI**: `response.choices[0].message.content`, `response.usage.prompt_tokens`, `response.choices[0].finish_reason`
- **Gemini**: `response.text`, `response.usage_metadata.prompt_token_count`, `response.candidates[0].finish_reason`
- **Anthropic**: `response.content[0].text`, `response.usage.input_tokens`, `response.stop_reason`

Mục tiêu của Phase 6 là chuẩn hóa đầu ra thành một đối tượng duy nhất `UnifiedResponse`, giúp người dùng, CLI renderer và các ứng dụng tích hợp dễ dàng đọc dữ liệu, thống kê token và thời gian phản hồi (latency).

---

## 2. Thiết kế Schema `UnifiedResponse`

```python
# models/unified_response.py
from dataclasses import dataclass, field
from typing import Optional, Any

@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def summary(self) -> str:
        return f"Input: {self.prompt_tokens:,} | Output: {self.completion_tokens:,} | Total: {self.total_tokens:,}"

@dataclass
class UnifiedResponse:
    content: str                               # Nội dung văn bản trả về hoàn chỉnh
    provider: str                              # 'openai' | 'gemini' | 'anthropic'
    model: str                                 # Model ID đã dùng
    usage: TokenUsage                          # Thống kê lượng token tiêu thụ
    finish_reason: Optional[str] = None        # 'stop', 'length', 'content_filter', ...
    latency_ms: Optional[float] = None         # Thời gian thực thi phản hồi (miliseconds)
    raw_response: Optional[Any] = field(default=None, repr=False) # Đối tượng nguyên bản từ SDK
```

---

## 3. Các hàm Adapter chuyển đổi Response

### 3.1 OpenAI Response Adapter
```python
# adapters/response_adapters.py
from models.unified_response import UnifiedResponse, TokenUsage

def parse_openai_response(raw_resp, model: str, latency_ms: float = 0.0) -> UnifiedResponse:
    content = ""
    finish_reason = None
    if raw_resp.choices:
        choice = raw_resp.choices[0]
        content = choice.message.content or ""
        finish_reason = choice.finish_reason

    usage = TokenUsage()
    if raw_resp.usage:
        usage = TokenUsage(
            prompt_tokens=raw_resp.usage.prompt_tokens,
            completion_tokens=raw_resp.usage.completion_tokens,
            total_tokens=raw_resp.usage.total_tokens,
        )

    return UnifiedResponse(
        content=content,
        provider="openai",
        model=model,
        usage=usage,
        finish_reason=finish_reason,
        latency_ms=latency_ms,
        raw_response=raw_resp
    )
```

### 3.2 Gemini Response Adapter
```python
def parse_gemini_response(raw_resp, model: str, latency_ms: float = 0.0) -> UnifiedResponse:
    content = getattr(raw_resp, "text", "") or ""
    
    finish_reason = None
    if getattr(raw_resp, "candidates", None):
        finish_reason = str(raw_resp.candidates[0].finish_reason)

    usage = TokenUsage()
    meta = getattr(raw_resp, "usage_metadata", None)
    if meta:
        usage = TokenUsage(
            prompt_tokens=getattr(meta, "prompt_token_count", 0) or 0,
            completion_tokens=getattr(meta, "candidates_token_count", 0) or 0,
            total_tokens=getattr(meta, "total_token_count", 0) or 0,
        )

    return UnifiedResponse(
        content=content,
        provider="gemini",
        model=model,
        usage=usage,
        finish_reason=finish_reason,
        latency_ms=latency_ms,
        raw_response=raw_resp
    )
```

### 3.3 Anthropic Response Adapter
```python
def parse_anthropic_response(raw_resp, model: str, latency_ms: float = 0.0) -> UnifiedResponse:
    content = ""
    if getattr(raw_resp, "content", None):
        # Trích xuất text từ các block content
        content = "".join([block.text for block in raw_resp.content if getattr(block, "type", "") == "text"])

    finish_reason = getattr(raw_resp, "stop_reason", None)

    usage = TokenUsage()
    raw_usage = getattr(raw_resp, "usage", None)
    if raw_usage:
        in_tokens = getattr(raw_usage, "input_tokens", 0) or 0
        out_tokens = getattr(raw_usage, "output_tokens", 0) or 0
        usage = TokenUsage(
            prompt_tokens=in_tokens,
            completion_tokens=out_tokens,
            total_tokens=in_tokens + out_tokens
        )

    return UnifiedResponse(
        content=content,
        provider="anthropic",
        model=model,
        usage=usage,
        finish_reason=finish_reason,
        latency_ms=latency_ms,
        raw_response=raw_resp
    )
```

---

## 4. Hiển thị thông tin thống kê trên CLI
Tạo một component hiển thị tóm tắt cuối mỗi câu trả lời:

```python
# cli/renderer.py
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from models.unified_response import UnifiedResponse

console = Console()

def render_response(resp: UnifiedResponse):
    """Hiển thị markdown câu trả lời và footer thống kê token/latency."""
    console.print("\n")
    console.print(Markdown(resp.content))
    console.print("\n")
    
    footer = (
        f"[dim]Provider: [cyan]{resp.provider}[/cyan] | "
        f"Model: [cyan]{resp.model}[/cyan] | "
        f"Latency: [yellow]{resp.latency_ms:.1f}ms[/yellow] | "
        f"{resp.usage.summary}[/dim]"
    )
    console.print(Panel(footer, style="dim"))
```

---

## 5. Tiêu chí hoàn thành (Definition of Done)
- [ ] Schema `UnifiedResponse` và `TokenUsage` được định nghĩa rõ ràng, dễ mở rộng.
- [ ] Kết quả từ bất kỳ provider nào cũng được wrap thành công thành `UnifiedResponse`.
- [ ] Tính toán chính xác thời gian phản hồi (latency tính bằng milliseconds).
- [ ] Giao diện CLI hiển thị thông số token usage rõ ràng, minh bạch sau mỗi phản hồi.
