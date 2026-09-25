# Plan 001 — Entrar al panel con la misma cuenta

## Resumen técnico

Este corte convierte a `panel-api` en la única puerta de identidad del panel: entrar, salir y consultar quién es. No crea ni persiste una cuenta propia; consume el sistema de cuentas (`account-api`) como dueño de la cuenta única y de la sesión compartida con la tienda. En esta iteración el acceso es solo con Google. El resto del panel sigue usable sin autenticación.

La nota histórica de `AGENTS.md` que difiere Keycloak/identidad queda subordinada a esta spec: sí se implementa autenticación del panel aquí, apoyada en `account-api`, no en Keycloak.

## Alcance en este repositorio

- Endpoints bajo el prefijo del servicio (`/panel/...`) para entrar, salir y “quién soy”.
- Cliente HTTP hacia `account-api` (servicios de dominio), sin escribir tablas ajenas.
- Autenticación opcional: ninguna vista existente exige login en este corte.
- Mensajes visibles al cliente del panel en español.
- Pruebas automatizadas que cubran todos los RF.

Fuera de este repositorio (solo contrato / coordinación): pantallas (`panel-web`), entrada de la tienda (`account-api` + `client-web`), disponibilidad del servicio de cuentas (`infra`), y acciones que exijan autenticación (p. ej. publicar catálogo).

## Arquitectura propuesta

### Apps y capas

- Nueva app de dominio, p. ej. `identity` (o nombre equivalente en inglés), separada de `shops`.
- Vistas DRF delgadas: validan entrada, delegan y mapean errores a respuestas JSON.
- Servicios de dominio (p. ej. `identity/services.py`):
  - orquestan entrar / salir / quién soy;
  - hablan solo con un cliente HTTP de `account-api`;
  - no crean modelos de cuenta local.
- Cliente de `account-api` (módulo dedicado, configurable por variables de entorno): timeouts, errores de red/5xx y respuestas de rechazo tipificados.
- Sin modelo Django de “Usuario del panel” ni tabla de cuentas alternativa. Si hace falta estado de request, se deriva de la sesión compartida que expone/resuelve `account-api`.

### Principios alineados con AGENTS.md

- Python / Django LTS / DRF; lógica reutilizable en servicios.
- Consumir APIs de dominio; no tocar la base `accounts`.
- Conservar `/panel`, `/health/live`, `/health/ready`.
- Configuración por entorno; secretos fuera del código.
- Tras implementar: `make verify`, tests y migraciones solo si hay cambio persistente (este corte no debería requerir modelo de cuenta).

## Contrato HTTP expuesto por panel-api (RF-7)

Única puerta del panel. Rutas bajo `/panel` (nombres exactos a fijar en implementación; el plan fija el comportamiento):

| Operación | Comportamiento | RF |
|-----------|----------------|----|
| Entrar | Recibe el resultado del acceso con Google (p. ej. credencial/id token o código según el flujo acordado con `panel-web`), lo valida vía sistema de cuentas, abre la sesión compartida y deja al cliente autenticado. Solo Google en esta iteración. | RF-2, RF-3, RF-4, RF-5, RF-9, RF-11, RF-12 |
| Salir | Cierra la sesión compartida. Si no había sesión, responde éxito y permanece sin autenticación. | RF-6, RF-10, RF-13 |
| Quién soy | Si hay sesión compartida activa, responde nombre y correo de Google; si no, indica no autenticado sin inventar identidad. | RF-1, RF-8, RF-13 |
| Resto del panel | Endpoints existentes (p. ej. `GET /panel`) siguen respondiendo sin exigir autenticación. | RF-1 |

No se exponen rutas de “entrada de la tienda” en esta puerta (RF-14).

## Integración con el sistema de cuentas

`panel-api` no es dueño de la cuenta ni de la sesión canónica. Delega en `account-api`:

1. **Entrar (panel):** enviar la prueba de Google al sistema de cuentas; si confirma, ese servicio deja abierta la sesión compartida (tienda + panel) y devuelve identidad (nombre, correo). `panel-api` refleja estado autenticado al cliente del panel (RF-2, RF-5).
2. **Reconocer cuenta:** cualquier cuenta que el sistema de cuentas reconozca es válida; no se exige membresía, rol ni vínculo previo con tiendas del panel (RF-3).
3. **Quién soy:** consultar la sesión compartida / identidad actual al sistema de cuentas (o el contrato que este exponga para el panel) y devolver solo nombre y correo (RF-8).
4. **Salir:** pedir al sistema de cuentas el cierre de la sesión compartida; tras éxito, panel y tienda quedan sin autenticación en la siguiente recarga o solicitud (RF-6, RF-13).
5. **Reentrada:** un nuevo entrar exitoso deja como actual la cuenta con la que se acaba de entrar, aunque ya hubiera otra sesión (RF-9).
6. **Rechazo Google:** si el sistema de cuentas rechaza el acceso, no hay autenticación; respuesta de error con mensaje en español (RF-11).
7. **Indisponibilidad:** timeouts, conexión fallida o 5xx del sistema de cuentas al entrar → no autenticar; informar que el acceso no pudo completarse, en español (RF-12).

La entrada de la tienda no se implementa ni se proxyfica aquí: la tienda entra por el servicio de cuentas; la sesión resultante es la misma (RF-14).

## Sesión compartida (RF-5, RF-6, RF-13)

- Entrar en el panel abre la misma sesión que usa la tienda.
- Salir en el panel la cierra en ambas superficies.
- Tras un salir, cualquier recarga o solicitud posterior (panel o tienda) se trata como no autenticada.
- Simétricamente, una sesión abierta desde la tienda debe verse en el panel al consultar “quién soy” (sin que la tienda use esta puerta).
- No hay caducidad por tiempo en este corte: la persona sigue autenticada hasta que sale (requisito no funcional de la spec).

Mecanismo concreto (cookie de sesión compartida, token opaco, etc.): el que defina/propague `account-api` como dueño de la sesión; `panel-api` lo reenvía o lo establece según ese contrato, sin duplicar almacenes de sesión locales como fuente de verdad.

## Autenticación opcional (RF-1)

- No añadir `IsAuthenticated` global ni middleware que bloquee `/panel` u otras rutas existentes.
- Entrar/salir/quién soy son operaciones explícitas; el uso anónimo del panel sigue permitido.
- Las acciones que exijan login (publicar catálogo, etc.) quedan fuera de alcance.

## Solo Google en esta iteración (RF-4)

- El endpoint de entrada acepta únicamente el flujo Google acordado.
- Otros proveedores o email/contraseña: rechazar o no exponer; no implementar.
- Mensajes de error de rechazo/indisponibilidad en español.

## Persistencia y datos

- No crear ni guardar cuenta alternativa del panel (RF-2; RNF de la spec).
- No copiar tablas de `account-api`.
- Modelos actuales de `shops` no se usan como identidad.
- Migraciones solo si algún detalle técnico local fuera imprescindible; el diseño preferido es cero tablas nuevas de identidad.

## Configuración

Variables de entorno (nombres orientativos):

- URL base de `account-api`.
- Credenciales/client id de Google necesarios en el lado servidor solo si este servicio valida el token; si la validación vive enteramente en `account-api`, documentar qué envía `panel-api` y qué secretos no debe tener.
- Timeouts del cliente HTTP.
- Flags CORS/CSRF/cookies según cómo se comparta la sesión entre orígenes del panel y la tienda (coordinar con `infra` / fronts; no inventar manifiestos aquí).

## Mapeo de requisitos funcionales

### Uso sin autenticación — RF-1

- Mantener el panel operable sin sesión.
- “Quién soy” sin sesión → no autenticado, sin error de negocio que bloquee el resto.
- Tests: rutas existentes y “quién soy” anónimo.

### Cuenta única, sin cuenta local — RF-2

- Servicio de login llama a `account-api`; no `User.objects.create` ni tabla de vendedor/panel-user.
- Tests: mock del cliente; asertar cero escrituras locales de cuenta.

### Sin membresía previa — RF-3

- No consultar modelos de membresía/`Shop` para autorizar el entrar.
- Tests: entrar con cuenta reconocida por el mock de cuentas aunque no exista membresía en `panel`.

### Solo Google — RF-4

- Entrada limitada a Google; otros métodos no contemplados.
- Tests: rechazo o no soporte de proveedor distinto si se intenta.

### Abrir sesión compartida al confirmar Google — RF-5

- Tras confirmación de cuentas, estado autenticado en panel y sesión compartida abierta.
- Tests: mock de confirmación → respuesta autenticada con identidad; verificación de que se invocó “abrir/confirmar sesión” en el cliente de cuentas.

### Cerrar sesión compartida al salir — RF-6

- Salir autenticado → llamada a cierre en cuentas; estado no autenticado.
- Tests: tras salir, “quién soy” no autenticado; se invocó cierre compartido.

### Única puerta del panel — RF-7

- Solo estos endpoints de `panel-api` para entrar/salir/quién soy del panel.
- No documentar ni implementar bypass hacia `account-api` desde el cliente del panel (eso lo cumple `panel-web`; aquí no se exponen atajos contradictorios).

### Nombre y correo mientras autenticado — RF-8

- Respuesta de “quién soy” con nombre y correo de Google cuando hay sesión.
- Tests: payload con ambos campos; sin sesión no los inventa.

### Reentrar reemplaza la cuenta actual — RF-9

- Segundo entrar exitoso con otra (o la misma) cuenta deja esa como actual.
- Tests: secuencia autenticado A → entrar B → “quién soy” es B.

### Salir sin autenticación — RF-10

- Salir anónimo → HTTP de éxito; sigue sin autenticación.
- Tests: no falla; no llama a cierre destructivo innecesario o, si llama, el resultado observable es éxito idempotente.

### Rechazo de Google — RF-11

- Mock de rechazo de cuentas → no autenticado + mensaje en español.
- Tests: sin cookie/sesión de autenticado; cuerpo de error esperado.

### Cuentas no disponibles — RF-12

- Simular timeout/5xx/conexión → no autenticado + mensaje de que el acceso no pudo completarse (español).
- Tests: no quedar autenticado tras fallo de infraestructura del cliente.

### Post-salir: solicitudes como anónimas — RF-13

- Tras salir, “quién soy” y requests siguientes sin identidad.
- Coordinación: el cierre en cuentas invalida la sesión que también usa la tienda (cubierto vía contrato mockeado).
- Tests: salir → quién soy anónimo; opcionalmente simular que la misma sesión ya no es válida para un consumidor tipo tienda.

### No atender entrada de la tienda — RF-14

- No endpoints ni flujos “login tienda” en esta API.
- Tests/documentación del plan: la puerta es solo panel; la tienda no usa estas rutas para entrar.

## Historias de usuario → diseño

| Historia | Diseño | RF |
|----------|--------|----|
| H1 Entrar con la misma cuenta | Entrar Google → `account-api` → sesión compartida | RF-2, RF-3, RF-4, RF-5 |
| H2 Salir cierra sesión con la tienda | Salir → cierre compartido en cuentas | RF-6, RF-13 |
| H3 Ver nombre y correo | Quién soy autenticado | RF-8 |
| H4 Usar panel sin autenticarse | Auth opcional; resto del API sin exigir login | RF-1 |

## Pruebas y verificación

- Suite Django/DRF con cliente HTTP de cuentas mockeado (sin red real en CI).
- Un caso (o más) por RF; marcar en el nombre o docstring el RF cubierto.
- `make verify` en verde al cerrar el corte.
- Demostración manual (criterios de la spec): panel sin entrar; entrar con Google; ver nombre/correo; salir y comprobar efecto en tienda al recargar/solicitar; salir anónimo; reentrar quedando la última cuenta.

## Orden de implementación sugerido

1. App `identity`, settings (URL de cuentas), cliente HTTP tipificado.
2. Endpoints quién soy y salir (incl. RF-10) contra mocks.
3. Endpoint entrar (Google → cuentas → sesión) con RF-3, RF-4, RF-5, RF-9, RF-11, RF-12.
4. Asegurar RF-1 en rutas existentes y ausencia de gate global.
5. Cobertura RF-7/RF-14 por contrato de API y tests negativos.
6. `make verify` y checklist de demostración.

## Riesgos y dependencias

- Contrato exacto de `account-api` (rutas, cookies, payload Google) puede evolucionar en paralelo: aislarlo detrás del cliente HTTP para no filtrar detalles a las vistas.
- Compartir sesión entre orígenes distintos (panel vs tienda) puede requerir ajustes de cookie/dominio en `infra`; este plan no redefine manifiestos, solo consume el contrato.
- No implementar Keycloak ni una segunda identidad local aunque textos viejos lo sugieran: la spec manda.
