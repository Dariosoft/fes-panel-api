# Tasks 001 — Login del panel con la sesión de cuentas

Tareas de implementación para `spec.md` y `plan.md` de este directorio.
Cada tarea dura ~20–30 minutos. Orden por dependencias. No implementa la
funcionalidad en este documento: solo la descompone.

## Configuración y CORS

- [ ] **T1. Añadir dependencia fijada `django-cors-headers`**
  - Cubre: RF-9
  - Añadir el paquete fijado en `requirements.txt` (y `requirements-dev.txt` si aplica el patrón del repo).
  - Done when: la dependencia aparece fijada y `pip install -r requirements.txt` (o el flujo del proyecto) la resuelve sin error.

- [ ] **T2. Exponer settings de cuentas y origen del panel**
  - Cubre: RF-8, RF-11
  - En `config/settings.py`, leer `ACCOUNT_API_BASE_URL`, `PANEL_PUBLIC_ORIGIN` y, si aplica, `SESSION_COOKIE_DOMAIN` / timeout opcional desde entorno (sin secretos en código).
  - Done when: con esas variables de entorno definidas, Django arranca y los settings reflejan base URL y un único origen público del panel.

- [ ] **T3. Activar CORS con credenciales desde el origen del panel**
  - Cubre: RF-9, RF-11
  - Registrar `corsheaders` en `INSTALLED_APPS` y `MIDDLEWARE`; `CORS_ALLOW_CREDENTIALS = True`; `CORS_ALLOWED_ORIGINS` = lista de un solo elemento con `PANEL_PUBLIC_ORIGIN` (sin `*`).
  - Done when: una petición OPTIONS/preflight desde ese origen hacia rutas del panel recibe cabeceras CORS con credenciales permitidas.

## Esqueleto del módulo identity

- [ ] **T4. Crear app `identity` con capas vacías y registro**
  - Cubre: RF-6, RF-10
  - Crear `identity/` con `apps.py` y paquetes `api/`, `application/`, `domain/`, `infrastructure/`; registrar en `INSTALLED_APPS`; actualizar `Dockerfile` para copiar `identity/` (y `tests/` si hace falta en build). No añadir modelos ni migraciones de cuenta.
  - Done when: la app carga al arrancar, no hay modelo/migración de identidad, y `GET /panel`, `/health/live` y `/health/ready` siguen respondiendo.

- [ ] **T5. Domain: constantes y error de indisponibilidad**
  - Cubre: RF-6, RF-7, RF-12, RF-13
  - En `identity/domain` (sin Django/DRF/HTTP): `SESSION_COOKIE_NAME = "fes_session"`, error tipado p. ej. `AccountServiceUnavailable`, sin entidad persistida ni reglas de membresía.
  - Done when: tests unitarios importan estas piezas sin Django y confirman que no hay dependencia hacia ORM ni shops.

## Application: puerto y casos de uso

- [ ] **T6. Definir puerto `AccountSessionGateway` y DTOs**
  - Cubre: RF-2, RF-3, RF-4
  - Protocolo en application: `get_session(fes_session)` y `logout(fes_session)` con DTOs de payload/resultado; la capa no importa DRF ni el cliente HTTP concreto.
  - Done when: el Protocol y los tipos existen y un fake en tests puede implementar el puerto.

- [ ] **T7. Caso de uso `BuildGoogleLoginRedirect`**
  - Cubre: RF-1, RF-8, RF-11
  - Función/caso puro que combina `ACCOUNT_API_BASE_URL` + `/accounts/login/google` + `return_to` = `PANEL_PUBLIC_ORIGIN` (URL-encoded).
  - Done when: un test unitario verifica la URL resultante con `return_to` igual al origen público (no el host de la API).

- [ ] **T8. Caso de uso `ResolvePanelSession`**
  - Cubre: RF-2, RF-3, RF-12, RF-14
  - Obtiene el payload vía gateway y lo devuelve tal cual; traduce fallos de infra a `AccountServiceUnavailable`; no inventa shape distinto del de cuentas para sesión válida/inválida.
  - Done when: con gateway fake, éxito propaga el JSON; fallo de infra lanza/produce indisponibilidad; sesión anónima/inválida del fake se propaga sin reinterpretar.

- [ ] **T9. Caso de uso `LogoutPanelSession`**
  - Cubre: RF-4, RF-5, RF-13, RF-15
  - Solicita cierre vía gateway; indica borrar cookie en éxito o sin sesión; **no** borrar cookie si el servicio falla.
  - Done when: tests con fake cubren éxito (borrar), sin sesión (borrar + no autenticado) y fallo (no borrar + error de dominio).

## Infrastructure

- [ ] **T10. Cliente HTTP `AccountSessionClient`**
  - Cubre: RF-8, RF-12, RF-13
  - Implementar el puerto contra `ACCOUNT_API_BASE_URL`: `GET /accounts/session` y `POST /accounts/logout` reenviando cookie `fes_session`; mapear timeout/red/5xx a `AccountServiceUnavailable`; timeouts acotados.
  - Done when: tests con servidor/mock HTTP verifican base URL, reenvío de cookie y mapeo a error de dominio ante fallo.

## API DRF y rutas

- [ ] **T11. Vista `GET /panel/login/google`**
  - Cubre: RF-1, RF-7, RF-11
  - Vista delgada AllowAny: invoca el caso de redirect y responde 302/303; sin llamar a account-api con el cuerpo ni validar membresía/tienda.
  - Done when: `GET /panel/login/google` redirige a `/accounts/login/google` con `return_to` = origen público configurado.

- [ ] **T12. Vista `GET /panel/session`**
  - Cubre: RF-2, RF-3, RF-7, RF-12, RF-14
  - AllowAny: lee `fes_session`, invoca `ResolvePanelSession`, devuelve el mismo JSON/status de cuentas; 503 con cuerpo en español distinto del JSON de no autenticado si el servicio falla.
  - Done when: integración con gateway/cliente mock: mismo JSON en éxito; 200 + `authenticated: false` sin sesión válida; 503 con shape de error distinto ante caída.

- [ ] **T13. Vista `POST /panel/logout` y borrado de cookie**
  - Cubre: RF-4, RF-5, RF-7, RF-13, RF-15
  - AllowAny: invoca `LogoutPanelSession`; si el caso lo autoriza, `delete_cookie('fes_session')` (Path `/`, HttpOnly, SameSite alineado, Domain/Secure según settings); en 503 no borrar cookie; mensaje 503 en español y shape distinto del JSON anónimo.
  - Done when: logout OK borra cookie y responde no autenticado; sin sesión → 200 + borra + `authenticated: false`; fallo de cuentas → 503 y cookie intacta.

- [ ] **T14. Cablear URLs sin sombrear rutas existentes**
  - Cubre: RF-10
  - Incluir rutas `panel/login/google`, `panel/session`, `panel/logout` desde `config/urls.py` (o `identity.api.urls`) sin alterar el contrato de `GET /panel`, `GET /health/live`, `GET /health/ready`.
  - Done when: las tres nuevas rutas resuelven y las tres rutas existentes siguen respondiendo como antes.

## Pruebas de cierre y verificación

- [ ] **T15. Tests de integración del redirect y de la base URL**
  - Cubre: RF-1, RF-8, RF-11
  - Con settings de test, comprobar Location del login Google y que el cliente usa `ACCOUNT_API_BASE_URL`.
  - Done when: tests automatizados fallan si falta `return_to` correcto o si la base URL no se usa.

- [ ] **T16. Tests de integración de sesión (proxy, anónima, 503)**
  - Cubre: RF-2, RF-3, RF-12, RF-14
  - Cubrir reenvío de cookie, JSON idéntico al mock de cuentas, 200 anónimo e inválido, y 503 con cuerpo ≠ no-autenticado.
  - Done when: la matriz anterior pasa en `tests/` (unitarios + integración según el plan).

- [ ] **T17. Tests de integración de logout (OK, idempotente, fallo)**
  - Cubre: RF-4, RF-5, RF-13, RF-15
  - Cubrir llamada a cuentas + borrado de cookie; logout sin sesión; 503 sin borrar cookie.
  - Done when: los tres escenarios pasan de forma verificable (cabeceras Set-Cookie / ausencia de borrado en 503).

- [ ] **T18. Tests de no persistencia, AllowAny, CORS y smoke de health**
  - Cubre: RF-6, RF-7, RF-9, RF-10
  - Verificar ausencia de modelo/migración de cuenta en identity; endpoints AllowAny sin consulta a shops/membership; CORS origen+credentials; smoke de `/panel`, `/health/live`, `/health/ready`.
  - Done when: esos asserts/smoke pasan y documentan cobertura de RF-6, RF-7, RF-9 y RF-10.

- [ ] **T19. Cierre con `make verify`**
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
