"""Google Gemini Configuration Module."""

import os
from typing import Optional, Tuple, Dict, Any
from providers.base import BaseConfig


class GeminiConfig(BaseConfig):
    """Quản lý cấu hình và API Key riêng biệt cho Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        # Hỗ trợ cả GEMINI_API_KEY (chuẩn SDK mới) và GOOGLE_API_KEY (tương thích ngược)
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    def validate(self) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Thiếu biến môi trường GEMINI_API_KEY (hoặc GOOGLE_API_KEY)."

        key = (self._api_key or "").strip()
        # Chấp nhận format chuẩn AIza, AQ. hoặc độ dài >= 20 ký tự
        if len(key) < 20:
            return False, "Định dạng GEMINI_API_KEY quá ngắn hoặc không hợp lệ."

        return True, "API Key hợp lệ và sẵn sàng."

    def get_client_kwargs(self) -> Dict[str, Any]:
        """Trả về dictionary tham số để truyền vào google.genai.Client()."""
        return {"api_key": self._api_key}
