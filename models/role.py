from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship
from models.engine.connection import Base
from models.permission import Permission
from models.user import User

role_permission = Table('role_permission', Base.metadata,
                        Column('role_id', Integer,
                               ForeignKey('roles.id', 
                                          onupdate='CASCADE', 
                                          ondelete='CASCADE'),
                                primary_key=True),
                        Column('permission_id', Integer,
                               ForeignKey('permissions.id', 
                                          onupdate='CASCADE', 
                                          ondelete='CASCADE'),
                                primary_key=True),
                        Column('status', Boolean, nullable=False))

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(30), unique=True, nullable=False)
    description = Column(String(50), nullable=True)
    status = Column(Boolean, nullable=False)
    permissions = relationship("Permission", secondary=role_permission, viewonly=False)
    users = relationship("User", back_populates="role")

