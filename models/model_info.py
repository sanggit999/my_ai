"""ModelInfo Data Model - Chuẩn hóa metadata của các model trên tất cả Provider."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ModelInfo:
    """Chuẩn hóa dữ liệu Model từ các nhà cung cấp khác nhau (OpenAI, Groq, Gemini, Anthropic)."""

    provider: str                                           # 'openai' | 'groq' | 'gemini' | 'anthropic'
    id: str                                                 # Model ID gửi API (vd: 'gpt-4o', 'gemini-3.8-flash', 'llama-3.3-70b-versatile')
    display_name: str                                       # Tên thân thiện hiển thị trên UI/CLI
    description: Optional[str] = None                       # Mô tả chức năng / thế mạnh của model
    input_token_limit: Optional[int] = None                 # Context window đầu vào tối đa
    output_token_limit: Optional[int] = None                # Giới hạn output tokens tối đa
    capabilities: List[str] = field(default_factory=list)   # ['chat', 'vision', 'reasoning', 'tools']
    rate_limits: Optional[Dict[str, str]] = None            # {'rpm': '30', 'rpd': '14.4K', 'tpm': '15K', 'tpd': '500K'}
    raw_metadata: Dict[str, Any] = field(default_factory=dict) # Lưu data gốc từ SDK để tra cứu debug

    @property
    def full_label(self) -> str:
        """Nhãn hiển thị trực quan trên giao diện CLI."""
        context_str = f" [Context: {self.input_token_limit:,}]" if self.input_token_limit else ""
        rate_str = f" [RPM: {self.rate_limits['rpm']}]" if self.rate_limits and "rpm" in self.rate_limits and self.rate_limits["rpm"] != "-" else ""
        return f"[{self.provider.upper()}] {self.display_name} ({self.id}){context_str}{rate_str}"

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi thành dictionary."""
        return {
            "provider": self.provider,
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "input_token_limit": self.input_token_limit,
            "output_token_limit": self.output_token_limit,
            "capabilities": self.capabilities,
            "rate_limits": self.rate_limits,
        }
