# Plan 001 — Login del panel con la sesión de cuentas

Plan técnico de implementación de `specs/001-feat-panel-session-login/spec.md`.
Refleja el código real en `src/` de la rama `001/feat-panel-session-login`
(`identity` + `common/{health,http}`; sin módulo `shops`).

## 1. Alcance y principios

- Capacidad dueña: **identity** (puerta de sesión del panel hacia `account-api`).
- El panel **no** es dueño de la identidad ni de Google; solo redirige, consulta y
  cierra la sesión compartida. **(RF-6, RF-7)**
- No hay modelos ni migraciones de cuenta/usuario en este corte. **(RF-6)**
- No se exige membresía de vendedor ni alta de tienda en este flujo. **(RF-7)**
- Se conservan sin cambio de contrato las rutas de sesión bajo `/panel` y
  `GET /health/live` / `GET /health/ready` (implementados en `identity.api` y `common.health`).
  **(RF-10)**
- Dependencias hacia dentro: `api → application → domain`; el cliente HTTP de
  cuentas vive en `infrastructure` e implementa el puerto `AccountSessionGateway`
  de `application`.

## 2. Ubicación del código (layout real)

Todo el runtime Django vive bajo `src/` (`PYTHONPATH` incluye `src`):

```text
src/
├── config/                 # settings, urls, wsgi
├── common/
│   ├── health/views.py     # live / ready
│   └── http.py             # request_json, RemoteServiceError
└── identity/
    ├── apps.py
    ├── api/                # vistas DRF, urls, clear_session_cookie
    ├── application/        # casos de uso, puertos, DTOs
    ├── domain/             # errores y constantes (sin Django)
    └── infrastructure/     # AccountSessionClient
tests/
├── identity/               # unitarios por capa
├── common/                 # request_json
└── integration/            # flujos HTTP del panel (login/session/logout)
```

- `identity` está en `INSTALLED_APPS`.
- `config/urls.py` monta `path("panel/", include("identity.api.urls"))` y las rutas de health.
- El `Dockerfile` copia `src/` y `tests/`; no existe app `shops`.
- Health vive en `common/`; las rutas del panel viven en `identity.api`, no en `shops.views`. **(RF-10)**

## 3. Configuración por entorno

En `config/settings.py` (variables de entorno, sin secretos en código):

| Variable | Uso | RF |
|---|---|---|
| `ACCOUNTS_PUBLIC_BASE_URL` | Base **pública** para el redirect del navegador a `/accounts/login/google` (default: mismo valor que `ACCOUNT_API_BASE_URL`) | **RF-1, RF-8, RF-11** |
| `ACCOUNT_API_BASE_URL` | Base **interna** del proxy servidor→servidor (`/accounts/session`, `/accounts/logout`) | **RF-8** |
| `PANEL_PUBLIC_ORIGIN` | Único origen para `return_to` y CORS (esquema + host, sin path) | **RF-1, RF-9, RF-11** |
| `SESSION_COOKIE_DOMAIN` (opcional) | Domain al borrar `fes_session` | **RF-5, RF-15** |
| `ACCOUNT_API_TIMEOUT_SECONDS` | Timeout del cliente HTTP (default `5`) | — |

Notas:

- Login Google usa **`ACCOUNTS_PUBLIC_BASE_URL`**, no la base interna: el navegador
  debe seguir el 302 hacia un host alcanzable. **(RF-1, RF-8, RF-11)**
- Session/logout usan **`ACCOUNT_API_BASE_URL`** vía `AccountSessionClient`.
  **(RF-8)**
- Un solo origen configurable alimenta el `return_to` del login y
  `CORS_ALLOWED_ORIGINS`. **(RF-11)**
- `clear_session_cookie` usa
  `secure=bool(getattr(settings, "SESSION_COOKIE_SECURE", False))`.
  Settings no define `SESSION_COOKIE_SECURE` hoy → cae en `False` salvo override
  en tests/entorno.

Dependencias:

- `django-cors-headers` fijado en `requirements.txt`. **(RF-9)**
- Cliente HTTP con `urllib` en `common.http` (sin `httpx`/`requests`).

## 4. Contratos HTTP del panel

### 4.1 `GET /panel/login/google` — **RF-1, RF-8, RF-11**

- Vista: `GoogleLoginRedirectView` (AllowAny).
- Caso de uso: `build_google_login_redirect(ACCOUNTS_PUBLIC_BASE_URL, PANEL_PUBLIC_ORIGIN)`.
- Responde **302** a
  `{ACCOUNTS_PUBLIC_BASE_URL}/accounts/login/google?return_to=<PANEL_PUBLIC_ORIGIN>`
  (URL-encoded). **No** usa `ACCOUNT_API_BASE_URL` en este camino.
- `return_to` = origen público del panel (no el host de la API). **(RF-1, RF-11)**
- No validar membresía ni tienda. **(RF-7)**

### 4.2 `GET /panel/session` — **RF-2, RF-3, RF-8, RF-12, RF-14**

- Vista: `PanelSessionView`; caso: `resolve_panel_session`.
- Reenvía `fes_session` a `GET {ACCOUNT_API_BASE_URL}/accounts/session`. **(RF-2, RF-8)**
- Si account-api responde OK, el panel devuelve **el mismo status y JSON**. **(RF-3)**
- Sin cookie o sesión inválida: propaga el JSON de cuentas con
  `authenticated: false` y **200**. **(RF-14)**
- Timeout / red / 5xx / JSON no usable → **503** con cuerpo en español distinto
  del JSON de no autenticado (`error` + `message`). **(RF-12)**

### 4.3 `POST /panel/logout` — **RF-4, RF-5, RF-8, RF-13, RF-15**

- Vista: `PanelLogoutView`; caso: `logout_panel_session`.
- Llama a `POST {ACCOUNT_API_BASE_URL}/accounts/logout` reenviando `fes_session`
  si existe. **(RF-4, RF-8)**
- Si el gateway no lanza: la vista **proxy** status/body de cuentas y **siempre**
  borra `fes_session` en la respuesta del panel (`clear_cookie=True`). El panel
  es quien limpia la cookie del navegador; no depende de que cuentas la borre
  en su Set-Cookie. **(RF-5, RF-15)**
- Cuerpo vacío de cuentas (p. ej. **204 No Content**) se normaliza a `{}` en
  `common.http.request_json`; el panel reenvía ese status/body tal cual. Los
  tests de integración suelen mockear `200` + `{"authenticated": false}` para
  afirmar RF-15; el código real no reescribe el JSON de logout.
- Sin sesión activa: se llama igual a cuentas; si responde OK → 200 (o el status
  que envíe cuentas), se borra cookie. **(RF-15)**
- Si account-api falla (timeout/5xx/red): **503** en español, **sin** borrar
  `fes_session`. **(RF-13)**

### 4.4 Rutas conservadas — **RF-10**

- `GET /health/live` → `common.health.views.live`
- `GET /health/ready` → `common.health.views.ready`
- Rutas del panel: `panel/login/google`, `panel/session`, `panel/logout`.

## 5. Capas internas (clean architecture)

### 5.1 Domain — **RF-6, RF-7, RF-12, RF-13**

- `AccountServiceUnavailable` (mapea a 503).
- `SESSION_COOKIE_NAME = "fes_session"`.
- Sin imports de Django, DRF, settings ni HTTP.
- Sin entidad persistida ni reglas de membresía. **(RF-6, RF-7)**

### 5.2 Application — **RF-2, RF-3, RF-4, RF-5, RF-12, RF-13, RF-14, RF-15**

Casos de uso (funciones reales):

1. **`resolve_panel_session`** — `gateway.get_session(cookie)`; propaga payload;
   cualquier fallo no tipado → `AccountServiceUnavailable`. **(RF-2, RF-3, RF-12, RF-14)**
2. **`logout_panel_session`** — `gateway.logout(cookie)`; si OK,
   `clear_cookie=True` siempre; si falla el servicio, propaga
   `AccountServiceUnavailable` (la vista no borra cookie). **(RF-4, RF-5, RF-13, RF-15)**
3. **`build_google_login_redirect`** — combina base URL + path + `return_to`.
   **(RF-1, RF-8, RF-11)**

Puerto `AccountSessionGateway`:

- `get_session(fes_session: str | None) -> SessionPayload`
- `logout(fes_session: str | None) -> LogoutResult`

### 5.3 Infrastructure — **RF-8, RF-12, RF-13**

- `AccountSessionClient(base_url=ACCOUNT_API_BASE_URL, timeout_seconds=...)`.
  - `GET /accounts/session` con `Cookie: fes_session=...` si existe.
  - `POST /accounts/logout` con la misma cookie.
- Errores vía `common.http.RemoteServiceError` → `AccountServiceUnavailable`.
- 200/4xx con JSON de objeto → resultado de aplicación; cuerpo vacío → `{}`.

### 5.4 API (DRF) — **RF-1, RF-3, RF-5, RF-9, RF-11, RF-12, RF-13, RF-14, RF-15**

- Vistas: `GoogleLoginRedirectView`, `PanelSessionView`, `PanelLogoutView`.
- `permission_classes = [AllowAny]`; `authentication_classes = []`. **(RF-7)**
- 503: `{"error": "servicio_no_disponible", "message": "..."}` en español.
  **(RF-12, RF-13)**
- Cookie: `clear_session_cookie` (Path `/`, HttpOnly, SameSite=Lax, Domain y
  Secure según settings/getattr).

## 6. CORS con credenciales — **RF-9, RF-11**

- `corsheaders` en `INSTALLED_APPS` y `MIDDLEWARE` (antes de `CommonMiddleware`).
- `CORS_ALLOW_CREDENTIALS = True`.
- `CORS_ALLOWED_ORIGINS = [PANEL_PUBLIC_ORIGIN]` (sin `*`).

## 7. Cookie `fes_session` — **RF-5, RF-13, RF-15**

- Nombre fijo: `fes_session`.
- Borrado tras logout exitoso (gateway OK), con o sin cookie de entrada.
- Nunca borrar en respuesta 503 de logout. **(RF-13)**
- Secure: `getattr(settings, "SESSION_COOKIE_SECURE", False)`.
- El panel no emite la cookie en el login; solo la reenvía y la invalida al salir.

## 8. Qué no hacer (fuera de alcance de la spec)

- OAuth Google, callback, emisión de identidad.
- Modelos de cuenta, tablas de sesión propias, Keycloak.
- Pantallas (`panel-web`).
- Gates de membresía/tienda. **(RF-7)**
- Cambios de manifiestos en `infra` salvo documentar variables esperadas.

## 9. Pruebas (cobertura por RF)

| Área | Qué verificar | RF |
|---|---|---|
| Redirect login | Location usa `ACCOUNTS_PUBLIC_BASE_URL` + `return_to` = origen público | **RF-1, RF-11** |
| Base URL proxy | Cliente usa `ACCOUNT_API_BASE_URL` | **RF-8** |
| Session proxy | Reenvío de `fes_session` y mismo JSON que el mock de cuentas | **RF-2, RF-3** |
| Session anónima | Sin cookie / inválida → 200 + `authenticated: false` | **RF-14** |
| Session caída | Fallo del cliente → 503 y cuerpo ≠ no-autenticado | **RF-12** |
| Logout OK | Llama a cuentas y el panel borra cookie | **RF-4, RF-5** |
| Logout sin sesión | Respuesta OK + borra cookie (tests asumen JSON `authenticated: false`) | **RF-15** |
| Logout fallo | 503, cookie intacta | **RF-13** |
| Sin persistencia | No hay modelo/migración de cuenta en identity | **RF-6** |
| Sin membresía | Endpoints AllowAny; no hay módulo shops | **RF-7** |
| CORS | Origen del panel + credentials | **RF-9, RF-11** |
| Smoke | `/health/live`, `/health/ready` desde `common` | **RF-10** |

Criterios de automatización:

- Unitarios de application/domain con gateway fake.
- Unitarios del cliente HTTP / `common.http` con servidor mock.
- Integración DRF/`APIClient` para los tres endpoints y conservación de health.
- Ejecutar `make verify` al cerrar la implementación.

## 10. Orden de implementación sugerido

1. Layout `src/` + settings (`ACCOUNT_API_BASE_URL`, `ACCOUNTS_PUBLIC_BASE_URL`,
   `PANEL_PUBLIC_ORIGIN`) + CORS (**RF-8, RF-9, RF-11**).
2. `common/{health,http}` y módulo `identity` con capas (**RF-8, RF-10, RF-12, RF-13**).
3. Casos de uso session/logout/redirect (**RF-1–RF-5, RF-12–RF-15**).
4. Vistas y rutas `/panel/login/google`, `/panel/session`, `/panel/logout`
   (**RF-1–RF-5, RF-7, RF-10**).
5. Borrado de cookie y matriz de tests (**RF-5, RF-6, RF-10, RF-12–RF-15**).
6. Dockerfile / registro de app / `make verify`.

## 11. Mapa resumen RF → entregable

| RF | Entregable principal |
|---|---|
| RF-1 | Redirect `GET /panel/login/google` → `ACCOUNTS_PUBLIC_BASE_URL` + `return_to` |
| RF-2 | Reenvío de `fes_session` a `GET /accounts/session` |
| RF-3 | Respuesta JSON/status idéntica a la de cuentas |
| RF-4 | `POST /panel/logout` llama a `POST /accounts/logout` |
| RF-5 | Panel borra `fes_session` tras logout exitoso |
| RF-6 | Sin modelos/persistencia de cuenta en panel |
| RF-7 | AllowAny; sin chequeo de membresía/tienda / sin shops |
| RF-8 | Proxy con `ACCOUNT_API_BASE_URL`; redirect con `ACCOUNTS_PUBLIC_BASE_URL` |
| RF-9 | CORS credentials desde origen del panel |
| RF-10 | Health checks `/health/live`, `/health/ready` en `common` |
| RF-11 | Un solo `PANEL_PUBLIC_ORIGIN` para `return_to` y CORS |
| RF-12 | 503 distinto de JSON anónimo en fallo de consulta |
| RF-13 | 503 sin borrar cookie en fallo de logout |
| RF-14 | 200 + `authenticated: false` sin sesión válida |
| RF-15 | Logout idempotente: panel borra cookie tras OK de cuentas |
