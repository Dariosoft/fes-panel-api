---
name: python-clean-code
description: Use when implementing or reviewing Python/Django code to keep constants, contracts, configuration, and framework routes in clear ownership boundaries.
---

# Python Clean Code

Use this skill when adding, moving, or reviewing Python/Django code, especially when deciding whether string literals should stay inline or become named constants.

## Constant Boundaries

- Extract constants when a literal represents a stable protocol, external contract, shared payload key, cookie contract, header name, status value, or repeated business term.
- Keep framework route declarations inline when the literal is local to the framework mapping and is not reused outside that mapping.
- Keep settings keys, Django app labels, import paths, and one-off local literals inline unless reuse creates a concrete maintenance problem.
- Do not create a generic `constants.py` dumping ground for unrelated values.
- Prefer small, categorized modules named after the contract or responsibility.

## Placement

- Put externally shared service contracts under `common/contracts/<service>.py` when multiple apps may call the same remote service.
- Put feature-owned constants inside that app when the value belongs only to that capability.
- Put configuration values in `config/settings.py` only when they vary by environment or deployment.
- Put HTTP-specific reusable values near HTTP code when they describe request/response behavior rather than domain rules.
- Avoid mega-generic folders such as `application/` when they hide unrelated responsibilities.
- Prefer categorized app-level packages such as `use_cases/`, `ports/`, `dtos/`, `navigation/`, `api/`, `domain/`, and `infrastructure/` when those names describe the files they contain more directly.
- Put use case functions in `use_cases/`, protocols/interfaces in `ports/`, immutable transfer shapes in `dtos/`, and redirect/navigation URL builders in `navigation/`.
- Keep one top-level class per file once code is categorized into packages; name the file after the class in snake_case.
- Put each DTO class in its own file under `dtos/` and each domain error class in its own file under `domain/errors/`.

## Django Routes

- Keep `path(...)` and `include(...)` route fragments inline in `urls.py` for readability.
- Do not extract route strings from Django URL declarations only for stylistic consistency.
- Extract route paths only when the same path is reused outside URL mapping, for example in redirects, tests, documentation generators, or reverse-proxy contracts.

## DRF Views And ViewSets

- Prefer `src/<module>/api/views/` as a package once an app exposes multiple API views or endpoint concepts.
- Keep one API view or viewset per file after the first simple endpoint, named after the HTTP concept it owns.
- Prefer a `ViewSet` when multiple routes operate on the same conceptual resource or aggregate, even if routes are mapped manually instead of through a router.
- Use DRF's conventional resource action names when they fit: `list`, `create`, `retrieve`, `update`, `partial_update`, and `destroy`.
- Map CRUD semantics to resource actions consistently: collection reads to `list`, single-resource reads to `retrieve`, creation to `create`, full replacement to `update`, partial changes to `partial_update`, and deletion/invalidating the resource to `destroy`.
- Add non-CRUD custom actions to a `ViewSet` only when they still belong to the same resource lifecycle or aggregate behavior, for example `activate`, `refresh`, `archive`, or `resend_invitation`.
- Prefer a separate `APIView` or a separate `ViewSet` when a custom action starts a different protocol, crosses into another capability, or only shares the URL prefix but not the resource concept.
- Prefer `APIView` for standalone redirects, callbacks, webhooks, health checks, and actions that do not share a resource lifecycle.
- Do not group unrelated endpoints into one `ViewSet` only to reduce file count.
- Keep public URLs stable when introducing a `ViewSet`; manual `as_view({"method": "action"})` mappings are acceptable when they preserve an existing contract.

## External API Contracts

- Treat paths, query parameters, payload keys, and cookie/header names for remote services as contract constants.
- Place remote-service constants outside a single app if the service can be called by future apps.
- Name contract modules by provider, for example `common/contracts/account_api.py`.

Example:

```python
ACCOUNT_LOGIN_GOOGLE_PATH = "/accounts/login/google"
ACCOUNT_LOGOUT_PATH = "/accounts/logout"
ACCOUNT_SESSION_PATH = "/accounts/session"

RETURN_TO_PARAM = "return_to"
```

## Cookie Contracts

- Extract cookie names and reusable cookie attributes when they form part of a shared HTTP contract.
- Keep one-off response values inline if they are specific to a single endpoint and unlikely to be reused.

Example:

```python
SESSION_COOKIE_NAME = "fes_session"
SESSION_COOKIE_EXPIRES_PAST = "Thu, 01 Jan 1970 00:00:00 GMT"
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_SAMESITE = "Lax"
```

## Review Checklist

- Does this literal describe a contract or just local implementation detail?
- Would moving this value make ownership clearer, or only add indirection?
- Is the constant placed where future callers would naturally look for it?
- Is the name specific enough to avoid a global constants bucket?
- Are Django route declarations still easy to read?
