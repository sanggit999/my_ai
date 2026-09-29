"""OpenAI Provider Implementation.

Kết nối tới OpenAI Models API để lấy danh mục models động:
- Tài liệu Models: https://platform.openai.com/docs/models
- Tài liệu API: https://platform.openai.com/docs/api-reference/models
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from .config import OpenAIConfig


class OpenAIProvider(BaseProvider):
    """Provider tương tác với OpenAI API."""

    def __init__(self, config: Optional[OpenAIConfig] = None):
        config = config or OpenAIConfig()
        super().__init__(config)
        self.config: OpenAIConfig = config

    def _call_via_sdk(self) -> List[Dict[str, Any]]:
        """Gọi qua official SDK `openai` nếu đã cài đặt."""
        from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
        try:
            client = OpenAI(**self.config.get_client_kwargs())
            response = client.models.list()
            # Chuẩn hóa danh sách Model object thành dict
            models = []
            for item in response.data:
                models.append({
                    "id": item.id,
                    "created": getattr(item, "created", None),
                    "owned_by": getattr(item, "owned_by", None),
                    "object": getattr(item, "object", "model"),
                })
            return models
        except AuthenticationError as e:
            raise PermissionError(f"[OpenAI 401] API Key không hợp lệ hoặc đã hết hạn: {e}") from e
        except RateLimitError as e:
            raise RuntimeError(f"[OpenAI 429] Tài khoản đã hết hạn mức (Quota) hoặc bị Rate Limit: {e}") from e
        except APIConnectionError as e:
            raise ConnectionError(f"[OpenAI Network] Không thể kết nối tới máy chủ OpenAI: {e}") from e

    def _call_via_rest_api(self) -> List[Dict[str, Any]]:
        """Fallback gọi trực tiếp HTTP REST endpoint bằng thư viện chuẩn (zero-dependency)."""
        base_url = (self.config.base_url or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/models"

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
        }
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization
        if self.config.project:
            headers["OpenAI-Project"] = self.config.project

        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    return payload.get("data", [])
                raise RuntimeError(f"OpenAI API trả về mã lỗi: {response.status}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                error_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                error_msg = err_body

            if e.code == 401:
                raise PermissionError(f"[OpenAI 401 Unauthorized] {error_msg}") from e
            elif e.code == 429:
                raise RuntimeError(f"[OpenAI 429 Rate Limit / Quota] {error_msg}") from e
            else:
                raise RuntimeError(f"[OpenAI HTTP {e.code}] {error_msg}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(f"[OpenAI Network Error] Lỗi kết nối: {e.reason}") from e

    def list_models(self) -> List[Dict[str, Any]]:
        """Truy vấn danh sách tất cả các models từ OpenAI API."""
        if not self.is_ready:
            raise ValueError("Chưa cấu hình OPENAI_API_KEY trong file .env!")

        # Thử dùng SDK chính thức nếu có, nếu chưa cài thì fallback REST API
        try:
            import openai
            return self._call_via_sdk()
        except ImportError:
            return self._call_via_rest_api()

    def list_chat_models(self) -> List[Dict[str, Any]]:
        """Lọc và trả về danh sách các model chuyên dụng cho Chat / Text Generation.
        
        Bao gồm: gpt-4o, gpt-4o-mini, o1, o3-mini, gpt-4-turbo, gpt-3.5-turbo,...
        Loại bỏ: whisper, tts, text-embedding, dall-e, moderation.
        """
        all_models = self.list_models()
        chat_prefixes = ("gpt-", "o1", "o3", "chatgpt-")
        exclude_keywords = ("realtime", "audio", "transcribe", "tts")

        chat_models = []
        for m in all_models:
            m_id = m.get("id", "").lower()
            if any(m_id.startswith(p) or f"/{p}" in m_id for p in chat_prefixes):
                if not any(k in m_id for k in exclude_keywords):
                    chat_models.append(m)

        # Sắp xếp các model phổ biến lên đầu (gpt-4o, o1, o3-mini,...)
        def sort_key(model_dict):
            m_id = model_dict.get("id", "")
            # Ưu tiên flagship models
            priority = 99
            if "gpt-4o-mini" in m_id:
                priority = 2
            elif "gpt-4o" in m_id:
                priority = 1
            elif "o3-mini" in m_id:
                priority = 3
            elif "o1" in m_id:
                priority = 4
            elif "gpt-4" in m_id:
                priority = 10
            return (priority, m_id)

        return sorted(chat_models, key=sort_key)

    def get_models(self) -> list:
        """Chuẩn hóa danh sách chat models thành List[ModelInfo] (Phase 3)."""
        from models.model_info import ModelInfo

        # Bảng tra cứu token limit cho các model OpenAI phổ biến
        known_specs = {
            "gpt-4o": {"context": 128000, "output": 16384, "caps": ["chat", "vision", "tools"]},
            "gpt-4o-mini": {"context": 128000, "output": 16384, "caps": ["chat", "vision", "tools"]},
            "o1": {"context": 200000, "output": 100000, "caps": ["reasoning", "tools"]},
            "o3-mini": {"context": 200000, "output": 100000, "caps": ["reasoning", "tools"]},
            "gpt-4-turbo": {"context": 128000, "output": 4096, "caps": ["chat", "vision", "tools"]},
            "gpt-3.5-turbo": {"context": 16385, "output": 4096, "caps": ["chat"]},
        }

        raw_chat = self.list_chat_models()
        normalized = []

        for m in raw_chat:
            m_id = m.get("id", "")
            spec = {"context": 128000, "output": 4096, "caps": ["chat"]}
            for prefix, s in known_specs.items():
                if prefix in m_id:
                    spec = s
                    break

            normalized.append(ModelInfo(
                provider="openai",
                id=m_id,
                display_name=m_id,
                description=f"OpenAI Model ({m.get('owned_by', 'system')})",
                input_token_limit=spec.get("context"),
                output_token_limit=spec.get("output"),
                capabilities=spec.get("caps", ["chat"]),
                raw_metadata=m,
            ))

        return normalized

    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ):
        """Sinh phản hồi và chuẩn hóa thành UnifiedResponse (Phase 5 & 6)."""
        import time
        from models.unified_response import UnifiedResponse, TokenUsage

        if not self.is_ready:
            raise ValueError("Chưa cấu hình OPENAI_API_KEY trong file .env!")

        # Chuẩn bị messages
        msgs = []
        if system_prompt and not any(m.get("role") == "system" for m in messages):
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        start_time = time.perf_counter()

        # 1. Thử qua OpenAI SDK
        try:
            from openai import OpenAI
            client = OpenAI(**self.config.get_client_kwargs())
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": msgs,
                "temperature": temperature,
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            resp = client.chat.completions.create(**kwargs)
            latency = (time.perf_counter() - start_time) * 1000

            choice = resp.choices[0]
            content = choice.message.content or ""
            finish_reason = getattr(choice, "finish_reason", None)

            usage = TokenUsage()
            if getattr(resp, "usage", None):
                usage = TokenUsage(
                    prompt_tokens=getattr(resp.usage, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(resp.usage, "completion_tokens", 0) or 0,
                    total_tokens=getattr(resp.usage, "total_tokens", 0) or 0,
                )

            return UnifiedResponse(
                content=content,
                provider="openai",
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                latency_ms=latency,
                raw_response=resp,
            )
        except ImportError:
            pass

        # 2. Fallback REST API
        base_url = (self.config.base_url or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
        }
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization
        if self.config.project:
            headers["OpenAI-Project"] = self.config.project

        body: Dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                latency = (time.perf_counter() - start_time) * 1000

                choice = res_json.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                finish_reason = choice.get("finish_reason")

                raw_usage = res_json.get("usage", {})
                usage = TokenUsage(
                    prompt_tokens=raw_usage.get("prompt_tokens", 0),
                    completion_tokens=raw_usage.get("completion_tokens", 0),
                    total_tokens=raw_usage.get("total_tokens", 0),
                )

                return UnifiedResponse(
                    content=content,
                    provider="openai",
                    model=model,
                    usage=usage,
                    finish_reason=finish_reason,
                    latency_ms=latency,
                    raw_response=res_json,
                )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OpenAI API Error ({e.code}): {err_body}") from e

    def generate_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ):
        """Sinh phản hồi streaming từng chunk theo thời gian thực (Phase 5)."""
        if not self.is_ready:
            raise ValueError("Chưa cấu hình OPENAI_API_KEY trong file .env!")

        msgs = []
        if system_prompt and not any(m.get("role") == "system" for m in messages):
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        # 1. Thử OpenAI SDK streaming
        try:
            from openai import OpenAI
            client = OpenAI(**self.config.get_client_kwargs())
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": msgs,
                "temperature": temperature,
                "stream": True,
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            response_stream = client.chat.completions.create(**kwargs)
            for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return
        except ImportError:
            pass

        # 2. Thử SSE streaming qua REST API
        base_url = (self.config.base_url or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
            "Accept": "text/event-stream",
        }
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization
        if self.config.project:
            headers["OpenAI-Project"] = self.config.project

        body: Dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                for line_bytes in resp:
                    line = line_bytes.decode("utf-8").strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            choices = data_json.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                text_chunk = delta.get("content", "")
                                if text_chunk:
                                    yield text_chunk
                        except json.JSONDecodeError:
                            continue
            return
        except Exception:
            # Fallback nếu SSE lỗi
            full = self.generate(model, messages, temperature, max_tokens, system_prompt)
            text = full.content
            chunk_size = 8
            for i in range(0, len(text), chunk_size):
                yield text[i:i + chunk_size]

    def generate_chat(self, model: str, prompt: str) -> str:
        """Hàm đơn giản tương thích ngược các script test."""
        resp = self.generate(model, [{"role": "user", "content": prompt}])
        return resp.content

