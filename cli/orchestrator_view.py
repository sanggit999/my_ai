"""CLI View cho Multi-Model Orchestration & Synthesis (Phase 8).

Cung cấp trải nghiệm người dùng trực quan:
- Hiển thị tiến trình theo thời gian thực (Step 1: Fan-out -> Step 2: Synthesis).
- Trình bày nổi bật Final Answer (Câu trả lời tổng hợp tối ưu nhất).
- Cho phép người dùng soi chi tiết câu trả lời độc lập của từng AI để đối chiếu.
"""

import sys
from orchestrator import AIOrchestrator, SynthesizerResult, ProviderExecutionResult


def run_synthesis_interactive():
    """Vòng lặp tương tác giao diện người dùng cho tính năng Orchestration & Synthesis."""
    orchestrator = AIOrchestrator()

    if not orchestrator.provider_names:
        print("\n[!] Không có API Key nào được cấu hình trong file .env!")
        return

    print("\n" + "=" * 78)
    print("  🧠 MULTI-MODEL ORCHESTRATION & SYNTHESIS (ĐIỀU PHỐI & TỔNG HỢP ĐA AI)")
    print(f"  - Các AI tham gia: {', '.join(p.upper() for p in orchestrator.provider_names)}")
    print("  - Quy trình: Hỏi đồng thời ➔ AI Synthesizer thẩm định ➔ Final Answer tối ưu")
    print("=" * 78)
    print("Gợi ý: Gõ 'exit' hoặc '0' để quay lại menu chính.\n")

    while True:
        try:
            question = input("👉 Nhập câu hỏi của bạn: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã hủy.")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit", "0", "q"):
            print("[✓] Đã thoát chế độ Orchestration.")
            break

        print("\n" + "─" * 78)
        print("  [+] BƯỚC 1: Phân phối câu hỏi đồng thời (Parallel Fan-out)...")
        print("─" * 78)

        def on_status_update(p_name: str, model_name: str, status: str):
            p_label = p_name.upper().ljust(10)
            if status == "STARTING":
                print(f"    ⏳ {p_label} ({model_name:<26}) : Đang gửi yêu cầu...")
            elif status == "SUCCESS":
                print(f"    ✅ {p_label} ({model_name:<26}) : [HOÀN TẤT THÀNH CÔNG]")
            elif status.startswith("FAILED:"):
                err = status.replace("FAILED:", "").strip()
                print(f"    ⚠️  {p_label} ({model_name:<26}) : [BỎ QUA - {err}]")
            elif status == "SYNTHESIZING":
                print(f"\n  [+] BƯỚC 2: AI Synthesizer ({p_label}) đang thẩm định & tổng hợp...")
            elif status == "SYNTHESIS_DONE":
                print(f"  [✓] AI Synthesizer đã hoàn tất tổng hợp!")

        # Gọi Orchestrator thực hiện toàn bộ quy trình
        res: SynthesizerResult = orchestrator.synthesize(
            prompt=question,
            status_callback=on_status_update
        )

        # Hiển thị Final Answer
        print("\n" + "═" * 78)
        sources_str = ", ".join(res.successful_providers) if res.successful_providers else "Không có"
        print(f"  🏆 CÂU TRẢ LỜI TỔNG HỢP TỐI ƯU NHẤT (FINAL SYNTHESIZED ANSWER)")
        print(f"  - Nguồn tổng hợp  : {sources_str}")
        print(f"  - AI Synthesizer : {res.synthesizer_provider.upper()} ({res.synthesizer_model})")
        print(f"  - Tổng thời gian : {res.total_latency_ms / 1000:.2f} giây (Tổng hợp: {res.synthesis_latency_ms / 1000:.2f}s)")
        print("═" * 78 + "\n")
        print(res.final_answer)
        print("\n" + "═" * 78)

        # Cho phép người dùng soi chi tiết câu trả lời của từng AI
        if len(res.individual_results) > 1:
            try:
                sub_opt = input("\n[?] Bạn có muốn xem câu trả lời gốc của từng AI không? (1 = Xem, Enter = Bỏ qua): ").strip()
                if sub_opt == "1":
                    print("\n" + "─" * 78)
                    print("  📋 CHI TIẾT CÂU TRẢ LỜI ĐỘC LẬP TỪNG AI:")
                    print("─" * 78)
                    for idx, ind in enumerate(res.individual_results, 1):
                        print(f"\n--- [{idx}] AI: {ind.provider.upper()} (Model: {ind.model} | {ind.latency_ms:,.0f} ms) ---")
                        if ind.success and ind.response:
                            print(ind.response.content.strip())
                        else:
                            print(f"[X] Không có nội dung. Lý do: {ind.error_message}")
                    print("─" * 78 + "\n")
            except (KeyboardInterrupt, EOFError):
                pass
