# Spec 002 — Frontera de catálogo: drafts, publicación y sesión

## Contexto y objetivo

El panel necesita que un vendedor con sesión dé de alta, edite, publique y despublic
sus productos sin que `panel-api` se convierta en dueño del catálogo. Esta
funcionalidad expone `/panel/catalog/...` como frontera: valida la cookie
`fes_session` contra el servicio de cuentas y reenvía cada operación al servicio
de catálogo propagando la cuenta dueña de la sesión, de modo que la fuente de
verdad de productos siga viviendo fuera de este repositorio y este no persista
productos.

## Usuarios / actores

- Vendedor u operador con sesión activa que gestiona productos desde el panel.
- Cliente web del panel (`panel-web`), que consume las rutas de catálogo.
- Servicio de cuentas (`account-api`), dueño de la sesión compartida y de la
  cookie `fes_session`.
- Servicio de catálogo (`catalog-api`), fuente de verdad de productos, etapas,
  dueños e imágenes.

## Historias de usuario

- H1: Como vendedor del panel quiero listar, crear, editar y eliminar mis productos para mantener mi catálogo sin que el panel guarde copia.
- H2: Como vendedor del panel quiero publicar y despublicar un producto para controlar qué se muestra.
- H3: Como vendedor del panel quiero publicar mi catálogo completo para poner a la venta de una vez los productos visibles de mi sesión.
- H4: Como operador sin sesión quiero recibir una respuesta de no autorizado clara para saber que debo iniciar sesión antes de operar el catálogo.

## Requisitos funcionales (criterios de aceptación en EARS)

- RF-1: EL SISTEMA expondrá bajo `/panel/catalog` las operaciones `GET /panel/catalog/products`, `POST /panel/catalog/products`, `PUT /panel/catalog/products/{id}`, `DELETE /panel/catalog/products/{id}`, `POST /panel/catalog/products/{id}/publish`, `POST /panel/catalog/products/{id}/unpublish` y `POST /panel/catalog/publish`.
- RF-2: CUANDO un cliente solicita una operación de catálogo del panel, EL SISTEMA resolverá la cookie `fes_session` contra el servicio de cuentas.
- RF-3: SI la petición no lleva cookie `fes_session` o la sesión resuelta no está autenticada, ENTONCES EL SISTEMA responderá 401 con cuerpo `{"error":"no_autenticado","message":"..."}` en español y no reenviará la operación al servicio de catálogo.
- RF-4: CUANDO la sesión resuelta está autenticada, EL SISTEMA reenviará la operación al servicio de catálogo fijando el `ownerAccountId` con la cuenta de la sesión.
- RF-5: CUANDO un cliente solicita `GET /panel/catalog/products`, EL SISTEMA consultará al servicio de catálogo los productos del `ownerAccountId` de la sesión.
- RF-6: CUANDO un cliente solicita `POST /panel/catalog/products`, EL SISTEMA creará en el servicio de catálogo el producto con el `ownerAccountId` de la sesión.
- RF-7: CUANDO un cliente solicita `PUT /panel/catalog/products/{id}`, EL SISTEMA actualizará en el servicio de catálogo el producto `{id}` del `ownerAccountId` de la sesión.
- RF-8: CUANDO un cliente solicita `DELETE /panel/catalog/products/{id}`, EL SISTEMA eliminará en el servicio de catálogo el producto `{id}` del `ownerAccountId` de la sesión.
- RF-9: CUANDO un cliente solicita `POST /panel/catalog/products/{id}/publish`, EL SISTEMA publicará en el servicio de catálogo el producto `{id}` del `ownerAccountId` de la sesión.
- RF-10: CUANDO un cliente solicita `POST /panel/catalog/products/{id}/unpublish`, EL SISTEMA despublicará en el servicio de catálogo el producto `{id}` del `ownerAccountId` de la sesión.
- RF-11: CUANDO un cliente solicita `POST /panel/catalog/publish`, EL SISTEMA solicitará al servicio de catálogo publicar el conjunto indicado por el cliente —los productos sin dueño enviados en el cuerpo y los draft con dueño de la cuenta de la sesión— fijando el dueño con la cuenta de la sesión.
- RF-12: EL SISTEMA usará `CATALOG_API_BASE_URL` como dirección base del servicio de catálogo interno.
- RF-13: CUANDO el servicio de catálogo devuelve una respuesta que no es 5xx a una operación, EL SISTEMA reenviará al cliente el mismo estado y el mismo cuerpo recibidos.
- RF-14: SI el servicio de cuentas no está disponible o falla al resolver la sesión, ENTONCES EL SISTEMA responderá 503 con cuerpo `{"error":"servicio_no_disponible","message":"..."}` en español y no reenviará la operación al servicio de catálogo.
- RF-15: SI el servicio de catálogo responde 5xx o está inalcanzable, ENTONCES EL SISTEMA responderá 503 con cuerpo `{"error":"servicio_no_disponible","message":"..."}` en español.
- RF-16: EL SISTEMA no persistirá productos, etapas, dueños ni imágenes en la base de datos del panel.
- RF-17: EL SISTEMA ignorará cualquier `ownerAccountId` enviado por el cliente y usará siempre el de la sesión, incluso para administrar productos de otra cuenta.
- RF-18: EL SISTEMA no validará los campos propios del dominio del producto; esa validación corresponde al servicio de catálogo.
- RF-19: EL SISTEMA conservará `GET /health/live` y `GET /health/ready`.
- RF-20: EL SISTEMA aceptará peticiones CORS con credenciales desde el origen del panel.
- RF-21: CUANDO `POST /panel/catalog/publish` no tenga productos por publicar, EL SISTEMA responderá 200 con conteo 0 publicados; no es error.
- RF-22: CUANDO el servicio de catálogo responde 4xx, EL SISTEMA reenviará ese estado y su cuerpo al cliente.

## Requisitos no funcionales

- La sesión y la identidad siguen perteneciendo al servicio de cuentas; esta funcionalidad solo actúa como frontera y no añade autenticación nueva.
- La frontera de catálogo reutiliza el mismo patrón de frontera de identidad ya existente hacia el servicio de cuentas.
- No se crean tablas ni migraciones nuevas en el panel.
- Los mensajes visibles al usuario estarán en español.
- Las respuestas de error propias de la frontera comparten el shape `{"error","message"}` ya usado por la frontera de identidad.

## Casos límite

- Petición sin cookie `fes_session`: 401 con `{"error":"no_autenticado","message":"..."}` y sin reenvío (RF-3).
- Petición con cookie `fes_session` que la sesión resuelta marca como no autenticada: 401 con `{"error":"no_autenticado","message":"..."}` y sin reenvío (RF-3).
- Servicio de cuentas caído o con error al resolver la sesión: 503 con `{"error":"servicio_no_disponible","message":"..."}` y sin reenvío (RF-14).
- Servicio de catálogo inalcanzable o con 5xx: 503 con `{"error":"servicio_no_disponible","message":"..."}` (RF-15).
- Servicio de catálogo con 4xx: se reenvía el estado y el cuerpo de catálogo tal cual (RF-22).
- Producto `{id}` inexistente o de otra cuenta: se reenvía la operación y la respuesta del servicio de catálogo determina el resultado (RF-13, RF-22).
- `POST /panel/catalog/publish` sin productos por publicar: responde 200 con 0 publicados; no es error (RF-21).
- Cliente que envía `ownerAccountId` en el cuerpo: se ignora y se usa el de la sesión (RF-17).

## Fuera de alcance

- Ser fuente de verdad de productos, etapas y dueños (responsabilidad de `catalog-api`).
- Guardar imágenes o integrarse con MinIO (responsabilidad de `catalog-api`).
- Gestionar el borrador local del navegador y los estados de sus botones (responsabilidad de `panel-web`).
- Crear el modelo de tiendas (Shop) en este recorte.
- Implementar el inicio de sesión con Google o emitir identidad (responsabilidad de `account-api`).
- Exponer la lectura de publicados para el futuro catálogo de market (`GET /catalog`).
- Persistir productos, etapas, dueños o imágenes en la base del panel.
- Validar o derivar campos del dominio del producto (moneda, imágenes, precios).
- Autenticación distinta de la sesión compartida de cuentas.

## Criterios de finalización

- Todos los RF verificables con prueba automatizada o demostración manual del flujo principal (listar, crear, editar, eliminar, publicar, despublicar y publicar catálogo).
- La frontera responde 401 sin sesión con `{"error":"no_autenticado","message":"..."}` y 503 con `{"error":"servicio_no_disponible","message":"..."}` cuando el servicio de cuentas o el de catálogo no está disponible.
- Los 4xx de `catalog-api` se reenvían con su estado y cuerpo; los 5xx y la indisponibilidad se traducen a 503.
- `POST /panel/catalog/publish` sin productos responde 200 con 0 publicados.
- No existen tablas ni migraciones nuevas en el panel.
- `GET /health/live` y `GET /health/ready` siguen respondiendo tras el cambio.

## Dudas abiertas

Ninguna.
