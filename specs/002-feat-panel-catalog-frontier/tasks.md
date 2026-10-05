# Tasks 002 - Frontera de catalogo: drafts, publicacion y sesion

Tareas **as-built** de `spec.md` y `plan.md`. Todas estan completadas. El
refactor arquitectonico mantuvo el comportamiento HTTP y no genero migraciones.

## Frontera original

- [x] **T1. Definir contratos externos y HTTP compartido**
  - Cubre: RF-12, RF-18, RF-22, RF-24, RF-25.
  - Implementar paths/claves de cuentas y catalogo, `JsonBody` y soporte de
    `body`/`content_type` en `common.http`.
  - Done when: 2xx/4xx retornan status/body, los fallos remotos se tipan y body +
    Content-Type se preservan en tests.

- [x] **T2. Configurar y registrar catalogo**
  - Cubre: RF-1, RF-12, RF-16, RF-19.
  - Registrar la app y settings de URL/timeout sin modelos ni migraciones.
  - Done when: Django carga, las rutas y health resuelven y no hay persistencia.

- [x] **T3. Implementar resolucion de owner**
  - Cubre: RF-2, RF-3, RF-4, RF-14, RF-17.
  - Resolver la sesion de cuentas antes del reenvio y fijar su account id.
  - Done when: fakes cubren sesion valida, anonima e indisponibilidad sin llamada
    posterior a catalogo.

- [x] **T4. Implementar operaciones de productos**
  - Cubre: RF-5 - RF-10, RF-13, RF-18, RF-22.
  - Listar, crear, actualizar, eliminar, publicar y despublicar mediante casos de
    uso sin reglas de dominio locales.
  - Done when: cada operacion recibe owner y propaga status/body con fakes.

- [x] **T5. Implementar publicacion de catalogo**
  - Cubre: RF-11, RF-21, RF-25.
  - Reenviar el conjunto visible; normalizar falta de cuerpo a `{}` JSON.
  - Done when: el conteo cero retorna 200 y el request vacio evita el 415.

- [x] **T6. Implementar API, guard y rutas**
  - Cubre: RF-1, RF-3, RF-13 - RF-15, RF-19, RF-22.
  - Exponer ViewSet/APIView, protegerlos con sesion y mapear errores propios.
  - Done when: las siete rutas tienen cobertura 401, 503 y proxy 2xx/4xx.

- [x] **T7. Propagar filtro `name`**
  - Cubre: RF-23.
  - Pasar el valor sin normalizar y omitirlo si no tiene contenido.
  - Done when: tests de view y cliente cubren presencia y ausencia del query param.

- [x] **T8. Preservar multipart completo**
  - Cubre: RF-24.
  - Usar `request.META["CONTENT_TYPE"]` para conservar el boundary.
  - Done when: create/update entregan body y Content-Type completos al gateway.

- [x] **T9. Conservar `return_to` seguro**
  - Cubre: RF-26, RF-27.
  - Aceptar solo rutas relativas seguras y combinar con el origen publico.
  - Done when: navegacion y view cubren ruta valida y fallback al origen.

## Refactor de fronteras comunes

- [x] **T10. Centralizar el cliente de cuentas**
  - Cubre: RF-2, RF-3, RF-14 y sesion/logout de identity.
  - Crear en `common` `AccountApiClient`, `AccountApiGateway`, `AccountSession`,
    `AccountLogout` y `AccountApiUnavailable`; incluir session y logout, cookie,
    parseo de `authenticated`/`id` y traduccion de errores.
  - Done when: identity, catalog y futuros modulos pueden consumir una sola
    implementacion mediante el puerto comun, sin adaptadores locales.
  - Cobertura: `tests/common/test_account_api_client.py`,
    `tests/identity/test_ports.py`, `tests/identity/test_use_cases.py` y tests del
    guard de catalogo.

- [x] **T11. Centralizar el cliente de catalogo**
  - Cubre: RF-4 - RF-13, RF-15, RF-17, RF-22 - RF-25.
  - Crear en `common` `CatalogApiClient`, `CatalogApiGateway`, `ServiceResponse`
    y `CatalogApiUnavailable`; conservar `name`, owner query autoritativo,
    multipart/body/Content-Type y publish.
  - Done when: todas las operaciones retornan `ServiceResponse`, los fallos
    remotos levantan el error comun y no existe otro cliente de catalogo.
  - Cobertura: `tests/common/test_catalog_api_client.py`, `tests/common/test_http.py`
    y tests de casos de uso/views de catalogo.

- [x] **T12. Migrar identity a la frontera comun**
  - Cubre: comportamiento de sesion/logout existente y RF-26, RF-27.
  - Componer `AccountApiClient` desde la API; migrar casos de uso a
    `AccountApiGateway`, DTOs y error comunes; conservar API, navegacion,
    cookies, casos de uso y `LogoutPanelSessionResult`.
  - Done when: identity no contiene adaptadores ni puertos propios, y no conserva
    los DTOs remotos reemplazados ni un error remoto local.
  - Cobertura: `tests/identity/test_ports.py`, `tests/identity/test_use_cases.py` y
    tests de views/navegacion existentes.

- [x] **T13. Migrar catalog a la frontera comun**
  - Cubre: RF-1 - RF-25.
  - Tipar guard y casos de uso con puertos comunes; construirlos con la factory
    comun; migrar a DTOs/errores/puertos comunes.
  - Done when: catalog conserva solo API y casos de uso relevantes, y el guard no
    importa contratos ni implementaciones internas de identity.
  - Cobertura: `tests/catalog/test_ports.py`, `tests/catalog/test_use_cases.py`,
    tests del guard, views e integracion.

- [x] **T14. Mover tests de clientes y unificar la constante de cookie**
  - Cubre: RF-2, RF-3, RF-14, RF-24 y prevencion de duplicaciones.
  - Mover pruebas de clientes a `tests/common/test_account_api_client.py` y
    `tests/common/test_catalog_api_client.py`; usar fakes de puertos comunes en
    los modulos; dejar `SESSION_COOKIE_NAME` definida solo en
    `common/contracts/account_api.py`.
  - Done when: no quedan tests de clientes bajo identity/catalog, todos los
    consumidores importan la misma constante y la suite protege ambos clientes.
  - Cobertura: los dos archivos de clientes comunes, tests de puertos de ambos
    modulos y tests del guard/API.

- [x] **T16. Centralizar la composicion de clientes**
  - Cubre: reutilizacion de la frontera comun y prevencion de builders duplicados.
  - Crear `common/infrastructure/client_factory.py` con
    `build_account_api_gateway`/`build_catalog_api_gateway` desde settings;
    consumirla en `identity.api` y en `PanelSessionGuardMixin`; eliminar
    `catalog/api/gateways.py` y el helper `_gateway` de identity.
  - Done when: ningun modulo define builders de clientes propios y no quedan
    referencias a `api.gateways` ni `build_session_gateway`.
  - Cobertura: `tests/common/test_client_factory.py`.

## Verificacion

- [x] **T15. Verificar el corte completo**
  - Cubre: RF-1 - RF-27.
  - Ejecutar lint, formato, checks Django, chequeo de migraciones y tests.
  - Done when: `make verify` finaliza verde con **114 tests** y sin migraciones.

## Cobertura RF

| RF | Tareas principales |
|---|---|
| RF-1 | T2, T6, T13, T15 |
| RF-2 - RF-4 | T3, T6, T10, T13 - T15 |
| RF-5 - RF-11 | T4, T5, T11, T13, T15 |
| RF-12 | T1, T2, T11, T15 |
| RF-13 | T4, T6, T11, T13, T15 |
| RF-14 | T3, T6, T10, T13 - T15 |
| RF-15 | T6, T11, T13, T15 |
| RF-16 | T2, T15 |
| RF-17, RF-18 | T3, T4, T11, T13, T15 |
| RF-19, RF-20 | T2, T6, T15 |
| RF-21, RF-22 | T4 - T6, T11, T13, T15 |
| RF-23 | T7, T11, T13, T15 |
| RF-24 | T1, T8, T11, T13 - T15 |
| RF-25 | T1, T5, T11, T13, T15 |
| RF-26, RF-27 | T9, T12, T15 |
