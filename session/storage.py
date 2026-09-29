"""Session Storage - Quản lý lưu trữ và tải lại phiên làm việc (Phase 7)."""

import json
from pathlib import Path
from typing import Optional, List
from models.chat import ChatSession, ChatMessage

SESSIONS_DIR = Path(__file__).resolve().parent.parent / ".sessions"


class SessionStorage:
    """Quản lý lưu và đọc phiên trò chuyện ra/vào file JSON."""

    @classmethod
    def ensure_dir(cls) -> Path:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        return SESSIONS_DIR

    @classmethod
    def save(cls, session: ChatSession, file_name: Optional[str] = None) -> Path:
        """Lưu phiên trò chuyện ra file JSON."""
        cls.ensure_dir()
        name = file_name or f"session_{session.id}.json"
        path = SESSIONS_DIR / name

        data = {
            "id": session.id,
            "provider": session.provider,
            "model": session.model,
            "system_prompt": session.system_prompt,
            "created_at": session.created_at,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "model": m.model,
                }
                for m in session.messages
            ]
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return path

    @classmethod
    def load(cls, file_path: Path) -> ChatSession:
        """Đọc phiên trò chuyện từ file JSON."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = ChatSession(
            id=data.get("id"),
            provider=data.get("provider", "gemini"),
            model=data.get("model", "gemini-3.8-flash"),
            system_prompt=data.get("system_prompt"),
            created_at=data.get("created_at"),
        )
        session.messages = [
            ChatMessage(
                role=m["role"],
                content=m["content"],
                timestamp=m.get("timestamp"),
                model=m.get("model"),
            )
            for m in data.get("messages", [])
        ]
        return session

    @classmethod
    def list_saved_sessions(cls) -> List[Path]:
        """Liệt kê danh sách các phiên trò chuyện đã lưu."""
        if not SESSIONS_DIR.exists():
            return []
        return sorted(list(SESSIONS_DIR.glob("*.json")), reverse=True)
