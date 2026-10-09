WITH seq AS (
    SELECT 0 AS i UNION ALL SELECT 1 UNION ALL SELECT 2
    UNION ALL SELECT 3 UNION ALL SELECT 4
),
doc_base AS (
    SELECT
        psm.id                                               AS id_match,
        d.id                                AS document_id,
        dt.code                                              AS doc_type_code,
        dt.is_credit_note                   AS is_credit_note,
        SUBSTRING_INDEX(d.serial_number, '-', 1)             AS cod_serie,             -- p.ej. 'B001'
        SUBSTRING_INDEX(d.serial_number, '-',-1)             AS doc_number,            -- p.ej. '000123'
        ap.siigo                                             AS cod_serial_siigo,
        SUBSTRING_INDEX(ap.siigo, '-', 1)                    AS rT,                    -- TIPO DE COMPROBANTE
        SUBSTRING_INDEX(ap.siigo, '-',-1)                    AS rSerie,                -- CÓDIGO COMPROBANTE
        d.emission_date,
        d.total_amount,
        d.net_amount,
        d.canceled,
        CAST(RIGHT(SUBSTRING_INDEX(d.serial_number,'-',1), 2) AS UNSIGNED) AS subcc,
        COALESCE(cl.code, '99999999')                        AS ruc,
        COALESCE(UPPER(cl.company), 'CONSUMIDOR FINAL')      AS client_name,
        COALESCE(b_igv.amount, 0)                            AS tax_igv,
        COALESCE(b_bag.amount, 0)                            AS tax_bag,
		ex.value                                             AS tipo_cambio,
        COALESCE(ap_ref.siigo, ap.siigo)                                     AS serie_references_siigo,
        COALESCE(SUBSTRING_INDEX(ref_d.serial_number,'-',-1), SUBSTRING_INDEX(d.serial_number,'-',-1)) AS number_reference,
        COALESCE(YEAR(ref_d.emission_date),  YEAR(d.emission_date))         AS emission_year_reference,
        COALESCE(MONTH(ref_d.emission_date), MONTH(d.emission_date))        AS emission_month_reference,
        COALESCE(DAY(ref_d.emission_date),   DAY(d.emission_date))          AS emission_day_reference
    FROM payment_source_match psm
     INNER JOIN payments  p      ON psm.id_payment = p.id
    INNER JOIN documents d      ON d.id = p.id_document
    JOIN document_types dt      ON dt.id = d.id_document_type
    LEFT JOIN clients   cl      ON cl.id = d.id_client
    LEFT JOIN approvals ap      ON ap.bsale = SUBSTRING_INDEX(d.serial_number, '-', 1)
    LEFT JOIN breakdowns b_igv  ON b_igv.document_id = d.id AND b_igv.tax_id = 1
    LEFT JOIN breakdowns b_bag  ON b_bag.document_id = d.id AND b_bag.tax_id = 4
    LEFT JOIN exchanges  ex     ON ex.day = d.emission_date AND ex.type = 'V'
    LEFT JOIN `returns`  r      ON r.credit_note_id = d.id AND dt.is_credit_note = 1
    LEFT JOIN documents  ref_d  ON ref_d.id = r.reference_document_id
    LEFT JOIN approvals  ap_ref ON ap_ref.bsale = SUBSTRING_INDEX(ref_d.serial_number, '-', 1)
    WHERE psm.source   = 'NIUBIZ'
      AND psm.canceled = 0
      AND dt.code      <> '09'
)
SELECT
    db.rT                                                            AS `TIPO DE COMPROBANTE (OBLIGATORIO)`,
    db.rSerie                                                        AS `CÓDIGO COMPROBANTE  (OBLIGATORIO)`,
    db.doc_number                                                    AS `NÚMERO DE DOCUMENTO`,
    CASE s.i
        WHEN 0 THEN IF(db.doc_type_code = '07', '7401010100', '7002020101')
        WHEN 1 THEN '1201020100'
        WHEN 2 THEN '4001010100'
        WHEN 3 THEN '4001080900'
        WHEN 4 THEN '2101010101'
    END                                                               AS `CUENTA CONTABLE   (OBLIGATORIO)`,
    CASE
        WHEN db.doc_type_code = '07' THEN IF(s.i = 1, 'C', 'D')
        ELSE IF(s.i = 1, 'D', 'C')
    END                                                               AS `DÉBITO O CRÉDITO (OBLIGATORIO)`,
    ROUND(
        CASE s.i
            WHEN 0 THEN db.net_amount
            WHEN 1 THEN db.total_amount
            WHEN 2 THEN db.tax_igv
            WHEN 3 THEN db.tax_bag
            WHEN 4 THEN 0
        END, 2)                                                      AS `VALOR DE LA SECUENCIA   (OBLIGATORIO)`,
    YEAR(db.emission_date)                                           AS `AÑO DEL DOCUMENTO`,
    MONTH(db.emission_date)                                          AS `MES DEL DOCUMENTO`,
    DAY(db.emission_date)                                            AS `DÍA DEL DOCUMENTO`,
    '1'                                           					 AS `CÓDIGO DEL VENDEDOR`,
    '1'                                           					 AS `CÓDIGO DE LA CIUDAD`,
    '1'                                           					 AS `CÓDIGO DE LA ZONA`,
    s.i + 1                                                          AS `SECUENCIA`,
    '3'                                                               AS `CENTRO DE COSTO`,
    db.subcc                                                          AS `SUBCENTRO DE COSTO`,
    db.ruc                                                            AS `NIT`,
    '0'																AS `SUCURSAL`,
    db.client_name                                                   AS `DESCRIPCIÓN DE LA SECUENCIA`,
    IF(s.i = 2, ROUND(db.net_amount, 0), 0)                          AS `NÚMERO DE CHEQUE`,
    IF(db.canceled, 'S', 'N')                                        AS `COMPROBANTE ANULADO`,
    '0'																AS `CÓDIGO DEL MOTIVO DE DEVOLUCIÓN`,
    IF(s.i = 1, 3, 0)                                                AS `FORMA DE PAGO`,
    FORMAT(0, 2)													AS `VALOR DEL CARGO 1 DE LA SECUENCIA`,
    FORMAT(0, 2)													AS `VALOR DEL CARGO 2 DE LA SECUENCIA`,
    FORMAT(0, 2)													AS `VALOR DEL DESCUENTO 1 DE LA SECUENCIA`,
    FORMAT(0, 2)													AS `VALOR DEL DESCUENTO 2 DE LA SECUENCIA`,
    FORMAT(0, 2)													AS `VALOR DEL DESCUENTO 3 DE LA SECUENCIA`,
    '0'																AS `PREFIJO DE ORDER REFERENCE`,
    '0'																AS `CONSECUTIVO DE ORDER REFERENCE`,
    '0'																AS `PREFIJO ORDEN DE ENTREGA`,
    '0'																AS `NÚMERO ORDEN DE ENTREGA`,
    '0'																AS `AÑO FECHA DE ORDEN DE ENTREGA`,
    '0'																AS `MES FECHA DE ORDEN DE ENTREGA`,
    '0'																AS `DÍA FECHA DE ORDEN DE ENTREGA`,
    ''																AS `INGRESOS PARA TERCEROS`,
	DATE_FORMAT(NOW(), '%Y%m%d')                                     AS `FECHA ACTUALIZACIÓN DEL DOCUMENTO`,
    DATE_FORMAT(NOW(), '%H%i%s')                                     AS `HORA DE ACTUALIZACIÓN DEL DOCUMENTO`,
    '0'																AS `PREFIJO ORDEN DE ENTREGA2`,
    '0'																AS `NÚMERO ORDEN DE ENTREGA2`,
    '0'																AS `AÑO FECHA DE ORDEN DE ENTREGA2`,
    '0'																AS `MES FECHA DE ORDEN DE ENTREGA2`,
    '0'																AS `DÍA FECHA DE ORDEN DE ENTREGA2`,
    '0'																AS `PREFIJO ORDEN DE ENTREGA3`,
    '0'																AS `NÚMERO ORDEN DE ENTREGA3`,
    '0'																AS `AÑO FECHA DE ORDEN DE ENTREGA3`,
    '0'																AS `MES FECHA DE ORDEN DE ENTREGA3`,
    '0'																AS `DÍA FECHA DE ORDEN DE ENTREGA3`,
    '0'																AS `PREFIJO ORDEN DE ENTREGA4`,
    '0'																AS `NÚMERO ORDEN DE ENTREGA4`,
    '0'																AS `AÑO FECHA DE ORDEN DE ENTREGA4`,
    '0'																AS `MES FECHA DE ORDEN DE ENTREGA4`,
    '0'																AS `DÍA FECHA DE ORDEN DE ENTREGA4`,
    '0'																AS `PREFIJO ORDEN DE ENTREGA5`,
    '0'																AS `NÚMERO ORDEN DE ENTREGA5`,
    '0'																AS `AÑO FECHA DE ORDEN DE ENTREGA5`,
    '0'																AS `MES FECHA DE ORDEN DE ENTREGA5`,
    '0'																AS `DÍA FECHA DE ORDEN DE ENTREGA5`,
    IF(s.i = 0, 18, 0)                    AS  `PORCENTAJE DEL IVA DE LA SECUENCIA`,
    FORMAT(0, 2)													AS `VALOR DE IVA DE LA SECUENCIA`,
    ''																AS `BASE DE RETENCIÓN`,
    FORMAT(0, 2)													AS `BASE PARA CUENTAS MARCADAS COMO RETEIVA`,
    ''																AS `PORCENTAJE AIU`,
    ''																AS `BASE IVA AIU`,
    FORMAT(0, 2)													AS `VALOR TOTAL IMPOCONSUMO DE LA SECUENCIA`,
    IF(db.doc_type_code <> '07' AND s.i IN (0,4), 21, '')            AS `LÍNEA PRODUCTO`,
    IF(db.doc_type_code <> '07' AND s.i IN (0,4), 1, '')             AS `GRUPO PRODUCTO`,
    IF(db.doc_type_code <> '07' AND s.i IN (0,4), 1, '')             AS `CÓDIGO PRODUCTO`,
    IF(db.doc_type_code <> '07' AND s.i IN (0,4), FORMAT(1,5), 0)     AS `CANTIDAD`,
    FORMAT(0,5)              										AS `CANTIDAD2`,
    IF(db.doc_type_code <> '07' AND s.i IN (0,4), 1, 0)              AS `CÓDIGO DE LA BODEGA`,
    0																AS `CÓDIGO DE LA UBICACIÓN`,
    FORMAT(0,5)              										AS `CANTIDAD DE FACTOR DE CONVERSIÓN`,
    0																AS `OPERADOR DE FACTOR DE CONVERSIÓN`,
    FORMAT(0,5)              										AS `VALOR DEL FACTOR DE CONVERSIÓN`,
    ''																AS `GRUPO ACTIVOS`,
    ''																AS `CÓDIGO ACTIVO`,
    0																AS `ADICIÓN O MEJORA`,
    0																AS `VECES ADICIONALES A DEPRECIAR POR ADICIÓN O MEJORA`,
    0																AS `VECES A DEPRECIAR NIIF`,
    0																AS `NÚMERO DEL DOCUMENTO DEL PROVEEDOR`,
    ''																AS `PREFIJO DEL DOCUMENTO DEL PROVEEDOR`,
    ''																AS `AÑO DOCUMENTO DEL PROVEEDOR`,
    ''																AS `MES DOCUMENTO DEL PROVEEDOR`,
    ''																AS `DÍA DOCUMENTO DEL PROVEEDOR`,
    ''																AS `TIPO DOCUMENTO DE PEDIDO`,
    0																AS `CÓDIGO COMPROBANTE DE PEDIDO`,
    0																AS `NÚMERO DE COMPROBANTE PEDIDO`,
    0																AS `SECUENCIA DE PEDIDO`,
    '1'																AS `CÓDIGO DE LA MONEDA`,
    db.tipo_cambio                                                   AS `TASA DE CAMBIO`,
    ROUND(
        CASE s.i
            WHEN 0 THEN db.net_amount
            WHEN 1 THEN db.total_amount
            WHEN 2 THEN db.tax_igv
            WHEN 3 THEN db.tax_bag
            WHEN 4 THEN 0
        END / db.tipo_cambio, 2)                                     AS `VALOR DE LA SECUENCIA EN EXTRANJERA`,
	0																 AS `TIPO DE MONEDA ELABORACIÓN`,
    IF(s.i = 0, '0-000', db.serie_references_siigo)                  AS `TIPO Y COMPROBANTE CRUCE`,
    IF(s.i = 1, db.number_reference, '0')                            AS `NÚMERO DE DOCUMENTO CRUCE`,
    IF(s.i = 1, 1, '0')                                              AS `NÚMERO DE VENCIMIENTO`,
    IF(s.i = 1, db.emission_year_reference, '')                      AS `AÑO VENCIMIENTO DE DOCUMENTO CRUCE`,
    IF(s.i = 1, db.emission_month_reference, '')                     AS `MES VENCIMIENTO DE DOCUMENTO CRUCE`,
    IF(s.i = 1, db.emission_day_reference, '')                       AS `DÍA VENCIMIENTO DE DOCUMENTO CRUCE`,
    ''																 AS `DOCUMENTO ORIGEN DADO POR EL PROVEEDOR`,
    ''																 AS `AÑO DE DETRACCIÓN`,
    ''																 AS `MES DE DETRACCIÓN`,
    ''																 AS `DÍA DE DETRACCIÓN`,
    ''																 AS `INDICADOR TIPO DE LETRA`,
    ''																 AS `ESTADO QUE SE ASIGNÓ A LA LETRA`,
    0																 AS `CÓDIGO DEL MEDIO DE PAGO`,
    0																 AS `ACTIVIDADES FLUJO DE EFECTIVO`,
    ''																 AS `NÚMERO DE DEPÓSITO`,
    FORMAT(0,2)																 AS `PORCENTAJE IGV DETRACCIÓN`,
    FORMAT(0,2)																 AS `BASE CÁLCULO DE DETRACCIÓN`,
    FORMAT(0,2)																 AS `VALOR IGV DE DETRACCIÓN`,
    ''																 AS `CÓDIGO TASA DE DETRACCIÓN`,
    ''																 AS `CÓDIGO TRANSACCIÓN BANCARIA`,
    IF(s.i = 0, 'S', 'N')                                            AS `ÍTEM AFECTO O INAFECTO`,
    ''                                                                                          AS `AÑO DE EMISIÓN`,
''                                                                                          AS `MES DE EMISIÓN`,
''                                                                                          AS `DÍA DE EMISIÓN`,
'0'                                                                                          AS `NÚMERO DE DOCUMENTO ORIGINAL  O PREIMPRESO`,
'0'                                                                                          AS `CÓDIGO SECUENCIA DE LA TRANSACCIÓN`,
'0'                                                                                          AS `TIPO DE OPERACIÓN`,
''                                                                                          AS `TIPO ORIGINAL`,
''                                                                                          AS `SERIE ORIGINAL`,
''                                                                                          AS `AÑO FECHA ORIGINAL`,
''                                                                                          AS `MES FECHA ORIGINAL`,
''                                                                                          AS `DIA FECHA ORIGINAL`,
'0'                                                                                          AS `NÚMERO DE BULTOS`,
''                                                                                          AS `UNIDAD DE MEDIDA PESO BRUTO`,
''                                                                                          AS `DOCUMENTO RELACIONADO`,
''                                                                                          AS `CÓDIGO DAM`,
'0'                                                                                          AS `CÓDIGO TRANSPORTISTA`,
'0'                                                                                          AS `CÓDIGO DE MOTIVO DE TRASLADO`,
'0'                                                                                          AS `FECHA DE INICIO DEL TRASLADO`,
''                                                                                          AS `NÚMERO DOCUMENTO DE IMPORTACIÓN`,
''                                                                                          AS `INCISO APLICABLE DEL ARTÍCULO 33`,
''                                                                                          AS `DESCRIPCIÓN DE COMENTARIOS`,
''                                                                                          AS `DESCRIPCIÓN LARGA-001`,
''                                                                                          AS `DESCRIPCIÓN LARGA-002`,
''                                                                                          AS `DESCRIPCIÓN LARGA-003`,
''                                                                                          AS `DESCRIPCIÓN LARGA-004`,
''                                                                                          AS `DESCRIPCIÓN LARGA-005`,
''                                                                                          AS `INCONTERM`,
''                                                                                          AS `DESCRIPCIÓN EXPORTACIÓN`,
''                                                                                          AS `MEDIO DE TRANSPORTE`,
'0'                                                                                          AS `PAÍS DE ORIGEN`,
'0'                                                                                          AS `CIUDAD DE ORIGEN`,
'0'                                                                                          AS `PAIS DESTINO`,
'0'                                                                                          AS `CIUDAD DESTINO`,
FORMAT(0,2)                                                                                          AS `PESO NETO`,
FORMAT(0,2)                                                                                     AS `PESO BRUTO`,
''                                                                                          AS `UNIDAD DE MEDIDA NETO`,
''                                                                                          AS `UNIDAD DE MEDIDA BRUTO`,
'0'                                                                                          AS `CONCEPTO FACTURACION EN BLOQUE`,
''                                                                                          AS `DATOS ESTABLEC. (L=LOCAL O=OFICINA)`,
'0'                                                                                          AS `NÚMERO ESTABLECIMIENTO`,
''																				AS `08976-DESCRIPCIÓN DEL MOTIVO O SUSTENTO`,
IF(s.i = 0, 0, '')                                           AS `08950-TIPO DOCUMENTO EMISOR ANTICIPO1`,
IF(s.i = 0, 0, '')                                           AS `08951-IDENTIFICACIÓN DEL EMISOR ANTICIPO1`,
IF(s.i = 0, FORMAT(0, 2), '')                                           AS `08952-VALOR ANTICIPO1`,
IF(s.i = 0, 0, '')                                           AS `08953-TIPO DOCUMENTO ANTICIPO1`,
''                                           AS `08954-SERIE Y NÚMERO DOCUMENTO ANTICIPO1`,
IF(s.i = 0, 0, '')                                           AS `08955-TIPO DOCUMENTO EMISOR ANTICIPO2`,
IF(s.i = 0, 0, '')                                           AS `08956-IDENTIFICACIÓN DEL EMISOR ANTICIPO2`,
IF(s.i = 0, FORMAT(0, 2), '')                                            AS `08957-VALOR ANTICIPO2`,
IF(s.i = 0, 0, '')                                           AS `08958-TIPO DOCUMENTO ANTICIPO2`,
''                                           AS `08959-SERIE Y NÚMERO DOCUMENTO ANTICIPO2`,
IF(s.i = 0, 0, '')                                           AS `08960-TIPO DOCUMENTO EMISOR ANTICIPO3`,
IF(s.i = 0, 0, '')                                           AS `08961-IDENTIFICACIÓN DEL EMISOR ANTICIPO3`,
IF(s.i = 0, FORMAT(0, 2), '')                                           AS `08962-VALOR ANTICIPO3`,
IF(s.i = 0, 0, '')                                           AS `08963-TIPO DOCUMENTO ANTICIPO3`,
''                                           AS `08964-SERIE Y NÚMERO DOCUMENTO ANTICIPO3`,
IF(s.i = 0, 0, '')                                           AS `08965-TIPO DOCUMENTO EMISOR ANTICIPO4`,
IF(s.i = 0, 0, '')                                           AS `08966-IDENTIFICACIÓN DEL EMISOR ANTICIPO4`,
IF(s.i = 0, FORMAT(0, 2), '')                                             AS `08967-VALOR ANTICIPO4`,
IF(s.i = 0, 0, '')                                           AS `08968-TIPO DOCUMENTO ANTICIPO4`,
''                                           AS `08969-SERIE Y NÚMERO DOCUMENTO ANTICIPO4`,
IF(s.i = 0, 0, '')                                           AS `08970-TIPO DOCUMENTO EMISOR ANTICIPO5`,
IF(s.i = 0, 0, '')                                           AS `08971-IDENTIFICACIÓN DEL EMISOR ANTICIPO5`,
IF(s.i = 0, FORMAT(0, 2), '')                                           AS `08972-VALOR ANTICIPO5`,
IF(s.i = 0, 0, '')                                           AS `08973-TIPO DOCUMENTO ANTICIPO5`,
''                                           AS `08974-SERIE Y NÚMERO DOCUMENTO ANTICIPO5`,
IF(s.i = 0, FORMAT(0, 2), '')                                           AS `08992-VALOR DEL ANTICIPO1 + IGV`,
IF(s.i = 0, FORMAT(0, 2), '')                                           AS `08993-VALOR DEL ANTICIPO2 + IGV`,
IF(s.i = 0, FORMAT(0, 2), '')                                           AS `08994-VALOR DEL ANTICIPO3 + IGV`,
IF(s.i = 0, FORMAT(0, 2), '')                                           AS `08995-VALOR DEL ANTICIPO4 + IGV`,
IF(s.i = 0, FORMAT(0, 2), '')                                           AS `08996-VALOR DEL ANTICIPO5 + IGV`,
''                                          AS `08975-REVALUADO CON EFECTO TRIBUTARIO (S/N)`
FROM doc_base db
JOIN seq s
  ON s.i < IF(db.doc_type_code = '07', 4, 5)
ORDER BY db.document_id, s.i;