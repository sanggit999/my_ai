"""Chat Data Model - Quản lý lịch sử hội thoại và phiên làm việc (Phase 7)."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional, Dict, Any

Role = Literal["system", "user", "assistant"]


@dataclass
class ChatMessage:
    """Đại diện cho một tin nhắn trong cuộc trò chuyện."""
    role: Role
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model: Optional[str] = None


@dataclass
class ChatSession:
    """Quản lý một phiên trò chuyện hội thoại nhiều lượt."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    provider: str = "gemini"
    model: str = "gemini-3.8-flash"
    system_prompt: Optional[str] = None
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_user_message(self, text: str) -> ChatMessage:
        msg = ChatMessage(role="user", content=text)
        self.messages.append(msg)
        return msg

    def add_assistant_message(self, text: str, model: Optional[str] = None) -> ChatMessage:
        msg = ChatMessage(role="assistant", content=text, model=model)
        self.messages.append(msg)
        return msg

    def clear(self):
        """Xóa toàn bộ lịch sử trò chuyện."""
        self.messages.clear()

    def to_dict_list(self) -> List[Dict[str, str]]:
        """Trả về danh sách message dạng chuẩn [{'role': ..., 'content': ...}]."""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def prune_context(self, max_messages: int = 20) -> List[Dict[str, str]]:
        """Cắt tỉa ngữ cảnh cũ (Sliding Window), đảm bảo bắt đầu bằng tin nhắn của user."""
        if len(self.messages) <= max_messages:
            return self.to_dict_list()

        recent = self.messages[-max_messages:]
        # Bỏ qua các tin nhắn đầu nếu role không phải user
        while recent and recent[0].role != "user":
            recent.pop(0)

        return [{"role": m.role, "content": m.content} for m in recent]
