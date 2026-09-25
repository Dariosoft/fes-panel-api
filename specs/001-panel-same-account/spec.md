# Spec 001 — Entrar al panel con la misma cuenta

## Contexto y objetivo
El panel administrativo necesita una única puerta de entrada y salida. No crea su propia cuenta: usa la cuenta única del producto, por ahora con Google. El panel se puede usar sin estar autenticado. Autenticarse hace falta para acciones concretas, como publicar un catálogo, y eso no es de este corte. La sesión es la misma de la tienda: entrar en cualquiera de las dos la abre, y salir en cualquiera de las dos la cierra en ambas.

## Usuarios / actores
- Persona que usa el panel, con o sin autenticación.
- Cliente del panel, que habla solo con este sistema para entrar, salir y saber quién es.
- Sistema de cuentas compartido, fuente de la cuenta única. No pertenece a este repositorio.
- La tienda, que comparte la sesión pero no entra por esta puerta.

## Historias de usuario
- H1: Como persona del panel quiero entrar con la misma cuenta del producto para no tener una identidad distinta.
- H2: Como persona del panel quiero salir para cerrar la sesión compartida con la tienda.
- H3: Como cliente del panel quiero saber el nombre y el correo de quien está autenticado.
- H4: Como persona quiero usar el panel sin autenticarme, y autenticarme solo cuando una acción lo exija.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: EL SISTEMA permitirá usar el panel sin estar autenticado.
- RF-2: CUANDO una persona solicita entrar al panel, EL SISTEMA usará la cuenta única del sistema de cuentas y no creará otra cuenta.
- RF-3: EL SISTEMA permitirá entrar a cualquier cuenta reconocida por el sistema de cuentas, sin exigir un vínculo o membresía previa con el panel.
- RF-4: CUANDO una persona solicita entrar al panel, EL SISTEMA permitirá el acceso solo mediante Google en esta iteración.
- RF-5: CUANDO el sistema de cuentas confirma el acceso con Google, EL SISTEMA abrirá la sesión compartida con la tienda y dejará a la persona autenticada en el panel (salida: estado autenticado).
- RF-6: CUANDO una persona autenticada solicita salir, EL SISTEMA cerrará la sesión compartida en el panel y en la tienda (salida: estado no autenticado en ambas).
- RF-7: EL SISTEMA será la única puerta por la que el panel entra, sale y consulta quién es.
- RF-8: MIENTRAS haya una persona autenticada, EL SISTEMA podrá decir quién es mediante su nombre y su correo de Google.
- RF-9: CUANDO una persona ya autenticada vuelve a entrar, EL SISTEMA dejará como actual la cuenta con la que acaba de entrar.
- RF-10: SI alguien solicita salir sin estar autenticado, ENTONCES EL SISTEMA responderá con éxito y seguirá sin autenticación.
- RF-11: SI el sistema de cuentas rechaza el acceso con Google, ENTONCES EL SISTEMA no dejará a la persona autenticada e informará del rechazo.
- RF-12: SI el sistema de cuentas no está disponible al intentar entrar, ENTONCES EL SISTEMA no dejará a la persona autenticada e informará de que el acceso no pudo completarse.
- RF-13: CUANDO el panel o la tienda recarguen o envíen una solicitud después de un salir, EL SISTEMA los tratará como sin autenticación.
- RF-14: EL SISTEMA no atenderá la entrada de la tienda por esta puerta. La tienda entra por el servicio de cuentas, y la sesión resultante es la misma.

## Requisitos no funcionales
- Idioma de mensajes visibles a quien usa el panel: español.
- No se crea ni se guarda una cuenta alternativa del panel distinta de la cuenta única.
- La persona sigue autenticada hasta que sale. No hay un plazo tras el cual el acceso deje de valer solo.

## Casos límite
- Uso del panel sin entrar: se permite (RF-1).
- Cualquier cuenta reconocida puede entrar; no hace falta membresía previa (RF-3).
- Acceso con Google rechazado: no hay entrada (RF-11).
- Sistema de cuentas no disponible al entrar: no hay entrada (RF-12).
- Salir sin estar autenticado: éxito, sigue sin autenticación (RF-10).
- Entrar estando ya autenticado: queda la cuenta con la que acaba de entrar (RF-9).
- Salir en el panel: la tienda también queda sin autenticación al recargar o al enviar una solicitud (RF-6, RF-13).
- Entrar en la tienda: el panel ve la misma sesión al recargar o al enviar una solicitud (RF-5, RF-13).

## Fuera de alcance
- Guardar la cuenta (responsabilidad del sistema de cuentas).
- Pantallas de la tienda.
- Pantallas del panel.
- Dejar el servicio de cuentas disponible en el entorno.
- Métodos de acceso distintos de Google en esta iteración.
- Crear o poseer una cuenta propia del panel.
- Roles, vínculo o membresía previa para poder entrar.
- Publicar un catálogo y las demás acciones que exijan autenticación. Este corte solo deja la puerta; no implementa esas acciones.

## Criterios de finalización
- Todos los RF tienen prueba automatizada en verde.
- Demostración manual: usar el panel sin entrar; entrar con Google; ver nombre y correo; salir y comprobar que la tienda también queda sin autenticación al recargar o al enviar una solicitud.
- Demostración de salir sin estar autenticado, y de entrar de nuevo quedando la cuenta con la que se acaba de entrar.

## Dudas abiertas
No quedan dudas abiertas.
