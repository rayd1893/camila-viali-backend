# Billing & Payment Management API

API REST para gestión de facturación, pagos y reportes financieros, integrada con Bsale, SUNAT y Niubiz.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Framework | FastAPI (Python) |
| ORM | SQLAlchemy |
| Base de datos | MySQL |
| Autenticación | JWT + bcrypt |
| Procesamiento de datos | Pandas / OpenPyXL |
| APIs externas | Bsale · SUNAT · Niubiz |

## Requisitos previos

- Python 3.10+
- MySQL 8.0+ corriendo localmente (el reporte de cancelación usa `WITH`, que no existe en 5.7)
- Base de datos `CV_DB` creada
- Zona horaria del equipo en `America/Lima` (ver [Despliegue](#despliegue))

## Instalación

```bash
# Instalar dependencias (versiones fijadas)
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env  # editar con tus credenciales
```

## Variables de entorno (`.env`)

La lista completa está en `.env.example`. Las principales:

```env
SECRET_TOKEN=<secreto del header X-Token>
SECRET_KEY=<clave para firmar el JWT, mínimo 32 caracteres>  # python -c "import secrets; print(secrets.token_urlsafe(64))"

MYSQL_USER=root
MYSQL_PASSWORD=<password>
MYSQL_HOST=localhost
MYSQL_DB=CV_DB
ENVIRONMENT=test

# APIs externas
ACCESS_TOKEN_BSALE=<token>
API_SUNAT_URL=https://api.apis.net.pe/v2/sunat/
API_SUNAT_TOKEN=<token>

# Correo de recuperación de contraseña
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=

# URL del panel (React + Vite); se usa para el enlace de /reset-password
FRONTEND_URL=http://localhost:5173
```

## Ejecución

```bash
# Desarrollo
uvicorn main:app --reload

# Producción (detrás de Nginx, ver Despliegue)
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers
```

La API estará disponible en `http://localhost:8000`. Documentación automática en `http://localhost:8000/docs`.

## Estructura del proyecto

```
app/
├── main.py                  # Punto de entrada FastAPI
├── dependencies.py          # Middleware de verificación de token
├── .env                     # Variables de entorno (no versionar)
│
├── models/                  # Modelos SQLAlchemy
│   ├── engine/
│   │   └── connection.py    # Conexión y sesión MySQL
│   ├── user.py / role.py / permission.py
│   ├── document.py / document_type.py
│   ├── payment.py / payment_type.py
│   ├── client.py
│   ├── approval.py / refund.py
│   ├── coin.py / exchange.py
│   ├── center.py / subcenter.py
│   ├── breakdown.py / tax.py
│   └── niubiz.py / payment_source_match.py
│
├── routers/                 # Endpoints FastAPI
│   ├── users.py             # Autenticación y gestión de usuarios
│   ├── roles.py             # Gestión de roles
│   └── bills.py             # Documentos, pagos y reportes (core)
│
├── schemas/                 # Schemas Pydantic (request/response)
│   ├── user.py
│   ├── bill.py
│   └── role.py
│
├── internal/
│   └── admin.py             # Endpoints de administración
│
├── queries/                 # Scripts SQL auxiliares
│   ├── add_column_payment.sql
│   ├── report.sql
│   └── update_payments.sql
│
├── requirements.txt         # Dependencias con versiones fijadas
└── procesos.ipynb           # Pipeline de importación de datos Niubiz
```

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/users/login` | Login (retorna JWT) |
| `GET/POST/PATCH` | `/users/*` | Perfil, avatar, recuperación de contraseña y gestión de usuarios |
| `GET/POST` | `/bills/*` | Sincronización, conciliación Niubiz y reportes |
| `GET/POST` | `/roles/*` | Gestión de roles |

> Todos los endpoints, incluido el login, requieren el header `X-Token` con el valor de `SECRET_TOKEN`. Los archivos de `/static` (avatares) no lo requieren.

## Autenticación

1. Hacer `POST /users/login` con `username` y `password` (y el header `X-Token`).
2. Enviar el JWT retornado en el header `Authorization: Bearer <jwt>` en las rutas protegidas, además del `X-Token`.
3. El JWT se firma con `SECRET_KEY` y expira a los 90 minutos; no hay endpoint de renovación. Un token vencido o inválido responde 401.

La API no arranca si `SECRET_KEY` falta o tiene menos de 32 caracteres. Cambiarla invalida todas las sesiones abiertas.

## Reportes

Los reportes de `/bills` (`sales_book`, `book_entry`, `cancellation_book`, `cancellation_entry`, `cruce_documents_niubiz`) son `GET` y reciben las fechas como query params:

```
GET /bills/sales_book?start_date=2026-10-01&end_date=2026-10-31&format=xlsx
```

- `format=json` (por defecto) devuelve las filas.
- `format=xlsx` devuelve el Excel como descarga (`Content-Disposition: attachment`). Si no hay datos responde 404 con el motivo en `detail`.
- Los Excel se generan en memoria; no se guardan en el servidor.

La sincronización de documentos es `POST /bills/extract_data` con fechas `YYYY-MM-DD`:

```json
{ "emission_date_start": "2026-10-01", "emission_date_end": "2026-10-31" }
```

## Importación de datos Niubiz

El notebook `procesos.ipynb` procesa los reportes Excel de Niubiz y los carga a la tabla `base_niubiz` en MySQL.

```
Reporte_Mis_depósitos_*.xlsx → procesos.ipynb → MySQL (base_niubiz)
```

El algoritmo de matching de pagos usa las siguientes prioridades:
1. **EXACT** — coincidencia exacta de monto
2. **TIME_TOLERANCE** — tolerancia de 5 minutos para transacciones POS
3. **WEB_ONLY** — pagos web sin coincidencia temporal
4. **DATE_FALLBACK** — ventana de 2 días como último recurso

## CORS

Orígenes permitidos en desarrollo (`origins` en `main.py`):
- `http://localhost`
- `http://localhost:8000`
- `http://localhost:5173` (panel React + Vite, `vite dev`)

El header `Content-Disposition` está expuesto para que el panel pueda leer el nombre de los Excel descargados. Al publicar el panel, agregar su dominio de producción a `origins`.

## Frontend

El panel administrativo se construirá aparte como una SPA con **React + Vite + TypeScript + Tailwind CSS**. Todavía no existe. Las consideraciones de integración (cliente HTTP, manejo del JWT, descargas de Excel, estructura sugerida) están en la sección 12 de `ficha_tecnica.md`.

## Despliegue

Para el volumen actual (base de ~74 MB) basta un solo servidor Linux con la API, MySQL y Nginx, que además sirva el panel como archivos estáticos. El detalle completo está en la sección 13 de `ficha_tecnica.md`.

### Requisitos mínimos

| Recurso | Mínimo |
|---|---|
| Servidor | 2 vCPU, 2 GB RAM (4 GB recomendado), 20 GB SSD, Ubuntu 22.04/24.04 LTS |
| Python | 3.10 |
| MySQL | 8.0, `utf8mb4` |
| Nginx | 1.18 |
| Node.js | 22 LTS, solo para compilar el panel |
| Paquetes del sistema | `build-essential pkg-config python3-dev default-libmysqlclient-dev` (para `mysqlclient`) |
| Dominio | 2 subdominios con HTTPS (ej. `panel.` y `api.`) |

### Red

- Entrada: 443 (80 solo para redirigir a HTTPS).
- Salida: 443 hacia `api.bsale.io` y `api.apis.net.pe`; 587 hacia el servidor SMTP.
- MySQL (3306) y uvicorn (8000) escuchan solo en `127.0.0.1`.

### Configuración obligatoria

1. **Zona horaria `America/Lima`.** El código usa la hora local del servidor para convertir fechas de Bsale; en un servidor en UTC quedan corridas 5 horas. `timedatectl set-timezone America/Lima` o `TZ=America/Lima` en el servicio.
2. **Variables de entorno** de `.env.example`, con `FRONTEND_URL` apuntando al dominio real del panel, y el dominio del panel agregado a `origins` en `main.py`.
3. **Nginx:** `proxy_read_timeout 300s` (la sincronización con Bsale y el matching tardan minutos), `client_max_body_size 20m` (el Excel de Niubiz supera el límite de 1 MB por defecto) y `try_files $uri /index.html` en el panel (para que `/reset-password` no dé 404).
4. **Usuario de MySQL** con `CREATE` e `INDEX` además de lectura y escritura, porque la API crea las tablas al arrancar.
5. **`static/avatars/` persistente** entre despliegues.
6. **uvicorn como servicio** (systemd o contenedor): `uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers`.
7. **Backup diario** de MySQL fuera del servidor. `cancellation_entry_folio` guarda los folios enviados a SIIGO y no se puede reconstruir desde Bsale.

## Integraciones externas

- **Bsale** — sincronización de documentos vía `/v1/*`
- **SUNAT** — tipo de cambio mensual vía `api.apis.net.pe`
- **Niubiz** — conciliación de pagos con POS y web
