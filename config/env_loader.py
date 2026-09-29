"""Module nạp biến môi trường từ file .env.

Tự động tìm kiếm file .env tại thư mục gốc của dự án hoặc thư mục con.
Tương thích cả khi chưa cài thư viện `python-dotenv`.
"""

import os
from pathlib import Path
from typing import Optional, Union


def _parse_env_file_fallback(file_path: Path, override: bool = False) -> None:
    """Fallback tự đọc file .env bằng thư viện chuẩn Python (không cần phụ thuộc bên ngoài)."""
    if not file_path.is_file():
        return

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Bỏ qua dòng trống và comment
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()

                # Bỏ dấu nháy bọc quanh giá trị nếu có
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]

                if override or key not in os.environ:
                    os.environ[key] = val


def load_env_files(base_dir: Optional[Union[str, Path]] = None, override: bool = False) -> Path:
    """Nạp file .env từ thư mục chỉ định hoặc thư mục gốc dự án."""
    if base_dir is None:
        # Mặc định lấy thư mục cha của config/ (tức root dự án)
        base_dir = Path(__file__).resolve().parent.parent
    else:
        base_dir = Path(base_dir).resolve()

    env_path = base_dir / ".env"

    try:
        from dotenv import load_dotenv  # type: ignore
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=override)
    except ImportError:
        # Nếu chưa cài python-dotenv, dùng fallback chuẩn
        _parse_env_file_fallback(env_path, override=override)

    return env_path


def save_env_var(key: str, value: str, base_dir: Optional[Union[str, Path]] = None) -> Path:
    """Lưu hoặc cập nhật một cặp KEY=VALUE vào file .env và nạp vào os.environ."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    else:
        base_dir = Path(base_dir).resolve()

    env_path = base_dir / ".env"
    key = key.strip()
    value = value.strip()

    lines = []
    found = False

    if env_path.is_file():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    curr_k, _ = stripped.split("=", 1)
                    if curr_k.strip() == key:
                        lines.append(f"{key}={value}\n")
                        found = True
                        continue
                lines.append(line if line.endswith("\n") else f"{line}\n")

    if not found:
        lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # Cập nhật ngay vào môi trường hiện tại
    os.environ[key] = value
    return env_path
