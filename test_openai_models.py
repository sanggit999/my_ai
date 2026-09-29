"""Test Script - Phase 2: OpenAI list_models()

Chạy script này để kiểm tra kết nối API thực tế tới OpenAI:
    python test_openai_models.py
Hoặc truyền trực tiếp key:
    python test_openai_models.py --key sk-...
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
from providers.openai import OpenAIConfig, OpenAIProvider


def prompt_for_api_key() -> str:
    """Cho phép người dùng nhập trực tiếp API Key từ bàn phím."""
    print("\n" + "-" * 70)
    print("NHẬP OPENAI API KEY TRỰC TIẾP")
    print("Lấy key tại: https://platform.openai.com/api-keys")
    print("-" * 70)
    
    try:
        entered_key = input("👉 Nhập OpenAI API Key (sk-...): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[!] Đã hủy thao tác nhập.")
        return ""

    if not entered_key:
        print("[!] Không có key nào được nhập.")
        return ""

    # Hỏi người dùng có muốn lưu vào .env không
    try:
        save_choice = input("💾 Bạn có muốn lưu key này vào file .env không? (Y/n): ").strip().lower()
        if save_choice in ("", "y", "yes"):
            save_env_var("OPENAI_API_KEY", entered_key)
            print("[✓] Đã lưu OPENAI_API_KEY vào file .env thành công!")
    except (KeyboardInterrupt, EOFError):
        pass

    return entered_key


def main():
    parser = argparse.ArgumentParser(description="Kiểm tra kết nối và lấy danh sách model từ OpenAI API.")
    parser.add_argument("--key", "--api-key", dest="api_key", help="OpenAI API Key truyền qua dòng lệnh.")
    args = parser.parse_args()

    print("=" * 70)
    print("       TEST PHASE 2: OPENAI DYNAMIC MODELS API")
    print("=" * 70)

    load_env_files()

    # Ưu tiên: Flag dòng lệnh -> Biến môi trường .env -> Hỏi nhập qua bàn phím
    api_key = args.api_key
    config = OpenAIConfig(api_key=api_key) if api_key else OpenAIConfig()
    provider = OpenAIProvider(config)

    print(f"[*] Provider:        {provider.name.upper()}")
    print(f"[*] Trạng thái Key:  {'SẴN SÀNG' if provider.is_ready else 'CHƯA CÓ KEY'}")
    print(f"[*] Masked Key:      {provider.config.masked_key}")

    # Nếu chưa có key, hỏi người dùng nhập trực tiếp
    if not provider.is_ready:
        entered_key = prompt_for_api_key()
        if not entered_key:
            print("\n[!] Không thể tiếp tục kiểm tra vì chưa có API Key.")
            print("=" * 70)
            return
        # Tạo lại provider với key vừa nhập
        provider = OpenAIProvider(OpenAIConfig(api_key=entered_key))
        print(f"[*] Masked Key mới:  {provider.config.masked_key}")

    print("\n[+] Đang kết nối tới OpenAI Models API...")
    try:
        # Lấy danh sách model chat đã lọc
        chat_models = provider.list_chat_models()
        total_raw = len(provider.list_models())

        print(f"[✓] Kết nối thành công!")
        print(f"[*] Tổng số model trả về từ OpenAI API: {total_raw}")
        print(f"[*] Số model Chat/LLM được nhận diện:    {len(chat_models)}\n")

        print(f"{'STT':<5} | {'MODEL ID':<35} | {'OWNED BY':<15}")
        print("-" * 70)
        for idx, m in enumerate(chat_models, 1):
            m_id = m.get("id", "")
            owner = m.get("owned_by", "")
            print(f"{idx:<5} | {m_id:<35} | {owner:<15}")

        print("-" * 70)
        print("[✓] Hoàn thành test Phase 2 cho OpenAI Models API!")

    except PermissionError as e:
        print(f"\n[X] LỖI XÁC THỰC (401): {e}")
        print("    -> Vui lòng kiểm tra lại tính chính xác của OPENAI_API_KEY.")
    except RuntimeError as e:
        print(f"\n[X] LỖI HẠN MỨC HOẶC API (429): {e}")
    except ConnectionError as e:
        print(f"\n[X] LỖI KẾT NỐI MẠNG: {e}")
    except Exception as e:
        print(f"\n[X] LỖI KHÔNG XÁC ĐỊNH: {type(e).__name__} - {e}")

    print("=" * 70)


if __name__ == "__main__":
    main()
