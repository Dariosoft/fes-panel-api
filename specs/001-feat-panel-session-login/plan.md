# Plan 001 — Login del panel con la sesión de cuentas

Plan técnico de implementación de `specs/001-feat-panel-session-login/spec.md`.
No implementa la funcionalidad; solo descompone el trabajo respetando
`panel-api-architecture`, `clean-architecture` y `django-patterns`, y el código
actual (`config/`, `shops/`, layout aún fuera de `src/`).

## 1. Alcance y principios

- Capacidad dueña: **identity** (puerta de sesión del panel hacia `account-api`).
- El panel **no** es dueño de la identidad ni de Google; solo redirige, consulta y
  cierra la sesión compartida. **(RF-6, RF-7)**
- No hay modelos ni migraciones de cuenta/usuario en este corte. **(RF-6)**
- No se exige membresía de vendedor ni alta de tienda en este flujo. **(RF-7)**
- Se conservan sin cambio de contrato `GET /panel`, `GET /health/live` y
  `GET /health/ready` (hoy en `shops.views`). **(RF-10)**
- Dependencias hacia dentro: `api → application → domain`; el cliente HTTP de
  cuentas vive en `infrastructure` e implementa un puerto de `application`.

## 2. Ubicación del código (layout actual)

El repositorio aún no migró a `src/`. Para no migrar parcialmente `shops`/`config`,
este plan coloca el módulo al mismo nivel que `shops`, con capas internas limpias:

```text
identity/
├── apps.py
├── api/                 # vistas DRF, urls, cookie HTTP, CORS de presentación
├── application/         # casos de uso, puertos, DTOs
├── domain/              # errores y reglas puras (sin Django)
└── infrastructure/      # cliente HTTP a account-api, lectura de settings
tests/
├── identity/            # unitarios por capa
└── integration/         # flujos HTTP del panel (login/session/logout)
```

- Registrar `identity` en `INSTALLED_APPS`.
- Incluir las rutas de identity bajo el prefijo `/panel/...` desde `config/urls.py`
  (o `include` desde `identity.api.urls`).
- Actualizar `Dockerfile` para copiar `identity/` (y `tests/` si la verificación
  los necesita en la imagen de build).
- No mover health a `common/health` en este corte (queda fuera; solo se conserva).
  **(RF-10)**

## 3. Configuración por entorno

Añadir en `config/settings.py` (variables de entorno, sin secretos en código):

| Variable | Uso | RF |
|---|---|---|
| `ACCOUNT_API_BASE_URL` | Base interna del servicio de cuentas (p. ej. `http://account-api.apps.svc.cluster.local:8080`) | **RF-8** |
| Origen público del panel (nombre propuesto: `PANEL_PUBLIC_ORIGIN`) | Único origen para `return_to` y CORS (esquema + host, sin path) | **RF-1, RF-9, RF-11** |
| `SESSION_COOKIE_DOMAIN` (opcional pero recomendado) | Mismos atributos al borrar `fes_session` que usó account-api al emitirla | **RF-5, RF-15** |

Notas:

- Un solo origen configurable alimenta tanto el `return_to` del login Google como
  la lista CORS con credenciales. **(RF-11)**
- La inyección de `ACCOUNT_API_BASE_URL` en el clúster es de `infra` (ya prevista);
  este plan solo la consume en settings.
- Timeout del cliente HTTP: valor fijo razonable o env opcional
  (`ACCOUNT_API_TIMEOUT_SECONDS`); no es un RF, pero evita cuelgues.

Dependencias:

- Añadir `django-cors-headers` fijado en `requirements.txt` para CORS con
  credenciales. **(RF-9)**
- Preferir cliente HTTP con biblioteca estándar (`urllib`) en infrastructure para
  no añadir dependencia de red innecesaria; si se elige `httpx`/`requests`, fijarla.

## 4. Contratos HTTP del panel

### 4.1 `GET /panel/login/google` — **RF-1, RF-8, RF-11**

- Vista en `identity.api` (AllowAny).
- Sin llamar a account-api con el cuerpo de la petición: construir URL
  `{ACCOUNT_API_BASE_URL}/accounts/login/google?return_to=<PANEL_PUBLIC_ORIGIN>`
  (URL-encoded) y responder **302/303** al navegador.
- `return_to` = origen público del panel (no el host de la API). **(RF-1, RF-11)**
- No validar membresía ni tienda. **(RF-7)**

### 4.2 `GET /panel/session` — **RF-2, RF-3, RF-8, RF-12, RF-14**

- Reenviar la cookie `fes_session` del request hacia
  `GET {ACCOUNT_API_BASE_URL}/accounts/session`. **(RF-2, RF-8)**
- Si account-api responde OK, devolver al cliente **el mismo JSON** (status y
  cuerpo alineados con la respuesta de cuentas; tipicamente 200). **(RF-3)**
- Sin cookie o sesión inválida: propagar el JSON de cuentas con
  `authenticated: false` y **200** (no inventar otro shape). **(RF-14)**
- Si account-api no está disponible o falla de forma no recuperable (timeout,
  5xx, error de red, cuerpo no usable): responder **503** con cuerpo de error
  **distinto** del JSON de no autenticado (mensaje en español). **(RF-12)**

### 4.3 `POST /panel/logout` — **RF-4, RF-5, RF-8, RF-13, RF-15**

- Con sesión activa (hay cookie / account-api confirma cierre): llamar a
  `POST {ACCOUNT_API_BASE_URL}/accounts/logout` reenviando `fes_session`.
  **(RF-4, RF-8)**
- Si el cierre en cuentas se completa: borrar `fes_session` en la respuesta al
  navegador (Path `/`, SameSite alineado, Domain si está configurado, HttpOnly)
  y devolver JSON coherente con no autenticado (`authenticated: false`).
  **(RF-5)**
- Sin sesión activa: **200**, borrar `fes_session` de todas formas y responder
  `authenticated: false` (idempotente). **(RF-15)**
- Si account-api falla al cerrar: **503** con cuerpo de error distinto del JSON
  de no autenticado, **sin** borrar `fes_session`. **(RF-13)**

### 4.4 Rutas existentes — **RF-10**

- Mantener `path("panel", ...)`, `health/live`, `health/ready` en `config/urls.py`.
- Las nuevas rutas no deben sombrear `GET /panel` exacto (usar
  `panel/login/google`, `panel/session`, `panel/logout`).

## 5. Capas internas (clean architecture)

### 5.1 Domain — **RF-6, RF-7, RF-12, RF-13**

- Errores tipados, p. ej. `AccountServiceUnavailable` (para mapear a 503).
- Constantes de negocio mínimas (`SESSION_COOKIE_NAME = "fes_session"`).
- Sin imports de Django, DRF, settings ni HTTP.
- Política implícita: cualquier cuenta Google vía sesión compartida es aceptable;
  no hay regla de membresía aquí. **(RF-7)**
- No hay entidad de “cuenta del panel” persistida. **(RF-6)**

### 5.2 Application — **RF-2, RF-3, RF-4, RF-5, RF-12, RF-13, RF-14, RF-15**

Casos de uso (nombres orientativos):

1. **ResolvePanelSession** — obtiene el payload de sesión vía puerto
   `AccountSessionGateway.get_session(cookie)` y lo devuelve tal cual; traduce
   fallos de infraestructura a error de dominio de indisponibilidad. **(RF-2, RF-3, RF-12, RF-14)**
2. **LogoutPanelSession** — solicita cierre vía gateway; indica si debe
   borrarse la cookie (sí si éxito o ya sin sesión; no si fallo del servicio).
   **(RF-4, RF-5, RF-13, RF-15)**
3. **BuildGoogleLoginRedirect** — puro: combina base URL + path + `return_to`.
   **(RF-1, RF-8, RF-11)**

Puerto (Protocol) en application, implementado en infrastructure:

- `get_session(fes_session: str | None) -> SessionPayload`
- `logout(fes_session: str | None) -> LogoutResult`

La application **no** importa DRF ni el cliente HTTP concreto.

### 5.3 Infrastructure — **RF-8, RF-12, RF-13**

- `AccountSessionClient`: HTTP a `ACCOUNT_API_BASE_URL`.
  - `GET /accounts/session` con header `Cookie: fes_session=...` si existe.
  - `POST /accounts/logout` con la misma cookie.
- Mapear timeouts / errores de red / 5xx → `AccountServiceUnavailable`.
- 200 con JSON de cuentas (autenticado o no) → resultado de aplicación, sin
  reinterpretar el payload más allá de lo necesario para logout idempotente.
- Lectura de settings solo aquí (o en un adapter de config), no en domain.

### 5.4 API (DRF) — **RF-1, RF-3, RF-5, RF-9, RF-11, RF-12, RF-13, RF-14, RF-15**

- Vistas delgadas: parsear cookie, invocar caso de uso, formar `Response` /
  `HttpResponseRedirect`, aplicar `delete_cookie` cuando el caso de uso lo indique.
- `permission_classes = [AllowAny]` en los tres endpoints. **(RF-7)**
- Cuerpo 503 en español, shape distinto de
  `{"authenticated": false, ...}`. **(RF-12, RF-13)**
- No llamar a account-api desde la vista directamente.

## 6. CORS con credenciales — **RF-9, RF-11**

- Instalar y activar `corsheaders` en `INSTALLED_APPS` y `MIDDLEWARE`
  (antes de `CommonMiddleware`, patrón Django habitual).
- `CORS_ALLOW_CREDENTIALS = True`.
- `CORS_ALLOWED_ORIGINS` = lista de un solo elemento: `PANEL_PUBLIC_ORIGIN`.
- No abrir `*` con credenciales.
- Asegurar que `POST /panel/logout` y `GET /panel/session` respondan a
  preflight si el navegador lo exige (métodos/headers necesarios para el cliente
  `panel-web`).

## 7. Cookie `fes_session` — **RF-5, RF-13, RF-15**

- Nombre fijo: `fes_session`.
- Borrado solo cuando el caso de uso lo autorice (éxito o logout sin sesión).
- Nunca borrar en respuesta 503 de logout. **(RF-13)**
- Atributos de borrado alineados con la cookie compartida (Path `/`, HttpOnly,
  SameSite=Lax, Domain desde env si aplica, Secure según entorno HTTPS).
- El panel no emite la cookie de sesión en el login (la emite account-api tras
  Google); este sistema solo la reenvía y, al salir, la invalida en cliente.

## 8. Qué no hacer (fuera de alcance de la spec)

- OAuth Google, callback, emisión de identidad.
- Modelos de cuenta, tablas de sesión propias, Keycloak.
- Pantallas (responsabilidad de `panel-web`).
- Gates de membresía/tienda en estos endpoints. **(RF-7)**
- Cambios de manifiestos en `infra` salvo documentar variables esperadas;
  la publicación de `ACCOUNT_API_BASE_URL` ya es de la spec de infra.

## 9. Pruebas (cobertura por RF)

| Área | Qué verificar | RF |
|---|---|---|
| Redirect login | `GET /panel/login/google` → Location a `/accounts/login/google` con `return_to` = origen público | **RF-1, RF-11** |
| Base URL | Cliente usa `ACCOUNT_API_BASE_URL` | **RF-8** |
| Session proxy | Reenvío de `fes_session` y mismo JSON que el mock de cuentas | **RF-2, RF-3** |
| Session anónima | Sin cookie / inválida → 200 + `authenticated: false` | **RF-14** |
| Session caída | Fallo del cliente → 503 y cuerpo ≠ no-autenticado | **RF-12** |
| Logout OK | Llama a cuentas y borra cookie | **RF-4, RF-5** |
| Logout sin sesión | 200, borra cookie, `authenticated: false` | **RF-15** |
| Logout fallo | 503, cookie intacta | **RF-13** |
| Sin persistencia | No hay modelo/migración de cuenta en identity | **RF-6** |
| Sin membresía | Endpoints AllowAny; no consultan shops/membership | **RF-7** |
| CORS | Origen del panel + credentials | **RF-9, RF-11** |
| Smoke | `GET /panel`, `/health/live`, `/health/ready` siguen resolviendo | **RF-10** |

Criterios de automatización:

- Unitarios de application/domain con gateway fake.
- Unitarios del cliente HTTP con servidor mock / respuestas controladas.
- Integración DRF/`APIClient` para los tres endpoints y conservación de health/panel.
- Ejecutar `make verify` al cerrar la implementación.

## 10. Orden de implementación sugerido

1. Settings + `django-cors-headers` + variables `ACCOUNT_API_BASE_URL` y
   `PANEL_PUBLIC_ORIGIN` (**RF-8, RF-9, RF-11**).
2. Módulo `identity` con capas y puerto; cliente HTTP (**RF-8, RF-12, RF-13**).
3. Casos de uso session/logout/redirect (**RF-1–RF-5, RF-12–RF-15**).
4. Vistas y rutas `/panel/login/google`, `/panel/session`, `/panel/logout`
   (**RF-1–RF-5, RF-7, RF-10**).
5. Borrado de cookie y matriz de tests (**RF-5, RF-6, RF-10, RF-12–RF-15**).
6. Dockerfile / registro de app / `make verify`.

## 11. Mapa resumen RF → entregable

| RF | Entregable principal |
|---|---|
| RF-1 | Redirect `GET /panel/login/google` → account-api con `return_to` |
| RF-2 | Reenvío de `fes_session` a `GET /accounts/session` |
| RF-3 | Respuesta JSON idéntica a la de cuentas |
| RF-4 | `POST /panel/logout` llama a `POST /accounts/logout` |
| RF-5 | `delete_cookie('fes_session')` tras logout exitoso |
| RF-6 | Sin modelos/persistencia de cuenta en panel |
| RF-7 | AllowAny; sin chequeo de membresía/tienda |
| RF-8 | Settings + cliente basados en `ACCOUNT_API_BASE_URL` |
| RF-9 | CORS credentials desde origen del panel |
| RF-10 | Rutas `/panel`, `/health/live`, `/health/ready` intactas |
| RF-11 | Un solo `PANEL_PUBLIC_ORIGIN` para `return_to` y CORS |
| RF-12 | 503 distinto de JSON anónimo en fallo de consulta |
| RF-13 | 503 sin borrar cookie en fallo de logout |
| RF-14 | 200 + `authenticated: false` sin sesión válida |
| RF-15 | Logout idempotente: 200, borra cookie, `authenticated: false` |
