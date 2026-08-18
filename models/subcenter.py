from sqlalchemy import Column, Integer, String, ForeignKey
from models.engine.connection import Base
from sqlalchemy.orm import relationship

class Subcenter(Base):
    __tablename__ = 'subcenters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    subcenter_code = Column(Integer, nullable=False)
    description = Column(String(50), nullable=False)
    id_center = Column(Integer, ForeignKey('centers.id'), nullable=False)
    center = relationship("Center", back_populates="subcenters")