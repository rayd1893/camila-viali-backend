from sqlalchemy import Column, Integer, Boolean, Double, String, Table, ForeignKey
from models.engine.connection import Base
from sqlalchemy.orm import relationship

class Tax(Base):
    __tablename__ = 'taxes'

    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)
    percentage = Column(Double, nullable=False)
    forAllProducts = Column(Boolean, nullable=True)
    amountTax = Column(Boolean, nullable=True)
    code = Column(String(10), nullable=True)
    breakdowns = relationship("Breakdown", back_populates="tax")
    
    