from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

class RequestDocument(BaseModel):
    emission_date_start: int
    emission_date_end: int

class RequestReport(BaseModel):
    start_date: date
    end_date: date

class RequestExchange(BaseModel):
    year: int
    month: int

class RequestPayment(BaseModel):
    recordDate: str

class RequestPaymentMatch(BaseModel):
    date_from: date
    date_to: date

class RequestCancellationBook(BaseModel):
    date_from: date
    date_to: date

class CancelCancellationBook(BaseModel):
    ids: list[int]

class RequestCancellationEntry(BaseModel):
    date_from: date
    date_to: date
    niubiz_lookback_days: int = 20
    niubiz_lookahead_days: int = 10

class CancellationEntryFolioOut(BaseModel):
    id: int
    serial_number_report: str
    year_month: str
    sequence_number: int
    document_number: str
    emission_date: Optional[date] = None
    source: str
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RequestRegisterManualFolio(BaseModel):
    serial_number_report: str = Field(min_length=1, max_length=10)
    year_month: str = Field(pattern=r"^\d{4}$", description="Formato AAMM, ej. '2608' para agosto 2026")
    sequence_number: int = Field(gt=0)
    note: Optional[str] = Field(default=None, max_length=300)

class Clients(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    code: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    company_or_person: bool
    is_foreigner: bool

class DocumentTypes(BaseModel):
    id: int
    name: str
    code: str
    is_electronic_document: bool
    is_credit_note: bool
    commercial_code: Optional[str] = None

class Coins(BaseModel):
    id: int
    name: str
    symbol: str
    code: Optional[str] = None

class Documents(BaseModel):
    id: int
    emission_date: date
    expiration_date: date
    generation_date: datetime
    serial_number: str
    tracking_number: str
    total_amount: float
    net_amount: float
    tax_amount: float
    exempt_amount: float
    address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    canceled: bool
    url_pdf: Optional[str] = None
    id_document_type: int
    id_client: Optional[int] = None
    id_coin: int

class Returns(BaseModel):
    id: int
    code: str
    return_date: date
    motive: Optional[str] = None
    type: int
    amount: float
    credit_note_id: int
    reference_document_id: int

class Exchanges(BaseModel):
    day: date
    value: float
    type: str

class Approvals(BaseModel):
    id: int
    bsale: str
    siigo: str

class Centers(BaseModel):
    id: int
    description: str

class Subcenters(BaseModel):
    id: int
    subcenter_code: int
    description: str
    id_center: int

class PaymentTypes(BaseModel):
    id: int
    name: str
    isVirtual: bool
    isCheck: bool
    isCreditNote: bool
    isClientCredit: bool
    isCash: bool
    isCreditMemo: bool
    inactive: bool
    isAgreementBank: bool

class Payments(BaseModel):
    id: int
    recordDate: date
    amount: float
    operationNumber: Optional[str]
    isCreditPayment: bool
    createdAt: datetime
    inactive: bool
    id_document: Optional[int]
    id_payment_type: int
    id_return: Optional[int]

class OperacionesNiubiz(BaseModel):
    id_operacion:               int
    ruc:                        Optional[str]
    razon_social:               Optional[str]
    cod_comercio:               Optional[int]
    nombre_comercial:           Optional[str]
    fecha_y_hora_operacion:     Optional[str]
    fecha_de_deposito:          Optional[str]
    producto:                   Optional[str]
    tipo_de_operacion:          Optional[str]
    tarjeta:                    Optional[str]
    origen_tarjeta:             Optional[str]
    tipo_de_tarjeta:            Optional[str]
    marca_de_tarjeta:           Optional[str]
    moneda:                     Optional[str]
    importe_de_operacion:       Optional[Decimal]
    es_dcc:                     Optional[str]
    monto_dcc:                  Optional[Decimal]
    comision_total:             Optional[Decimal]
    comision_niubiz:            Optional[Decimal]
    igv:                        Optional[Decimal]
    suma_depositada:            Optional[Decimal]
    estado:                     Optional[str]
    cuenta_banco_pagador:       Optional[int]
    banco_pagador:              Optional[str]
    n_serie_terminal:           Optional[int]
    codigo_de_autorizacion:     Optional[str]
    n_referencia:               Optional[str]
    n_lote:                     Optional[int]
    n_voucher:                  Optional[str]
    tipo_de_abono:              Optional[str]