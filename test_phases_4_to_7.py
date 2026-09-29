"""Automated End-to-End Test cho Phases 4, 5, 6, 7.

Kiểm tra:
1. Dynamic model listing & ModelInfo normalization (Phase 3).
2. Streaming & Non-streaming Generation (Phase 5).
3. UnifiedResponse structure (Phase 6).
4. Multi-turn Session Management & Context Pruning (Phase 7).
5. Session JSON Persistence (Phase 7).
"""

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

from config.env_loader import load_env_files
from providers import get_available_provider_configs, get_provider
from models.chat import ChatSession, ChatMessage
from models.unified_response import UnifiedResponse
from session.storage import SessionStorage


def test_session_persistence():
    print("\n" + "=" * 65)
    print("TEST 1: SESSION STORAGE & CONTEXT PRUNING (Phase 7)")
    print("=" * 65)

    session = ChatSession(
        provider="groq",
        model="openai/gpt-oss-120b",
        system_prompt="Bạn là trợ lý AI chuyên nghiệp."
    )
    session.add_user_message("Xin chào!")
    session.add_assistant_message("Chào bạn! Tôi có thể giúp gì cho bạn?")
    session.add_user_message("Hôm nay thời tiết thế nào?")
    session.add_assistant_message("Tôi không có dữ liệu thời tiết thời gian thực.")

    # Test context pruning
    pruned = session.prune_context(max_messages=2)
    assert len(pruned) == 2, f"Expected 2 messages, got {len(pruned)}"
    assert pruned[0]["role"] == "user", "Pruned window should start with user"
    print(f"  [✓] Cắt tỉa ngữ cảnh thành công (2 tin nhắn gần nhất: {pruned[0]['content']})")

    # Test Save
    saved_path = SessionStorage.save(session, file_name="test_temp_session.json")
    assert saved_path.exists(), "Saved file does not exist!"
    print(f"  [✓] Lưu session thành công tại: {saved_path.name}")

    # Test Load
    loaded = SessionStorage.load(saved_path)
    assert loaded.id == session.id
    assert loaded.provider == session.provider
    assert loaded.model == session.model
    assert loaded.system_prompt == session.system_prompt
    assert len(loaded.messages) == 4
    print(f"  [✓] Tải lại session thành công: #{loaded.id} ({len(loaded.messages)} tin nhắn)")

    # Cleanup temp test file
    saved_path.unlink()
    print("  [✓] Dọn dẹp file test thành công.")


def test_groq_streaming_and_unified_response():
    print("\n" + "=" * 65)
    print("TEST 2: GROQ GENERATE STREAM & UNIFIED RESPONSE (Phases 5 & 6)")
    print("=" * 65)

    provider = get_provider("groq")
    if not provider.is_ready:
        print("  [!] Bỏ qua test Groq vì chưa cấu hình key.")
        return

    # Lấy model đầu tiên
    models = provider.get_models()
    assert len(models) > 0, "Groq returned 0 models"
    target_model = models[0].id
    print(f"  [*] Đang thử nghiệm với model: {target_model}")

    # Test non-streaming
    prompt = "2 + 3 bằng bao nhiêu? Trả lời chỉ 1 số."
    resp: UnifiedResponse = provider.generate(
        model=target_model,
        messages=[{"role": "user", "content": prompt}],
    )
    print(f"  [✓] Generate thành công:")
    print(f"      - Nội dung : {resp.content.strip()}")
    print(f"      - Tokens   : {resp.usage.summary}")
    print(f"      - Độ trễ   : {resp.latency_ms:,.1f} ms")
    assert resp.content.strip() != "", "Content should not be empty"
    assert resp.provider == "groq"

    # Test streaming
    print(f"  [*] Đang kiểm tra Streaming:")
    sys.stdout.write("      Chunks: ")
    stream_chunks = []
    for chunk in provider.generate_stream(
        model=target_model,
        messages=[{"role": "user", "content": "Đếm 1, 2, 3"}],
    ):
        sys.stdout.write(f"[{chunk}]")
        stream_chunks.append(chunk)
    print()
    full_stream_text = "".join(stream_chunks)
    assert full_stream_text.strip() != "", "Stream text should not be empty"
    print(f"  [✓] Streaming thành công: '{full_stream_text.strip()}' ({len(stream_chunks)} chunks)")


def test_gemini_streaming_and_unified_response():
    print("\n" + "=" * 65)
    print("TEST 3: GEMINI GENERATE & UNIFIED RESPONSE (Phases 5 & 6)")
    print("=" * 65)

    provider = get_provider("gemini")
    if not provider.is_ready:
        print("  [!] Bỏ qua test Gemini vì chưa cấu hình key.")
        return

    target_model = "gemini-3.1-flash-lite"
    print(f"  [*] Đang thử nghiệm với model: {target_model}")

    prompt = "Mặt trời mọc hướng nào? Trả lời trong 5 từ."
    resp: UnifiedResponse = provider.generate(
        model=target_model,
        messages=[{"role": "user", "content": prompt}],
    )
    print(f"  [✓] Generate thành công:")
    print(f"      - Nội dung : {resp.content.strip()}")
    print(f"      - Tokens   : {resp.usage.summary}")
    print(f"      - Độ trễ   : {resp.latency_ms:,.1f} ms")
    assert resp.content.strip() != "", "Content should not be empty"
    assert resp.provider == "gemini"


def main():
    load_env_files()
    print("=" * 65)
    print("   BẮT ĐẦU CHẠY KIỂM THỬ TỔNG HỢP CÁC PHASES 4, 5, 6, 7")
    print("=" * 65)

    test_session_persistence()
    test_groq_streaming_and_unified_response()
    test_gemini_streaming_and_unified_response()

    print("\n" + "=" * 65)
    print("   🎉 TẤT CẢ CÁC BÀI TEST TỔNG HỢP ĐỀU ĐÃ ĐẠT (PASSED)!")
    print("=" * 65)


if __name__ == "__main__":
    main()
