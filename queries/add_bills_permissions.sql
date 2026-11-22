-- Permisos de /bills y su asignación al rol administrador.
--
-- Desde que /bills exige JWT + permiso por endpoint (routers/bills.py), un rol
-- sin estos permisos recibe 403 en esas rutas. Este script:
--   1. Crea los permisos bills:sync, bills:reconcile y bills:confirm
--      (bills:read ya existía).
--   2. Los asigna, junto con bills:read y roles:read, al rol 'admin'.
--
-- Es idempotente: se puede ejecutar más de una vez sin duplicar filas.

INSERT INTO permissions (permission, description, status) VALUES
    ('bills:read',      'Ver y descargar reportes',          1),
    ('bills:sync',      'Sincronizar datos de Bsale y SUNAT', 1),
    ('bills:reconcile', 'Cargar y conciliar Niubiz',          1),
    ('bills:confirm',   'Confirmar cancelaciones y folios',   1),
    ('roles:read',      'Mostrar roles',                      1)
ON DUPLICATE KEY UPDATE permission = permission;

INSERT INTO role_permission (role_id, permission_id, status)
SELECT r.id, p.id, 1
FROM roles r
JOIN permissions p ON p.permission IN (
    'bills:read', 'bills:sync', 'bills:reconcile', 'bills:confirm', 'roles:read'
)
WHERE r.role = 'admin'
ON DUPLICATE KEY UPDATE status = 1;
