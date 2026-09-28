# Spec 001 — Login del panel con la sesión de cuentas

## Contexto y objetivo

El panel necesita una puerta de acceso que reutilice la sesión compartida de cuentas, sin convertirse en dueño de la identidad. Esta funcionalidad arranca el mismo inicio de sesión con Google, consulta quién es la persona autenticada preguntando al servicio de cuentas y permite cerrar esa sesión, de modo que cualquier cuenta de Google pueda entrar al panel sin que este repositorio guarde la cuenta.

## Usuarios / actores

- Operador o vendedor que inicia sesión en el panel desde el navegador.
- Cliente web del panel (`panel-web`), que consume sesión y cierre de sesión.
- Servicio de cuentas (`account-api`), dueño de Google, de la identidad y de la cookie `fes_session`.

## Historias de usuario

- H1: Como operador del panel quiero iniciar sesión con Google a través del panel para autenticarme con la misma cuenta que el resto de Friendly E-Shop.
- H2: Como cliente del panel quiero consultar si hay sesión activa para saber quién está autenticado sin que el panel almacene la cuenta.
- H3: Como operador del panel quiero cerrar la sesión para que deje de valer en el navegador y en el servicio de cuentas.

## Requisitos funcionales (criterios de aceptación en EARS)

- RF-1: CUANDO un navegador solicita `GET /panel/login/google`, EL SISTEMA redirigirá al navegador a `GET /accounts/login/google` con el parámetro `return_to` igual al origen público del panel.
- RF-2: CUANDO un cliente solicita `GET /panel/session`, EL SISTEMA consultará la sesión en el servicio de cuentas reenviando la cookie `fes_session`.
- RF-3: CUANDO el servicio de cuentas responde a la consulta de sesión, EL SISTEMA devolverá al cliente el mismo JSON recibido de `GET /accounts/session`.
- RF-4: CUANDO un cliente solicita `POST /panel/logout` y hay sesión activa, EL SISTEMA solicitará el cierre de esa sesión en el servicio de cuentas.
- RF-5: CUANDO el cierre en el servicio de cuentas se completa, EL SISTEMA borrará la cookie `fes_session` en la respuesta al navegador.
- RF-6: EL SISTEMA no persistirá la cuenta del usuario como dato propio de identidad del panel.
- RF-7: EL SISTEMA permitirá el acceso al flujo de sesión del panel a cualquier cuenta de Google autenticada mediante la sesión compartida, sin exigir membresía de vendedor ni alta de tienda.
- RF-8: EL SISTEMA usará `ACCOUNT_API_BASE_URL` como dirección base del servicio de cuentas interno.
- RF-9: EL SISTEMA aceptará peticiones CORS con credenciales desde el origen del panel.
- RF-10: EL SISTEMA conservará `GET /health/live` y `GET /health/ready`.
- RF-11: EL SISTEMA usará, para `return_to` y para CORS, un único origen configurable por entorno: el host público del panel.
- RF-12: SI el servicio de cuentas no está disponible o falla al consultar la sesión, ENTONCES EL SISTEMA responderá 503 con un cuerpo de error distinto del JSON de no autenticado.
- RF-13: SI el servicio de cuentas no está disponible o falla al cerrar la sesión, ENTONCES EL SISTEMA responderá 503 con un cuerpo de error distinto del JSON de no autenticado y no borrará `fes_session`.
- RF-14: SI se solicita `GET /panel/session` sin cookie `fes_session` o con sesión inválida, ENTONCES EL SISTEMA responderá 200 y el mismo JSON de cuentas con `authenticated` en false.
- RF-15: SI se solicita `POST /panel/logout` sin sesión activa, ENTONCES EL SISTEMA responderá 200, borrará `fes_session` y responderá `authenticated` en false.

## Requisitos no funcionales

- La identidad y el inicio de sesión con Google permanecen fuera de este sistema; este solo actúa como puerta hacia el servicio de cuentas.
- Los mensajes visibles al usuario, si los hubiera en respuestas de error de este flujo, estarán en español.
- Cuando el servicio de cuentas no está disponible o falla al consultar o cerrar la sesión, la respuesta es 503 con un cuerpo de error distinto del JSON de no autenticado (RF-12, RF-13).

## Casos límite

- Solicitud de `GET /panel/session` sin cookie `fes_session` o con cookie inválida: 200 y el mismo JSON de cuentas con `authenticated` en false (RF-14).
- `POST /panel/logout` sin sesión activa: 200, se borra `fes_session` y se responde `authenticated` en false (RF-15).
- Fallo del servicio de cuentas durante logout tras haber recibido la petición: 503 y no se borra `fes_session` (RF-13).

## Fuera de alcance

- Implementar Google OAuth o emitir la identidad (responsabilidad de `account-api`).
- Construir la pantalla de login o de sesión (responsabilidad de `panel-web`).
- Exigir membresía de vendedor o alta de tienda para entrar.
- Publicar o gestionar catálogos.
- Guardar o replicar la cuenta como fuente de verdad en este repositorio.
- Autenticación distinta de la sesión compartida de cuentas (p. ej. Keycloak propio del panel).

## Criterios de finalización

- Todos los RF verificables con prueba automatizada o demostración manual del flujo principal (inicio vía Google, consulta de sesión y cierre).
- `GET /health/live` y `GET /health/ready` siguen respondiendo tras el cambio.
- Ninguna duda marcada como `[NECESITA ACLARACIÓN]` queda sin resolver o sin decisión explícita documentada en la spec.

## Dudas abiertas

Ninguna.
