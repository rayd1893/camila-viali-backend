use cv_db;

-- Extraer documentos
WITH filtered_documents AS
(select d.id as id_document,  d.emission_date, dt.name as document_type_name, d.serial_number, d.net_amount, d.tax_amount, d.total_amount,
d.id, format(IFNULL(c.code,99999999), 0) as nit, d.expiration_date
from documents d
inner join document_types dt
on d.id_document_type = dt.id
left join clients c 
on d.id_client = c.id
where d.emission_date between '20260901' and '20260915'),
-- Extraer operaciones niubiz
filtered_operation_niubiz as
(select id_operacion, cod_comercio, n_lote, date(str_to_date(fecha_y_hora_operacion,'%d-%m-%Y %H:%i')) as operation_date, nombre_comercial
from operaciones_niubiz
where str_to_date(fecha_y_hora_operacion,'%d-%m-%Y %H:%i') between '20260815' and '20260920'),
-- Extraer pagos Niubiz
filtered_payments_niubiz as (
select p.id as id_payment, p.recordDate, p.id_document,pt.name payment_type_name 
from payments p 
inner join payment_types pt
on p.id_payment_type = pt.id
where p.recordDate between '20260815' and '20260920'
and pt.name like '%niubiz%'
),
-- Cruzar con operaciones de niubiz
match_niubiz as (select distinct fd.serial_number, fd.emission_date, fd.document_type_name, fd.net_amount, 
fd.tax_amount, fd.total_amount, fon.n_lote, fd.expiration_date,
CASE WHEN fd.document_type_name LIKE '%PLAZA NORTE%' THEN 'L-14'
	 WHEN fd.document_type_name LIKE '%POLO%' THEN 'L-17'
     WHEN fd.document_type_name LIKE '%CHACARILLA%' THEN 'L-19'
     WHEN fd.document_type_name LIKE '%SAN MIGUEL%' THEN 'L-20'
     WHEN fd.document_type_name LIKE '%SALAVERRY%' THEN 'L-21'
     WHEN fd.document_type_name LIKE '%PRIMAVERA%' THEN 'L-22'
     WHEN fd.document_type_name LIKE '%TRUJILLO%' THEN 'L-23'
     WHEN fd.document_type_name LIKE '%A4%' THEN 'L-10'
     ELSE 'L-1'
END serial_number_report,
(select siigo from approvals where bsale = SUBSTRING(fd.serial_number, 1, 4) limit 1) as serial_number_siigo,
nit, '1201020100' as number_account, 'C' as credit_or_debit, 'FT BL Y OTROS COMP X COB EN CARTERA MN' as sequence_description,
format(right(SUBSTRING_INDEX(serial_number, '-', 1),2),0) as subcenter
from filtered_operation_niubiz fon
inner join payment_source_match psm
on  fon.id_operacion = psm.id_operacion
inner join filtered_payments_niubiz fpn
on psm.id_payment = fpn.id_payment
inner join filtered_documents fd
on fpn.id_document = fd.id_document
),
agrup_match_niubiz as (select emission_date, serial_number_report, subcenter,'1602090100' as number_account , 'D' as credit_or_debit,
SUM(total_amount) as total_amount, format('20341198217', 0) as nit, '' as expiration_date,
concat('LOTE ', right(max(n_lote),4), ' VISA ', CASE WHEN serial_number_report = 'L-10' THEN 'ECOMERCE' 
										   WHEN serial_number_report = 'L-14' THEN 'PLAZA NORTE'
                                           WHEN serial_number_report = 'L-17' THEN 'EL POLO'
                                           WHEN serial_number_report = 'L-19' THEN 'CHACARILLA'
                                           WHEN serial_number_report = 'L-20' THEN 'SAN MIGUEL'
                                           WHEN serial_number_report = 'L-21' THEN 'SALAVERRY'
                                           WHEN serial_number_report = 'L-22' THEN 'PRIMAVERA'
                                           WHEN serial_number_report = 'L-23' THEN 'TRUJILLO'
                                           ELSE 'AFFARI'
											END) as sequence_description 
from match_niubiz
group by emission_date, serial_number_report, subcenter),
report as (
select emission_date, serial_number_report, number_account, credit_or_debit, total_amount, nit, sequence_description, 
'' as serial_number_siigo, '0' as document_number, subcenter, expiration_date
from agrup_match_niubiz
union 
select emission_date, serial_number_report, number_account, credit_or_debit, total_amount, nit, sequence_description, 
serial_number_siigo, SUBSTRING_INDEX(serial_number, '-', -1)  as document_number, subcenter, expiration_date
from match_niubiz
)
select 
SUBSTRING_INDEX(serial_number_report, '-', 1) as 'TIPO DE COMPROBANTE (OBLIGATORIO)',
SUBSTRING_INDEX(serial_number_report, '-', -1) as 'CÓDIGO COMPROBANTE  (OBLIGATORIO)',
concat(DATE_FORMAT(emission_date, '%Y%m'), 
	right(concat('000', DENSE_RANK() OVER (PARTITION BY serial_number_report ORDER BY emission_date )),3)) as 'NÚMERO DE DOCUMENTO',
number_account as 'CUENTA CONTABLE   (OBLIGATORIO)',
credit_or_debit as 'DÉBITO O CRÉDITO (OBLIGATORIO)',
format(round(total_amount,2),2) as 'VALOR DE LA SECUENCIA   (OBLIGATORIO)',
year(emission_date) as 'AÑO DEL DOCUMENTO',
month(emission_date) as 'MES DEL DOCUMENTO',
day(emission_date) as 'DÍA DEL DOCUMENTO',
1 as 'CÓDIGO DEL VENDEDOR',
1 as 'CÓDIGO DE LA CIUDAD',
0 as 'CÓDIGO DE LA ZONA',
ROW_NUMBER() OVER (PARTITION BY serial_number_report, emission_date ORDER BY document_number ) AS 'SECUENCIA',
3 as 'CENTRO DE COSTO', subcenter as 'SUBCENTRO DE COSTO', nit as 'NIT', '0' as 'SUCURSAL',
sequence_description as 'DESCRIPCIÓN DE LA SECUENCIA',
'0' as 'NÚMERO DE CHEQUE', 'N' as 'COMPROBANTE ANULADO', '0' as 'CÓDIGO DEL MOTIVO DE DEVOLUCIÓN'
, '0' as 'FORMA DE PAGO', '0.00' as 'VALOR DEL CARGO 1 DE LA SECUENCIA', '0.00' as 'VALOR DEL CARGO 2 DE LA SECUENCIA'
, '0.00' as 'VALOR DEL DESCUENTO 1 DE LA SECUENCIA', '0.00' as 'VALOR DEL DESCUENTO 2 DE LA SECUENCIA',
'0.00' as 'VALOR DEL DESCUENTO 3 DE LA SECUENCIA',  '0' as 'PREFIJO DE ORDER REFERENCE',
'0' as 'CONSECUTIVO DE ORDER REFERENCE', '0' as 'PREFIJO ORDEN DE ENTREGA', '0' as 'NÚMERO ORDEN DE ENTREGA', 
'0' as 'AÑO FECHA DE ORDEN DE ENTREGA', '0' as 'MES FECHA DE ORDEN DE ENTREGA', '0' as 'DÍA FECHA DE ORDEN DE ENTREGA', 
'' as 'INGRESOS PARA TERCEROS', DATE_FORMAT(CURDATE(),'%Y%m%d') as 'FECHA ACTUALIZACIÓN DEL DOCUMENTO', 
DATE_FORMAT(NOW(),'%H%i%s') as 'HORA DE ACTUALIZACIÓN DEL DOCUMENTO',
'0' as 'PREFIJO ORDEN DE ENTREGA2', '0' as 'NÚMERO ORDEN DE ENTREGA2', '0' as 'AÑO FECHA DE ORDEN DE ENTREGA2', 
'0' as 'MES FECHA DE ORDEN DE ENTREGA2', '0' as 'DÍA FECHA DE ORDEN DE ENTREGA2', '0' as 'PREFIJO ORDEN DE ENTREGA3', 
'0' as 'NÚMERO ORDEN DE ENTREGA3', '0' as 'AÑO FECHA DE ORDEN DE ENTREGA3', '0' as 'MES FECHA DE ORDEN DE ENTREGA3', 
'0' as 'DÍA FECHA DE ORDEN DE ENTREGA3', '0' as 'PREFIJO ORDEN DE ENTREGA4', '0' as 'NÚMERO ORDEN DE ENTREGA4', 
'0' as 'AÑO FECHA DE ORDEN DE ENTREGA4', '0' as 'MES FECHA DE ORDEN DE ENTREGA4', '0' as 'DÍA FECHA DE ORDEN DE ENTREGA4', 
'0' as 'PREFIJO ORDEN DE ENTREGA5', '0' as 'NÚMERO ORDEN DE ENTREGA5', '0' as 'AÑO FECHA DE ORDEN DE ENTREGA5', 
'0' as 'MES FECHA DE ORDEN DE ENTREGA5', '0' as 'DÍA FECHA DE ORDEN DE ENTREGA5', '0.00' as 'PORCENTAJE DEL IVA DE LA SECUENCIA', 
'0.00' as 'VALOR DE IVA DE LA SECUENCIA', '' as 'BASE DE RETENCIÓN', '0.00' as 'BASE PARA CUENTAS MARCADAS COMO RETEIVA',
'' as 'PORCENTAJE AIU', '' as 'BASE IVA AIU', '0.00' as 'VALOR TOTAL IMPOCONSUMO DE LA SECUENCIA', '' as 'LÍNEA PRODUCTO', 
'' as 'GRUPO PRODUCTO', '' as 'CÓDIGO PRODUCTO', '0.00000' as 'CANTIDAD', '0.00000' as 'CANTIDAD DOS', '0' as 'CÓDIGO DE LA BODEGA',
'0' as 'CÓDIGO DE LA UBICACIÓN', '0.00000' as 'CANTIDAD DE FACTOR DE CONVERSIÓN', '0' as 'OPERADOR DE FACTOR DE CONVERSIÓN',
'0.00000' as 'VALOR DEL FACTOR DE CONVERSIÓN', '' as 'GRUPO ACTIVOS', '' as 'CÓDIGO ACTIVO', '0' as 'ADICIÓN O MEJORA',
'0' as 'VECES ADICIONALES A DEPRECIAR POR ADICIÓN O MEJORA', '0' as 'VECES A DEPRECIAR NIIF', 
'2,764' as 'NÚMERO DEL DOCUMENTO DEL PROVEEDOR', '' as 'PREFIJO DEL DOCUMENTO DEL PROVEEDOR', 
year(emission_date) as 'AÑO DOCUMENTO DEL PROVEEDOR',
month(emission_date) as 'MES DOCUMENTO DEL PROVEEDOR',
day(emission_date) as 'DÍA DOCUMENTO DEL PROVEEDOR', '' as 'TIPO DOCUMENTO DE PEDIDO', '0' as 'CÓDIGO COMPROBANTE DE PEDIDO',
'0' as 'NÚMERO DE COMPROBANTE PEDIDO', '0' as 'SECUENCIA DE PEDIDO', '1' as 'CÓDIGO DE LA MONEDA',
format((select value from exchanges where type = 'V' and day = emission_date limit 1), 5) as 'TASA DE CAMBIO',
format(ROUND(total_amount/ (select value from exchanges where type = 'V' and day = emission_date limit 1),2) , 5) as 'VALOR DE LA SECUENCIA EN EXTRANJERA',
'0' AS 'TIPO DE MONEDA ELABORACIÓN',
serial_number_siigo AS 'TIPO Y COMPROBANTE CRUCE', document_number AS 'NÚMERO DE DOCUMENTO CRUCE',
CASE WHEN expiration_date = '' THEN 0
ELSE 1 END AS 'NÚMERO DE VENCIMIENTO', IFNULL(YEAR(expiration_date),'') AS 'AÑO VENCIMIENTO DE DOCUMENTO CRUCE',
IFNULL(MONTH(expiration_date),'') AS 'MES VENCIMIENTO DE DOCUMENTO CRUCE',
IFNULL(DAY(expiration_date),'') AS 'DÍA VENCIMIENTO DE DOCUMENTO CRUCE',
'2' AS 'DOCUMENTO ORIGEN DADO POR EL PROVEEDOR', 
'' AS 'AÑO DE DETRACCIÓN', '' AS 'MES DE DETRACCIÓN', '' AS 'DÍA DE DETRACCIÓN', '' AS 'INDICADOR TIPO DE LETRA', 
'' AS 'ESTADO QUE SE ASIGNÓ A LA LETRA', '0' AS 'CÓDIGO DEL MEDIO DE PAGO', '0' AS 'ACTIVIDADES FLUJO DE EFECTIVO',
'' AS 'NÚMERO DE DEPÓSITO', '0.00' AS 'PORCENTAJE IGV DETRACCIÓN', '0.00' AS 'BASE CÁLCULO DE DETRACCIÓN', 
'0.00' AS 'VALOR IGV DE DETRACCIÓN', '' AS 'CÓDIGO TASA DE DETRACCIÓN', '' AS 'CÓDIGO TRANSACCIÓN BANCARIA',
' ' AS 'ÍTEM AFECTO O INAFECTO',
'    ' AS 'AÑO DE EMISIÓN',
'  ' AS 'MES DE EMISIÓN',
'  ' AS 'DÍA DE EMISIÓN',
'2764' AS 'NÚMERO DE DOCUMENTO ORIGINAL  O PREIMPRESO',
'0' AS 'CÓDIGO SECUENCIA DE LA TRANSACCIÓN',
'0' AS 'TIPO DE OPERACIÓN',
'   ' AS 'TIPO ORIGINAL',
'                    ' AS 'SERIE ORIGINAL',
'    ' AS 'AÑO FECHA ORIGINAL',
'  ' AS 'MES FECHA ORIGINAL',
'  ' AS 'DIA FECHA ORIGINAL',
'0' AS 'NÚMERO DE BULTOS',
'   ' AS 'UNIDAD DE MEDIDA PESO BRUTO',
'  ' AS 'DOCUMENTO RELACIONADO',
'                       ' AS 'CÓDIGO DAM',
'0' AS 'CÓDIGO TRANSPORTISTA',
'0' AS 'CÓDIGO DE MOTIVO DE TRASLADO',
DATE_FORMAT(emission_date,'%Y%m%d') as 'FECHA DE INICIO DEL TRASLADO',
'                    ' AS 'NÚMERO DOCUMENTO DE IMPORTACIÓN',
' ' AS 'INCISO APLICABLE DEL ARTÍCULO 33',
'                                                                                                                                                                                                                                    ' AS 'DESCRIPCIÓN DE COMENTARIOS',
'                                                            ' AS 'DESCRIPCIÓN LARGA-001',
'                                                            ' AS 'DESCRIPCIÓN LARGA-002',
'                                                            ' AS 'DESCRIPCIÓN LARGA-003',
'                                                            ' AS 'DESCRIPCIÓN LARGA-004',
'                                                            ' AS 'DESCRIPCIÓN LARGA-005',
'          ' AS 'INCONTERM',
'                                                  ' AS 'DESCRIPCIÓN EXPORTACIÓN',
'                                                  ' AS 'MEDIO DE TRANSPORTE',
'0' AS 'PAÍS DE ORIGEN',
'0' AS 'CIUDAD DE ORIGEN',
'0' AS 'PAIS DESTINO',
'0' AS 'CIUDAD DESTINO',
'0.00' AS 'PESO NETO',
'0.00' AS 'PESO BRUTO',
'          ' AS 'UNIDAD DE MEDIDA NETO',
'          ' AS 'UNIDAD DE MEDIDA BRUTO',
'0' AS 'CONCEPTO FACTURACION EN BLOQUE',
' ' AS 'DATOS ESTABLEC. (L=LOCAL O=OFICINA)',
'0' AS 'NÚMERO ESTABLECIMIENTO',
'                                                                                                   ' AS '08976-DESCRIPCIÓN DEL MOTIVO O SUSTENTO',
' ' AS '08950-TIPO DOCUMENTO EMISOR ANTICIPO1',
'                 ' AS '08951-IDENTIFICACIÓN DEL EMISOR ANTICIPO1',
'                ' AS '08952-VALOR ANTICIPO1',
'  ' AS '08953-TIPO DOCUMENTO ANTICIPO1',
'                              ' AS '08954-SERIE Y NÚMERO DOCUMENTO ANTICIPO1',
' ' AS '08955-TIPO DOCUMENTO EMISOR ANTICIPO2',
'                 ' AS '08956-IDENTIFICACIÓN DEL EMISOR ANTICIPO2',
'                ' AS '08957-VALOR ANTICIPO2',
'  ' AS '08958-TIPO DOCUMENTO ANTICIPO2',
'                              ' AS '08959-SERIE Y NÚMERO DOCUMENTO ANTICIPO2',
' ' AS '08960-TIPO DOCUMENTO EMISOR ANTICIPO3',
'                 ' AS '08961-IDENTIFICACIÓN DEL EMISOR ANTICIPO3',
'                ' AS '08962-VALOR ANTICIPO3',
'  ' AS '08963-TIPO DOCUMENTO ANTICIPO3',
'                              ' AS '08964-SERIE Y NÚMERO DOCUMENTO ANTICIPO3',
' ' AS '08965-TIPO DOCUMENTO EMISOR ANTICIPO4',
'                 ' AS '08966-IDENTIFICACIÓN DEL EMISOR ANTICIPO4',
'                ' AS '08967-VALOR ANTICIPO4',
'  ' AS '08968-TIPO DOCUMENTO ANTICIPO4',
'                              ' AS '08969-SERIE Y NÚMERO DOCUMENTO ANTICIPO4',
' ' AS '08970-TIPO DOCUMENTO EMISOR ANTICIPO5',
'                 ' AS '08971-IDENTIFICACIÓN DEL EMISOR ANTICIPO5',
'                ' AS '08972-VALOR ANTICIPO5',
'  ' AS '08973-TIPO DOCUMENTO ANTICIPO5',
'                              ' AS '08974-SERIE Y NÚMERO DOCUMENTO ANTICIPO5',
'                ' AS '08992-VALOR DEL ANTICIPO1 + IGV',
'                ' AS '08993-VALOR DEL ANTICIPO2 + IGV',
'                ' AS '08994-VALOR DEL ANTICIPO3 + IGV',
'                ' AS '08995-VALOR DEL ANTICIPO4 + IGV',
'                ' AS '08996-VALOR DEL ANTICIPO5 + IGV',
'' AS '08975-REVALUADO CON EFECTO TRIBUTARIO (S/N)'
 from report r 
order by serial_number_report, emission_date, number_account desc, document_number 