"""Web Server - Zero-Dependency Local Studio Dashboard (Option C / Phase 11).

Chạy thuần thư viện chuẩn Python (http.server, urllib, json, threading)
- Phục vụ Static SPA (HTML5, CSS3, JS) tại http://localhost:8000
- Cung cấp API RESTful & SSE Streaming cho Dây chuyền 3 chặng Tự Phục Hồi.
- Tự động mở trình duyệt khi khởi chạy.
"""

import sys
import os
import json
import time
import threading
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.env_loader import load_env_files
from providers import get_available_provider_configs, get_provider
from config.active_models import get_all_active_models, set_active_model, get_active_model
from config.pipeline_stages import get_pipeline_stages, set_stage_config, reset_pipeline_stages
from orchestrator.pipeline_engine import ThreeStagePipeline, ThreeStageResult

STATIC_DIR = Path(__file__).resolve().parent / "static"


class StudioHTTPHandler(SimpleHTTPRequestHandler):
    """Bộ xử lý HTTP tùy biến cho Studio Dashboard."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format, *args):
        # Giảm ồn console, chỉ log khi cần
        pass

    def _send_json(self, data: dict, status_code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            available = get_available_provider_configs()
            active_models = get_all_active_models()
            status_data = {}
            for p in ("groq", "gemini", "openai", "anthropic"):
                is_configured = p in available and available[p].is_configured
                status_data[p] = {
                    "is_ready": is_configured,
                    "active_model": active_models.get(p, "default"),
                    "masked_key": available[p].masked_key if is_configured else "Chưa có key",
                }
            self._send_json({"status": "ok", "providers": status_data})

        elif path == "/api/stages":
            stages = get_pipeline_stages()
            self._send_json({"status": "ok", "stages": stages})

        elif path == "/api/models":
            # Trả về danh sách model khả dụng cho từng provider
            result = {}
            for p in ("groq", "gemini", "openai", "anthropic"):
                try:
                    prov = get_provider(p)
                    if prov.is_ready:
                        models = prov.list_models()
                        result[p] = [m.get("id") for m in models if isinstance(m, dict) and "id" in m]
                    else:
                        result[p] = []
                except Exception:
                    result[p] = [get_active_model(p)]
            self._send_json({"status": "ok", "models": result})

        else:
            # Phục vụ static files (index.html, app.css, app.js)
            if path == "/" or path == "":
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        body = {}
        if body_bytes:
            try:
                body = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                pass

        if path == "/api/stages":
            # Cập nhật cấu hình chặng: { stage_key: "head", provider: "groq", model: "..." }
            stage_key = body.get("stage_key")
            provider = body.get("provider")
            model = body.get("model")
            if stage_key and provider and model:
                set_stage_config(stage_key, provider, model)
                self._send_json({"status": "ok", "stages": get_pipeline_stages()})
            else:
                self._send_json({"status": "error", "message": "Thiếu thông tin cấu hình chặng"}, 400)

        elif path == "/api/stages/reset":
            stages = reset_pipeline_stages()
            self._send_json({"status": "ok", "stages": stages})

        elif path == "/api/active-model":
            # Cập nhật active model cho 1 provider
            provider = body.get("provider")
            model = body.get("model")
            if provider and model:
                set_active_model(provider, model)
                self._send_json({"status": "ok", "active_models": get_all_active_models()})
            else:
                self._send_json({"status": "error", "message": "Thiếu provider hoặc model"}, 400)

        elif path == "/api/pipeline/run":
            # Chạy dây chuyền 3 chặng kèm cơ chế con chết con sống nhảy vào
            prompt = body.get("prompt", "").strip()
            if not prompt:
                self._send_json({"status": "error", "message": "Prompt rỗng"}, 400)
                return

            events_log = []
            def on_status(stage_key, stage_name, prov, status_msg):
                events_log.append({
                    "stage_key": stage_key,
                    "stage_name": stage_name,
                    "provider": prov,
                    "status": status_msg,
                    "timestamp": time.time(),
                })

            try:
                pipeline = ThreeStagePipeline()
                result: ThreeStageResult = pipeline.run(prompt, status_callback=on_status)

                stages_data = []
                for s in result.stages:
                    stages_data.append({
                        "stage_key": s.stage_key,
                        "stage_name": s.stage_name,
                        "assigned_provider": s.assigned_provider,
                        "assigned_model": s.assigned_model,
                        "executed_provider": s.executed_provider,
                        "executed_model": s.executed_model,
                        "is_failover": s.is_failover,
                        "failover_reason": s.failover_reason,
                        "output_content": s.output_content,
                        "latency_ms": s.latency_ms,
                    })

                self._send_json({
                    "status": "ok",
                    "input_prompt": result.input_prompt,
                    "final_content": result.final_content,
                    "total_latency_ms": result.total_latency_ms,
                    "failovers_occurred": result.failovers_occurred,
                    "stages": stages_data,
                    "events": events_log,
                })
            except Exception as e:
                self._send_json({
                    "status": "error",
                    "message": str(e),
                    "events": events_log
                }, 500)
        else:
            self._send_json({"status": "error", "message": "Endpoint không tồn tại"}, 404)


def start_studio_server(port: int = 8000, auto_open: bool = True):
    """Khởi chạy máy chủ Studio Dashboard."""
    load_env_files()
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    server_address = ("127.0.0.1", port)
    try:
        httpd = ThreadingHTTPServer(server_address, StudioHTTPHandler)
    except OSError:
        # Nếu port 8000 bị chiếm, thử 8001
        port = 8001
        server_address = ("127.0.0.1", port)
        httpd = ThreadingHTTPServer(server_address, StudioHTTPHandler)

    url = f"http://127.0.0.1:{port}"
    print("\n" + "=" * 70)
    print(f"   🌟 MULTI-AI WEB STUDIO DASHBOARD IS LIVE!")
    print(f"   👉 Truy cập tại: {url}")
    print(f"   🛑 Nhấn Ctrl+C trong terminal để dừng server.")
    print("=" * 70 + "\n")

    if auto_open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        print("\n[✓] Đang tắt Studio Web Server...")
        httpd.server_close()


if __name__ == "__main__":
    start_studio_server()
