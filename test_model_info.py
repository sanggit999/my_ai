"""Test Script - Phase 3: Chuẩn hóa ModelInfo Data Model

Chạy script này để kiểm tra ModelInfo chuẩn hóa từ tất cả các provider đã có API key:
    python test_model_info.py
"""

import sys
from pathlib import Path

# Đảm bảo console Windows hiển thị đúng UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.env_loader import load_env_files
from providers import get_all_provider_configs, get_provider
from models.model_info import ModelInfo


def main():
    print("=" * 80)
    print("       TEST PHASE 3: CHUẨN HÓA MODELINFO DATA MODEL TẤT CẢ PROVIDER")
    print("=" * 80)

    load_env_files()
    all_configs = get_all_provider_configs()

    total_normalized = 0

    for name, cfg in all_configs.items():
        print(f"\n[+] Đang tải và chuẩn hóa models từ Provider: {name.upper()}...")
        if not cfg.is_configured:
            print(f"    [-] Bỏ qua (Chưa có API Key).")
            continue

        provider = get_provider(name)
        if not provider:
            print(f"    [-] Chưa khởi tạo được provider.")
            continue

        try:
            models: list[ModelInfo] = provider.get_models()
            print(f"    [✓] Đã chuẩn hóa {len(models)} models thành ModelInfo object!")
            total_normalized += len(models)

            # In 3 model tiêu biểu nhất của provider đó
            print(f"    {'PROVIDER':<10} | {'MODEL ID':<32} | {'CONTEXT':<12} | {'CAPABILITIES'}")
            print("    " + "-" * 76)
            for m in models[:4]:
                ctx = f"{m.input_token_limit:,}" if m.input_token_limit else "-"
                caps = ", ".join(m.capabilities)
                print(f"    {m.provider.upper():<10} | {m.id:<32} | {ctx:<12} | {caps}")

        except Exception as e:
            print(f"    [X] Lỗi khi lấy models: {e}")

    print("\n" + "=" * 80)
    print(f"[✓] TỔNG CỘNG ĐÃ CHUẨN HÓA: {total_normalized} ModelInfo objects xuyên suốt các Provider!")
    print("=" * 80)


if __name__ == "__main__":
    main()
