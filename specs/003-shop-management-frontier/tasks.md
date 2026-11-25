# Tareas 003 — Frontera de gestión de tienda del vendedor

Ordenadas por dependencia. Cada tarea está pensada para 20–30 minutos y declara los RF que
cubre y una condición verificable de cierre.

## Contrato y capa de infraestructura (`common/`)

- [x] **T01 — Constante de contrato `ACCOUNT_SHOP_PATH`**
  Agregar `ACCOUNT_SHOP_PATH = "/accounts/shop"` en `src/common/contracts/account_api.py`,
  junto a las rutas existentes de sesión/logout.
  Cubre: RF-1, RF-3, RF-7, RF-8.
  Done when: `from common.contracts.account_api import ACCOUNT_SHOP_PATH` importa y el valor es
  exactamente `"/accounts/shop"`; Ruff no reporta errores.

- [x] **T02 — `AccountApiClient.get_shop` y `save_shop`**
  Ampliar `src/common/infrastructure/clients/account_api_client.py`: generalizar el helper
  privado para aceptar `body`/`content_type`, e implementar `get_shop(fes_session)` (GET) y
  `save_shop(fes_session, body, content_type)` (PUT) que devuelven `ServiceResponse` y
  reenvían `Cookie: fes_session=<valor>`. Mantener intactos `get_session` y `logout`.
  Cubre: RF-1, RF-3, RF-7, RF-8, RF-13.
  Done when: los métodos usan `ACCOUNT_SHOP_PATH`, el mismo patrón de header `Cookie` y
  `request_json`; los tests existentes de sesión/logout siguen pasando.

- [x] **T03 — Ampliar el port `AccountApiGateway`**
  Añadir firmas `get_shop(fes_session: str | None) -> ServiceResponse` y
  `save_shop(fes_session: str | None, body: bytes, content_type: str | None) -> ServiceResponse`
  en `src/common/ports/account_api_gateway.py`, con docstrings.
  Cubre: RF-1, RF-3.
  Done when: `AccountApiClient` satisface el protocolo (importable, mismas firmas) y Ruff pasa.

- [x] **T04 — Tests de cliente para shop**
  Ampliar `tests/common/test_account_api_client.py` con: GET a `/accounts/shop` con cookie;
  PUT a `/accounts/shop` con cookie, body y `Content-Type`; propagación de `404`/`401`/`422`;
  mapeo de `5xx` y de fallo de conexión a `AccountApiUnavailable`. Añadir `do_PUT` al handler
  de prueba si falta.
  Cubre: RF-1, RF-3, RF-9, RF-13.
  Done when: `python src/manage.py test tests.common.test_account_api_client` pasa y cubre las
  ramas de shop sin romper los casos existentes.

## Casos de uso y app `shops`

- [x] **T05 — Casos de uso `get_shop` y `save_shop`**
  Crear `src/shops/use_cases/get_shop.py`, `src/shops/use_cases/save_shop.py` y el
  `__init__.py` que los exporta. Delegación directa al gateway sin transformar datos.
  Cubre: RF-1, RF-3, RF-13.
  Done when: `from shops.use_cases import get_shop, save_shop` funciona; las firmas reciben
  gateway, `fes_session` y (en save) `body`/`content_type`.

- [x] **T06 — Fake de tests del gateway**
  Crear `tests/shops/__init__.py` y `tests/shops/fakes.py` con `FakeShopGateway` que implemente
  `get_shop`/`save_shop` (registrando llamadas y devolviendo un `ServiceResponse`
  configurable, con error opcional). Debe satisfacer `AccountApiGateway`.
  Cubre: RF-1, RF-3.
  Done when: `FakeShopGateway` es asignable a una variable tipada `AccountApiGateway` y
  registra los argumentos recibidos.

- [x] **T07 — Tests unitarios de casos de uso**
  Crear `tests/shops/test_use_cases.py` usando `FakeShopGateway`: `get_shop` delega y retorna
  el `ServiceResponse`; `save_shop` reenvía `fes_session`, `body` y `content_type` verbatim y no
  altera el cuerpo.
  Cubre: RF-1, RF-3, RF-13.
  Done when: `python src/manage.py test tests.shops.test_use_cases` pasa y verifica el body
  byte a byte.

- [x] **T08 — Test de conformidad del port**
  Crear `tests/shops/test_ports.py` que instancie `FakeShopGateway` y lo use a través de
  `AccountApiGateway` para `get_shop`/`save_shop`.
  Cubre: RF-1, RF-3.
  Done when: el test pasa y demuestra que el fake cumple el protocolo.

- [x] **T09 — Esqueleto de la app `shops` y registro**
  Crear `src/shops/__init__.py`, `src/shops/apps.py` (`ShopsConfig`, `name="shops"`,
  `label="shops"`), `src/shops/api/__init__.py`, `src/shops/api/views/__init__.py` y
  `src/shops/use_cases/__init__.py` si faltan. Registrar `"shops"` en `INSTALLED_APPS` de
  `src/config/settings.py`. No crear `models.py` ni `migrations/`.
  Cubre: RF-7.
  Done when: `python src/manage.py check` pasa y `apps.get_app_config("shops")` no tiene modelos.

- [x] **T10 — URLs `/panel/shop`**
  Crear `src/shops/api/urls.py` con `path("shop", PanelShopView.as_view(), name="panel-shop")`
  y en `src/config/urls.py` añadir `path("panel/", include("shops.api.urls"))`.
  Cubre: RF-1, RF-3.
  Done when: `resolve("/panel/shop")` resuelve a `PanelShopView` y las rutas de identidad,
  catálogo y health siguen resolviendo.

## Vistas HTTP y mapeo de errores

- [x] **T11 — Vista GET `PanelShopView.get`**
  Crear `src/shops/api/views/panel_shop.py` con `PanelShopView(APIView)`
  (`permission_classes=[AllowAny]`, `authentication_classes=[]`). `get()` toma
  `fes_session` de `request.COOKIES`, llama a `get_shop(build_account_api_gateway(), ...)` y
  responde `Response(result.body, status=result.status_code)`. Capturar
  `AccountApiUnavailable` y responder `503` con el cuerpo de contrato en español.
  Cubre: RF-1, RF-2, RF-9, RF-10, RF-12.
  Done when: un GET reenvía la cookie y retransmite `200`/`404`/`401`; un fallo del gateway
  devuelve `503` con `{"error":"servicio_no_disponible","message":"..."}`.

- [x] **T12 — Vista PUT `PanelShopView.put`**
  Añadir `put()` a `PanelShopView`: reenviar `request.body` y el `Content-Type` recibido
  (`application/json` por defecto) a `save_shop`, retransmitir estado y cuerpo, y mapear
  `AccountApiUnavailable` a `503` con el mismo cuerpo. No validar ni transformar el JSON.
  Cubre: RF-3, RF-4, RF-11, RF-12, RF-13, RF-14, RF-15.
  Done when: el PUT reenvía el cuerpo tal cual y retransmite `200`/`400`/`422`/`401`/`403`;
  la indisponibilidad devuelve `503` sin tocar la cookie.

## Pruebas de integración y verificación

- [x] **T13 — Integración de URLs**
  Crear `tests/integration/test_panel_shop_urls.py` que verifique `resolve("/panel/shop")` a
  `PanelShopView` con acciones `get`/`put` y que las rutas previas siguen intactas.
  Cubre: RF-1, RF-3.
  Done when: `python src/manage.py test tests.integration.test_panel_shop_urls` pasa.

- [x] **T14 — Integración de operaciones y errores**
  Crear `tests/integration/test_panel_shop_operations.py` con `patch` de
  `build_account_api_gateway` en `shops.api.views.panel_shop`. Cubrir: GET `200` y `404`;
  PUT reenvía body/`Content-Type` y retransmite `200`; PUT `422` con motivo; `401` propagado;
  `AccountApiUnavailable` en GET y PUT → `503` con cuerpo de contrato; y que la app `shops`
  no tiene modelos ni `migrations/`.
  Cubre: RF-2, RF-6, RF-7, RF-9, RF-10, RF-11, RF-12, RF-14, RF-15.
  Done when: `python src/manage.py test tests.integration.test_panel_shop_operations` pasa y
  todos los escenarios anteriores quedan cubiertos.

- [x] **T15 — Verificación completa**
  Ejecutar `make verify` (Ruff, formato, `manage.py check`, `makemigrations --check` y
  cobertura ≥ 90 %) y corregir lo que falle en los archivos tocados.
  Cubre: RF-1 a RF-15 (cierre).
  Done when: `make verify` termina en verde y no aparece `shops/migrations`.
