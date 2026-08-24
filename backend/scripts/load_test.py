"""
NFR-PERF-01 — load test จริงสำหรับ FR-006 (เช็คประกันสาธารณะ)
สเปก: ตอบกลับภายใน 2 วินาทีที่ P95 เมื่อมีผู้ใช้เข้าพร้อมกัน 200 คน (CR-005)

รัน: cd backend && python scripts/load_test.py
ต้องตั้ง DATABASE_URL/JWT_SECRET ชี้ไปที่ DB ที่มี seed data จริงแล้ว (เช่น sme_inventory
จาก `python scripts/seed.py`) เพราะทดสอบ path จริงที่ต้อง query serial ที่มีอยู่จริง

หมายเหตุ: ปิด rate limiter (STRIDE-D) ชั่วคราวเฉพาะรอบทดสอบนี้ในกระบวนการนี้เท่านั้น —
ไม่แตะโค้ด production เพราะ 200 request จากเครื่องเดียวกันจะมาจาก IP เดียว (loopback)
ทำให้โดน 429 ตั้งแต่ request ที่ 31 ถ้าไม่ปิด ซึ่งจะวัด throughput จริงไม่ได้ (STRIDE-D
มี test แยกต่างหากอยู่แล้วที่ tests/integration/test_stride_mitigations.py)
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import io  # noqa: E402

if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import httpx  # noqa: E402
import uvicorn  # noqa: E402

from app.limiter import limiter  # noqa: E402
from app.main import app  # noqa: E402

CONCURRENT_USERS = 200
PORT = 8099
TARGET_PATH = "/api/public/warranty/SN-RAM-00001"  # ต้องมีจริงใน DB (seed.py สร้างไว้ให้)
P95_TARGET_SECONDS = 2.0


async def fire_one(client: httpx.AsyncClient) -> tuple[float, int]:
    start = time.perf_counter()
    resp = await client.get(TARGET_PATH)
    elapsed = time.perf_counter() - start
    return elapsed, resp.status_code


async def main() -> int:
    limiter.enabled = False  # ดูเหตุผลใน docstring ด้านบน

    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)

    try:
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{PORT}", timeout=30.0) as client:
            results = await asyncio.gather(*(fire_one(client) for _ in range(CONCURRENT_USERS)))
    finally:
        server.should_exit = True
        await server_task
        limiter.enabled = True

    latencies = sorted(r[0] for r in results)
    statuses = [r[1] for r in results]
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95) - 1]
    p99 = latencies[int(len(latencies) * 0.99) - 1]

    print(f"Concurrent requests : {CONCURRENT_USERS}")
    print(f"Status codes        : {sorted(set(statuses))} (ต้องมีแต่ 200 ไม่มี error)")
    print(f"P50 latency         : {p50 * 1000:.0f} ms")
    print(f"P95 latency         : {p95 * 1000:.0f} ms  (target: <= {P95_TARGET_SECONDS * 1000:.0f} ms)")
    print(f"P99 latency         : {p99 * 1000:.0f} ms")
    print(f"Max latency         : {latencies[-1] * 1000:.0f} ms")

    ok = p95 <= P95_TARGET_SECONDS and all(s == 200 for s in statuses)
    print("\nPASS — NFR-PERF-01 ผ่านเป้าหมาย" if ok else "\nFAIL — NFR-PERF-01 ไม่ผ่านเป้าหมาย")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
