-- Reporte de cancelación (asiento contable de conciliación Niubiz) — versión optimizada.
--
-- Cambios respecto a la versión original:
--   1. Fechas parametrizadas (:date_from, :date_to, :niubiz_date_from, :niubiz_date_to)
--      en vez de rangos de fecha fijos ("20260901", "20260815", ...).
--   2. Las dos subconsultas correlacionadas (tipo de cambio en `exchanges` y
--      serie SIIGO en `approvals`), que antes se ejecutaban una vez POR FILA,
--      se reemplazan por LEFT JOIN (una sola pasada, resuelto por el optimizador
--      con un join normal en vez de N subconsultas).
--   3. Se elimina el DISTINCT final: `payment_source_match` tiene una
--      restricción UNIQUE sobre `id_payment` (uq_match_payment) y los pagos
--      se agrupan por documento, por lo que el grano (una fila por documento)
--      ya es único; el DISTINCT era trabajo innecesario para el motor.
--   4. Se recortan las columnas del layout plano de SIIGO (NIT, cuentas,
--      descripciones, ~185 columnas en total) que eran constantes/derivadas:
--      esa lógica y el armado de las filas de resumen (débito) y detalle
--      (crédito) se movieron a Python (routers/bills.py), que además genera
--      el archivo Excel. Aquí solo se devuelven los datos reales necesarios
--      para esa capa (documento, monto, tipo de cambio, referencia SIIGO).
--      Esto además reduce drásticamente el tamaño del resultado que viaja
--      desde MySQL (antes ~185 columnas, muchas de ancho fijo con padding de
--      espacios, por cada fila).
--   5. Se filtra psm.canceled = 0: el reporte solo incluye los matches
--      Niubiz aún PENDIENTES de confirmar (no los ya confirmados vía
--      POST /bills/cancellation_book/confirm).
--   6. Se filtra payments.inactive = 0: solo se consideran pagos activos
--      (un pago inactivo/anulado en Bsale no debe generar asiento contable).
--   7. El importe del asiento es la suma de payments.amount de los pagos
--      Niubiz conciliados de cada documento (niubiz_amount), no
--      documents.total_amount. El resultado pasa a ser una fila por documento.
--   8. Se agregan los pagos EFECTIVO (payment_types.name = 'EFECTIVO'): no
--      tienen otra fuente con la que cruzar, así que se toman directamente de
--      payments (activos, mismo rango de recordDate) y se suman por
--      documento. La columna payment_kind ('NIUBIZ' / 'EFECTIVO') indica el
--      origen y `amount` el importe del asiento; un documento pagado con
--      ambos medios devuelve una fila por cada uno.
--
-- Índices recomendados para que este query escale bien:
--   documents(emission_date)
--   payments(recordDate), payments(id_payment_type)
--   payment_source_match(id_operacion)  [ya es parte de un UNIQUE]
--   approvals(bsale)
--   exchanges(day, type)
--   operaciones_niubiz: la condición STR_TO_DATE(fecha_y_hora_operacion, ...)
--     no puede usar índice al aplicar una función sobre la columna. Si el
--     volumen de operaciones_niubiz crece, conviene agregar una columna
--     generada `operation_datetime DATETIME GENERATED ALWAYS AS
--     (STR_TO_DATE(REPLACE(fecha_y_hora_operacion, '/', '-'), '%d-%m-%Y %H:%i')) STORED` con
--     índice, y filtrar por esa columna en vez de recalcularla cada vez.
--
-- Parámetros esperados (bind params, ver load_cancellation_entry_matches en
-- routers/bills.py):
--   :date_from, :date_to                 rango de emission_date de los documentos
--   :niubiz_date_from, :niubiz_date_to    rango (más amplio) para operaciones
--                                         Niubiz y pagos, ya que la fecha de
--                                         depósito/registro puede no coincidir
--                                         exactamente con la fecha de emisión

WITH filtered_documents AS (
    SELECT
        d.id                                    AS id_document,
        d.emission_date,
        d.expiration_date,
        d.serial_number,
        dt.name                                 AS document_type_name,
        FORMAT(IFNULL(c.code, 99999999), 0)     AS nit
    FROM documents d
    INNER JOIN document_types dt ON dt.id = d.id_document_type
    LEFT JOIN clients c           ON c.id = d.id_client
    WHERE d.emission_date BETWEEN :date_from AND :date_to
),
filtered_operations_niubiz AS (
    SELECT
        id_operacion,
        n_lote,
        STR_TO_DATE(REPLACE(fecha_y_hora_operacion, '/', '-'), '%d-%m-%Y %H:%i') AS operation_datetime
    FROM operaciones_niubiz
    -- Niubiz envía la fecha como 'dd-mm-yyyy HH:MM' o 'dd/mm/yyyy HH:MM':
    -- se normaliza '/' → '-' para admitir ambos formatos.
    WHERE STR_TO_DATE(REPLACE(fecha_y_hora_operacion, '/', '-'), '%d-%m-%Y %H:%i')
          BETWEEN :niubiz_date_from AND :niubiz_date_to
),
filtered_payments_niubiz AS (
    SELECT p.id AS id_payment, p.id_document, p.amount
    FROM payments p
    INNER JOIN payment_types pt ON pt.id = p.id_payment_type
    WHERE p.recordDate BETWEEN :niubiz_date_from AND :niubiz_date_to
      AND pt.name LIKE '%niubiz%'
      AND p.inactive = 0
),
-- Suma por documento de SOLO los pagos Niubiz conciliados y pendientes. Ese
-- es el importe del asiento (no documents.total_amount): un documento pagado
-- en parte con otro medio, o con varios pagos Niubiz, debe cancelarse por lo
-- realmente cobrado vía Niubiz. payment_source_match.id_payment es UNIQUE, así
-- que cada pago se suma una sola vez.
niubiz_amount_by_document AS (
    SELECT
        fpn.id_document,
        SUM(fpn.amount)  AS niubiz_amount,
        MAX(fon.n_lote)  AS n_lote
    FROM filtered_operations_niubiz fon
    INNER JOIN payment_source_match psm     ON psm.id_operacion = fon.id_operacion
                                            AND psm.canceled = 0
    INNER JOIN filtered_payments_niubiz fpn ON fpn.id_payment   = psm.id_payment
    GROUP BY fpn.id_document
),
-- EFECTIVO: sin fuente externa con la que conciliar, se suman directamente
-- los pagos activos de cada documento.
cash_amount_by_document AS (
    SELECT
        p.id_document,
        SUM(p.amount) AS cash_amount
    FROM payments p
    INNER JOIN payment_types pt ON pt.id = p.id_payment_type
    WHERE p.recordDate BETWEEN :niubiz_date_from AND :niubiz_date_to
      AND pt.name = 'EFECTIVO'
      AND p.inactive = 0
    GROUP BY p.id_document
),
amount_by_document AS (
    SELECT 'NIUBIZ' AS payment_kind, id_document, niubiz_amount AS amount, n_lote
    FROM niubiz_amount_by_document
    UNION ALL
    SELECT 'EFECTIVO' AS payment_kind, id_document, cash_amount AS amount, NULL AS n_lote
    FROM cash_amount_by_document
)
-- Grano: una fila por documento y medio de pago (NIUBIZ conciliado / EFECTIVO).
SELECT
    abd.payment_kind,
    fd.id_document,
    fd.emission_date,
    fd.expiration_date,
    fd.serial_number,
    abd.amount,
    fd.document_type_name,
    fd.nit,
    abd.n_lote,
    a.siigo  AS serial_number_siigo,
    ex.value AS exchange_rate
FROM amount_by_document abd
INNER JOIN filtered_documents fd ON fd.id_document = abd.id_document
LEFT JOIN approvals a  ON a.bsale = SUBSTRING(fd.serial_number, 1, 4)
LEFT JOIN exchanges ex ON ex.day = fd.emission_date AND ex.type = 'V'
ORDER BY abd.payment_kind, fd.document_type_name, fd.emission_date, fd.serial_number;
