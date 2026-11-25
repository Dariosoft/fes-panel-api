# UML 003 — Frontera de gestión de tienda del vendedor

Este documento describe el desarrollo de `panel-api` para la spec 003: una frontera que reenvía
la consulta y el guardado de la tienda del vendedor hacia `account-api`, sin modelo ni
migración local. La identidad y la tienda son propiedad de `account-api`; `panel-api` solo
transporta la cookie de sesión `fes_session` y retransmite estado y cuerpo JSON.

## Flujo principal (secuencia)

El navegador (`panel-web`) llama a `panel-api` con la cookie `fes_session`. `panel-api` construye
el gateway con `build_account_api_gateway()`, y la vista `PanelShopView` invoca el caso de uso
correspondiente (`get_shop` o `save_shop`), que delega en `AccountApiGateway`. El adaptador
`AccountApiClient` hace la llamada HTTP real a `account-api` reenviando la cookie mediante el
header `Cookie`. Los `200`/`404`/`401`/`403`/`400`/`422` se retransmiten tal cual; cualquier
error de transporte o `5xx` se convierte en `AccountApiUnavailable` y la vista responde `503`
con el cuerpo de contrato, sin borrar la cookie.

```mermaid
sequenceDiagram
    autonumber
    participant W as panel-web (navegador)
    participant P as PanelShopView (panel-api)
    participant U as get_shop / save_shop
    participant G as AccountApiClient (gateway)
    participant A as account-api

    Note over W,A: Consulta de tienda
    W->>P: GET /panel/shop  (Cookie: fes_session=...)
    P->>G: get_shop(fes_session)
    G->>A: GET /accounts/shop  (Cookie: fes_session=...)
    alt Cuenta con tienda
        A-->>G: 200 {name, description|null}
        G-->>P: ServiceResponse(200, body)
        P-->>W: 200 {name, description|null}
    else Cuenta sin tienda
        A-->>G: 404 (cuerpo de account-api)
        G-->>P: ServiceResponse(404, body)
        P-->>W: 404 (panel-web lo trata como estado vacío)
    else Sin sesión
        A-->>G: 401
        G-->>P: ServiceResponse(401, body)
        P-->>W: 401
    else Servicio no disponible
        G--xP: AccountApiUnavailable
        P-->>W: 503 {error: servicio_no_disponible, message: "..."}
    end

    Note over W,A: Guardado (upsert) de tienda
    W->>P: PUT /panel/shop  (Cookie: fes_session)  body JSON {name, description}
    P->>G: save_shop(fes_session, body, content_type)
    G->>A: PUT /accounts/shop  (Cookie, body, Content-Type)
    alt Guardado válido
        A-->>G: 200 {name, description|null}
        G-->>P: ServiceResponse(200, body)
        P-->>W: 200 {name, description|null}
    else Datos inválidos
        A-->>G: 400/422 {motivo}
        G-->>P: ServiceResponse(400/422, body)
        P-->>W: 400/422 {motivo reportado}
    else Sin sesión / no permitido
        A-->>G: 401/403
        G-->>P: ServiceResponse(401/403, body)
        P-->>W: 401/403
    else Servicio no disponible
        G--xP: AccountApiUnavailable
        P-->>W: 503 {error: servicio_no_disponible, message: "..."}
    end
```

Observaciones de contrato:

- La sesión nunca se invalida en `panel-api`; la cookie solo se reenvía. Un `503` no emite
  `Set-Cookie` de borrado (RF-12).
- `PUT` es upsert en `account-api`: crea si no existe y reemplaza `name`/`description` si
  existe (RF-3, RF-4).
- `panel-api` no valida ni transforma `name`/`description`; solo reenvía bytes (RF-13).

## Estructura de componentes

La vista depende de los casos de uso; los casos de uso dependen del port `AccountApiGateway`;
el adaptador `AccountApiClient` implementa el port y usa el transporte compartido `request_json`
de `common/http.py`. `build_account_api_gateway()` es el punto de composición que construye el
cliente desde settings. La app `shops` no tiene `models.py` ni `migrations/`.

```mermaid
classDiagram
    direction LR

    class PanelShopView {
        +permission_classes = [AllowAny]
        +authentication_classes = []
        +get(request) Response
        +put(request) Response
        -_unavailable_body
    }

    class get_shop {
        <<use case>>
        +get_shop(gateway, fes_session) ServiceResponse
    }

    class save_shop {
        <<use case>>
        +save_shop(gateway, fes_session, body, content_type) ServiceResponse
    }

    class AccountApiGateway {
        <<protocol>>
        +get_session(fes_session) AccountSession
        +logout(fes_session) AccountLogout
        +get_shop(fes_session) ServiceResponse
        +save_shop(fes_session, body, content_type) ServiceResponse
    }

    class AccountApiClient {
        -str base_url
        -float timeout_seconds
        +get_shop(fes_session) ServiceResponse
        +save_shop(fes_session, body, content_type) ServiceResponse
        -_request(method, path, fes_session, body, content_type)
    }

    class build_account_api_gateway {
        <<factory>>
        +build_account_api_gateway() AccountApiGateway
    }

    class ServiceResponse {
        +int status_code
        +JsonBody body
    }

    class AccountApiUnavailable {
        <<exception>>
    }

    class request_json {
        <<common/http.py>>
        +request_json(base_url, JsonRequest) tuple
    }

    class ShopsConfig {
        +name = "shops"
        +label = "shops"
    }

    class ACCOUNT_SHOP_PATH {
        <<constant>>
        = "/accounts/shop"
    }

    PanelShopView --> get_shop : usa en GET
    PanelShopView --> save_shop : usa en PUT
    PanelShopView ..> AccountApiUnavailable : captura -> 503
    PanelShopView ..> build_account_api_gateway : compone gateway

    get_shop --> AccountApiGateway : delega
    save_shop --> AccountApiGateway : delega
    get_shop ..> ServiceResponse : retorna
    save_shop ..> ServiceResponse : retorna

    AccountApiClient ..|> AccountApiGateway : implementa
    build_account_api_gateway ..> AccountApiClient : construye
    AccountApiClient ..> ACCOUNT_SHOP_PATH : usa ruta
    AccountApiClient ..> ServiceResponse : produce
    AccountApiClient ..> AccountApiUnavailable : lanza ante 5xx/transporte
    AccountApiClient --> request_json : transporte HTTP

    ShopsConfig ..> PanelShopView : registra app
```

## Notas de ubicación y dependencias

- `src/shops/api/views/panel_shop.py`: vista DRF delgada; traduce HTTP a entrada de casos de
  uso y arma la respuesta. No contiene reglas de negocio ni acceso HTTP saliente directo.
- `src/shops/use_cases/get_shop.py` y `save_shop.py`: orquestación mínima, sin Django ni DRF.
- `src/common/ports/account_api_gateway.py`: contrato de la frontera con `account-api`.
- `src/common/infrastructure/clients/account_api_client.py`: adaptador concreto; reenvía la
  cookie `fes_session` y mapea fallos a `AccountApiUnavailable`.
- `src/common/contracts/account_api.py`: `ACCOUNT_SHOP_PATH = "/accounts/shop"`.
- `src/config/settings.py` y `src/config/urls.py`: registro de la app `shops` y ruta
  `panel/shop`.
- Sin `src/shops/models.py` ni `src/shops/migrations/`: `panel-api` no persiste tienda
  (RF-7, RF-8).
