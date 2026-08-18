from sqlalchemy import Column, Integer, String
from models.engine.connection import Base
from sqlalchemy.orm import relationship

class Center(Base):
    __tablename__ = 'centers'

    id = Column(Integer, primary_key=True, autoincrement=False)
    description = Column(String(50), nullable=False)
    subcenters = relationship("Subcenter", back_populates="center")