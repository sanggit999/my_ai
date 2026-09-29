"""Groq Provider Implementation (OpenAI-Compatible 3rd-party API).

Hỗ trợ lấy models động và chat completion siêu tốc qua Groq:
- Endpoint Models: GET https://api.groq.com/openai/v1/models
- Endpoint Chat:   POST https://api.groq.com/openai/v1/chat/completions
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from .config import GroqConfig


# Bảng thông số giới hạn gói miễn phí (Free Plan Limits) chính thức của Groq
GROQ_FREE_PLAN_LIMITS: Dict[str, Dict[str, str]] = {
    "canopylabs/orpheus-arabic-saudi": {
        "rpm": "10", "rpd": "100", "tpm": "1.2K", "tpd": "3.6K", "ash": "-", "asd": "-"
    },
    "canopylabs/orpheus-v1-english": {
        "rpm": "10", "rpd": "100", "tpm": "1.2K", "tpd": "3.6K", "ash": "-", "asd": "-"
    },
    "meta-llama/llama-prompt-guard-2-22m": {
        "rpm": "30", "rpd": "14.4K", "tpm": "15K", "tpd": "500K", "ash": "-", "asd": "-"
    },
    "meta-llama/llama-prompt-guard-2-86m": {
        "rpm": "30", "rpd": "14.4K", "tpm": "15K", "tpd": "500K", "ash": "-", "asd": "-"
    },
    "openai/gpt-oss-120b": {
        "rpm": "30", "rpd": "1K", "tpm": "8K", "tpd": "200K", "ash": "-", "asd": "-"
    },
    "openai/gpt-oss-20b": {
        "rpm": "30", "rpd": "1K", "tpm": "8K", "tpd": "200K", "ash": "-", "asd": "-"
    },
    "openai/gpt-oss-safeguard-20b": {
        "rpm": "30", "rpd": "1K", "tpm": "8K", "tpd": "200K", "ash": "-", "asd": "-"
    },
    "qwen/qwen3.8-27b": {
        "rpm": "30", "rpd": "1K", "tpm": "8K", "tpd": "200K", "ash": "-", "asd": "-"
    },
    "whisper-large-v3": {
        "rpm": "20", "rpd": "2K", "tpm": "-", "tpd": "-", "ash": "7.2K", "asd": "28.8K"
    },
    "whisper-large-v3-turbo": {
        "rpm": "20", "rpd": "2K", "tpm": "-", "tpd": "-", "ash": "7.2K", "asd": "28.8K"
    },
}


class GroqProvider(BaseProvider):
    """Provider tương tác với Groq API (OpenAI-compatible siêu tốc)."""

    def __init__(self, config: Optional[GroqConfig] = None):
        config = config or GroqConfig()
        super().__init__(config)
        self.config: GroqConfig = config

    @classmethod
    def get_model_limits(cls, model_id: str) -> Optional[Dict[str, str]]:
        """Lấy thông số giới hạn Free Plan (RPM, RPD, TPM, TPD) của một model."""
        return GROQ_FREE_PLAN_LIMITS.get(model_id)

    def _call_via_groq_sdk(self) -> List[Dict[str, Any]]:
        """Gọi qua SDK chính thức `groq`."""
        from groq import Groq, AuthenticationError, RateLimitError, APIConnectionError
        try:
            client = Groq(api_key=self.config.api_key)
            response = client.models.list()
            models = []
            for item in response.data:
                models.append({
                    "id": item.id,
                    "created": getattr(item, "created", None),
                    "owned_by": getattr(item, "owned_by", "groq"),
                    "active": getattr(item, "active", True),
                    "context_window": getattr(item, "context_window", None),
                    "limits": self.get_model_limits(item.id),
                })
            return models
        except AuthenticationError as e:
            raise PermissionError(f"[Groq 401] API Key không hợp lệ hoặc đã hết hạn: {e}") from e
        except RateLimitError as e:
            raise RuntimeError(f"[Groq 429] Tài khoản đã chạm giới hạn tốc độ/quota: {e}") from e
        except APIConnectionError as e:
            raise ConnectionError(f"[Groq Network] Không thể kết nối tới máy chủ Groq: {e}") from e

    def _call_via_openai_sdk(self) -> List[Dict[str, Any]]:
        """Gọi qua OpenAI SDK với base_url của Groq."""
        from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
        try:
            client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
            response = client.models.list()
            models = []
            for item in response.data:
                models.append({
                    "id": item.id,
                    "created": getattr(item, "created", None),
                    "owned_by": getattr(item, "owned_by", "groq"),
                    "limits": self.get_model_limits(item.id),
                })
            return models
        except AuthenticationError as e:
            raise PermissionError(f"[Groq/OpenAI 401] API Key không hợp lệ: {e}") from e
        except RateLimitError as e:
            raise RuntimeError(f"[Groq 429] Rate Limit: {e}") from e
        except APIConnectionError as e:
            raise ConnectionError(f"[Groq Network] Lỗi kết nối: {e}") from e

    def _call_via_rest_api(self) -> List[Dict[str, Any]]:
        """Fallback gọi trực tiếp HTTP REST endpoint bằng thư viện chuẩn (zero-dependency)."""
        url = f"{self.config.base_url.rstrip('/')}/models"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    data = payload.get("data", [])
                    for item in data:
                        item["limits"] = self.get_model_limits(item.get("id", ""))
                    return data
                raise RuntimeError(f"Groq API trả về mã: {response.status}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                error_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                error_msg = err_body

            if e.code == 401:
                raise PermissionError(f"[Groq 401 Unauthorized] {error_msg}") from e
            elif e.code == 429:
                raise RuntimeError(f"[Groq 429 Rate Limit] {error_msg}") from e
            else:
                raise RuntimeError(f"[Groq HTTP {e.code}] {error_msg}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(f"[Groq Network Error] Lỗi kết nối: {e.reason}") from e

    def list_models(self) -> List[Dict[str, Any]]:
        """Truy vấn danh sách tất cả các models từ Groq."""
        if not self.is_ready:
            raise ValueError("Chưa cấu hình GROQ_API_KEY trong file .env!")

        # 1. Thử dùng SDK groq
        try:
            import groq
            return self._call_via_groq_sdk()
        except ImportError:
            pass

        # 2. Thử dùng SDK openai với Groq base_url
        try:
            import openai
            return self._call_via_openai_sdk()
        except ImportError:
            pass

        # 3. Fallback thư viện chuẩn urllib
        return self._call_via_rest_api()

    def list_chat_models(self) -> List[Dict[str, Any]]:
        """Lọc và trả về danh sách các model chat/LLM phổ biến trên Groq."""
        all_models = self.list_models()
        # Loại bỏ các model audio như whisper
        chat_models = [
            m for m in all_models
            if not any(k in m.get("id", "").lower() for k in ("whisper", "tts", "audio"))
        ]

        def sort_key(model_dict):
            m_id = model_dict.get("id", "").lower()
            priority = 99
            if "llama-3.3-70b" in m_id:
                priority = 1
            elif "deepseek-r1" in m_id:
                priority = 2
            elif "llama-3.1-8b" in m_id:
                priority = 3
            elif "gemma2-9b" in m_id:
                priority = 4
            elif "mixtral" in m_id:
                priority = 5
            return (priority, m_id)

        return sorted(chat_models, key=sort_key)

    def get_models(self) -> list:
        """Chuẩn hóa danh sách chat models thành List[ModelInfo] (Phase 3)."""
        from models.model_info import ModelInfo

        raw_chat = self.list_chat_models()
        normalized = []

        context_windows = {
            "llama-3.3-70b": 128000,
            "llama-3.1-8b": 128000,
            "deepseek-r1": 128000,
            "openai/gpt-oss-120b": 131072,
            "openai/gpt-oss-20b": 131072,
            "qwen/qwen3.8-27b": 32768,
            "gemma2-9b": 8192,
        }

        for m in raw_chat:
            m_id = m.get("id", "")
            limits = m.get("limits")
            ctx = m.get("context_window")
            if not ctx:
                for k, v in context_windows.items():
                    if k in m_id.lower():
                        ctx = v
                        break
                ctx = ctx or 8192

            caps = ["chat"]
            if "deepseek" in m_id.lower() or "reasoning" in m_id.lower():
                caps.append("reasoning")

            normalized.append(ModelInfo(
                provider="groq",
                id=m_id,
                display_name=m_id,
                description=f"Groq LPU Model ({m.get('owned_by', 'groq')})",
                input_token_limit=ctx,
                output_token_limit=4096,
                capabilities=caps,
                rate_limits=limits,
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
        """Sinh phản hồi hoàn chỉnh từ Groq và chuẩn hóa thành UnifiedResponse (Phase 5 & 6)."""
        import time
        from models.unified_response import UnifiedResponse, TokenUsage

        if not self.is_ready:
            raise ValueError("Chưa cấu hình GROQ_API_KEY trong file .env!")

        # Chuẩn bị messages
        msgs = []
        if system_prompt and not any(m.get("role") == "system" for m in messages):
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        start_time = time.perf_counter()

        # 1. Thử qua Groq SDK
        try:
            from groq import Groq
            client = Groq(api_key=self.config.api_key)
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
                provider="groq",
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                latency_ms=latency,
                raw_response=resp,
            )
        except ImportError:
            pass

        # 2. Fallback REST API
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
        }
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
                    provider="groq",
                    model=model,
                    usage=usage,
                    finish_reason=finish_reason,
                    latency_ms=latency,
                    raw_response=res_json,
                )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Groq API Error ({e.code}): {err_body}") from e

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
            raise ValueError("Chưa cấu hình GROQ_API_KEY trong file .env!")

        msgs = []
        if system_prompt and not any(m.get("role") == "system" for m in messages):
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        # 1. Thử Groq SDK streaming
        try:
            from groq import Groq
            client = Groq(api_key=self.config.api_key)
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
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
            "Accept": "text/event-stream",
        }
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
            # Fallback nếu SSE lỗi: gọi generate() thông thường và yield
            full = self.generate(model, messages, temperature, max_tokens, system_prompt)
            text = full.content
            chunk_size = 8
            for i in range(0, len(text), chunk_size):
                yield text[i:i + chunk_size]

    def generate_chat(self, model: str, prompt: str) -> str:
        """Hàm đơn giản tương thích ngược các script test."""
        resp = self.generate(model, [{"role": "user", "content": prompt}])
        return resp.content

