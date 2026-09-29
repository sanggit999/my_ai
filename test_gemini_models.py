"""Test Script - Phase 2: Google Gemini Models API

Chạy script này để kiểm tra kết nối API tới Gemini:
    python test_gemini_models.py
Hoặc truyền trực tiếp key:
    python test_gemini_models.py --key AIzaSy...
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
from providers.gemini import GeminiConfig, GeminiProvider


def prompt_for_api_key() -> str:
    """Cho phép người dùng nhập trực tiếp Gemini API Key từ bàn phím."""
    print("\n" + "-" * 70)
    print("NHẬP GOOGLE GEMINI API KEY TRỰC TIẾP")
    print("Lấy key miễn phí tại: https://aistudio.google.com/apikey")
    print("-" * 70)

    try:
        entered_key = input("👉 Nhập Gemini API Key (AIzaSy...): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[!] Đã hủy thao tác nhập.")
        return ""

    if not entered_key:
        print("[!] Không có key nào được nhập.")
        return ""

    try:
        save_choice = input("💾 Bạn có muốn lưu key này vào file .env không? (Y/n): ").strip().lower()
        if save_choice in ("", "y", "yes"):
            save_env_var("GEMINI_API_KEY", entered_key)
            print("[✓] Đã lưu GEMINI_API_KEY vào file .env thành công!")
    except (KeyboardInterrupt, EOFError):
        pass

    return entered_key


def main():
    parser = argparse.ArgumentParser(description="Kiểm tra kết nối và lấy danh sách model từ Google Gemini API.")
    parser.add_argument("--key", "--api-key", dest="api_key", help="Gemini API Key truyền qua dòng lệnh.")
    args = parser.parse_args()

    print("=" * 70)
    print("       TEST PHASE 2: GOOGLE GEMINI DYNAMIC MODELS API")
    print("=" * 70)

    load_env_files()

    api_key = args.api_key
    config = GeminiConfig(api_key=api_key) if api_key else GeminiConfig()
    provider = GeminiProvider(config)

    print(f"[*] Provider:        {provider.name.upper()} (Google DeepMind / AI Studio)")
    print(f"[*] Trạng thái Key:  {'SẴN SÀNG' if provider.is_ready else 'CHƯA CÓ KEY'}")
    print(f"[*] Masked Key:      {provider.config.masked_key}")

    # Nếu chưa có key, hỏi người dùng nhập trực tiếp
    if not provider.is_ready:
        entered_key = prompt_for_api_key()
        if not entered_key:
            print("\n[!] Không thể tiếp tục kiểm tra vì chưa có Gemini API Key.")
            print("=" * 70)
            return
        provider = GeminiProvider(GeminiConfig(api_key=entered_key))
        print(f"[*] Masked Key mới:  {provider.config.masked_key}")

    print("\n[+] Đang kết nối tới Google Gemini Models API...")
    try:
        chat_models = provider.list_chat_models()
        total_raw = len(provider.list_models())

        print(f"[✓] Kết nối thành công!")
        print(f"[*] Tổng số model trả về từ Gemini API: {total_raw}")
        print(f"[*] Số model hỗ trợ Chat (generateContent): {len(chat_models)}\n")

        header = f"{'STT':<4} | {'MODEL ID':<28} | {'DISPLAY NAME':<24} | {'INPUT TOKENS':<14} | {'OUTPUT'}"
        print(header)
        print("-" * len(header))
        for idx, m in enumerate(chat_models, 1):
            m_id = m.get("id", "")
            disp = m.get("display_name", "")[:24]
            in_limit = f"{m.get('input_token_limit'):,}" if m.get('input_token_limit') else "-"
            out_limit = f"{m.get('output_token_limit'):,}" if m.get('output_token_limit') else "-"
            print(f"{idx:<4} | {m_id:<28} | {disp:<24} | {in_limit:<14} | {out_limit}")

        print("-" * len(header))

        # Tự động chọn model khả dụng để test chat
        candidate_priority = ("gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-2.5-pro", "gemini-flash-latest")
        chosen_model = chat_models[0].get("id") if chat_models else "gemini-3.8-flash"
        for cand in candidate_priority:
            if any(m.get("id") == cand for m in chat_models):
                chosen_model = cand
                break

        print(f"\n[+] Thử nghiệm Chat Generation với Gemini (model: {chosen_model})...")
        sample_prompt = "Xin chào! Bạn là ai và có thể giúp gì cho tôi? Trả lời ngắn trong 1-2 câu."
        print(f"Prompt: \"{sample_prompt}\"\nPhản hồi từ Gemini:")
        print("-" * 70)
        response_text = provider.generate_chat(chosen_model, sample_prompt)
        print(response_text)
        print("-" * 70)
        print("[✓] Hoàn thành test Phase 2 cho Gemini API!")

    except PermissionError as e:
        print(f"\n[X] LỖI XÁC THỰC (400/403): {e}")
        print("    -> Vui lòng kiểm tra lại tính chính xác của GEMINI_API_KEY.")
    except RuntimeError as e:
        print(f"\n[X] LỖI HẠN MỨC HOẶC API (429): {e}")
    except ConnectionError as e:
        print(f"\n[X] LỖI KẾT NỐI MẠNG: {e}")
    except Exception as e:
        print(f"\n[X] LỖI KHÔNG XÁC ĐỊNH: {type(e).__name__} - {e}")

    print("=" * 70)


if __name__ == "__main__":
    main()
