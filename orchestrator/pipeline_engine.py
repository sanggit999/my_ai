"""ThreeStagePipeline Engine - Dây chuyền 3 chặng ĐẦU - THÂN - CUỐI Tự Phục Hồi (Phase 10).

Nguyên tắc cốt lõi: "Con nào chết thì con còn sống nhảy vào gánh!"
- Bắt lỗi độc lập ở từng chặng (429 Quota, 400 Balance, 503 Overload, Timeout).
- Tự động phát hiện AI còn sống và chuyển giao dữ liệu để AI sống nhảy vào thay thế ngay lập tức.
- Đảm bảo dây chuyền không bao giờ bị đứt đoạn.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Callable

from providers.base import BaseProvider
from providers import get_available_provider_configs, get_provider
from config.pipeline_stages import get_pipeline_stages, set_stage_config
from config.active_models import get_active_model
from models.unified_response import UnifiedResponse


@dataclass
class StageOutput:
    """Kết quả thực thi của một chặng trong dây chuyền."""
    stage_key: str                     # 'head' | 'body' | 'tail'
    stage_name: str                    # 'Chặng 1: ĐẦU', 'Chặng 2: THÂN', 'Chặng 3: CUỐI'
    assigned_provider: str             # Provider được chỉ định ban đầu
    assigned_model: str                # Model được chỉ định ban đầu
    executed_provider: str             # Provider thực tế đã chạy (có thể là con nhảy vào cứu)
    executed_model: str                # Model thực tế đã chạy
    is_failover: bool = False          # True nếu con ban đầu chết và con khác nhảy vào gánh
    failover_reason: Optional[str] = None
    output_content: str = ""
    latency_ms: float = 0.0


@dataclass
class ThreeStageResult:
    """Kết quả tổng thể toàn bộ dây chuyền 3 chặng."""
    input_prompt: str
    stages: List[StageOutput] = field(default_factory=list)
    final_content: str = ""
    total_latency_ms: float = 0.0
    failovers_occurred: int = 0


class ThreeStagePipeline:
    """Điều phối dây chuyền 3 chặng ĐẦU - THÂN - CUỐI với cơ chế Active-Survivor Failover."""

    def __init__(self):
        self.available_configs = get_available_provider_configs()
        self.provider_instances: Dict[str, BaseProvider] = {
            p: get_provider(p) for p in self.available_configs.keys()
        }

    def _get_survivor_candidates(self, exclude: set) -> List[Tuple[str, str]]:
        """Tìm danh sách các AI còn sống có thể nhảy vào cứu trợ theo thứ tự ưu tiên."""
        priority_survivors = ["groq", "gemini", "openai", "anthropic"]
        candidates = []
        for p in priority_survivors:
            if p not in exclude and p in self.provider_instances:
                prov = self.provider_instances[p]
                if prov.is_ready:
                    candidates.append((p, get_active_model(p)))

        for p, prov in self.provider_instances.items():
            if p not in exclude and prov.is_ready:
                pair = (p, get_active_model(p))
                if pair not in candidates:
                    candidates.append(pair)

        return candidates

    def _execute_stage(
        self,
        stage_key: str,
        stage_name: str,
        input_prompt: str,
        previous_output: str,
        status_callback: Optional[Callable[[str, str, str, str], None]] = None
    ) -> StageOutput:
        """Thực thi một chặng đơn lẻ kèm cơ chế 'Con nào chết thì con sống nhảy vào'."""
        stages_config = get_pipeline_stages()
        cfg = stages_config.get(stage_key, {})

        assigned_p = cfg.get("provider", "groq")
        assigned_m = cfg.get("model", get_active_model(assigned_p))
        prompt_tmpl = cfg.get("prompt_template", "{previous_output}\n\n{input}")

        # Chuẩn bị nội dung prompt cho chặng này
        formatted_prompt = prompt_tmpl.format(
            input=input_prompt,
            previous_output=previous_output
        )

        stage_start = time.perf_counter()

        # 1. Thử gọi con được chỉ định ban đầu
        if status_callback:
            status_callback(stage_key, stage_name, assigned_p, f"STARTING:{assigned_m}")

        try:
            provider = self.provider_instances.get(assigned_p)
            if not provider or not provider.is_ready:
                raise ValueError(f"Provider '{assigned_p}' chưa được cấu hình API Key.")

            resp: UnifiedResponse = provider.generate(
                model=assigned_m,
                messages=[{"role": "user", "content": formatted_prompt}],
            )
            elapsed = (time.perf_counter() - stage_start) * 1000

            if status_callback:
                status_callback(stage_key, stage_name, assigned_p, f"SUCCESS:{assigned_m}")

            return StageOutput(
                stage_key=stage_key,
                stage_name=stage_name,
                assigned_provider=assigned_p,
                assigned_model=assigned_m,
                executed_provider=assigned_p,
                executed_model=assigned_m,
                is_failover=False,
                output_content=resp.content,
                latency_ms=elapsed,
            )

        except Exception as e:
            # CON ĐƯỢC CHỈ ĐỊNH BỊ CHẾT (429, 400, 503, Timeout, v.v.)
            err_text = str(e)
            if "429" in err_text:
                err_summary = "429 Quota/Hạn mức đã hết"
            elif "400" in err_text and "credit" in err_text.lower():
                err_summary = "400 Số dư Credit bằng 0"
            elif "503" in err_text:
                err_summary = "503 Server model quá tải tạm thời"
            else:
                err_summary = err_text[:60]

            if status_callback:
                status_callback(stage_key, stage_name, assigned_p, f"FAILED:{err_summary}")

            # 2. KÍCH HOẠT QUY TẮC: CON CÒN SỐNG NHẢY VÀO GÁNH!
            tried_providers = {assigned_p}
            failover_errors = []

            while True:
                candidates = self._get_survivor_candidates(exclude=tried_providers)
                if not candidates:
                    raise RuntimeError(
                        f"Chặng '{stage_name}' thất bại: Cả model gốc ({assigned_p}) và tất cả AI cứu hộ đều không thể phản hồi! "
                        f"Lỗi: {failover_errors}"
                    )

                surv_p, surv_m = candidates[0]
                tried_providers.add(surv_p)

                if status_callback:
                    status_callback(stage_key, stage_name, surv_p, f"FAILOVER_STEP_IN:{surv_m}")

                try:
                    surv_provider = self.provider_instances[surv_p]
                    surv_resp: UnifiedResponse = surv_provider.generate(
                        model=surv_m,
                        messages=[{"role": "user", "content": formatted_prompt}],
                    )
                    elapsed = (time.perf_counter() - stage_start) * 1000

                    if status_callback:
                        status_callback(stage_key, stage_name, surv_p, f"SUCCESS:{surv_m}")

                    return StageOutput(
                        stage_key=stage_key,
                        stage_name=stage_name,
                        assigned_provider=assigned_p,
                        assigned_model=assigned_m,
                        executed_provider=surv_p,
                        executed_model=surv_m,
                        is_failover=True,
                        failover_reason=err_summary,
                        output_content=surv_resp.content,
                        latency_ms=elapsed,
                    )
                except Exception as surv_err:
                    surv_err_text = str(surv_err)
                    if "429" in surv_err_text:
                        s_summary = "429 Quota hết"
                    elif "400" in surv_err_text:
                        s_summary = "400 Hết Credit"
                    else:
                        s_summary = surv_err_text[:40]
                    failover_errors.append(f"{surv_p}: {s_summary}")
                    if status_callback:
                        status_callback(stage_key, stage_name, surv_p, f"FAILED:{s_summary}")

    def run(
        self,
        prompt: str,
        status_callback: Optional[Callable[[str, str, str, str], None]] = None
    ) -> ThreeStageResult:
        """Vận hành toàn bộ dây chuyền 3 chặng tuần tự: ĐẦU -> THÂN -> CUỐI."""
        total_start = time.perf_counter()
        stages_output: List[StageOutput] = []
        failovers = 0

        # CHẶNG 1: ĐẦU (Head - Blueprint / Dàn ý)
        head_res = self._execute_stage(
            stage_key="head",
            stage_name="Chặng 1: ĐẦU (Blueprint & Kiến trúc)",
            input_prompt=prompt,
            previous_output=prompt,
            status_callback=status_callback
        )
        stages_output.append(head_res)
        if head_res.is_failover:
            failovers += 1

        # CHẶNG 2: THÂN (Body - Core Execution / Triển khai)
        body_res = self._execute_stage(
            stage_key="body",
            stage_name="Chặng 2: THÂN (Triển khai cốt lõi & Code)",
            input_prompt=prompt,
            previous_output=head_res.output_content,
            status_callback=status_callback
        )
        stages_output.append(body_res)
        if body_res.is_failover:
            failovers += 1

        # CHẶNG 3: CUỐI (Tail - Quality Audit & Polishing / Thẩm định & Trau chuốt)
        tail_res = self._execute_stage(
            stage_key="tail",
            stage_name="Chặng 3: CUỐI (Kiểm toán & Trau chuốt)",
            input_prompt=prompt,
            previous_output=body_res.output_content,
            status_callback=status_callback
        )
        stages_output.append(tail_res)
        if tail_res.is_failover:
            failovers += 1

        total_elapsed = (time.perf_counter() - total_start) * 1000

        return ThreeStageResult(
            input_prompt=prompt,
            stages=stages_output,
            final_content=tail_res.output_content,
            total_latency_ms=total_elapsed,
            failovers_occurred=failovers,
        )
