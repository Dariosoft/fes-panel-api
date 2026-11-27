# Spec 004 — Proxy del panel hacia analítica y notificaciones

## Contexto y objetivo

El panel del vendedor necesita historial, métricas y feed en vivo, pero `panel-api` no debe consumir
Kafka ni RabbitMQ ni replicar datos. Este corte expone bajo `/panel` un proxy hacia `analytics-api` y
`notifications-api`, resolviendo la tienda y la sesión como ya hace con catálogo y cuentas, y
preservando el streaming del feed SSE.

## Usuarios / actores

- Vendedor que usa el panel.
- `panel-web`, que consume las rutas del panel.
- `analytics-api` y `notifications-api`, aguas arriba.
- Equipo de operaciones.

## Historias de usuario

- H1: Como vendedor quiero ver historial y métricas sin que el panel hable con Kafka.
- H2: Como vendedor quiero ver el feed en vivo a través del panel.
- H3: Como operador quiero que el proxy preserve la sesión y la tienda actuales.
- H4: Como operador quiero errores claros si un servicio aguas arriba no responde.

## Requisitos funcionales (criterios de aceptación en EARS)

- RF-1: EL SISTEMA expondrá `GET /panel/analytics/timeline`.
- RF-2: EL SISTEMA expondrá `GET /panel/analytics/metrics`.
- RF-3: EL SISTEMA expondrá `GET /panel/notifications/feed` como `text/event-stream`.
- RF-4: EL SISTEMA resolverá la tienda y la sesión del vendedor como en las rutas actuales del panel.
- RF-5: EL SISTEMA reenviará a `analytics-api` y `notifications-api` la tienda resuelta.
- RF-6: EL SISTEMA reenviará el feed SSE sin buffering y cerrando la conexión aguas arriba cuando el cliente se desconecte.
- RF-7: SI el servicio aguas arriba no responde, ENTONCES EL SISTEMA devolverá un error claro sin exponer detalles internos.
- RF-8: EL SISTEMA obtendrá las URLs desde `ANALYTICS_API_BASE_URL` y `NOTIFICATIONS_API_BASE_URL`.
- RF-9: EL SISTEMA aplicará un timeout acotado a las consultas que no son streaming.
- RF-10: EL SISTEMA no consumirá Kafka ni RabbitMQ.
- RF-11: EL SISTEMA no persistirá datos de analítica ni notificaciones.
- RF-12: EL SISTEMA conservará sin cambios las rutas existentes de identidad, catálogo y tienda.
- RF-13: EL SISTEMA conservará `/health/live`, `/health/ready` y las variables de entorno existentes.

## Requisitos no funcionales

- Streaming sin buffering.
- Sin secretos nuevos.
- Sin acceso a bases de otros dominios.
- Compatibilidad con la sesión y CORS actuales.

## Casos límite

- Cliente SSE que se desconecta: se cierra la conexión aguas arriba.
- Upstream caído: error 502 con mensaje controlado.
- Timeout de consulta: error controlado.
- Tienda no resuelta: se conserva el comportamiento actual.

## Fuera de alcance

- Consumir Kafka o RabbitMQ.
- Proyectar o persistir analítica/notificaciones.
- Cambiar autenticación o sesión.
- Cambiar las rutas existentes de identidad, catálogo o tienda.
- Endpoints nuevos fuera de los tres del proxy.

## Criterios de finalización

- `make verify` en verde.
- Demo: timeline y métricas responden a través del panel; el feed SSE llega en vivo y corta al desconectar; upstream caído devuelve 502 controlado.

## Dudas abiertas

Ninguna.
