# Plan 002 — Frontera de catálogo: drafts, publicación y sesión

Plan técnico de implementación de `specs/002-feat-panel-catalog-frontier/spec.md`.
Respeta `AGENTS.md` y las skills `python-clean-code`, `panel-api-architecture`,
`django-patterns` y `clean-architecture`. Reutiliza el patrón de frontera de
identidad ya presente en `src/identity` (contratos remotos en
`src/common/contracts`, HTTP en `src/common/http.py`) y añade un módulo nuevo
`catalog` sin persistir productos ni añadir tablas.

## 1. Alcance y principios

- Capacidad dueña: **catalog** (frontera `/panel/catalog` hacia `catalog-api`).
- El panel **no** es fuente de verdad de productos, etapas, dueños ni imágenes;
  solo valida la sesión, fija el dueño y reenvía. **(RF-16)**
- No hay modelos ni migraciones nuevas; la base `panel` no cambia. **(RF-16)**
- Se conservan sin cambio de contrato las rutas de sesión bajo `/panel/identity`,
  los health checks `GET /health/live` y `GET /health/ready`, y CORS con
  credenciales. **(RF-19, RF-20)**
- La frontera **no** valida campos de dominio del producto (moneda, precio,
  imágenes); solo valida HTTP y sesión. **(RF-18)**
- Dependencias hacia dentro: `api → use_cases/ports/dtos → domain`; los clientes
  HTTP de cuentas y catálogo viven en `infrastructure` e implementan sendos
  puertos de `ports`.
- La sesión se resuelve **antes** de reenviar; sin sesión no hay reenvío. **(RF-2, RF-3)**

## 2. Ubicación del código (layout objetivo)

Todo el runtime Django vive bajo `src/` (`PYTHONPATH` incluye `src`):

```text
src/
├── config/                      # settings, urls (sin cambios de layout)
├── common/
│   ├── contracts/
│   │   ├── account_api.py       # existente: paths de /accounts
│   │   └── catalog_api.py       # NUEVO: paths y claves de /catalog
│   ├── health/views.py          # live / ready (sin cambios)
│   └── http.py                  # ampliado con body/content_type
├── identity/                    # existente, sin cambios de contrato
└── catalog/                     # NUEVO módulo (frontera)
    ├── apps.py
    ├── api/
    │   ├── panel_session.py     # mixin/guard de sesión de la frontera
    │   ├── urls.py              # rutas /panel/catalog
    │   └── views/
    │       ├── panel_catalog_products.py   # ViewSet de productos
    │       └── panel_catalog_publish.py    # APIView de publicar catálogo
    ├── use_cases/               # una función por operación
    ├── ports/                   # PanelSessionGateway, CatalogGateway
    ├── dtos/                    # PanelSession, CatalogResponse
    ├── domain/
    │   ├── constants.py
    │   └── errors/              # SessionServiceUnavailable, CatalogServiceUnavailable
    └── infrastructure/
        ├── account_session_client.py   # resuelve fes_session
        └── catalog_api_client.py       # reenvía a CATALOG_API_BASE_URL
tests/
├── catalog/                   # unitarios de use cases/dtos/infra
└── integration/               # flujos HTTP /panel/catalog con account/catalog mock
```

- `catalog` se registra en `INSTALLED_APPS`.
- `config/urls.py` monta `path("panel/catalog/", include("catalog.api.urls"))`
  además de las rutas existentes. **(RF-1, RF-19)**

## 3. Configuración por entorno

En `config/settings.py` (variables de entorno, sin secretos en código):

| Variable | Uso | RF |
|---|---|---|
| `CATALOG_API_BASE_URL` | Base interna del servicio de catálogo | **RF-12** |
| `CATALOG_API_TIMEOUT_SECONDS` | Timeout del cliente de catálogo (default `5`) | — |
| `ACCOUNT_API_BASE_URL` | Base interna del servicio de cuentas (ya existente) | **RF-2, RF-14** |
| `ACCOUNT_API_TIMEOUT_SECONDS` | Timeout del cliente de cuentas (ya existente) | — |
| `PANEL_PUBLIC_ORIGIN` | Único origen CORS con credenciales (ya existente) | **RF-20** |

Notas:

- `CATALOG_API_BASE_URL` se normaliza con `rstrip("/")` como ya hace
  `ACCOUNT_API_BASE_URL`.
- No se añaden dependencias nuevas: el HTTP cliente sigue con `urllib` en
  `common.http`.

## 4. Contratos HTTP

### 4.1 Contrato del panel (`panel-web` → `panel-api`)

Cookie `fes_session` obligatoria; todos requieren sesión. **(RF-1, RF-3)**

| Método y path | Operación | RF |
|---|---|---|
| `GET /panel/catalog/products` | Listar productos de la cuenta | **RF-5** |
| `POST /panel/catalog/products` | Crear draft con dueño | **RF-6** |
| `PUT /panel/catalog/products/{id}` | Actualizar producto | **RF-7** |
| `DELETE /panel/catalog/products/{id}` | Eliminar producto | **RF-8** |
| `POST /panel/catalog/products/{id}/publish` | Publicar producto | **RF-9** |
| `POST /panel/catalog/products/{id}/unpublish` | Despublicar producto | **RF-10** |
| `POST /panel/catalog/publish` | Publicar el catálogo visible | **RF-11** |

El cuerpo de `POST`/`PUT` se reenvía tal cual (JSON o `multipart/form-data`);
la frontera no lo interpreta ni valida. **(RF-18)**

### 4.2 Contrato interno (`panel-api` → `catalog-api`)

Base `CATALOG_API_BASE_URL`. La frontera propaga la cuenta de la sesión como
`ownerAccountId` **en query string**, param autoritativo que `catalog-api`
prioriza sobre cualquier valor del cuerpo; así se sobrescribe sin parsear el
cuerpo. **(RF-4, RF-17)**

| Llamada interna | RF |
|---|---|
| `GET /catalog/products?ownerAccountId={id}` | **RF-5** |
| `POST /catalog/products?ownerAccountId={id}` | **RF-6** |
| `PUT /catalog/products/{id}?ownerAccountId={id}` | **RF-7** |
| `DELETE /catalog/products/{id}?ownerAccountId={id}` | **RF-8** |
| `POST /catalog/products/{id}/publish?ownerAccountId={id}` | **RF-9** |
| `POST /catalog/products/{id}/unpublish?ownerAccountId={id}` | **RF-10** |
| `POST /catalog/publish?ownerAccountId={id}` (cuerpo con los productos sin dueño visibles) | **RF-11** |

Claves y paths como constantes en `src/common/contracts/catalog_api.py`:

```python
CATALOG_PRODUCTS_PATH = "/catalog/products"
CATALOG_PRODUCT_ITEM_PATH = "/catalog/products/{product_id}"
CATALOG_PRODUCT_PUBLISH_PATH = "/catalog/products/{product_id}/publish"
CATALOG_PRODUCT_UNPUBLISH_PATH = "/catalog/products/{product_id}/unpublish"
CATALOG_PUBLISH_PATH = "/catalog/publish"
OWNER_ACCOUNT_ID_QUERY_PARAM = "ownerAccountId"
OWNER_ACCOUNT_ID_KEY = "ownerAccountId"
```

En `src/common/contracts/account_api.py` se añaden las claves de lectura de la
sesión: `SESSION_AUTHENTICATED_KEY = "authenticated"` y `SESSION_ID_KEY = "id"`.

### 4.3 `common.http` — reenvío con cuerpo

`JsonRequest` se amplía con `body: bytes | None = None` y
`content_type: str | None = None`; `_read_body` adjunta `data=body` y la
cabecera `Content-Type` cuando corresponda. Se mantiene el comportamiento actual:

- Respuestas 2xx/4xx devuelven `(status_code, body_dict)`.
- 5xx, timeout, red o JSON no usable lanzan `RemoteServiceError`.
- Cuerpo vacío se normaliza a `{}`.

Con esto, `catalog_api_client` puede reenviar el cuerpo sin conocer su formato.
**(RF-18, RF-22)**

## 5. Reutilización de la frontera de identidad

La frontera de catálogo repite el patrón de `identity`, sin acoplarse a sus
internos:

- Puertos propios en `catalog/ports` e implementaciones en
  `catalog/infrastructure`.
- Uso de `common.contracts.account_api` y `common.http`, igual que
  `identity.infrastructure.AccountSessionClient`.
- Los errores se mapean a errores de dominio de `catalog` y a los mismos shapes
  `{"error","message"}` usados por identidad: `no_autenticado` (401) y
  `servicio_no_disponible` (503). **(RF-3, RF-14, RF-15)**

`catalog` no importa `identity.api`, `identity.infrastructure` ni
`identity.use_cases`; si en el futuro se consolida la resolución de sesión en
`common`, será otro corte.

## 6. Capas internas (clean architecture)

### 6.1 Domain — **RF-16**

- `catalog/domain/constants.py`: `SESSION_COOKIE_NAME = "fes_session"`.
- `catalog/domain/errors/session_service_unavailable.py`:
  `SessionServiceUnavailable` (mapea a 503 por caída de cuentas).
- `catalog/domain/errors/catalog_service_unavailable.py`:
  `CatalogServiceUnavailable` (mapea a 503 por caída de catálogo).
- Sin Django, DRF, settings ni HTTP; sin entidades persistidas.

### 6.2 Use cases, ports y DTOs — **RF-2 … RF-11, RF-13, RF-21, RF-22**

Puertos:

- `PanelSessionGateway.resolve(fes_session) -> PanelSession`.
- `CatalogGateway` con un método por operación (`list_products`,
  `create_product`, `update_product`, `delete_product`, `publish_product`,
  `unpublish_product`, `publish_catalog`), todos recibiendo `owner_account_id`
  y devolviendo `CatalogResponse`.

DTOs (un archivo por clase en `catalog/dtos/`):

- `PanelSession(authenticated: bool, account_id: str | None)`.
- `CatalogResponse(status_code: int, body: dict[str, Any])`.

Casos de uso (una función por archivo en `catalog/use_cases/`):

1. `resolve_panel_owner(session_gateway, fes_session) -> PanelSession` —
   traduce fallo de infra a `SessionServiceUnavailable`. **(RF-2, RF-3, RF-14)**
2. `list_products(catalog_gateway, owner) -> CatalogResponse` **(RF-5, RF-13)**
3. `create_product(catalog_gateway, owner, body, content_type)` **(RF-6, RF-22)**
4. `update_product(catalog_gateway, owner, product_id, body, content_type)` **(RF-7)**
5. `delete_product(catalog_gateway, owner, product_id)` **(RF-8)**
6. `publish_product(catalog_gateway, owner, product_id)` **(RF-9)**
7. `unpublish_product(catalog_gateway, owner, product_id)` **(RF-10)**
8. `publish_catalog(catalog_gateway, owner, body, content_type)` — el conjunto
   lo define el cuerpo (sin dueño) + los draft del dueño. **(RF-11, RF-21)**

Los casos de uso no importan DRF, Django HTTP ni clientes concretos; reciben los
puertos por parámetro (como `resolve_panel_session` en identidad).

### 6.3 Infrastructure — **RF-2, RF-4, RF-12 … RF-15, RF-17, RF-22**

- `AccountSessionClient(base_url, timeout_seconds)`:
  - `GET {ACCOUNT_API_BASE_URL}/accounts/session` con `Cookie: fes_session=...`.
  - `authenticated` y `id` desde el cuerpo (`common.contracts.account_api`).
  - `RemoteServiceError` → `SessionServiceUnavailable`.
- `CatalogApiClient(base_url, timeout_seconds)`:
  - Construye cada path de `common.contracts.catalog_api` e **inyecta siempre**
    `ownerAccountId` de la sesión como query param; ignora el del cliente.
    **(RF-4, RF-17)**
  - Reenvía `body`/`content_type` sin interpretarlos. **(RF-18)**
  - `RemoteServiceError` → `CatalogServiceUnavailable`; el resto devuelve
    `CatalogResponse(status_code, body)`. **(RF-13, RF-22)**

### 6.4 API (DRF) — **RF-1, RF-3, RF-5 … RF-15, RF-19, RF-21, RF-22**

- `api/panel_session.py`: mixin/base que, en `dispatch`, resuelve la sesión con
  `_session_gateway()`:
  - `SessionServiceUnavailable` → `503` `{"error":"servicio_no_disponible","message":"..."}`. **(RF-14)**
  - `PanelSession.authenticated` falso → `401` `{"error":"no_autenticado","message":"..."}`. **(RF-3)**
  - Si es válida, guarda `self.owner_account_id` y continúa. **(RF-4)**
- `PanelCatalogProductViewSet` (`ViewSet`) con acciones `list`, `create`,
  `update`, `destroy`, `publish`, `unpublish`; mapeo manual con `as_view({...})`
  para conservar las rutas del contrato. **(RF-5 … RF-10)**
- `PanelCatalogPublishView` (`APIView`) para `POST /panel/catalog/publish`.
  **(RF-11, RF-21)**
- Todas `permission_classes = [AllowAny]` y `authentication_classes = []`: la
  autorización la hace el guard de sesión, no DRF. Sin sesión → 401. **(RF-3)**
- `CatalogServiceUnavailable` → `503` `{"error":"servicio_no_disponible","message":"..."}`. **(RF-15)**
- En operaciones con `{id}`, el `id` se reenvía sin validarlo contra catálogo;
  la respuesta de `catalog-api` decide. **(RF-13, RF-22)**

### 6.5 Rutas — **RF-1, RF-19**

En `catalog/api/urls.py`, mapeo manual (sin router) para conservar el contrato:

```text
catalog/products                          GET list / POST create
catalog/products/<str:product_id>         PUT update / DELETE destroy
catalog/products/<str:product_id>/publish  POST publish
catalog/products/<str:product_id>/unpublish POST unpublish
catalog/publish                            POST publicar catálogo
```

`config/urls.py` las incluye bajo `panel/catalog/` y conserva health y
`panel/identity/`.

## 7. Manejo de errores y códigos — **RF-13, RF-14, RF-15, RF-21, RF-22**

| Origen | Resultado de la frontera |
|---|---|
| Sin cookie o sesión no autenticada | `401` `{"error":"no_autenticado","message":"..."}` |
| Cuentas inalcanzable / 5xx | `503` `{"error":"servicio_no_disponible","message":"..."}` sin reenviar |
| Catálogo inalcanzable / 5xx | `503` `{"error":"servicio_no_disponible","message":"..."}` |
| Catálogo 4xx | mismo estado y cuerpo de `catalog-api` |
| Catálogo 2xx | mismo estado y cuerpo de `catalog-api` |
| `publish` sin productos | `200` con 0 publicados (lo decide `catalog-api`) |

## 8. CORS y health — **RF-19, RF-20**

- `corsheaders` y `CORS_ALLOW_CREDENTIALS`/`CORS_ALLOWED_ORIGINS` ya configurados
  cubren `/panel/catalog/...` sin cambios.
- `GET /health/live` y `GET /health/ready` permanecen en `common.health`.

## 9. Qué no hacer (fuera de alcance de la spec)

- Persistir productos, etapas, dueños o imágenes en `panel`. **(RF-16)**
- Validar moneda, precio, stock o imágenes (lo hace `catalog-api`). **(RF-18)**
- Llamar a MinIO o gestionar imágenes.
- Crear el modelo Shop o autenticación nueva.
- Exponer `GET /catalog` de publicados para el market.
- Tocar el contrato de `identity` o sus rutas.

## 10. Pruebas (cobertura por RF)

| Área | Qué verificar | RF |
|---|---|---|
| Sin sesión | 401 con `no_autenticado` y sin llamada a catálogo | **RF-2, RF-3** |
| Cuentas caído | 503 `servicio_no_disponible` y sin reenvío | **RF-14** |
| Listar | `GET /catalog/products?ownerAccountId=` con la cuenta de la sesión | **RF-5** |
| Crear/editar | Reenvío de cuerpo y dueño de la sesión | **RF-6, RF-7, RF-18** |
| Eliminar | `DELETE /catalog/products/{id}?ownerAccountId=` | **RF-8** |
| Publicar/despublicar | `POST .../publish` y `.../unpublish` con dueño | **RF-9, RF-10** |
| Publicar catálogo | Cuerpo reenviado + dueño; 200 con 0 cuando no hay productos | **RF-11, RF-21** |
| Error 4xx | Mismo estado y cuerpo de catálogo | **RF-13, RF-22** |
| Error 5xx | 503 con shape propio | **RF-15** |
| Dueño del cliente | Se ignora y se usa el de la sesión | **RF-4, RF-17** |
| Sin persistencia | No hay modelo/migración en `catalog` | **RF-16** |
| CORS/health/rutas | Preflight con credenciales, health y rutas resuelven | **RF-1, RF-19, RF-20** |

Criterios de automatización:

- Unitarios de use cases/domain con gateways fake.
- Unitarios de `catalog_api_client` contra servidor mock (paths, query param de
  dueño y reenvío de cuerpo).
- Integración DRF/`APIClient` con mocks de cuentas y catálogo.
- Ejecutar `make verify` al cerrar la implementación.

## 11. Orden de implementación sugerido

1. `common/contracts/catalog_api.py`, claves de sesión en
   `common/contracts/account_api.py` y `common.http` con `body`/`content_type`
   (**RF-12, RF-18**).
2. Settings `CATALOG_API_BASE_URL`/timeout y registro de `catalog` (**RF-12**).
3. Domain, DTOs y puertos (**RF-3, RF-14, RF-15**).
4. Casos de uso de reenvío y de sesión (**RF-2 … RF-11, RF-13, RF-21, RF-22**).
5. Clientes de cuentas y catálogo (**RF-2, RF-4, RF-12, RF-14, RF-15, RF-17, RF-22**).
6. Vistas, guard de sesión y rutas `/panel/catalog/...` (**RF-1, RF-3 … RF-15, RF-19**).
7. Matriz de tests y `make verify` (**RF-1 … RF-22**).

## 12. Mapa resumen RF → entregable

| RF | Entregable principal |
|---|---|
| RF-1 | Rutas `/panel/catalog/...` en `catalog.api.urls` |
| RF-2 | Resolución de `fes_session` antes de reenviar |
| RF-3 | 401 `no_autenticado` sin reenvío |
| RF-4 | `ownerAccountId` de la sesión en el reenvío |
| RF-5 | `GET /catalog/products?ownerAccountId=` |
| RF-6 | `POST /catalog/products?ownerAccountId=` |
| RF-7 | `PUT /catalog/products/{id}?ownerAccountId=` |
| RF-8 | `DELETE /catalog/products/{id}?ownerAccountId=` |
| RF-9 | `POST /catalog/products/{id}/publish?ownerAccountId=` |
| RF-10 | `POST /catalog/products/{id}/unpublish?ownerAccountId=` |
| RF-11 | `POST /catalog/publish` con cuerpo + dueño de la sesión |
| RF-12 | `CATALOG_API_BASE_URL` en settings |
| RF-13 | Proxy de estado y cuerpo (no 5xx) |
| RF-14 | 503 `servicio_no_disponible` por caída de cuentas |
| RF-15 | 503 `servicio_no_disponible` por caída de catálogo |
| RF-16 | Sin modelos ni migraciones en `panel` |
| RF-17 | `ownerAccountId` del cliente ignorado |
| RF-18 | Cuerpo reenviado sin validación de dominio |
| RF-19 | Health checks conservados |
| RF-20 | CORS con credenciales conservado |
| RF-21 | `publish` sin productos → 200 con 0 |
| RF-22 | 4xx de catálogo reenviados con su cuerpo |
