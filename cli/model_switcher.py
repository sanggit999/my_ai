"""Model Switcher CLI - Quản lý & Chuyển đổi Model cho từng API (Phase 9.1)."""

import sys
from typing import List, Dict, Optional

from config.active_models import (
    get_all_active_models,
    get_active_model,
    set_active_model,
    reset_to_defaults,
)
from providers import get_all_provider_configs, get_available_provider_configs, get_provider
from models.model_info import ModelInfo


def display_active_models_summary():
    """In bảng tổng quan model đang dùng cho từng provider."""
    active_map = get_all_active_models()
    configs = get_all_provider_configs()

    print("\n" + "=" * 80)
    print("  🔄 BẢNG MODEL ĐANG KÍCH HOẠT CHO TỪNG API (ACTIVE MODELS)")
    print("=" * 80)
    print(f"{'STT':<4} | {'PROVIDER':<12} | {'MODEL ĐANG KÍCH HOẠT':<32} | {'TRẠNG THÁI API'}")
    print("-" * 80)

    providers_list = ["groq", "gemini", "openai", "anthropic"]
    for idx, p in enumerate(providers_list, 1):
        cfg = configs.get(p)
        status = "✅ SẴN SÀNG" if (cfg and cfg.is_configured) else "⚠️ CHƯA CÓ KEY"
        curr_model = active_map.get(p, "default")
        print(f" {idx:<3} | {p.upper():<12} | {curr_model:<32} | {status}")
    print("=" * 80)


def switch_model_for_provider(provider_name: str):
    """Tải models động từ provider và cho phép người dùng chọn model mới."""
    provider = get_provider(provider_name)
    if not provider.is_ready:
        print(f"\n[!] Provider {provider_name.upper()} chưa được cấu hình API Key trong .env!")
        return

    current_model = get_active_model(provider_name)
    print(f"\n[+] Đang tải danh sách models từ {provider_name.upper()} API...")

    try:
        models: List[ModelInfo] = provider.get_models()
    except Exception as e:
        print(f"[X] Không thể lấy danh sách models từ {provider_name}: {e}")
        return

    if not models:
        print(f"[!] Không tìm thấy model nào khả dụng cho {provider_name}.")
        return

    print(f"[✓] Đã tải thành công {len(models)} models!")
    print(f"[*] Model hiện tại của {provider_name.upper()}: '{current_model}'")

    current_list = models
    while True:
        print("\n" + "-" * 80)
        print(f"DANH SÁCH MODELS CỦA {provider_name.upper()} (Đang hiển thị {len(current_list)}/{len(models)} models)")
        print("-" * 80)
        print(f"{'STT':<4} | {'MODEL ID':<36} | {'CONTEXT':<12} | {'HIỆN TẠI'}")
        print("-" * 80)

        for idx, m in enumerate(current_list[:15], 1):
            ctx = f"{m.input_token_limit:,}" if m.input_token_limit else "-"
            is_cur = "⭐ [ĐANG DÙNG]" if m.id == current_model else ""
            print(f"{idx:<4} | {m.id:<36} | {ctx:<12} | {is_cur}")

        if len(current_list) > 15:
            print(f"... và còn {len(current_list) - 15} model khác. Gõ /filter <từ khóa> để lọc.")

        print("-" * 80)
        print("Lựa chọn: Nhập số thứ tự để CHỌN | Gõ /filter <từ khóa> để LỌC | 0 để QUAY LẠI")

        try:
            cmd = input("👉 Nhập lựa chọn của bạn: ").strip()
            if cmd in ("0", "exit", "quit"):
                break

            if cmd.startswith("/filter "):
                kw = cmd.replace("/filter ", "").strip().lower()
                current_list = [m for m in models if kw in m.id.lower() or kw in m.display_name.lower()]
                if not current_list:
                    print(f"[!] Không tìm thấy model nào khớp với '{kw}'. Khôi phục danh sách đầy đủ.")
                    current_list = models
                continue

            if cmd.isdigit() and 1 <= int(cmd) <= len(current_list):
                chosen = current_list[int(cmd) - 1]
                set_active_model(provider_name, chosen.id)
                print(f"\n[✓] THÀNH CÔNG: Đã chuyển đổi model của {provider_name.upper()} thành: '{chosen.id}'!")
                print(f"[i] Cấu hình mới đã được lưu vĩnh viễn vào config/active_models.json.")
                break

            # Nếu gõ khớp trực tiếp tên model
            matches = [m for m in models if cmd.lower() in m.id.lower()]
            if len(matches) == 1:
                chosen = matches[0]
                set_active_model(provider_name, chosen.id)
                print(f"\n[✓] THÀNH CÔNG: Đã chuyển đổi model của {provider_name.upper()} thành: '{chosen.id}'!")
                break
            elif len(matches) > 1:
                current_list = matches
                continue

            print("[!] Lựa chọn không hợp lệ, vui lòng thử lại.")
        except (KeyboardInterrupt, EOFError):
            print("\nĐã hủy.")
            break


def run_model_switcher_menu():
    """Vòng lặp menu quản lý chuyển đổi model."""
    provider_keys = ["groq", "gemini", "openai", "anthropic"]

    while True:
        display_active_models_summary()
        print("\nTÙY CHỌN:")
        for idx, p in enumerate(provider_keys, 1):
            print(f"  {idx}. Đổi Model cho {p.upper()}")
        print("  R. Khôi phục tất cả về Model mặc định tối ưu ban đầu")
        print("  0. Quay lại Menu Chính")
        print("-" * 50)

        try:
            choice = input("👉 Chọn Provider cần đổi Model (1-4, R hoặc 0): ").strip()
            if choice in ("0", "exit", "quit"):
                break
            elif choice.lower() == "r":
                reset_to_defaults()
                print("\n[✓] Đã khôi phục toàn bộ Model về mặc định ban đầu!")
            elif choice.isdigit() and 1 <= int(choice) <= len(provider_keys):
                selected_p = provider_keys[int(choice) - 1]
                switch_model_for_provider(selected_p)
            else:
                print("[!] Lựa chọn không hợp lệ, vui lòng thử lại.")
        except (KeyboardInterrupt, EOFError):
            print("\nĐã quay lại.")
            break
