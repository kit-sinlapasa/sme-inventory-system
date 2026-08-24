from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin, require_any_role
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services.audit import write_audit_log

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),  # Admin + BranchStaff — FR-008 read access
):
    """FR-001, FR-008 — ทั้งสอง role อ่านได้ แก้ไขได้เฉพาะ Admin (ดู endpoint ด้านล่าง)"""
    query = db.query(Product)
    if not include_inactive:
        query = query.filter(Product.is_active.is_(True))
    return query.order_by(Product.category, Product.brand, Product.model).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")
    return product


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # NFR-SEC-02 — Admin เท่านั้น
):
    """FR-001 — เพิ่ม SKU ใหม่ พร้อมระยะเวลารับประกัน"""
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    write_audit_log(
        db,
        actor=current_user,
        action="CREATE_PRODUCT",
        entity_type="Product",
        entity_id=product.id,
        before=None,
        after=payload.model_dump(),
    )
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # NFR-SEC-02 — Admin เท่านั้น
):
    """FR-001 — Backoffice ต้องแก้ไขข้อมูลสินค้าได้"""
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")

    before = {"category": product.category, "brand": product.brand, "model": product.model,
              "spec": product.spec, "warranty_months": product.warranty_months}

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)

    write_audit_log(
        db,
        actor=current_user,
        action="UPDATE_PRODUCT",
        entity_type="Product",
        entity_id=product.id,
        before=before,
        after=updates,
    )
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def suspend_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    FR-001 "ระงับ" — soft delete เท่านั้น (is_active=False)
    ห้าม hard delete: Item หลายชิ้นอาจอ้างอิง product นี้ผ่าน FK อยู่ (ประวัติการขาย/ประกันต้องคงอยู่)
    """
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")
    if not product.is_active:
        return  # idempotent — ระงับซ้ำไม่ error

    product.is_active = False
    db.commit()

    write_audit_log(
        db,
        actor=current_user,
        action="SUSPEND_PRODUCT",
        entity_type="Product",
        entity_id=product.id,
        before={"is_active": True},
        after={"is_active": False},
    )
