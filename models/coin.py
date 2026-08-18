from sqlalchemy import Column, Integer, String
from models.engine.connection import Base
from sqlalchemy.orm import relationship

class Coin(Base):
    __tablename__ = 'coins'

    id = Column(Integer, primary_key=True)
    name = Column(String(10), unique=True, nullable=False)
    symbol = Column(String(10), unique=True, nullable=False)
    code = Column(String(10), nullable=True)
    documents = relationship("Document", back_populates="coin")
    