from sqlalchemy import Column, Integer, String, Boolean
from models.engine.connection import Base
from sqlalchemy.orm import relationship

class PaymentType(Base):
    __tablename__ = 'payment_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    isVirtual = Column(Boolean, nullable=False)
    isCheck = Column(Boolean, nullable=False)
    isCreditNote = Column(Boolean, nullable=False)
    isClientCredit = Column(Boolean, nullable=False)
    isCash = Column(Boolean, nullable=False)
    isCreditMemo = Column(Boolean, nullable=False)
    inactive = Column(Boolean, nullable=False)
    isAgreementBank = Column(Boolean, nullable=False)
    payments = relationship("Payment", back_populates="payment_type")