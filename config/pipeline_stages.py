"""Pipeline Stages Config - Quản lý cấu hình dây chuyền ĐẦU - THÂN - CUỐI (Phase 10)."""

import json
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE = Path(__file__).resolve().parent / "pipeline_stages.json"

DEFAULT_STAGES_CONFIG: Dict[str, Dict[str, str]] = {
    "head": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "role": "Planner & Architect",
        "prompt_template": (
            "Bạn là Software Architect và Chuyên gia Lập Kế Hoạch. Với yêu cầu sau: '{input}', "
            "hãy phân tích kỹ lưỡng, bóc tách các yêu cầu cốt lõi và lập đề cương/dàn ý kiến trúc kỹ thuật chuẩn xác, "
            "rõ ràng từng phần để Chặng tiếp theo triển khai code/nội dung."
        ),
    },
    "body": {
        "provider": "gemini",
        "model": "gemini-3.1-flash-lite",
        "role": "Core Implementer",
        "prompt_template": (
            "Dựa trên dàn ý kiến trúc từ Chặng ĐẦU sau:\n{previous_output}\n\n"
            "và yêu cầu gốc: '{input}', bạn là Kỹ Sư Cốt Lõi (Core Implementer). Hãy triển khai toàn bộ giải pháp chi tiết, "
            "viết mã nguồn hoàn chỉnh chuẩn công nghiệp (có xử lý ngoại lệ, chú thích) hoặc nội dung chuyên sâu nhất."
        ),
    },
    "tail": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "role": "Auditor & Polisher",
        "prompt_template": (
            "Bạn là Senior Code Reviewer & Quality Auditor. Hãy đọc toàn bộ bản thảo từ Chặng THÂN sau:\n{previous_output}\n\n"
            "1. Kiểm toán rà soát lỗi logic, lỗ hổng bảo mật, bắt các edge cases tiềm tàng.\n"
            "2. Tối ưu hiệu năng và trau chuốt xuất bản phiên bản hoàn hảo, sắc sảo nhất với định dạng Markdown chuyên nghiệp."
        ),
    },
}


def get_pipeline_stages() -> Dict[str, Dict[str, str]]:
    """Đọc cấu hình 3 chặng từ file JSON hoặc dùng mặc định."""
    config = dict(DEFAULT_STAGES_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    for k in ("head", "body", "tail"):
                        if k in saved:
                            config[k] = saved[k]
        except Exception:
            pass
    return config


def set_stage_config(stage_key: str, provider: str, model: str) -> None:
    """Cập nhật provider và model cho một chặng ('head', 'body', hoặc 'tail')."""
    stages = get_pipeline_stages()
    if stage_key in stages:
        stages[stage_key]["provider"] = provider
        stages[stage_key]["model"] = model

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(stages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise IOError(f"Không thể lưu file {CONFIG_FILE}: {e}") from e


def reset_pipeline_stages() -> Dict[str, Dict[str, str]]:
    """Khôi phục cấu hình 3 chặng về mặc định ban đầu."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_STAGES_CONFIG, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return dict(DEFAULT_STAGES_CONFIG)
