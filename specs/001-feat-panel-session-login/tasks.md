# Tasks 001 — Login del panel con la sesión de cuentas

Tareas de implementación para `spec.md` y `plan.md` de este directorio.
Cada tarea dura ~20–30 minutos. Orden por dependencias. Estado alineado con el
código real en `src/` (identity + common; sin shops).

## Configuración y CORS

- [x] **T1. Añadir dependencia fijada `django-cors-headers`**
  - Cubre: RF-9
  - Añadir el paquete fijado en `requirements.txt` (y `requirements-dev.txt` si aplica el patrón del repo).
  - Done when: la dependencia aparece fijada y `pip install -r requirements.txt` (o el flujo del proyecto) la resuelve sin error.

- [x] **T2. Exponer settings de cuentas y origen del panel**
  - Cubre: RF-8, RF-11
  - En `src/config/settings.py`, leer `ACCOUNT_API_BASE_URL` (proxy interno), `ACCOUNTS_PUBLIC_BASE_URL` (redirect del navegador; default = base interna), `PANEL_PUBLIC_ORIGIN` y, si aplica, `SESSION_COOKIE_DOMAIN` / `ACCOUNT_API_TIMEOUT_SECONDS` desde entorno (sin secretos en código).
  - Done when: con esas variables definidas, Django arranca y los settings reflejan ambas bases URL y un único origen público del panel.

- [x] **T3. Activar CORS con credenciales desde el origen del panel**
  - Cubre: RF-9, RF-11
  - Registrar `corsheaders` en `INSTALLED_APPS` y `MIDDLEWARE`; `CORS_ALLOW_CREDENTIALS = True`; `CORS_ALLOWED_ORIGINS` = lista de un solo elemento con `PANEL_PUBLIC_ORIGIN` (sin `*`).
  - Done when: una petición OPTIONS/preflight desde ese origen hacia rutas del panel recibe cabeceras CORS con credenciales permitidas.

## Esqueleto del módulo identity

- [x] **T4. Crear app `identity` con capas vacías y registro bajo `src/`**
  - Cubre: RF-6, RF-10
  - Crear `src/identity/` con `apps.py` y paquetes `api/`, `application/`, `domain/`, `infrastructure/`; registrar en `INSTALLED_APPS`; health/panel en `src/common/`; Dockerfile copia `src/` y `tests/`. No añadir modelos ni migraciones de cuenta. Sin módulo `shops`.
  - Done when: la app carga al arrancar, no hay modelo/migración de identidad, y `GET /panel`, `/health/live` y `/health/ready` responden desde `common`.

- [x] **T5. Domain: constantes y error de indisponibilidad**
  - Cubre: RF-6, RF-7, RF-12, RF-13
  - En `identity/domain` (sin Django/DRF/HTTP): `SESSION_COOKIE_NAME = "fes_session"`, error tipado `AccountServiceUnavailable`, sin entidad persistida ni reglas de membresía.
  - Done when: tests unitarios importan estas piezas sin Django y confirman que no hay dependencia hacia ORM ni hacia un módulo shops.

## Application: puerto y casos de uso

- [x] **T6. Definir puerto `AccountSessionGateway` y DTOs**
  - Cubre: RF-2, RF-3, RF-4
  - Protocolo en application: `get_session(fes_session)` y `logout(fes_session)` con DTOs de payload/resultado; la capa no importa DRF ni el cliente HTTP concreto.
  - Done when: el Protocol y los tipos existen y un fake en tests puede implementar el puerto.

- [x] **T7. Caso de uso `build_google_login_redirect`**
  - Cubre: RF-1, RF-8, RF-11
  - Función pura que combina la base pública (`ACCOUNTS_PUBLIC_BASE_URL`) + `/accounts/login/google` + `return_to` = `PANEL_PUBLIC_ORIGIN` (URL-encoded).
  - Done when: un test unitario verifica la URL resultante con `return_to` igual al origen público (no el host interno de la API).

- [x] **T8. Caso de uso `resolve_panel_session`**
  - Cubre: RF-2, RF-3, RF-12, RF-14
  - Obtiene el payload vía gateway y lo devuelve tal cual; traduce fallos de infra a `AccountServiceUnavailable`; no inventa shape distinto del de cuentas para sesión válida/inválida.
  - Done when: con gateway fake, éxito propaga el JSON; fallo de infra lanza/produce indisponibilidad; sesión anónima/inválida del fake se propaga sin reinterpretar.

- [x] **T9. Caso de uso `logout_panel_session`**
  - Cubre: RF-4, RF-5, RF-13, RF-15
  - Solicita cierre vía gateway; si OK, `clear_cookie=True` siempre (el panel borra la cookie); **no** borrar cookie si el servicio falla. Proxy del status/body de cuentas (cuerpo vacío → `{}` en el cliente HTTP).
  - Done when: tests con fake cubren éxito (borrar), sin sesión (borrar) y fallo (no borrar + error de dominio).

## Infrastructure

- [x] **T10. Cliente HTTP `AccountSessionClient`**
  - Cubre: RF-8, RF-12, RF-13
  - Implementar el puerto contra `ACCOUNT_API_BASE_URL` vía `common.http`: `GET /accounts/session` y `POST /accounts/logout` reenviando cookie `fes_session`; mapear timeout/red/5xx a `AccountServiceUnavailable`; timeouts acotados.
  - Done when: tests con servidor/mock HTTP verifican base URL interna, reenvío de cookie y mapeo a error de dominio ante fallo.

## API DRF y rutas

- [x] **T11. Vista `GoogleLoginRedirectView` (`GET /panel/login/google`)**
  - Cubre: RF-1, RF-7, RF-11
  - Vista delgada AllowAny: invoca `build_google_login_redirect` con `ACCOUNTS_PUBLIC_BASE_URL` y responde 302; sin llamar a account-api servidor→servidor ni validar membresía/tienda.
  - Done when: `GET /panel/login/google` redirige a `/accounts/login/google` sobre la base **pública** con `return_to` = origen público configurado.

- [x] **T12. Vista `PanelSessionView` (`GET /panel/session`)**
  - Cubre: RF-2, RF-3, RF-7, RF-12, RF-14
  - AllowAny: lee `fes_session`, invoca `resolve_panel_session`, devuelve el mismo JSON/status de cuentas; 503 con cuerpo en español distinto del JSON de no autenticado si el servicio falla.
  - Done when: integración con gateway/cliente mock: mismo JSON en éxito; 200 + `authenticated: false` sin sesión válida; 503 con shape de error distinto ante caída.

- [x] **T13. Vista `PanelLogoutView` (`POST /panel/logout`) y borrado de cookie**
  - Cubre: RF-4, RF-5, RF-7, RF-13, RF-15
  - AllowAny: invoca `logout_panel_session`; si el caso lo autoriza, `clear_session_cookie` (Path `/`, HttpOnly, SameSite=Lax, Domain; Secure vía `getattr(SESSION_COOKIE_SECURE, False)`); en 503 no borrar cookie; mensaje 503 en español. El panel proxy status/body de cuentas (p. ej. 204 vacío → `{}`); los tests pueden asumir 200 + `authenticated: false`.
  - Done when: logout OK borra cookie en la respuesta del panel; sin sesión → OK + borra; fallo de cuentas → 503 y cookie intacta.

- [x] **T14. Cablear URLs sin sombrear rutas existentes**
  - Cubre: RF-10
  - En `src/config/urls.py`: `panel` y health desde `common`; `include("identity.api.urls")` bajo `panel/` para login/session/logout, sin alterar el contrato de `GET /panel`, `GET /health/live`, `GET /health/ready`.
  - Done when: las tres nuevas rutas resuelven y las tres rutas existentes siguen respondiendo desde `common`.

## Pruebas de cierre y verificación

- [x] **T15. Tests de integración del redirect y de la base URL**
  - Cubre: RF-1, RF-8, RF-11
  - Con settings de test, comprobar Location del login Google (`ACCOUNTS_PUBLIC_BASE_URL` + `return_to`) y que el cliente de sesión/logout usa `ACCOUNT_API_BASE_URL`.
  - Done when: tests automatizados fallan si falta `return_to` correcto o si la base pública/interna no se usan en sus caminos respectivos.

- [x] **T16. Tests de integración de sesión (proxy, anónima, 503)**
  - Cubre: RF-2, RF-3, RF-12, RF-14
  - Cubrir reenvío de cookie, JSON idéntico al mock de cuentas, 200 anónimo e inválido, y 503 con cuerpo ≠ no-autenticado.
  - Done when: la matriz anterior pasa en `tests/` (unitarios + integración según el plan).

- [x] **T17. Tests de integración de logout (OK, idempotente, fallo)**
  - Cubre: RF-4, RF-5, RF-13, RF-15
  - Cubrir llamada a cuentas + borrado de cookie por el panel; logout sin sesión; 503 sin borrar cookie. (Mocks de test suelen devolver 200 + `authenticated: false`; producción puede ser 204 vacío.)
  - Done when: los tres escenarios pasan de forma verificable (cabeceras Set-Cookie / ausencia de borrado en 503).

- [x] **T18. Tests de no persistencia, AllowAny, CORS y smoke de health**
  - Cubre: RF-6, RF-7, RF-9, RF-10
  - Verificar ausencia de modelo/migración de cuenta en identity; endpoints AllowAny sin módulo shops; CORS origen+credentials; smoke de `/panel`, `/health/live`, `/health/ready` desde `common`.
  - Done when: esos asserts/smoke pasan y documentan cobertura de RF-6, RF-7, RF-9 y RF-10.

- [x] **T19. Cierre con `make verify`**
  - Cubre: RF-1 … RF-15 (verificación global)
  - Ejecutar `make verify` (lint, formato, checks Django, migraciones, tests) tras el corte.
  - Done when: `make verify` termina en verde con la matriz de RF del plan cubierta por tests o smoke explícito.

## Cobertura RF

| RF | Tareas |
|---|---|
| RF-1 | T7, T11, T15, T19 |
| RF-2 | T6, T8, T12, T16, T19 |
| RF-3 | T6, T8, T12, T16, T19 |
| RF-4 | T6, T9, T13, T17, T19 |
| RF-5 | T9, T13, T17, T19 |
| RF-6 | T4, T5, T18, T19 |
| RF-7 | T5, T11, T12, T13, T18, T19 |
| RF-8 | T2, T7, T10, T15, T19 |
| RF-9 | T1, T3, T18, T19 |
| RF-10 | T4, T14, T18, T19 |
| RF-11 | T2, T3, T7, T11, T15, T19 |
| RF-12 | T5, T8, T10, T12, T16, T19 |
| RF-13 | T5, T9, T10, T13, T17, T19 |
| RF-14 | T8, T12, T16, T19 |
| RF-15 | T9, T13, T17, T19 |
