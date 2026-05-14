from pydantic import BaseModel, EmailStr
from typing import Optional

class ClientCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    region: Optional[str] = None
    password: Optional[str] = None

class ClientResponse(BaseModel):
    client_code: str
    full_name: str
    email: str
    phone: Optional[str]
    region: Optional[str]
    status: str
    
    class Config:
        from_attributes = True