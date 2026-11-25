from common.dtos import AccountLogout, AccountSession, ServiceResponse


class FakeShopGateway:
    def __init__(
        self,
        response: ServiceResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response or ServiceResponse(status_code=200, body={})
        self._error = error
        self.calls: list[tuple] = []

    def get_session(self, fes_session: str | None) -> AccountSession:
        raise AssertionError("get_session should not be called")

    def logout(self, fes_session: str | None) -> AccountLogout:
        raise AssertionError("logout should not be called")

    def get_shop(self, fes_session: str | None) -> ServiceResponse:
        self.calls.append(("get_shop", fes_session))
        if self._error:
            raise self._error
        return self._response

    def save_shop(
        self,
        fes_session: str | None,
        body: bytes,
        content_type: str | None,
    ) -> ServiceResponse:
        self.calls.append(("save_shop", fes_session, body, content_type))
        if self._error:
            raise self._error
        return self._response
