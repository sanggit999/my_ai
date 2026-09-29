"""TUI Engine - Terminal User Interface & Rich Formatting (Phase 11).

Cung cấp các công cụ tạo giao diện Terminal chuyên nghiệp, chuẩn phong cách Hacker / Modern CLI:
- Hỗ trợ màu sắc ANSI 24-bit / 256 màu và tự động fallback.
- Khung hộp bo góc tròn (Rounded Box Borders), đường kẻ gradient.
- Render Markdown trực tiếp trên terminal (Code blocks, Headers, Bullet lists, Quotes).
- Bảng tiến trình đa chặng & Banner cứu hộ sinh động (Active-Survivor Failover Alert).
- Zero-dependency: Chạy thuần thư viện chuẩn Python!
"""

import sys
import os
import time

# Đảm bảo console UTF-8 trên Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class Colors:
    """Mã màu ANSI cho giao diện terminal."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Màu cơ bản
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Màu sáng (Bright)
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Màu nền
    BG_DARK = "\033[48;5;234m"
    BG_BLUE = "\033[44m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_MAGENTA = "\033[45m"


def box(title: str, content: str, width: int = 72, color: str = Colors.BRIGHT_CYAN, border_style: str = "round") -> str:
    """Vẽ một khung viền đẹp mắt bao quanh nội dung."""
    chars = {
        "round": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
        "double": {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"},
        "single": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
    }.get(border_style, {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"})

    lines = content.splitlines()
    inner_width = max(width - 2, 40)
    
    # Header
    title_str = f" {title} " if title else ""
    header_h_len = inner_width - len(title_str)
    left_h = chars["h"] * 2
    right_h = chars["h"] * max(header_h_len - 2, 0)
    top = f"{color}{chars['tl']}{left_h}{Colors.BOLD}{Colors.BRIGHT_WHITE}{title_str}{color}{right_h}{chars['tr']}{Colors.RESET}"

    # Body
    body_lines = []
    for line in lines:
        # Wrap nếu dòng dài hơn inner_width
        while len(line) > inner_width - 2:
            chunk = line[: inner_width - 2]
            line = line[inner_width - 2 :]
            body_lines.append(f"{color}{chars['v']}{Colors.RESET} {chunk:<{inner_width-2}} {color}{chars['v']}{Colors.RESET}")
        body_lines.append(f"{color}{chars['v']}{Colors.RESET} {line:<{inner_width-2}} {color}{chars['v']}{Colors.RESET}")

    # Bottom
    bottom = f"{color}{chars['bl']}{chars['h'] * inner_width}{chars['br']}{Colors.RESET}"

    return "\n".join([top] + body_lines + [bottom])


def render_markdown(text: str) -> str:
    """Render sơ lược Markdown trên terminal (Headers, Code blocks, Lists, Bold)."""
    rendered_lines = []
    in_code_block = False
    code_lang = ""

    for line in text.splitlines():
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line.strip()[3:].strip() or "code"
                rendered_lines.append(f"{Colors.BG_DARK}{Colors.BRIGHT_YELLOW}╭── [{code_lang.upper()}] {'─'*48}{Colors.RESET}")
            else:
                in_code_block = False
                rendered_lines.append(f"{Colors.BG_DARK}{Colors.BRIGHT_YELLOW}╰{'─'*58}{Colors.RESET}")
            continue

        if in_code_block:
            rendered_lines.append(f"{Colors.BG_DARK}{Colors.BRIGHT_WHITE}│ {line}{Colors.RESET}")
            continue

        # Headers
        if line.startswith("# "):
            rendered_lines.append(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}▌ {line[2:].upper()}{Colors.RESET}")
        elif line.startswith("## "):
            rendered_lines.append(f"\n{Colors.BOLD}{Colors.BRIGHT_BLUE}▶ {line[3:]}{Colors.RESET}")
        elif line.startswith("### "):
            rendered_lines.append(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}◈ {line[4:]}{Colors.RESET}")
        # Bullet list
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            rendered_lines.append(f"  {Colors.BRIGHT_GREEN}•{Colors.RESET} {line.strip()[2:]}")
        # Quotes
        elif line.strip().startswith("> "):
            rendered_lines.append(f"  {Colors.DIM}{Colors.CYAN}▎ {line.strip()[2:]}{Colors.RESET}")
        else:
            rendered_lines.append(line)

    return "\n".join(rendered_lines)


def print_failover_alert(stage_name: str, dead_provider: str, dead_model: str, reason: str, survivor_provider: str, survivor_model: str):
    """In banner cảnh báo rực rỡ khi 1 model chết và model sống nhảy vào gánh."""
    msg = (
        f"{Colors.BRIGHT_RED}❌ SỰ CỐ CHẶNG: {stage_name}\n"
        f"  • Model gặp sự cố : {dead_provider.upper()} ({dead_model})\n"
        f"  • Nguyên nhân      : {reason}\n\n"
        f"{Colors.BRIGHT_GREEN}🚨 KÍCH HOẠT QUY TẮC: CON CÒN SỐNG NHẢY VÀO GÁNH!\n"
        f"  • AI Tiếp Quản    : {survivor_provider.upper()} ({survivor_model})\n"
        f"  • Trạng thái      : Tiếp tục dây chuyền, không để đứt đoạn!"
    )
    print("\n" + box("🚨 ACTIVE-SURVIVOR FAILOVER ACTIVATED 🚨", msg, color=Colors.BRIGHT_RED, border_style="double") + "\n")


def print_stage_progress(stage_num: int, stage_name: str, provider: str, model: str, status: str = "running"):
    """In thẻ trạng thái tiến trình của từng chặng trong dây chuyền."""
    if status == "running":
        icon = f"{Colors.BRIGHT_YELLOW}⏳ ĐANG CHẠY...{Colors.RESET}"
        badge = f"{Colors.BG_DARK}{Colors.BRIGHT_YELLOW} [{provider.upper()}: {model}] {Colors.RESET}"
    elif status == "success":
        icon = f"{Colors.BRIGHT_GREEN}✅ HOÀN TẤT{Colors.RESET}"
        badge = f"{Colors.BG_DARK}{Colors.BRIGHT_GREEN} [{provider.upper()}: {model}] {Colors.RESET}"
    elif status == "failed":
        icon = f"{Colors.BRIGHT_RED}❌ GẶP SỰ CỐ{Colors.RESET}"
        badge = f"{Colors.BG_DARK}{Colors.BRIGHT_RED} [{provider.upper()}: {model}] {Colors.RESET}"
    elif status == "rescued":
        icon = f"{Colors.BRIGHT_MAGENTA}🚨 ĐÃ ĐƯỢC CỨU HỘ{Colors.RESET}"
        badge = f"{Colors.BG_DARK}{Colors.BRIGHT_MAGENTA} [{provider.upper()}: {model}] {Colors.RESET}"
    else:
        icon = status
        badge = f"[{provider.upper()}: {model}]"

    print(f"  {Colors.BOLD}Chặng {stage_num}: {stage_name:<28}{Colors.RESET} {badge} ➔ {icon}")
