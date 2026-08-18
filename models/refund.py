from sqlalchemy import Column, Integer, String, Date, Double, ForeignKey
from sqlalchemy.orm import relationship
from models.engine.connection import Base
from models.document import Document

class Return(Base):
    __tablename__ = 'returns'

    id = Column(Integer, primary_key=True)
    code = Column(String(30), nullable=False)
    return_date = Column(Date, nullable=False)
    motive = Column(String(300), nullable=True)
    type = Column(Integer, nullable=False)
    amount =  Column(Double, nullable=False)
    credit_note_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    reference_document_id = Column(Integer, nullable=False)
    document = relationship("Document", back_populates="refund")