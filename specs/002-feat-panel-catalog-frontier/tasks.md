# Tasks 002 — Frontera de catálogo: drafts, publicación y sesión

Tareas de implementación **as-built** para `spec.md` y `plan.md` de este
directorio. Todas completadas; cada `Done when` describe la evidencia que quedó
en el código y en los tests del corte.

## Contratos y utilidades compartidas

- [x] **T1. Crear `common/contracts/catalog_api.py` y claves de sesión**
  - Cubre: RF-12
  - Definir constantes de paths (`/catalog/products`, item, publish, unpublish, `/catalog/publish`), `OWNER_ACCOUNT_ID_QUERY_PARAM`, `OWNER_ACCOUNT_ID_KEY` y `NAME_QUERY_PARAM`; añadir `SESSION_AUTHENTICATED_KEY` y `SESSION_ID_KEY` en `common/contracts/account_api.py`.
  - Done when: los nombres existen y son importables desde `common.contracts` sin depender de Django.

- [x] **T2. Ampliar `common.http` con cuerpo de reenvío**
  - Cubre: RF-18, RF-22, RF-24, RF-25
  - Añadir `body: bytes | None` y `content_type: str | None` a `JsonRequest`; `_read_body` envía `data` y cabecera `Content-Type` cuando aplica; mantener 2xx/4xx como `(status, dict|list)` y 5xx/red/JSON inválido como `RemoteServiceError`; declarar el alias `JsonBody` en `common/json_types.py`.
  - Done when: tests con servidor mock demuestran que el cuerpo llega intacto y que 4xx devuelve cuerpo y 5xx lanza `RemoteServiceError`.

- [x] **T3. Settings y registro de la app `catalog`**
  - Cubre: RF-12, RF-26
  - En `config/settings.py`, leer `CATALOG_API_BASE_URL` (default interno, `rstrip("/")`) y `CATALOG_API_TIMEOUT_SECONDS`; registrar `catalog` en `INSTALLED_APPS`; conservar `PANEL_PUBLIC_ORIGIN` y `ACCOUNTS_PUBLIC_BASE_URL`.
  - Done when: Django arranca con la nueva variable y el setting refleja la base de catálogo.

- [x] **T4. Esqueleto del módulo `catalog`**
  - Cubre: RF-1, RF-16
  - Crear `src/catalog/` con `apps.py` y paquetes `api/`, `use_cases/`, `ports/`, `dtos/`, `domain/errors/`, `infrastructure/`. Sin modelos ni migraciones.
  - Done when: la app carga al arrancar, no hay modelo/migración en `catalog` y los health checks siguen respondiendo.

## Domain, DTOs y puertos

- [x] **T5. Domain: constantes y errores tipados**
  - Cubre: RF-3, RF-14, RF-15
  - En `catalog/domain`: `SESSION_COOKIE_NAME = "fes_session"`; errores `SessionServiceUnavailable` y `CatalogServiceUnavailable`, uno por archivo, sin Django/DRF/HTTP.
  - Done when: tests unitarios importan las piezas sin Django y los errores son distintos entre sí.

- [x] **T6. DTOs y puertos**
  - Cubre: RF-2 … RF-11, RF-23
  - `catalog/dtos/`: `PanelSession(authenticated, account_id)` y `CatalogResponse(status_code, body)`. `catalog/ports/`: `PanelSessionGateway.resolve` y `CatalogGateway` con un método por operación, todos con `owner_account_id` y `name` opcional en `list_products`.
  - Done when: un fake en tests puede implementar ambos Protocol y las firmas devuelven los DTOs.

## Use cases y clientes

- [x] **T7. Caso de uso `resolve_panel_owner`**
  - Cubre: RF-2, RF-3, RF-14
  - Recibe `PanelSessionGateway` y `fes_session`; traduce cualquier fallo de infra a `SessionServiceUnavailable`; devuelve `PanelSession` (autenticado o no) sin reinterpretar la sesión.
  - Done when: con gateway fake, sesión válida devuelve `account_id`, sesión anónima devuelve `authenticated=False` y fallo de infra produce `SessionServiceUnavailable`.

- [x] **T8. Cliente `AccountSessionClient`**
  - Cubre: RF-2, RF-4, RF-14
  - Implementa `PanelSessionGateway` contra `ACCOUNT_API_BASE_URL`: `GET /accounts/session` con cookie `fes_session`; lee `authenticated` e `id`; mapea `RemoteServiceError` a `SessionServiceUnavailable`.
  - Done when: tests con servidor mock verifican base URL, reenvío de cookie, lectura de `authenticated`/`id` y mapeo de fallo.

- [x] **T9. Cliente `CatalogApiClient`**
  - Cubre: RF-4, RF-5, RF-6, RF-7, RF-8, RF-9, RF-10, RF-11, RF-12, RF-13, RF-17, RF-22, RF-23, RF-24
  - Implementa `CatalogGateway` contra `CATALOG_API_BASE_URL`; arma cada path de `common.contracts.catalog_api`; inyecta siempre `ownerAccountId` como query param (ignora el del cliente); añade `name` solo si viene con valor; reenvía `body`/`content_type` completos; `RemoteServiceError` → `CatalogServiceUnavailable`, el resto → `CatalogResponse`.
  - Done when: tests con servidor mock verifican paths, query params de dueño/`name`, reenvío de cuerpo (incluido `Content-Type`), que 4xx devuelve estado/cuerpo y que 5xx produce `CatalogServiceUnavailable`.

- [x] **T10. Casos de uso de productos: listar, crear, editar y eliminar**
  - Cubre: RF-5, RF-6, RF-7, RF-8, RF-13, RF-18, RF-22, RF-23
  - Funciones `list_products` (con `name` opcional), `create_product`, `update_product`, `delete_product`; reciben `CatalogGateway`, `owner` y, cuando corresponde, `body`/`content_type`; devuelven `CatalogResponse` sin validar el dominio.
  - Done when: con gateway fake, cada función llama al método correcto con el dueño de la sesión, el filtro y el cuerpo tal cual.

- [x] **T11. Casos de uso `publish_product` y `unpublish_product`**
  - Cubre: RF-9, RF-10
  - Funciones que reenvían la publicación/despublicación del `{id}` con el dueño de la sesión y devuelven `CatalogResponse`.
  - Done when: con gateway fake se invocan `publish_product`/`unpublish_product` del puerto con el dueño y el id correctos.

- [x] **T12. Caso de uso `publish_catalog`**
  - Cubre: RF-11, RF-21, RF-25
  - Reenvía el cuerpo del cliente (productos sin dueño) y el dueño de la sesión a `POST /catalog/publish`; no trata como error el conteo 0 (lo determina `catalog-api`).
  - Done when: con gateway fake se reenvían cuerpo y dueño, y una respuesta 200 con 0 publicados se propaga sin excepción.

## API DRF y rutas

- [x] **T13. Guard de sesión de la frontera**
  - Cubre: RF-2, RF-3, RF-4, RF-14
  - `PanelSessionGuardMixin` en `catalog/api/panel_session.py` que en `initial` resuelve la sesión con `_session_gateway()`: `SessionServiceUnavailable` → 503 `servicio_no_disponible` vía `handle_exception`; no autenticada → 401 `no_autenticado`; válida → `self.owner_account_id` y continúa. Incluye `_forward` con la traducción de `CatalogServiceUnavailable`. Mensajes en español.
  - Done when: una vista de prueba responde 401 sin cookie, 503 si cuentas falla y 200/continúa con sesión válida guardando el dueño.

- [x] **T14. `PanelCatalogProductViewSet` y rutas de productos**
  - Cubre: RF-1, RF-5, RF-6, RF-7, RF-8, RF-9, RF-10, RF-15, RF-22
  - `ViewSet` con acciones `list`, `create`, `update`, `destroy`, `publish`, `unpublish`, `AllowAny` + guard; mapeo manual `as_view({...})`; `CatalogServiceUnavailable` → 503 `servicio_no_disponible`; 4xx/2xx de catálogo reenviados.
  - Done when: las seis operaciones resuelven en sus paths y, con mocks, reenvían dueño/cuerpo y traducen los errores según el plan.

- [x] **T15. `PanelCatalogPublishView` (`POST /panel/catalog/publish`)**
  - Cubre: RF-1, RF-11, RF-21
  - `APIView` con guard de sesión que invoca `publish_catalog` y reenvía estado/cuerpo; 200 con 0 publicados no es error.
  - Done when: la ruta responde 401 sin sesión, y con mock reenvía cuerpo + dueño propagando el conteo.

- [x] **T16. Cablear URLs de catálogo y conservar health**
  - Cubre: RF-1, RF-19
  - `catalog/api/urls.py` con las rutas del contrato; `config/urls.py` incluye `panel/catalog/` y conserva `panel/identity/`, `/health/live` y `/health/ready`.
  - Done when: las siete rutas resuelven y los health checks siguen respondiendo desde `common`.

## Fixes de integración con el panel real

- [x] **T17. Filtro `name` en el listado de productos**
  - Cubre: RF-23
  - `list` lee `request.query_params.get("name")`; el puerto, el caso de uso y `CatalogApiClient` propagan `name` y solo lo añaden a la query si tiene valor.
  - Done when: un test de vista y uno de cliente verifican que `name` viaja al listar y que no aparece en la query cuando no se envía.

- [x] **T18. Fix: reenvío del `Content-Type` completo en create/update (multipart)**
  - Cubre: RF-24
  - Reemplazar `request.content_type` por `request.META.get("CONTENT_TYPE")` en `create`/`update` para preservar el `boundary` de `multipart/form-data`; sin el boundary `catalog-api` devolvía 415.
  - Done when: un test con `content_type="multipart/form-data; boundary=boundary"` verifica que el gateway recibe el `Content-Type` completo.

- [x] **T19. Fix: cuerpo por defecto al publicar catálogo**
  - Cubre: RF-25
  - En `PanelCatalogPublishView.post`, usar `request.body or b"{}"` y fijar `Content-Type: application/json`, de modo que el cliente Angular (que enviaba `text/plain` sin cuerpo) ya no provoque un 415.
  - Done when: un test con cuerpo vacío y `CONTENT_TYPE=""` verifica que se reenvía `b"{}"` como `application/json`.

- [x] **T20. `return_to` seguro en `GET /panel/identity/login/google`**
  - Cubre: RF-26, RF-27
  - `build_google_login_redirect_url` recibe `return_to`, lo acepta solo si es ruta relativa (empieza con `/` y no con `//`) y arma `PANEL_PUBLIC_ORIGIN + ruta`; el view lee `return_to` de la query. La validación por origen queda en `account-api`.
  - Done when: tests de navegación y de vista verifican origen + ruta segura y el fallback al origen con rutas inseguras o ausentes.

## Pruebas y verificación

- [x] **T21. Tests unitarios de casos de uso e infraestructura**
  - Cubre: RF-2, RF-4, RF-5 … RF-12, RF-14, RF-15, RF-17, RF-18, RF-22 … RF-24
  - Cubrir `resolve_panel_owner`, los casos de uso de productos y catálogo con gateways fake; y `CatalogApiClient`/`AccountSessionClient` con servidor mock (paths, dueño, `name`, cuerpo, mapeo de errores).
  - Done when: la matriz unitaria pasa y verifica que el `ownerAccountId` del cliente nunca se propaga.

- [x] **T22. Tests de integración de sesión y errores**
  - Cubre: RF-2, RF-3, RF-13, RF-14, RF-15, RF-17, RF-22
  - Con `APIClient` y gateways fake: 401 sin cookie con `no_autenticado`; 401 con sesión anónima; 503 con `servicio_no_disponible` si cuentas falla; 4xx de catálogo reenviado; 5xx/inalcanzable → 503; dueño del cliente ignorado.
  - Done when: cada escenario devuelve el estado y el shape esperados y no hay reenvío cuando falta la sesión.

- [x] **T23. Tests de integración de operaciones, CORS y no persistencia**
  - Cubre: RF-1, RF-5 … RF-11, RF-16, RF-19, RF-20, RF-21, RF-23
  - Cubrir las siete operaciones reenviadas con su dueño, el filtro `name`, `publish` sin productos (200/0), preflight CORS con credenciales, health y ausencia de modelo/migración en `catalog`.
  - Done when: la matriz pasa y documenta la cobertura de RF-1, RF-5–RF-11, RF-16 y RF-19–RF-21, RF-23.

- [x] **T24. Tests de los fixes de multipart y publish**
  - Cubre: RF-24, RF-25
  - Tests de vista que fijan el `Content-Type` multipart completo en `create`/`update` y el default `b"{}"` + `application/json` en `publish` sin cuerpo.
  - Done when: ambos tests pasan y protegen contra la regresión del 415.

- [x] **T25. Cierre con `make verify`**
  - Cubre: RF-1 … RF-27 (verificación global)
  - Ejecutar `make verify` (Ruff, formato, checks Django, migraciones y tests) tras el corte.
  - Done when: `make verify` termina en verde con la matriz de RF cubierta por tests o smoke explícito.

## Cobertura RF

| RF | Tareas |
|---|---|
| RF-1 | T4, T14, T15, T16, T25 |
| RF-2 | T6, T7, T8, T13, T21, T22, T25 |
| RF-3 | T5, T7, T13, T22, T25 |
| RF-4 | T6, T8, T9, T13, T21, T22, T25 |
| RF-5 | T6, T9, T10, T14, T21, T23, T25 |
| RF-6 | T6, T9, T10, T14, T21, T23, T25 |
| RF-7 | T6, T9, T10, T14, T21, T23, T25 |
| RF-8 | T6, T9, T10, T14, T21, T23, T25 |
| RF-9 | T6, T9, T11, T14, T21, T23, T25 |
| RF-10 | T6, T9, T11, T14, T21, T23, T25 |
| RF-11 | T6, T9, T12, T15, T21, T23, T25 |
| RF-12 | T1, T3, T9, T21, T25 |
| RF-13 | T9, T10, T14, T22, T25 |
| RF-14 | T5, T7, T8, T13, T21, T22, T25 |
| RF-15 | T5, T9, T14, T21, T22, T25 |
| RF-16 | T4, T23, T25 |
| RF-17 | T9, T21, T22, T25 |
| RF-18 | T2, T10, T21, T25 |
| RF-19 | T16, T23, T25 |
| RF-20 | T23, T25 |
| RF-21 | T12, T15, T23, T25 |
| RF-22 | T2, T9, T10, T14, T21, T22, T25 |
| RF-23 | T6, T9, T10, T14, T17, T21, T23, T25 |
| RF-24 | T2, T9, T10, T14, T18, T21, T24, T25 |
| RF-25 | T2, T12, T15, T19, T24, T25 |
| RF-26 | T3, T20, T25 |
| RF-27 | T20, T25 |
