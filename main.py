"""Multi-AI Python Tool - Main Entry Point (Phases 1 - 7).

Hệ thống AI đa nhà cung cấp (OpenAI, Groq, Google Gemini, Anthropic Claude):
- Phase 1: Quản lý cấu hình và bảo mật API Key riêng biệt theo từng thư mục.
- Phase 2: Khám phá Catalog Model động không hardcode (`list_models`).
- Phase 3: Chuẩn hóa siêu dữ liệu mô hình (`ModelInfo` schema).
- Phase 4: Menu điều hướng tương tác lựa chọn Provider -> Model (hỗ trợ lọc/tìm kiếm).
- Phase 5: Sinh phản hồi Streaming thời gian thực (`generate_stream`).
- Phase 6: Chuẩn hóa phản hồi đầu ra (`UnifiedResponse`, TokenUsage, Latency).
- Phase 7: Quản lý hội thoại đa lượt (`ChatSession`, sliding window context, lưu/tải JSON).
"""

import sys
from pathlib import Path

# Đảm bảo console Windows in đúng tiếng Việt UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm thư mục gốc vào sys.path để import tương đối an toàn
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.env_loader import load_env_files
from providers import get_all_provider_configs, get_available_provider_configs


def print_banner():
    print("=" * 75)
    print("      🌟 MULTI-AI PYTHON CLI & SDK — UNIFIED MULTI-PROVIDER SYSTEM 🌟")
    print("        OpenAI • Groq (LPU) • Google Gemini • Anthropic Claude")
    print("=" * 75)


def check_and_display_status():
    env_file = load_env_files()
    print(f"\n[*] Đường dẫn file .env: {env_file}")
    print(f"[*] Trạng thái file .env: {'TỒN TẠI' if env_file.exists() else 'CHƯA TẠO'}\n")

    configs = get_all_provider_configs()
    available = get_available_provider_configs()

    print(f"{'PROVIDER':<15} | {'TRẠNG THÁI':<15} | {'API KEY MASKED':<20} | {'GHI CHÚ'}")
    print("-" * 75)

    for name, cfg in configs.items():
        is_ready = cfg.is_configured
        status_text = "[ READY ]" if is_ready else "[ MISSING ]"
        masked = cfg.masked_key
        is_valid, msg = cfg.validate()

        print(f"{name.upper():<15} | {status_text:<15} | {masked:<20} | {msg}")

    print("-" * 75)
    ready_names = [n.upper() for n in available.keys()]
    if ready_names:
        print(f"[+] Các Provider đã sẵn sàng hoạt động ({len(ready_names)}): {', '.join(ready_names)}")
    else:
        print("[!] Hiện tại chưa có API Key nào được cấu hình.")
        print("    Vui lòng mở file .env hoặc chọn mục (4) để nhập API Key.")

    print("=" * 75)
    return len(available) > 0


def prompt_set_key():
    from config.env_loader import save_env_var
    print("\n" + "-" * 75)
    print("THIẾT LẬP / CẬP NHẬT API KEY:")
    print("1. OpenAI Official (OPENAI_API_KEY)")
    print("2. Groq LPU / OpenAI-Compatible (GROQ_API_KEY)")
    print("3. Google Gemini (GEMINI_API_KEY)")
    print("4. Anthropic Claude (ANTHROPIC_API_KEY)")
    print("0. Quay lại")
    print("-" * 75)

    choice = input("Chọn provider muốn nhập key (1-4, hoặc 0): ").strip()
    key_map = {
        "1": ("OPENAI_API_KEY", "sk-..."),
        "2": ("GROQ_API_KEY", "gsk_..."),
        "3": ("GEMINI_API_KEY", "AIzaSy..."),
        "4": ("ANTHROPIC_API_KEY", "sk-ant-..."),
    }
    if choice not in key_map:
        return

    var_name, hint = key_map[choice]
    val = input(f"👉 Nhập {var_name} ({hint}): ").strip()
    if val:
        save_env_var(var_name, val)
        print(f"[✓] Đã lưu {var_name} thành công vào file .env!")
    else:
        print("[!] Không có key nào được nhập.")


def start_interactive_chat():
    """Khởi động luồng Chat tương tác Phases 4 -> 5 -> 6 -> 7."""
    from cli.selector import CLISelector
    from cli.chat_loop import ChatLoop

    res = CLISelector.select_provider()
    if not res:
        return
    p_name, provider = res

    selected_model = CLISelector.select_model(provider)
    if not selected_model:
        return

    chat = ChatLoop(provider=provider, model_info=selected_model)
    chat.run()


def start_orchestrator_synthesis():
    """Khởi động luồng Multi-Model Orchestration & Synthesis (Phase 8)."""
    from cli.orchestrator_view import run_synthesis_interactive
    run_synthesis_interactive()


def start_role_orchestration():
    """Khởi động luồng Multi-Persona Role Orchestration & Pipeline (Phase 9)."""
    from cli.role_orchestrator_view import run_role_orchestration_menu
    run_role_orchestration_menu()


def start_model_switcher():
    """Khởi động trình quản lý & chuyển đổi model cho từng API (Phase 9.1)."""
    from cli.model_switcher import run_model_switcher_menu
    run_model_switcher_menu()


def start_three_stage_pipeline():
    """Khởi động Dây Chuyền 3 Chặng ĐẦU ➔ THÂN ➔ CUỐI Tự Phục Hồi (Phase 10)."""
    from cli.pipeline_view import pipeline_loop
    pipeline_loop()


def run_phase3_inspection():
    """Chạy kiểm tra và so sánh chuẩn hóa ModelInfo (Phase 3)."""
    from test_model_info import main as test_p3
    test_p3()


if __name__ == "__main__":
    print_banner()
    load_env_files()
    check_and_display_status()

    while True:
        try:
            print("\n" + "═" * 60)
            print("          BẢNG ĐIỀU KHIỂN CHÍNH (MAIN MENU)")
            print("═" * 60)
            print("  1. 🚀 Chat Đơn Lẻ với 1 Model (Phases 4, 5, 6, 7)")
            print("  2. 🧠 Multi-Model Orchestration & Synthesis (Phase 8)")
            print("  3. 🎭 Multi-Persona Role Orchestration & Pipeline (Phase 9)")
            print("  4. 🔄 Quản Lý & Chuyển Đổi Model Cho Từng API (Phase 9.1)")
            print("  5. ⛓️ Dây Chuyền 3 Chặng ĐẦU ➔ THÂN ➔ CUỐI (Tự Phục Hồi - Phase 10)")
            print("  6. 📋 So sánh Model Catalog chuẩn hóa (Phase 3)")
            print("  7. 🔍 Kiểm tra trạng thái các Provider & Keys (Phase 1)")
            print("  8. 🔑 Nhập / Cập nhật API Key trực tiếp")
            print("  9. ⚡ Test Groq Models & Chat (OpenAI-compatible / Free)")
            print(" 10. 🌟 Test Google Gemini Models & Chat")
            print(" 11. 🧠 Test OpenAI Official Models")
            print(" 12. 🎭 Test Anthropic Claude Models")
            print("  0. 🚪 Thoát")
            print("═" * 60)
            opt = input("👉 Nhập lựa chọn của bạn (0-12): ").strip()

            if opt == "1":
                start_interactive_chat()
            elif opt == "2":
                start_orchestrator_synthesis()
            elif opt == "3":
                start_role_orchestration()
            elif opt == "4":
                start_model_switcher()
            elif opt == "5":
                start_three_stage_pipeline()
            elif opt == "6":
                run_phase3_inspection()
            elif opt == "7":
                check_and_display_status()
            elif opt == "8":
                prompt_set_key()
                check_and_display_status()
            elif opt == "9":
                from test_groq_models import main as run_groq_test
                run_groq_test()
            elif opt == "10":
                from test_gemini_models import main as run_gemini_test
                run_gemini_test()
            elif opt == "11":
                from test_openai_models import main as run_openai_test
                run_openai_test()
            elif opt == "12":
                from test_anthropic_models import main as run_anthropic_test
                run_anthropic_test()
            elif opt in ("0", "exit", "quit"):
                print("\n[✓] Tạm biệt!")
                break
            else:
                print("[!] Lựa chọn không hợp lệ, vui lòng chọn lại.")
        except (KeyboardInterrupt, EOFError):
            print("\n\n[✓] Đã thoát chương trình.")
            break



