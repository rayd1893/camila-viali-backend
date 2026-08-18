from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Double, ForeignKey, Table
from sqlalchemy.orm import relationship
from models.engine.connection import Base
from models.document_type import DocumentType
from models.client import Client
from models.coin import Coin
from models.tax import Tax

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    emission_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    generation_date = Column(DateTime, nullable=False)
    serial_number = Column(String(20), unique=True, nullable=False)
    tracking_number = Column(String(100), nullable=False)
    total_amount = Column(Double, nullable=False)
    net_amount = Column(Double, nullable=False)
    tax_amount = Column(Double, nullable=False)
    exempt_amount = Column(Double, nullable=False)
    address = Column(String(300), nullable=True)
    district = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    canceled = Column(Boolean, nullable=False)
    url_pdf = Column(String(300), nullable=True)
    id_document_type = Column(Integer, ForeignKey('document_types.id'), nullable=False)
    id_client = Column(Integer, ForeignKey('clients.id'), nullable=True)
    id_coin = Column(Integer, ForeignKey('coins.id'), nullable=False)
    document_type = relationship("DocumentType", back_populates="documents")
    client = relationship("Client", back_populates="documents")
    coin = relationship("Coin", back_populates="documents")
    refund = relationship("Return", back_populates="document")
    breakdowns = relationship("Breakdown", back_populates="document")
    payments = relationship("Payment", back_populates="document")