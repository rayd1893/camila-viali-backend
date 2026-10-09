from sqlalchemy import Column, BigInteger, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from models.engine.connection import Base

class PaymentSourceMatch(Base):
    __tablename__ = "payment_source_match"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    id_payment      = Column(Integer,    ForeignKey("payments.id"), nullable=False)
    id_operacion    = Column(BigInteger, nullable=False)   # FK lógica: apunta a la tabla de la source
    source          = Column(String(30), nullable=False)   # 'NIUBIZ' | 'AMEX' | ...
    match_type      = Column(String(20), nullable=False)   # EXACT | TIME_TOLERANCE | WEB_ONLY
    time_diff_secs  = Column(Integer,    nullable=True)    # Δt real en segundos (None para WEB_ONLY)
    matched_at      = Column(DateTime,   nullable=False)
    canceled        = Column(Boolean,    nullable=False, default=False, server_default="0")  # marca del libro de cancelación
    canceled_at     = Column(DateTime,   nullable=True)

    __table_args__ = (
        UniqueConstraint("id_payment",            name="uq_match_payment"),
        UniqueConstraint("source", "id_operacion", name="uq_match_operacion_per_source"),
    )