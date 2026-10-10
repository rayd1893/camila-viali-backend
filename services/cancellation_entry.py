"""Generacion del asiento contable de cancelacion (conciliacion Niubiz) en formato SIIGO.

Este modulo reemplaza la logica que antes vivia completa en
``queries/repote_cancelacion.sql``. La consulta SQL (ver
``queries/repote_cancelacion.sql``, ya optimizada: sin subconsultas
correlacionadas y con fechas parametrizadas) ahora solo devuelve los datos
reales de cada pago Niubiz conciliado. Todo lo demas -resolucion de tienda,
armado de la fila de resumen (debito) y de detalle (credito), numeracion
correlativa y las ~185 columnas fijas que exige el layout de importacion de
SIIGO- se calcula aqui, en Python, donde es mas facil de leer, probar y
mantener que dentro de un SELECT gigante.

``CANCELLATION_ENTRY_TEMPLATE`` fue generado automaticamente a partir de la
version original de la consulta (para no transcribir a mano el padding de
espacios de las columnas de texto fijo). Las columnas marcadas con ``None``
son las que dependen de cada fila real y se completan en ``build_siigo_row``;
si alguna quedara sin asignar, ``build_siigo_row`` lanza un error en vez de
exportar un Excel con columnas vacias por accidente.

El ``NÚMERO DE DOCUMENTO`` (folio) ya NO se recalcula en memoria a partir de
lo que esté pendiente en cada corrida (eso hacía que un folio ya enviado a
SIIGO pudiera repetirse en una corrida posterior). Se persiste en la tabla
``cancellation_entry_folio`` (ver ``models/cancellation_entry_folio.py``),
compartida con los libros creados a mano vía
``POST /bills/cancellation_entry/folios``, de forma que el correlativo por
tienda+mes nunca se repite ni deja huecos sin importar cuántas veces se
regenere el reporte o en qué orden se registren los folios manuales.
"""

from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import text, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.cancellation_entry_folio import CancellationEntryFolio

_SQL_PATH = Path(__file__).resolve().parent.parent / "queries" / "repote_cancelacion.sql"
CANCELLATION_ENTRY_QUERY = text(_SQL_PATH.read_text(encoding="utf-8"))

# Máximo de reintentos al asignar un folio automático si dos requests chocan
# por el UNIQUE(serial_number_report, year_month, sequence_number).
MAX_FOLIO_ASSIGNMENT_ATTEMPTS = 5

# Mapeo tienda (document_type_name) -> (codigo de comprobante SIIGO, etiqueta
# para la descripcion del lote). Unica fuente de verdad: en la consulta
# original este mismo mapeo estaba duplicado en dos CASE WHEN distintos (uno
# para el codigo, otro para la etiqueta), que habia que mantener sincronizados
# a mano.
STORE_CODE_MAP: list[tuple[str, str, str]] = [
    ("PLAZA NORTE", "L-14", "PLAZA NORTE"),
    ("POLO",        "L-17", "EL POLO"),
    ("CHACARILLA",  "L-19", "CHACARILLA"),
    ("SAN MIGUEL",  "L-20", "SAN MIGUEL"),
    ("SALAVERRY",   "L-21", "SALAVERRY"),
    ("PRIMAVERA",   "L-22", "PRIMAVERA"),
    ("TRUJILLO",    "L-23", "TRUJILLO"),
    ("A4",          "L-10", "ECOMMERCE"),
]
# AFFARI (ningun token de STORE_CODE_MAP coincide) comparte el mismo codigo de
# comprobante L-10 y la misma etiqueta que A4/ECOMMERCE: ambos caen en el
# mismo correlativo de folios por mes y en la misma descripcion de lote
# ("LOTE XXXX NIUBIZ ECOMMERCE").
DEFAULT_STORE_CODE = "L-10"
DEFAULT_STORE_LABEL = "ECOMMERCE"

NIUBIZ_SUMMARY_NIT = "20341198217"
CREDIT_ACCOUNT = "1201020100"
DEBIT_ACCOUNT = "1602090100"
CREDIT_SEQUENCE_DESCRIPTION = "FT BL Y OTROS COMP X COB EN CARTERA MN"

# Caso especial AFFARI/ECOMMERCE: a diferencia de las tiendas fisicas (que
# siempre tienen un unico subcentro), bajo L-10 caen documentos con distintos
# codigos de serie (y por lo tanto distintos subcentros, ej. 1 y 15). El
# resumen (debito) debe ser UNA sola fila por fecha que sume todos esos
# subcentros, con un subcentro fijo -no una fila de resumen por subcentro-.
# Los detalles (credito) si conservan el subcentro real de cada documento.
COMBINED_SUMMARY_STORE_CODE = "L-10"
COMBINED_SUMMARY_SUBCENTER = 1


def resolve_store(document_type_name):
    """Devuelve (codigo de comprobante, etiqueta de tienda) para un tipo de documento."""
    name = (document_type_name or "").upper()
    for token, code, label in STORE_CODE_MAP:
        if token in name:
            return code, label
    return DEFAULT_STORE_CODE, DEFAULT_STORE_LABEL


def load_cancellation_entry_matches(db, date_from, date_to, niubiz_lookback_days=20, niubiz_lookahead_days=10):
    """Ejecuta la consulta optimizada y devuelve una fila por pago Niubiz conciliado.

    ``niubiz_lookback_days``/``niubiz_lookahead_days`` amplian el rango de
    busqueda de operaciones Niubiz y pagos respecto al rango de emision de
    documentos, porque el deposito/registro del pago puede quedar unos dias
    antes o despues de la fecha de emision del documento (igual que hacia la
    consulta original con sus fechas fijas).
    """
    niubiz_date_from = date_from - timedelta(days=niubiz_lookback_days)
    niubiz_date_to = date_to + timedelta(days=niubiz_lookahead_days)

    rows = db.execute(
        CANCELLATION_ENTRY_QUERY,
        {
            "date_from": date_from,
            "date_to": date_to,
            "niubiz_date_from": niubiz_date_from,
            "niubiz_date_to": niubiz_date_to,
        },
    ).mappings().all()

    return [dict(row) for row in rows]


def _split_serial_number(serial_number):
    cod_serie, document_number = serial_number.split("-")
    return cod_serie, document_number


def _subcenter_from_serial(cod_serie):
    return int(cod_serie[-2:])


def build_cancellation_entry_rows(matches):
    """Construye las filas de detalle (credito, una por documento) y de
    resumen (debito, una por tienda+dia), igual que hacian las CTE
    ``match_niubiz``/``agrup_match_niubiz``/``report`` de la consulta original.
    """
    detail_rows = []
    for match in matches:
        cod_serie, document_number = _split_serial_number(match["serial_number"])
        store_code, store_label = resolve_store(match["document_type_name"])
        detail_rows.append({
            "serial_number_report": store_code,
            "store_label": store_label,
            "subcenter": _subcenter_from_serial(cod_serie),
            "emission_date": match["emission_date"],
            "expiration_date": match["expiration_date"],
            "number_account": CREDIT_ACCOUNT,
            "credit_or_debit": "C",
            "total_amount": float(match["total_amount"]),
            "nit": match["nit"],
            "sequence_description": CREDIT_SEQUENCE_DESCRIPTION,
            "serial_number_siigo": match.get("serial_number_siigo") or "",
            "document_number": document_number,
            "exchange_rate": float(match["exchange_rate"]) if match.get("exchange_rate") else None,
            "n_lote": match.get("n_lote"),
        })

    groups = {}
    for row in detail_rows:
        if row["serial_number_report"] == COMBINED_SUMMARY_STORE_CODE:
            # AFFARI/ECOMMERCE (L-10): un solo resumen por fecha que suma TODOS
            # los subcentros (1, 15, ...) en una sola fila débito, con
            # subcentro fijo. Los detalles mantienen su subcentro real.
            key = (row["emission_date"], row["serial_number_report"])
            group_subcenter = COMBINED_SUMMARY_SUBCENTER
        else:
            key = (row["emission_date"], row["serial_number_report"], row["subcenter"])
            group_subcenter = row["subcenter"]
        group = groups.setdefault(key, {
            "serial_number_report": row["serial_number_report"],
            "store_label": row["store_label"],
            "subcenter": group_subcenter,
            "emission_date": row["emission_date"],
            "expiration_date": None,
            "number_account": DEBIT_ACCOUNT,
            "credit_or_debit": "D",
            "total_amount": 0.0,
            "nit": NIUBIZ_SUMMARY_NIT,
            "serial_number_siigo": "",
            "document_number": "0",
            "exchange_rate": row["exchange_rate"],
            "max_n_lote": None,
        })
        group["total_amount"] += row["total_amount"]
        if row["n_lote"] is not None:
            group["max_n_lote"] = (
                row["n_lote"] if group["max_n_lote"] is None else max(group["max_n_lote"], row["n_lote"])
            )

    summary_rows = []
    for group in groups.values():
        lote_suffix = str(group["max_n_lote"])[-4:] if group["max_n_lote"] is not None else "0000"
        summary_row = dict(group)
        summary_row["sequence_description"] = "LOTE {} NIUBIZ {}".format(lote_suffix, group["store_label"])
        summary_row.pop("max_n_lote", None)
        summary_rows.append(summary_row)

    return summary_rows + detail_rows


def _next_sequence_number(db: Session, serial_number_report: str, year_month: str) -> int:
    last = db.query(func.max(CancellationEntryFolio.sequence_number)).filter(
        CancellationEntryFolio.serial_number_report == serial_number_report,
        CancellationEntryFolio.year_month == year_month,
    ).scalar()
    return (last or 0) + 1


def get_or_create_document_number(db: Session, serial_number_report: str, emission_date: date) -> str:
    """Devuelve el folio (``NÚMERO DE DOCUMENTO``) para (tienda, fecha de
    emisión), reutilizando ``cancellation_entry_folio`` si ya se asignó uno
    (por una corrida automática previa o por un libro manual registrado vía
    ``POST /bills/cancellation_entry/folios``), o reservando el siguiente
    correlativo disponible para ese mes si es la primera vez que se ve esa
    fecha. El correlativo nunca tiene huecos ni se repite, porque automático
    y manual comparten el mismo contador (``MAX(sequence_number)`` sobre la
    misma tabla) en vez de numerar cada uno por su cuenta.
    """
    year_month = emission_date.strftime("%y%m")

    existing = db.query(CancellationEntryFolio).filter(
        CancellationEntryFolio.serial_number_report == serial_number_report,
        CancellationEntryFolio.emission_date == emission_date,
    ).one_or_none()
    if existing is not None:
        return existing.document_number

    for _ in range(MAX_FOLIO_ASSIGNMENT_ATTEMPTS):
        sequence_number = _next_sequence_number(db, serial_number_report, year_month)
        document_number = f"{year_month}{str(sequence_number).zfill(3)}"
        folio = CancellationEntryFolio(
            serial_number_report=serial_number_report,
            year_month=year_month,
            sequence_number=sequence_number,
            document_number=document_number,
            emission_date=emission_date,
            source="auto",
            note=None,
            created_at=datetime.now(),
        )
        db.add(folio)
        try:
            db.commit()
        except IntegrityError:
            # Otro request reservó el mismo sequence_number justo antes
            # (UNIQUE serial_number_report+year_month+sequence_number):
            # se descarta el intento y se vuelve a calcular el siguiente.
            db.rollback()
            continue
        return document_number

    raise RuntimeError(
        f"No se pudo asignar folio para {serial_number_report} {year_month} "
        f"tras {MAX_FOLIO_ASSIGNMENT_ATTEMPTS} intentos "
        "(posible alta concurrencia sobre cancellation_entry_folio)."
    )


def assign_document_numbers(db: Session, rows: list[dict]) -> list[dict]:
    """Completa ``document_sequence_number`` en cada fila usando el folio
    persistido en ``cancellation_entry_folio`` (ver ``get_or_create_document_number``).
    Una sola consulta/inserción por (tienda, fecha) distinta, aunque esa
    combinación aparezca en varias filas (resumen + detalle comparten fecha).
    """
    cache: dict[tuple, str] = {}
    for row in rows:
        key = (row["serial_number_report"], row["emission_date"])
        if key not in cache:
            cache[key] = get_or_create_document_number(db, *key)
        row["document_sequence_number"] = cache[key]
    return rows


def assign_row_sequence(rows: list[dict]) -> list[dict]:
    """Calcula ``SECUENCIA`` (equivalente a ``ROW_NUMBER() OVER (PARTITION BY
    serial_number_report, emission_date ORDER BY document_number)``): el
    orden de las filas dentro de un mismo (tienda, fecha) en el Excel final.
    No depende de folios persistidos, solo del orden relativo dentro de la
    corrida actual.
    """
    if not rows:
        return rows

    rows_sorted = sorted(
        rows,
        key=lambda r: (r["serial_number_report"], r["emission_date"], int(r["document_number"])),
    )
    counters: dict[tuple, int] = {}
    for row in rows_sorted:
        key = (row["serial_number_report"], row["emission_date"])
        counters[key] = counters.get(key, 0) + 1
        row["sequence"] = counters[key]

    return rows_sorted


CANCELLATION_ENTRY_TEMPLATE = {
    'TIPO DE COMPROBANTE (OBLIGATORIO)': None,  # calculado por fila, ver build_cancellation_entry_row
    'CÓDIGO COMPROBANTE  (OBLIGATORIO)': None,  # calculado por fila, ver build_cancellation_entry_row
    'NÚMERO DE DOCUMENTO': None,  # calculado por fila, ver build_cancellation_entry_row
    'CUENTA CONTABLE   (OBLIGATORIO)': None,  # calculado por fila, ver build_cancellation_entry_row
    'DÉBITO O CRÉDITO (OBLIGATORIO)': None,  # calculado por fila, ver build_cancellation_entry_row
    'VALOR DE LA SECUENCIA   (OBLIGATORIO)': None,  # calculado por fila, ver build_cancellation_entry_row
    'AÑO DEL DOCUMENTO': None,  # calculado por fila, ver build_cancellation_entry_row
    'MES DEL DOCUMENTO': None,  # calculado por fila, ver build_cancellation_entry_row
    'DÍA DEL DOCUMENTO': None,  # calculado por fila, ver build_cancellation_entry_row
    'CÓDIGO DEL VENDEDOR': 1,
    'CÓDIGO DE LA CIUDAD': 1,
    'CÓDIGO DE LA ZONA': 0,
    'SECUENCIA': None,  # calculado por fila, ver build_cancellation_entry_row
    'CENTRO DE COSTO': 3,
    'SUBCENTRO DE COSTO': None,  # calculado por fila, ver build_cancellation_entry_row
    'NIT': None,  # calculado por fila, ver build_cancellation_entry_row
    'SUCURSAL': '0',
    'DESCRIPCIÓN DE LA SECUENCIA': None,  # calculado por fila, ver build_cancellation_entry_row
    'NÚMERO DE CHEQUE': '0',
    'COMPROBANTE ANULADO': 'N',
    'CÓDIGO DEL MOTIVO DE DEVOLUCIÓN': '0',
    'FORMA DE PAGO': '0',
    'VALOR DEL CARGO 1 DE LA SECUENCIA': '0.00',
    'VALOR DEL CARGO 2 DE LA SECUENCIA': '0.00',
    'VALOR DEL DESCUENTO 1 DE LA SECUENCIA': '0.00',
    'VALOR DEL DESCUENTO 2 DE LA SECUENCIA': '0.00',
    'VALOR DEL DESCUENTO 3 DE LA SECUENCIA': '0.00',
    'PREFIJO DE ORDER REFERENCE': '0',
    'CONSECUTIVO DE ORDER REFERENCE': '0',
    'PREFIJO ORDEN DE ENTREGA': '0',
    'NÚMERO ORDEN DE ENTREGA': '0',
    'AÑO FECHA DE ORDEN DE ENTREGA': '0',
    'MES FECHA DE ORDEN DE ENTREGA': '0',
    'DÍA FECHA DE ORDEN DE ENTREGA': '0',
    'INGRESOS PARA TERCEROS': '',
    'FECHA ACTUALIZACIÓN DEL DOCUMENTO': None,  # calculado por fila, ver build_cancellation_entry_row
    'HORA DE ACTUALIZACIÓN DEL DOCUMENTO': None,  # calculado por fila, ver build_cancellation_entry_row
    'PREFIJO ORDEN DE ENTREGA2': '0',
    'NÚMERO ORDEN DE ENTREGA2': '0',
    'AÑO FECHA DE ORDEN DE ENTREGA2': '0',
    'MES FECHA DE ORDEN DE ENTREGA2': '0',
    'DÍA FECHA DE ORDEN DE ENTREGA2': '0',
    'PREFIJO ORDEN DE ENTREGA3': '0',
    'NÚMERO ORDEN DE ENTREGA3': '0',
    'AÑO FECHA DE ORDEN DE ENTREGA3': '0',
    'MES FECHA DE ORDEN DE ENTREGA3': '0',
    'DÍA FECHA DE ORDEN DE ENTREGA3': '0',
    'PREFIJO ORDEN DE ENTREGA4': '0',
    'NÚMERO ORDEN DE ENTREGA4': '0',
    'AÑO FECHA DE ORDEN DE ENTREGA4': '0',
    'MES FECHA DE ORDEN DE ENTREGA4': '0',
    'DÍA FECHA DE ORDEN DE ENTREGA4': '0',
    'PREFIJO ORDEN DE ENTREGA5': '0',
    'NÚMERO ORDEN DE ENTREGA5': '0',
    'AÑO FECHA DE ORDEN DE ENTREGA5': '0',
    'MES FECHA DE ORDEN DE ENTREGA5': '0',
    'DÍA FECHA DE ORDEN DE ENTREGA5': '0',
    'PORCENTAJE DEL IVA DE LA SECUENCIA': '0.00',
    'VALOR DE IVA DE LA SECUENCIA': '0.00',
    'BASE DE RETENCIÓN': '',
    'BASE PARA CUENTAS MARCADAS COMO RETEIVA': '0.00',
    'PORCENTAJE AIU': '',
    'BASE IVA AIU': '',
    'VALOR TOTAL IMPOCONSUMO DE LA SECUENCIA': '0.00',
    'LÍNEA PRODUCTO': '',
    'GRUPO PRODUCTO': '',
    'CÓDIGO PRODUCTO': '',
    'CANTIDAD': '0.00000',
    'CANTIDAD DOS': '0.00000',
    'CÓDIGO DE LA BODEGA': '0',
    'CÓDIGO DE LA UBICACIÓN': '0',
    'CANTIDAD DE FACTOR DE CONVERSIÓN': '0.00000',
    'OPERADOR DE FACTOR DE CONVERSIÓN': '0',
    'VALOR DEL FACTOR DE CONVERSIÓN': '0.00000',
    'GRUPO ACTIVOS': '',
    'CÓDIGO ACTIVO': '',
    'ADICIÓN O MEJORA': '0',
    'VECES ADICIONALES A DEPRECIAR POR ADICIÓN O MEJORA': '0',
    'VECES A DEPRECIAR NIIF': '0',
    'NÚMERO DEL DOCUMENTO DEL PROVEEDOR': '2,764',
    'PREFIJO DEL DOCUMENTO DEL PROVEEDOR': '',
    'AÑO DOCUMENTO DEL PROVEEDOR': None,  # calculado por fila, ver build_cancellation_entry_row
    'MES DOCUMENTO DEL PROVEEDOR': None,  # calculado por fila, ver build_cancellation_entry_row
    'DÍA DOCUMENTO DEL PROVEEDOR': None,  # calculado por fila, ver build_cancellation_entry_row
    'TIPO DOCUMENTO DE PEDIDO': '',
    'CÓDIGO COMPROBANTE DE PEDIDO': '0',
    'NÚMERO DE COMPROBANTE PEDIDO': '0',
    'SECUENCIA DE PEDIDO': '0',
    'CÓDIGO DE LA MONEDA': '1',
    'TASA DE CAMBIO': None,  # calculado por fila, ver build_cancellation_entry_row
    'VALOR DE LA SECUENCIA EN EXTRANJERA': None,  # calculado por fila, ver build_cancellation_entry_row
    'TIPO DE MONEDA ELABORACIÓN': '0',
    'TIPO Y COMPROBANTE CRUCE': None,  # calculado por fila, ver build_cancellation_entry_row
    'NÚMERO DE DOCUMENTO CRUCE': None,  # calculado por fila, ver build_cancellation_entry_row
    'NÚMERO DE VENCIMIENTO': None,  # calculado por fila, ver build_cancellation_entry_row
    'AÑO VENCIMIENTO DE DOCUMENTO CRUCE': None,  # calculado por fila, ver build_cancellation_entry_row
    'MES VENCIMIENTO DE DOCUMENTO CRUCE': None,  # calculado por fila, ver build_cancellation_entry_row
    'DÍA VENCIMIENTO DE DOCUMENTO CRUCE': None,  # calculado por fila, ver build_cancellation_entry_row
    'DOCUMENTO ORIGEN DADO POR EL PROVEEDOR': '2',
    'AÑO DE DETRACCIÓN': '',
    'MES DE DETRACCIÓN': '',
    'DÍA DE DETRACCIÓN': '',
    'INDICADOR TIPO DE LETRA': '',
    'ESTADO QUE SE ASIGNÓ A LA LETRA': '',
    'CÓDIGO DEL MEDIO DE PAGO': '0',
    'ACTIVIDADES FLUJO DE EFECTIVO': '0',
    'NÚMERO DE DEPÓSITO': '',
    'PORCENTAJE IGV DETRACCIÓN': '0.00',
    'BASE CÁLCULO DE DETRACCIÓN': '0.00',
    'VALOR IGV DE DETRACCIÓN': '0.00',
    'CÓDIGO TASA DE DETRACCIÓN': '',
    'CÓDIGO TRANSACCIÓN BANCARIA': '',
    'ÍTEM AFECTO O INAFECTO': ' ',
    'AÑO DE EMISIÓN': '    ',
    'MES DE EMISIÓN': '  ',
    'DÍA DE EMISIÓN': '  ',
    'NÚMERO DE DOCUMENTO ORIGINAL  O PREIMPRESO': '2764',
    'CÓDIGO SECUENCIA DE LA TRANSACCIÓN': '0',
    'TIPO DE OPERACIÓN': '0',
    'TIPO ORIGINAL': '   ',
    'SERIE ORIGINAL': '                    ',
    'AÑO FECHA ORIGINAL': '    ',
    'MES FECHA ORIGINAL': '  ',
    'DIA FECHA ORIGINAL': '  ',
    'NÚMERO DE BULTOS': '0',
    'UNIDAD DE MEDIDA PESO BRUTO': '   ',
    'DOCUMENTO RELACIONADO': '  ',
    'CÓDIGO DAM': '                       ',
    'CÓDIGO TRANSPORTISTA': '0',
    'CÓDIGO DE MOTIVO DE TRASLADO': '0',
    'FECHA DE INICIO DEL TRASLADO': None,  # calculado por fila, ver build_cancellation_entry_row
    'NÚMERO DOCUMENTO DE IMPORTACIÓN': '                    ',
    'INCISO APLICABLE DEL ARTÍCULO 33': ' ',
    'DESCRIPCIÓN DE COMENTARIOS': '                                                                                                                                                                                                                                    ',
    'DESCRIPCIÓN LARGA-001': '                                                            ',
    'DESCRIPCIÓN LARGA-002': '                                                            ',
    'DESCRIPCIÓN LARGA-003': '                                                            ',
    'DESCRIPCIÓN LARGA-004': '                                                            ',
    'DESCRIPCIÓN LARGA-005': '                                                            ',
    'INCONTERM': '          ',
    'DESCRIPCIÓN EXPORTACIÓN': '                                                  ',
    'MEDIO DE TRANSPORTE': '                                                  ',
    'PAÍS DE ORIGEN': '0',
    'CIUDAD DE ORIGEN': '0',
    'PAIS DESTINO': '0',
    'CIUDAD DESTINO': '0',
    'PESO NETO': '0.00',
    'PESO BRUTO': '0.00',
    'UNIDAD DE MEDIDA NETO': '          ',
    'UNIDAD DE MEDIDA BRUTO': '          ',
    'CONCEPTO FACTURACION EN BLOQUE': '0',
    'DATOS ESTABLEC. (L=LOCAL O=OFICINA)': ' ',
    'NÚMERO ESTABLECIMIENTO': '0',
    '08976-DESCRIPCIÓN DEL MOTIVO O SUSTENTO': '                                                                                                   ',
    '08950-TIPO DOCUMENTO EMISOR ANTICIPO1': ' ',
    '08951-IDENTIFICACIÓN DEL EMISOR ANTICIPO1': '                 ',
    '08952-VALOR ANTICIPO1': '                ',
    '08953-TIPO DOCUMENTO ANTICIPO1': '  ',
    '08954-SERIE Y NÚMERO DOCUMENTO ANTICIPO1': '                              ',
    '08955-TIPO DOCUMENTO EMISOR ANTICIPO2': ' ',
    '08956-IDENTIFICACIÓN DEL EMISOR ANTICIPO2': '                 ',
    '08957-VALOR ANTICIPO2': '                ',
    '08958-TIPO DOCUMENTO ANTICIPO2': '  ',
    '08959-SERIE Y NÚMERO DOCUMENTO ANTICIPO2': '                              ',
    '08960-TIPO DOCUMENTO EMISOR ANTICIPO3': ' ',
    '08961-IDENTIFICACIÓN DEL EMISOR ANTICIPO3': '                 ',
    '08962-VALOR ANTICIPO3': '                ',
    '08963-TIPO DOCUMENTO ANTICIPO3': '  ',
    '08964-SERIE Y NÚMERO DOCUMENTO ANTICIPO3': '                              ',
    '08965-TIPO DOCUMENTO EMISOR ANTICIPO4': ' ',
    '08966-IDENTIFICACIÓN DEL EMISOR ANTICIPO4': '                 ',
    '08967-VALOR ANTICIPO4': '                ',
    '08968-TIPO DOCUMENTO ANTICIPO4': '  ',
    '08969-SERIE Y NÚMERO DOCUMENTO ANTICIPO4': '                              ',
    '08970-TIPO DOCUMENTO EMISOR ANTICIPO5': ' ',
    '08971-IDENTIFICACIÓN DEL EMISOR ANTICIPO5': '                 ',
    '08972-VALOR ANTICIPO5': '                ',
    '08973-TIPO DOCUMENTO ANTICIPO5': '  ',
    '08974-SERIE Y NÚMERO DOCUMENTO ANTICIPO5': '                              ',
    '08992-VALOR DEL ANTICIPO1 + IGV': '                ',
    '08993-VALOR DEL ANTICIPO2 + IGV': '                ',
    '08994-VALOR DEL ANTICIPO3 + IGV': '                ',
    '08995-VALOR DEL ANTICIPO4 + IGV': '                ',
    '08996-VALOR DEL ANTICIPO5 + IGV': '                ',
    '08975-REVALUADO CON EFECTO TRIBUTARIO (S/N)': '',
}


def build_siigo_row(entry):
    """Combina la plantilla de columnas fijas de SIIGO con los valores reales de una fila."""
    row = dict(CANCELLATION_ENTRY_TEMPLATE)

    comprobante_tipo, comprobante_codigo = entry["serial_number_report"].split("-")
    emission_date = entry["emission_date"]
    expiration_date = entry.get("expiration_date")
    has_expiration = expiration_date is not None
    exchange_rate = entry.get("exchange_rate") or None
    total_amount = round(entry["total_amount"], 2)
    now = datetime.now()

    row["TIPO DE COMPROBANTE (OBLIGATORIO)"] = comprobante_tipo
    row["CÓDIGO COMPROBANTE  (OBLIGATORIO)"] = comprobante_codigo
    row["NÚMERO DE DOCUMENTO"] = entry["document_sequence_number"]
    row["CUENTA CONTABLE   (OBLIGATORIO)"] = entry["number_account"]
    row["DÉBITO O CRÉDITO (OBLIGATORIO)"] = entry["credit_or_debit"]
    row["VALOR DE LA SECUENCIA   (OBLIGATORIO)"] = total_amount
    row["AÑO DEL DOCUMENTO"] = emission_date.year
    row["MES DEL DOCUMENTO"] = emission_date.month
    row["DÍA DEL DOCUMENTO"] = emission_date.day
    row["SECUENCIA"] = entry["sequence"]
    row["SUBCENTRO DE COSTO"] = entry["subcenter"]
    row["NIT"] = entry["nit"]
    row["DESCRIPCIÓN DE LA SECUENCIA"] = entry["sequence_description"]
    row["FECHA ACTUALIZACIÓN DEL DOCUMENTO"] = now.strftime("%Y%m%d")
    row["HORA DE ACTUALIZACIÓN DEL DOCUMENTO"] = now.strftime("%H%M%S")
    row["AÑO DOCUMENTO DEL PROVEEDOR"] = emission_date.year
    row["MES DOCUMENTO DEL PROVEEDOR"] = emission_date.month
    row["DÍA DOCUMENTO DEL PROVEEDOR"] = emission_date.day
    row["TASA DE CAMBIO"] = round(exchange_rate, 5) if exchange_rate else ""
    row["VALOR DE LA SECUENCIA EN EXTRANJERA"] = (
        round(total_amount / exchange_rate, 5) if exchange_rate else ""
    )
    row["TIPO Y COMPROBANTE CRUCE"] = entry["serial_number_siigo"]
    row["NÚMERO DE DOCUMENTO CRUCE"] = entry["document_number"]
    row["NÚMERO DE VENCIMIENTO"] = 1 if has_expiration else 0
    row["AÑO VENCIMIENTO DE DOCUMENTO CRUCE"] = expiration_date.year if has_expiration else ""
    row["MES VENCIMIENTO DE DOCUMENTO CRUCE"] = expiration_date.month if has_expiration else ""
    row["DÍA VENCIMIENTO DE DOCUMENTO CRUCE"] = expiration_date.day if has_expiration else ""
    row["FECHA DE INICIO DEL TRASLADO"] = emission_date.strftime("%Y%m%d")

    missing = [key for key, value in row.items() if value is None]
    if missing:
        raise RuntimeError("Columnas SIIGO sin valor asignado en build_siigo_row: {}".format(missing))

    return row


def generate_cancellation_entry_rows(db, date_from, date_to, niubiz_lookback_days=20, niubiz_lookahead_days=10):
    """Orquesta todo el flujo: carga los matches, los agrupa/numera y los
    formatea al layout plano de SIIGO. Devuelve una lista de filas lista para
    volcar a un DataFrame/Excel."""
    matches = load_cancellation_entry_matches(
        db, date_from, date_to, niubiz_lookback_days, niubiz_lookahead_days
    )
    if not matches:
        return []

    entries = build_cancellation_entry_rows(matches)
    entries = assign_document_numbers(db, entries)
    entries = assign_row_sequence(entries)
    return [build_siigo_row(entry) for entry in entries]
