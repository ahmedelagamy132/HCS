from pydantic import BaseModel
from typing import Optional

class HorseCreate(BaseModel):
    name: str
    breed: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None

class HorseResponse(BaseModel):
    horse_code: str
    name: str
    breed: Optional[str]
    color: Optional[str]
    health_status: str
    is_active: bool
    
    class Config:
        from_attributes = True