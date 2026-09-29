"""Base interface cho Configuration và Provider."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any


class BaseConfig(ABC):
    """Abstract Base Class cho cấu hình của từng Provider / API Key."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Tên định danh provider (ví dụ: 'openai', 'gemini', 'anthropic')."""
        pass

    @property
    @abstractmethod
    def api_key(self) -> Optional[str]:
        """API Key của provider."""
        pass

    @property
    def is_configured(self) -> bool:
        """Kiểm tra API Key đã được nhập hay chưa."""
        key = self.api_key
        return bool(key and key.strip() and not key.strip().startswith("<") and not key.strip() == "sk-...")

    @property
    def masked_key(self) -> str:
        """Che bớt ký tự API Key để hiển thị an toàn trên màn hình."""
        key = self.api_key
        if not self.is_configured or not key:
            return "<Chưa cấu hình>"
        key = key.strip()
        if len(key) <= 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"

    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """Kiểm tra tính hợp lệ cú pháp của cấu hình.
        
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        pass

    def get_status_info(self) -> Dict[str, Any]:
        """Lấy thông tin tóm tắt cấu hình của provider."""
        is_valid, msg = self.validate()
        return {
            "provider": self.provider_name,
            "configured": self.is_configured,
            "masked_key": self.masked_key,
            "is_valid": is_valid,
            "status_message": msg,
        }


class BaseProvider(ABC):
    """Abstract Base Class cho các Provider xử lý API."""

    def __init__(self, config: BaseConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.provider_name

    @property
    def is_ready(self) -> bool:
        return self.config.is_configured

    @abstractmethod
    def list_models(self) -> list[Dict[str, Any]]:
        """Gọi API của provider và trả về danh sách model thô từ API."""
        pass

    @abstractmethod
    def get_models(self) -> list[Any]:
        """Gọi API của provider và chuẩn hóa thành danh sách List[ModelInfo]."""
        pass

    @abstractmethod
    def generate(
        self,
        model: str,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Any:
        """Sinh phản hồi đầy đủ và chuẩn hóa thành UnifiedResponse (Phase 5 & 6)."""
        pass

    @abstractmethod
    def generate_stream(
        self,
        model: str,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ):
        """Sinh phản hồi streaming từng chunk theo thời gian thực (Phase 5)."""
        pass
