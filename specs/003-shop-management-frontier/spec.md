# Spec 003 — Frontera de gestión de tienda del vendedor

## Contexto y objetivo

El detalle público de una publicación necesita mostrar la tienda del vendedor. Para que eso sea posible, el vendedor autenticado en el panel debe poder consultar y guardar los datos de su tienda sin que `panel-api` se convierta en dueño de esa información: la tienda pertenece 1:1 a una cuenta y su fuente de verdad vive en el servicio de cuentas. Esta funcionalidad define el comportamiento de esa frontera de gestión de tienda desde el panel: qué puede hacer el vendedor con los datos de su tienda (consultarlos y guardarlos en una única operación que crea o reemplaza), qué garantías de propiedad se respetan y qué ocurre cuando el servicio dueño no responde.

## Usuarios / actores

- Vendedor con sesión activa en el panel que configura los datos de su tienda.
- Cuenta autenticada, que determina la tienda sobre la que se opera.
- Servicio de cuentas (`account-api`), dueño de la identidad y fuente de verdad de la tienda de cada cuenta.
- Cliente web del panel (`panel-web`), que consume los datos de tienda.

## Historias de usuario

- H1: Como vendedor autenticado quiero consultar los datos de mi tienda —o saber que todavía no la configuré— para conocer qué información se mostrará en mis publicaciones.
- H2: Como vendedor autenticado quiero guardar los datos de mi tienda (creándola si no existe o reemplazándola si ya existe) para mantenerla al día sin salir del panel.
- H3: Como vendedor autenticado quiero que un fallo del servicio dueño de la tienda no me saque de la sesión para poder reintentar sin volver a iniciar sesión.
- H4: Como vendedor autenticado quiero que solo se puedan ver y modificar los datos de mi propia tienda para que nadie opere sobre la de otra cuenta.

## Requisitos funcionales (criterios de aceptación en EARS)

- RF-1: CUANDO un vendedor autenticado consulta los datos de su tienda, EL SISTEMA obtendrá esos datos del servicio dueño de la tienda y se los devolverá tal como ese servicio los reporte.
- RF-2: CUANDO un vendedor autenticado consulta los datos de su tienda y la cuenta no tiene tienda configurada, EL SISTEMA informará explícitamente que todavía no hay tienda, sin tratarlo como un error de sistema.
- RF-3: CUANDO un vendedor autenticado guarda los datos de su tienda, EL SISTEMA solicitará al servicio dueño, en una única operación de guardado, crear la tienda si la cuenta no tiene una y reemplazar el nombre y la descripción si ya existe.
- RF-4: CUANDO el servicio dueño confirma un guardado, EL SISTEMA devolverá al vendedor los datos de su tienda tal como el servicio dueño los reporte tras el cambio.
- RF-5: EL SISTEMA determinará la tienda sobre la que opera exclusivamente a partir de la cuenta autenticada.
- RF-6: SI una solicitud intenta consultar o guardar una tienda distinta de la de la cuenta autenticada, ENTONCES EL SISTEMA no expondrá ni modificará los datos de esa otra tienda y responderá con un error de operación no permitida.
- RF-7: EL SISTEMA no persistirá los datos de tienda en almacenamiento propio.
- RF-8: EL SISTEMA tratará al servicio dueño de la tienda como única fuente de verdad de esos datos.
- RF-9: SI no hay una sesión autenticada, ENTONCES EL SISTEMA no expondrá ni modificará datos de tienda.
- RF-10: SI el servicio dueño de la tienda no está disponible al consultar los datos, ENTONCES EL SISTEMA informará al vendedor que la consulta no pudo completarse con el mensaje "No pudimos cargar tu tienda. Intentá de nuevo.".
- RF-11: SI el servicio dueño de la tienda no está disponible al guardar los datos, ENTONCES EL SISTEMA informará al vendedor que el guardado no pudo completarse con el mensaje "No pudimos guardar tu tienda. Intentá de nuevo.".
- RF-12: SI una operación de tienda falla por indisponibilidad del servicio dueño, ENTONCES EL SISTEMA mantendrá activa la sesión del vendedor.
- RF-13: EL SISTEMA no validará ni transformará los datos propios de la tienda como fuente de verdad; la validación de nombre (obligatorio, de 1 a 80 caracteres) y descripción (opcional, de hasta 1000 caracteres) corresponde al servicio dueño.
- RF-14: CUANDO el servicio dueño rechaza una operación por datos inválidos, EL SISTEMA mostrará al vendedor el motivo del rechazo tal como lo reporte el servicio dueño.
- RF-15: CUANDO el servicio dueño rechaza un guardado, EL SISTEMA no alterará los datos de la tienda.

## Requisitos no funcionales

- Los mensajes visibles al vendedor estarán en español.
- Los mensajes de fallo son, respectivamente para consulta y guardado: "No pudimos cargar tu tienda. Intentá de nuevo." y "No pudimos guardar tu tienda. Intentá de nuevo.".
- La sesión y la identidad siguen perteneciendo al servicio de cuentas; esta funcionalidad no añade autenticación nueva.
- Los fallos del servicio dueño de la tienda no cierran ni invalidan la sesión del vendedor.
- La tienda es única por cuenta (relación 1:1) y su fuente de verdad reside en el servicio dueño.
- No se crean datos ni estructuras persistentes de tienda en este repositorio.

## Casos límite

- Cuenta autenticada sin tienda configurada: la consulta informa explícitamente que todavía no hay tienda, sin tratarlo como error de sistema; el panel podrá ofrecer crearla con el mismo formulario de guardado (RF-1, RF-2, RF-3).
- Servicio dueño no disponible al consultar: se informa "No pudimos cargar tu tienda. Intentá de nuevo." y la sesión sigue activa (RF-10, RF-12).
- Servicio dueño no disponible al guardar: se informa "No pudimos guardar tu tienda. Intentá de nuevo." y la sesión sigue activa (RF-11, RF-12).
- Servicio dueño rechaza un guardado por datos inválidos (por ejemplo, nombre fuera de 1 a 80 caracteres o descripción de más de 1000 caracteres): se muestra el motivo reportado y no se altera la tienda (RF-13, RF-14, RF-15).
- Creación y edición de la tienda: se resuelven con una única operación de guardado que crea la tienda si la cuenta no tiene una y reemplaza nombre y descripción si ya existe; no hay operaciones separadas de alta y edición (RF-3).
- Guardado que reemplaza todos los datos frente a cambios parciales: el guardado reemplaza todos los datos públicos de la tienda (nombre y descripción), sin cambios parciales (RF-3, RF-4).
- Solicitud sobre la tienda de otra cuenta: error de operación no permitida (RF-6).
- Petición sin sesión autenticada: no se expone ni modifica ningún dato de tienda (RF-9).

## Fuera de alcance

- Tener un modelo propio de tienda en `panel-api`.
- Puntos de venta.
- Membresías de vendedor.
- Imágenes de tienda.
- Múltiples tiendas por cuenta.
- Compras, carrito, cantidades o checkout.
- La página pública de detalle de publicación y su visualización.
- Persistir o replicar los datos de tienda como fuente de verdad.
- Operaciones separadas de alta y edición de tienda; la creación y la edición se resuelven en un único guardado.
- Actualizaciones parciales de la tienda; el guardado reemplaza nombre y descripción.
- Validar o derivar campos del dominio de la tienda (responsabilidad del servicio dueño).
- Duplicar en el panel la validación de nombre y descripción como fuente de verdad; el panel solo muestra el motivo reportado por el servicio dueño.
- Alta, baja o autenticación de cuentas (responsabilidad del servicio de cuentas).

## Criterios de finalización

- Todos los RF verificables con prueba automatizada o demostración manual del flujo principal (consultar y guardar la propia tienda).
- La consulta y el guardado operan únicamente sobre la tienda de la cuenta autenticada.
- La consulta de una cuenta sin tienda configurada informa explícitamente su ausencia sin tratarlo como error de sistema.
- El guardado crea la tienda si la cuenta no tiene una y reemplaza nombre y descripción si ya existe; no existen operaciones separadas de alta y edición ni cambios parciales.
- Un fallo del servicio dueño no cierra la sesión del vendedor y se informa en español con los mensajes definidos para consulta y guardado.
- Un rechazo por datos inválidos muestra el motivo reportado por el servicio dueño sin alterar la tienda.
- No existen datos ni estructuras persistentes de tienda en este repositorio.
- Las dudas abiertas quedan resueltas o con una decisión explícita documentada en la spec.

## Decisiones resueltas

- ~~¿La creación de la tienda y su edición deben resolverse en una misma operación o son operaciones separadas?~~ Decisión: se resuelven con una única operación de "guardar mi tienda": si la cuenta no tiene tienda la crea; si ya tiene, reemplaza nombre y descripción. No hay operaciones separadas de alta y edición.
- ~~¿Qué debe hacer el panel cuando la cuenta autenticada no tiene tienda configurada: informar su ausencia, ofrecer crearla o responder con un error?~~ Decisión: la consulta informa explícitamente que todavía no hay tienda (no es un error de sistema); el panel podrá ofrecer crearla con el mismo formulario de guardado.
- ~~¿Una actualización reemplaza todos los datos de la tienda o solo los campos enviados?~~ Decisión: el guardado reemplaza todos los datos públicos de la tienda (nombre y descripción), sin cambios parciales.
- ~~¿Qué mensajes exactos debe mostrar el panel cuando el servicio dueño de la tienda no está disponible?~~ Decisión: al fallar la consulta, "No pudimos cargar tu tienda. Intentá de nuevo."; al fallar el guardado, "No pudimos guardar tu tienda. Intentá de nuevo."; si el servicio dueño rechaza datos inválidos, se muestra el motivo reportado. En todos los casos la sesión permanece activa.
- Validación del servicio dueño: nombre obligatorio de 1 a 80 caracteres y descripción opcional de hasta 1000 caracteres; el panel no duplica esa validación como fuente de verdad y solo muestra el motivo reportado.
