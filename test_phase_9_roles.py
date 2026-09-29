"""Kiểm thử tự động Phase 9: Multi-Persona Role Assignment & Sequential Pipeline."""

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
from orchestrator import AIOrchestrator
from orchestrator.models import RoleAssignment, PipelineStep, PipelineResult, SynthesizerResult
from orchestrator.personas import BUILTIN_PERSONAS


def test_council_of_experts():
    print("\n" + "=" * 75)
    print("TEST 1: HỘI ĐỒNG CHUYÊN GIA (COUNCIL OF EXPERTS)")
    print("=" * 75)

    orch = AIOrchestrator()
    available = orch.provider_names
    print(f"[*] Providers sẵn sàng: {', '.join(available).upper()}")

    # Tạo phân vai
    roles = []
    if "groq" in available:
        roles.append(RoleAssignment(
            provider="groq",
            model="openai/gpt-oss-120b",
            role_name="Senior Technical Architect",
            system_prompt=BUILTIN_PERSONAS["tech_lead"]["system_prompt"]
        ))
        roles.append(RoleAssignment(
            provider="groq",
            model="qwen/qwen3.8-27b",
            role_name="Product & Business Analyst",
            system_prompt=BUILTIN_PERSONAS["business_analyst"]["system_prompt"]
        ))
    if "gemini" in available:
        roles.append(RoleAssignment(
            provider="gemini",
            model="gemini-3.1-flash-lite",
            role_name="Cybersecurity Specialist",
            system_prompt=BUILTIN_PERSONAS["security_expert"]["system_prompt"]
        ))

    problem = "Đề xuất kiến trúc hệ thống xác thực người dùng (Authentication) cho ứng dụng tài chính ngân hàng."
    print(f"[?] Đề tài: '{problem}'\n")

    res: SynthesizerResult = orch.synthesize_with_roles(
        prompt=problem,
        role_assignments=roles,
        synthesizer_provider="gemini" if "gemini" in available else "groq",
        synthesizer_model="gemini-3.1-flash-lite" if "gemini" in available else "openai/gpt-oss-120b",
    )

    print(f"[✓] Tổng hợp thành công bởi: {res.synthesizer_provider.upper()} ({res.synthesizer_model})")
    print(f"    - Thời gian: {res.total_latency_ms:,.0f} ms")
    print(f"    - Các bên tham gia: {', '.join(res.successful_providers)}")
    print("\nTrích đoạn kết quả tổng hợp:")
    print(res.final_answer[:450] + "...\n")
    assert res.final_answer.strip() != "", "Final answer must not be empty"


def test_sequential_pipeline():
    print("\n" + "=" * 75)
    print("TEST 2: DÂY CHUYỀN TUẦN TỰ (SEQUENTIAL PIPELINE CHAIN)")
    print("=" * 75)

    orch = AIOrchestrator()
    available = orch.provider_names

    p1 = "groq" if "groq" in available else "gemini"
    m1 = "openai/gpt-oss-120b" if "groq" in available else "gemini-3.1-flash-lite"

    p2 = "gemini" if "gemini" in available else "groq"
    m2 = "gemini-3.1-flash-lite" if "gemini" in available else "openai/gpt-oss-120b"

    steps = [
        PipelineStep(
            step_id=1,
            step_name="Planner",
            provider=p1,
            model=m1,
            prompt_template="Hãy lập dàn ý 3 gạch đầu dòng ngắn gọn về thuật toán tính số Fibonacci bằng Python: {input}",
        ),
        PipelineStep(
            step_id=2,
            step_name="Coder",
            provider=p2,
            model=m2,
            prompt_template="Dựa trên dàn ý sau:\n{previous_output}\nHãy viết 1 hàm Python ngắn gọn tính số Fibonacci có kiểm tra đầu vào.",
        ),
    ]

    pipe_res: PipelineResult = orch.run_pipeline("Tính số Fibonacci thứ n", steps)
    print(f"[✓] Pipeline hoàn thành {len(pipe_res.step_outputs)} bước trong {pipe_res.total_latency_ms:,.0f} ms")
    for step_out in pipe_res.step_outputs:
        print(f"    - Bước {step_out['step_id']} ({step_out['step_name']}) [{step_out['provider'].upper()}]: {step_out['latency_ms']:,.0f} ms")
    print("\nMã nguồn đầu ra cuối cùng:")
    print(pipe_res.final_output[:350] + "...")
    assert pipe_res.final_output.strip() != "", "Pipeline output must not be empty"


def main():
    load_env_files()
    print("=" * 75)
    print("   BẮT ĐẦU KIỂM THỬ: PHASE 9 ROLE ORCHESTRATION & PIPELINES")
    print("=" * 75)
    test_council_of_experts()
    test_sequential_pipeline()
    print("\n" + "=" * 75)
    print("   🎉 TẤT CẢ TEST PHASE 9 ĐỀU ĐẠT CHUẨN XUẤT SẮC (PASSED)!")
    print("=" * 75)


if __name__ == "__main__":
    main()
