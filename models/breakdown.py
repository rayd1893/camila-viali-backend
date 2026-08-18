from sqlalchemy import Column, Integer, Double, ForeignKey, Table
from sqlalchemy.orm import relationship
from models.engine.connection import Base


class Breakdown(Base):
    __tablename__ = 'breakdowns'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), primary_key=True)
    tax_id = Column(Integer, ForeignKey('taxes.id'), primary_key=True)
    amount = Column( Double, nullable=False)
    document = relationship("Document", back_populates="breakdowns")
    tax = relationship("Tax", back_populates="breakdowns")