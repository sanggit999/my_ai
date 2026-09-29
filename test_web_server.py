import sys
import json
import urllib.request
import threading
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from web.server import StudioHTTPHandler
from http.server import ThreadingHTTPServer

def run_test():
    print("\n--- KIỂM THỬ KHỞI ĐỘNG WEB STUDIO HTTP SERVER ---")
    server_address = ("127.0.0.1", 8765)
    httpd = ThreadingHTTPServer(server_address, StudioHTTPHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    base_url = "http://127.0.0.1:8765"
    
    # 1. Test GET /
    print("1. Kiểm tra GET / (Phục vụ index.html)...")
    req = urllib.request.urlopen(f"{base_url}/")
    assert req.status == 200
    html = req.read().decode("utf-8")
    assert "Multi-AI Studio" in html
    print("   ✅ Phục vụ index.html thành công!")

    # 2. Test GET /api/status
    print("2. Kiểm tra GET /api/status...")
    req = urllib.request.urlopen(f"{base_url}/api/status")
    assert req.status == 200
    data = json.loads(req.read().decode("utf-8"))
    assert data.get("status") == "ok"
    assert "groq" in data.get("providers", {})
    print("   ✅ API /api/status phản hồi chính xác!")

    # 3. Test GET /api/stages
    print("3. Kiểm tra GET /api/stages...")
    req = urllib.request.urlopen(f"{base_url}/api/stages")
    assert req.status == 200
    stages_data = json.loads(req.read().decode("utf-8"))
    assert stages_data.get("status") == "ok"
    assert "head" in stages_data.get("stages", {})
    print("   ✅ API /api/stages phản hồi chính xác!")

    httpd.shutdown()
    httpd.server_close()
    print("🎉 WEB STUDIO SERVER KIỂM THỬ HOÀN HẢO!\n")

if __name__ == "__main__":
    run_test()
