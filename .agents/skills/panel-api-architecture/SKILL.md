---
name: panel-api-architecture
description: Use ONLY in panel-api when creating, moving, or reviewing Django code placement, src layout, tests layout, modules, apps, API views, services, domain logic, infrastructure adapters, migrations, or health checks.
metadata:
  project: panel-api
---

# Panel API Architecture

This skill defines where code belongs in `panel-api`. Apply it before creating,
moving, or reviewing files in this project.

## Required Layout

All importable application code lives under `src/`. All tests live under `tests/`.
Do not add new Django apps or production Python modules at the repository root.

```text
panel-api/
├── src/
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── common/
│   │   └── health/
│   └── identity/
│       ├── api/
│       ├── application/
│       ├── domain/
│       └── infrastructure/
├── tests/
│   ├── identity/
│   ├── shops/
│   ├── common/
│   ├── integration/
│   └── architecture/
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Makefile
└── Dockerfile
```

## Architectural Style

Use feature-based Django apps with internal clean architecture boundaries.

- Organize first by business capability: `identity` today, and a new module when a capability exists.
- Do not create global technical folders such as `controllers/`, `services/`,
  `repositories/`, `serializers/`, or `models/` at `src/` root.
- Inside each module, organize by responsibility: `api`, `application`, `domain`,
  and `infrastructure`.
- Keep Django framework details at the edges. Business rules should not depend on
  DRF requests, responses, serializers, settings, HTTP clients, or ORM querysets.

## Layer Responsibilities

### `src/<module>/api/`

Put HTTP and DRF boundary code here.

- DRF views, viewsets, API-specific permissions, serializers, request parsing, and
  response shaping.
- URL declarations local to the module when needed.
- Translation from HTTP input into application use case input.
- No business rules beyond HTTP validation and presentation concerns.
- No direct outbound HTTP calls to other services.

Typical files:

```text
src/identity/api/views.py
src/identity/api/serializers.py
src/identity/api/urls.py
```

### `src/<module>/application/`

Put use cases and orchestration here.

- Application services, use cases, commands, queries, DTOs, and ports/protocols.
- Coordinates domain logic and infrastructure interfaces.
- Defines contracts needed by the use case, implemented by infrastructure.
- Does not import DRF, Django HTTP objects, concrete HTTP clients, or settings.
- Avoid direct ORM usage unless the module intentionally uses Django models as the
  persistence boundary for owned data and there is no cleaner adapter yet.

Typical files:

```text
src/identity/application/services.py
src/identity/application/use_cases.py
src/identity/application/ports.py
src/identity/application/dtos.py
```

### `src/<module>/domain/`

Put business concepts and rules here.

- Entities, value objects, domain services, policies, errors, and pure business
  rules.
- No Django, DRF, ORM, HTTP, environment variables, settings, or infrastructure
  imports.
- Prefer plain Python dataclasses, enums, functions, and exceptions.
- Code here should be testable without Django setup.

Typical files:

```text
src/<module>/domain/entities.py
src/<module>/domain/policies.py
src/<module>/domain/errors.py
```

### `src/<module>/infrastructure/`

Put external system adapters here.

- HTTP clients, repository implementations, cache adapters, message clients,
  settings readers, and telemetry adapters.
- Implements ports defined in `application`.
- May import Django settings, requests/httpx, ORM models, environment-backed
  configuration, and third-party SDKs.
- Must not contain business rules that belong in `domain` or orchestration that
  belongs in `application`.

Typical files:

```text
src/identity/infrastructure/account_session_client.py
src/<module>/infrastructure/repositories.py
```

### `src/<module>/models.py` and `src/<module>/migrations/`

Keep Django-owned persistence here.

- Use `models.py` and `migrations/` at the app root so Django migration discovery
  stays conventional.
- Only create models for data owned by `panel-api`.
- Do not mirror products, orders, payments, or external identity data as a source
  of truth.
- If model logic grows into business rules, move the rule into `domain` and keep
  the Django model as persistence state.

## Shared Code

### `src/common/health/`

Put cross-module health checks here.

- `/health/live` and `/health/ready` do not belong to `identity`.
- Keep health views small and explicit.
- Readiness may check database or required dependencies; liveness should avoid
  fragile dependency checks.

### `src/common/`

Only place code here when it is truly shared across modules.

- Do not create generic dumping grounds such as `common/utils.py`.
- `src/common/http.py` performs a JSON HTTP call. Each module adds its own headers and maps `RemoteServiceError` to its own error.
- Shared code must be stable and domain-neutral.

## Tests Layout

All tests live under `tests/`, grouped by the module or test type.

```text
tests/
├── identity/
├── common/
├── integration/
└── architecture/
```

- Put module unit tests in `tests/<module>/`.
- Put cross-module and API flow tests in `tests/integration/`.
- Put import-boundary, layout, and dependency-rule tests in `tests/architecture/`.
- Do not add new `tests.py` files inside Django apps.
- Domain tests should not require Django database setup unless the behavior
  genuinely crosses into persistence.

## Adding A New Module

When adding a new business capability, create the module under `src/<module>/`
with this shape:

```text
src/<module>/
├── api/
├── application/
├── domain/
├── infrastructure/
├── models.py
└── migrations/
```

Also create tests under:

```text
tests/<module>/
```

Register the Django app in `INSTALLED_APPS` only after the module exists and the
app has a clear ownership boundary.

## Import Rules

Allowed dependency direction:

```text
api -> application -> domain
infrastructure -> application/domain
models -> domain only when model methods delegate to domain concepts
config -> api/common wiring only
```

Forbidden dependencies:

- `domain` importing `api`, `application`, `infrastructure`, Django, DRF, or ORM.
- `application` importing `api`, concrete infrastructure clients, DRF, or Django
  HTTP request/response classes.
- `api` containing business rules or outbound service clients.
- `infrastructure` calling DRF views or serializers.
- Cross-module imports that bypass an application-level interface.

When two modules need to collaborate, prefer an application port or explicit
facade instead of importing another module's internals.

## Placement Checklist

Before creating a file, answer these questions:

1. Which business capability owns this behavior?
2. Is this HTTP/API code? Put it in `src/<module>/api/`.
3. Is this a use case or orchestration? Put it in `src/<module>/application/`.
4. Is this a business rule independent of Django? Put it in `src/<module>/domain/`.
5. Is this an external dependency adapter? Put it in `src/<module>/infrastructure/`.
6. Is this a Django model for owned data? Put it in `src/<module>/models.py`.
7. Is this health or truly shared code? Put it under `src/common/`.
8. Is this a test? Put it under `tests/`, not inside `src/`.

If none of these answers is clear, stop and clarify the ownership boundary before
writing code.

## Migration From Current Layout

The target layout is `src/` plus `tests/`. When moving existing code, update all
affected tooling in the same change:

- `Makefile` commands should call `python src/manage.py ...`.
- `Dockerfile` should copy `src/` and run from the correct working directory.
- `DJANGO_SETTINGS_MODULE` should still point to `config.settings` if `src/` is on
  `PYTHONPATH`.
- `INSTALLED_APPS` should keep the stable app label `identity`.
- Test discovery must include `tests/`.
- Ruff and architecture tests must validate the new paths.

Do not partially migrate one module to `src/` while leaving related imports,
commands, or tests broken.
