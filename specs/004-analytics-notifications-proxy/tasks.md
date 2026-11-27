# Tasks 004 — Proxy del panel hacia analítica y notificaciones

## Fase A — Configuración y contratos

- [x] **T1. Agregar URLs y timeouts a `settings.py`.** Cubre RF-8, RF-9.
  Done when: existen defaults locales y de clúster.
- [x] **T2. Crear ports y clients HTTP.** Cubre RF-5, RF-7.
  Done when: `timeline`, `metrics` y `open_feed` tienen adaptadores con timeout y errores controlados.

## Fase B — Vistas y rutas

- [x] **T3. Crear app `analytics` con timeline y metrics.** Cubre RF-1, RF-2, RF-4.
  Done when: `GET /panel/analytics/timeline` y `/metrics` reenvían la tienda resuelta.
- [x] **T4. Crear app `notifications` con el feed SSE.** Cubre RF-3, RF-6.
  Done when: el stream reenvía `text/event-stream` sin buffering y corta al desconectar.
- [x] **T5. Registrar rutas en `config/urls.py`.** Cubre RF-1, RF-2, RF-3.
  Done when: las tres rutas responden bajo `/panel`.

## Fase C — Errores y pruebas

- [x] **T6. Mapear errores de upstream.** Cubre RF-7, RF-9.
  Done when: upstream caído devuelve 502 y timeout 504 sin detalles internos.
- [x] **T7. Tests de clients y vistas.** Cubre RF-1…RF-7.
  Done when: cubren 200, 502, headers SSE y streaming.
- [x] **T8. Verificar rutas existentes y `make verify`.** Cubre RF-10…RF-13.
  Done when: identidad, catálogo, tienda y health siguen igual.
