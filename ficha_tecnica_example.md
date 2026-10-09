# FICHA TÉCNICA — TUINMUEBLE.COM

## 1. Información general

**Nombre del proyecto:** tuinmueble.com  
**Tipo de aplicación:** Portal inmobiliario + sistema administrativo  
**Versión:** MVP 1.0  
**Stack tecnológico:**

- Laravel 13
- React
- Inertia.js
- TypeScript
- MySQL
- Tailwind CSS
- Vite

---

# 2. Descripción del negocio

**tuinmueble.com** es una empresa inmobiliaria que cuenta con una cartera amplia de propiedades disponibles para:

- Venta
- Alquiler

La empresa necesita centralizar la publicación y administración de estas propiedades en una plataforma propia.

Actualmente, el objetivo principal es contar con un portal inmobiliario donde los clientes finales puedan explorar las propiedades disponibles, revisar toda su información y realizar consultas directamente a la inmobiliaria.

Al mismo tiempo, el personal interno debe disponer de un sistema administrativo desde donde pueda crear, actualizar y gestionar las propiedades publicadas.

---

# 3. Objetivo del proyecto

Construir una plataforma inmobiliaria que permita:

1. Administrar propiedades desde un panel privado.
2. Publicar automáticamente esas propiedades en un portal público.
3. Permitir a visitantes buscar y visualizar propiedades.
4. Permitir que un visitante realice una consulta sobre una propiedad.
5. Registrar esa consulta dentro del sistema.
6. Asociar cada consulta con la propiedad correspondiente.
7. Permitir que el equipo interno gestione las consultas recibidas.

El MVP debe priorizar que este flujo funcione completamente de punta a punta.

---

# 4. Evento central del sistema

El evento central del MVP es:

> **Un cliente muestra interés y realiza una consulta sobre una propiedad.**

Flujo principal:

```text
Administrador / Asistente
        ↓
Crea una propiedad
        ↓
Publica la propiedad
        ↓
La propiedad aparece en el portal
        ↓
Cliente encuentra la propiedad
        ↓
Visualiza el detalle
        ↓
Realiza una consulta
        ↓
Sistema registra la consulta
        ↓
Consulta queda asociada a la propiedad
        ↓
Administrador / Asistente recibe la consulta
        ↓
Equipo inmobiliario realiza seguimiento
```

---

# 5. Tipos de usuario

El sistema tendrá dos tipos principales de usuarios internos.

## 5.1 Administrador

Tiene control completo del sistema.

Puede:

- Iniciar sesión.
- Acceder al dashboard.
- Crear propiedades.
- Editar propiedades.
- Eliminar propiedades.
- Publicar o despublicar propiedades.
- Cambiar el estado de una propiedad.
- Administrar fotografías.
- Visualizar todas las consultas.
- Gestionar consultas.
- Crear usuarios.
- Editar usuarios.
- Desactivar usuarios.
- Asignar roles.
- Acceder a configuraciones generales.

---

## 5.2 Asistente

Usuario operativo encargado principalmente de administrar propiedades y consultas.

Puede:

- Iniciar sesión.
- Acceder al dashboard.
- Crear propiedades.
- Editar propiedades.
- Publicar propiedades.
- Actualizar fotografías.
- Actualizar disponibilidad.
- Visualizar consultas.
- Gestionar consultas.

No puede:

- Crear administradores.
- Modificar roles.
- Gestionar usuarios críticos.
- Modificar configuraciones globales del sistema.

---

# 6. Clientes finales

Los visitantes del portal **no necesitan crear una cuenta para el MVP**.

Podrán:

- Acceder al portal.
- Visualizar propiedades.
- Buscar propiedades.
- Filtrar propiedades.
- Abrir el detalle de una propiedad.
- Revisar fotografías.
- Consultar características.
- Consultar ubicación.
- Enviar una consulta.
- Contactar a la inmobiliaria.

---

# 7. Módulos del MVP

## 7.1 Autenticación

El sistema administrativo debe contar con autenticación.

Funciones:

- Login.
- Logout.
- Recuperación de contraseña.
- Protección de rutas.
- Gestión de sesión.
- Middleware de autenticación.
- Middleware/autorización por roles.

No habrá registro público.

Los usuarios serán creados por el administrador.

---

# 8. Dashboard

Después de iniciar sesión, el usuario accede al dashboard.

El dashboard MVP debe mostrar como mínimo:

- Total de propiedades.
- Propiedades publicadas.
- Propiedades disponibles.
- Propiedades vendidas.
- Propiedades alquiladas.
- Consultas nuevas.
- Consultas pendientes.
- Últimas propiedades registradas.
- Últimas consultas recibidas.

Ejemplo:

```text
-----------------------------------------------------
| Propiedades | Disponibles | Vendidas | Consultas |
|     142     |     108     |    18    |     24    |
-----------------------------------------------------

Últimas consultas

Cliente             Propiedad                Estado
-------------------------------------------------------
Carlos Pérez         Departamento Miraflores  Nueva
Lucía Torres         Casa Surco               Contactado
Mario López          Oficina San Isidro       Nueva
```

---

# 9. Gestión de propiedades

Este será uno de los módulos principales.

Ruta administrativa conceptual:

```text
/dashboard/properties
```

Funciones:

- Listar propiedades.
- Buscar propiedades.
- Filtrar propiedades.
- Crear propiedad.
- Editar propiedad.
- Eliminar propiedad.
- Publicar propiedad.
- Despublicar propiedad.
- Cambiar estado.
- Administrar fotografías.

---

# 10. Información de una propiedad

Cada propiedad debe almacenar como mínimo:

## Información general

- ID
- Código interno
- Título
- Slug
- Descripción corta
- Descripción completa

## Operación

- Venta
- Alquiler

## Tipo de inmueble

Ejemplos:

- Departamento
- Casa
- Terreno
- Oficina
- Local comercial
- Almacén
- Casa de playa
- Casa de campo
- Otro

## Precio

- Precio
- Moneda

Monedas iniciales:

- PEN
- USD

## Ubicación

- País
- Departamento / región
- Provincia
- Distrito
- Dirección
- Referencia
- Latitud
- Longitud

La dirección exacta podrá ocultarse públicamente cuando sea necesario.

---

# 11. Características de propiedad

La propiedad podrá registrar características como:

- Área total
- Área construida
- Dormitorios
- Baños
- Estacionamientos
- Antigüedad
- Número de pisos
- Piso donde se encuentra
- Ascensor
- Amoblado
- Mascotas permitidas

No todos los campos deben ser obligatorios.

Algunos tipos de propiedad pueden no utilizar ciertas características.

---

# 12. Comodidades / amenities

Cada propiedad podrá tener múltiples características adicionales.

Ejemplos:

- Piscina
- Gimnasio
- Terraza
- Jardín
- Parrilla
- Seguridad
- Portería
- Área de juegos
- Área común
- Sala de reuniones
- Depósito
- Lavandería
- Balcón

Estas características deben modelarse de forma reutilizable.

---

# 13. Fotografías

Cada propiedad puede tener múltiples fotografías.

Se debe permitir:

- Subir varias fotografías.
- Eliminar fotografías.
- Reordenarlas.
- Definir una fotografía principal.
- Guardar texto alternativo cuando corresponda.

Una propiedad debe tener una imagen de portada.

Modelo conceptual:

```text
Property
    |
    └── PropertyImages[]
```

---

# 14. Estados de una propiedad

Separar el estado comercial de la visibilidad pública.

## Estado comercial

```text
available
reserved
sold
rented
inactive
```

Equivalentes visuales:

- Disponible
- Reservado
- Vendido
- Alquilado
- Inactivo

## Estado de publicación

```text
draft
published
```

De esta forma una propiedad puede estar disponible comercialmente pero todavía no estar publicada.

---

# 15. Portal público

El portal público será accesible sin autenticación.

Secciones principales:

```text
/
├── Inicio
├── Propiedades
│   ├── Venta
│   └── Alquiler
├── Detalle de propiedad
├── Nosotros
└── Contacto
```

---

# 16. Página de propiedades

Ruta conceptual:

```text
/propiedades
```

Debe mostrar propiedades publicadas mediante cards.

Cada card puede mostrar:

- Fotografía principal.
- Título.
- Distrito.
- Tipo de propiedad.
- Venta / alquiler.
- Precio.
- Dormitorios.
- Baños.
- Área.
- Botón "Ver propiedad".

---

# 17. Buscador y filtros

El portal debe permitir filtrar propiedades.

Filtros iniciales:

- Venta / alquiler.
- Tipo de propiedad.
- Distrito.
- Precio mínimo.
- Precio máximo.
- Dormitorios.
- Baños.

Los filtros deben reflejarse en parámetros de URL cuando sea posible.

Ejemplo:

```text
/propiedades?operation=sale&district=miraflores&bedrooms=3
```

Esto facilitará compartir búsquedas y posteriormente trabajar SEO.

---

# 18. Detalle de propiedad

Ruta conceptual:

```text
/propiedades/{slug}
```

Debe mostrar:

- Galería de fotografías.
- Título.
- Código de propiedad.
- Precio.
- Tipo de operación.
- Descripción.
- Características.
- Amenities.
- Ubicación.
- Área.
- Dormitorios.
- Baños.
- Estacionamientos.
- Estado.
- Formulario de consulta.

---

# 19. Consultas de clientes

El visitante podrá enviar una consulta desde una propiedad.

Formulario:

- Nombre
- Teléfono
- Email
- Mensaje

Debe almacenar automáticamente:

- Propiedad consultada.
- Fecha.
- Hora.
- IP opcional.
- URL de origen.
- Estado de la consulta.

El usuario NO debe escribir qué propiedad está consultando.

El sistema debe asociarla automáticamente.

---

# 20. Estados de una consulta

Estados sugeridos:

```text
new
contacted
in_progress
closed
discarded
```

Interfaz:

- Nueva
- Contactado
- En seguimiento
- Cerrada
- Descartada

---

# 21. Bandeja de consultas

Ruta conceptual:

```text
/dashboard/inquiries
```

Listado:

| Campo | Descripción |
|---|---|
| Cliente | Nombre |
| Teléfono | Número |
| Email | Correo |
| Propiedad | Propiedad consultada |
| Fecha | Fecha de creación |
| Estado | Estado comercial |
| Responsable | Usuario interno |

Debe permitir:

- Buscar.
- Filtrar por estado.
- Filtrar por propiedad.
- Abrir consulta.
- Cambiar estado.
- Asignar responsable.
- Agregar notas internas.

---

# 22. Detalle de consulta

Ejemplo:

```text
CONSULTA #000152

Cliente
Carlos Pérez
987654321
carlos@email.com

Propiedad
Departamento moderno en Miraflores
Código: PROP-00124

Mensaje:
"Hola, quisiera saber si todavía está disponible."

Estado:
En seguimiento

Responsable:
María González

Fecha:
07/09/2026
```

Debe existir acceso directo desde la consulta hacia la propiedad.

---

# 23. Gestión de usuarios

Disponible únicamente para administradores.

Ruta:

```text
/dashboard/users
```

Funciones:

- Listar usuarios.
- Crear usuario.
- Editar usuario.
- Activar/desactivar usuario.
- Cambiar rol.

Campos:

- Nombre.
- Email.
- Contraseña.
- Rol.
- Estado.

---

# 24. Modelo de datos propuesto

## users

```text
id
name
email
password
role
is_active
created_at
updated_at
```

Roles iniciales:

```text
admin
assistant
```

---

## properties

```text
id
code
title
slug
short_description
description

operation_type
property_type

currency
price

country
region
province
district
address
reference
latitude
longitude
show_exact_address

total_area
built_area

bedrooms
bathrooms
parking_spaces
floors
floor_number
age_years

has_elevator
is_furnished
pets_allowed

commercial_status
publication_status

created_by
updated_by

published_at

created_at
updated_at
deleted_at
```

---

## property_images

```text
id
property_id
path
alt_text
position
is_cover
created_at
updated_at
```

Relación:

```text
Property hasMany PropertyImage
```

---

## amenities

```text
id
name
slug
icon
created_at
updated_at
```

---

## amenity_property

```text
property_id
amenity_id
```

Relación:

```text
Property belongsToMany Amenity
Amenity belongsToMany Property
```

---

## inquiries

```text
id
property_id

name
phone
email
message

status

assigned_to

source_url
ip_address

created_at
updated_at
```

Relaciones:

```text
Inquiry belongsTo Property

Inquiry belongsTo User
    through assigned_to
```

---

## inquiry_notes

```text
id
inquiry_id
user_id
note
created_at
updated_at
```

Permite registrar seguimiento interno.

---

# 25. Relaciones principales

```text
User
 ├── creates Properties
 ├── updates Properties
 ├── manages Inquiries
 └── creates InquiryNotes


Property
 ├── hasMany PropertyImages
 ├── belongsToMany Amenities
 └── hasMany Inquiries


Inquiry
 ├── belongsTo Property
 ├── belongsTo User (responsable)
 └── hasMany InquiryNotes
```

---

# 26. Estructura conceptual de Laravel

Se recomienda mantener una arquitectura sencilla y compatible con Laravel.

```text
app/
├── Actions/
├── Enums/
├── Http/
│   ├── Controllers/
│   │   ├── Dashboard/
│   │   └── Public/
│   ├── Middleware/
│   └── Requests/
├── Models/
├── Policies/
└── Services/
```

React:

```text
resources/js/
├── components/
├── layouts/
├── pages/
│
├── pages/dashboard/
│   ├── Dashboard.tsx
│   ├── Properties/
│   ├── Inquiries/
│   └── Users/
│
├── pages/public/
│   ├── Home.tsx
│   ├── Properties/
│   └── Contact.tsx
│
├── types/
└── utils/
```

Evitar crear capas arquitectónicas innecesarias durante el MVP.

---

# 27. Seguridad

Implementar:

- CSRF.
- Validación del backend.
- Form Requests.
- Policies.
- Autorización por roles.
- Protección de rutas.
- Escape de contenido.
- Restricción de tipos de archivos.
- Restricción del tamaño de imágenes.
- Rate limiting en formulario público.
- Protección contra spam básica.

La autorización nunca debe depender únicamente del frontend.

---

# 28. Validación de imágenes

Aceptar inicialmente:

```text
jpg
jpeg
png
webp
```

Definir un límite razonable de tamaño.

El sistema debe almacenar las imágenes utilizando Laravel Storage.

No almacenar archivos binarios dentro de MySQL.

---

# 29. SEO

Aunque es un MVP, la arquitectura debe permitir SEO para las propiedades.

Cada propiedad deberá tener:

- URL amigable.
- Título SEO.
- Meta description.
- Open Graph.
- Imagen principal.
- Canonical URL.

Ejemplo:

```text
https://tuinmueble.com/propiedades/departamento-en-venta-miraflores-3-dormitorios
```

Laravel debe entregar los metadatos necesarios desde el servidor mediante Inertia.

---

# 30. Responsive

Todo el sistema debe funcionar correctamente en:

- Desktop.
- Tablet.
- Mobile.

Prioridad especialmente alta para el portal público.

---

# 31. Funcionalidades fuera del MVP

NO implementar inicialmente:

## Agenda de visitas

Posteriormente permitirá:

- Programar visitas.
- Asignar asesor.
- Registrar fecha/hora.
- Registrar estado.
- Registrar observaciones.

---

## Recorridos de propiedades

Posteriormente podrán incorporarse:

- Video.
- Tour virtual.
- Recorrido 360°.

---

## Compartir propiedad en PDF

Posteriormente se podrá generar automáticamente una ficha PDF con:

- Logo.
- Fotografías.
- Información de la propiedad.
- Precio.
- Características.
- Datos de contacto.

---

## CRM de clientes

Segunda fase.

Permitirá consolidar personas interesadas aunque hayan realizado consultas sobre varias propiedades.

Modelo futuro:

```text
Client
 ├── hasMany Inquiries
 ├── hasMany Visits
 └── hasMany Notes
```

---

## Reportes

Segunda fase.

Ejemplos:

- Propiedades más consultadas.
- Consultas por periodo.
- Consultas por distrito.
- Consultas por tipo de propiedad.
- Rendimiento por asesor.
- Propiedades publicadas.
- Propiedades vendidas.
- Propiedades alquiladas.

---

# 32. Prioridad de implementación

## BLOQUE 1 — Base del proyecto

1. Inspeccionar estructura actual.
2. Confirmar versiones instaladas.
3. Configurar MySQL.
4. Revisar Laravel + React + Inertia.
5. Configurar TypeScript.
6. Definir layouts.
7. Crear migraciones base.

Al finalizar:

```bash
php artisan test
npm run build
```

---

# BLOQUE 2 — Autenticación y roles

Implementar:

- Login.
- Logout.
- Recuperación.
- Roles.
- Policies.
- Protección del dashboard.
- Usuarios.

Validar:

```text
Administrador → acceso completo.

Asistente → acceso operativo.

Visitante → sin acceso administrativo.
```

Ejecutar tests y build.

---

# BLOQUE 3 — Propiedades

Implementar:

- Modelo Property.
- Migraciones.
- CRUD.
- Imágenes.
- Amenities.
- Estados.
- Publicación.

Objetivo:

> El administrador debe poder crear una propiedad completa desde el dashboard.

Ejecutar tests y build.

---

# BLOQUE 4 — Portal público

Implementar:

- Home.
- Listado.
- Filtros.
- Cards.
- Detalle.
- Galería.
- Responsive.

Objetivo:

> Una propiedad creada y publicada desde el dashboard debe aparecer automáticamente en el portal público.

Ejecutar tests y build.

---

# BLOQUE 5 — Consultas

Implementar:

- Formulario público.
- Modelo Inquiry.
- Asociación con Property.
- Bandeja administrativa.
- Estados.
- Responsable.
- Notas.

Objetivo:

> Un visitante debe poder consultar una propiedad y el equipo debe visualizar inmediatamente esa consulta en el dashboard asociada a la propiedad correcta.

Este constituye el flujo principal del MVP.

Ejecutar tests y build.

---

# BLOQUE 6 — Dashboard

Agregar:

- KPIs.
- Propiedades recientes.
- Consultas recientes.
- Indicadores.

No retrasar el flujo principal por gráficos o visualizaciones avanzadas.

---

# 33. Flujo crítico que debe funcionar

Antes de considerar terminado el MVP debe funcionar esta prueba completa:

```text
1. Administrador inicia sesión.

2. Crea una propiedad.

3. Sube fotografías.

4. Define características.

5. Publica la propiedad.

6. Abre el portal público.

7. Encuentra la propiedad.

8. Abre su detalle.

9. Completa el formulario de consulta.

10. Envía la consulta.

11. Laravel valida la información.

12. Se crea Inquiry.

13. Inquiry queda asociada a Property.

14. Administrador abre el dashboard.

15. Visualiza la nueva consulta.

16. Accede al detalle.

17. Puede visualizar la propiedad consultada.

18. Cambia el estado a "Contactado".

19. Puede asignar un responsable.

20. Puede agregar una nota.
```

Si este flujo no funciona completamente, el MVP todavía no debe considerarse terminado.

---

# 34. Testing

Crear tests prioritariamente para flujos críticos.

## Authentication

```text
✓ usuario puede iniciar sesión
✓ usuario inválido no puede ingresar
✓ usuario no autenticado no puede acceder al dashboard
```

## Roles

```text
✓ administrador puede gestionar usuarios
✓ asistente no puede gestionar usuarios
✓ asistente puede gestionar propiedades
```

## Properties

```text
✓ administrador puede crear propiedad
✓ asistente puede crear propiedad
✓ propiedad draft no aparece públicamente
✓ propiedad published aparece públicamente
✓ propiedad puede tener múltiples imágenes
```

## Inquiries

```text
✓ visitante puede crear consulta
✓ consulta requiere propiedad válida
✓ consulta queda relacionada con propiedad
✓ administrador puede visualizar consultas
✓ asistente puede visualizar consultas
✓ usuario puede actualizar estado
```

---

# 35. Seeders

Crear información inicial para desarrollo.

Roles:

```text
admin
assistant
```

Usuario administrador de desarrollo.

Crear también:

- PropertyFactory
- InquiryFactory
- UserFactory

Y un conjunto de propiedades ficticias para poder probar visualmente el portal.

Nunca dejar credenciales inseguras de desarrollo en producción.

---

# 36. Criterios de aceptación del MVP

El MVP estará terminado cuando:

- Existe autenticación funcional.
- Existen roles administrador y asistente.
- Se pueden gestionar usuarios.
- Se pueden crear propiedades.
- Se pueden editar propiedades.
- Se pueden subir varias fotografías.
- Se puede publicar/despublicar una propiedad.
- El portal solamente muestra propiedades publicadas.
- Se pueden filtrar propiedades.
- Existe página individual de propiedad.
- El cliente puede enviar una consulta.
- La consulta queda asociada a la propiedad.
- La consulta aparece en el dashboard.
- Se puede cambiar su estado.
- Se puede asignar un responsable.
- El sistema funciona responsive.
- Las validaciones funcionan.
- Las políticas de autorización funcionan.
- Los tests críticos pasan.
- `npm run build` termina sin errores.
- No existen errores de TypeScript.
- No existen errores importantes en consola.

---

# 37. Restricciones para el desarrollo

Durante el MVP:

1. No implementar funcionalidades que no estén descritas en esta ficha salvo que sean necesarias técnicamente.

2. No implementar agenda de visitas todavía.

3. No implementar CRM completo todavía.

4. No implementar generación PDF todavía.

5. No implementar reportes avanzados todavía.

6. No sobrearquitecturar.

7. Priorizar Laravel nativo siempre que exista una solución adecuada.

8. Mantener TypeScript correctamente tipado.

9. Evitar `any` salvo casos justificados.

10. Mantener las reglas de autorización en backend.

11. Mantener migraciones reversibles.

12. Crear índices de base de datos donde sean necesarios.

13. Evitar consultas N+1 utilizando eager loading.

14. Mantener componentes React reutilizables sin crear abstracciones prematuras.

15. Ejecutar tests después de cada bloque.

16. Ejecutar build después de cada bloque.

---

# 38. Instrucciones para el agente de desarrollo

Antes de comenzar a modificar código:

1. Inspecciona todo el proyecto existente.

2. Identifica:
   - versión de Laravel;
   - versión de PHP;
   - versión de React;
   - versión de Inertia;
   - configuración de TypeScript;
   - sistema de autenticación existente;
   - estructura actual;
   - migraciones existentes;
   - modelos existentes;
   - dependencias instaladas.

3. No reemplaces funcionalidades existentes que ya resuelvan correctamente algún requerimiento.

4. Compara el proyecto encontrado contra esta ficha.

5. Propón las migraciones y relaciones necesarias.

6. Presenta un plan corto por bloques.

7. Después comienza la implementación.

Orden obligatorio:

```text
Autenticación
    ↓
Roles y permisos
    ↓
Propiedades
    ↓
Imágenes y características
    ↓
Portal público
    ↓
Consultas
    ↓
Dashboard
    ↓
Módulos secundarios
```

Después de cada bloque:

```bash
php artisan test
npm run build
```

Corrige cualquier error antes de avanzar.

No considerar un bloque terminado mientras los tests o el build estén fallando.

---

# 39. Principio principal del proyecto

La prioridad absoluta es conseguir que este flujo funcione:

> **PUBLICAR PROPIEDAD → MOSTRAR PROPIEDAD → CLIENTE CONSULTA → CONSULTA LLEGA AL DASHBOARD**

Todo desarrollo que no contribuya directamente a este flujo debe considerarse secundario durante el MVP.

---

# 40. Evolución futura

Una vez estabilizado el MVP, la plataforma podrá evolucionar hacia un sistema inmobiliario más completo:

```text
Portal inmobiliario
        ↓
CRM inmobiliario
        ↓
Agenda de visitas
        ↓
Gestión de asesores
        ↓
Seguimiento comercial
        ↓
PDF de propiedades
        ↓
Tours virtuales
        ↓
Reportes comerciales
        ↓
Automatizaciones
```

La arquitectura del MVP debe permitir esta evolución sin implementar anticipadamente esos módulos.