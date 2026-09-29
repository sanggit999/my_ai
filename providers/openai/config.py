"""OpenAI Configuration Module."""

import os
from typing import Optional, Tuple, Dict, Any
from providers.base import BaseConfig


class OpenAIConfig(BaseConfig):
    """Quản lý cấu hình và API Key riêng biệt cho OpenAI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        project: Optional[str] = None
    ):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self._organization = organization or os.getenv("OPENAI_ORG_ID")
        self._project = project or os.getenv("OPENAI_PROJECT_ID")

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    @property
    def organization(self) -> Optional[str]:
        return self._organization

    @property
    def project(self) -> Optional[str]:
        return self._project

    def validate(self) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Thiếu biến môi trường OPENAI_API_KEY."

        key = (self._api_key or "").strip()
        if not (key.startswith("sk-") or key.startswith("sess-")):
            return False, "Định dạng OPENAI_API_KEY có vẻ không hợp lệ (thường bắt đầu bằng 'sk-')."

        return True, "API Key hợp lệ và sẵn sàng."

    def get_client_kwargs(self) -> Dict[str, Any]:
        """Trả về dictionary tham số để truyền vào OpenAI() client SDK."""
        kwargs: Dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        if self._organization:
            kwargs["organization"] = self._organization
        if self._project:
            kwargs["project"] = self._project
        return kwargs
