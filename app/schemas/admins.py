from pydantic import BaseModel, EmailStr
from typing import Optional

class AdminCreate(BaseModel):
    full_name: str
    email: EmailStr
    role: str = 'view_only'
    password: Optional[str] = 'welcome123'

class AdminResponse(BaseModel):
    id: int
    admin_code: str
    full_name: str
    email: str
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True