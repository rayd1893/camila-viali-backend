from sqlalchemy import Column, Integer, String
from models.engine.connection import Base

class Approval(Base):
    __tablename__ = 'approvals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bsale = Column(String(10), unique=True, nullable=False )
    siigo = Column(String(10), unique=True, nullable=False)