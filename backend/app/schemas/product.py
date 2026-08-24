from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product_image import ProductImageOut


class ProductCreate(BaseModel):
    category: str = Field(..., examples=["RAM", "Mainboard", "CPU"])
    brand: str
    model: str
    spec: str | None = None
    warranty_months: int = Field(..., gt=0, description="ต้องมากกว่า 0 (FR-001)")


class ProductUpdate(BaseModel):
    category: str | None = None
    brand: str | None = None
    model: str | None = None
    spec: str | None = None
    warranty_months: int | None = Field(None, gt=0)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    brand: str
    model: str
    spec: str | None
    warranty_months: int
    is_active: bool
    images: list[ProductImageOut] = []  # FR-013 (CR-007)
