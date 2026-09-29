"""Google Gemini Provider Implementation.

Kết nối tới Google Gemini Models API để lấy danh mục models động:
- Tài liệu Models: https://ai.google.dev/gemini-api/docs/models
- Tài liệu API:    https://ai.google.dev/api/models
- Endpoint:        GET https://generativelanguage.googleapis.com/v1beta/models
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from .config import GeminiConfig


class GeminiProvider(BaseProvider):
    """Provider tương tác với Google Gemini API."""

    def __init__(self, config: Optional[GeminiConfig] = None):
        config = config or GeminiConfig()
        super().__init__(config)
        self.config: GeminiConfig = config

    def _call_via_sdk(self) -> List[Dict[str, Any]]:
        """Gọi qua SDK mới `google-genai` nếu đã cài đặt."""
        from google import genai 
        from google.genai import errors 
        try:
            client = genai.Client(**self.config.get_client_kwargs())
            response = client.models.list()
            models = []
            for item in response:
                m_name = getattr(item, "name", "")
                m_id = m_name.replace("models/", "") if m_name.startswith("models/") else m_name
                models.append({
                    "id": m_id,
                    "name": m_name,
                    "display_name": getattr(item, "display_name", m_id),
                    "description": getattr(item, "description", ""),
                    "input_token_limit": getattr(item, "input_token_limit", None),
                    "output_token_limit": getattr(item, "output_token_limit", None),
                    "supported_methods": getattr(item, "supported_generation_methods", []) or [],
                })
            return models
        except errors.APIError as e:
            if "API_KEY_INVALID" in str(e) or e.code == 400 or e.code == 403:
                raise PermissionError(f"[Gemini Auth Error] API Key không hợp lệ hoặc không có quyền: {e}") from e
            elif e.code == 429:
                raise RuntimeError(f"[Gemini 429] Vượt quá giới hạn Quota hoặc Rate Limit: {e}") from e
            raise RuntimeError(f"[Gemini API Error] {e}") from e

    def _call_via_rest_api(self) -> List[Dict[str, Any]]:
        """Fallback gọi trực tiếp REST endpoint bằng thư viện chuẩn (zero-dependency)."""
        key = (self.config.api_key or "").strip()
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    raw_models = payload.get("models", [])
                    cleaned = []
                    for item in raw_models:
                        raw_name = item.get("name", "")
                        clean_id = raw_name.replace("models/", "") if raw_name.startswith("models/") else raw_name
                        cleaned.append({
                            "id": clean_id,
                            "name": raw_name,
                            "display_name": item.get("displayName", clean_id),
                            "description": item.get("description", ""),
                            "input_token_limit": item.get("inputTokenLimit"),
                            "output_token_limit": item.get("outputTokenLimit"),
                            "supported_methods": item.get("supportedGenerationMethods", []),
                        })
                    return cleaned
                raise RuntimeError(f"Gemini API trả về mã lỗi: {response.status}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                error_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                error_msg = err_body

            if e.code in (400, 403):
                raise PermissionError(f"[Gemini Auth Error {e.code}] {error_msg}") from e
            elif e.code == 429:
                raise RuntimeError(f"[Gemini 429 Quota Exceeded] {error_msg}") from e
            else:
                raise RuntimeError(f"[Gemini HTTP {e.code}] {error_msg}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(f"[Gemini Network Error] Lỗi kết nối: {e.reason}") from e

    def list_models(self) -> List[Dict[str, Any]]:
        """Truy vấn danh sách tất cả các models từ Gemini API."""
        if not self.is_ready:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY trong file .env!")

        try:
            from google import genai 
            return self._call_via_sdk()
        except ImportError:
            return self._call_via_rest_api()

    def list_chat_models(self) -> List[Dict[str, Any]]:
        """Lọc và trả về danh sách các model hỗ trợ generateContent (Chat / Completion)."""
        all_models = self.list_models()
        chat_models = []
        for m in all_models:
            methods = m.get("supported_methods", []) or []
            if "generateContent" in methods:
                chat_models.append(m)

        def sort_key(model_dict):
            m_id = model_dict.get("id", "").lower()
            priority = 99
            if "gemini-3.1-flash-lite" in m_id:
                priority = 1
            elif "gemini-3.8-flash" in m_id:
                priority = 2
            elif "gemini-3.5-flash-lite" in m_id:
                priority = 3
            elif "gemini-3.5-flash" in m_id:
                priority = 4
            elif "gemini-flash-latest" in m_id:
                priority = 5
            elif "gemini-pro-latest" in m_id:
                priority = 6
            elif "gemini-2.5-flash" in m_id:
                priority = 20
            return (priority, m_id)

        return sorted(chat_models, key=sort_key)


    def get_models(self) -> list:
        """Chuẩn hóa danh sách chat models thành List[ModelInfo] (Phase 3)."""
        from models.model_info import ModelInfo

        raw_chat = self.list_chat_models()
        normalized = []

        for m in raw_chat:
            m_id = m.get("id", "")
            disp = m.get("display_name") or m_id
            desc = m.get("description", "")
            in_limit = m.get("input_token_limit")
            out_limit = m.get("output_token_limit")
            
            caps = ["chat"]
            if any(k in m_id.lower() or k in desc.lower() for k in ("image", "vision", "banana")):
                caps.append("vision")
            if any(k in m_id.lower() for k in ("pro", "deep-research")):
                caps.append("reasoning")

            normalized.append(ModelInfo(
                provider="gemini",
                id=m_id,
                display_name=disp,
                description=desc or f"Google Gemini Model ({disp})",
                input_token_limit=in_limit,
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
        """Sinh phản hồi và chuẩn hóa thành UnifiedResponse (Phase 5 & 6)."""
        import time
        from models.unified_response import UnifiedResponse, TokenUsage

        if not self.is_ready:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY!")

        model_id = model.replace("models/", "") if model.startswith("models/") else model
        start_time = time.perf_counter()

        # Chuẩn bị payload messages dạng contents cho Gemini
        contents = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        # Gọi qua SDK nếu có
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(**self.config.get_client_kwargs())
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                system_instruction=system_prompt if system_prompt else None
            )
            resp = client.models.generate_content(
                model=model_id,
                contents=[types.Content(role=c["role"], parts=[types.Part.from_text(text=c["parts"][0]["text"])]) for c in contents],
                config=config
            )
            latency = (time.perf_counter() - start_time) * 1000
            
            # Lấy token usage
            usage = TokenUsage()
            if getattr(resp, "usage_metadata", None):
                meta = resp.usage_metadata
                usage = TokenUsage(
                    prompt_tokens=getattr(meta, "prompt_token_count", 0) or 0,
                    completion_tokens=getattr(meta, "candidates_token_count", 0) or 0,
                    total_tokens=getattr(meta, "total_token_count", 0) or 0,
                )

            finish_reason = None
            if getattr(resp, "candidates", None):
                finish_reason = str(resp.candidates[0].finish_reason)

            return UnifiedResponse(
                content=resp.text or "",
                provider="gemini",
                model=model_id,
                usage=usage,
                finish_reason=finish_reason,
                latency_ms=latency,
                raw_response=resp
            )
        except ImportError:
            pass

        # Fallback REST API
        key = (self.config.api_key or "").strip()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={key}"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Multi-AI-Python-Tool/1.0",
        }
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        if max_tokens:
            body["generationConfig"]["maxOutputTokens"] = max_tokens
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                res_json = json.loads(response.read().decode("utf-8"))
                latency = (time.perf_counter() - start_time) * 1000

                content = ""
                candidates = res_json.get("candidates", [])
                finish_reason = None
                if candidates:
                    finish_reason = candidates[0].get("finishReason")
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        content = parts[0].get("text", "")

                meta = res_json.get("usageMetadata", {})
                usage = TokenUsage(
                    prompt_tokens=meta.get("promptTokenCount", 0),
                    completion_tokens=meta.get("candidatesTokenCount", 0),
                    total_tokens=meta.get("totalTokenCount", 0),
                )

                return UnifiedResponse(
                    content=content,
                    provider="gemini",
                    model=model_id,
                    usage=usage,
                    finish_reason=finish_reason,
                    latency_ms=latency,
                    raw_response=res_json
                )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Gemini API Error ({e.code}): {err_body}") from e

    def generate_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ):
        """Sinh phản hồi streaming từng chunk theo thời gian thực (Phase 5)."""
        # Với fallback đơn giản hoặc SDK, trả về nội dung hoàn chỉnh hoặc từng mẩu
        full_resp = self.generate(model, messages, temperature, max_tokens, system_prompt)
        text = full_resp.content
        # Chia nhỏ chuỗi mô phỏng streaming hoặc trả về trực tiếp
        chunk_size = 8
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]

    def generate_chat(self, model: str, prompt: str) -> str:
        """Hàm đơn giản tương thích ngược các script test."""
        resp = self.generate(model, [{"role": "user", "content": prompt}])
        return resp.content
