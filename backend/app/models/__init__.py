# import ทุก model ที่นี่ให้ครบ — Alembic autogenerate ต้องเห็นทุกตัวผ่านไฟล์นี้
from app.models.branch import Branch  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.branch_sku import BranchSKU  # noqa: F401
from app.models.item import Item  # noqa: F401
from app.models.sale import Sale  # noqa: F401
from app.models.purchase_request import PurchaseRequest  # noqa: F401
from app.models.purchase_order import PurchaseOrder  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
