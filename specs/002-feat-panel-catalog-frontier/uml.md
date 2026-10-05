# UML 002 - Frontera de catalogo: drafts, publicacion y sesion

Diagramas **as-built**. Los clientes, puertos, DTOs, errores y contratos de
servicios externos pertenecen a `common`; identity y catalog contienen solo su
API, navegacion/casos de uso y DTOs estrictamente locales.

## 1. Layout

```text
src/
|-- common/
|   |-- contracts/               account_api.py, catalog_api.py
|   |-- dtos/                    AccountSession, AccountLogout, ServiceResponse
|   |-- errors/                  AccountApiUnavailable, CatalogApiUnavailable
|   |-- ports/                   AccountApiGateway, CatalogApiGateway
|   |-- infrastructure/clients/ AccountApiClient, CatalogApiClient
|   |-- http.py
|   |-- json_types.py
|   `-- health/
|-- identity/
|   |-- api/
|   |-- navigation/
|   |-- use_cases/
|   `-- dtos/                    LogoutPanelSessionResult
`-- catalog/
    |-- api/                     composition, guard, views y URLs
    `-- use_cases/
```

## 2. Componentes y dependencias

```mermaid
flowchart TB
  UI["panel-web<br/>cookie fes_session"]

  subgraph Panel[panel-api]
    subgraph Identity[identity]
      IdentityApi["api<br/>session, logout, login redirect"]
      IdentityUC["use_cases<br/>resolve session, logout"]
      IdentityDTO["LogoutPanelSessionResult"]
      Navigation["navigation<br/>return_to seguro"]
    end

    subgraph Catalog[catalog]
      CatalogViews["api.views<br/>products, publish"]
      Guard["api.panel_session<br/>PanelSessionGuardMixin"]
      CatalogUC["use_cases<br/>resolve owner + operaciones"]
    end

    subgraph Common[common]
      Contracts["contracts<br/>account_api, catalog_api<br/>unica SESSION_COOKIE_NAME"]
      Ports["ports<br/>AccountApiGateway<br/>CatalogApiGateway"]
      DTOs["dtos<br/>AccountSession<br/>AccountLogout<br/>ServiceResponse"]
      Errors["errors<br/>AccountApiUnavailable<br/>CatalogApiUnavailable"]
      AccountClient["infrastructure.clients<br/>AccountApiClient"]
      CatalogClient["infrastructure.clients<br/>CatalogApiClient"]
      Factory["infrastructure.client_factory<br/>build_account_api_gateway<br/>build_catalog_api_gateway"]
      Http["http<br/>request_json"]
      Health["health<br/>live, ready"]
    end
  end

  Accounts[account-api]
  CatalogService[catalog-api]

  UI --> IdentityApi
  UI --> CatalogViews
  UI --> Health
  IdentityApi --> IdentityUC
  IdentityApi --> Navigation
  IdentityUC --> Ports
  IdentityUC --> DTOs
  IdentityUC --> Errors
  IdentityUC --> IdentityDTO
  IdentityApi --> Factory

  CatalogViews --> Guard
  CatalogViews --> CatalogUC
  Guard --> CatalogUC
  Guard --> Ports
  Guard --> DTOs
  Guard --> Errors
  Guard --> Contracts
  Guard --> Factory
  Factory --> AccountClient
  Factory --> CatalogClient
  Factory --> Ports
  CatalogUC --> Ports
  CatalogUC --> DTOs

  AccountClient -. implementa .-> Ports
  CatalogClient -. implementa .-> Ports
  AccountClient --> Contracts
  AccountClient --> DTOs
  AccountClient --> Errors
  AccountClient --> Http
  CatalogClient --> Contracts
  CatalogClient --> DTOs
  CatalogClient --> Errors
  CatalogClient --> Http
  AccountClient --> Accounts
  CatalogClient --> CatalogService
```

## 3. Clases y contratos comunes

```mermaid
classDiagram
  direction TB

  class AccountApiGateway {
    <<Protocol>>
    +get_session(fes_session) AccountSession
    +logout(fes_session) AccountLogout
  }
  class CatalogApiGateway {
    <<Protocol>>
    +list_products(owner, name) ServiceResponse
    +create_product(owner, body, content_type) ServiceResponse
    +update_product(owner, id, body, content_type) ServiceResponse
    +delete_product(owner, id) ServiceResponse
    +publish_product(owner, id) ServiceResponse
    +unpublish_product(owner, id) ServiceResponse
    +publish_catalog(owner, body, content_type) ServiceResponse
  }
  class AccountApiClient {
    +get_session(fes_session) AccountSession
    +logout(fes_session) AccountLogout
  }
  class CatalogApiClient {
    +list_products(owner, name) ServiceResponse
    +create_product(owner, body, content_type) ServiceResponse
    +update_product(owner, id, body, content_type) ServiceResponse
    +delete_product(owner, id) ServiceResponse
    +publish_product(owner, id) ServiceResponse
    +unpublish_product(owner, id) ServiceResponse
    +publish_catalog(owner, body, content_type) ServiceResponse
  }
  class AccountSession {
    +status_code: int
    +body: dict
    +authenticated: bool
    +account_id: str?
  }
  class AccountLogout {
    +status_code: int
    +body: dict
    +had_active_session: bool
  }
  class ServiceResponse {
    +status_code: int
    +body: JsonBody
  }
  class AccountApiUnavailable
  class CatalogApiUnavailable
  class LogoutPanelSessionResult {
    +status_code: int
    +body: dict
    +clear_cookie: bool
  }
  class PanelSessionGuardMixin

  AccountApiClient ..|> AccountApiGateway
  CatalogApiClient ..|> CatalogApiGateway
  AccountApiClient --> AccountSession
  AccountApiClient --> AccountLogout
  AccountApiClient --> AccountApiUnavailable
  CatalogApiClient --> ServiceResponse
  CatalogApiClient --> CatalogApiUnavailable
  PanelSessionGuardMixin --> AccountApiGateway
  PanelSessionGuardMixin --> CatalogApiGateway
  PanelSessionGuardMixin --> AccountApiUnavailable
  PanelSessionGuardMixin --> CatalogApiUnavailable
  LogoutPanelSessionResult ..> AccountLogout : adapta
```

## 4. Secuencia identity: consultar sesion

```mermaid
sequenceDiagram
  actor Browser as panel-web
  participant View as identity.api PanelSessionViewSet
  participant UC as resolve_panel_session
  participant Port as common AccountApiGateway
  participant Client as common AccountApiClient
  participant Accounts as account-api

  Browser->>View: GET /panel/identity/session + Cookie
  View->>UC: resolve_panel_session(port, fes_session)
  UC->>Port: get_session(fes_session)
  Port->>Client: implementacion compuesta
  Client->>Accounts: GET /accounts/session + Cookie fes_session
  alt respuesta 2xx o 4xx utilizable
    Accounts-->>Client: status + body
    Client-->>UC: AccountSession(status, body, authenticated, id)
    UC-->>View: AccountSession
    View-->>Browser: mismo status + body
  else red, 5xx o respuesta invalida
    Client-->>View: AccountApiUnavailable
    View-->>Browser: 503 servicio_no_disponible
  end
```

Logout usa el mismo cliente y puerto: `AccountApiClient.logout` devuelve
`AccountLogout`; el caso de uso lo adapta a `LogoutPanelSessionResult` para que
la API decida limpiar la cookie del panel.

## 5. Secuencia catalog: listar con filtro

```mermaid
sequenceDiagram
  actor Browser as panel-web
  participant View as catalog.api product view
  participant Guard as PanelSessionGuardMixin
  participant SessionUC as resolve_panel_owner
  participant AccountPort as common AccountApiGateway
  participant AccountClient as common AccountApiClient
  participant Accounts as account-api
  participant ProductUC as list_products
  participant CatalogPort as common CatalogApiGateway
  participant CatalogClient as common CatalogApiClient
  participant Catalog as catalog-api

  Browser->>View: GET /panel/catalog/products?name=mat + Cookie
  View->>Guard: initial(request)
  Guard->>SessionUC: resolve_panel_owner(account port, cookie)
  SessionUC->>AccountPort: get_session(cookie)
  AccountPort->>AccountClient: implementacion compuesta
  AccountClient->>Accounts: GET /accounts/session + Cookie
  alt cuentas no disponible
    AccountClient-->>Guard: AccountApiUnavailable
    Guard-->>Browser: 503 servicio_no_disponible
  else sesion no autenticada o sin id
    Accounts-->>Guard: AccountSession no valida
    Guard-->>Browser: 401 no_autenticado
  else sesion valida
    Accounts-->>Guard: AccountSession(account_id)
    Guard->>View: owner_account_id = account_id
    View->>ProductUC: list_products(catalog port, owner, "mat")
    ProductUC->>CatalogPort: list_products(owner, "mat")
    CatalogPort->>CatalogClient: implementacion compuesta
    CatalogClient->>Catalog: GET /catalog/products?ownerAccountId={owner}&name=mat
    alt catalogo 2xx o 4xx
      Catalog-->>CatalogClient: status + body
      CatalogClient-->>View: ServiceResponse
      View-->>Browser: mismo status + body
    else catalogo no disponible o 5xx
      CatalogClient-->>Guard: CatalogApiUnavailable
      Guard-->>Browser: 503 servicio_no_disponible
    end
  end
```

## 6. Secuencia catalog: multipart y publish

```mermaid
sequenceDiagram
  actor Browser as panel-web
  participant View as catalog.api view
  participant UC as catalog use case
  participant Port as common CatalogApiGateway
  participant Client as common CatalogApiClient
  participant Catalog as catalog-api

  alt crear o actualizar producto
    Browser->>View: POST/PUT + multipart body + Content-Type con boundary
    Note over View: el guard ya fijo owner_account_id
    View->>UC: owner, request.body, META[CONTENT_TYPE]
    UC->>Port: create/update(owner, body, content_type)
    Port->>Client: implementacion compuesta
    Client->>Catalog: ownerAccountId query + body intacto + Content-Type intacto
  else publicar catalogo sin body
    Browser->>View: POST /panel/catalog/publish sin body
    View->>View: body = b"{}"; content_type = application/json
    View->>UC: publish_catalog(owner, body, content_type)
    UC->>Port: publish_catalog(owner, body, content_type)
    Port->>Client: implementacion compuesta
    Client->>Catalog: POST /catalog/publish?ownerAccountId={owner} + {}
  end
  Catalog-->>Client: status + body
  Client-->>View: ServiceResponse
  View-->>Browser: status + body
```

## 7. Restricciones verificadas

- `SESSION_COOKIE_NAME` vive unicamente en `common/contracts/account_api.py`.
- Ambos modulos usan fakes de `common.ports` en sus tests.
- Los tests de clientes viven en `tests/common`.
- La composicion concreta queda en las APIs; los casos de uso dependen de
  Protocols comunes.
- El contrato HTTP, health, CORS y ausencia de persistencia no cambiaron.
- `make verify`: verde, 112 tests, sin migraciones.
