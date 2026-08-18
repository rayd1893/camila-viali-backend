from sqlalchemy import Column, Integer, String, Boolean
from models.engine.connection import Base

class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    permission = Column(String(30), unique=True, nullable=False)
    description = Column(String(50), nullable=True)
    status = Column(Boolean, nullable=False)
