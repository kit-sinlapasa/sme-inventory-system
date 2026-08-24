from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: int
    action: str
    entity_type: str
    entity_id: int
    before_value: dict | None
    after_value: dict | None
    occurred_at: datetime
