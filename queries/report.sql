use cv_db;

with t1 as (
select c.serial_number ,a.id as payment_id, a.recordDate, a.amount, d.commercial_code,
ROW_NUMBER() OVER (
            PARTITION BY d.commercial_code, a.recordDate, a.amount
            ORDER BY a.id
        ) AS rn
from payments a
inner join payment_types b
on a.id_payment_type = b.id
inner join documents c
on a.id_document = c.id
inner join document_types d
on c.id_document_type = d.id
where a.recordDate between '20250911' and '20250916'
and b.name like '%niubiz%'
and a.inactive = 0
),
 t2 as (
select `Cód. Comercio` as commercial_code, `Nombre Comercial` as commercial_name,
date(STR_TO_DATE(`Fecha y Hora de Operación`, '%d-%m-%Y %T')) as operation_date, 
STR_TO_DATE(`Fecha y Hora de Operación`, '%d-%m-%Y %T') as operation_date_hour,
`Fecha de depósito` as deposit_date, Producto as product, `Tipo de Operación` as operation_type,
`Tarjeta` as card_number, `Tipo de Tarjeta` as card_type, 
CAST(`Importe de Operación` as DECIMAL(10,2)) as operation_amount,
`Es DCC` as is_dcc, `Monto DCC` as dcc_amount, `Comisión Total` as total_commision, 
`Comisión Niubiz` as niubiz_comision, `IGV` as igv_comision, `Suma Depositada` as deposited_amount, 
`ID Operación` as operation_id, `Cuenta Banco Pagador` as target_account, `Banco Pagador` as bank_name, 
`N° Serie Terminal` as terminal_serial, `Código Autorización` as authorization_code, 
`N° Referencia` as references_number, `N° Voucher` as voucher_number,
ROW_NUMBER() OVER (
            PARTITION BY `Cód. Comercio`, 
            date(STR_TO_DATE(`Fecha y Hora de Operación`, '%d-%m-%Y %T')), 
            `Importe de Operación`
            ORDER BY `Fecha y Hora de Operación`
        ) AS rn
 from base_niubiz
)
select * 
from t1 
left join t2
on  LOCATE(t2.commercial_code, t1.commercial_code) > 0
and t2.operation_amount = t1.amount
and t1.recordDate = t2.operation_date
and t1.rn = t2.rn





---------------------------------------------------------------------------------

use cv_db;

with t1 as (
select c.serial_number, a.id as payment_id, a.recordDate, a.amount, d.commercial_code,
ROW_NUMBER() OVER (
            PARTITION BY d.commercial_code, a.recordDate, a.amount
            ORDER BY a.id
        ) AS rn
from payments a
inner join payment_types b
on a.id_payment_type = b.id
inner join documents c
on a.id_document = c.id
inner join document_types d
on c.id_document_type = d.id
where a.recordDate between '20250911' and '20250916'
and b.name like '%niubiz%'
and a.inactive = 0
),
 t2 as (
select `Cód. Comercio` as commercial_code, `Nombre Comercial` as commercial_name,
date(STR_TO_DATE(`Fecha y Hora de Operación`, '%d-%m-%Y %T')) as operation_date, 
STR_TO_DATE(`Fecha y Hora de Operación`, '%d-%m-%Y %T') as operation_date_hour,
`Fecha de depósito` as deposit_date, Producto as product, `Tipo de Operación` as operation_type,
`Tarjeta` as card_number, `Tipo de Tarjeta` as card_type, 
CAST(`Importe de Operación` as DECIMAL(10,2)) as operation_amount,
`Es DCC` as is_dcc, `Monto DCC` as dcc_amount, `Comisión Total` as total_commision, 
`Comisión Niubiz` as niubiz_comision, `IGV` as igv_comision, `Suma Depositada` as deposited_amount, 
`ID Operación` as operation_id, `Cuenta Banco Pagador` as target_account, `Banco Pagador` as bank_name, 
`N° Serie Terminal` as terminal_serial, `Código Autorización` as authorization_code, 
`N° Referencia` as references_number, `N° Voucher` as voucher_number,
ROW_NUMBER() OVER (
            PARTITION BY `Cód. Comercio`, 
            date(STR_TO_DATE(`Fecha y Hora de Operación`, '%d-%m-%Y %T')), 
            `Importe de Operación`
            ORDER BY `Fecha y Hora de Operación`
        ) AS rn
 from base_niubiz
)
select * 
from t2 
left join t1
on  LOCATE(t2.commercial_code, t1.commercial_code) > 0
and t2.operation_amount = t1.amount
and t1.recordDate = t2.operation_date
and t1.rn = t2.rn