use cv_db;

-- 1145 documentos únicos
-- 1282 pagos
select d.id as id_document,d.serial_number, d.emission_date, d.total_amount, d.net_amount, d.tax_amount, dt.code, dt.name as document_type,
p.recordDate as payment_date, p.amount as payment_amount, pt.name as payment_type, opn.id_operacion, opn.fecha_y_hora_operacion,
opn.fecha_de_deposito,opn.cod_comercio, opn.codigo_de_autorizacion, opn.n_voucher, opn.n_lote, 
 opn.importe_de_operacion, opn.monto_dcc, opn.suma_depositada, psm.match_type
from documents d
inner join document_types dt
on d.id_document_type = dt.id
inner join payments p
on d.id = p.id_document 
inner join payment_types pt
on p.id_payment_type = pt.id
left join payment_source_match psm 
on p.id = psm.id_payment
left join operaciones_niubiz opn 
on psm.id_operacion = opn.id_operacion
where emission_date between '20260901' and '20260915'
and dt.code != '09'; 