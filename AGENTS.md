# AGENTS.md - panel-api

## Proyecto
API administrativa de Friendly E-Shop en Python, Django LTS y Django REST Framework. Posee tiendas y membresías del panel, y actúa como frontera hacia los servicios de dominio sin escribir sus tablas.
Persiste en la base `panel`, expone `/panel` y health checks, y se ejecuta con Gunicorn instrumentado por OpenTelemetry.

## Comandos
- Preparar: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
- Ejecutar: `python manage.py runserver 0.0.0.0:8000`
- Tests: `python manage.py test`
- Chequeos: `python manage.py check && python manage.py makemigrations --check --dry-run`
- Lint/formato: no está configurado; sigue PEP 8 y el estilo existente.

## Estilo y convenciones
- Usa Python 3.14, Django 5.2 LTS y DRF; mantén la configuración global en `config` y el dominio en apps.
- Nombres, código y documentación técnica en inglés; mensajes visibles al usuario en español.
- Usa ORM y migraciones de Django; crea una migración nueva por cada cambio persistente.
- Mantén las vistas pequeñas y mueve reglas reutilizables a servicios del dominio correspondiente.

## Reglas
- Lee la skill `/django-patterns` y la spec activa, si existe, antes de tocar código.
- Solo posee datos de tiendas, vendedores y membresías; no repliques productos, pedidos ni pagos como fuente de verdad.
- Consume las APIs de dominio en lugar de acceder a sus bases o tablas.
- Conserva `/panel`, `/health/live` y `/health/ready`, además de la configuración por variables de entorno.
- Keycloak y la identidad externa están diferidos; no añadas autenticación nueva sin una spec.
- Mantén dependencias fijadas y nunca incluyas secretos en código o migraciones.
- Los manifiestos y secretos pertenecen a `infra`; coordina allí cambios de puerto, ruta o configuración.

## Al terminar cualquier tarea
- Ejecuta `python manage.py test` y los chequeos indicados arriba.
- Añade tests y migraciones para todo cambio de comportamiento o modelo.
- Verifica los health checks si modificas base de datos, middleware, settings o arranque.
