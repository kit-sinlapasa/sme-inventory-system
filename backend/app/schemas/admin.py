from datetime import datetime

from pydantic import BaseModel


class PurgeBuyerDataOut(BaseModel):
    purged_count: int
    cutoff: datetime
