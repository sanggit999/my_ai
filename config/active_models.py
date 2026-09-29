"""Active Models Manager - Quản lý và lưu trữ model đang dùng cho từng API (Phase 9.1)."""

import json
from pathlib import Path
from typing import Dict, Optional

CONFIG_FILE = Path(__file__).resolve().parent / "active_models.json"

DEFAULT_ACTIVE_MODELS: Dict[str, str] = {
    "groq": "openai/gpt-oss-120b",
    "gemini": "gemini-3.1-flash-lite",
    "openai": "gpt-4o",
    "anthropic": "claude-3-7-sonnet-20250219",
}


def get_all_active_models() -> Dict[str, str]:
    """Lấy danh sách model đang kích hoạt cho tất cả các provider."""
    models = dict(DEFAULT_ACTIVE_MODELS)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    models.update(saved)
        except Exception:
            pass
    return models


def get_active_model(provider_name: str) -> str:
    """Lấy model đang kích hoạt của một provider cụ thể."""
    all_models = get_all_active_models()
    return all_models.get(provider_name.lower(), DEFAULT_ACTIVE_MODELS.get(provider_name.lower(), "default"))


def set_active_model(provider_name: str, model_id: str) -> None:
    """Lưu model kích hoạt mới cho một provider."""
    current = get_all_active_models()
    current[provider_name.lower()] = model_id

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise IOError(f"Không thể lưu file {CONFIG_FILE}: {e}") from e


def reset_to_defaults() -> Dict[str, str]:
    """Khôi phục danh sách model về mặc định ban đầu."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_ACTIVE_MODELS, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return dict(DEFAULT_ACTIVE_MODELS)
