from pydantic import BaseModel, EmailStr
from typing import Optional


class OwnerLogin(BaseModel):
    email: str
    password: str
    rememberMe: bool = False


class OwnerResponse(BaseModel):
    id: str
    client_code: str
    full_name: str
    email: str
    region: Optional[str] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True


class OwnerHorseResponse(BaseModel):
    id: str
    code: str
    name: str
    breed: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    color: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    stable: Optional[str] = None
    stable_code: Optional[str] = None
    box: Optional[str] = None
    stable_full: Optional[str] = None
    registered: Optional[str] = None
    health: Optional[str] = None
    health_txt: Optional[str] = None
    last_check: Optional[str] = None
    stream: Optional[str] = None
    cam: Optional[str] = None
    rtsp_url: Optional[str] = None
    image: Optional[str] = None
    vitals: Optional[dict] = None

    class Config:
        from_attributes = True
