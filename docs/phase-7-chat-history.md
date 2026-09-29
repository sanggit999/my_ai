# Phase 7: Chat History & Session Management

## 1. Mục tiêu (Objective)
Xây dựng hệ thống hội thoại nhiều lượt (Multi-turn Chat) với khả năng:
1. Lưu giữ ngữ cảnh cuộc trò chuyện giữa người dùng (user) và trợ lý AI (assistant).
2. Chuẩn hóa format lịch sử để gửi vào bất kỳ provider nào (OpenAI, Gemini, Anthropic).
3. Quản lý cửa sổ ngữ cảnh (Context Window Truncation): Tự động cắt tỉa các tin nhắn quá cũ khi vượt ngưỡng token cho phép của model.
4. Lưu và khôi phục phiên hội thoại ra file JSON hoặc SQLite (Session Persistence).
5. Cung cấp các lệnh đặc biệt trong CLI: `/clear`, `/history`, `/save`, `/switch-model`, `/exit`.

---

## 2. Thiết kế Data Model Hội thoại

```python
# models/chat.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional
import uuid

Role = Literal["system", "user", "assistant"]

@dataclass
class ChatMessage:
    role: Role
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model: Optional[str] = None
    tokens: Optional[int] = None

@dataclass
class ChatSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    provider: str = "openai"
    model: str = "gpt-4o"
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
        self.messages.clear()

    def to_dict_list(self) -> List[dict]:
        """Format chung đơn giản [{role: ..., content: ...}]."""
        return [{"role": m.role, "content": m.content} for m in self.messages]
```

---

## 3. Quản lý Ngữ cảnh (Context Window Management)

Khi cuộc trò chuyện kéo dài, tổng số token có thể vượt qua `input_token_limit` của model. Cần cơ chế cắt tỉa thông minh (Sliding Window):

```python
# session/manager.py
from models.chat import ChatSession

class SessionManager:
    @staticmethod
    def prune_context(session: ChatSession, max_messages: int = 20) -> list[dict]:
        """
        Cắt tỉa tin nhắn cũ, giữ lại các tin nhắn mới nhất để không vượt quá context window.
        Giữ cấu trúc xen kẽ user/assistant hợp lệ.
        """
        messages = session.messages
        if len(messages) <= max_messages:
            return session.to_dict_list()

        # Giữ lại max_messages tin nhắn gần nhất
        pruned = messages[-max_messages:]
        # Đảm bảo tin nhắn đầu tiên của đoạn trích xuất luôn là từ 'user'
        while pruned and pruned[0].role != "user":
            pruned.pop(0)

        return [{"role": m.role, "content": m.content} for m in pruned]
```

---

## 4. Lưu và Nạp phiên làm việc (Session Persistence)

Lưu phiên trò chuyện vào thư mục `.sessions/` dưới định dạng JSON:

```python
# session/storage.py
import json
import os
from pathlib import Path
from models.chat import ChatSession, ChatMessage

SESSIONS_DIR = Path(".sessions")

class SessionStorage:
    @staticmethod
    def ensure_dir():
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def save(cls, session: ChatSession, file_name: Optional[str] = None) -> str:
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
                {"role": m.role, "content": m.content, "timestamp": m.timestamp, "model": m.model}
                for m in session.messages
            ]
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(path)

    @classmethod
    def load(cls, file_path: str) -> ChatSession:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        session = ChatSession(
            id=data.get("id"),
            provider=data.get("provider", "openai"),
            model=data.get("model", "gpt-4o"),
            system_prompt=data.get("system_prompt"),
            created_at=data.get("created_at")
        )
        session.messages = [
            ChatMessage(role=m["role"], content=m["content"], timestamp=m.get("timestamp"), model=m.get("model"))
            for m in data.get("messages", [])
        ]
        return session
```

---

## 5. Vòng lặp Chat REPL trong CLI (Interactive Chat Loop)

```python
# cli/chat_loop.py
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from models.chat import ChatSession
from session.manager import SessionManager
from session.storage import SessionStorage

console = Console()

def run_chat_loop(provider, model_info, system_prompt: str = None):
    session = ChatSession(provider=provider.name, model=model_info.id, system_prompt=system_prompt)
    console.print(f"[bold green]Bắt đầu phiên trò chuyện với {model_info.display_name} ({provider.name.upper()})[/bold green]")
    console.print("[dim]Các lệnh: /clear (xóa ngữ cảnh), /save (lưu session), /exit (thoát)[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold blue]Bạn[/bold blue]").strip()
            if not user_input:
                continue

            if user_input.lower() in ["/exit", "exit", "quit"]:
                console.print("[yellow]Đã kết thúc phiên trò chuyện.[/yellow]")
                break
            elif user_input.lower() == "/clear":
                session.clear()
                console.print("[yellow]Đã xóa toàn bộ lịch sử ngữ cảnh cuộc trò chuyện.[/yellow]")
                continue
            elif user_input.lower() == "/save":
                saved_path = SessionStorage.save(session)
                console.print(f"[green]Đã lưu session vào:[/green] {saved_path}")
                continue

            # Thêm câu hỏi vào lịch sử
            session.add_user_message(user_input)
            payload_messages = SessionManager.prune_context(session)

            console.print(f"\n[bold green]{model_info.display_name}[/bold green]:", end=" ")
            
            # Streaming câu trả lời
            collected_chunks = []
            for chunk in provider.generate_stream(
                model_id=model_info.id,
                messages=payload_messages,
                system_prompt=session.system_prompt
            ):
                console.print(chunk, end="", highlight=False)
                collected_chunks.append(chunk)

            console.print("\n")
            full_response = "".join(collected_chunks)
            session.add_assistant_message(full_response, model=model_info.id)

        except KeyboardInterrupt:
            console.print("\n[yellow]Hủy lệnh... Nhập /exit để thoát.[/yellow]")
        except Exception as e:
            console.print(f"\n[bold red]Lỗi xảy ra:[/bold red] {e}\n")
```

---

## 6. Tiêu chí hoàn thành (Definition of Done)
- [ ] Hội thoại nhiều lượt duy trì được ngữ cảnh chính xác ở cả 3 provider.
- [ ] Chức năng streaming phản hồi chạy mượt mà theo thời gian thực trong terminal.
- [ ] Các lệnh điều khiển `/clear`, `/save`, `/exit` hoạt động ổn định.
- [ ] Hỗ trợ lưu trữ và nạp lại lịch sử phiên từ file JSON.
