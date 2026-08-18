from sqlalchemy import Column, Integer, String, Date, Double
from models.engine.connection import Base

class Exchange(Base):
    __tablename__ = 'exchanges'

    id = Column(Integer, primary_key=True, autoincrement=True)
    day = Column(Date, nullable=False)
    value = Column(Double, nullable=False)
    type = Column(String(1), nullable=False)