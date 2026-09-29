"""Test Script - Phase 2: Groq (OpenAI-Compatible 3rd Party) API

Chạy script này để kiểm tra kết nối API tới Groq:
    python test_groq_models.py
Hoặc truyền trực tiếp key:
    python test_groq_models.py --key gsk_...
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
from providers.groq import GroqConfig, GroqProvider


def prompt_for_api_key() -> str:
    """Cho phép người dùng nhập trực tiếp Groq API Key từ bàn phím."""
    print("\n" + "-" * 70)
    print("NHẬP GROQ API KEY TRỰC TIẾP")
    print("Lấy key miễn phí tại: https://console.groq.com/keys")
    print("-" * 70)

    try:
        entered_key = input("👉 Nhập Groq API Key (gsk_...): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[!] Đã hủy thao tác nhập.")
        return ""

    if not entered_key:
        print("[!] Không có key nào được nhập.")
        return ""

    try:
        save_choice = input("💾 Bạn có muốn lưu key này vào file .env không? (Y/n): ").strip().lower()
        if save_choice in ("", "y", "yes"):
            save_env_var("GROQ_API_KEY", entered_key)
            print("[✓] Đã lưu GROQ_API_KEY vào file .env thành công!")
    except (KeyboardInterrupt, EOFError):
        pass

    return entered_key


def main():
    parser = argparse.ArgumentParser(description="Kiểm tra kết nối và lấy danh sách model từ Groq API.")
    parser.add_argument("--key", "--api-key", dest="api_key", help="Groq API Key truyền qua dòng lệnh.")
    parser.add_argument("--chat", action="store_true", help="Thử nghiệm sinh text với llama-3.3-70b-versatile.")
    args = parser.parse_args()

    print("=" * 70)
    print("       TEST PHASE 2: GROQ (OPENAI-COMPATIBLE) MODELS API")
    print("=" * 70)

    load_env_files()

    api_key = args.api_key
    config = GroqConfig(api_key=api_key) if api_key else GroqConfig()
    provider = GroqProvider(config)

    print(f"[*] Provider:        {provider.name.upper()} (OpenAI-compatible LPU)")
    print(f"[*] Base URL:        {provider.config.base_url}")
    print(f"[*] Trạng thái Key:  {'SẴN SÀNG' if provider.is_ready else 'CHƯA CÓ KEY'}")
    print(f"[*] Masked Key:      {provider.config.masked_key}")

    # Nếu chưa có key, hỏi người dùng nhập trực tiếp
    if not provider.is_ready:
        entered_key = prompt_for_api_key()
        if not entered_key:
            print("\n[!] Không thể tiếp tục kiểm tra vì chưa có Groq API Key.")
            print("=" * 70)
            return
        provider = GroqProvider(GroqConfig(api_key=entered_key))
        print(f"[*] Masked Key mới:  {provider.config.masked_key}")

    print("\n[+] Đang kết nối tới Groq Models API...")
    try:
        chat_models = provider.list_chat_models()
        total_raw = len(provider.list_models())

        print(f"[✓] Kết nối thành công!")
        print(f"[*] Tổng số model trả về từ Groq API: {total_raw}")
        print(f"[*] Số model Chat/LLM được nhận diện: {len(chat_models)}\n")

        header = f"{'STT':<4} | {'MODEL ID':<36} | {'RPM':<6} | {'RPD':<6} | {'TPM':<6} | {'TPD':<6} | {'ASH/ASD'}"
        print(header)
        print("-" * len(header))
        for idx, m in enumerate(chat_models, 1):
            m_id = m.get("id", "")
            limits = m.get("limits") or {}
            rpm = limits.get("rpm", "-")
            rpd = limits.get("rpd", "-")
            tpm = limits.get("tpm", "-")
            tpd = limits.get("tpd", "-")
            ash = limits.get("ash", "-")
            asd = limits.get("asd", "-")
            audio = f"{ash}/{asd}" if ash != "-" else "-"
            print(f"{idx:<4} | {m_id:<36} | {rpm:<6} | {rpd:<6} | {tpm:<6} | {tpd:<6} | {audio}")

        print("-" * len(header))
        print("[*] Ghi chú: RPM=Requests/Min | RPD=Requests/Day | TPM=Tokens/Min | TPD=Tokens/Day | ASH=Audio Sec/Hr")

        # Tự động chọn model khả dụng trong danh sách của tài khoản để thử nghiệm
        candidate_priority = ("openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile")
        chosen_model = chat_models[0].get("id") if chat_models else "openai/gpt-oss-120b"
        for cand in candidate_priority:
            if any(m.get("id") == cand for m in chat_models):
                chosen_model = cand
                break

        print(f"\n[+] Thử nghiệm Chat Completion với Groq (model: {chosen_model})...")
        sample_prompt = "Xin chào! Bạn là ai và có thể giúp gì cho tôi? Trả lời ngắn trong 1-2 câu."
        print(f"Prompt: \"{sample_prompt}\"\nPhản hồi từ Groq:")
        print("-" * 70)
        response_text = provider.generate_chat(chosen_model, sample_prompt)
        print(response_text)
        print("-" * 70)
        print("[✓] Hoàn thành test Phase 2 cho Groq API!")

    except PermissionError as e:
        print(f"\n[X] LỖI XÁC THỰC (401): {e}")
        print("    -> Vui lòng kiểm tra lại tính chính xác của GROQ_API_KEY.")
    except RuntimeError as e:
        print(f"\n[X] LỖI HẠN MỨC HOẶC API (429): {e}")
    except ConnectionError as e:
        print(f"\n[X] LỖI KẾT NỐI MẠNG: {e}")
    except Exception as e:
        print(f"\n[X] LỖI KHÔNG XÁC ĐỊNH: {type(e).__name__} - {e}")

    print("=" * 70)


if __name__ == "__main__":
    main()
