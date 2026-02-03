#!/usr/bin/env python3
"""
验收测试脚本：自动跑完「创建 plot → lot → 四类事件 → 上传并绑定文件 → 获取 ledger」闭环。
仅用 Python 标准库，无需 pip install。
用法：先启动后端（Docker 或 uvicorn），再在项目根目录执行：
  python scripts/run_acceptance.py
或指定 base URL：
  python scripts/run_acceptance.py http://localhost:8000
"""
import json
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin

BASE = "http://localhost:8000"


def _build_multipart(boundary: str, filename: str, content: bytes) -> bytes:
    import io
    buf = io.BytesIO()
    buf.write(f"--{boundary}\r\n".encode("utf-8"))
    buf.write(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
    buf.write(b"Content-Type: application/octet-stream\r\n\r\n")
    buf.write(content)
    buf.write(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    return buf.getvalue()


def req(method: str, path: str, body: dict = None, file_upload: tuple = None):
    """file_upload = (filename, bytes_content) for POST multipart."""
    url = urljoin(BASE, path)
    if body and not file_upload:
        data = json.dumps(body).encode("utf-8")
        req_obj = urllib.request.Request(url, data=data, method=method)
        req_obj.add_header("Content-Type", "application/json")
    elif file_upload:
        boundary = "----AcceptanceTestBoundary"
        filename, content = file_upload
        body_bytes = _build_multipart(boundary, filename, content)
        req_obj = urllib.request.Request(url, data=body_bytes, method=method)
        req_obj.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    else:
        req_obj = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req_obj, timeout=30) as r:
            return r.getcode(), json.loads(r.read().decode("utf-8")) if r.length else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err = json.loads(body)
        except Exception:
            err = {"detail": body}
        return e.code, err
    except Exception as e:
        return -1, {"error": str(e)}


def main():
    global BASE
    if len(sys.argv) > 1:
        BASE = sys.argv[1].rstrip("/")
    print(f"BASE = {BASE}\n")

    # 1. Health
    code, data = req("GET", "/health")
    if code != 200:
        print(f"FAIL: GET /health -> {code} {data}")
        sys.exit(1)
    print("OK  GET /health")

    # 2. Create plot
    code, data = req("POST", "/plots", {"plot_name": "北坡A区", "entity_name": "张三种植户", "admin_division": "云南省某某县"})
    if code != 200:
        print(f"FAIL: POST /plots -> {code} {data}")
        sys.exit(1)
    plot_id = data["plot_id"]
    print(f"OK  POST /plots  plot_id={plot_id}")

    # 3. Create lot
    code, data = req("POST", "/lots", {
        "lot_type": "washed",
        "received_at": "2025-02-02T08:00:00Z",
        "plot_ids": [{"plot_id": plot_id}],
    })
    if code != 200:
        print(f"FAIL: POST /lots -> {code} {data}")
        sys.exit(1)
    lot_id = data["lot_id"]
    print(f"OK  POST /lots  lot_id={lot_id}")

    # 4. Four events
    events_payload = [
        ("RECEIVE_CHERRY", {"event_type": "RECEIVE_CHERRY", "lot_id": lot_id, "event_time": "2025-02-02T09:00:00Z", "data": {"cherry_weight_kg": 1000, "float_rate_pct": 5, "defect_rate_pct": 2, "ripeness_grade": 1}}),
        ("DRYING_CHECK", {"event_type": "DRYING_CHECK", "lot_id": lot_id, "event_time": "2025-02-02T14:00:00Z", "data": {"moisture_pct": 12, "turns_per_day": 2, "covered_overnight": True, "mold_flag": False}}),
        ("WAREHOUSE_IN", {"event_type": "WAREHOUSE_IN", "lot_id": lot_id, "event_time": "2025-02-02T16:00:00Z", "data": {"in_weight_kg": 200, "packaging_type": "grain_pro", "bin_code": "B001"}}),
        ("WAREHOUSE_OUT", {"event_type": "WAREHOUSE_OUT", "lot_id": lot_id, "event_time": "2025-02-02T18:00:00Z", "data": {"out_weight_kg": 199, "buyer_name": "测试买家", "shipment_ref": "SHIP001", "sample_retained_kg": 1}}),
    ]
    event_id_first = None
    for name, payload in events_payload:
        code, data = req("POST", "/events", payload)
        if code != 200:
            print(f"FAIL: POST /events {name} -> {code} {data}")
            sys.exit(1)
        if event_id_first is None:
            event_id_first = data["event_id"]
        print(f"OK  POST /events {name}  event_id={data['event_id']}")

    # 5. Upload file (small dummy) and bind
    dummy_content = b"dummy evidence file for test"
    code, data = req("POST", "/files/upload", file_upload=("test.txt", dummy_content))
    if code != 200:
        print(f"FAIL: POST /files/upload -> {code} {data}")
        sys.exit(1)
    file_id = data["file_id"]
    print(f"OK  POST /files/upload  file_id={file_id}")

    code, data = req("POST", f"/files/bind?event_id={event_id_first}&file_id={file_id}")
    if code != 200:
        print(f"FAIL: POST /files/bind -> {code} {data}")
        sys.exit(1)
    print("OK  POST /files/bind")

    # 6. Ledger
    code, data = req("GET", f"/lots/{lot_id}/ledger")
    if code != 200:
        print(f"FAIL: GET /lots/.../ledger -> {code} {data}")
        sys.exit(1)
    print(f"OK  GET /lots/{lot_id}/ledger")
    print("\n--- Ledger 结果 ---")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    status = data.get("status")
    balance_kg = data.get("balance_kg")
    red_lights = data.get("red_lights", [])
    if status == "green" and balance_kg == 0 and len(red_lights) == 0:
        print("\n验收通过：status=green, balance_kg=0, 无红灯")
    else:
        print(f"\n结果：status={status}, balance_kg={balance_kg}, red_lights={len(red_lights)}")
    print("\n全部步骤完成。")


if __name__ == "__main__":
    main()
