from sqlalchemy import Column, Integer, String, Boolean
from models.engine.connection import Base
from sqlalchemy.orm import relationship

class DocumentType(Base):
    __tablename__ = 'document_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(5), nullable=False)
    is_electronic_document = Column(Boolean, nullable=False)
    is_credit_note = Column(Boolean, nullable=False)
    commercial_code = Column(String(10), nullable=True)
    documents = relationship("Document", back_populates="document_type")
