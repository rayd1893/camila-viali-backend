-- Cruce documentos / pagos / operaciones Niubiz — reporte de diagnóstico.
--
-- Para cada documento (excluyendo notas de crédito, dt.code != '09') en el
-- rango de emission_date indicado, muestra su pago y, si ya fue conciliado
-- (payment_source_match), la operación Niubiz correspondiente y el tipo de
-- match. Los LEFT JOIN hacen que los pagos aún sin conciliar también
-- aparezcan (con las columnas de Niubiz en NULL), para poder detectar a
-- simple vista qué quedó sin cruzar.
--
-- Parámetros esperados (bind params):
--   :date_from, :date_to   rango de documents.emission_date

SELECT
    d.id                        AS id_document,
    d.serial_number,
    d.emission_date,
    d.generation_date,
    d.total_amount,
    d.net_amount,
    d.tax_amount,
    dt.commercial_code,
    dt.code,
    dt.name                     AS document_type,
    p.recordDate                AS payment_date,
    p.createdAt                 AS fecha_hora_registro_pago,
    p.inactive,
    p.operationNumber           AS cod_auth_nro_voucher,
    p.amount                    AS payment_amount,
    pt.name                     AS payment_type,
    opn.id_operacion,
    opn.fecha_y_hora_operacion,
    opn.fecha_de_deposito,
    opn.cod_comercio,
    opn.codigo_de_autorizacion,
    opn.n_voucher,
    opn.n_lote,
    opn.importe_de_operacion,
    opn.monto_dcc,
    opn.suma_depositada,
    psm.match_type
FROM documents d
INNER JOIN document_types dt ON d.id_document_type = dt.id
INNER JOIN payments p        ON d.id = p.id_document
INNER JOIN payment_types pt  ON p.id_payment_type = pt.id
LEFT JOIN payment_source_match psm ON p.id = psm.id_payment
LEFT JOIN operaciones_niubiz opn   ON psm.id_operacion = opn.id_operacion
WHERE d.emission_date BETWEEN :date_from AND :date_to
  AND dt.code != '09'
ORDER BY d.emission_date, d.serial_number;
