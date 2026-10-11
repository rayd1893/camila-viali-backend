use cv_db;

select * from users;

-- MySQL no soporta "BEFORE"; se usa AFTER status para que avatar quede
-- justo antes de role_id (mismo orden que models/user.py).
alter table users add avatar varchar(255) null after status;
