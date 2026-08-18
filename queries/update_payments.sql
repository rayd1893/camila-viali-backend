update payments a
-- select a.*, e.* from payments a
inner join payment_types b
on a.id_payment_type = b.id
inner join documents c
on a.id_document = c.id
inner join document_types d
on c.id_document_type = d.id
inner join base_niubiz e
on a.recordDate = date(STR_TO_DATE(e.`Fecha y Hora de Operación`, '%d-%m-%Y %T'))
and abs(a.amount - CAST(e.`Importe de Operación` as decimal(10,2))) <= 0.01
and LOCATE(e.`Cód. Comercio`, d.commercial_code) > 0
set a.commercial_code = e.`Cód. Comercio`,
	a.commercial_name = e.`Nombre Comercial`,
    a.operation_date = e.`Fecha y Hora de Operación`,
    a.deposit_date = e.`Fecha de depósito`,
    a.product = e.`Producto`,
    a.operation_type = e.`Tipo de Operación`,
    a.card_number = e.`Tarjeta`,
    a.card_type = e.`Tipo de Tarjeta`,
    a.operation_amount = e.`Importe de Operación`
where a.recordDate between '20250911' and '20250917'
and b.name like '%niubiz%'
and a.inactive = 0;