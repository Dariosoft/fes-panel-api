# Plan 003 — Frontera de gestión de tienda del vendedor

## 1. Objetivo técnico

Exponer en `panel-api` una frontera HTTP que permita al vendedor autenticado consultar y
guardar los datos de su propia tienda, delegando por completo en `account-api` como dueño y
única fuente de verdad. `panel-api` **no** agrega modelo, migración ni almacenamiento propio:
actúa como proxy autenticado que reenvía la cookie de sesión `fes_session` y retransmite
estado y cuerpo JSON sin validarlos ni transformarlos.

Rutas nuevas (ambas bajo `/panel`):

- `GET /panel/shop` → reenvía a `account-api GET /accounts/shop`.
- `PUT /panel/shop` → reenvía a `account-api PUT /accounts/shop` (upsert).

Los datos de tienda (`name`, `description`) siguen viviendo en `account-api`. Toda la
autorización y la resolución de "la tienda de la cuenta" ocurren en `account-api` a partir de
la sesión; `panel-api` nunca recibe ni acepta un identificador de cuenta o de tienda.

## 2. Decisiones técnicas y su motivo

| Decisión | Motivo | RF |
|---|---|---|
| `panel-api` es proxy puro, sin modelo ni migración | La tienda pertenece 1:1 a la cuenta y su fuente de verdad es `account-api`; replicarla rompería la propiedad del dato. | RF-5, RF-7, RF-8 |
| Usar la app de negocio `shops` (sin `models.py`) para la frontera | Sigue la organización por capacidad de negocio de `panel-api-architecture`; `catalog` es el precedente de app sin modelo. | RF-1, RF-3 |
| Reutilizar `AccountApiClient` y `AccountApiGateway` de `common/` en vez de un cliente propio | Los clientes de microservicios compartidos viven en `common/infrastructure/clients`; evita duplicar autenticación y transporte. | RF-1, RF-3 |
| Reenviar la cookie `fes_session` con el mismo patrón que `get_session`/`logout` (header `Cookie`) | No se inventa autenticación nueva; se conserva el mecanismo existente de sesión compartida. | RF-5, RF-9 |
| **No** pre-validar la sesión con `get_session` antes de reenviar | El contrato cross-repo indica que `account-api` responde `401` y `panel-api` lo propaga. Evita doble llamada y mantiene a `account-api` como autoridad. | RF-5, RF-9 |
| GET y PUT en una sola vista `APIView` (`PanelShopView`) | Es un único recurso con dos verbos; no hace falta `ViewSet`. Sigue el estilo de `PanelPublishCatalogView`. | RF-1, RF-3 |
| Propagar `404` de la consulta tal cual | "Sin tienda" no es error de sistema; `panel-web` lo interpreta como estado vacío. | RF-1, RF-2 |
| Propagar `401`/`403`/`400`/`422` de `account-api` sin reinterpretar | La sesión, la propiedad y la validación son responsabilidad de `account-api`; el panel muestra el motivo reportado. | RF-5, RF-6, RF-9, RF-13, RF-14, RF-15 |
| Mapear indisponibilidad (transporte o `5xx`) a `503` con cuerpo en español, sin tocar la cookie | Un fallo del servicio dueño no debe cerrar la sesión; el vendedor puede reintentar. | RF-10, RF-11, RF-12 |
| Reenviar `request.body` y `Content-Type` sin parsear ni validar | La validación de `name` (1–80) y `description` (≤1000) es de `account-api`; el panel no duplica reglas. | RF-3, RF-13 |
| Upsert resuelto en una sola operación `PUT` | La spec decide que alta y edición se resuelven en un único guardado que reemplaza nombre y descripción. | RF-3, RF-4 |

> Nota sobre mensajes: el contrato cross-repo fija el cuerpo `503` con
> `{"error":"servicio_no_disponible","message":"El servicio de cuentas no está disponible. Inténtalo de nuevo más tarde."}`.
> Las frases de RF-10/RF-11 ("No pudimos cargar tu tienda…" / "No pudimos guardar tu tienda…")
> son el texto visible que `panel-web` muestra a partir de ese `503`; `panel-api` devuelve el
> cuerpo de contrato y no lo personaliza por verbo.

## 3. Estructura objetivo

```text
panel-api/
├── src/
│   ├── common/
│   │   ├── contracts/account_api.py          # + ACCOUNT_SHOP_PATH = "/accounts/shop"
│   │   ├── infrastructure/clients/account_api_client.py  # + get_shop() / save_shop()
│   │   └── ports/account_api_gateway.py      # + get_shop() / save_shop()
│   ├── shops/                                 # nueva app de negocio (sin models.py)
│   │   ├── __init__.py
│   │   ├── apps.py                            # ShopsConfig(label="shops")
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── urls.py                        # path("", PanelShopView.as_view(), name="panel-shop")
│   │   │   └── views/
│   │   │       ├── __init__.py
│   │   │       └── panel_shop.py              # PanelShopView(APIView): get() y put()
│   │   └── use_cases/
│   │       ├── __init__.py
│   │       ├── get_shop.py                    # get_shop(gateway, fes_session)
│   │       └── save_shop.py                   # save_shop(gateway, fes_session, body, content_type)
│   └── config/
│       ├── settings.py                        # + "shops" en INSTALLED_APPS
│       └── urls.py                            # + path("panel/shop", include("shops.api.urls"))
└── tests/
    ├── shops/
    │   ├── __init__.py
    │   ├── fakes.py                           # FakeShopGateway (implementa el port)
    │   ├── test_use_cases.py
    │   └── test_ports.py
    ├── common/
    │   ├── test_account_api_client.py         # se amplía con casos de shop
    │   └── ...
    └── integration/
        ├── test_panel_shop_urls.py            # resolución de /panel/shop
        └── test_panel_shop_operations.py      # flujo GET/PUT con gateway mockeado y errores
```

No se crean `shops/models.py` ni `shops/migrations/`.

## 4. Contrato HTTP/JSON

### `GET /panel/shop`

- Entrada: cookie `fes_session` (si existe).
- Reenvío: `GET {ACCOUNT_API_BASE_URL}/accounts/shop` con header `Cookie: fes_session=<valor>`.
- Salidas propagadas tal cual:
  - `200` con `{"name": "<texto>", "description": "<texto>" | null}`.
  - `404` cuando la cuenta no tiene tienda (cuerpo de `account-api`).
  - `401` cuando no hay sesión válida.
  - `403`/`400`/`422` si `account-api` los emite.
- Indisponibilidad (transporte o `5xx` de `account-api`): `503` con
  `{"error":"servicio_no_disponible","message":"El servicio de cuentas no está disponible. Inténtalo de nuevo más tarde."}`.

### `PUT /panel/shop`

- Entrada: cookie `fes_session` y cuerpo JSON `{"name": "<texto>", "description": "<texto>" | null}`.
- Reenvío: `PUT {ACCOUNT_API_BASE_URL}/accounts/shop` con header de cookie y el **mismo**
  `body` y `Content-Type` recibidos (`application/json`), sin parsear ni validar.
- `account-api` hace upsert: crea si no existe, reemplaza `name` y `description` si existe.
- Salidas propagadas tal cual:
  - `200` con los datos de la tienda tras el cambio.
  - `400`/`422` con el motivo de rechazo reportado por `account-api` (tienda intacta).
  - `401` sin sesión válida.
  - `403` operación no permitida.
- Indisponibilidad: `503` con el mismo cuerpo de contrato anterior.

Transporte de errores en `panel-api`:

```json
{ "error": "servicio_no_disponible", "message": "El servicio de cuentas no está disponible. Inténtalo de nuevo más tarde." }
```

## 5. Manejo de estados 404 / 401 / 503

- **404 (consulta sin tienda):** `request_json` devuelve `(404, body)` para errores `< 500`;
  la vista responde `Response(result.body, status=404)`. `panel-web` lo trata como estado
  vacío y ofrece el formulario de guardado. No se genera `404` artificial en `panel-api`.
- **401 (sin sesión):** `account-api` es la autoridad; su `401` se propaga sin reescribir.
  `panel-api` no ejecuta `get_session` aparte ni inventa autenticación. La sesión no se toca.
- **503 (servicio dueño no disponible):** se lanza `AccountApiUnavailable` desde el cliente
  ante error de transporte o `5xx`; la vista captura esa excepción y responde `503` con el
  cuerpo de contrato. En ningún caso se borra la cookie ni se modifica la sesión (RF-12).

## 6. Pruebas

- **Unitarias de casos de uso (`tests/shops/test_use_cases.py`):**
  - `get_shop` delega en `gateway.get_shop(fes_session)` y retorna el `ServiceResponse`.
  - `save_shop` delega con `fes_session`, `body` y `content_type` **verbatim**.
  - El cuerpo no se inspecciona ni se altera (se preserva `b'{"name":"..."}'` byte a byte).
- **Unitarias de cliente (`tests/common/test_account_api_client.py`, ampliado):**
  - `get_shop` usa `GET /accounts/shop` y reenvía `Cookie: fes_session=<valor>`.
  - `save_shop` usa `PUT /accounts/shop`, reenvía cookie, body y `Content-Type`.
  - `404`/`401`/`422` se devuelven como `ServiceResponse` con estado y cuerpo.
  - `5xx` y fallo de conexión se mapean a `AccountApiUnavailable`.
  - Se conservan los casos existentes de `get_session`/`logout` (sin regresión).
- **Port (`tests/shops/test_ports.py`):** `FakeShopGateway` satisface `AccountApiGateway`.
- **Integración de URLs (`tests/integration/test_panel_shop_urls.py`):**
  - `resolve("/panel/shop")` resuelve a `PanelShopView` con acciones `get`/`put`.
  - Se preservan rutas de identidad, catálogo y health.
- **Integración de operaciones (`tests/integration/test_panel_shop_operations.py`), con
  `patch` del `build_account_api_gateway` en `shops.api.views.panel_shop` (mismo patrón que
  catálogo):**
  - GET `200` retransmite `{name, description}` y pasa la cookie del request.
  - GET `404` se propaga como `404` (estado vacío).
  - PUT reenvía `body` y `Content-Type` y retransmite `200`.
  - PUT `422` retransmite estado y motivo de rechazo.
  - Sin sesión: `account-api` `401` se propaga como `401`.
  - `AccountApiUnavailable` en GET y PUT → `503` con cuerpo de contrato; la cookie sigue presente.
  - La app `shops` no tiene modelos ni carpeta `migrations/`.
- **`make verify`** debe pasar: Ruff, formato, checks de Django, `makemigrations --check` y
  cobertura ≥ 90 %.

## 7. Riesgos

- **Dependencia del contrato de `account-api`:** la semántica `404` = sin tienda y `PUT` =
  upsert debe estar acordada cross-repo; un cambio allí impacta esta frontera.
- **Mensajes RF-10/RF-11 vs. cuerpo 503 genérico:** se resuelve dejando el texto específico en
  `panel-web`; el `503` de `panel-api` respeta el contrato cross-repo. Riesgo de confusión si
  se espera el texto exacto en el cuerpo del API.
- **Regresión en `AccountApiClient._request`:** al añadir `body`/`content_type` hay que
  mantener intactos `get_session` y `logout`; los tests existentes lo cubren.
- **Lectura de `request.body`:** DRF debe entregar el cuerpo crudo antes de cualquier parseo;
  se usa `request.body` directamente y `application/json` por defecto para el PUT.
- **Cobertura:** nuevas ramas (404/401/503, body vacío) deben tener test para no bajar del 90 %.
- **Sin pre-check de sesión:** cada request de tienda llama a `account-api`; es el
  comportamiento deseado por contrato, pero implica una llamada remota incluso sin cookie.

## 8. Trazabilidad de RF

| RF | Cómo se cubre en el plan |
|---|---|
| RF-1 | GET `/panel/shop` reenvía a `account-api` y retransmite `200` tal cual. |
| RF-2 | `404` de `account-api` se propaga; `panel-web` lo trata como estado vacío. |
| RF-3 | `PUT /panel/shop` reenvía a `PUT /accounts/shop`; upsert en `account-api`. |
| RF-4 | La vista retransmite el `200` y el cuerpo que `account-api` reporta tras el cambio. |
| RF-5 | Solo se propaga la cookie; no se aceptan `accountId`/`shopId` del cliente. |
| RF-6 | Cualquier `403`/restricción la decide `account-api` sobre la sesión y se propaga. |
| RF-7 | No hay modelo, migración ni persistencia en `shops`. |
| RF-8 | `account-api` es la única fuente de verdad; `panel-api` es proxy. |
| RF-9 | Sin sesión, `account-api` responde `401` y `panel-api` lo propaga. |
| RF-10 | Indisponibilidad en GET → `503` con cuerpo en español; `panel-web` muestra el mensaje de carga. |
| RF-11 | Indisponibilidad en PUT → `503` con cuerpo en español; `panel-web` muestra el mensaje de guardado. |
| RF-12 | El manejo de `503` no elimina ni invalida la cookie de sesión. |
| RF-13 | El cuerpo JSON se reenvía sin validar ni transformar; validación en `account-api`. |
| RF-14 | `400`/`422` de `account-api` se propagan con su motivo reportado. |
| RF-15 | No se escribe nada en `panel-api`; ante rechazo la tienda en `account-api` queda intacta. |
