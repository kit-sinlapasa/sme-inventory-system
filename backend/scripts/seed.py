"""
Seed ข้อมูลเริ่มต้นสำหรับ local dev / demo — ไม่ใช้กับ production
รัน: cd backend && python -m scripts.seed

CR-009 — ขยาย seed data ให้ครบ 6 หมวดหมู่ x 10 รายการ = 60 สินค้า พร้อม Item/S/N รับเข้าจริง
บางส่วนขายแล้ว (Sale) บางส่วนมีคำขอสั่งซื้อ (PurchaseRequest) ครบทุกสถานะ เพื่อให้ demo
เห็นข้อมูลสมจริงในทุกหน้า ไม่ใช่แค่ผู้ใช้ 2 คนเปล่า ๆ เหมือนเดิม
"""
import io
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Windows console เริ่มต้นด้วย cp1252 ซึ่ง print ข้อความไทยไม่ได้ (พังจริงตอน dev บน Windows)
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from passlib.context import CryptContext  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.branch import Branch  # noqa: E402
from app.models.branch_sku import BranchSKU  # noqa: E402
from app.models.item import Item  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.models.product_image import ProductImage  # noqa: E402
from app.models.purchase_order import PurchaseOrder  # noqa: E402
from app.models.purchase_request import PurchaseRequest  # noqa: E402
from app.models.sale import Sale  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.stock_alerts import evaluate_low_stock_alert  # noqa: E402

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ยี่ห้อ/รุ่นจริงในตลาด ให้ demo ดูสมจริง (ไม่ใช่ "Product 1", "Product 2")
CATALOG = {
    "RAM": [
        ("Corsair", "Vengeance LPX 8GB DDR4-3200"),
        ("Kingston", "Fury Beast 16GB DDR4-3600"),
        ("G.Skill", "Trident Z 32GB DDR4-3600"),
        ("Corsair", "Dominator Platinum 16GB DDR5-5600"),
        ("Kingston", "ValueRAM 8GB DDR4-2666"),
        ("TeamGroup", "T-Force Delta 16GB DDR4-3200"),
        ("Crucial", "Ballistix 8GB DDR4-3000"),
        ("ADATA", "XPG Gammix 16GB DDR4-3200"),
        ("Patriot", "Viper Steel 32GB DDR4-3600"),
        ("Corsair", "Vengeance RGB 16GB DDR5-6000"),
    ],
    "CPU": [
        ("Intel", "Core i5-13400"),
        ("Intel", "Core i7-13700K"),
        ("Intel", "Core i9-13900K"),
        ("AMD", "Ryzen 5 5600X"),
        ("AMD", "Ryzen 7 5800X"),
        ("AMD", "Ryzen 9 7900X"),
        ("Intel", "Core i3-13100"),
        ("AMD", "Ryzen 5 7600X"),
        ("Intel", "Core i5-12400F"),
        ("AMD", "Ryzen 7 7700X"),
    ],
    "Mainboard": [
        ("ASUS", "ROG Strix B650-A"),
        ("MSI", "MAG B760 Tomahawk"),
        ("Gigabyte", "B550 Aorus Elite"),
        ("ASRock", "B660M Pro RS"),
        ("ASUS", "TUF Gaming X670E"),
        ("MSI", "PRO B650M-A"),
        ("Gigabyte", "Z790 Aorus Elite"),
        ("ASRock", "X570 Phantom Gaming"),
        ("ASUS", "Prime B760M-A"),
        ("MSI", "MPG B550 Gaming Edge"),
    ],
    "GPU": [
        ("ASUS", "GeForce RTX 4060"),
        ("MSI", "GeForce RTX 4070"),
        ("Gigabyte", "GeForce RTX 4080"),
        ("Sapphire", "Radeon RX 7600"),
        ("PowerColor", "Radeon RX 7700 XT"),
        ("ASUS", "GeForce RTX 3060"),
        ("XFX", "Radeon RX 6700 XT"),
        ("MSI", "GeForce RTX 4090"),
        ("Sapphire", "Radeon RX 7900 XTX"),
        ("Gigabyte", "GeForce RTX 3050"),
    ],
    "Storage": [
        ("Samsung", "970 EVO 1TB NVMe"),
        ("WD", "Black SN850X 1TB NVMe"),
        ("Kingston", "NV2 500GB NVMe"),
        ("Crucial", "MX500 1TB SATA SSD"),
        ("Seagate", "Barracuda 2TB HDD"),
        ("Samsung", "980 Pro 2TB NVMe"),
        ("WD", "Blue 1TB SATA SSD"),
        ("ADATA", "XPG Gammix S70 1TB NVMe"),
        ("Kingston", "KC3000 1TB NVMe"),
        ("Toshiba", "P300 2TB HDD"),
    ],
    "PSU": [
        ("Corsair", "RM750x 750W 80+ Gold"),
        ("Seasonic", "Focus GX-650 650W 80+ Gold"),
        ("EVGA", "SuperNOVA 850W 80+ Gold"),
        ("Cooler Master", "MWE 550W 80+ Bronze"),
        ("Thermaltake", "Toughpower 700W 80+ Gold"),
        ("be quiet!", "Straight Power 750W 80+ Platinum"),
        ("ASUS", "ROG Strix 850W 80+ Gold"),
        ("Corsair", "CV550 550W 80+ Bronze"),
        ("FSP", "Hydro G Pro 750W 80+ Gold"),
        ("Antec", "HCG850 850W 80+ Gold"),
    ],
}

WARRANTY_MONTHS = {"RAM": 60, "CPU": 36, "Mainboard": 36, "GPU": 36, "Storage": 60, "PSU": 60}

# วนซ้ำ scenario ต่อ (product, branch) เพื่อให้เห็นทุกสถานะสต็อกในหน้า dashboard จริง
# (reorder_point, received, sold) — บาง combo ตั้งใจให้คงเหลือ <= reorder_point เพื่อ demo alert
STOCK_SCENARIOS = [
    (2, 1, 0),  # รับเข้าน้อยกว่า reorder point ตั้งแต่แรก — เห็นแดงทันทีที่ dashboard
    (2, 4, 3),  # ขายจนเหลือต่ำกว่า reorder point — เห็น flow การแจ้งเตือนตอนขายจริง
    (1, 3, 0),  # สต็อกปกติ ไม่ใกล้หมด
    (0, 2, 0),  # ไม่ได้ตั้ง reorder point (0 = ไม่ track) — สต็อกปกติ
    (3, 5, 2),  # คงเหลือเท่ากับ reorder point พอดี
]

# ── CR-013: ข้อมูลย้อนหลังให้ dashboard วิเคราะห์ได้จริง ───────────────────────────
# เดิม seed ใส่ทุกอย่างด้วยเวลา "ตอนนี้" หมด (ห่างกันไม่ถึง 10 วินาที) ทำให้:
#   - กราฟยอดขายรายวันเป็นแท่งเดียวโดด ๆ
#   - คำนวณ "ขายวันละกี่ชิ้น / ของจะหมดในกี่วัน" ไม่ได้เลย
#   - แยก "ของค้างสต็อก" ไม่ออกเพราะทุกชิ้นรับเข้าพร้อมกัน
# จึงกระจายเวลาย้อนหลัง 9 เดือน + ทำให้ยอดขายเป็นแบบ Pareto (บางรุ่นขายดี บางรุ่นค้าง)
# + ใส่ seasonality รายสัปดาห์ (ศุกร์-อาทิตย์ขายดีกว่า) เพื่อให้กราฟทั้ง 5 ตัวมีความหมาย
#
# ⚠️ นี่คือข้อมูลสาธิตที่ "ออกแบบ" ให้มีรูปแบบเหล่านี้โดยตั้งใจ ไม่ใช่ข้อมูลธุรกิจจริง
# ตัวเลขที่ dashboard วิเคราะห์ได้จึงสะท้อนสิ่งที่ใส่เข้าไป ไม่ใช่การค้นพบเชิงธุรกิจ
HISTORY_DAYS = 270  # ย้อนหลัง ~9 เดือน

# เวลาไทย (UTC+7, ไม่มี DST) — ต้องสร้างเวลาในโซนนี้ ไม่ใช่ UTC
# ถ้าสุ่มชั่วโมงทำการ 9-20 บนนาฬิกา UTC จะกลายเป็น 16:00-03:00 เวลาไทย ทำให้ยอดขาย
# ราว 1 ใน 3 ตกไปนับเป็น "วันถัดไป" ตอน frontend เรนเดอร์ด้วย th-TH → กราฟรายวัน/รายสัปดาห์
# จะยังมีความต่างให้เห็น แต่เป็นความต่างที่ผิดวัน ตรวจด้วยตาเปล่าไม่เจอ
BKK = timezone(timedelta(hours=7))

# น้ำหนักยอดขายตามวันในสัปดาห์ (จันทร์=0 ... อาทิตย์=6) — ร้านอะไหล่คอมขายดีช่วงสุดสัปดาห์
DOW_WEIGHT = {0: 0.70, 1: 0.65, 2: 0.80, 3: 0.85, 4: 1.20, 5: 1.60, 6: 1.40}
MAX_DOW_WEIGHT = max(DOW_WEIGHT.values())

# Pareto — ร้านจริงมีไม่กี่รุ่นที่ขายดีมาก และมีรุ่นที่แทบไม่ขยับเลย
# sales_factor = ตัวคูณจำนวนที่ขายได้ต่อ (รุ่น, สาขา) — 0 = ไม่เคยขายเลย กลายเป็นของค้างสต็อก
# age_range   = ช่วงอายุ (วัน) ของ "ของที่ยังเหลือ" — ของขายดีหมุนเร็วจึงเป็นของใหม่
#               ส่วนของค้างสต็อกต้องเก่าจริง ไม่งั้นกราฟอายุสต็อกจะกองอยู่ถังเดียว
POPULARITY_TIERS = [
    ("ขายดีมาก", 0.15, 4.0, (0, 45)),
    ("ขายดี", 0.20, 2.0, (5, 75)),
    ("ปานกลาง", 0.30, 1.0, (15, 130)),
    ("ขายช้า", 0.20, 0.4, (70, 200)),
    ("ค้างสต็อก", 0.15, 0.0, (185, HISTORY_DAYS)),
]


def build_popularity_map(products, rng):
    """แจกระดับความนิยมให้สินค้าแบบ deterministic — คืน {product_id: (factor, age_range)}"""
    shuffled = products[:]
    rng.shuffle(shuffled)
    result, start = {}, 0
    for i, (_label, share, factor, age_range) in enumerate(POPULARITY_TIERS):
        end = len(shuffled) if i == len(POPULARITY_TIERS) - 1 else start + round(len(shuffled) * share)
        for p in shuffled[start:end]:
            result[p.id] = (factor, age_range)
        start = end
    return result


def pick_sold_at(rng, received_at, now):
    """
    สุ่มเวลาขายหลังวันรับเข้า ถ่วงน้ำหนักตามวันในสัปดาห์ด้วย rejection sampling
    (โอกาสผ่านต่อรอบ ~0.64 จึงแทบไม่มีทางวนครบ 25 รอบแล้วไม่ได้ค่า)

    ผู้เรียกต้องส่ง received_at ที่เก่ากว่า now อย่างน้อย 2 วัน เพื่อให้ span >= 1 เสมอ —
    ถ้าปล่อยให้ฟังก์ชันคืน None แล้วผู้เรียกใช้ค่า fallback แบบ received_at + 1 วัน
    ค่านั้นจะไม่ผ่านการถ่วงน้ำหนักวัน ทำให้กราฟยอดขายรายวันในสัปดาห์เจือจางลง
    """
    span = (now - received_at).days
    assert span >= 1, "received_at ต้องเก่ากว่า now อย่างน้อย 1 วัน"
    for _ in range(50):
        # ยกกำลัง 0.7 = เอียงเข้าหาวันปัจจุบัน (ขายเพิ่งเกิดมากกว่าขายนานแล้ว)
        offset = int(span * (rng.random() ** 0.7))
        # ตั้งเวลาบนวันนั้น ๆ ตรง ๆ (ไม่ใช่บวกชั่วโมงทับเวลาเดิมของ received_at ซึ่งจะล้นไปวันถัดไป)
        day = (received_at + timedelta(days=offset)).date()
        cand = datetime.combine(day, datetime.min.time(), tzinfo=BKK) + timedelta(
            hours=rng.randint(9, 20), minutes=rng.randint(0, 59)
        )
        if cand > now or cand < received_at:
            continue
        if rng.random() < DOW_WEIGHT[cand.weekday()] / MAX_DOW_WEIGHT:
            return cand
    return received_at + timedelta(days=1)


# 4 สาขาที่มีขนาดต่างกันจริง — ไม่ให้ทุกสาขามีของเท่ากันเป๊ะเพราะไม่สมจริง
# sku_coverage = สัดส่วน SKU ที่สาขานั้นสต็อก (สาขาเล็กไม่ได้มีของครบทุกรุ่น)
# size = ตัวคูณจำนวนที่รับเข้า (สาขาใหญ่รับเข้าเยอะกว่าต่อรุ่น)
# ทุกสาขามีพนักงานของตัวเอง รวมถึงสำนักงานใหญ่ — เดิมสำนักงานใหญ่มีของแต่ไม่มีใครขายได้เลย
BRANCH_PROFILES = [
    {
        "name": "สำนักงานใหญ่",
        "address": "กรุงเทพฯ",
        "username": "hq1",
        "password": "hq1234",
        "sku_coverage": 1.00,  # คลังกลาง มีของครบทุกรุ่น
        "size": 1.4,
    },
    {
        "name": "สาขาสยาม",
        "address": "สยามสแควร์",
        "username": "branch1",
        "password": "branch1234",  # คงไว้ตามเดิม เอกสาร/ภาพหน้าจอที่ทำไปแล้วอ้างถึงรหัสนี้
        "sku_coverage": 0.90,
        "size": 1.0,
    },
    {
        "name": "สาขารัชดา",
        "address": "ถนนรัชดาภิเษก กรุงเทพฯ",
        "username": "branch2",
        "password": "rachada1234",  # ตั้งชื่อตามสาขา อ่านแล้วไม่สับสนแบบ "branch2" + "1234"
        "sku_coverage": 0.70,
        "size": 0.7,
    },
    {
        "name": "สาขารังสิต",
        "address": "รังสิต ปทุมธานี",
        "username": "branch3",
        "password": "rangsit1234",
        "sku_coverage": 0.50,  # สาขาใหม่ ยังสต็อกไม่ครบ
        "size": 0.5,
    },
]


def _describe_target() -> str:
    """
    บอกว่ากำลังจะลงฐานข้อมูลไหน โดย**ไม่แสดงรหัสผ่าน**

    จำเป็นเพราะที่ผ่านมาสคริปต์ไม่เคยบอกเป้าหมายเลย — รันผิดฐาน (เช่นตั้ง env var
    ไม่ติดแล้วตกไปใช้ค่า default ที่ชี้ localhost) กับรันถูกฐาน ผลลัพธ์บนหน้าจอ
    เหมือนกันทุกบรรทัด ทำให้เข้าใจว่า seed ขึ้น production แล้วทั้งที่ยังเป็นชุดเดิมอยู่
    """
    from urllib.parse import urlparse

    u = urlparse(settings.DATABASE_URL)
    where = "🖥️  เครื่องนี้ (local)" if u.hostname in ("localhost", "127.0.0.1") else "☁️  รีโมต"
    return f"{where}  host={u.hostname or '?'}  db={(u.path or '/?').lstrip('/')}  user={u.username or '?'}"


def _wipe(db):
    """
    ล้างทุกตาราง **พร้อมรีเซ็ตลำดับ id กลับไปเริ่มที่ 1**

    ต้องใช้ TRUNCATE ... RESTART IDENTITY ไม่ใช่ DELETE เพราะ DELETE ลบแถวอย่างเดียว
    แต่ไม่แตะ sequence ของ id — reseed รอบถัดไปสินค้าจะได้ id 61-120 แทนที่จะเป็น 1-60
    ผลที่ตามมาเคยเกิดจริงตอนทดสอบ:
      - JWT ที่ยังค้างในเบราว์เซอร์ชี้ไป user id เดิมที่ถูกลบแล้ว -> 401 ทุก request
      - sku_id ที่ค้างบนหน้าจอชี้ไปสินค้าที่ไม่มีแล้ว -> 404
      - ที่สำคัญกว่านั้น: ข้อมูลสาธิตจะไม่ reproducible เพราะ id เลื่อนทุกครั้งที่ reseed
        เอกสาร/ภาพหน้าจอที่อ้างถึงสินค้า id หนึ่ง ๆ จะไม่ตรงอีกต่อไป

    CASCADE จำเป็นเพราะ TRUNCATE หลายตารางที่มี FK ต่อกันต้องสั่งพร้อมกันทั้งชุด
    """
    from app.database import Base

    names = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    db.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    db.commit()


# จำนวนวันที่มีการขายขั้นต่ำที่ถือว่า "เป็นข้อมูลชุดใหม่แล้ว"
# ชุดเก่า seed ทุกอย่างในหน้าต่างเดียว จึงมีวันที่ขายแค่ 1 วัน ส่วนชุดใหม่กระจาย 270 วัน
# ได้ ~177 วัน — ตั้งเกณฑ์ไว้ 60 ซึ่งอยู่กลาง ๆ ห่างจากทั้งสองฝั่งมากพอไม่ให้ก้ำกึ่ง
FRESH_DATA_MIN_SALE_DAYS = 60


def _sale_day_spread(db) -> int:
    """จำนวนวัน (ตามปฏิทินไทย) ที่มีการขายเกิดขึ้น — ใช้แยกข้อมูลชุดเก่ากับชุดใหม่"""
    return (
        db.execute(
            text(
                "select count(distinct (sold_at at time zone 'Asia/Bangkok')::date) from sales"
            )
        ).scalar()
        or 0
    )


def seed(reset: bool = False, only_if_stale: bool = False):
    # พิมพ์เป้าหมายก่อนแตะข้อมูลใด ๆ เสมอ ทั้งตอนสำเร็จและตอนถูกปฏิเสธ
    print(f"เป้าหมาย: {_describe_target()}\n")
    db = SessionLocal()
    # seed คงที่ทำให้ "รูปแบบ" ของข้อมูลซ้ำเดิมได้ (สัดส่วน Pareto, การกระจายรายสัปดาห์)
    # แต่ **จำนวนรวมไม่เท่ากันเป๊ะทุกรอบ** เพราะจุดอ้างอิงเวลาคือ datetime.now() —
    # วันในสัปดาห์ขยับ ทำให้ rejection sampling ใน pick_sold_at รับ/ทิ้งค่าต่างกัน
    # สาย RNG จึงเลื่อนไปทั้งสาย (วัดจริง: รันห่างกันไม่กี่ชั่วโมงได้ 913 vs 831 การขาย)
    # ถ้าต้องการซ้ำเป๊ะจริงต้องตรึงเวลาอ้างอิงด้วย ซึ่งไม่จำเป็นสำหรับข้อมูลสาธิต
    rng = random.Random(42)
    try:
        if db.query(User).filter(User.username == "admin").first():
            if only_if_stale:
                # โหมดสำหรับรันตอน service บูตบน Render ซึ่งจะถูกเรียกซ้ำทุกครั้งที่เครื่องตื่น
                # (free tier หลับบ่อย) จึงต้อง "ไม่ทำอะไร" เมื่อข้อมูลเป็นชุดใหม่อยู่แล้ว
                # ไม่งั้นฐานข้อมูลจะถูกล้างทิ้งทุกครั้งที่มีคนเปิดเว็บหลังเครื่องหลับ
                spread = _sale_day_spread(db)
                if spread >= FRESH_DATA_MIN_SALE_DAYS:
                    print(f"ข้อมูลเป็นชุดใหม่อยู่แล้ว (มีการขาย {spread} วัน) — ไม่ทำอะไร")
                    return
                print(f"ข้อมูลเป็นชุดเก่า (มีการขายแค่ {spread} วัน) — จะเขียนทับด้วยชุดใหม่")
                _wipe(db)
            elif not reset:
                # เตือนให้ชัดว่า "ไม่ได้ทำอะไรเลย" — เดิมพิมพ์แค่ "ข้าม" แล้ว exit 0
                # ซึ่งอ่านเผิน ๆ เหมือน seed สำเร็จ ทำให้เข้าใจผิดว่าข้อมูลใหม่ขึ้นแล้ว
                # ทั้งที่ยังเป็นชุดเดิมอยู่ (เจอปัญหานี้ตอนเตรียม reseed production จริง)
                print("❌ ไม่ได้ทำอะไร — ฐานข้อมูลนี้มี seed data อยู่แล้ว")
                print("   ถ้าต้องการเขียนทับด้วยชุดใหม่ ให้รันด้วย: python -m scripts.seed --reset")
                print("   ⚠️ --reset จะลบข้อมูลในทุกตารางทิ้งก่อน ใช้กับฐานข้อมูล demo เท่านั้น")
                sys.exit(1)
            else:
                print("--reset: กำลังลบข้อมูลเดิมทั้งหมด...")
                _wipe(db)

        admin = User(
            username="admin",
            password_hash=pwd_context.hash("admin1234"),
            role="Admin",
            branch_id=None,  # Admin ดูแลทุกสาขา จึงไม่สังกัดสาขาใด และ "ขายเองไม่ได้"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        branches = []  # [(Branch, User, profile)]
        for profile in BRANCH_PROFILES:
            branch = Branch(name=profile["name"], address=profile["address"])
            db.add(branch)
            db.commit()
            db.refresh(branch)

            staff = User(
                username=profile["username"],
                password_hash=pwd_context.hash(profile["password"]),
                role="BranchStaff",
                branch_id=branch.id,
            )
            db.add(staff)
            db.commit()
            db.refresh(staff)
            branches.append((branch, staff, profile))

        # --- 60 สินค้า (6 หมวดหมู่ x 10) พร้อมรูปตัวอย่าง ---
        # สร้างสินค้าให้ครบก่อน แล้วค่อยลงสต็อก เพราะการแจกระดับความนิยม (Pareto) ต้องเห็น
        # สินค้าทั้งชุดถึงจะแบ่งสัดส่วนได้ถูก — แบ่งไปทีละตัวระหว่างวนลูปทำไม่ได้
        products = []
        for category, entries in CATALOG.items():
            for brand, model in entries:
                product = Product(
                    category=category,
                    brand=brand,
                    model=model,
                    spec=None,
                    warranty_months=WARRANTY_MONTHS[category],
                )
                db.add(product)
                products.append(product)
        db.commit()

        for product in products:
            db.add(
                ProductImage(
                    product_id=product.id,
                    image_url=f"https://placehold.co/400x300?text={product.category}",
                    sort_order=0,
                )
            )
        db.commit()

        popularity = build_popularity_map(products, rng)
        now = datetime.now(BKK)

        serial_counter = 0
        combo_index = 0  # นับ (product, branch) แยกจาก serial_counter — กันไม่ให้ modulo วนซ้ำ pattern เดิม
        for product in products:
            category = product.category
            # --- รับเข้าสต็อก + ตั้ง reorder point + ขายบางส่วน แยกตามขนาดสาขา ---
            for branch, staff, profile in branches:
                combo_index += 1

                # สาขาเล็กไม่ได้สต็อกครบทุกรุ่น — ข้ามบางรุ่นแบบ deterministic
                if rng.random() > profile["sku_coverage"]:
                    continue

                reorder_point, base_received, base_sold = STOCK_SCENARIOS[
                    combo_index % len(STOCK_SCENARIOS)
                ]
                factor, age_range = popularity[product.id]

                # scenario คุมว่า "เหลือเท่าไร" (จึงคุมการแจ้งเตือนใกล้หมดได้เหมือนเดิม)
                # ส่วนความนิยมคุมว่า "ขายไปแล้วกี่ชิ้นในอดีต" — สองอย่างนี้แยกกัน
                remaining = max(0, round((base_received - base_sold) * profile["size"]))
                sold = round(factor * profile["size"] * rng.uniform(2.0, 5.0))

                db.add(BranchSKU(branch_id=branch.id, sku_id=product.id, reorder_point=reorder_point))

                # commit เป็นชุดต่อ (สาขา, สินค้า) ไม่ใช่ต่อชิ้น — ตอน seed ขึ้น production
                # ที่ DB อยู่คนละทวีป การ commit ทีละชิ้นทำให้ใช้เวลาเป็นสิบ ๆ นาที
                # เพราะเสีย network round-trip ทุกครั้ง
                #
                # ของที่ยังเหลือ: อายุตามระดับความนิยม (ขายดี = ของใหม่, ค้างสต็อก = ของเก่าจริง)
                # ของที่ขายแล้ว: บังคับอายุ >= 2 วัน เพื่อให้ pick_sold_at มีช่วงให้เลือกเสมอ
                plan = [(rng.randint(*age_range), "InStock") for _ in range(remaining)]
                plan += [(rng.randint(2, HISTORY_DAYS), "Sold") for _ in range(sold)]

                sold_items = []  # [(Item, received_at)] — เก็บ received_at ไว้เองเพราะหลัง commit
                for age, status in plan:  # SQLAlchemy จะ expire attribute แล้วอ่านกลับมาเป็น UTC
                    serial_counter += 1
                    received_at = now - timedelta(days=age, hours=rng.randint(0, 23))
                    item = Item(
                        sku_id=product.id,
                        serial_number=f"SN-{category.upper()}-{serial_counter:05d}",
                        branch_id=branch.id,
                        status=status,
                        received_at=received_at,
                    )
                    db.add(item)
                    if status == "Sold":
                        sold_items.append((item, received_at))

                db.flush()  # ได้ item.id มาอ้างใน Sale โดยไม่ expire ค่าที่เพิ่งตั้งไป

                for item, received_at in sold_items:
                    sold_at = pick_sold_at(rng, received_at, now)
                    db.add(
                        Sale(
                            item_id=item.id,
                            buyer_name=rng.choice(
                                ["สมชาย ใจดี", "สุดา รักเรียน", "วิชัย มั่นคง", "อรทัย สว่างใจ", "ประยุทธ ตั้งใจ"]
                            ),
                            buyer_phone=f"08{rng.randint(10000000, 99999999)}",
                            branch_id=branch.id,
                            sold_at=sold_at,
                            # ประกันนับจากวันขายจริง ไม่ใช่วันที่รัน seed — ไม่งั้นของที่ "ขายเมื่อ 8 เดือนก่อน"
                            # จะมีประกันยาวกว่าความจริงไป 8 เดือน
                            warranty_expires_at=sold_at + timedelta(days=30 * product.warranty_months),
                            idempotency_key=f"seed-{item.id}",
                        )
                    )
                db.commit()

                # CR-006 — รับเข้าเคลียร์ debounce เท่านั้น ไม่ยิงแจ้งเตือนใหม่ (ตรงกับ items.py จริง)
                # เรียกครั้งเดียวหลังรับเข้าครบ ผลลัพธ์เท่ากับเรียกทีละชิ้นเพราะ logic ดูยอดรวม
                # ไม่ได้ดูว่ารับเข้ากี่ครั้ง
                evaluate_low_stock_alert(db, branch_id=branch.id, sku_id=product.id, may_alert=False)
                if sold:
                    # CR-006 — ขายเป็นจุดเดียวที่ยิงแจ้งเตือนใหม่ได้ (ตรงกับ sales.py จริง)
                    # เรียกเฉพาะเมื่อมีการขายจริง ถ้าไม่มีขายก็ต้องไม่ตั้ง flag
                    # (ไม่งั้นรายการที่สต็อกต่ำตั้งแต่แรกจะถูกมองว่า "แจ้งเตือนไปแล้ว" ทั้งที่ยังไม่เคยแจ้ง)
                    evaluate_low_stock_alert(db, branch_id=branch.id, sku_id=product.id, may_alert=True)

        # --- คำขอสั่งซื้อ (PR) — มาจากหลายสาขา ไม่ใช่สาขาเดียวเหมือนเดิม ---
        # สาขาเล็กขอของบ่อยกว่าเพราะสต็อกน้อย (สำนักงานใหญ่เป็นคลังกลาง ไม่ต้องขอจากตัวเอง)
        requesting = [(b, s, p) for b, s, p in branches if p["name"] != "สำนักงานใหญ่"]
        reject_reasons = [
            "งบประมาณไตรมาสนี้เต็มแล้ว",
            "สินค้าตัวนี้ยอดขายช้า ขอชะลอก่อน",
            "สาขายังมีของค้างสต็อกอยู่ รอระบายก่อน",
        ]
        reject_i = 0
        counts = {"Pending": 0, "Approved": 0, "Rejected": 0}

        for branch, staff, profile in requesting:
            # สาขายิ่งเล็ก ยิ่งขอเยอะ (size น้อย = ของน้อย = ต้องเติมบ่อย)
            n_requests = {0.5: 10, 0.7: 8, 1.0: 6}.get(profile["size"], 6)
            for product in rng.sample(products, n_requests):
                # ถ่วงให้ Pending เยอะกว่า — คิวงานค้างเป็นเรื่องปกติของงานอนุมัติจริง
                # และตาราง "คำขอค้างพิจารณา" บน dashboard ต้องมีของให้เรียงลำดับความเร่งด่วนพอสมควร
                status = rng.choices(["Pending", "Approved", "Rejected"], weights=[5, 3, 2])[0]
                # กระจายวันที่ขอย้อนหลัง เพื่อให้ตาราง "คำขอค้างพิจารณา" เรียงตามอายุได้จริง
                # (ถ้าทุกใบขอวันเดียวกัน คอลัมน์ 'ค้างมากี่วัน' จะเป็นเลขเดียวกันหมด ไม่มีประโยชน์)
                requested_at = now - timedelta(days=rng.randint(1, 45), hours=rng.randint(0, 23))
                pr = PurchaseRequest(
                    branch_id=branch.id,
                    sku_id=product.id,
                    quantity=rng.randint(2, 12),
                    status=status,
                    requested_by=staff.id,
                    requested_at=requested_at,
                    decided_by=None if status == "Pending" else admin.id,
                    # ตัดสินใจหลังขอ 1-5 วัน — สะท้อนรอบอนุมัติจริง ไม่ใช่อนุมัติทันทีวินาทีเดียวกัน
                    decided_at=(
                        None if status == "Pending" else requested_at + timedelta(days=rng.randint(1, 5))
                    ),
                    reject_reason=(
                        reject_reasons[reject_i % len(reject_reasons)] if status == "Rejected" else None
                    ),
                )
                if status == "Rejected":
                    reject_i += 1
                db.add(pr)
                db.commit()
                db.refresh(pr)
                counts[status] += 1

                # FR-010 — PR ที่อนุมัติแล้วต้องมี PO คู่กันเสมอ
                if status == "Approved":
                    db.add(PurchaseOrder(pr_id=pr.id, created_by=admin.id))
                    db.commit()

        print(f"Seed สำเร็จ ที่ {_describe_target()}")
        print("  Admin       -> username: admin      password: admin1234   (ดูแลทุกสาขา, ขายเองไม่ได้)")
        for branch, staff, profile in branches:
            stock = (
                db.query(Item).filter(Item.branch_id == branch.id, Item.status == "InStock").count()
            )
            skus = db.query(BranchSKU).filter(BranchSKU.branch_id == branch.id).count()
            print(
                f"  BranchStaff -> username: {staff.username:<8} password: {profile['password']:<12}"
                f" ({branch.name}: {skus} รุ่น / {stock} ชิ้นคงเหลือ)"
            )
        print(f"  สินค้า {len(products)} รายการ (6 หมวดหมู่ x 10) กระจายตามขนาดสาขา ไม่เท่ากันทุกสาขา")
        print(
            f"  คำขอสั่งซื้อ: {counts['Pending']} Pending, {counts['Approved']} Approved (มี PO), "
            f"{counts['Rejected']} Rejected"
        )
        total_sales = db.query(Sale).count()
        total_items = db.query(Item).count()
        print(
            f"  ประวัติการขาย {total_sales} รายการ จากสินค้าทั้งหมด {total_items} ชิ้น "
            f"กระจายย้อนหลัง {HISTORY_DAYS} วัน (เวลาไทย)"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed(
        reset="--reset" in sys.argv,
        only_if_stale="--reset-if-stale" in sys.argv,
    )
