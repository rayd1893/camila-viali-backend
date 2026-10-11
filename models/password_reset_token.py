from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.engine.connection import Base


class PasswordResetToken(Base):
    """Token de un solo uso para el flujo de recuperación de contraseña.
    ``used_at`` nulo significa que todavía es válido (sujeto a ``expires_at``)."""

    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)

    user = relationship("User")
