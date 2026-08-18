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
- MySQL corriendo localmente
- Base de datos `CV_DB` creada

## Instalación

```bash
# Instalar dependencias
pip install fastapi uvicorn sqlalchemy mysqlclient pandas openpyxl pyjwt bcrypt python-dotenv requests pytz

# Configurar variables de entorno
cp .env.example .env  # editar con tus credenciales
```

## Variables de entorno (`.env`)

```env
MYSQL_USER=root
MYSQL_PASSWORD=<password>
MYSQL_HOST=localhost
MYSQL_DB=CV_DB
ENVIRONMENT=test

# APIs externas
API_SUNAT_URL=https://api.apis.net.pe/v2/sunat/
BSALE_ACCESS_TOKEN=<token>
NIUBIZ_API_KEY=<key>
```

## Ejecución

```bash
# Desarrollo
uvicorn main:app --reload

# Producción
uvicorn main:app --host 0.0.0.0 --port 8000
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
└── procesos.ipynb           # Pipeline de importación de datos Niubiz
```

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/users/token` | Login (retorna JWT) |
| `GET/POST` | `/bills/*` | Gestión de documentos y pagos |
| `GET/POST` | `/roles/*` | Gestión de roles |
| `POST` | `/admin/` | Operaciones de administración |

> Todos los endpoints (excepto `/users/token`) requieren el header `X-Token: <jwt>`.

## Autenticación

1. Hacer `POST /users/token` con `username` y `password`
2. Usar el token retornado en el header `X-Token` de todas las demás requests

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

Orígenes permitidos en desarrollo:
- `http://localhost`
- `http://localhost:8000`
- `http://localhost:4200` (Angular)

## Integraciones externas

- **Bsale** — sincronización de documentos vía `/v1/*`
- **SUNAT** — consulta de RUC/DNI vía `api.apis.net.pe`
- **Niubiz** — conciliación de pagos con POS y web
