from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin, require_any_role
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.user import User
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.schemas.product_image import ProductImageCreate, ProductImageOut
from app.services.audit import write_audit_log

MAX_PRODUCT_IMAGES = 5  # FR-013 (CR-007)

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


@router.post("/{product_id}/restore", response_model=ProductOut)
def restore_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    FR-001 — ยกเลิกการระงับ (กลับมาใช้งานได้)

    เดิมระบบระงับสินค้าได้อย่างเดียว ไม่มีทางเอากลับ — ถ้ากดพลาดก็จบเลย
    เพราะ `ProductUpdate` ไม่มี field `is_active` ให้แก้ผ่าน PUT ด้วย
    endpoint นี้ปิดช่องว่างนั้น (idempotent เหมือน suspend)
    """
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")
    if product.is_active:
        return product  # อยู่ในสถานะใช้งานอยู่แล้ว ไม่ต้องทำอะไร

    product.is_active = True
    db.commit()
    db.refresh(product)

    write_audit_log(
        db,
        actor=current_user,
        action="RESTORE_PRODUCT",
        entity_type="Product",
        entity_id=product.id,
        before={"is_active": False},
        after={"is_active": True},
    )
    return product


@router.post(
    "/{product_id}/images", response_model=ProductImageOut, status_code=status.HTTP_201_CREATED
)
def add_product_image(
    product_id: int,
    payload: ProductImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # FR-013 (CR-007) — Admin เท่านั้น
):
    """สูงสุด 5 รูปต่อ SKU — บังคับที่นี่ ไม่ใช่ DB constraint (เก็บเป็น URL ตาม CR-007)"""
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="ไม่พบสินค้า")

    count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
    if count >= MAX_PRODUCT_IMAGES:
        raise HTTPException(status_code=409, detail=f"สินค้านี้มีรูปครบ {MAX_PRODUCT_IMAGES} รูปแล้ว")

    image = ProductImage(product_id=product_id, image_url=str(payload.image_url), sort_order=count)
    db.add(image)
    db.commit()
    db.refresh(image)

    write_audit_log(
        db,
        actor=current_user,
        action="ADD_PRODUCT_IMAGE",
        entity_type="Product",
        entity_id=product_id,
        before=None,
        after={"image_id": image.id, "image_url": image.image_url},
    )
    return image


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    image = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id, ProductImage.product_id == product_id)
        .first()
    )
    if image is None:
        raise HTTPException(status_code=404, detail="ไม่พบรูปภาพนี้")

    db.delete(image)
    db.commit()

    write_audit_log(
        db,
        actor=current_user,
        action="DELETE_PRODUCT_IMAGE",
        entity_type="Product",
        entity_id=product_id,
        before={"image_id": image_id},
        after=None,
    )
