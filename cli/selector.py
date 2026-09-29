"""CLI Selector - Phase 4: Lựa chọn Provider -> Model có hỗ trợ tìm kiếm / lọc.

Tương thích cả khi có hoặc chưa có thư viện `questionary`/`rich`.
"""

import sys
from typing import Optional, Tuple, List, Dict
from providers.base import BaseProvider
from models.model_info import ModelInfo
from providers import get_available_provider_configs, get_provider


class CLISelector:
    """Điều hướng và lựa chọn Provider & Model tương tác qua terminal."""

    @staticmethod
    def select_provider() -> Optional[Tuple[str, BaseProvider]]:
        """Hiển thị menu các provider đang có API Key sẵn sàng."""
        available_configs = get_available_provider_configs()
        if not available_configs:
            print("\n[!] Không có Provider nào được cấu hình API Key trong file .env!")
            print("    Vui lòng cấu hình ít nhất một trong: OPENAI_API_KEY, GROQ_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY")
            return None

        provider_names = list(available_configs.keys())

        # Thử dùng questionary nếu có
        try:
            import questionary
            choices = [
                questionary.Choice(
                    title=f"{p.upper()} ({available_configs[p].masked_key})",
                    value=p
                )
                for p in provider_names
            ]
            choices.append(questionary.Choice(title="[Thoát]", value=None))

            selected = questionary.select(
                "Chọn AI Provider bạn muốn sử dụng:",
                choices=choices
            ).ask()

            if not selected:
                return None
            return selected, get_provider(selected)

        except ImportError:
            # Fallback console chuẩn
            print("\n" + "=" * 65)
            print("DANH SÁCH AI PROVIDERS SẴN SÀNG:")
            print("=" * 65)
            for idx, p in enumerate(provider_names, 1):
                masked = available_configs[p].masked_key
                print(f"  {idx}. {p.upper():<12} (Key: {masked})")
            print("  0. Thoát")
            print("-" * 65)

            while True:
                try:
                    choice = input(f"Chọn Provider (1-{len(provider_names)}, hoặc 0): ").strip()
                    if choice in ("0", "exit", "quit"):
                        return None
                    if choice.isdigit() and 1 <= int(choice) <= len(provider_names):
                        name = provider_names[int(choice) - 1]
                        return name, get_provider(name)
                    print("Lựa chọn không hợp lệ, vui lòng nhập lại.")
                except (KeyboardInterrupt, EOFError):
                    print("\nĐã hủy.")
                    return None

    @staticmethod
    def select_model(provider: BaseProvider) -> Optional[ModelInfo]:
        """Tải models động từ provider và cho phép người dùng chọn / tìm kiếm."""
        print(f"\n[+] Đang tải danh sách models từ {provider.name.upper()} API...")
        try:
            models: List[ModelInfo] = provider.get_models()
        except Exception as e:
            print(f"[X] Lỗi khi truy vấn models từ {provider.name}: {e}")
            return None

        if not models:
            print(f"[!] Không tìm thấy model nào khả dụng cho {provider.name}.")
            return None

        print(f"[✓] Đã tải thành công {len(models)} models!")

        # Thử dùng questionary với ô tìm kiếm fuzzy
        try:
            import questionary
            choices = [
                questionary.Choice(
                    title=m.full_label,
                    value=m
                )
                for m in models
            ]
            choices.append(questionary.Choice(title="[Quay lại]", value=None))

            selected = questionary.select(
                f"Chọn model của {provider.name.upper()} (Gõ phím để tìm kiếm):",
                choices=choices,
                use_search_filter=True
            ).ask()

            return selected

        except ImportError:
            # Fallback tìm kiếm console thông minh
            current_list = models
            while True:
                print("\n" + "=" * 80)
                print(f"DANH SÁCH MODELS CỦA {provider.name.upper()} (Đang hiển thị {len(current_list)}/{len(models)} models)")
                print("=" * 80)
                print(f"{'STT':<4} | {'MODEL ID':<36} | {'CONTEXT':<12} | {'TÍNH NĂNG'}")
                print("-" * 80)

                for idx, m in enumerate(current_list[:15], 1):
                    ctx = f"{m.input_token_limit:,}" if m.input_token_limit else "-"
                    caps = ", ".join(m.capabilities)
                    print(f"{idx:<4} | {m.id:<36} | {ctx:<12} | {caps}")

                if len(current_list) > 15:
                    print(f"... và còn {len(current_list) - 15} model khác. Hãy gõ từ khóa để lọc.")

                print("-" * 80)
                print("Gợi ý: Nhập số thứ tự để CHỌN (vd: 1) | Gõ /filter <từ khóa> để LỌC | 0 để QUAY LẠI")

                try:
                    cmd = input("👉 Lựa chọn của bạn: ").strip()
                    if cmd in ("0", "exit", "quit"):
                        return None

                    if cmd.startswith("/filter "):
                        kw = cmd.replace("/filter ", "").strip().lower()
                        current_list = [m for m in models if kw in m.id.lower() or kw in m.display_name.lower()]
                        if not current_list:
                            print(f"[!] Không tìm thấy model nào khớp với từ khóa '{kw}'. Đặt lại danh sách ban đầu.")
                            current_list = models
                        continue

                    if cmd.isdigit() and 1 <= int(cmd) <= len(current_list):
                        return current_list[int(cmd) - 1]

                    # Nếu gõ thẳng tên model gần đúng
                    matches = [m for m in models if cmd.lower() in m.id.lower()]
                    if len(matches) == 1:
                        return matches[0]
                    elif len(matches) > 1:
                        current_list = matches
                        continue

                    print("Lựa chọn không hợp lệ, vui lòng thử lại.")
                except (KeyboardInterrupt, EOFError):
                    print("\nĐã hủy.")
                    return None
