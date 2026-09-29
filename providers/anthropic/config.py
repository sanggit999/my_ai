"""Anthropic Claude Configuration Module."""

import os
from typing import Optional, Tuple, Dict, Any
from providers.base import BaseConfig


class AnthropicConfig(BaseConfig):
    """Quản lý cấu hình và API Key riêng biệt cho Anthropic Claude."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    def validate(self) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Thiếu biến môi trường ANTHROPIC_API_KEY."

        key = (self._api_key or "").strip()
        # Anthropic API key thường bắt đầu bằng 'sk-ant-'
        if not key.startswith("sk-ant-"):
            return False, "Định dạng ANTHROPIC_API_KEY có vẻ không hợp lệ (thường bắt đầu bằng 'sk-ant-')."

        return True, "API Key hợp lệ và sẵn sàng."

    def get_client_kwargs(self) -> Dict[str, Any]:
        """Trả về dictionary tham số để truyền vào anthropic.Anthropic()."""
        kwargs: Dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return kwargs
