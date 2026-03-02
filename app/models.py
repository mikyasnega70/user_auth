from sqlalchemy import Column, INTEGER, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy_utils import EmailType
from .database import Base

class Users(Base):
    __tablename__='users'

    id = Column(INTEGER, primary_key=True)
    email = Column(EmailType, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

