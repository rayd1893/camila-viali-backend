from sqlalchemy import Column, BigInteger, Integer, String, Numeric, DateTime, Date
from models.engine.connection import Base


class OperacionNiubiz(Base):
    __tablename__ = "operaciones_niubiz"

    # Identificador único (PK)
    id_operacion              = Column(BigInteger, primary_key=True)

    # Datos del comercio
    ruc                       = Column(String(20), nullable=True)
    razon_social              = Column(String(255), nullable=True)
    cod_comercio              = Column(BigInteger, nullable=True)
    nombre_comercial          = Column(String(255), nullable=True)

    # Fechas
    fecha_y_hora_operacion    = Column(String(50), nullable=True)
    fecha_de_deposito         = Column(String(50), nullable=True)

    # Operación
    producto                  = Column(String(100), nullable=True)
    tipo_de_operacion         = Column(String(100), nullable=True)
    tarjeta                   = Column(String(50), nullable=True)
    origen_tarjeta            = Column(String(10), nullable=True)
    tipo_de_tarjeta           = Column(String(50), nullable=True)
    marca_de_tarjeta          = Column(String(50), nullable=True)
    moneda                    = Column(String(20), nullable=True)
    importe_de_operacion      = Column(Numeric(14, 2), nullable=True)
    es_dcc                    = Column(String(10), nullable=True)
    monto_dcc                 = Column(Numeric(14, 2), nullable=True)
    comision_total            = Column(Numeric(14, 2), nullable=True)
    comision_niubiz           = Column(Numeric(14, 2), nullable=True)
    igv                       = Column(Numeric(14, 2), nullable=True)
    suma_depositada           = Column(Numeric(14, 2), nullable=True)
    estado                    = Column(String(10), nullable=True)

    # Banco / terminal
    cuenta_banco_pagador      = Column(BigInteger, nullable=True)
    banco_pagador             = Column(String(100), nullable=True)
    n_serie_terminal          = Column(BigInteger, nullable=True)
    codigo_de_autorizacion    = Column(String(50), nullable=True)
    n_referencia              = Column(String(50), nullable=True)
    n_lote                    = Column(Integer, nullable=True)
    n_voucher                 = Column(String(50), nullable=True)
    tipo_de_abono             = Column(String(100), nullable=True)