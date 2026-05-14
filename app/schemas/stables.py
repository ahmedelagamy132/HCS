from pydantic import BaseModel
from typing import Optional

class StableCreate(BaseModel):
    name: str
    location: Optional[str] = None
    capacity: Optional[int] = 0

class StableResponse(BaseModel):
    stable_code: str
    name: str
    city: Optional[str]
    capacity: Optional[int]
    status: str
    
    class Config:
        from_attributes = True