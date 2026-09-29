"""Test Multi-Model Orchestration & Synthesis (Phase 8)."""

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
from orchestrator import AIOrchestrator, SynthesizerResult


def main():
    load_env_files()
    print("=" * 75)
    print("   KIỂM THỬ: MULTI-MODEL ORCHESTRATION & SYNTHESIS (Phase 8)")
    print("=" * 75)

    orch = AIOrchestrator()
    print(f"[*] Các Providers tham gia ({len(orch.provider_names)}): {', '.join(orch.provider_names).upper()}")

    question = "So sánh ngắn gọn ưu điểm lớn nhất của Python so với Rust trong 2 ý chính."
    print(f"\n[?] Câu hỏi: '{question}'\n")

    def progress(p, m, st):
        print(f"  --> [{p.upper()}] ({m}) : {st}")

    result: SynthesizerResult = orch.synthesize(question, status_callback=progress)

    print("\n" + "=" * 75)
    print("   🏆 KẾT QUẢ TỔNG HỢP CUỐI CÙNG (FINAL SYNTHESIZED ANSWER)")
    print("=" * 75)
    print(f"- Nguồn thành công: {', '.join(result.successful_providers)}")
    print(f"- AI Synthesizer  : {result.synthesizer_provider.upper()} ({result.synthesizer_model})")
    print(f"- Thời gian xử lý : Tổng {result.total_latency_ms:,.0f} ms (Tổng hợp: {result.synthesis_latency_ms:,.0f} ms)")
    print("-" * 75)
    print(result.final_answer)
    print("=" * 75)

    assert result.final_answer.strip() != "", "Final answer should not be empty!"
    assert len(result.successful_providers) >= 1, "At least 1 provider should succeed!"
    print("\n[✓] KIỂM THỬ MULTI-MODEL SYNTHESIS HOÀN TOÀN THÀNH CÔNG!")


if __name__ == "__main__":
    main()
