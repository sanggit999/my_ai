"""Interactive CLI Chat Loop - Tương tác đa lượt (Phases 4, 5, 6, 7).

Tính năng:
- Lựa chọn linh hoạt Provider & Model (Phase 4).
- Phản hồi Streaming thời gian thực (Phase 5).
- Định dạng thống nhất UnifiedResponse (Latency, Token Usage) (Phase 6).
- Quản lý phiên hội thoại nhiều lượt, cắt tỉa ngữ cảnh, lưu/tải JSON (Phase 7).
"""

import sys
import time
from typing import Optional
from pathlib import Path

from providers.base import BaseProvider
from models.model_info import ModelInfo
from models.chat import ChatSession, ChatMessage
from models.unified_response import UnifiedResponse, TokenUsage
from session.storage import SessionStorage
from cli.selector import CLISelector
from providers import get_provider


def print_banner(session: ChatSession, model_info: Optional[ModelInfo] = None):
    """In thông tin session và hướng dẫn sử dụng lệnh."""
    print("\n" + "=" * 75)
    print(f"  🤖 MULTI-AI INTERACTIVE CHAT ENGINE")
    print(f"  - Provider : {session.provider.upper()}")
    print(f"  - Model    : {session.model}")
    if model_info and model_info.input_token_limit:
        print(f"  - Context  : {model_info.input_token_limit:,} tokens")
    if session.system_prompt:
        print(f"  - System   : {session.system_prompt}")
    print(f"  - Session  : #{session.id} ({len(session.messages)} tin nhắn)")
    print("-" * 75)
    print("  LỆNH HỖ TRỢ:")
    print("    /switch         - Đổi Model hoặc Provider khác")
    print("    /system <text>  - Thiết lập System Prompt cho AI")
    print("    /clear          - Xóa lịch sử trò chuyện trong phiên hiện tại")
    print("    /save [tên]     - Lưu phiên hội thoại ra file JSON")
    print("    /load           - Tải lại phiên hội thoại cũ từ thư mục .sessions/")
    print("    /history        - Xem lại toàn bộ lịch sử cuộc trò chuyện")
    print("    /exit           - Thoát chương trình")
    print("=" * 75 + "\n")


class ChatLoop:
    """Điều phối vòng lặp chat đa lượt người dùng <-> AI."""

    def __init__(self, provider: BaseProvider, model_info: ModelInfo, session: Optional[ChatSession] = None):
        self.provider = provider
        self.model_info = model_info
        if session:
            self.session = session
        else:
            self.session = ChatSession(
                provider=provider.name,
                model=model_info.id,
            )

    def run(self):
        """Khởi động vòng lặp chat tương tác."""
        print_banner(self.session, self.model_info)

        while True:
            try:
                user_input = input(f"\n👤 Bạn [{self.session.model}]: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\n[!] Tạm biệt!")
                break

            if not user_input:
                continue

            # Xử lý các lệnh đặc biệt (slash commands)
            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                arg = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""

                if cmd in ("/exit", "/quit", "/q"):
                    if len(self.session.messages) > 0:
                        save_prompt = input("Bạn có muốn lưu phiên hội thoại này trước khi thoát không? (y/N): ").strip().lower()
                        if save_prompt in ("y", "yes"):
                            saved_path = SessionStorage.save(self.session)
                            print(f"[✓] Đã lưu phiên vào: {saved_path}")
                    print("\n[✓] Cảm ơn bạn đã sử dụng Multi-AI Chat! Hẹn gặp lại.")
                    break

                elif cmd in ("/switch", "/model", "/provider"):
                    self._handle_switch()
                    continue

                elif cmd in ("/system", "/sys"):
                    if arg:
                        self.session.system_prompt = arg
                        print(f"[✓] Đã cập nhật System Prompt: '{arg}'")
                    else:
                        print(f"[*] System Prompt hiện tại: '{self.session.system_prompt or '<Chưa thiết lập>'}'")
                    continue

                elif cmd in ("/clear", "/reset"):
                    self.session.clear()
                    print("[✓] Đã xóa toàn bộ lịch sử hội thoại của phiên này.")
                    continue

                elif cmd in ("/save",):
                    file_name = f"{arg}.json" if arg and not arg.endswith(".json") else (arg or None)
                    saved_path = SessionStorage.save(self.session, file_name=file_name)
                    print(f"[✓] Đã lưu phiên hội thoại thành công: {saved_path}")
                    continue

                elif cmd in ("/load",):
                    self._handle_load()
                    continue

                elif cmd in ("/history", "/hist"):
                    self._show_history()
                    continue

                elif cmd in ("/help", "/h", "/?"):
                    print_banner(self.session, self.model_info)
                    continue

                else:
                    print(f"[!] Lệnh không nhận diện: '{cmd}'. Gõ /help để xem danh sách lệnh.")
                    continue

            # Xử lý gửi tin nhắn tới AI
            self._send_message(user_input)

    def _send_message(self, text: str):
        """Gửi tin nhắn của người dùng và hiển thị phản hồi từ AI."""
        # Thêm tin nhắn của User vào Session
        self.session.add_user_message(text)

        # Cắt tỉa ngữ cảnh nếu vượt quá 20 tin nhắn gần nhất
        messages_payload = self.session.prune_context(max_messages=20)

        print(f"\n🤖 {self.provider.name.upper()} ({self.session.model}): ", end="", flush=True)

        start_time = time.perf_counter()
        full_response_text = ""
        stream_success = False

        # Thử phản hồi streaming thời gian thực (Phase 5)
        try:
            for chunk in self.provider.generate_stream(
                model=self.session.model,
                messages=messages_payload,
                system_prompt=self.session.system_prompt,
            ):
                full_response_text += chunk
                sys.stdout.write(chunk)
                sys.stdout.flush()
            stream_success = True
        except Exception as stream_err:
            # Fallback nếu streaming lỗi: thử gọi generate() đồng bộ
            pass

        # Nếu streaming không khả dụng hoặc trả về rỗng, gọi fallback generate()
        if not stream_success or not full_response_text.strip():
            try:
                resp: UnifiedResponse = self.provider.generate(
                    model=self.session.model,
                    messages=messages_payload,
                    system_prompt=self.session.system_prompt,
                )
                full_response_text = resp.content
                sys.stdout.write(full_response_text)
                sys.stdout.flush()
            except Exception as e:
                print(f"\n[X] Lỗi khi nhận phản hồi từ {self.provider.name}: {e}")
                # Xóa tin nhắn user vừa gửi khỏi session nếu bị lỗi để tránh lệch ngữ cảnh
                if self.session.messages and self.session.messages[-1].content == text:
                    self.session.messages.pop()
                return

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        print() # Dòng mới

        # Lưu tin nhắn Assistant vào Session (Phase 7)
        self.session.add_assistant_message(full_response_text, model=self.session.model)

        # In thông tin thống kê Phase 6 (Tokens / Latency)
        # Ước lượng tokens nếu không có từ streaming
        approx_in = sum(len(m.get("content", "").split()) for m in messages_payload) * 4 // 3
        approx_out = len(full_response_text.split()) * 4 // 3
        approx_total = approx_in + approx_out

        print(f"─" * 70)
        print(f"⏱️  Thời gian: {elapsed_ms:,.0f} ms | 📊 Ước tính Tokens: In ~{approx_in} • Out ~{approx_out} • Tổng ~{approx_total}")
        print(f"─" * 70)

    def _show_history(self):
        """Hiển thị toàn bộ lịch sử các lượt trò chuyện."""
        if not self.session.messages:
            print("\n[i] Lịch sử hội thoại hiện đang trống.")
            return

        print("\n" + "=" * 70)
        print(f"LỊCH SỬ HỘI THOẠI (Phiên #{self.session.id} - {len(self.session.messages)} tin nhắn)")
        print("=" * 70)
        for idx, msg in enumerate(self.session.messages, 1):
            role_name = "👤 User" if msg.role == "user" else f"🤖 Assistant ({msg.model or 'AI'})"
            print(f"\n[{idx}] {role_name} ({msg.timestamp[:19]}):")
            print(f"{msg.content}")
        print("=" * 70)

    def _handle_switch(self):
        """Cho phép người dùng chuyển đổi Provider / Model ngay trong phiên chat."""
        print("\n[?] Bạn muốn đổi gì?")
        print("  1. Đổi Model khác của Provider hiện tại")
        print("  2. Đổi sang Provider khác")
        print("  0. Giữ nguyên")
        choice = input("Lựa chọn (1/2/0): ").strip()

        if choice == "1":
            new_model = CLISelector.select_model(self.provider)
            if new_model:
                self.model_info = new_model
                self.session.model = new_model.id
                print(f"[✓] Đã chuyển sang Model: {new_model.id}")
                print_banner(self.session, self.model_info)

        elif choice == "2":
            res = CLISelector.select_provider()
            if res:
                p_name, new_provider = res
                new_model = CLISelector.select_model(new_provider)
                if new_model:
                    self.provider = new_provider
                    self.model_info = new_model
                    self.session.provider = p_name
                    self.session.model = new_model.id
                    print(f"[✓] Đã chuyển sang Provider: {p_name.upper()} | Model: {new_model.id}")
                    print_banner(self.session, self.model_info)

    def _handle_load(self):
        """Tải một phiên hội thoại cũ từ thư mục .sessions/."""
        saved_files = SessionStorage.list_saved_sessions()
        if not saved_files:
            print("\n[!] Chưa có file session nào được lưu trong thư mục .sessions/")
            return

        print("\nDANH SÁCH CÁC PHIÊN ĐÃ LƯU:")
        for idx, file_path in enumerate(saved_files, 1):
            print(f"  {idx}. {file_path.name}")
        print("  0. Hủy")

        choice = input(f"Chọn file cần tải (1-{len(saved_files)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(saved_files):
            chosen_file = saved_files[int(choice) - 1]
            try:
                loaded_session = SessionStorage.load(chosen_file)
                self.session = loaded_session
                self.provider = get_provider(loaded_session.provider)
                # Tìm lại model info nếu có
                try:
                    all_models = self.provider.get_models()
                    matches = [m for m in all_models if m.id == loaded_session.model]
                    self.model_info = matches[0] if matches else ModelInfo(provider=loaded_session.provider, id=loaded_session.model, display_name=loaded_session.model)
                except Exception:
                    self.model_info = ModelInfo(provider=loaded_session.provider, id=loaded_session.model, display_name=loaded_session.model)

                print(f"[✓] Đã tải phiên thành công từ file {chosen_file.name}!")
                print_banner(self.session, self.model_info)
            except Exception as e:
                print(f"[X] Lỗi khi tải file: {e}")
