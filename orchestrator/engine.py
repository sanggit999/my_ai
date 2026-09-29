"""AI Orchestrator Engine - Điều phối đa mô hình và tổng hợp trí tuệ AI (Phase 8).

Cung cấp:
- Fan-out song song đa luồng tới nhiều AI (OpenAI, Claude, Gemini, Groq).
- Xử lý lỗi độc lập và timeout thread-safe.
- AI Synthesizer: Thẩm định và tổng hợp các câu trả lời thành Final Answer tối ưu nhất.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Tuple, Callable

from providers.base import BaseProvider
from providers import get_available_provider_configs, get_provider
from models.unified_response import UnifiedResponse
from orchestrator.models import (
    ProviderExecutionResult,
    SynthesizerResult,
    RoleAssignment,
    PipelineStep,
    PipelineResult,
)
from config.active_models import get_all_active_models, get_active_model




class AIOrchestrator:
    """Bộ điều phối trung tâm cho toàn bộ hệ thống Multi-AI."""

    def __init__(self, target_providers: Optional[List[str]] = None):
        """Khởi tạo Orchestrator với danh sách các provider mong muốn hoặc tự động nhận diện."""
        available = get_available_provider_configs()
        if target_providers:
            self.provider_names = [p for p in target_providers if p in available]
        else:
            self.provider_names = list(available.keys())

        # Khởi tạo các provider instances
        self.providers: Dict[str, BaseProvider] = {
            p: get_provider(p) for p in self.provider_names
        }

    def _execute_single(
        self,
        provider_name: str,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> ProviderExecutionResult:
        """Thực thi gọi 1 provider đơn lẻ trong 1 worker thread."""
        provider = self.providers.get(provider_name)
        if not provider or not provider.is_ready:
            return ProviderExecutionResult(
                provider=provider_name,
                model=model_name,
                success=False,
                error_message="Provider chưa được cấu hình API Key.",
            )

        start_time = time.perf_counter()
        try:
            resp: UnifiedResponse = provider.generate(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
            )
            elapsed = (time.perf_counter() - start_time) * 1000
            return ProviderExecutionResult(
                provider=provider_name,
                model=model_name,
                success=True,
                response=resp,
                latency_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            err_text = str(e)
            # Rút ngắn các thông báo lỗi dài
            if "429" in err_text:
                err_text = "429: Hạn mức gọi API (Quota/Rate Limit) đã hết hoặc bị giới hạn."
            elif "400" in err_text and "credit" in err_text.lower():
                err_text = "400: Tài khoản chưa nạp Credit hoặc số dư bằng 0."
            elif "503" in err_text:
                err_text = "503: Máy chủ của model đang quá tải tạm thời."

            return ProviderExecutionResult(
                provider=provider_name,
                model=model_name,
                success=False,
                error_message=err_text,
                latency_ms=elapsed,
            )

    def broadcast(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        custom_models: Optional[Dict[str, str]] = None,
        status_callback: Optional[Callable[[str, str, str], None]] = None,
        timeout_sec: int = 35
    ) -> List[ProviderExecutionResult]:
        """Gửi câu hỏi đồng thời (Fan-out) tới tất cả các Provider đã cấu hình."""
        if not self.provider_names:
            return []

        models_map = get_all_active_models()
        if custom_models:
            models_map.update(custom_models)

        results: List[ProviderExecutionResult] = []

        with ThreadPoolExecutor(max_workers=len(self.provider_names)) as executor:
            future_to_provider = {}
            for p in self.provider_names:
                m = models_map.get(p, "default")
                if status_callback:
                    status_callback(p, m, "STARTING")
                future = executor.submit(self._execute_single, p, m, prompt, system_prompt)
                future_to_provider[future] = (p, m)

            for future in as_completed(future_to_provider, timeout=timeout_sec):
                p, m = future_to_provider[future]
                try:
                    res: ProviderExecutionResult = future.result()
                    results.append(res)
                    if status_callback:
                        status = "SUCCESS" if res.success else f"FAILED: {res.error_message}"
                        status_callback(p, m, status)
                except Exception as exc:
                    err_res = ProviderExecutionResult(
                        provider=p,
                        model=m,
                        success=False,
                        error_message=f"Thread error: {exc}",
                    )
                    results.append(err_res)
                    if status_callback:
                        status_callback(p, m, f"FAILED: {exc}")

        # Sắp xếp lại thứ tự kết quả theo danh sách provider ban đầu
        p_order = {name: idx for idx, name in enumerate(self.provider_names)}
        results.sort(key=lambda r: p_order.get(r.provider, 99))
        return results

    def synthesize(
        self,
        prompt: str,
        synthesizer_provider: Optional[str] = None,
        synthesizer_model: Optional[str] = None,
        status_callback: Optional[Callable[[str, str, str], None]] = None
    ) -> SynthesizerResult:
        """Thực hiện quy trình hoàn chỉnh: Fan-out tới các AI -> Tổng hợp thành Final Answer."""
        total_start = time.perf_counter()

        # BƯỚC 1: Phân phối song song (Fan-out)
        individual_results = self.broadcast(prompt, status_callback=status_callback)

        successful_results = [r for r in individual_results if r.success and r.response and r.response.content.strip()]
        successful_names = [r.provider.upper() for r in successful_results]

        if not successful_results:
            # Tất cả AI đều thất bại
            total_elapsed = (time.perf_counter() - total_start) * 1000
            failed_reasons = "\n".join(f"- {r.provider.upper()}: {r.error_message}" for r in individual_results)
            return SynthesizerResult(
                prompt=prompt,
                individual_results=individual_results,
                synthesizer_provider="none",
                synthesizer_model="none",
                final_answer=f"[!] Rất tiếc, tất cả các mô hình AI đều không thể phản hồi:\n{failed_reasons}",
                total_latency_ms=total_elapsed,
                successful_providers=[],
            )

        # Nếu chỉ có duy nhất 1 AI thành công, không cần tổng hợp
        if len(successful_results) == 1:
            only = successful_results[0]
            total_elapsed = (time.perf_counter() - total_start) * 1000
            return SynthesizerResult(
                prompt=prompt,
                individual_results=individual_results,
                synthesizer_provider=only.provider,
                synthesizer_model=only.model,
                final_answer=only.response.content + f"\n\n*(Lưu ý: Chỉ có {only.provider.upper()} phản hồi thành công, các AI khác bị lỗi/hết quota nên không cần bước tổng hợp)*",
                total_latency_ms=total_elapsed,
                successful_providers=successful_names,
            )

        # BƯỚC 2: Thẩm định & Tổng hợp (Synthesizer / Meta-Judge)
        # Chọn provider để tổng hợp (ưu tiên provider thành công)
        synth_p_name = synthesizer_provider
        if not synth_p_name or synth_p_name not in [r.provider for r in successful_results]:
            # Ưu tiên Gemini hoặc Groq trong các bên thành công
            avail_success = [r.provider for r in successful_results]
            if "gemini" in avail_success:
                synth_p_name = "gemini"
            elif "groq" in avail_success:
                synth_p_name = "groq"
            else:
                synth_p_name = avail_success[0]

        synth_m_name = synthesizer_model or get_active_model(synth_p_name)
        synth_provider = self.providers[synth_p_name]

        if status_callback:
            status_callback(synth_p_name, synth_m_name, "SYNTHESIZING")

        # Chuẩn bị nội dung tổng hợp
        formatted_answers = []
        for r in successful_results:
            formatted_answers.append(
                f"=== [CÂU TRẢ LỜI TỪ {r.provider.upper()} (Model: {r.model})] ===\n{r.response.content.strip()}"
            )
        answers_text = "\n\n".join(formatted_answers)

        synthesis_prompt = f"""Bạn là Chuyên gia Tổng hợp & Thẩm định AI (AI Meta-Synthesizer).
Dưới đây là một câu hỏi của người dùng và các câu trả lời độc lập nhận được từ các mô hình AI khác nhau ({', '.join(successful_names)}).

=== CÂU HỎI GỐC CỦA NGƯỜI DÙNG ===
{prompt}

=== CÁC CÂU TRẢ LỜI TỪ TỪNG MÔ HÌNH AI ===
{answers_text}

=== NHIỆM VỤ CỦA BẠN ===
Hãy đọc kỹ các câu trả lời trên, phân tích và tạo ra CÂU TRẢ LỜI TỔNG HỢP TOÀN DIỆN VÀ TỐI ƯU NHẤT (Final Answer) cho người dùng:
1. Đưa ra câu trả lời trực tiếp, rõ ràng, sâu sắc cho câu hỏi.
2. Kết hợp các góc nhìn phong phú, chi tiết chính xác và ví dụ hay từ tất cả các AI.
3. Nếu các AI có điểm mâu thuẫn hoặc sai lệch, hãy phân tích khách quan và đính chính.
4. Trình bày bài bản với định dạng Markdown chuyên nghiệp (sử dụng gạch đầu dòng, bảng biểu hoặc code block nếu phù hợp).
"""

        synth_start = time.perf_counter()
        try:
            synth_resp = synth_provider.generate(
                model=synth_m_name,
                messages=[{"role": "user", "content": synthesis_prompt}],
                system_prompt="Bạn là chuyên gia tổng hợp kiến thức AI khách quan, sâu sắc và chuẩn xác.",
            )
            synth_elapsed = (time.perf_counter() - synth_start) * 1000
            final_text = synth_resp.content
            if status_callback:
                status_callback(synth_p_name, synth_m_name, "SYNTHESIS_DONE")
        except Exception as e:
            synth_elapsed = (time.perf_counter() - synth_start) * 1000
            final_text = f"[!] Lỗi khi chạy AI Synthesizer ({e}).\nHiển thị câu trả lời từ {successful_results[0].provider.upper()}:\n\n{successful_results[0].response.content}"

        total_elapsed = (time.perf_counter() - total_start) * 1000

        return SynthesizerResult(
            prompt=prompt,
            individual_results=individual_results,
            synthesizer_provider=synth_p_name,
            synthesizer_model=synth_m_name,
            final_answer=final_text,
            synthesis_latency_ms=synth_elapsed,
            total_latency_ms=total_elapsed,
            successful_providers=successful_names,
        )

    def synthesize_with_roles(
        self,
        prompt: str,
        role_assignments: List[RoleAssignment],
        synthesizer_provider: Optional[str] = None,
        synthesizer_model: Optional[str] = None,
        status_callback: Optional[Callable[[str, str, str], None]] = None,
        timeout_sec: int = 40
    ) -> SynthesizerResult:
        """Thực thi đa mô hình theo vai trò chuyên biệt (Phase 9 Multi-Persona)."""
        total_start = time.perf_counter()
        individual_results: List[ProviderExecutionResult] = []

        with ThreadPoolExecutor(max_workers=len(role_assignments)) as executor:
            future_to_role = {}
            for role in role_assignments:
                p = role.provider
                m = role.model
                if status_callback:
                    status_callback(p, f"{m} ({role.role_name})", "STARTING")
                future = executor.submit(self._execute_single, p, m, prompt, role.system_prompt)
                future_to_role[future] = role

            for future in as_completed(future_to_role, timeout=timeout_sec):
                role = future_to_role[future]
                try:
                    res: ProviderExecutionResult = future.result()
                    individual_results.append(res)
                    if status_callback:
                        status = "SUCCESS" if res.success else f"FAILED: {res.error_message}"
                        status_callback(role.provider, f"{role.model} ({role.role_name})", status)
                except Exception as exc:
                    err_res = ProviderExecutionResult(
                        provider=role.provider,
                        model=role.model,
                        success=False,
                        error_message=f"Thread error: {exc}",
                    )
                    individual_results.append(err_res)
                    if status_callback:
                        status_callback(role.provider, f"{role.model} ({role.role_name})", f"FAILED: {exc}")

        successful_results = [r for r in individual_results if r.success and r.response and r.response.content.strip()]
        successful_names = [r.provider.upper() for r in successful_results]

        if not successful_results:
            total_elapsed = (time.perf_counter() - total_start) * 1000
            failed_reasons = "\n".join(f"- {r.provider.upper()}: {r.error_message}" for r in individual_results)
            return SynthesizerResult(
                prompt=prompt,
                individual_results=individual_results,
                synthesizer_provider="none",
                synthesizer_model="none",
                final_answer=f"[!] Không có AI nào phản hồi thành công:\n{failed_reasons}",
                total_latency_ms=total_elapsed,
                successful_providers=[],
            )

        if len(successful_results) == 1:
            only = successful_results[0]
            total_elapsed = (time.perf_counter() - total_start) * 1000
            return SynthesizerResult(
                prompt=prompt,
                individual_results=individual_results,
                synthesizer_provider=only.provider,
                synthesizer_model=only.model,
                final_answer=only.response.content + f"\n\n*(Lưu ý: Chỉ có vai diễn {only.provider.upper()} phản hồi thành công)*",
                total_latency_ms=total_elapsed,
                successful_providers=successful_names,
            )

        # Chọn synthesizer
        synth_p_name = synthesizer_provider
        if not synth_p_name or synth_p_name not in [r.provider for r in successful_results]:
            avail_success = [r.provider for r in successful_results]
            if "gemini" in avail_success:
                synth_p_name = "gemini"
            elif "groq" in avail_success:
                synth_p_name = "groq"
            else:
                synth_p_name = avail_success[0]

        synth_m_name = synthesizer_model or get_active_model(synth_p_name)
        synth_provider = self.providers[synth_p_name]

        if status_callback:
            status_callback(synth_p_name, synth_m_name, "SYNTHESIZING")

        # Map vai trò tương ứng cho từng câu trả lời
        role_map = {(r.provider, r.model): r.role_name for r in role_assignments}
        formatted_answers = []
        for r in successful_results:
            r_name = role_map.get((r.provider, r.model), "Chuyên gia")
            formatted_answers.append(
                f"=== [GÓC NHÌN TỪ: {r_name.upper()} ({r.provider.upper()} - {r.model})] ===\n{r.response.content.strip()}"
            )
        answers_text = "\n\n".join(formatted_answers)

        synthesis_prompt = f"""Bạn là Giám Đốc Điều Hành Chiến Lược & Tổng Trưởng Dự Án (Executive Project Director & Chief Strategist).
Dưới đây là một bài toán/câu hỏi lớn và các bản tham mưu độc lập từ các Chuyên Gia trong Hội đồng:

=== BÀI TOÁN GỐC ===
{prompt}

=== CÁC GÓC NHÌN CHUYÊN MÔN TỪ CÁC VAI DIỄN TRONG HỘI ĐỒNG ===
{answers_text}

=== NHIỆM VỤ TỔNG HỢP CHIẾN LƯỢC ===
Hãy tổng hợp các phân tích trên thành MỘT BẢN GIẢI PHÁP CHIẾN LƯỢC TOÀN DIỆN VÀ HOÀN HẢO NHẤT (Executive Final Plan):
1. **Tóm lược Đánh giá Chung**: Nhận định các điểm thống nhất và mục tiêu then chốt.
2. **Giải pháp Kiến trúc & Kỹ thuật Tối ưu**: Chắt lọc giải pháp kỹ thuật, cấu trúc code/hệ thống mạnh mẽ nhất.
3. **Chiến lược An ninh & Kiểm soát Rủi ro**: Biện pháp bảo mật, phòng ngừa rủi ro tương ứng với kiến trúc đã chọn.
4. **Hiệu quả Kinh doanh & Kế hoạch Thực thi**: Lộ trình triển khai, chi phí và giá trị thu lại.
5. Trình bày bài bản, sắc sảo, dùng Markdown chuyên nghiệp.
"""

        synth_start = time.perf_counter()
        try:
            synth_resp = synth_provider.generate(
                model=synth_m_name,
                messages=[{"role": "user", "content": synthesis_prompt}],
                system_prompt="Bạn là Chief Strategist điều phối và tổng hợp chiến lược cấp cao.",
            )
            synth_elapsed = (time.perf_counter() - synth_start) * 1000
            final_text = synth_resp.content
            if status_callback:
                status_callback(synth_p_name, synth_m_name, "SYNTHESIS_DONE")
        except Exception as e:
            synth_elapsed = (time.perf_counter() - synth_start) * 1000
            final_text = f"[!] Lỗi khi chạy AI Synthesizer ({e}).\nHiển thị câu trả lời từ {successful_results[0].provider.upper()}:\n\n{successful_results[0].response.content}"

        total_elapsed = (time.perf_counter() - total_start) * 1000
        return SynthesizerResult(
            prompt=prompt,
            individual_results=individual_results,
            synthesizer_provider=synth_p_name,
            synthesizer_model=synth_m_name,
            final_answer=final_text,
            synthesis_latency_ms=synth_elapsed,
            total_latency_ms=total_elapsed,
            successful_providers=successful_names,
        )

    def run_pipeline(
        self,
        prompt: str,
        steps: List[PipelineStep],
        status_callback: Optional[Callable[[str, str, str], None]] = None
    ) -> PipelineResult:
        """Chạy dây chuyền xử lý tuần tự (Sequential Pipeline Chain)."""
        start_all = time.perf_counter()
        previous_output = prompt
        step_outputs = []

        for step in steps:
            provider = self.providers.get(step.provider)
            if not provider or not provider.is_ready:
                continue

            if status_callback:
                status_callback(step.provider, f"{step.model} [Bước {step.step_id}: {step.step_name}]", "STARTING")

            step_prompt = step.prompt_template.format(
                input=prompt,
                previous_output=previous_output
            )

            s_start = time.perf_counter()
            resp: UnifiedResponse = provider.generate(
                model=step.model,
                messages=[{"role": "user", "content": step_prompt}],
            )
            s_elapsed = (time.perf_counter() - s_start) * 1000

            step_outputs.append({
                "step_id": step.step_id,
                "step_name": step.step_name,
                "provider": step.provider,
                "model": step.model,
                "output": resp.content,
                "latency_ms": s_elapsed,
            })
            previous_output = resp.content

            if status_callback:
                status_callback(step.provider, f"{step.model} [Bước {step.step_id}: {step.step_name}]", "SUCCESS")

        total_elapsed = (time.perf_counter() - start_all) * 1000
        return PipelineResult(
            original_input=prompt,
            step_outputs=step_outputs,
            final_output=previous_output,
            total_latency_ms=total_elapsed,
        )

