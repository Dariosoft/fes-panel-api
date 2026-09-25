# Tareas 001 — Entrar al panel con la misma cuenta

Implementación paso a paso del plan. Cada tarea ~20–30 min. Orden por dependencias.
Mensajes visibles al cliente: español. Sin cuenta local del panel. La spec manda sobre notas viejas que difieren identidad.

---

## Fundación

- [x] **T1 — Crear app `identity` y registrarla**
  - RFs: (infraestructura; habilita RF-7)
  - Crear la app Django `identity` (o nombre equivalente en inglés), sin modelos de cuenta.
  - Registrarla en `INSTALLED_APPS` y dejar el esqueleto listo (apps, urls vacías).
  - Done when: la app importa sin error y aparece en `INSTALLED_APPS`; `python manage.py check` pasa.

- [x] **T2 — Configurar URL base y timeouts hacia account-api**
  - RFs: RF-2
  - Añadir variables de entorno para URL base de `account-api` y timeouts del cliente HTTP.
  - Documentar en settings qué se lee del entorno; sin secretos en código.
  - Done when: con variables de entorno definidas, settings expone URL y timeout; sin inventar valores secretos en el repo.

- [x] **T3 — Cliente HTTP tipificado hacia account-api**
  - RFs: RF-2, RF-11, RF-12
  - Módulo dedicado (p. ej. `identity/account_client.py`) con métodos tipados: confirmar acceso Google / abrir sesión, consultar identidad, cerrar sesión.
  - Mapear rechazo de negocio, timeout, error de conexión y 5xx a excepciones distintas.
  - Done when: el cliente puede invocarse en tests unitarios con respuestas mockeadas y distingue rechazo vs indisponibilidad.

- [x] **T4 — Servicios de dominio entrar / salir / quién soy**
  - RFs: RF-2, RF-5, RF-6, RF-8
  - Implementar `identity/services.py` que orquesta las tres operaciones vía el cliente; sin `User.objects.create` ni tablas de cuenta.
  - Done when: tests unitarios del servicio (con cliente mockeado) cubren éxito de entrar, salir y quién soy autenticado/anónimo sin escrituras locales de cuenta.

---

## Endpoints: quién soy y salir

- [x] **T5 — Endpoint «quién soy» anónimo**
  - RFs: RF-1, RF-8
  - Vista DRF + ruta bajo `/panel/...` que, sin sesión, responde no autenticado sin inventar identidad.
  - Done when: petición sin sesión → estado no autenticado; no hay nombre ni correo inventados; test automatizado en verde (marca RF-1/RF-8).

- [x] **T6 — Endpoint «quién soy» autenticado**
  - RFs: RF-8, RF-13
  - Con sesión compartida activa (simulada vía mock de account-api), devolver nombre y correo de Google.
  - Done when: test con sesión mockeada → payload con nombre y correo; sin sesión no los inventa.

- [x] **T7 — Endpoint salir autenticado**
  - RFs: RF-6, RF-13
  - Vista/ruta de salir que pide el cierre de sesión compartida a account-api y deja al cliente no autenticado.
  - Done when: tras salir, «quién soy» es anónimo y el mock confirma que se invocó el cierre compartido; test en verde (RF-6, RF-13).

- [x] **T8 — Salir sin autenticación (idempotente)**
  - RFs: RF-10
  - Salir anónimo responde éxito y permanece sin autenticación.
  - Done when: test sin sesión → HTTP de éxito; «quién soy» sigue anónimo; no falla (RF-10).

---

## Endpoint entrar (Google)

- [x] **T9 — Endpoint entrar: contrato solo Google**
  - RFs: RF-4, RF-7
  - Exponer ruta de entrada bajo `/panel/...` que acepta únicamente el flujo Google acordado; rechazar u omitir otros proveedores.
  - Done when: petición con proveedor distinto de Google no autentica (o no se soporta); test marca RF-4; la ruta queda bajo la puerta `/panel`.

- [x] **T10 — Entrar exitoso abre sesión compartida**
  - RFs: RF-2, RF-5
  - Tras confirmación de account-api, reflejar estado autenticado e identidad; no crear cuenta local.
  - Done when: mock de confirmación → respuesta autenticada con identidad; se invocó abrir/confirmar sesión en el cliente; cero escrituras locales de cuenta (RF-2, RF-5).

- [x] **T11 — Entrar sin exigir membresía previa**
  - RFs: RF-3
  - Autorizar el entrar solo por reconocimiento de account-api; no consultar modelos de membresía/`Shop`.
  - Done when: test con cuenta reconocida por el mock y sin membresía en `panel` → entrar exitoso (RF-3).

- [x] **T12 — Reentrar reemplaza la cuenta actual**
  - RFs: RF-9
  - Un segundo entrar exitoso deja como actual la cuenta con la que se acaba de entrar.
  - Done when: secuencia autenticado A → entrar B → «quién soy» es B; test en verde (RF-9).

- [x] **T13 — Rechazo de Google no autentica**
  - RFs: RF-11
  - Si account-api rechaza el acceso, no hay sesión autenticada; mensaje de error en español.
  - Done when: mock de rechazo → no autenticado; cuerpo con mensaje en español; test (RF-11).

- [x] **T14 — Indisponibilidad de account-api al entrar**
  - RFs: RF-12
  - Timeout, conexión fallida o 5xx al entrar → no autenticar; informar que el acceso no pudo completarse (español).
  - Done when: simulación de timeout/5xx → no autenticado + mensaje esperado; test (RF-12).

---

## Autenticación opcional y límites de la puerta

- [x] **T15 — Panel usable sin login en rutas existentes**
  - RFs: RF-1
  - No añadir `IsAuthenticated` global ni middleware que bloquee `/panel` u otras rutas existentes.
  - Done when: `GET /panel` (y health si aplica) responden sin sesión; test confirma que no exigen autenticación (RF-1).

- [x] **T16 — Única puerta del panel (entrar / salir / quién soy)**
  - RFs: RF-7
  - Solo estos endpoints de `panel-api` sirven al cliente del panel para identidad; sin atajos contradictorios.
  - Done when: las tres operaciones están bajo `/panel/...` y un test/contrato documenta que son la puerta única del panel (RF-7).

- [x] **T17 — No atender entrada de la tienda**
  - RFs: RF-14
  - No implementar ni exponer rutas/flujos de «login tienda» en esta API.
  - Done when: no existen endpoints de entrada de tienda; test negativo o aserción de rutas confirma ausencia (RF-14).

- [x] **T18 — Tras salir, solicitudes posteriores anónimas**
  - RFs: RF-6, RF-13
  - Flujo integrado: entrar → salir → «quién soy» anónimo; el cierre invalidó la sesión compartida (mock).
  - Done when: test de secuencia pasa; opcionalmente el mock muestra que la misma sesión ya no es válida (RF-6, RF-13).

---

## Cierre

- [x] **T19 — Cobertura automatizada de todos los RF**
  - RFs: RF-1 … RF-14
  - Revisar que cada RF tiene al menos un test nombrado o documentado; completar huecos si faltan.
  - Done when: lista RF-1 a RF-14 mapeada a tests en verde; `make test` pasa.

- [x] **T20 — Verificación completa del corte**
  - RFs: (criterios de finalización)
  - Ejecutar `make verify` (lint, formato, checks, migraciones, tests).
  - Done when: `make verify` en verde; sin modelos/tablas de cuenta alternativa del panel.
