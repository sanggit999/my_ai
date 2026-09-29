# providers/__init__.py
from typing import Dict, Optional
from .base import BaseConfig, BaseProvider
from .openai import OpenAIConfig, OpenAIProvider
from .groq import GroqConfig, GroqProvider
from .gemini import GeminiConfig, GeminiProvider
from .anthropic import AnthropicConfig, AnthropicProvider


def get_all_provider_configs() -> Dict[str, BaseConfig]:
    """Khởi tạo và trả về instance cấu hình của tất cả các provider."""
    return {
        "openai": OpenAIConfig(),
        "groq": GroqConfig(),
        "gemini": GeminiConfig(),
        "anthropic": AnthropicConfig(),
    }


def get_available_provider_configs() -> Dict[str, BaseConfig]:
    """Chỉ trả về các provider đã được cấu hình API Key."""
    all_configs = get_all_provider_configs()
    return {name: cfg for name, cfg in all_configs.items() if cfg.is_configured}


def get_provider(name: str) -> Optional[BaseProvider]:
    """Factory lấy Provider instance theo tên."""
    name = name.lower().strip()
    if name == "openai":
        return OpenAIProvider()
    elif name == "groq":
        return GroqProvider()
    elif name == "gemini":
        return GeminiProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    return None


__all__ = [
    "BaseConfig",
    "BaseProvider",
    "OpenAIConfig",
    "OpenAIProvider",
    "GroqConfig",
    "GroqProvider",
    "GeminiConfig",
    "GeminiProvider",
    "AnthropicConfig",
    "AnthropicProvider",
    "get_all_provider_configs",
    "get_available_provider_configs",
    "get_provider",
]
