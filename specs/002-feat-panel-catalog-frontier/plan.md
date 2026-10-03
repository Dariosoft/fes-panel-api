# Plan 002 — Frontera de catálogo: drafts, publicación y sesión

Plan técnico **as-built** de `specs/002-feat-panel-catalog-frontier/spec.md`.
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
- El cuerpo y el `Content-Type` de create/update/publicar se reenvían de forma
  fiel; el panel no los interpreta. **(RF-24, RF-25)**

## 2. Ubicación del código (layout as-built)

Todo el runtime Django vive bajo `src/` (`PYTHONPATH` incluye `src`):

```text
src/
├── config/                      # settings, urls (sin cambios de layout)
├── common/
│   ├── contracts/
│   │   ├── account_api.py       # paths de /accounts + claves de sesión
│   │   └── catalog_api.py       # paths de /catalog, ownerAccountId y name
│   ├── health/views.py          # live / ready (sin cambios)
│   ├── http.py                  # ampliado con body/content_type
│   └── json_types.py            # NUEVO: alias JsonBody (dict | list)
├── identity/
│   ├── navigation/google_login_redirect.py   # return_to relativo seguro
│   └── api/views/google_login_redirect.py    # lee return_to y reenvía
└── catalog/                     # NUEVO módulo (frontera)
    ├── apps.py
    ├── api/
    │   ├── gateways.py          # factories de sesión y catálogo desde settings
    │   ├── panel_session.py     # PanelSessionGuardMixin + _forward
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
├── catalog/                   # unitarios de use cases/dtos/infra/views
├── common/                    # http con reenvío de cuerpo
├── identity/                  # return_to del login
└── integration/               # flujos HTTP /panel/catalog con gateways fake
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
| `PANEL_PUBLIC_ORIGIN` | Único origen CORS con credenciales y base del `return_to` | **RF-20, RF-26** |
| `ACCOUNTS_PUBLIC_BASE_URL` | Base pública de cuentas para el redirect de login | **RF-26** |

Notas:

- `CATALOG_API_BASE_URL` se normaliza con `rstrip("/")` como ya hace
  `ACCOUNT_API_BASE_URL`.
- No se añaden dependencias nuevas: el cliente HTTP sigue con `urllib` en
  `common.http`.
- Las factories `catalog/api/gateways.py` leen estos settings y construyen
  `AccountSessionClient` y `CatalogApiClient`, de modo que las vistas no
  dependen de `django.conf.settings` directamente.

## 4. Contratos HTTP

### 4.1 Contrato del panel (`panel-web` → `panel-api`)

Cookie `fes_session` obligatoria; todos requieren sesión. **(RF-1, RF-3)**

| Método y path | Operación | RF |
|---|---|---|
| `GET /panel/catalog/products` | Listar productos de la cuenta, filtrable por `name` | **RF-5, RF-23** |
| `POST /panel/catalog/products` | Crear draft con dueño | **RF-6** |
| `PUT /panel/catalog/products/{id}` | Actualizar producto | **RF-7** |
| `DELETE /panel/catalog/products/{id}` | Eliminar producto | **RF-8** |
| `POST /panel/catalog/products/{id}/publish` | Publicar producto | **RF-9** |
| `POST /panel/catalog/products/{id}/unpublish` | Despublicar producto | **RF-10** |
| `POST /panel/catalog/publish` | Publicar el catálogo visible | **RF-11** |

Detalles as-built del contrato del panel:

- `GET /panel/catalog/products?name=<texto>` reenvía `name` sin tocarlo; el
  filtrado real lo decide `catalog-api`. **(RF-23)**
- El cuerpo de `POST`/`PUT` se reenvía tal cual (JSON o `multipart/form-data`).
  Se usa `request.META["CONTENT_TYPE"]` (no `request.content_type`) porque el
  primero conserva el `boundary` del multipart; usar el segundo perdía el
  `boundary` y provocaba un **415** en `catalog-api`. **(RF-24)**
- `POST /panel/catalog/publish` normaliza el cuerpo: si no viene, envía `b"{}"`
  con `Content-Type: application/json`. El cliente Angular enviaba
  `text/plain` sin cuerpo, lo que producía un **415** en `catalog-api`. **(RF-25)**
- `POST /panel/catalog/publish` con lista vacía responde 200 con 0 publicados;
  no es error. **(RF-21)**

### 4.2 Contrato interno (`panel-api` → `catalog-api`)

Base `CATALOG_API_BASE_URL`. La frontera propaga la cuenta de la sesión como
`ownerAccountId` **en query string**, param autoritativo que `catalog-api`
prioriza sobre cualquier valor del cuerpo; así se sobrescribe sin parsear el
cuerpo. **(RF-4, RF-17)**

| Llamada interna | RF |
|---|---|
| `GET /catalog/products?ownerAccountId={id}[&name={texto}]` | **RF-5, RF-23** |
| `POST /catalog/products?ownerAccountId={id}` | **RF-6** |
| `PUT /catalog/products/{id}?ownerAccountId={id}` | **RF-7** |
| `DELETE /catalog/products/{id}?ownerAccountId={id}` | **RF-8** |
| `POST /catalog/products/{id}/publish?ownerAccountId={id}` | **RF-9** |
| `POST /catalog/products/{id}/unpublish?ownerAccountId={id}` | **RF-10** |
| `POST /catalog/publish?ownerAccountId={id}` (cuerpo con los productos sin dueño visibles) | **RF-11, RF-25** |

`name` solo se añade a la query cuando tiene valor (`if name:`), de modo que el
listado sin filtro mantiene la URL limpia. **(RF-23)**

Claves y paths como constantes en `src/common/contracts/catalog_api.py`:

```python
CATALOG_PRODUCTS_PATH = "/catalog/products"
CATALOG_PRODUCT_ITEM_PATH = "/catalog/products/{product_id}"
CATALOG_PRODUCT_PUBLISH_PATH = "/catalog/products/{product_id}/publish"
CATALOG_PRODUCT_UNPUBLISH_PATH = "/catalog/products/{product_id}/unpublish"
CATALOG_PUBLISH_PATH = "/catalog/publish"
OWNER_ACCOUNT_ID_QUERY_PARAM = "ownerAccountId"
OWNER_ACCOUNT_ID_KEY = "ownerAccountId"
NAME_QUERY_PARAM = "name"
```

En `src/common/contracts/account_api.py` se añaden las claves de lectura de la
sesión: `SESSION_AUTHENTICATED_KEY = "authenticated"` y `SESSION_ID_KEY = "id"`.

### 4.3 `common.http` — reenvío con cuerpo

`JsonRequest` se amplía con `body: bytes | None = None` y
`content_type: str | None = None`; `_read_body` adjunta `data=body` y la
cabecera `Content-Type` cuando corresponde. El alias de tipo `JsonBody`
(`dict[str, Any] | list[Any]`) vive en `src/common/json_types.py`. Se mantiene
el comportamiento:

- Respuestas 2xx/4xx devuelven `(status_code, body)`.
- 5xx, timeout, red o JSON no usable lanzan `RemoteServiceError`.
- Cuerpo vacío se normaliza a `{}`.

Con esto, `catalog_api_client` reenvía el cuerpo sin conocer su formato.
**(RF-18, RF-24, RF-25, RF-22)**

### 4.4 Contrato de retorno de login (`GET /panel/identity/login/google`)

- El view lee `return_to` de la query y delega en
  `identity/navigation/build_google_login_redirect_url`, que arma
  `PANEL_PUBLIC_ORIGIN.rstrip("/") + ruta` y lo envía como `return_to` a
  `ACCOUNT_LOGIN_GOOGLE_PATH`. **(RF-26)**
- `_safe_path` acepta solo rutas relativas: vacías, que no empiecen con `/` o
  que empiecen con `//` caen a la cadena vacía, con lo que el `return_to` queda
  reducido al origen público. **(RF-27)**
- La validación de que la ruta pertenezca al panel (por origen) la hace
  `account-api`; se documenta aquí como contrato de frontera. **(RF-26, RF-27)**

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
- `catalog/domain/__init__.py` reexporta la constante y los dos errores.
- Sin Django, DRF, settings ni HTTP; sin entidades persistidas.

### 6.2 Use cases, ports y DTOs — **RF-2 … RF-11, RF-13, RF-21 … RF-23**

Puertos:

- `PanelSessionGateway.resolve(fes_session) -> PanelSession`.
- `CatalogGateway` con un método por operación (`list_products`,
  `create_product`, `update_product`, `delete_product`, `publish_product`,
  `unpublish_product`, `publish_catalog`), todos recibiendo `owner_account_id`
  y devolviendo `CatalogResponse`.

DTOs (un archivo por clase en `catalog/dtos/`):

- `PanelSession(authenticated: bool, account_id: str | None)`.
- `CatalogResponse(status_code: int, body: JsonBody)`.

Casos de uso (una función por archivo en `catalog/use_cases/`):

1. `resolve_panel_owner(session_gateway, fes_session) -> PanelSession` —
   traduce fallo de infra a `SessionServiceUnavailable`. **(RF-2, RF-3, RF-14)**
2. `list_products(catalog_gateway, owner, name=None) -> CatalogResponse` **(RF-5, RF-13, RF-23)**
3. `create_product(catalog_gateway, owner, body, content_type)` **(RF-6, RF-22, RF-24)**
4. `update_product(catalog_gateway, owner, product_id, body, content_type)` **(RF-7, RF-24)**
5. `delete_product(catalog_gateway, owner, product_id)` **(RF-8)**
6. `publish_product(catalog_gateway, owner, product_id)` **(RF-9)**
7. `unpublish_product(catalog_gateway, owner, product_id)` **(RF-10)**
8. `publish_catalog(catalog_gateway, owner, body, content_type)` — el conjunto
   lo define el cuerpo (sin dueño) + los draft del dueño. **(RF-11, RF-21, RF-25)**

Los casos de uso son funciones puras que reciben los puertos por parámetro (como
`resolve_panel_session` en identidad) y no importan DRF, Django HTTP ni clientes
concretos. Incluso `resolve_panel_owner` atrapa cualquier excepción y la
normaliza a `SessionServiceUnavailable`.

### 6.3 Infrastructure — **RF-2, RF-4, RF-12 … RF-15, RF-17, RF-22 … RF-25**

- `AccountSessionClient(base_url, timeout_seconds)`:
  - `GET {ACCOUNT_API_BASE_URL}/accounts/session` con `Cookie: fes_session=...`.
  - `authenticated` y `id` desde el cuerpo (`common.contracts.account_api`).
  - `RemoteServiceError` → `SessionServiceUnavailable`.
- `CatalogApiClient(base_url, timeout_seconds)`:
  - Construye cada path de `common.contracts.catalog_api` e **inyecta siempre**
    `ownerAccountId` de la sesión como query param; ignora el del cliente.
    **(RF-4, RF-17)**
  - Añade `name` a la query de `list_products` solo si viene con valor. **(RF-23)**
  - Reenvía `body`/`content_type` sin interpretarlos. **(RF-18, RF-24, RF-25)**
  - `RemoteServiceError` → `CatalogServiceUnavailable`; el resto devuelve
    `CatalogResponse(status_code, body)`. **(RF-13, RF-22)**
  - `_with_query` centraliza la construcción de la query string con `urlencode`.

### 6.4 API (DRF) — **RF-1, RF-3, RF-5 … RF-15, RF-19, RF-21 … RF-25**

- `api/panel_session.py` define `PanelSessionGuardMixin`, no una vista concreta.
  En `initial(request, ...)` (no en `dispatch`) resuelve la sesión con
  `_session_gateway()`:
  - `SessionServiceUnavailable` → se lanza `_SessionUnavailable`, mapeada a
    503 `{"error":"servicio_no_disponible","message":"..."}`. **(RF-14)**
  - `PanelSession.authenticated` falso o sin `account_id` → se lanza
    `_Unauthenticated`, mapeada a 401 `{"error":"no_autenticado","message":"..."}`. **(RF-3)**
  - Si es válida, guarda `self.owner_account_id` y continúa. **(RF-4)**
  - `handle_exception` traduce `_SessionUnavailable` y `_Unauthenticated` a los
    bodies en español; el resto lo delega en DRF.
  - `_forward(operation)` ejecuta la operación contra `_catalog_gateway()` y
    traduce `CatalogServiceUnavailable` a 503; si no, responde con el estado y
    cuerpo reenviados (`Response(result.body, status=result.status_code)`). **(RF-13, RF-15, RF-22)**
  - `_session_gateway()`/`_catalog_gateway()` usan las factories de
    `catalog/api/gateways.py`, fáciles de reemplazar en tests.
- `PanelCatalogProductViewSet` (`ViewSet`) con acciones `list`, `create`,
  `update`, `destroy`, `publish`, `unpublish`; mapeo manual con `as_view({...})`
  para conservar las rutas del contrato. **(RF-5 … RF-10)**
  - `list` lee `request.query_params.get("name")`. **(RF-23)**
  - `create`/`update` pasan `request.body` y `request.META.get("CONTENT_TYPE")`.
    **(RF-24)**
- `PanelCatalogPublishView` (`APIView`) para `POST /panel/catalog/publish`.
  **(RF-11, RF-21)**
  - `post` usa `request.body or b"{}"` y fija `"application/json"`. **(RF-25)**
- Todas `permission_classes = [AllowAny]` y `authentication_classes = []`: la
  autorización la hace el guard de sesión, no DRF. Sin sesión → 401. **(RF-3)**
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
| Multipart sin `boundary` (bug corregido) | se evitaba con `request.META["CONTENT_TYPE"]`; ya no ocurre |
| `publish` sin cuerpo / `text/plain` (bug corregido) | se evitaba enviando `{}` como `application/json`; ya no ocurre |

## 8. CORS y health — **RF-19, RF-20**

- `corsheaders` y `CORS_ALLOW_CREDENTIALS`/`CORS_ALLOWED_ORIGINS` ya configurados
  cubren `/panel/catalog/...` sin cambios.
- `GET /health/live` y `GET /health/ready` permanecen en `common.health`.

## 9. Qué no hacer (fuera de alcance de la spec)

- Persistir productos, etapas, dueños o imágenes en `panel`. **(RF-16)**
- Validar moneda, precio, stock o imágenes (lo hace `catalog-api`). **(RF-18)**
- Interpretar o reconstruir el cuerpo reenviado. **(RF-24, RF-25)**
- Filtrar o normalizar `name` en el panel; el filtrado es de `catalog-api`. **(RF-23)**
- Validar por origen el `return_to`; eso vive en `account-api`. **(RF-26, RF-27)**
- Llamar a MinIO o gestionar imágenes.
- Crear el modelo Shop o autenticación nueva.
- Exponer `GET /catalog` de publicados para el market.
- Tocar el contrato de `identity` fuera del `return_to` documentado.

## 10. Pruebas (cobertura por RF)

| Área | Qué verificar | RF |
|---|---|---|
| Sin sesión | 401 con `no_autenticado` y sin llamada a catálogo | **RF-2, RF-3** |
| Cuentas caído | 503 `servicio_no_disponible` y sin reenvío | **RF-14** |
| Listar | `GET /catalog/products?ownerAccountId=` con la cuenta de la sesión | **RF-5** |
| Filtro por nombre | `name` reenviado al listar y ausente cuando no viene | **RF-23** |
| Crear/editar | Reenvío de cuerpo y dueño de la sesión | **RF-6, RF-7, RF-18** |
| Multipart | `Content-Type` completo con `boundary` reenviado | **RF-24** |
| Eliminar | `DELETE /catalog/products/{id}?ownerAccountId=` | **RF-8** |
| Publicar/despublicar | `POST .../publish` y `.../unpublish` con dueño | **RF-9, RF-10** |
| Publicar catálogo | Cuerpo reenviado + dueño; 200 con 0 cuando no hay productos | **RF-11, RF-21** |
| Publicar sin cuerpo | Se envía `{}` como `application/json` | **RF-25** |
| Error 4xx | Mismo estado y cuerpo de catálogo | **RF-13, RF-22** |
| Error 5xx | 503 con shape propio | **RF-15** |
| Dueño del cliente | Se ignora y se usa el de la sesión | **RF-4, RF-17** |
| Return-to login | Origen + ruta relativa segura; fallback al origen | **RF-26, RF-27** |
| Sin persistencia | No hay modelo/migración en `catalog` | **RF-16** |
| CORS/health/rutas | Preflight con credenciales, health y rutas resuelven | **RF-1, RF-19, RF-20** |

Criterios de automatización:

- Unitarios de use cases/domain con gateways fake.
- Unitarios de `catalog_api_client` contra servidor mock (paths, query params de
  dueño y `name`, reenvío de cuerpo, mapeo de errores).
- Unitarios de vistas con `RequestFactory` y gateways fake (incluye el
  `Content-Type` multipart completo y el default de `publish`).
- Integración DRF/`APIClient` con gateways fake de cuentas y catálogo.
- Ejecutar `make verify` al cerrar la implementación.

## 11. Orden de implementación as-built

1. `common/contracts/catalog_api.py` (con `NAME_QUERY_PARAM`), claves de sesión
   en `common/contracts/account_api.py`, `common/json_types.py` y `common.http`
   con `body`/`content_type` (**RF-12, RF-18, RF-24, RF-25**).
2. Settings `CATALOG_API_BASE_URL`/timeout y registro de `catalog` (**RF-12**).
3. Domain, DTOs y puertos (**RF-3, RF-14, RF-15**).
4. Casos de uso de reenvío y de sesión, con `name` en el listado
   (**RF-2 … RF-11, RF-13, RF-21 … RF-23**).
5. Clientes de cuentas y catálogo (**RF-2, RF-4, RF-12, RF-14, RF-15, RF-17, RF-22 … RF-24**).
6. Vistas, `PanelSessionGuardMixin` (en `initial`/`handle_exception`),
   factories en `catalog/api/gateways.py` y rutas `/panel/catalog/...`
   (**RF-1, RF-3 … RF-15, RF-19, RF-21, RF-23 … RF-25**).
7. `return_to` en `GET /panel/identity/login/google` (**RF-26, RF-27**).
8. Matriz de tests y `make verify` (**RF-1 … RF-27**).

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
| RF-23 | `name` reenviado al listar productos |
| RF-24 | `Content-Type` completo (boundary) en create/update |
| RF-25 | `publish` sin cuerpo → `{}` como `application/json` |
| RF-26 | `return_to` = origen público + ruta relativa segura |
| RF-27 | `return_to` no seguro cae al origen público |
