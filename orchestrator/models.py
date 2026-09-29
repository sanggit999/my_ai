"""Data Models cho AI Orchestration & Synthesis (Phase 8)."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from models.unified_response import UnifiedResponse


@dataclass
class ProviderExecutionResult:
    """Kết quả thực thi từ một Provider đơn lẻ trong quá trình điều phối."""
    provider: str
    model: str
    success: bool
    response: Optional[UnifiedResponse] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0

    @property
    def content(self) -> str:
        if self.success and self.response:
            return self.response.content
        return ""


@dataclass
class SynthesizerResult:
    """Kết quả tổng hợp cuối cùng từ AI Synthesizer."""
    prompt: str                                               # Câu hỏi ban đầu của người dùng
    individual_results: List[ProviderExecutionResult]         # Danh sách kết quả chi tiết từng AI
    synthesizer_provider: str                                 # Provider thực hiện tổng hợp
    synthesizer_model: str                                    # Model thực hiện tổng hợp
    final_answer: str                                         # Câu trả lời tổng hợp cuối cùng
    synthesis_latency_ms: float = 0.0                         # Thời gian chạy bước tổng hợp
    total_latency_ms: float = 0.0                             # Tổng thời gian (bước 1 + bước 2)
    successful_providers: List[str] = field(default_factory=list) # Các AI đã phản hồi thành công


@dataclass
class RoleAssignment:
    """Gán vai trò chuyên môn cụ thể cho một mô hình AI (Phase 9)."""
    provider: str                      # 'groq', 'gemini', 'openai', 'anthropic'
    model: str                         # Model ID cụ thể
    role_name: str                     # Tên vai diễn (vd: 'Senior Tech Lead')
    system_prompt: str                 # Chỉ dẫn hành vi chuyên biệt cho vai diễn
    description: Optional[str] = None  # Mô tả tóm tắt vai diễn


@dataclass
class PipelineStep:
    """Một mắt xích trong dây chuyền xử lý tuần tự (Sequential Pipeline Chain)."""
    step_id: int
    step_name: str                     # vd: 'Planner', 'Coder', 'Reviewer'
    provider: str                      # Provider phụ trách bước này
    model: str                         # Model phụ trách bước này
    prompt_template: str               # Mẫu prompt định hướng (sử dụng {previous_output}, {input})


@dataclass
class PipelineResult:
    """Kết quả thực thi dây chuyền tuần tự nhiều AI."""
    original_input: str
    step_outputs: List[Dict[str, Any]] = field(default_factory=list)
    final_output: str = ""
    total_latency_ms: float = 0.0

