from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Double, ForeignKey
from sqlalchemy.orm import relationship
from models.engine.connection import Base

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    recordDate = Column(Date, nullable=False)
    amount = Column(Double, nullable=False)
    operationNumber = Column(String(50), nullable=True)
    isCreditPayment = Column(Boolean, nullable=False)
    createdAt = Column(DateTime, nullable=False)
    inactive = Column(Boolean, nullable=False)
    id_document = Column(Integer, ForeignKey('documents.id'), nullable=True)
    id_payment_type = Column(Integer, ForeignKey('payment_types.id'), nullable=False)
    id_return = Column(Integer, ForeignKey('returns.id'), nullable=True)
    document = relationship("Document", back_populates="payments")
    payment_type = relationship("PaymentType", back_populates="payments")
    refund =relationship("Return", back_populates="payments")
