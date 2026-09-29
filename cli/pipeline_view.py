"""Pipeline View - Giao diện CLI tương tác Dây chuyền 3 chặng ĐẦU - THÂN - CUỐI (Phase 10).

Hỗ trợ:
- Hiển thị trực quan cấu hình 3 chặng hiện tại.
- Lệnh /setup để cấu hình con nào làm ĐẦU, THÂN, CUỐI.
- Cơ chế Active-Survivor: Khi 1 con chết, con còn sống nhảy vào gánh ngay lập tức.
- Lệnh /view để soi chi tiết dàn ý của ĐẦU, bản thảo của THÂN, và thẩm định của CUỐI.
"""

import sys
from typing import Optional

from orchestrator.pipeline_engine import ThreeStagePipeline, ThreeStageResult
from config.pipeline_stages import get_pipeline_stages, set_stage_config, reset_pipeline_stages
from config.active_models import get_active_model
from cli.selector import CLISelector
from providers import get_provider


def _print_pipeline_header():
    stages = get_pipeline_stages()
    print("\n" + "=" * 70)
    print("   ⛓️ DÂY CHUYỀN 3 CHẶNG TỰ PHỤC HỒI (ACTIVE-SURVIVOR PIPELINE)")
    print("=" * 70)
    
    stage_titles = {
        "head": ("Chặng 1: ĐẦU ", "Planner & Architect"),
        "body": ("Chặng 2: THÂN", "Core Implementer"),
        "tail": ("Chặng 3: CUỐI", "Auditor & Polisher"),
    }
    
    for k in ("head", "body", "tail"):
        title, role = stage_titles[k]
        cfg = stages.get(k, {})
        p = cfg.get("provider", "groq")
        m = cfg.get("model", "default")
        print(f"  [{title}] ➔ {p.upper():<9} : {m:<28} ({role})")
        
    print("-" * 70)
    print("  🛡️ Nguyên tắc: Con nào chết (429/400/503/lỗi) ➔ Con sống nhảy vào gánh!")
    print("  💡 Lệnh: /setup (Đổi AI từng chặng) | /reset (Mặc định) | /view (Xem từng chặng) | /exit")
    print("=" * 70 + "\n")


def _setup_stage_interactive():
    print("\n--- 🛠️ CẤU HÌNH DÂY CHUYỀN 3 CHẶNG ---")
    print("1. Chặng 1: ĐẦU  (Planner / Dàn ý kiến trúc)")
    print("2. Chặng 2: THÂN (Core Implementer / Triển khai code & nội dung)")
    print("3. Chặng 3: CUỐI (Auditor & Polisher / Kiểm toán & Trau chuốt)")
    print("0. Quay lại")
    
    choice = input("\n👉 Chọn chặng muốn thay đổi (0-3): ").strip()
    stage_map = {"1": "head", "2": "body", "3": "tail"}
    if choice not in stage_map:
        return
        
    stage_key = stage_map[choice]
    stage_name = "ĐẦU" if choice == "1" else ("THÂN" if choice == "2" else "CUỐI")
    
    print(f"\n--- Chọn Provider cho Chặng {stage_name} ---")
    providers = ["groq", "gemini", "openai", "anthropic"]
    for i, p in enumerate(providers, 1):
        print(f"  {i}. {p.upper()}")
        
    p_choice = input(f"👉 Chọn Provider (1-{len(providers)}) [Mặc định 1]: ").strip() or "1"
    try:
        p_idx = int(p_choice) - 1
        if 0 <= p_idx < len(providers):
            selected_provider = providers[p_idx]
        else:
            selected_provider = "groq"
    except ValueError:
        selected_provider = "groq"
        
    # Cho phép chọn model của provider đó
    prov_instance = get_provider(selected_provider)
    print(f"\nĐang tải danh sách model cho {selected_provider.upper()}...")
    try:
        models = prov_instance.list_models()
        if models:
            selector = CLISelector(models)
            selected_model_info = selector.select(
                title=f"Chọn Model cho Chặng {stage_name} ({selected_provider.upper()}):"
            )
            selected_model = selected_model_info.id if selected_model_info else get_active_model(selected_provider)
        else:
            selected_model = get_active_model(selected_provider)
    except Exception as e:
        print(f"⚠️ Không thể tải danh sách model ({e}). Sử dụng model active mặc định.")
        selected_model = get_active_model(selected_provider)
        
    set_stage_config(stage_key, selected_provider, selected_model)
    print(f"\n✅ Đã lưu: Chặng {stage_name} ➔ {selected_provider.upper()} ({selected_model})\n")


def pipeline_loop():
    """Vòng lặp CLI chính cho Dây chuyền 3 chặng."""
    pipeline = ThreeStagePipeline()
    last_result: Optional[ThreeStageResult] = None
    
    _print_pipeline_header()
    
    while True:
        try:
            user_input = input("User ➔ ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Đang thoát về menu chính...")
            break
            
        if not user_input:
            continue
            
        cmd = user_input.lower()
        if cmd in ("/exit", "/quit", "exit", "quit"):
            print("👋 Đã thoát khỏi Dây chuyền 3 chặng.")
            break
            
        if cmd == "/setup":
            _setup_stage_interactive()
            _print_pipeline_header()
            continue
            
        if cmd == "/reset":
            reset_pipeline_stages()
            print("\n🔄 Đã khôi phục cấu hình dây chuyền về mặc định ban đầu.")
            _print_pipeline_header()
            continue
            
        if cmd == "/view":
            if not last_result:
                print("\n⚠️ Chưa có lượt chạy nào trước đó để xem chi tiết.\n")
                continue
                
            print("\n" + "#" * 70)
            print(f"🔍 CHI TIẾT CÁC CHẶNG CỦA PROMPT: '{last_result.input_prompt[:50]}...'")
            print("#" * 70)
            for st in last_result.stages:
                failover_badge = " [🚨 NHẢY VÀO GÁNH]" if st.is_failover else " [CHÍNH THỨC]"
                print(f"\n--- {st.stage_name} {failover_badge} ---")
                print(f"  • Chỉ định : {st.assigned_provider.upper()} ({st.assigned_model})")
                print(f"  • Thực thi : {st.executed_provider.upper()} ({st.executed_model})")
                if st.is_failover:
                    print(f"  • Lý do    : {st.failover_reason}")
                print(f"  • Thời gian: {st.latency_ms:.0f} ms")
                print(f"\n[NỘI DUNG XUẤT RA TỪ CHẶNG]:\n{st.output_content}\n")
            print("#" * 70 + "\n")
            continue
            
        # Callback hiển thị tiến độ thời gian thực
        def status_callback(stage_key: str, stage_name: str, prov: str, status_msg: str):
            if status_msg.startswith("STARTING:"):
                model = status_msg.split(":", 1)[1]
                print(f"  ⏳ {stage_name}: [{prov.upper()}: {model}] đang xử lý...")
            elif status_msg.startswith("SUCCESS:"):
                model = status_msg.split(":", 1)[1]
                print(f"  ✅ {stage_name}: [{prov.upper()}: {model}] hoàn tất!")
            elif status_msg.startswith("FAILED:"):
                reason = status_msg.split(":", 1)[1]
                print(f"  ❌ {stage_name}: [{prov.upper()}] GẶP SỰ CỐ: {reason}")
            elif status_msg.startswith("FAILOVER_STEP_IN:"):
                surv_m = status_msg.split(":", 1)[1]
                print(f"  🚨 CON CÒN SỐNG NHẢY VÀO GÁNH: [{prov.upper()}: {surv_m}] đang tiếp quản!")
                
        print("\n⚙️ BẮT ĐẦU VẬN HÀNH DÂY CHUYỀN 3 CHẶNG...")
        try:
            last_result = pipeline.run(user_input, status_callback=status_callback)
            
            print("\n" + "=" * 70)
            print("🏁 KẾT QUẢ CUỐI CÙNG (FINAL SYNTHESIZED ANSWER)")
            print("=" * 70)
            print(last_result.final_content.strip())
            print("=" * 70)
            
            # Tóm tắt số liệu
            failover_info = f"🚨 {last_result.failovers_occurred} chặng đã được con sống nhảy vào gánh" if last_result.failovers_occurred > 0 else "✨ Cả 3 chặng mượt mà"
            print(f"⏱️ Tổng thời gian: {last_result.total_latency_ms/1000:.2f}s | {failover_info} | (Gõ /view để soi chi tiết từng chặng)\n")
            
        except Exception as e:
            print(f"\n❌ Lỗi hệ thống dây chuyền: {e}\n")


if __name__ == "__main__":
    pipeline_loop()
