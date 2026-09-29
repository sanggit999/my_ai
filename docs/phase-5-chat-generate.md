# Phase 5: Chat & Generation Engine

## 1. Mục tiêu (Objective)
Xây dựng phương thức sinh phản hồi `generate(model, prompt)` và `generate_stream(model, prompt)` cho từng provider. Mỗi provider tự quản lý SDK và định dạng payload của mình, tuân thủ nguyên tắc đa hình (Polymorphism) để caller ở tầng ứng dụng không cần biết bên dưới là OpenAI, Gemini hay Anthropic.

---

## 2. Đặc tả Interface chung trong `BaseProvider`

```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import Generator, Optional, List, Dict, Any

class BaseProvider(ABC):
    ...
    @abstractmethod
    def generate(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Any:
        """Gửi prompt và trả về raw response đầy đủ từ provider."""
        pass

    @abstractmethod
    def generate_stream(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Stream từng mẩu text (chunks) trả về từ model theo thời gian thực."""
        pass
```

---

## 3. Triển khai chi tiết theo từng Provider

### 3.1 OpenAI Implementation
OpenAI hỗ trợ cả streaming lẫn synchronous thông qua `client.chat.completions.create`:

```python
# providers/openai_provider.py
class OpenAIProvider(BaseProvider):
    ...
    def _prepare_messages(self, messages, system_prompt):
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        return full_messages

    def generate(self, model_id: str, messages, temperature=0.7, max_tokens=None, system_prompt=None):
        payload = {
            "model": model_id,
            "messages": self._prepare_messages(messages, system_prompt),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        return self.client.chat.completions.create(**payload)

    def generate_stream(self, model_id: str, messages, temperature=0.7, max_tokens=None, system_prompt=None):
        stream = self.client.chat.completions.create(
            model=model_id,
            messages=self._prepare_messages(messages, system_prompt),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content
```

### 3.2 Google Gemini Implementation
Sử dụng SDK `google-genai` mới:

```python
# providers/gemini_provider.py
from google.genai import types

class GeminiProvider(BaseProvider):
    ...
    def _prepare_contents_and_config(self, messages, system_prompt, temperature, max_tokens):
        # Chuyển đổi tin nhắn sang dạng cấu trúc Gemini
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_prompt if system_prompt else None
        )
        return contents, config

    def generate(self, model_id: str, messages, temperature=0.7, max_tokens=None, system_prompt=None):
        contents, config = self._prepare_contents_and_config(messages, system_prompt, temperature, max_tokens)
        return self.client.models.generate_content(
            model=model_id,
            contents=contents,
            config=config
        )

    def generate_stream(self, model_id: str, messages, temperature=0.7, max_tokens=None, system_prompt=None):
        contents, config = self._prepare_contents_and_config(messages, system_prompt, temperature, max_tokens)
        stream = self.client.models.generate_content_stream(
            model=model_id,
            contents=contents,
            config=config
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text
```

### 3.3 Anthropic Claude Implementation
Claude Messages API có quy tắc: `system` prompt phải truyền qua param riêng `system`, không để trong mảng `messages`:

```python
# providers/anthropic_provider.py
class AnthropicProvider(BaseProvider):
    ...
    def generate(self, model_id: str, messages, temperature=0.7, max_tokens=None, system_prompt=None):
        # Claude bắt buộc phải có max_tokens (mặc định set 4096 nếu None)
        max_tokens = max_tokens or 4096
        
        # Chỉ giữ lại role user và assistant
        formatted_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages if m["role"] in ["user", "assistant"]
        ]

        kwargs = {
            "model": model_id,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        return self.client.messages.create(**kwargs)

    def generate_stream(self, model_id: str, messages, temperature=0.7, max_tokens=None, system_prompt=None):
        max_tokens = max_tokens or 4096
        formatted_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages if m["role"] in ["user", "assistant"]
        ]

        kwargs = {
            "model": model_id,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
```

---

## 4. Xử lý các tình huống đặc biệt (Edge Cases)
1. **Lỗi Quota / Rate Limit (HTTP 429)**: Thông báo người dùng chờ đợi hoặc chuyển tạm sang provider khác.
2. **Context Window Exceeded**: Cắt bớt các message cũ ở đầu danh sách (xem Phase 7).
3. **Mô hình suy luận (Reasoning Models)**:
   - Các model như `o1`, `o3-mini` của OpenAI có thể không hỗ trợ tham số `temperature` tùy chỉnh hoặc yêu cầu `max_completion_tokens` thay vì `max_tokens`. Cần adapter kiểm tra tiền tố model trước khi gửi request.

---

## 5. Tiêu chí hoàn thành (Definition of Done)
- [ ] Cả 3 provider thực thi thành công cả `generate()` và `generate_stream()`.
- [ ] Tham số `system_prompt`, `temperature` được chuyển đổi tương thích với cú pháp của từng provider.
- [ ] Hỗ trợ stream phản hồi ra terminal từng chữ một giúp trải nghiệm người dùng phản hồi tức thì.
