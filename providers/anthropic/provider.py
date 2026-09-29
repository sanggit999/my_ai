"""Anthropic Claude Provider Implementation.

Kết nối tới Anthropic API để lấy danh mục models động và sinh phản hồi:
- Tài liệu Models: https://docs.anthropic.com/en/docs/about-claude/models/overview
- Tài liệu API:    https://docs.anthropic.com/en/api/models-list
- Endpoint Models: GET https://api.anthropic.com/v1/models
- Endpoint Chat:   POST https://api.anthropic.com/v1/messages
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from .config import AnthropicConfig


class AnthropicProvider(BaseProvider):
    """Provider tương tác với Anthropic Claude API."""

    def __init__(self, config: Optional[AnthropicConfig] = None):
        config = config or AnthropicConfig()
        super().__init__(config)
        self.config: AnthropicConfig = config

    def _call_via_sdk(self) -> List[Dict[str, Any]]:
        """Gọi qua SDK chính thức `anthropic` nếu đã cài đặt."""
        import anthropic
        from anthropic import AuthenticationError, RateLimitError, APIConnectionError
        try:
            client = anthropic.Anthropic(**self.config.get_client_kwargs())
            models = []
            page = client.models.list(limit=50)
            for item in page.data:
                models.append({
                    "id": item.id,
                    "display_name": getattr(item, "display_name", item.id),
                    "type": getattr(item, "type", "model"),
                    "created_at": getattr(item, "created_at", None),
                })
            while page.has_more:
                page = client.models.list(limit=50, after_id=page.last_id)
                for item in page.data:
                    models.append({
                        "id": item.id,
                        "display_name": getattr(item, "display_name", item.id),
                        "type": getattr(item, "type", "model"),
                        "created_at": getattr(item, "created_at", None),
                    })
            return models
        except AuthenticationError as e:
            raise PermissionError(f"[Anthropic 401] API Key không hợp lệ hoặc đã hết hạn: {e}") from e
        except RateLimitError as e:
            raise RuntimeError(f"[Anthropic 429] Tài khoản đã chạm giới hạn tốc độ/quota: {e}") from e
        except APIConnectionError as e:
            raise ConnectionError(f"[Anthropic Network] Không thể kết nối tới máy chủ Anthropic: {e}") from e

    def _call_via_rest_api(self) -> List[Dict[str, Any]]:
        """Fallback gọi trực tiếp REST endpoint bằng thư viện chuẩn (zero-dependency)."""
        base_url = (self.config.base_url or "https://api.anthropic.com").rstrip("/")
        url = f"{base_url}/v1/models?limit=50"

        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    raw_data = payload.get("data", [])
                    models = []
                    for item in raw_data:
                        models.append({
                            "id": item.get("id", ""),
                            "display_name": item.get("display_name", item.get("id", "")),
                            "type": item.get("type", "model"),
                            "created_at": item.get("created_at"),
                        })
                    return models
                raise RuntimeError(f"Anthropic API trả về mã: {response.status}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                error_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                error_msg = err_body

            if e.code == 401:
                raise PermissionError(f"[Anthropic 401 Unauthorized] {error_msg}") from e
            elif e.code == 429:
                raise RuntimeError(f"[Anthropic 429 Rate Limit / Quota] {error_msg}") from e
            else:
                raise RuntimeError(f"[Anthropic HTTP {e.code}] {error_msg}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(f"[Anthropic Network Error] Lỗi kết nối: {e.reason}") from e

    def list_models(self) -> List[Dict[str, Any]]:
        """Truy vấn danh sách tất cả các models từ Anthropic API."""
        if not self.is_ready:
            raise ValueError("Chưa cấu hình ANTHROPIC_API_KEY trong file .env!")

        try:
            import anthropic
            return self._call_via_sdk()
        except ImportError:
            return self._call_via_rest_api()

    def list_chat_models(self) -> List[Dict[str, Any]]:
        """Lọc và sắp xếp các model Claude theo độ ưu tiên."""
        all_models = self.list_models()

        def sort_key(model_dict):
            m_id = model_dict.get("id", "").lower()
            priority = 99
            if "claude-3-7-sonnet" in m_id:
                priority = 1
            elif "claude-3-5-sonnet" in m_id:
                priority = 2
            elif "claude-3-5-haiku" in m_id:
                priority = 3
            elif "claude-3-opus" in m_id:
                priority = 4
            elif "claude-3-haiku" in m_id:
                priority = 5
            return (priority, m_id)

        return sorted(all_models, key=sort_key)

    def get_models(self) -> list:
        """Chuẩn hóa danh sách chat models thành List[ModelInfo] (Phase 3)."""
        from models.model_info import ModelInfo

        raw_chat = self.list_chat_models()
        normalized = []

        for m in raw_chat:
            m_id = m.get("id", "")
            disp = m.get("display_name") or m_id
            created = m.get("created_at")

            # Context window chuẩn của Claude là 200k tokens
            ctx = 200000
            out_limit = 8192
            if "3-7" in m_id or "opus" in m_id:
                out_limit = 64000

            caps = ["chat", "vision", "tools"]
            if "opus" in m_id or "3-7" in m_id or "sonnet" in m_id:
                caps.append("reasoning")

            normalized.append(ModelInfo(
                provider="anthropic",
                id=m_id,
                display_name=disp,
                description=f"Anthropic Claude Model ({disp})",
                input_token_limit=ctx,
                output_token_limit=out_limit,
                capabilities=caps,
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
        """Sinh phản hồi hoàn chỉnh từ Anthropic Claude và chuẩn hóa thành UnifiedResponse (Phase 5 & 6)."""
        import time
        from models.unified_response import UnifiedResponse, TokenUsage

        if not self.is_ready:
            raise ValueError("Chưa cấu hình ANTHROPIC_API_KEY trong file .env!")

        # Anthropic yêu cầu max_tokens bắt buộc
        max_tokens = max_tokens or 4096

        # Phân tách system prompt và messages
        sys_text = system_prompt or ""
        filtered_messages = []
        for m in messages:
            if m.get("role") == "system":
                sys_text = (sys_text + "\n" + m.get("content", "")).strip()
            else:
                filtered_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        start_time = time.perf_counter()

        # 1. Thử qua Anthropic SDK
        try:
            import anthropic
            client = anthropic.Anthropic(**self.config.get_client_kwargs())
            kwargs: Dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": filtered_messages,
            }
            if sys_text:
                kwargs["system"] = sys_text

            response = client.messages.create(**kwargs)
            latency = (time.perf_counter() - start_time) * 1000

            text_blocks = [b.text for b in response.content if getattr(b, "type", "") == "text"]
            content = "".join(text_blocks)
            finish_reason = getattr(response, "stop_reason", None)

            usage = TokenUsage()
            if getattr(response, "usage", None):
                in_tok = getattr(response.usage, "input_tokens", 0) or 0
                out_tok = getattr(response.usage, "output_tokens", 0) or 0
                usage = TokenUsage(
                    prompt_tokens=in_tok,
                    completion_tokens=out_tok,
                    total_tokens=in_tok + out_tok,
                )

            return UnifiedResponse(
                content=content,
                provider="anthropic",
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                latency_ms=latency,
                raw_response=response,
            )
        except ImportError:
            pass

        # 2. Fallback REST API
        base_url = (self.config.base_url or "https://api.anthropic.com").rstrip("/")
        url = f"{base_url}/v1/messages"

        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered_messages,
        }
        if sys_text:
            payload["system"] = sys_text

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                latency = (time.perf_counter() - start_time) * 1000

                contents = res_json.get("content", [])
                text_parts = [c.get("text", "") for c in contents if c.get("type") == "text"]
                content = "".join(text_parts)
                finish_reason = res_json.get("stop_reason")

                raw_usage = res_json.get("usage", {})
                in_tok = raw_usage.get("input_tokens", 0)
                out_tok = raw_usage.get("output_tokens", 0)
                usage = TokenUsage(
                    prompt_tokens=in_tok,
                    completion_tokens=out_tok,
                    total_tokens=in_tok + out_tok,
                )

                return UnifiedResponse(
                    content=content,
                    provider="anthropic",
                    model=model,
                    usage=usage,
                    finish_reason=finish_reason,
                    latency_ms=latency,
                    raw_response=res_json,
                )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                error_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                error_msg = err_body
            raise RuntimeError(f"Anthropic API Error ({e.code}): {error_msg}") from e

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
            raise ValueError("Chưa cấu hình ANTHROPIC_API_KEY trong file .env!")

        max_tokens = max_tokens or 4096
        sys_text = system_prompt or ""
        filtered_messages = []
        for m in messages:
            if m.get("role") == "system":
                sys_text = (sys_text + "\n" + m.get("content", "")).strip()
            else:
                filtered_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        # 1. Thử Anthropic SDK streaming
        try:
            import anthropic
            client = anthropic.Anthropic(**self.config.get_client_kwargs())
            kwargs: Dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": filtered_messages,
            }
            if sys_text:
                kwargs["system"] = sys_text

            with client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text
            return
        except ImportError:
            pass

        # 2. Thử SSE streaming qua REST API
        base_url = (self.config.base_url or "https://api.anthropic.com").rstrip("/")
        url = f"{base_url}/v1/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
            "accept": "text/event-stream",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": filtered_messages,
            "stream": True,
        }
        if sys_text:
            payload["system"] = sys_text

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                for line_bytes in resp:
                    line = line_bytes.decode("utf-8").strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        try:
                            data_json = json.loads(data_str)
                            msg_type = data_json.get("type")
                            if msg_type == "content_block_delta":
                                delta = data_json.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                            elif msg_type == "message_stop":
                                break
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

    def generate_chat(self, model: str, prompt: str, max_tokens: int = 1024) -> str:
        """Hàm đơn giản tương thích ngược các script test."""
        resp = self.generate(model, [{"role": "user", "content": prompt}], max_tokens=max_tokens)
        return resp.content

