"""CLI View cho Multi-Persona Role Assignment & Sequential Pipeline (Phase 9).

Cung cấp:
1. 🏛️ Hội đồng Chuyên gia (Council of Experts: Tech + Security + Business -> Executive Consensus).
2. ⚙️ Tùy chọn cấu hình phân vai thủ công (Chọn con nào làm việc gì, con nào làm Trọng tài).
3. ⛓️ Dây chuyền Tuần tự (Pipeline: Planner ➔ Coder ➔ Reviewer).
"""

import sys
from typing import List

from orchestrator import (
    AIOrchestrator,
    SynthesizerResult,
    ProviderExecutionResult,
)
from orchestrator.models import RoleAssignment, PipelineStep, PipelineResult
from orchestrator.personas import BUILTIN_PERSONAS, get_persona


def run_council_of_experts():
    """Chế độ 1: Hội đồng Chuyên gia (Tech + Security + Business)."""
    orch = AIOrchestrator()
    if not orch.provider_names:
        print("\n[!] Chưa có API Key nào được cấu hình trong file .env!")
        return

    print("\n" + "=" * 78)
    print("  🏛️ HỘI ĐỒNG CHUYÊN GIA ĐA GÓC NHÌN (COUNCIL OF EXPERTS)")
    print("  - Chuyên gia 1: 🛠️ Senior Technical Architect (Groq - LPU)")
    print("  - Chuyên gia 2: 🛡️ Cybersecurity Specialist (Google Gemini)")
    print("  - Chuyên gia 3: 💼 Product & Business Analyst (Groq - LPU)")
    print("  - Tổng Trưởng Dự Án: 🧠 Executive Chief Strategist (Gemini Synthesizer)")
    print("=" * 78)

    while True:
        try:
            problem = input("\n👉 Nhập đề tài / bài toán cần Hội đồng thẩm định (0 để quay lại): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã hủy.")
            break

        if not problem or problem in ("0", "exit", "quit"):
            break

        # Gán vai trò cụ thể cho từng model
        role_assignments = [
            RoleAssignment(
                provider="groq",
                model="openai/gpt-oss-120b",
                role_name="Senior Technical Architect",
                system_prompt=BUILTIN_PERSONAS["tech_lead"]["system_prompt"],
            ),
            RoleAssignment(
                provider="gemini",
                model="gemini-3.1-flash-lite",
                role_name="Cybersecurity Specialist",
                system_prompt=BUILTIN_PERSONAS["security_expert"]["system_prompt"],
            ),
            RoleAssignment(
                provider="groq",
                model="qwen/qwen3.8-27b",
                role_name="Product & Business Analyst",
                system_prompt=BUILTIN_PERSONAS["business_analyst"]["system_prompt"],
            ),
        ]

        # Lọc chỉ các provider sẵn sàng
        active_roles = [r for r in role_assignments if r.provider in orch.provider_names]

        print("\n" + "─" * 78)
        print("  [+] BƯỚC 1: Các chuyên gia trong Hội đồng đang phân tích độc lập...")
        print("─" * 78)

        def on_status(p, info, st):
            if st == "STARTING":
                print(f"    ⏳ {info:<40} : Đang soạn bản tham mưu...")
            elif st == "SUCCESS":
                print(f"    ✅ {info:<40} : [HOÀN TẤT THAM MƯU]")
            elif st.startswith("FAILED:"):
                err = st.replace("FAILED:", "").strip()
                print(f"    ⚠️  {info:<40} : [LỖI - {err}]")
            elif st == "SYNTHESIZING":
                print(f"\n  [+] BƯỚC 2: Giám Đốc Chiến Lược đang tổng hợp Giải Pháp Toàn Diện...")
            elif st == "SYNTHESIS_DONE":
                print(f"  [✓] Hoàn tất bản Giải Pháp Chiến Lược Toàn Diện!")

        res: SynthesizerResult = orch.synthesize_with_roles(
            prompt=problem,
            role_assignments=active_roles,
            synthesizer_provider="gemini",
            synthesizer_model="gemini-3.1-flash-lite",
            status_callback=on_status
        )

        print("\n" + "═" * 78)
        print("  🏆 BẢN GIẢI PHÁP CHIẾN LƯỢC TOÀN DIỆN (EXECUTIVE STRATEGIC PLAN)")
        print(f"  - Tham vấn từ    : {', '.join(res.successful_providers)}")
        print(f"  - Tổng hợp bởi   : {res.synthesizer_provider.upper()} ({res.synthesizer_model})")
        print(f"  - Tổng thời gian : {res.total_latency_ms / 1000:.2f} giây")
        print("═" * 78 + "\n")
        print(res.final_answer)
        print("\n" + "═" * 78)

        # Cho phép soi chi tiết từng góc nhìn
        try:
            sub = input("\n[?] Bạn có muốn xem chi tiết báo cáo từng Chuyên gia? (1 = Xem, Enter = Bỏ qua): ").strip()
            if sub == "1":
                for idx, ind in enumerate(res.individual_results, 1):
                    role_tag = active_roles[idx - 1].role_name if idx <= len(active_roles) else ind.provider
                    print(f"\n--- [CHUYÊN GIA {idx}: {role_tag.upper()} ({ind.provider.upper()})] ---")
                    if ind.success and ind.response:
                        print(ind.response.content.strip())
                    else:
                        print(f"[X] Lỗi: {ind.error_message}")
                print("─" * 78)
        except (KeyboardInterrupt, EOFError):
            pass


def run_sequential_pipeline():
    """Chế độ 3: Dây chuyền tuần tự (Planner ➔ Coder ➔ Reviewer)."""
    orch = AIOrchestrator()
    if not orch.provider_names:
        print("\n[!] Chưa có API Key nào được cấu hình trong file .env!")
        return

    print("\n" + "=" * 78)
    print("  ⛓️ DÂY CHUYỀN TUẦN TỰ (SEQUENTIAL PIPELINE CHAIN)")
    print("  - Bước 1: 📐 Planner (Lập dàn ý thiết kế kiến trúc)")
    print("  - Bước 2: 💻 Implementer / Coder (Viết code hoàn chỉnh theo dàn ý)")
    print("  - Bước 3: 🔍 Auditor / Reviewer (Kiểm thử, bắt lỗi và tối ưu hiệu năng)")
    print("=" * 78)

    while True:
        try:
            task = input("\n👉 Nhập yêu cầu phần mềm / tính năng cần dây chuyền xử lý (0 để quay lại): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã hủy.")
            break

        if not task or task in ("0", "exit", "quit"):
            break

        # Định nghĩa 3 mắt xích trong dây chuyền
        steps = [
            PipelineStep(
                step_id=1,
                step_name="Planner (Kiến trúc & Dàn ý)",
                provider="groq" if "groq" in orch.provider_names else "gemini",
                model="openai/gpt-oss-120b" if "groq" in orch.provider_names else "gemini-3.1-flash-lite",
                prompt_template=(
                    "Bạn là Software Architect. Với yêu cầu sau: '{input}', hãy lập dàn ý kiến trúc phần mềm, "
                    "xác định các module, hàm cần thiết và cấu trúc dữ liệu tối ưu. Trình bày rõ ràng để coder có thể viết code ngay."
                ),
            ),
            PipelineStep(
                step_id=2,
                step_name="Coder (Triển khai mã nguồn)",
                provider="gemini" if "gemini" in orch.provider_names else "groq",
                model="gemini-3.1-flash-lite" if "gemini" in orch.provider_names else "openai/gpt-oss-120b",
                prompt_template=(
                    "Dựa trên dàn ý kiến trúc sau:\n{previous_output}\n\n"
                    "Hãy viết mã nguồn hoàn chỉnh, chuẩn PEP 8 (nếu là Python) hoặc chuẩn công nghiệp, "
                    "có xử lý ngoại lệ đầy đủ và chú thích giải thích chi tiết."
                ),
            ),
            PipelineStep(
                step_id=3,
                step_name="Reviewer (Kiểm thử & Tối ưu)",
                provider="groq" if "groq" in orch.provider_names else "gemini",
                model="openai/gpt-oss-120b" if "groq" in orch.provider_names else "gemini-3.1-flash-lite",
                prompt_template=(
                    "Bạn là Senior Code Reviewer & Security Auditor. Hãy đánh giá đoạn mã nguồn sau:\n{previous_output}\n\n"
                    "1. Phát hiện các lỗi tiềm ẩn (edge cases), lỗ hổng bảo mật hoặc nghẽn hiệu năng.\n"
                    "2. Đưa ra phiên bản mã nguồn đã được sửa lỗi và tối ưu hóa tốt nhất."
                ),
            ),
        ]

        def on_step_status(p, info, st):
            if st == "STARTING":
                print(f"  ⏳ [{p.upper()}] {info} : Đang thực hiện...")
            elif st == "SUCCESS":
                print(f"  ✅ [{p.upper()}] {info} : [HOÀN THÀNH]")

        pipe_res: PipelineResult = orch.run_pipeline(task, steps, status_callback=on_step_status)

        print("\n" + "═" * 78)
        print(f"  🎉 KẾT QUẢ DÂY CHUYỀN HOÀN TẤT (Tổng thời gian: {pipe_res.total_latency_ms / 1000:.2f}s)")
        print("═" * 78)
        print(pipe_res.final_output)
        print("═" * 78)


def run_role_orchestration_menu():
    """Menu chọn tính năng của Phase 9."""
    while True:
        print("\n" + "═" * 60)
        print("   🎭 MULTI-PERSONA ROLE ORCHESTRATION & PIPELINE (PHASE 9)")
        print("═" * 60)
        print("  1. 🏛️ Hội Đồng Chuyên Gia (Tech + Security + Business)")
        print("  2. ⛓️ Dây Chuyền Tuần Tự (Planner ➔ Coder ➔ Reviewer)")
        print("  0. 🚪 Quay lại Menu Chính")
        print("═" * 60)

        try:
            choice = input("👉 Lựa chọn của bạn (0-2): ").strip()
            if choice == "1":
                run_council_of_experts()
            elif choice == "2":
                run_sequential_pipeline()
            elif choice in ("0", "exit", "quit"):
                break
            else:
                print("[!] Lựa chọn không hợp lệ.")
        except (KeyboardInterrupt, EOFError):
            print("\nĐã quay lại.")
            break
