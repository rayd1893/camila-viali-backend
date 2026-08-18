from sqlalchemy import Column, Integer, String, Boolean
from models.engine.connection import Base
from sqlalchemy.orm import relationship

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(200), nullable=True)
    last_name = Column(String(200), nullable=True)
    email = Column(String(100), nullable=True)
    code = Column(String(30), nullable=True)
    phone = Column(String(30), nullable=True)
    company = Column(String(500), nullable=True)
    company_or_person = Column(Boolean, nullable=False)
    is_foreigner = Column(Boolean, nullable=False)
    documents = relationship("Document", back_populates="client")