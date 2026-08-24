from pydantic import BaseModel, ConfigDict, HttpUrl


class ProductImageCreate(BaseModel):
    image_url: HttpUrl  # validate ว่าเป็น URL รูปแบบถูกต้องอย่างน้อยระดับ syntax


class ProductImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    sort_order: int
