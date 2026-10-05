# Plan 002 - Frontera de catalogo: drafts, publicacion y sesion

Plan tecnico **as-built** de `spec.md`. El refactor no cambio el contrato HTTP:
centralizo en `common` los clientes, puertos, DTOs, errores y contratos de los
servicios externos para que `identity`, `catalog` y futuros modulos compartan una
sola frontera por servicio.

## 1. Alcance y principios

- `catalog` sigue siendo la capacidad que expone `/panel/catalog`; no persiste ni
  valida productos, etapas, dueños o imagenes. **(RF-1, RF-16, RF-18)**
- La sesion se resuelve antes de llamar a catalogo y el dueño autenticado se
  envia como `ownerAccountId` autoritativo. **(RF-2, RF-4, RF-17)**
- `common` es dueño de las fronteras reutilizables hacia `account-api` y
  `catalog-api`: contratos, puertos, DTOs, errores y clientes HTTP.
- `identity` conserva API, navegacion, casos de uso y su DTO de presentacion
  `LogoutPanelSessionResult`; no posee adaptadores ni contratos remotos.
- `catalog` conserva API y casos de uso; no posee adaptadores, puertos, DTOs de
  servicio, constantes de cookie ni errores de disponibilidad.
- `SESSION_COOKIE_NAME` tiene una unica definicion en
  `common/contracts/account_api.py`.
- Las dependencias apuntan a abstracciones comunes: API y casos de uso de los
  modulos usan `common.ports`, `common.dtos` y `common.errors`; la composicion
  crea los clientes concretos.
- El cuerpo y `Content-Type` de create/update se reenvian sin interpretarlos; el
  publish vacio se normaliza a `{}` JSON. **(RF-18, RF-24, RF-25)**
- Las rutas de identidad, CORS y health permanecen sin cambios. **(RF-19, RF-20)**
- No hay modelos ni migraciones nuevas.

## 2. Layout as-built

```text
src/
|-- config/
|-- common/
|   |-- contracts/
|   |   |-- account_api.py          # paths, claves y unica SESSION_COOKIE_NAME
|   |   `-- catalog_api.py          # paths, ownerAccountId y name
|   |-- dtos/
|   |   |-- account_session.py      # AccountSession
|   |   |-- account_logout.py       # AccountLogout
|   |   `-- service_response.py     # ServiceResponse
|   |-- errors/
|   |   |-- account_api_unavailable.py
|   |   `-- catalog_api_unavailable.py
|   |-- ports/
|   |   |-- account_api_gateway.py  # AccountApiGateway
|   |   `-- catalog_api_gateway.py  # CatalogApiGateway
|   |-- infrastructure/
|   |   |-- client_factory.py       # composition root: settings -> clients comunes
|   |   `-- clients/
|   |       |-- account_api_client.py   # AccountApiClient: session + logout
|   |       `-- catalog_api_client.py   # CatalogApiClient: operaciones de catalogo
|   |-- health/
|   |-- http.py
|   `-- json_types.py
|-- identity/
|   |-- api/                        # sesion, logout, cookies y URLs
|   |-- navigation/                 # redirect de Google y return_to seguro
|   |-- use_cases/                  # resolve y logout de sesion
|   |-- dtos/
|   |   `-- logout_panel_session_result.py
|   `-- domain/                     # constantes propias de presentacion/cookie
`-- catalog/
    |-- api/
    |   |-- panel_session.py         # guard tipado solo con common
    |   |-- urls.py
    |   `-- views/
    `-- use_cases/                  # resolve owner y operaciones de catalogo

tests/
|-- common/
|   |-- test_account_api_client.py
|   |-- test_catalog_api_client.py
|   `-- test_http.py
|-- identity/                       # casos de uso con fake AccountApiGateway
|-- catalog/                        # casos de uso/API con fakes de puertos comunes
`-- integration/                    # contrato HTTP de la frontera
```

No existen clientes debajo de `identity` ni `catalog`. Tampoco existen paquetes
de puertos o infraestructura propios de esos modulos.

## 3. Capas y dependencias

| Capa | Responsabilidad | Dependencias permitidas |
|---|---|---|
| `common.contracts` | Nombres externos, paths, cookie y claves de payload | Ninguna capa de aplicacion |
| `common.dtos` | Datos neutrales devueltos por servicios | `common.json_types` cuando aplica |
| `common.ports` | Protocols reutilizables por servicio | `common.dtos` |
| `common.errors` | Fallos tipados de disponibilidad por servicio | Ninguna capa de modulo |
| `common.infrastructure.clients` | HTTP, parseo y traduccion de errores | contracts, DTOs, errors y `common.http` |
| `common.infrastructure.client_factory` | Compone clientes desde settings | `common.infrastructure.clients`, `common.ports`, settings |
| `identity.use_cases` | Resolver sesion y adaptar logout al panel | puertos, DTOs y errores comunes |
| `catalog.use_cases` | Orquestar operaciones sin conocer HTTP | puertos y DTOs comunes |
| `identity.api` | Componer cuentas y presentar respuestas/cookies | casos de uso + frontera comun |
| `catalog.api` | Componer cuentas/catalogo, autenticar y presentar | casos de uso + frontera comun |

Flujo de dependencia:

```text
identity.api -----> identity.use_cases -----> common.ports/common.dtos
      |                                            ^
      `--> common.infrastructure.client_factory ---> common.infrastructure.clients

catalog.api ------> catalog.use_cases ------> common.ports/common.dtos
      |                                            ^
      `--> common.infrastructure.client_factory ---> common.infrastructure.clients
```

`common/infrastructure/client_factory.py` construye `AccountApiClient` y
`CatalogApiClient` (tipados como `AccountApiGateway`/`CatalogApiGateway`) desde
settings. `identity.api.views.panel_session` y `PanelSessionGuardMixin` obtienen
sus gateways con esa factory e importan exclusivamente de `common` la cookie,
puertos, DTO de respuesta y errores externos.

## 4. Archivos del refactor

| Archivo | Estado as-built |
|---|---|
| `common/contracts/account_api.py` | Unica fuente de `SESSION_COOKIE_NAME`; conserva paths y claves auth/id |
| `common/dtos/account_session.py` | `AccountSession`: status, body, authenticated y account_id |
| `common/dtos/account_logout.py` | `AccountLogout`: status, body y si habia sesion activa |
| `common/dtos/service_response.py` | Respuesta neutral status/body para catalogo |
| `common/errors/account_api_unavailable.py` | Error comun de indisponibilidad de cuentas |
| `common/errors/catalog_api_unavailable.py` | Error comun de indisponibilidad de catalogo |
| `common/ports/account_api_gateway.py` | Protocol compartido `get_session` + `logout` |
| `common/ports/catalog_api_gateway.py` | Protocol compartido de las siete operaciones |
| `common/infrastructure/clients/account_api_client.py` | Cliente unico de cuentas |
| `common/infrastructure/clients/catalog_api_client.py` | Cliente unico de catalogo |
| `common/infrastructure/client_factory.py` | Compone ambos clientes desde settings |
| `identity/dtos/logout_panel_session_result.py` | Unico DTO especifico conservado por identity |
| `catalog/api/panel_session.py` | Guard desacoplado de implementaciones concretas |

## 5. Clientes comunes

| Cliente | Puerto | Retorno | Responsabilidad | Error |
|---|---|---|---|---|
| `AccountApiClient` | `AccountApiGateway` | `AccountSession`, `AccountLogout` | Session y logout, cookie compartida, parseo de `authenticated`/`id` | `AccountApiUnavailable` |
| `CatalogApiClient` | `CatalogApiGateway` | `ServiceResponse` | Filtro `name`, owner query autoritativo, body/Content-Type y publish | `CatalogApiUnavailable` |

`AccountApiClient` se comparte entre identity, catalog y futuros consumidores.
Envia `Cookie: fes_session=...` solo cuando hay valor y convierte fallos de
`common.http` al error comun de cuentas.

`CatalogApiClient` agrega siempre `ownerAccountId` desde la sesion, agrega `name`
solo si tiene valor, preserva multipart incluido su boundary y propaga respuestas
2xx/4xx como `ServiceResponse`. Red, payload remoto invalido o 5xx se traducen al
error comun de catalogo. **(RF-4, RF-13, RF-15, RF-17, RF-22, RF-23, RF-24)**

## 6. Contratos HTTP conservados

| Panel | Llamada interna principal | RF |
|---|---|---|
| `GET /panel/catalog/products` | `GET /catalog/products?ownerAccountId={id}[&name=...]` | RF-5, RF-23 |
| `POST /panel/catalog/products` | `POST /catalog/products?ownerAccountId={id}` | RF-6, RF-24 |
| `PUT /panel/catalog/products/{id}` | `PUT /catalog/products/{id}?ownerAccountId={id}` | RF-7, RF-24 |
| `DELETE /panel/catalog/products/{id}` | `DELETE /catalog/products/{id}?ownerAccountId={id}` | RF-8 |
| `POST .../{id}/publish` | `POST /catalog/products/{id}/publish?ownerAccountId={id}` | RF-9 |
| `POST .../{id}/unpublish` | `POST /catalog/products/{id}/unpublish?ownerAccountId={id}` | RF-10 |
| `POST /panel/catalog/publish` | `POST /catalog/publish?ownerAccountId={id}` | RF-11, RF-25 |

- Sin sesion valida: 401 y ninguna llamada a catalogo. **(RF-2, RF-3)**
- Cuentas no disponible: 503 y ninguna llamada a catalogo. **(RF-14)**
- Catalogo 2xx/4xx: mismo estado y cuerpo. **(RF-13, RF-22)**
- Catalogo no disponible/5xx: 503. **(RF-15)**
- `request.META["CONTENT_TYPE"]` conserva el boundary multipart. **(RF-24)**
- Publish sin cuerpo envia `b"{}"` como `application/json`. **(RF-25)**
- Login conserva `return_to` seguro basado en `PANEL_PUBLIC_ORIGIN`. **(RF-26, RF-27)**

## 7. Configuracion

| Variable | Consumidor |
|---|---|
| `ACCOUNT_API_BASE_URL` | `AccountApiClient` compuesto por identity/catalog |
| `ACCOUNT_API_TIMEOUT_SECONDS` | Timeout comun de cuentas |
| `CATALOG_API_BASE_URL` | `CatalogApiClient` compuesto por catalog |
| `CATALOG_API_TIMEOUT_SECONDS` | Timeout comun de catalogo |
| `PANEL_PUBLIC_ORIGIN` | CORS y `return_to` |
| `ACCOUNTS_PUBLIC_BASE_URL` | Redirect publico de login |

## 8. Tests as-built

| Ubicacion | Cobertura |
|---|---|
| `tests/common/test_account_api_client.py` | Session, logout, cookie, auth/id, DTOs y `AccountApiUnavailable` |
| `tests/common/test_catalog_api_client.py` | Paths, owner, `name`, multipart, publish, `ServiceResponse` y `CatalogApiUnavailable` |
| `tests/common/test_http.py` | Body/Content-Type, 2xx/4xx, 5xx/red y JSON |
| `tests/identity/test_ports.py` | Fakes conformes a `AccountApiGateway` comun |
| `tests/identity/test_use_cases.py` | Resolucion y logout con DTOs/errores comunes; resultado local de logout |
| `tests/catalog/test_ports.py` | Fakes conformes a los dos puertos comunes |
| `tests/catalog/test_use_cases.py` | Operaciones con `AccountSession` y `ServiceResponse` |
| `tests/catalog/test_panel_session_guard.py` | 401/503, owner y errores comunes |
| `tests/catalog/test_panel_catalog_product_viewset.py` | Operaciones, name, multipart y proxy de respuesta |
| `tests/catalog/test_panel_catalog_publish_view.py` | Publish, cuerpo JSON default y conteo cero |
| `tests/integration/` | Rutas, CORS, health y frontera completa con fakes comunes |

Verificacion del corte: `make verify` verde, **112 tests**, sin migraciones.

## 9. Mapa RF

| RF | Entregable as-built |
|---|---|
| RF-1 | URLs y views en `catalog.api` |
| RF-2, RF-3 | Guard + `AccountApiGateway.get_session` |
| RF-4, RF-17 | Owner autoritativo en `CatalogApiClient` |
| RF-5 - RF-11 | Casos de uso de catalogo + `CatalogApiGateway` |
| RF-12 | Settings + composition root de catalogo |
| RF-13, RF-22 | `ServiceResponse` comun y proxy de API |
| RF-14 | `AccountApiUnavailable` comun |
| RF-15 | `CatalogApiUnavailable` comun |
| RF-16 | Modulo sin modelos ni migraciones |
| RF-18 | Reenvio opaco mediante cliente/HTTP comunes |
| RF-19, RF-20 | Health y CORS conservados |
| RF-21 | Publish con cero propagado como 200 |
| RF-23 | `name` en puerto y cliente comunes |
| RF-24 | Body y Content-Type multipart preservados |
| RF-25 | `{}` JSON por defecto en view de publish |
| RF-26, RF-27 | Navegacion segura conservada en identity |

## 10. Fuera de alcance

- Cambiar rutas, estados o cuerpos HTTP de la spec.
- Persistir o validar datos de catalogo en panel.
- Crear autenticacion, modelos o migraciones.
- Duplicar clientes o contratos externos dentro de modulos de negocio.
