from fastapi import APIRouter, Depends, UploadFile, File
from requests import request
from dotenv import load_dotenv
import re
from os import getenv
import pandas as pd
from datetime import date, datetime, timedelta
import pytz
import logging
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, PatternFill
from sqlalchemy import text
from sqlalchemy.orm import Session
from models.engine.connection import get_db
from models.document_type import DocumentType
from models.client import Client
from models.coin import Coin
from models.document import Document
from models.exchange import Exchange
from models.refund import Return
from models.approval import Approval
from models.center import Center
from models.subcenter import Subcenter
from models.tax import Tax
from models.breakdown import Breakdown
from models.payment_type import PaymentType
from models.payment import Payment
from models.niubiz import OperacionNiubiz
from models.payment_source_match import PaymentSourceMatch
from schemas.bill import Clients, Coins, DocumentTypes, Documents, Returns, RequestDocument, RequestExchange, RequestReport, RequestPayment, Exchanges, Approvals, Centers, Subcenters, Payments, PaymentTypes, OperacionesNiubiz, RequestPaymentMatch
from typing import List

load_dotenv()

ACCESS_TOKEN_BSALE = getenv('ACCESS_TOKEN_BSALE')
API_SUNAT_URL = getenv('API_SUNAT_URL')
API_SUNAT_TOKEN = getenv('API_SUNAT_TOKEN')
URI = 'https://api.bsale.io/v1'

payload = {}
headers = {
  'access_token': ACCESS_TOKEN_BSALE
}

router = APIRouter(
    prefix="/bills",
    tags=["bills"],
    responses={404: {"description": "Not found"}}
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# Cargar base niubiz
UNIQUE_FIELD = "id_operacion"
HEADER_ROW   = 7


# Configuraciones para el match
MATCH_TYPE_VOUCHER    = "VOUCHER_MATCH"
MATCH_TYPE_AUTH_CODE  = "AUTH_CODE_MATCH"
MATCH_TYPE_EXACT      = "EXACT"
MATCH_TYPE_TOLERANCE  = "TIME_TOLERANCE"
MATCH_TYPE_WEB_ONLY   = "WEB_ONLY"
MATCH_TYPE_DATE_FALLBACK = "DATE_FALLBACK"

# Prioridad numérica: menor número = mejor match
MATCH_PRIORITY = {
    MATCH_TYPE_VOUCHER:       1,
    MATCH_TYPE_AUTH_CODE:     2,
    MATCH_TYPE_EXACT:         3,
    MATCH_TYPE_TOLERANCE:     4,
    MATCH_TYPE_WEB_ONLY:      5,
    MATCH_TYPE_DATE_FALLBACK: 6,
}
 
TIME_WINDOW_MINUTES = 5  # tolerancia en minutos para POS
DATE_FALLBACK_DAYS  = 2
SOURCE_NIUBIZ = "NIUBIZ"

def convert_float_to_string(ammount, decimal):
  return str(round(round(ammount,decimal) * (10 ** decimal))).zfill(15)

def convert_date_to_timestamp(date:str):
  return int(datetime.strptime(date, '%Y-%m-%d').timestamp())

def get_client(id_client: int, db: Session):
  client = db.query(Client).where(Client.id == id_client).one_or_none()
  return client

def get_serial_number_siigo(serial_number_bsale:str, db: Session):
  print('buscar: ', serial_number_bsale)
  serial_number = db.query(Approval).where(Approval.bsale == serial_number_bsale).one_or_none()
  return serial_number.siigo

def get_subcenter(serial_number_bsale:str):
  subcenter = int(serial_number_bsale[-2:])
  return subcenter



def insert_or_update_client(client: Clients, db: Session):
  client_modify = get_client(client.id, db)
  if client_modify is None:
    new_client = Client(**client.model_dump())
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client
  else:
    ignore = ['id']
    for key, value in client.model_dump().items():
       if key not in ignore:
          setattr(client_modify, key, value)
    db.commit()
    return client_modify

def get_payment_type(id_payment_type: int, db: Session):
  payment_type = db.query(PaymentType).where(PaymentType.id == id_payment_type).one_or_none()
  return payment_type

def insert_or_update_payment_type(payment_type: PaymentTypes, db: Session):
  payment_type_modify = get_payment_type(payment_type.id, db)
  if payment_type_modify is None:
    new_payment_type = PaymentType(**payment_type.model_dump())
    db.add(new_payment_type)
    db.commit()
    db.refresh(new_payment_type)
    return new_payment_type
  ignore = ['id']
  for key, value in payment_type.model_dump().items():
    if key not in ignore:
      setattr(payment_type_modify, key, value)
  db.commit()
  return payment_type_modify 

def get_coin(id_coin: int, db: Session):
  coin = db.query(Coin).where(Coin.id == id_coin).one_or_none()
  return coin

def insert_or_update_coin(coin: Coins, db: Session):
  coin_modify = get_coin(coin.id, db)
  if coin_modify is None:
    new_coin = Coin(**coin.model_dump())
    db.add(new_coin)
    db.commit()
    db.refresh(new_coin)
    return new_coin
  ignore = ['id']
  for key, value in coin.model_dump().items():
    if key not in ignore:
      setattr(coin_modify, key, value)
  db.commit()
  return coin_modify

def get_document_type(id_document_Type: int, db: Session):
  document_type = db.query(DocumentType).where(DocumentType.id == id_document_Type).one_or_none()
  return document_type

def insert_document_type(document_type: DocumentTypes, db:Session):
  found = get_document_type(document_type.id, db)
  if found is None:
    new_document_type = DocumentType(**document_type.model_dump())
    db.add(new_document_type)
    db.commit()
    db.refresh(new_document_type)
    return new_document_type
  return found

def get_document(id_document: int, db:Session):
  document = db.query(Document).where(Document.id == id_document).one_or_none()
  return document

def insert_or_update_document(document: Documents, taxes: list,  db: Session):
  document_modify = get_document(document.id, db)
  if document_modify is None:
    new_document = Document(**document.model_dump())
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    for tax in taxes:
      id_breakdown = tax['id']
      id_tax = tax['tax']['id']
      t = get_tax(id_tax, db)
      amount = tax['totalAmount']
      breakdown = Breakdown (id = id_breakdown, amount = amount, document = new_document, tax = t)
      exist = db.query(Breakdown).filter_by(id = id_breakdown).first()
      if not exist:
        db.add(breakdown)
        db.commit()
        db.refresh(breakdown)
    
    return new_document
  ignore = ['id']
  for key, value in document.model_dump().items():
    if key not in ignore:
      setattr(document_modify, key, value)
  db.commit()
  return document_modify

def get_return(id_return: int, db: Session):
  refund = db.query(Return).where(Return.id == id_return).one_or_none()
  return refund

def insert_or_update_return(refund: Returns, db: Session):
  return_modify = get_return(refund.id, db)
  if return_modify is None:
    new_return = Return(**refund.model_dump())
    db.add(new_return)
    db.commit()
    db.refresh(new_return)
    return new_return
  ignore = ['id']
  for key, value in refund.model_dump().items():
    if key not in ignore:
      setattr(return_modify, key, value)
  db.commit()
  return return_modify

def convert_timestamp_peru(timestamp):
  my_timestamp = datetime.fromtimestamp(timestamp)
  old_timezone = pytz.timezone("America/Lima")
  new_timezone = pytz.timezone("UTC")
  localized_timestamp = old_timezone.localize(my_timestamp)
  new_timezone_timestamp = localized_timestamp.astimezone(new_timezone)
  return new_timezone_timestamp

def get_exchange(day: date, type: str, db: Session):
  exchange = db.query(Exchange).where(Exchange.day == day, Exchange.type == type).one_or_none()
  return exchange

def get_tax(id: int, db:Session):
  tax = db.query(Tax).where(Tax.id == id).one_or_none()
  return tax

def get_list_exchanges(year:int, month:int):
  endpoint_sunat = f'{API_SUNAT_URL}tipo-cambio?year={year}&month={month}'
  payload = {}
  headers_sunat = {
      'Authorization': f'Bearer {API_SUNAT_TOKEN}'
  }
  data = request("GET", endpoint_sunat, headers=headers_sunat, data=payload)
  return data.json()

def get_payment(id_payment: int, db: Session):
  payment = db.query(Payment).where(Payment.id == id_payment).one_or_none()
  return payment

def insert_or_update_payment(payment: Payments, db: Session):
  payment_modify = get_payment(payment.id, db)
  if payment_modify is None:
    new_payment = Payment(**payment.model_dump())
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment
  ignore = ['id']
  for key, value in payment.model_dump().items():
    if key not in ignore:
      setattr(payment_modify, key, value)
  db.commit()
  return payment_modify


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace("á", "a").str.replace("é", "e")
        .str.replace("í", "i").str.replace("ó", "o")
        .str.replace("ú", "u").str.replace("ñ", "n")
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return df
 
 
def get_operacion(id_operacion: int, db: Session):
    return db.query(OperacionNiubiz).where(OperacionNiubiz.id_operacion == id_operacion).one_or_none()
 
 
def insert_operacion(operacion: OperacionesNiubiz, db: Session):
    found = get_operacion(operacion.id_operacion, db)
    if found is None:
        new_operacion = OperacionNiubiz(**operacion.model_dump())
        db.add(new_operacion)
        db.commit()
        db.refresh(new_operacion)
        return new_operacion
    return found
 
 
def process_niubiz_file(file_bytes: bytes, db: Session):
    df = pd.read_excel(file_bytes, header=HEADER_ROW)
    df = normalize_columns(df)
 
    # Retirar registros sin id_operacion
    df = df.dropna(subset=[UNIQUE_FIELD])
    df = df[df[UNIQUE_FIELD].astype(str).str.strip() != ""]
    df = df.drop_duplicates(subset=[UNIQUE_FIELD])
 
    # Convertir id_operacion a entero
    df[UNIQUE_FIELD] = df[UNIQUE_FIELD].astype("int64")
    df["ruc"] = df["ruc"].apply(lambda x: str(int(x)) if x is not None and pd.notna(x) else None)
    # Forzar n_referencia a string (valores > BIGINT max)
    df["n_referencia"] = df["n_referencia"].apply(lambda x: str(int(x)) if x is not None and pd.notna(x) else None)
    # Forzar n_voucher a string
    df["n_voucher"] = df["n_voucher"].apply(lambda x: str(int(x)) if x is not None and pd.notna(x) else None)
    
    # Reemplazar NaN por None para compatibilidad con Pydantic
    df = df.where(pd.notna(df), None)
 
    inserted = 0
    skipped  = 0
 
    for _, row in df.iterrows():
        data = row.to_dict()
        operacion = OperacionesNiubiz(**data)
        found = get_operacion(operacion.id_operacion, db)
        if found is None:
            new_operacion = OperacionNiubiz(**operacion.model_dump())
            db.add(new_operacion)
            db.commit()
            db.refresh(new_operacion)
            inserted += 1
        else:
            skipped += 1
 
    return inserted, skipped

def parse_niubiz_fecha(raw: str) -> datetime | None:
    """
    Convierte '01-03-2026 10:54' (dd-mm-yyyy HH:MM) a datetime.
    Retorna None si el valor es nulo o no parseable.
    """
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), "%d-%m-%Y %H:%M")
    except ValueError:
        log.warning("Fecha Niubiz no parseable: %r", raw)
        return None
 
 
def split_commercial_codes(raw: str | None) -> list[str]:
    """
    '650193209 | 650236454' → ['650193209', '650236454']
    Retorna lista vacía si el valor es NULL o vacío.
    """
    if not raw:
        return []
    return [c.strip() for c in re.split(r"\|", raw) if c.strip()]
 
 
def classify_match(delta_secs: int | None, is_web: bool) -> str:
    if is_web:
        return MATCH_TYPE_WEB_ONLY
    if delta_secs == 0:
        return MATCH_TYPE_EXACT
    return MATCH_TYPE_TOLERANCE

def load_niubiz(
    session: Session,
    date_from: date,
    date_to: date,
) -> list[dict]:
    """
    Carga operaciones_niubiz acotadas al rango [date_from, date_to].
 
    fecha_y_hora_operacion tiene formato 'dd-mm-yyyy HH:MM' (texto), por lo
    que el filtro de rango se aplica en Python tras parsear, no en SQL.
    Para evitar cargar todo el histórico se añade un margen de ±1 día al
    rango en el filtro de texto usando STR_TO_DATE, lo cual sirve de pre-
    filtro aproximado que luego el parseo Python afina con exactitud.
    """
    # Pre-filtro en MySQL: convierte la columna de texto a DATE para el WHERE.
    # El margen de 1 día cubre el desfase de zona horaria o registros limítrofes.
    rows = session.execute(
        text("""
            SELECT
                id_operacion,
                cod_comercio,
                importe_de_operacion,
                fecha_y_hora_operacion,
                producto,
                n_voucher,
                codigo_de_autorizacion
            FROM operaciones_niubiz
            WHERE STR_TO_DATE(
                      SUBSTRING(fecha_y_hora_operacion, 1, 10),
                      '%d-%m-%Y'
                  ) BETWEEN :date_from - INTERVAL 1 DAY
                        AND :date_to   + INTERVAL 1 DAY
        """),
        {"date_from": date_from, "date_to": date_to},
    ).mappings().all()

    result = []
    for r in rows:
        fecha = parse_niubiz_fecha(r["fecha_y_hora_operacion"])
        if fecha is None:
            continue
        # Filtro exacto en Python después del pre-filtro SQL
        if not (date_from <= fecha.date() <= date_to):
            continue
        raw_voucher = r["n_voucher"]
        n_voucher_last4 = str(raw_voucher)[-4:] if raw_voucher else None
        result.append({
            "id_operacion":          r["id_operacion"],
            "cod_comercio":          str(r["cod_comercio"]),
            "monto":                 float(r["importe_de_operacion"] or 0),
            "fecha":                 fecha,
            "is_web":                (r["producto"] or "") == "Niubiz Pago Web",
            "n_voucher_last4":       n_voucher_last4,
            "cod_autorizacion":      str(r["codigo_de_autorizacion"]) if r["codigo_de_autorizacion"] else None,
        })
    log.info(
        "Niubiz cargado: %d operaciones (%s → %s)",
        len(result), date_from, date_to,
    )
    return result
 
 
def load_payments(
    session: Session,
    date_from: date,
    date_to: date,
) -> list[dict]:
    """
    Carga payments cuyos documentos tienen emission_date en [date_from, date_to].
    Solo incluye payments NO inactivos y de documentos NO cancelados.
    Normaliza commercial_code múltiple en lista de strings.
    """
    rows = session.execute(
        text("""
            SELECT
                p.id            AS id_payment,
                p.amount,
                p.createdAt,
                p.recordDate,
                p.operationNumber,
                dt.commercial_code
            FROM payments p
            JOIN documents      d  ON d.id   = p.id_document
            JOIN document_types dt ON dt.id  = d.id_document_type
            JOIN payment_types  pt ON pt.id  = p.id_payment_type
            WHERE p.inactive           = 0
              AND d.canceled           = 0
              AND dt.commercial_code IS NOT NULL
              AND dt.commercial_code  <> 'NULL'
              AND d.emission_date BETWEEN :date_from AND :date_to
              AND pt.name LIKE 'niubiz%'
        """),
        {"date_from": date_from, "date_to": date_to},
    ).mappings().all()

    result = []
    for r in rows:
        codes = split_commercial_codes(r["commercial_code"])
        if not codes:
            continue
        result.append({
            "id_payment":       r["id_payment"],
            "monto":            float(r["amount"] or 0),
            "created_at":       r["createdAt"],
            "record_date":      r["recordDate"],
            "operation_number": r["operationNumber"],
            "codes":            codes,
        })
    log.info(
        "Payments cargado: %d registros (%s → %s)",
        len(result), date_from, date_to,
    )
    return result

def build_niubiz_index(niubiz_rows: list[dict]) -> dict:
    """
    Índice: cod_comercio → lista de operaciones de ese comercio.
    Separamos POS y Web para aplicar lógicas distintas.
    """
    idx: dict[str, list[dict]] = {}
    for op in niubiz_rows:
        key = op["cod_comercio"]
        idx.setdefault(key, []).append(op)
    return idx
 
 
# ──────────────────────────────────────────────
# 5. Núcleo del matching
# ──────────────────────────────────────────────
 
def find_best_match(
    payment: dict,
    niubiz_index: dict,
    used_operaciones: set,
    max_priority: int | None = None,
) -> dict | None:
    """
    Para un payment dado busca la mejor operación Niubiz disponible.

    Criterios de selección (en orden de prioridad):
      1. VOUCHER_MATCH → últimos 4 dígitos n_voucher == operationNumber + Δmonto ≤ 0.1
      2. AUTH_CODE     → codigo_de_autorizacion == operationNumber + Δmonto ≤ 0.1 (Web)
      3. EXACT         → monto + comercio + |Δt| = 0  (dentro de ±3 min exacto)
      4. TIME_TOLERANCE→ monto + comercio + 0 < |Δt| ≤ 3 min
      5. WEB_ONLY      → monto + comercio, sin restricción de tiempo (producto Web)
      6. DATE_FALLBACK → monto + comercio + misma fecha calendario ±1 día
                         (POS que no cruzó por tiempo; último recurso)

    max_priority: si se indica, descarta candidatos con prioridad > max_priority.
    Prioridad de desempate dentro del mismo tipo:
      menor Δt → menor id_operacion
    """
    candidates = []
    window        = timedelta(minutes=TIME_WINDOW_MINUTES)
    fallback_days = timedelta(days=DATE_FALLBACK_DAYS)
    p_monto       = round(payment["monto"], 2)
    p_ts          = payment["created_at"]
    p_record_date = payment["record_date"]  # date, para DATE_FALLBACK
    p_op_number   = payment.get("operation_number")  # operationNumber tal cual desde payments

    for code in payment["codes"]:
        for op in niubiz_index.get(code, []):

            if op["id_operacion"] in used_operaciones:
                continue

            if op["is_web"]:
                # Web prioridad 1: codigo_de_autorizacion == operationNumber
                if (
                    op.get("cod_autorizacion")
                    and p_op_number
                    and op["cod_autorizacion"] == str(p_op_number)
                    and abs(round(op["monto"], 2) - p_monto) <= 0.1
                ):
                    candidates.append({
                        "id_operacion": op["id_operacion"],
                        "match_type":   MATCH_TYPE_AUTH_CODE,
                        "delta_secs":   None,
                        "priority":     MATCH_PRIORITY[MATCH_TYPE_AUTH_CODE],
                    })
                    continue  # no evaluar WEB_ONLY para esta misma op

                # Web fallback: solo monto exacto + comercio
                if round(op["monto"], 2) != p_monto:
                    continue
                candidates.append({
                    "id_operacion": op["id_operacion"],
                    "match_type":   MATCH_TYPE_WEB_ONLY,
                    "delta_secs":   None,
                    "priority":     MATCH_PRIORITY[MATCH_TYPE_WEB_ONLY],
                })
            else:
                # POS: prioridad 1 → cruce por n_voucher (últimos 4 dígitos) + Δmonto ≤ 0.1
                if (
                    op.get("n_voucher_last4")
                    and p_op_number
                    and str(p_op_number).endswith(op["n_voucher_last4"])
                    and abs(round(op["monto"], 2) - p_monto) <= 0.1
                ):
                    candidates.append({
                        "id_operacion": op["id_operacion"],
                        "match_type":   MATCH_TYPE_VOUCHER,
                        "delta_secs":   None,
                        "priority":     MATCH_PRIORITY[MATCH_TYPE_VOUCHER],
                    })
                    continue  # ya encontró el mejor tipo para esta op, no evaluar más

                # POS fallback: monto exacto + ventana de tiempo / fecha
                if round(op["monto"], 2) != p_monto:
                    continue
                if p_ts is None:
                    continue
                delta = abs(op["fecha"] - p_ts)
                if delta <= window:
                    delta_secs = int(delta.total_seconds())
                    mtype = MATCH_TYPE_EXACT if delta_secs == 0 else MATCH_TYPE_TOLERANCE
                    candidates.append({
                        "id_operacion": op["id_operacion"],
                        "match_type":   mtype,
                        "delta_secs":   delta_secs,
                        "priority":     MATCH_PRIORITY[mtype],
                    })
                elif p_record_date is not None and abs(op["fecha"].date() - p_record_date) <= fallback_days:
                    delta_secs = int(abs(op["fecha"] - p_ts).total_seconds())
                    candidates.append({
                        "id_operacion": op["id_operacion"],
                        "match_type":   MATCH_TYPE_DATE_FALLBACK,
                        "delta_secs":   delta_secs,
                        "priority":     MATCH_PRIORITY[MATCH_TYPE_DATE_FALLBACK],
                    })
 
    if max_priority is not None:
        candidates = [c for c in candidates if c["priority"] <= max_priority]

    if not candidates:
        return None

    # Ordenar: mejor tipo → menor Δt → menor id_operacion
    candidates.sort(key=lambda c: (
        c["priority"],
        c["delta_secs"] if c["delta_secs"] is not None else 0,
        c["id_operacion"],
    ))
    return candidates[0]

@router.post('/matching_niubiz')
def run_matching(
    requestMatch: RequestPaymentMatch,
    session: Session = Depends(get_db)
):
    """
    Ejecuta el matching para el rango [date_from, date_to] basado en
    documents.emission_date y persiste los resultados.
 
    El proceso es siempre incremental dentro del rango:
      - Payments del período que ya tienen match → se saltan.
      - Operaciones Niubiz ya usadas (de cualquier período) → no se reusan.
 
    Para re-procesar un período ya matcheado, primero borra manualmente
    los registros del rango en payment_source_match:
        DELETE mn FROM payment_source_match mn
        JOIN payments p ON p.id = mn.id_payment
        JOIN documents d ON d.id = p.id_document
        WHERE mn.source = 'NIUBIZ'
          AND d.emission_date BETWEEN '2026-03-01' AND '2026-03-31';
    Luego vuelve a ejecutar run_matching con el mismo rango.
    """
    date_from = requestMatch.date_from
    date_to = requestMatch.date_to
    now = datetime.utcnow()
 
    log.info("Iniciando matching | rango: %s → %s", date_from, date_to)
 
    # — Cargar datos acotados al rango —
    niubiz_rows  = load_niubiz(session, date_from, date_to)
    payment_rows = load_payments(session, date_from, date_to)
 
    if not payment_rows:
        log.info("Sin payments en el rango. Proceso finalizado.")
        return
 
    niubiz_index = build_niubiz_index(niubiz_rows)
 
    # — Operaciones ya usadas por esta misma source en CUALQUIER período previo —
    used_operaciones: set = set(
        row[0] for row in session.execute(
            text("SELECT id_operacion FROM payment_source_match WHERE source = :source"),
            {"source": SOURCE_NIUBIZ},
        ).all()
    )
 
    # — Payments del rango que ya tienen match (runs previos del mismo período) —
    payment_ids_in_range = [p["id_payment"] for p in payment_rows]
    already_matched: set = set()
    if payment_ids_in_range:
        placeholders = ", ".join(str(i) for i in payment_ids_in_range)
        already_matched = set(
            row[0] for row in session.execute(
                text(f"""
                    SELECT id_payment FROM payment_source_match
                    WHERE id_payment IN ({placeholders})
                """)
            ).all()
        )
 
    # — Matching en dos pasadas para evitar que matches débiles consuman ops
    #   que pertenecen a un VOUCHER/AUTH_CODE de otro payment —
    matches_to_insert = []
    unmatched = []
    matched_in_pass1: set[int] = set()

    # Pasada 1: solo VOUCHER_MATCH y AUTH_CODE (prioridades 1 y 2)
    for payment in payment_rows:
        if payment["id_payment"] in already_matched:
            continue
        best = find_best_match(payment, niubiz_index, used_operaciones, max_priority=2)
        if best is None:
            continue
        used_operaciones.add(best["id_operacion"])
        matched_in_pass1.add(payment["id_payment"])
        matches_to_insert.append({
            "id_payment":     payment["id_payment"],
            "id_operacion":   best["id_operacion"],
            "source":         SOURCE_NIUBIZ,
            "match_type":     best["match_type"],
            "time_diff_secs": best["delta_secs"],
            "matched_at":     now,
        })

    # Pasada 2: EXACT, TIME_TOLERANCE, WEB_ONLY, DATE_FALLBACK
    for payment in payment_rows:
        if payment["id_payment"] in already_matched:
            continue
        if payment["id_payment"] in matched_in_pass1:
            continue
        best = find_best_match(payment, niubiz_index, used_operaciones)
        if best is None:
            unmatched.append(payment["id_payment"])
            continue
        used_operaciones.add(best["id_operacion"])
        matches_to_insert.append({
            "id_payment":     payment["id_payment"],
            "id_operacion":   best["id_operacion"],
            "source":         SOURCE_NIUBIZ,
            "match_type":     best["match_type"],
            "time_diff_secs": best["delta_secs"],
            "matched_at":     now,
        })
 
    # — Insertar en batch —
    if matches_to_insert:
        session.execute(
            PaymentSourceMatch.__table__.insert(),
            matches_to_insert,
        )
        session.commit()
 
    # — Resumen —
    procesados = len(payment_rows) - len(already_matched)
    log.info("─" * 50)
    log.info("Rango              :  %s → %s", date_from, date_to)
    log.info("Payments procesados:  %d", procesados)
    log.info("Ya matcheados (skip): %d", len(already_matched))
    log.info("Matches nuevos     :  %d", len(matches_to_insert))
    log.info("Sin match          :  %d", len(unmatched))
    by_type: dict[str, int] = {}
    for m in matches_to_insert:
        by_type[m["match_type"]] = by_type.get(m["match_type"], 0) + 1
    for mtype, count in sorted(by_type.items()):
        log.info("  %-18s :  %d", mtype, count)
    if unmatched:
        log.warning("Payments sin match (ids): %s", unmatched[:20])
    log.info("─" * 50)

    return {
        'code':     200,
        'message':  'Archivo Niubiz cargado exitosamente',
        'unmatched': unmatched
    }

@router.post('/upload_niubiz')
async def upload_niubiz(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_bytes = await file.read()
    inserted, skipped = process_niubiz_file(file_bytes, db)
 
    return {
        'code':     200,
        'message':  'Archivo Niubiz cargado exitosamente',
        'inserted': inserted,
        'skipped':  skipped,
    }
 

@router.post('/insert_payment_types')
def insert_payment_type(db: Session = Depends(get_db)):
  i = 0
  offset = 0
  total = 0
  while i <= total:
    endpoint_bsale = f'{URI}/payment_types.json?offset={offset}&limit=50'
    payload = {}
    response = request("GET", endpoint_bsale, headers=headers, data=payload)
    count = response.json()['count']
    items = response.json()['items']
    for payment_type in items:
      isVirtual =  payment_type['isVirtual'] is not None if payment_type['isVirtual'] else 0
      payment_type_to_insert = {
        'id': payment_type['id'],
        'name': payment_type['name'],
        'isVirtual': isVirtual,
        'isCheck': payment_type['isCheck'],
        'isCreditNote': payment_type['isCreditNote'],
        'isClientCredit': payment_type['isClientCredit'],
        'isCash': payment_type['isCash'],
        'isCreditMemo': payment_type['isCreditMemo'],
        'inactive': payment_type['state'],
        'isAgreementBank': payment_type['isAgreementBank']
      }
      insert_or_update_payment_type(PaymentTypes(**payment_type_to_insert), db)
    total = int(count/50)
    offset += 50
    i += 1
  result = {
    'code' : 200,
    'message': 'Tipos de pago insertados'
  }
  return result


@router.post('/insert_payments')
def insert_payment(requestPayment: RequestPayment, db: Session = Depends(get_db)):

  i = 0
  offset = 0
  total = 0
  recordDate = convert_date_to_timestamp(requestPayment.recordDate)
  while i <= total:
    endpoint_bsale = f'{URI}/payments.json?offset={offset}&limit=50&recorddate={recordDate}&expand=[dynamic_attributes]'
    print('endpoint', endpoint_bsale)
    payload = {}
    response = request("GET", endpoint_bsale, headers=headers, data=payload)
    count = response.json()['count']
    items = response.json()['items']
    for payment in items:
      operationNumber = None
      if payment['attributes']:
          for attribute in payment['attributes']:
              if attribute['name'] == 'N° de operación' or attribute['name'] == 'Número Operación':
                operationNumber = attribute['value']
      if payment['documentId'] == 0:
        continue
      payment_to_insert = {
        'id': payment['id'],
        'recordDate': convert_timestamp_peru(payment['recordDate']).date(),
        'amount': payment['amount'],
        'operationNumber': operationNumber,
        'isCreditPayment': payment['isCreditPayment'],
        'createdAt': datetime.fromtimestamp(payment['createdAt']),
        'inactive': payment['state'],
        'id_document': payment['documentId'],
        'id_payment_type': payment['payment_type']['id']
      }
      insert_or_update_payment(Payments(**payment_to_insert), db)
    total = int(count/50)
    offset += 50
    i += 1
  result = {
    'code' : 200,
    'message': 'Pagos insertados'
  }
  return result


@router.post('/insert_exchanges')
def insert_exchange(request: RequestExchange, db: Session = Depends(get_db)):
  exchanges = get_list_exchanges(request.year, request.month)
  for exchange in exchanges:
    purchase_price = float(exchange['precioCompra'])
    sale_price = float(exchange['precioVenta'])
    day = exchange['fecha']
    exchange_purchase_price = get_exchange(day, 'C', db)
    exchange_sale_price = get_exchange(day, 'V', db)
    
    if exchange_purchase_price is None:
      e = Exchanges(day=day, value=purchase_price, type='C')
      new_exchange = Exchange(**e.model_dump())
      db.add(new_exchange)
      db.commit()
      db.refresh(new_exchange)
    if exchange_sale_price is None:
      e = Exchanges(day=day, value=sale_price, type='V')
      new_exchange = Exchange(**e.model_dump())
      db.add(new_exchange)
      db.commit()
      db.refresh(new_exchange)
  result = {
    'code' : 200,
    'message': 'Tipos de cambio insertados'
  }

  return result
    

@router.get("/extract_data")
def find_documents(requestDocument: RequestDocument, db: Session = Depends(get_db)):
  start = requestDocument.emission_date_start
  end = requestDocument.emission_date_end
  i = 0
  offset = 0
  total = 0
  while i <= total:
    url = "{}/documents.json?emissiondaterange=[{},{}]&limit=50&offset={}&expand=[document_type,client, coin, document_taxes]".format(URI, start, end, offset)
    print('url: ', url)
    response = request("GET", url, headers=headers, data=payload)
    bills = response.json()['items']
    count = response.json()['count']
    for bill in bills:
      coin = bill['coin']
      id_coin = coin['id']
      new_coin = Coins(
        id=id_coin,
        name=coin['name'],
        symbol=coin['symbol']
      )
      insert_or_update_coin(new_coin, db)
      document_type = bill['document_type']
      print('off', offset)
      print('doc_type', document_type)
      new_document_type = DocumentTypes(
        id=document_type['id'],
        name=document_type['name'],
        code=document_type['code'],
        is_electronic_document=document_type['isElectronicDocument'],
        is_credit_note=document_type['isCreditNote']
      )
      insert_document_type(new_document_type, db)
      id_client = None
      try:
        client = bill['client']
        id_client = client['id']
        new_client = Clients(
          id = client['id'],
          first_name = client['firstName'],
          new_client = client['lastName'],
          email = client['email'],
          code = client['code'],
          phone = client['phone'],
          company = client['company'],
          company_or_person = client['companyOrPerson'],
          is_foreigner=client['isForeigner']
        )
            
        insert_or_update_client(new_client, db)
      except KeyError:
        print('El documento no tiene un cliente asociado')
      print('bill_id', bill['id'])
      print('doc_type_id', document_type['id'])
      new_document = Documents(
        id=bill['id'],
        emission_date=convert_timestamp_peru(bill['emissionDate']).date(),
        expiration_date=convert_timestamp_peru(bill['expirationDate']).date(),
        generation_date=convert_timestamp_peru(bill['generationDate']),
        serial_number=bill['serialNumber'],
        tracking_number=bill['trackingNumber'],
        total_amount=bill['totalAmount'],
        net_amount=bill['netAmount'],
        tax_amount=bill['taxAmount'],
        exempt_amount=bill['exemptAmount'],
        address=bill['address'],
        district=bill['district'],
        city=bill['city'],
        canceled=bill['state'],
        url_pdf=bill['urlPdf'],
        id_document_type=document_type['id'],
        id_client=id_client,
        id_coin=coin['id']
      )
      doc_taxes = bill['document_taxes']['items']
      insert_or_update_document(new_document, doc_taxes,  db)

      if document_type['isCreditNote']:
        url_returns = "{}/returns.json?creditnoteid={}&expand=[reference_document, credit_note]".format(URI, bill['id'])
        response_returns = request("GET", url_returns, headers=headers, data=payload)
        returns = response_returns.json()['items']
        for refund in returns:
          reference_document = refund['reference_document']
          doc = get_document(reference_document['id'], db)
          if doc is None:
            id_clt = None
            try:
              clt = reference_document['client']
              id_clt = clt['id']
              find_client = get_client(id_clt, db)
              if find_client is None:
                response_clt = request("GET", clt['href'], headers=headers, data=payload)
                c = response_clt.json()
                new_clt = Clients(
                  id = c['id'],
                  first_name = c['firstName'],
                  new_client = c['lastName'],
                  email = c['email'],
                  code = c['code'],
                  phone = c['phone'],
                  company = c['company'],
                  company_or_person = c['companyOrPerson'],
                  is_foreigner=c['isForeigner']
                )
                insert_or_update_client(new_clt)
            except:
              pass
            new_doc = Documents(id=reference_document['id'],
                                emission_date=convert_timestamp_peru(reference_document['emissionDate']).date(),
                                expiration_date=convert_timestamp_peru(reference_document['expirationDate']).date(),
                                generation_date=convert_timestamp_peru(reference_document['generationDate']),
                                serial_number=reference_document['serialNumber'],
                                tracking_number=reference_document['trackingNumber'],
                                total_amount=reference_document['totalAmount'],
                                net_amount=reference_document['netAmount'],
                                tax_amount=reference_document['taxAmount'],
                                exempt_amount=reference_document['exemptAmount'],
                                address=reference_document['address'],
                                district=reference_document['district'],
                                city=reference_document['city'],
                                canceled=reference_document['state'],
                                url_pdf=reference_document['urlPdf'],
                                id_document_type=reference_document['document_type']['id'],
                                id_client=id_clt,
                                id_coin=reference_document['coin']['id'])
            url_tax = '{}/documents/{}/document_taxes.json'.format(URI, reference_document['id'])
            response_tax = request("GET", url_tax, headers=headers, data={})
            txs = response_tax.json()['items']
            insert_or_update_document(new_doc, txs,  db)
          new_return = Returns(
            id=refund['id'],
            code=refund['code'],
            return_date=convert_timestamp_peru(refund['returnDate']).date(),
            motive=refund['motive'],
            type=refund['type'],
            amount=refund['amount'],
            credit_note_id=refund['credit_note']['id'],
            reference_document_id=reference_document['id']
          )
          insert_or_update_return(new_return, db)
    total = int(count/50)
    offset += 50
    i += 1
    result = {
      'code': 200,
      'message': 'Actualizado correctamente'
    }
  return result

@router.get("/sales_book")
def generate_sales_book(dates: RequestReport, db: Session = Depends(get_db)):
  documents = db.query(Document).where(Document.emission_date >= dates.start_date, Document.emission_date <= dates.end_date).all()
  report = []
  for document in documents:
    data = {}
    if document.document_type.code == '09':
      continue
    data['Código Tributario'] = document.document_type.code
    data['Serie'], data['Número'] = (document.serial_number).split("-")
    data['Emisión'] = document.emission_date
    data['Receptor'] = ''
    data['Código Receptor'] = ''
    data['Tipo Receptor'] = ''
    if document.id_client is not None:
      data['Receptor'] = document.client.company
      data['Código Receptor'] = document.client.code
      if document.client.is_foreigner:
        data['Tipo Receptor'] = 0
      elif document.client.company_or_person:
        data['Tipo Receptor'] = 6
      else:
        data['Tipo Receptor'] = 1
    data['Emisor'] = ''
    data['Código Emisor'] = ''
    data['Exonerado'] = document.exempt_amount
    data['IGV'] = document.tax_amount
    data['ISC'] = 0
    data['ICBPER'] = 0
    data['Neto'] = document.net_amount
    data['Inafecto'] = document.exempt_amount
    data['Otros Impuestos'] = 0
    data['Total'] = document.total_amount
    data['Código Moneda'] = 'PEN'
    data['Tipo Cambio'] = 1
    data['Código Referencia'] = ''
    data['Serie Referencia'] = ''
    data['Número Referencia'] = ''
    data['Fecha Referencia'] = ''
    if document.document_type.is_credit_note:
      data['Exonerado'] = document.exempt_amount * -1
      data['IGV'] = document.tax_amount * -1
      data['Neto'] = document.net_amount * -1
      data['Inafecto'] = document.exempt_amount * -1
      data['Total'] = document.total_amount * -1
      print('devolucion')
      refund = db.query(Return).where(Return.credit_note_id == document.id).one()
      document_reference = db.query(Document).where(Document.id == refund.reference_document_id).one()
      data['Código Referencia'] = document_reference.document_type.code
      data['Serie Referencia'], data['Número Referencia'] = (document_reference.serial_number).split("-")
      data['Fecha Referencia'] = document_reference.emission_date
    data['Anulado'] = ''
    if document.canceled:
      data['Anulado'] = 'Si'
      data['Exonerado'] = 0
      data['IGV'] = 0
      data['Neto'] = 0
      data['Inafecto'] = 0
      data['Total'] = 0
    report.append(data)
  df = pd.DataFrame(data=report)
  df.to_excel('report.xlsx', index=False)
  return report

@router.get("/book_entry")
def generate_book_entry(dates: RequestReport, db: Session = Depends(get_db)):
  documents = db.query(Document).where(Document.emission_date >= dates.start_date, Document.emission_date <= dates.end_date).all()
  report = []
  igv = 0.18
  for document in documents:
    if document.document_type.code == '09':
      continue
    doc_serial_number = document.serial_number
    cod_serie, doc_number = doc_serial_number.split("-")
    cod_serial_siigo = get_serial_number_siigo(cod_serie, db)
    serie ,doc_cod = (cod_serial_siigo).split("-")
    rT = serie
    rSerie = doc_cod
    rnumber = str(doc_number)
    ruc = '99999999'
    client_name = 'CONSUMIDOR FINAL'
    if document.id_client is not None:
      ruc = str(document.client.code)
      client_name = str(document.client.company).upper()
    sucursal = '0'
    if document.document_type.code == '07':
      ctas = ['7401010100', '1201020100', '4001010100', '4001080900'] 
    else:
      ctas = ['7002020101', '1201020100', '4001010100', '4001080900', '2101010101']
    year_emission = (document.emission_date).strftime("%Y")
    month_emission = (document.emission_date).strftime("%m")
    day_emission = (document.emission_date).strftime("%d")
    expiration = (document.expiration_date).strftime("%Y%m%d")
    serie_references_siigo = cod_serial_siigo
    number_reference = rnumber
    emission_year_reference = year_emission
    emission_month_reference = month_emission
    emission_day_reference = day_emission
    if document.document_type.is_credit_note:
      refund = db.query(Return).where(Return.credit_note_id == document.id).one()
      document_reference = db.query(Document).where(Document.id == refund.reference_document_id).one()
      serie_references_bsale, number_reference = (document_reference.serial_number).split("-")
      emission_references = document_reference.emission_date
      serie_references_siigo = (get_serial_number_siigo(serie_references_bsale, db))
      emission_year_reference = emission_references.strftime("%Y")
      emission_month_reference = emission_references.strftime("%m")
      emission_day_reference = emission_references.strftime("%d")
    print(document.id)
    b_igv = db.query(Breakdown).where(Breakdown.document_id == document.id).where(Breakdown.tax_id == 1).one_or_none()
    b_tax_bag = db.query(Breakdown).where(Breakdown.document_id == document.id ).where(Breakdown.tax_id == 4).one_or_none()
    tax_igv = 0
    tax_bag = 0
    if b_igv is not None:
      tax_igv = b_igv.amount
    if b_tax_bag is not None:
      tax_bag = b_tax_bag.amount
    today = (datetime.now()).strftime("%Y%m%d")
    hour_today = (datetime.now()).strftime("%H%M%S")
    cc = '3'
    subcc = get_subcenter(cod_serie)
    ammounts = []
    ammounts.append(document.net_amount)
    ammounts.append(document.total_amount)
    ammounts.append(tax_igv)
    ammounts.append(tax_bag)
    ammounts.append(0)
    ret = '0'.zfill(16)
    seller = '0001'
    city = '0002'
    zone = '000'
    office = '0001'
    ubi = '000'
    quantity = '000000000100000'
    pay_method = '0001'
    bank = '00'
    coin = '01'
    exchange = get_exchange(document.emission_date, 'V', db)
    canceled = ("N", "S")[document.canceled]
    for i in range(0, len(ctas)):
      row = {}
      row['TIPO DE COMPROBANTE (OBLIGATORIO)'] = rT
      row['CÓDIGO COMPROBANTE  (OBLIGATORIO)'] = rSerie
      row['NÚMERO DE DOCUMENTO'] = rnumber
      row['CUENTA CONTABLE   (OBLIGATORIO)'] = ctas[i]
      if document.document_type.code == '07':
        row['DÉBITO O CRÉDITO (OBLIGATORIO)'] = ('D', 'C')[i == 1]
      else:
        row['DÉBITO O CRÉDITO (OBLIGATORIO)'] = ('C', 'D')[i == 1]
      row['VALOR DE LA SECUENCIA   (OBLIGATORIO)'] = round(ammounts[i], 2)
      row['AÑO DEL DOCUMENTO'] = year_emission
      row['MES DEL DOCUMENTO'] = int(month_emission)
      row['DÍA DEL DOCUMENTO'] = int(day_emission)
      row['CÓDIGO DEL VENDEDOR'] = 1
      row['CÓDIGO DE LA CIUDAD'] = 1
      row['CÓDIGO DE LA ZONA'] = 1
      row['SECUENCIA'] = i + 1
      row['CENTRO DE COSTO'] = cc
      row['SUBCENTRO DE COSTO'] = subcc
      row['NIT'] = ruc
      row['SUCURSAL'] = sucursal
      row['DESCRIPCIÓN DE LA SECUENCIA'] = client_name
      row['NÚMERO DE CHEQUE'] = (0, round(ammounts[0],0))[i == 2]
      row['COMPROBANTE ANULADO'] = canceled
      row['CÓDIGO DEL MOTIVO DE DEVOLUCIÓN'] = 0
      row['FORMA DE PAGO'] = (0, 3)[i == 1]
      row['VALOR DEL CARGO 1 DE LA SECUENCIA'] = 0.0
      row['VALOR DEL CARGO 2 DE LA SECUENCIA'] = 0.0
      row['VALOR DEL DESCUENTO 1 DE LA SECUENCIA'] = 0.0
      row['VALOR DEL DESCUENTO 2 DE LA SECUENCIA'] = 0.0
      row['VALOR DEL DESCUENTO 3 DE LA SECUENCIA'] = 0.0
      row['PREFIJO DE ORDER REFERENCE'] = 0
      row['CONSECUTIVO DE ORDER REFERENCE'] = 0
      row['PREFIJO ORDEN DE ENTREGA'] = 0
      row['NÚMERO ORDEN DE ENTREGA'] = 0
      row['AÑO FECHA DE ORDEN DE ENTREGA'] = 0
      row['MES FECHA DE ORDEN DE ENTREGA'] = 0
      row['DÍA FECHA DE ORDEN DE ENTREGA'] = 0
      row['INGRESOS PARA TERCEROS'] = 0
      row['FECHA ACTUALIZACIÓN DEL DOCUMENTO'] = today
      row['HORA DE ACTUALIZACIÓN DEL DOCUMENTO'] = hour_today
      row['PREFIJO ORDEN DE ENTREGA2'] = 0
      row['NÚMERO ORDEN DE ENTREGA2'] = 0
      row['AÑO FECHA DE ORDEN DE ENTREGA2'] = 0
      row['MES FECHA DE ORDEN DE ENTREGA2'] = 0
      row['DÍA FECHA DE ORDEN DE ENTREGA2'] = 0
      row['PREFIJO ORDEN DE ENTREGA3'] = 0
      row['NÚMERO ORDEN DE ENTREGA3'] = 0
      row['AÑO FECHA DE ORDEN DE ENTREGA3'] = 0
      row['MES FECHA DE ORDEN DE ENTREGA3'] = 0
      row['DÍA FECHA DE ORDEN DE ENTREGA3'] = 0
      row['PREFIJO ORDEN DE ENTREGA4'] = 0
      row['NÚMERO ORDEN DE ENTREGA4'] = 0
      row['AÑO FECHA DE ORDEN DE ENTREGA4'] = 0
      row['MES FECHA DE ORDEN DE ENTREGA4'] = 0
      row['DÍA FECHA DE ORDEN DE ENTREGA4'] = 0
      row['PREFIJO ORDEN DE ENTREGA5'] = 0
      row['NÚMERO ORDEN DE ENTREGA5'] = 0
      row['AÑO FECHA DE ORDEN DE ENTREGA5'] = 0
      row['MES FECHA DE ORDEN DE ENTREGA5'] = 0
      row['DÍA FECHA DE ORDEN DE ENTREGA5'] = 0
      row['PORCENTAJE DEL IVA DE LA SECUENCIA'] = (0, igv * 100)[i == 0]
      row['VALOR DE IVA DE LA SECUENCIA'] = 0
      row['BASE DE RETENCIÓN'] = ""
      row['BASE PARA CUENTAS MARCADAS COMO RETEIVA'] = 0.0
      row['PORCENTAJE AIU'] = ""
      row['BASE IVA AIU'] = ""
      row['VALOR TOTAL IMPOCONSUMO DE LA SECUENCIA'] = 0.0
      row['LÍNEA PRODUCTO'] = ""
      row['GRUPO PRODUCTO'] = ""
      row['CÓDIGO PRODUCTO'] = ""
      row['CANTIDAD'] = 0
      row['CANTIDAD DOS'] = 0
      row['CÓDIGO DE LA BODEGA'] = 0
      if document.document_type.code != '07' and (i == 0 or i == 4):
        row['LÍNEA PRODUCTO'] = 21
        row['GRUPO PRODUCTO'] = 1
        row['CÓDIGO PRODUCTO'] = 1
        row['CANTIDAD'] = 1
        row['CÓDIGO DE LA BODEGA'] = 1
      row['CÓDIGO DE LA UBICACIÓN'] = 0
      row['CANTIDAD DE FACTOR DE CONVERSIÓN'] = 0
      row['OPERADOR DE FACTOR DE CONVERSIÓN'] = 0
      row['VALOR DEL FACTOR DE CONVERSIÓN'] = 0
      row['GRUPO ACTIVOS'] = ""
      row['CÓDIGO ACTIVO'] = ""
      row['ADICIÓN O MEJORA'] = 0
      row['VECES ADICIONALES A DEPRECIAR POR ADICIÓN O MEJORA'] = 0
      row['VECES A DEPRECIAR NIIF'] = 0
      row['NÚMERO DEL DOCUMENTO DEL PROVEEDOR'] = 0
      row['PREFIJO DEL DOCUMENTO DEL PROVEEDOR'] = ""
      row['AÑO DOCUMENTO DEL PROVEEDOR'] = ""
      row['MES DOCUMENTO DEL PROVEEDOR'] = ""
      row['DÍA DOCUMENTO DEL PROVEEDOR'] = ""
      row['TIPO DOCUMENTO DE PEDIDO'] = ""
      row['CÓDIGO COMPROBANTE DE PEDIDO'] = 0
      row['NÚMERO DE COMPROBANTE PEDIDO'] = 0
      row['SECUENCIA DE PEDIDO'] = 0
      row['CÓDIGO DE LA MONEDA'] = 1
      row['TASA DE CAMBIO'] = exchange.value
      row['VALOR DE LA SECUENCIA EN EXTRANJERA'] = ammounts[i] / exchange.value
      row['TIPO DE MONEDA ELABORACIÓN'] = 0
      row['TIPO Y COMPROBANTE CRUCE'] = (serie_references_siigo, "0-000")[i == 0]
      row['NÚMERO DE DOCUMENTO CRUCE'] = ("0", number_reference )[i == 1]
      row['NÚMERO DE VENCIMIENTO'] = ("0", 1)[i == 1]
      row['AÑO VENCIMIENTO DE DOCUMENTO CRUCE'] = ("", emission_year_reference)[i == 1]
      row['MES VENCIMIENTO DE DOCUMENTO CRUCE'] = ("", emission_month_reference)[i == 1]
      row['DÍA VENCIMIENTO DE DOCUMENTO CRUCE'] = ("", emission_day_reference)[i == 1]
      row['DOCUMENTO ORIGEN DADO POR EL PROVEEDOR'] = ""
      row['AÑO DE DETRACCIÓN'] = ""
      row['MES DE DETRACCIÓN'] = ""
      row['DÍA DE DETRACCIÓN'] = ""
      row['INDICADOR TIPO DE LETRA'] = ""
      row['ESTADO QUE SE ASIGNÓ A LA LETRA'] = ""
      row['CÓDIGO DEL MEDIO DE PAGO'] = 0
      row['ACTIVIDADES FLUJO DE EFECTIVO'] = 0
      row['NÚMERO DE DEPÓSITO'] = ""
      row['PORCENTAJE IGV DETRACCIÓN'] = 0
      row['BASE CÁLCULO DE DETRACCIÓN'] = 0
      row['VALOR IGV DE DETRACCIÓN'] = 0
      row['CÓDIGO TASA DE DETRACCIÓN'] = ""
      row['CÓDIGO TRANSACCIÓN BANCARIA'] = ""
      row['ÍTEM AFECTO O INAFECTO'] = ("N", "S")[i == 0]
      row['AÑO DE EMISIÓN'] = ""
      row['MES DE EMISIÓN'] = ""
      row['DÍA DE EMISIÓN'] = ""
      row['NÚMERO DE DOCUMENTO ORIGINAL  O PREIMPRESO'] = 0
      row['CÓDIGO SECUENCIA DE LA TRANSACCIÓN'] = 0
      row['TIPO DE OPERACIÓN'] = 0
      row['TIPO ORIGINAL'] = ""
      row['SERIE ORIGINAL'] = ""
      row['AÑO FECHA ORIGINAL'] = ""
      row['MES FECHA ORIGINAL'] = ""
      row['DIA FECHA ORIGINAL'] = ""
      row['NÚMERO DE BULTOS'] = 0
      row['UNIDAD DE MEDIDA PESO BRUTO'] = ""
      row['DOCUMENTO RELACIONADO'] = ""
      row['CÓDIGO DAM'] = ""
      row['CÓDIGO TRANSPORTISTA'] = 0
      row['CÓDIGO DE MOTIVO DE TRASLADO'] = 0
      row['FECHA DE INICIO DEL TRASLADO'] = 0
      row['NÚMERO DOCUMENTO DE IMPORTACIÓN'] = ""
      row['INCISO APLICABLE DEL ARTÍCULO 33'] = ""
      row['DESCRIPCIÓN DE COMENTARIOS'] = ""
      row['INCONTERM'] = ""
      row['DESCRIPCIÓN EXPORTACIÓN'] = ""
      row['MEDIO DE TRANSPORTE'] = ""
      row['PAÍS DE ORIGEN'] = 0
      row['CIUDAD DE ORIGEN'] = 0
      row['PAIS DESTINO'] = 0
      row['CIUDAD DESTINO'] = 0
      row['PESO NETO'] = 0
      row['PESO BRUTO'] = 0
      row['UNIDAD DE MEDIDA NETO'] = ""
      row['UNIDAD DE MEDIDA BRUTO'] = ""
      row['CONCEPTO FACTURACION EN BLOQUE'] = 0
      row['DATOS ESTABLEC. (L=LOCAL O=OFICINA)'] = ""
      row['NÚMERO ESTABLECIMIENTO'] = 0
      row['08976-DESCRIPCIÓN DEL MOTIVO O SUSTENTO'] = ""
      row['08950-TIPO DOCUMENTO EMISOR ANTICIPO1'] = ""
      row['08951-IDENTIFICACIÓN DEL EMISOR ANTICIPO1'] = ""
      row['08952-VALOR ANTICIPO1'] = ""
      row['08953-TIPO DOCUMENTO ANTICIPO1'] = ""
      row['08954-SERIE Y NÚMERO DOCUMENTO ANTICIPO1'] = ""
      row['08955-TIPO DOCUMENTO EMISOR ANTICIPO2'] = ""
      row['08956-IDENTIFICACIÓN DEL EMISOR ANTICIPO2'] = ""
      row['08957-VALOR ANTICIPO2'] = ""
      row['08958-TIPO DOCUMENTO ANTICIPO2'] = ""
      row['08959-SERIE Y NÚMERO DOCUMENTO ANTICIPO2'] = ""
      row['08960-TIPO DOCUMENTO EMISOR ANTICIPO3'] = ""
      row['08961-IDENTIFICACIÓN DEL EMISOR ANTICIPO3'] = ""
      row['08962-VALOR ANTICIPO3'] = ""
      row['08963-TIPO DOCUMENTO ANTICIPO3'] = ""
      row['08964-SERIE Y NÚMERO DOCUMENTO ANTICIPO3'] = ""
      row['08965-TIPO DOCUMENTO EMISOR ANTICIPO4'] = ""
      row['08966-IDENTIFICACIÓN DEL EMISOR ANTICIPO4'] = ""
      row['08967-VALOR ANTICIPO4'] = ""
      row['08968-TIPO DOCUMENTO ANTICIPO4'] = ""
      row['08969-SERIE Y NÚMERO DOCUMENTO ANTICIPO4'] = ""
      row['08970-TIPO DOCUMENTO EMISOR ANTICIPO5'] = ""
      row['08971-IDENTIFICACIÓN DEL EMISOR ANTICIPO5'] = ""
      row['08972-VALOR ANTICIPO5'] = ""
      row['08973-TIPO DOCUMENTO ANTICIPO5'] = ""
      row['08974-SERIE Y NÚMERO DOCUMENTO ANTICIPO5'] = ""
      row['08992-VALOR DEL ANTICIPO1 + IGV'] = ""
      row['08993-VALOR DEL ANTICIPO2 + IGV'] = ""
      row['08994-VALOR DEL ANTICIPO3 + IGV'] = ""
      row['08995-VALOR DEL ANTICIPO4 + IGV'] = ""
      row['08996-VALOR DEL ANTICIPO5 + IGV'] = ""
      row['08975-REVALUADO CON EFECTO TRIBUTARIO (S/N)'] = ""
      report.append(row)
  df = pd.DataFrame(data=report)
  wb = Workbook()
  ws = wb.active
  
  ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=180)
  ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=180)
  ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=180)
  ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=180)
  ws['A1'] =  'R & D CORPORACION SAC'
  a1 = ws['A1']
  b1 = ws['B1']
  c1 = ws['C1']
  d1 = ws['D1']
  ft = Font(name="Verdana", size=10, color="000000", bold=True)
  fill = PatternFill(patternType='solid', fgColor="ff99ccff")
  a1.font = ft
  b1.font = ft
  c1.font = ft
  d1.font = ft

  a1.fill = fill
  b1.fill = fill
  c1.fill = fill
  d1.fill = fill
 
  for r in dataframe_to_rows(df, index=False, header=True):
    ws.append(r)
  ws.cell(row=5, column=180).font = ft
  ws.cell(row=5, column=180).fill = fill
  wb.save("Asiento_contable_v2.xlsx")
  #df.to_excel('Asiento_contable.xlsx', index=False)
  return report
