from pydantic import BaseModel
from typing import Optional

class Roles(BaseModel):
    role: str
    description: Optional[str] = None
    status: bool = True