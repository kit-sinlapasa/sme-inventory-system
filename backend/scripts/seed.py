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
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Windows console เริ่มต้นด้วย cp1252 ซึ่ง print ข้อความไทยไม่ได้ (พังจริงตอน dev บน Windows)
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from passlib.context import CryptContext  # noqa: E402
from sqlalchemy import func  # noqa: E402

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


def seed():
    db = SessionLocal()
    rng = random.Random(42)  # deterministic — รันซ้ำได้ผลเดิมถ้าลบ DB แล้วรันใหม่
    try:
        if db.query(User).filter(User.username == "admin").first():
            print("Seed data มีอยู่แล้ว — ข้าม")
            return

        hq = Branch(name="สำนักงานใหญ่", address="กรุงเทพฯ")
        branch1 = Branch(name="สาขาสยาม", address="สยามสแควร์")
        db.add_all([hq, branch1])
        db.commit()
        db.refresh(hq)
        db.refresh(branch1)

        admin = User(
            username="admin",
            password_hash=pwd_context.hash("admin1234"),
            role="Admin",
            branch_id=None,
        )
        branch_staff = User(
            username="branch1",
            password_hash=pwd_context.hash("branch1234"),
            role="BranchStaff",
            branch_id=branch1.id,
        )
        db.add_all([admin, branch_staff])
        db.commit()
        db.refresh(branch_staff)

        # --- 60 สินค้า (6 หมวดหมู่ x 10) พร้อมรูปตัวอย่าง ---
        products = []
        serial_counter = 0
        combo_index = 0  # นับ (product, branch) แยกจาก serial_counter — กันไม่ให้ modulo วนซ้ำ pattern เดิม
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
                db.commit()
                db.refresh(product)
                products.append(product)

                db.add(
                    ProductImage(
                        product_id=product.id,
                        image_url=f"https://placehold.co/400x300?text={category}",
                        sort_order=0,
                    )
                )
                db.commit()

                # --- รับเข้าสต็อก + ตั้ง reorder point + ขายบางส่วน ทั้ง 2 สาขา ---
                for branch in (hq, branch1):
                    combo_index += 1
                    reorder_point, received, sold = STOCK_SCENARIOS[combo_index % len(STOCK_SCENARIOS)]

                    branch_sku = BranchSKU(branch_id=branch.id, sku_id=product.id, reorder_point=reorder_point)
                    db.add(branch_sku)
                    db.commit()

                    received_items = []
                    for _ in range(received):
                        serial_counter += 1
                        item = Item(
                            sku_id=product.id,
                            serial_number=f"SN-{category.upper()}-{serial_counter:05d}",
                            branch_id=branch.id,
                            status="InStock",
                        )
                        db.add(item)
                        db.commit()
                        db.refresh(item)
                        received_items.append(item)
                        # CR-006 — รับเข้าเคลียร์ debounce เท่านั้น ไม่ยิงแจ้งเตือนใหม่ (ตรงกับ items.py จริง)
                        evaluate_low_stock_alert(db, branch_id=branch.id, sku_id=product.id, may_alert=False)

                    for item in received_items[:sold]:
                        item.status = "Sold"
                        db.add(item)
                        db.commit()
                        sale = Sale(
                            item_id=item.id,
                            buyer_name=rng.choice(
                                ["สมชาย ใจดี", "สุดา รักเรียน", "วิชัย มั่นคง", "อรทัย สว่างใจ", "ประยุทธ ตั้งใจ"]
                            ),
                            buyer_phone=f"08{rng.randint(10000000, 99999999)}",
                            branch_id=branch.id,
                            warranty_expires_at=func.now() + timedelta(days=30 * product.warranty_months),
                            idempotency_key=f"seed-{item.id}",
                        )
                        db.add(sale)
                        db.commit()
                        # CR-006 — ขายเป็นจุดเดียวที่ยิงแจ้งเตือนใหม่ได้ (ตรงกับ sales.py จริง)
                        evaluate_low_stock_alert(db, branch_id=branch.id, sku_id=product.id, may_alert=True)

        # --- คำขอสั่งซื้อ (PR) จากสาขาสยาม ครบทุกสถานะ ---
        pr_products = rng.sample(products, 8)
        pending_products = pr_products[:3]
        approved_products = pr_products[3:6]
        rejected_products = pr_products[6:8]

        for product in pending_products:
            db.add(
                PurchaseRequest(
                    branch_id=branch1.id,
                    sku_id=product.id,
                    quantity=rng.randint(2, 10),
                    status="Pending",
                    requested_by=branch_staff.id,
                )
            )
        db.commit()

        for product in approved_products:
            pr = PurchaseRequest(
                branch_id=branch1.id,
                sku_id=product.id,
                quantity=rng.randint(2, 10),
                status="Approved",
                requested_by=branch_staff.id,
                decided_by=admin.id,
                decided_at=func.now(),
            )
            db.add(pr)
            db.commit()
            db.refresh(pr)
            db.add(PurchaseOrder(pr_id=pr.id, created_by=admin.id))
            db.commit()

        reject_reasons = ["งบประมาณไตรมาสนี้เต็มแล้ว", "สินค้าตัวนี้ยอดขายช้า ขอชะลอก่อน"]
        for product, reason in zip(rejected_products, reject_reasons, strict=True):
            db.add(
                PurchaseRequest(
                    branch_id=branch1.id,
                    sku_id=product.id,
                    quantity=rng.randint(2, 10),
                    status="Rejected",
                    requested_by=branch_staff.id,
                    decided_by=admin.id,
                    decided_at=func.now(),
                    reject_reason=reason,
                )
            )
        db.commit()

        print("Seed สำเร็จ:")
        print("  Admin      -> username: admin      password: admin1234")
        print(f"  BranchStaff -> username: branch1    password: branch1234  (สาขา: {branch1.name})")
        print(f"  สินค้า {len(products)} รายการ (6 หมวดหมู่ x 10), รับเข้าสต็อกทั้ง 2 สาขา")
        print("  คำขอสั่งซื้อ: 3 Pending, 3 Approved (มี PO), 2 Rejected")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
