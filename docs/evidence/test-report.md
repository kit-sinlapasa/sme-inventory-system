# Test Report

> สร้างจากการรัน `python -m pytest` จริง ไม่ใช่พิมพ์เอง — รันซ้ำได้ด้วยคำสั่งเดียวกัน
> ทุกเคสรันบน **PostgreSQL จริง** ไม่ใช่ mock หรือ SQLite

## สรุปตามระดับการทดสอบ

| ระดับ | จำนวน | ทดสอบอะไร | trace กลับไปหา |
|---|---|---|---|
| **Unit** | 14 | ตรรกะบริสุทธิ์แยกเดี่ยว — ขอบเขตสาขา, ช่วงเวลารายงาน, แปลง scheme ของ DB URL, CORS | NFR-SEC-02, ADR-003 |
| **Integration** | 95 | ยิงผ่าน API จริงบน Postgres จริง ครอบทุก endpoint | FR-001~015 |
| **Acceptance** | 9 | เขียนตาม Given-When-Then ของ User Story โดยตรง | US-01, US-04~07 |
| **System / Concurrency** | 4 | 10 thread แข่งกันขายชิ้นเดียวกันบน DB จริง | NFR-REL-01, ADR-002 |
| **รวม** | **122** | | |

## ผลรันจริง

```
    result = context.run(func, *args)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
122 passed, 1 warning in 51.82s
```
