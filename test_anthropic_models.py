"""Test Script - Phase 2: Anthropic Claude Models API

Chạy script này để kiểm tra kết nối API tới Anthropic Claude:
    python test_anthropic_models.py
Hoặc truyền trực tiếp key:
    python test_anthropic_models.py --key sk-ant-...
"""

import sys
import argparse
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

from config.env_loader import load_env_files, save_env_var
from providers.anthropic import AnthropicConfig, AnthropicProvider


def prompt_for_api_key() -> str:
    """Cho phép người dùng nhập trực tiếp Anthropic API Key từ bàn phím."""
    print("\n" + "-" * 70)
    print("NHẬP ANTHROPIC CLAUDE API KEY TRỰC TIẾP")
    print("Lấy key tại: https://console.anthropic.com/settings/keys")
    print("-" * 70)

    try:
        entered_key = input("👉 Nhập Anthropic API Key (sk-ant-...): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[!] Đã hủy thao tác nhập.")
        return ""

    if not entered_key:
        print("[!] Không có key nào được nhập.")
        return ""

    try:
        save_choice = input("💾 Bạn có muốn lưu key này vào file .env không? (Y/n): ").strip().lower()
        if save_choice in ("", "y", "yes"):
            save_env_var("ANTHROPIC_API_KEY", entered_key)
            print("[✓] Đã lưu ANTHROPIC_API_KEY vào file .env thành công!")
    except (KeyboardInterrupt, EOFError):
        pass

    return entered_key


def main():
    parser = argparse.ArgumentParser(description="Kiểm tra kết nối và lấy danh sách model từ Anthropic Claude API.")
    parser.add_argument("--key", "--api-key", dest="api_key", help="Anthropic API Key truyền qua dòng lệnh.")
    args = parser.parse_args()

    print("=" * 70)
    print("       TEST PHASE 2: ANTHROPIC CLAUDE DYNAMIC MODELS API")
    print("=" * 70)

    load_env_files()

    api_key = args.api_key
    config = AnthropicConfig(api_key=api_key) if api_key else AnthropicConfig()
    provider = AnthropicProvider(config)

    print(f"[*] Provider:        {provider.name.upper()} (Anthropic Claude)")
    print(f"[*] Trạng thái Key:  {'SẴN SÀNG' if provider.is_ready else 'CHƯA CÓ KEY'}")
    print(f"[*] Masked Key:      {provider.config.masked_key}")

    # Nếu chưa có key, hỏi người dùng nhập trực tiếp
    if not provider.is_ready:
        entered_key = prompt_for_api_key()
        if not entered_key:
            print("\n[!] Không thể tiếp tục kiểm tra vì chưa có Anthropic API Key.")
            print("=" * 70)
            return
        provider = AnthropicProvider(AnthropicConfig(api_key=entered_key))
        print(f"[*] Masked Key mới:  {provider.config.masked_key}")

    print("\n[+] Đang kết nối tới Anthropic Claude Models API...")
    try:
        chat_models = provider.list_chat_models()
        total_raw = len(provider.list_models())

        print(f"[✓] Kết nối thành công!")
        print(f"[*] Tổng số model trả về từ Anthropic API: {total_raw}")
        print(f"[*] Số model Claude được nhận diện:        {len(chat_models)}\n")

        header = f"{'STT':<4} | {'MODEL ID':<34} | {'DISPLAY NAME':<26} | {'CREATED AT'}"
        print(header)
        print("-" * len(header))
        for idx, m in enumerate(chat_models, 1):
            m_id = m.get("id", "")
            disp = m.get("display_name", "")[:26]
            created = str(m.get("created_at") or "-")[:10]
            print(f"{idx:<4} | {m_id:<34} | {disp:<26} | {created}")

        print("-" * len(header))

        # Tự động chọn model khả dụng để test chat
        candidate_priority = (
            "claude-3-5-haiku-latest",
            "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-latest",
            "claude-3-5-sonnet-20241022",
            "claude-3-7-sonnet-latest",
            "claude-3-7-sonnet-20250219",
            "claude-3-haiku-20240307",
        )
        chosen_model = chat_models[0].get("id") if chat_models else "claude-3-5-haiku-20241022"
        for cand in candidate_priority:
            if any(m.get("id") == cand for m in chat_models):
                chosen_model = cand
                break

        print(f"\n[+] Thử nghiệm Messages Generation với Claude (model: {chosen_model})...")
        sample_prompt = "Xin chào! Bạn là ai và có thể giúp gì cho tôi? Trả lời ngắn trong 1-2 câu."
        print(f"Prompt: \"{sample_prompt}\"\nPhản hồi từ Claude:")
        print("-" * 70)
        response_text = provider.generate_chat(chosen_model, sample_prompt)
        print(response_text)
        print("-" * 70)
        print("[✓] Hoàn thành test Phase 2 cho Anthropic Claude API!")

    except PermissionError as e:
        print(f"\n[X] LỖI XÁC THỰC (401): {e}")
        print("    -> Vui lòng kiểm tra lại tính chính xác của ANTHROPIC_API_KEY.")
    except RuntimeError as e:
        print(f"\n[X] LỖI HẠN MỨC HOẶC API (429): {e}")
    except ConnectionError as e:
        print(f"\n[X] LỖI KẾT NỐI MẠNG: {e}")
    except Exception as e:
        print(f"\n[X] LỖI KHÔNG XÁC ĐỊNH: {type(e).__name__} - {e}")

    print("=" * 70)


if __name__ == "__main__":
    main()
