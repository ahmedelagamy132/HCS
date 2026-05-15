from sqlalchemy import Column, String, Boolean, text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMPTZ, CITEXT
from .session import Base

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    admin_code = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(CITEXT, unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String, nullable=False, server_default="view_only")
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
