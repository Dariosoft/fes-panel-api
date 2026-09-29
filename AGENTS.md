# AGENTS.md - panel-api

## Proyecto
API administrativa de Friendly E-Shop en Python, Django LTS y Django REST Framework. Posee tiendas y membresías del panel, y actúa como frontera hacia los servicios de dominio sin escribir sus tablas.
Persiste en la base `panel`, expone rutas bajo `/panel` y health checks, y se ejecuta con Gunicorn instrumentado por OpenTelemetry.

## Comandos
- Preparar: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt`
- Ejecutar: `python src/manage.py runserver 0.0.0.0:8000`
- Lint/formato: `make lint`
- Tests: `make test`
- Verificación completa: `make verify`

## Estilo y convenciones
- Usa Python 3.14, Django 5.2 LTS y DRF; el layout objetivo es código importable en `src/` y pruebas en `tests/`.
- Mantén la configuración global en `src/config`, health checks compartidos en `src/common/health` y el dominio en apps por capacidad de negocio.
- Nombres, código y documentación técnica en inglés; mensajes visibles al usuario en español.
- Respeta `pyproject.toml`: Ruff valida imports, errores comunes y formato con líneas de hasta 100 caracteres.
- Usa ORM y migraciones de Django; crea una migración nueva por cada cambio persistente.
- Mantén las vistas pequeñas y mueve reglas reutilizables a servicios del dominio correspondiente.

## Reglas
- Lee `/python-clean-code`, `/panel-api-architecture`, `/django-patterns` y la spec activa, si existe, antes de tocar código Python/Django.
- Aplica `/python-clean-code` al decidir límites de constantes, contratos externos, configuración, rutas del framework, organización de views y uso de `APIView` vs `ViewSet`.
- Usa `/clean-architecture` al diseñar o modificar capas, límites, dependencias, casos de uso o adaptadores.
- Solo posee datos de tiendas, vendedores y membresías; no repliques productos, pedidos ni pagos como fuente de verdad.
- Consume las APIs de dominio en lugar de acceder a sus bases o tablas.
- Conserva las rutas bajo `/panel`, `/health/live` y `/health/ready`, además de la configuración por variables de entorno.
- Keycloak y la identidad externa están diferidos; no añadas autenticación nueva sin una spec.
- Mantén dependencias fijadas y nunca incluyas secretos en código o migraciones.
- No omitas reglas ni añadas `noqa` para evitar corregir una violación sin justificarlo.
- Los manifiestos y secretos pertenecen a `infra`; coordina allí cambios de puerto, ruta o configuración.

## Al terminar cualquier tarea
- Tras cambios no triviales de código de producción, aplica `/clean-code-guard` antes de finalizar.
- Ejecuta `make verify`; incluye Ruff, formato, checks de Django, migraciones y tests.
- Añade tests y migraciones para todo cambio de comportamiento o modelo.
- Verifica los health checks si modificas base de datos, middleware, settings o arranque.
