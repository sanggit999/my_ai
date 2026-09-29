"""Kiểm thử tự động Phase 10: Dây chuyền 3 chặng ĐẦU - THÂN - CUỐI Tự Phục Hồi.

Mục tiêu kiểm thử:
1. Kiểm tra luồng chạy bình thường khi cả 3 chặng đều chọn model hoạt động.
2. Kiểm tra kịch bản 'Con nào chết thì con còn sống nhảy vào gánh':
   - Cố tình gán Chặng THÂN vào model chết/hết credit (OpenAI 429 Quota).
   - Quan sát hệ thống tự bắt lỗi 429 và điều động AI còn sống (Groq/Gemini) nhảy vào gánh.
   - Dây chuyền hoàn thành trọn vẹn 3 chặng mà không bị gián đoạn.
"""

import sys
from pathlib import Path

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
from config.pipeline_stages import get_pipeline_stages, set_stage_config, reset_pipeline_stages
from orchestrator.pipeline_engine import ThreeStagePipeline, ThreeStageResult


def test_normal_pipeline():
    print("\n" + "=" * 70)
    print("TEST 1: DÂY CHUYỀN 3 CHẶNG BÌNH THƯỜNG (Groq ➔ Gemini ➔ Groq)")
    print("=" * 70)
    
    # Thiết lập cấu hình mặc định (Groq -> Gemini -> Groq)
    reset_pipeline_stages()
    pipeline = ThreeStagePipeline()
    
    test_prompt = "Hãy giải thích ngắn gọn nguyên lý Active-Survivor trong hệ thống phân tán trong 3 ý chính."
    print(f"👉 Prompt: {test_prompt}")
    
    def on_status(stage_key, stage_name, prov, msg):
        print(f"   [{stage_name}] ({prov.upper()}) ➔ {msg}")
        
    result = pipeline.run(test_prompt, status_callback=on_status)
    
    print("\n--- KẾT QUẢ TEST 1 ---")
    print(f"• Tổng số chặng hoàn thành: {len(result.stages)}/3")
    print(f"• Tổng thời gian: {result.total_latency_ms:.0f} ms")
    print(f"• Số lần cứu hộ (Failover): {result.failovers_occurred}")
    print(f"• Nội dung kết quả cuối ({len(result.final_content)} ký tự):\n{result.final_content[:200]}...")
    
    assert len(result.stages) == 3, "Phải hoàn thành đủ 3 chặng!"
    assert result.final_content, "Phải có kết quả cuối cùng!"
    print("✅ TEST 1 THÀNH CÔNG!\n")


def test_survivor_failover():
    print("\n" + "=" * 70)
    print("TEST 2: CƠ CHẾ 'CON NÀO CHẾT THÌ CON CÒN SỐNG NHẢY VÀO GÁNH'")
    print("  Kịch bản: Cố tình gán Chặng THÂN = OpenAI (Hết tiền / 429 Quota)")
    print("=" * 70)
    
    # Gán Chặng THÂN vào OpenAI
    set_stage_config("body", "openai", "gpt-4o-mini")
    print("⚙️ Đã cấu hình Chặng 2 (THÂN) = OPENAI (gpt-4o-mini) [Model biết chắc sẽ chết vì 429]")
    
    pipeline = ThreeStagePipeline()
    test_prompt = "Viết hàm Python tính giai thừa đệ quy có memoization."
    
    events = []
    def on_status(stage_key, stage_name, prov, msg):
        events.append((stage_key, prov, msg))
        print(f"   [{stage_name}] ({prov.upper()}) ➔ {msg}")
        
    result = pipeline.run(test_prompt, status_callback=on_status)
    
    print("\n--- KẾT QUẢ TEST 2 ---")
    head_st = result.stages[0]
    body_st = result.stages[1]
    tail_st = result.stages[2]
    
    print(f"• Chặng 1 (ĐẦU) : Chỉ định={head_st.assigned_provider} ➔ Thực tế={head_st.executed_provider} (Failover={head_st.is_failover})")
    print(f"• Chặng 2 (THÂN): Chỉ định={body_st.assigned_provider} ➔ Thực tế={body_st.executed_provider} (Failover={body_st.is_failover})")
    print(f"  ↳ Lý do Failover: {body_st.failover_reason}")
    print(f"• Chặng 3 (CUỐI): Chỉ định={tail_st.assigned_provider} ➔ Thực tế={tail_st.executed_provider} (Failover={tail_st.is_failover})")
    print(f"• Tổng số lần cứu hộ: {result.failovers_occurred}")
    print(f"• Bản kiểm duyệt cuối cùng:\n{result.final_content[:250]}...\n")
    
    assert body_st.assigned_provider == "openai", "Chặng THÂN phải được gán cho openai"
    assert body_st.is_failover is True, "Chặng THÂN phải kích hoạt failover do OpenAI chết!"
    assert body_st.executed_provider in ("groq", "gemini"), f"AI nhảy vào gánh phải là Groq hoặc Gemini, thực tế: {body_st.executed_provider}"
    assert result.failovers_occurred >= 1, "Phải ghi nhận ít nhất 1 lần failover!"
    assert len(result.final_content) > 50, "Kết quả cuối cùng vẫn phải được hoàn thành xuất sắc!"
    
    # Khôi phục lại cấu hình gốc
    reset_pipeline_stages()
    print("🔄 Đã khôi phục cấu hình dây chuyền mặc định.")
    print("✅ TEST 2 THÀNH CÔNG: CON CÒN SỐNG ĐÃ NHẢY VÀO GÁNH HOÀN HẢO!\n")


if __name__ == "__main__":
    load_env_files()
    try:
        test_normal_pipeline()
        test_survivor_failover()
        print("🎉 TẤT CẢ CÁC BÀI KIỂM THỬ PHASE 10 ĐỀU ĐẠT CHUẨN XUẤT SẮC!")
    except Exception as e:
        reset_pipeline_stages()
        print(f"\n❌ LỖI KIỂM THỬ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
