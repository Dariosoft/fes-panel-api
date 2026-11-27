# Plan 004 — Proxy del panel hacia analítica y notificaciones

## 1. Resumen

Agregar dos gateways HTTP y tres vistas finas que reenvían a `analytics-api` y
`notifications-api`, reutilizando la resolución de tienda y sesión existente. El feed SSE se
transmite sin buffering con `StreamingHttpResponse` y un iterador que cierra aguas arriba al
desconectar. Cubre RF-1 … RF-13.

## 2. Configuración

`src/config/settings.py`:

- `ANALYTICS_API_BASE_URL` default `http://analytics-api.apps.svc.cluster.local:8080`.
- `NOTIFICATIONS_API_BASE_URL` default `http://notifications-api.apps.svc.cluster.local:8080`.
- `ANALYTICS_API_TIMEOUT_SECONDS` default `5`.

## 3. Capas (arquitectura del panel)

- `common/ports/analytics_api_gateway.py`: protocolo con `timeline`, `metrics`.
- `common/ports/notifications_api_gateway.py`: protocolo con `open_feed`.
- `common/infrastructure/clients/analytics_api_client.py` y
  `notifications_api_client.py`: `requests` con timeout y errores controlados.
- `common/errors/analytics_api_unavailable.py`, `notifications_api_unavailable.py`.
- `analytics/` app nueva: `api/views/panel_analytics.py`, `api/urls.py`;
  `use_cases/get_timeline.py`, `get_metrics.py`, `resolve_panel_tenant.py`.
- `notifications/` app nueva: `api/views/panel_feed.py`, `api/urls.py`;
  `use_cases/open_feed.py`, `resolve_panel_tenant.py`.

La resolución de tienda reutiliza lo que ya usan `catalog`/`shops`; no se inventa autenticación.

## 4. Rutas

`config/urls.py`:

- `path("panel/analytics/", include("analytics.api.urls"))`
- `path("panel/notifications/", include("notifications.api.urls"))`

Vistas:

- `GET /panel/analytics/timeline` → upstream `/analytics/timeline` con `tenantId`.
- `GET /panel/analytics/metrics` → upstream `/analytics/metrics`.
- `GET /panel/notifications/feed` → upstream `/notifications/feed` en streaming.

## 5. SSE

`panel_feed.py`:

- valida tienda/sesión;
- abre la conexión upstream con `requests.get(..., stream=True)`;
- devuelve `StreamingHttpResponse` con `content_type="text/event-stream"`,
  `Cache-Control: no-cache` y `X-Accel-Buffering: no`;
- itera `raw.stream()`; al cerrar el cliente, cierra la respuesta upstream.

## 6. Errores

- `requests.RequestException` → 502 con JSON `{"error": "..."} ` sin detalles internos.
- Timeout → 504.
- Tienda no resuelta → comportamiento actual (400/404).

## 7. Verificación

- Tests de gateways con `responses`/mock.
- Tests de vistas: timeline/metrics 200, upstream caído 502, feed headers y streaming.
- `make verify`.

## 8. Trazabilidad RF → plan

| RF | Sección |
|---|---|
| RF-1, RF-2, RF-3 | §4 |
| RF-4, RF-5 | §3, §4 |
| RF-6 | §5 |
| RF-7 | §6 |
| RF-8 | §2 |
| RF-9 | §2, §6 |
| RF-10, RF-11 | §3 |
| RF-12, RF-13 | §3, §4 |
