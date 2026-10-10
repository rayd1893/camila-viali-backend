from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from models.engine.connection import Base


class CancellationEntryFolio(Base):
    """Folios (NÚMERO DE DOCUMENTO) ya usados en el asiento contable de
    cancelación, por tienda y mes, sin importar si los asignó el proceso
    automático (`source='auto'`) o si corresponden a un libro creado a mano
    directamente en SIIGO (`source='manual'`). Ambos comparten el mismo
    correlativo para que nunca se repita un número ni queden huecos."""

    __tablename__ = 'cancellation_entry_folio'

    id = Column(Integer, primary_key=True, autoincrement=True)
    serial_number_report = Column(String(10), nullable=False)
    year_month = Column(String(4), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    document_number = Column(String(10), nullable=False)
    emission_date = Column(Date, nullable=True)
    source = Column(String(10), nullable=False)
    note = Column(String(300), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'serial_number_report', 'year_month', 'sequence_number',
            name='uq_folio_store_month_seq',
        ),
    )
