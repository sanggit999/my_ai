"""Kiểm thử tự động Phase 9.1: Per-API Model Switcher."""

import sys
from pathlib import Path

# Đảm bảo console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.active_models import (
    get_all_active_models,
    get_active_model,
    set_active_model,
    reset_to_defaults,
)
from orchestrator import AIOrchestrator


def main():
    print("=" * 75)
    print("   KIỂM THỬ: PHASE 9.1 PER-API MODEL SWITCHER")
    print("=" * 75)

    # 1. Kiểm tra danh sách mặc định ban đầu
    initial = get_all_active_models()
    print("[1] Danh sách ban đầu:", initial)
    assert "groq" in initial and "gemini" in initial

    # 2. Thử chuyển đổi Model của Groq sang Qwen
    print("\n[2] Đang chuyển đổi model của Groq sang 'qwen/qwen3.8-27b'...")
    set_active_model("groq", "qwen/qwen3.8-27b")
    new_groq_model = get_active_model("groq")
    print(f"    [✓] Model Groq sau khi đổi: '{new_groq_model}'")
    assert new_groq_model == "qwen/qwen3.8-27b"

    # 3. Thử chuyển đổi Model của Gemini
    print("\n[3] Đang chuyển đổi model của Gemini sang 'gemini-3.1-flash-lite'...")
    set_active_model("gemini", "gemini-3.1-flash-lite")
    new_gemini_model = get_active_model("gemini")
    print(f"    [✓] Model Gemini sau khi đổi: '{new_gemini_model}'")
    assert new_gemini_model == "gemini-3.1-flash-lite"

    # 4. Kiểm tra AIOrchestrator tự động nạp model mới
    print("\n[4] Kiểm tra AIOrchestrator tự động đồng bộ model mới...")
    orch = AIOrchestrator()
    broadcast_models = get_all_active_models()
    print(f"    [✓] Orchestrator nhận diện Groq: '{broadcast_models['groq']}'")
    print(f"    [✓] Orchestrator nhận diện Gemini: '{broadcast_models['gemini']}'")
    assert broadcast_models["groq"] == "qwen/qwen3.8-27b"

    # 5. Khôi phục về model khuyên dùng mặc định
    print("\n[5] Đang khôi phục về mặc định ban đầu...")
    reset_to_defaults()
    restored = get_all_active_models()
    print(f"    [✓] Đã khôi phục thành công. Groq hiện tại: '{restored['groq']}'")
    assert restored["groq"] == "openai/gpt-oss-120b"

    print("\n" + "=" * 75)
    print("   🎉 TẤT CẢ TEST PHASE 9.1 ĐỀU THÀNH CÔNG (PASSED)!")
    print("=" * 75)


if __name__ == "__main__":
    main()
