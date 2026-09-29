"""Groq Configuration Module.

Groq cung cấp API tương thích 100% với OpenAI API (OpenAI-compatible) với tốc độ siêu nhanh (LPU).
Đăng ký nhận API key miễn phí tại: https://console.groq.com/keys
"""

import os
from typing import Optional, Tuple, Dict, Any
from providers.base import BaseConfig


class GroqConfig(BaseConfig):
    """Quản lý cấu hình và API Key riêng biệt cho Groq (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self._api_key = api_key or os.getenv("GROQ_API_KEY")
        # Mặc định sử dụng endpoint OpenAI-compatible của Groq
        self._base_url = base_url or os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def base_url(self) -> str:
        return self._base_url

    def validate(self) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Thiếu biến môi trường GROQ_API_KEY."

        key = (self._api_key or "").strip()
        # Groq API key chuẩn luôn bắt đầu bằng 'gsk_'
        if not key.startswith("gsk_"):
            return False, "Định dạng GROQ_API_KEY có vẻ không hợp lệ (thường bắt đầu bằng 'gsk_')."

        return True, "API Key hợp lệ và sẵn sàng."

    def get_client_kwargs(self) -> Dict[str, Any]:
        """Trả về dictionary tham số cho client (groq.Groq hoặc openai.OpenAI)."""
        return {
            "api_key": self._api_key,
            "base_url": self._base_url,
        }
