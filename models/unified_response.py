"""UnifiedResponse Data Model - Chuẩn hóa đầu ra phản hồi cho Phase 6."""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class TokenUsage:
    """Thống kê lượng Token tiêu thụ trong lượt sinh văn bản."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def summary(self) -> str:
        return f"Input: {self.prompt_tokens:,} | Output: {self.completion_tokens:,} | Total: {self.total_tokens:,}"


@dataclass
class UnifiedResponse:
    """Đối tượng phản hồi chuẩn hóa thống nhất cho tất cả Provider."""

    content: str                                                # Nội dung văn bản hoàn chỉnh
    provider: str                                               # 'openai' | 'groq' | 'gemini' | 'anthropic'
    model: str                                                  # Model ID đã xử lý
    usage: TokenUsage = field(default_factory=TokenUsage)       # Lượng token
    finish_reason: Optional[str] = None                         # 'stop', 'length', ...
    latency_ms: float = 0.0                                     # Độ trễ thực thi (miliseconds)
    raw_response: Optional[Any] = field(default=None, repr=False) # Phản hồi thô gốc
