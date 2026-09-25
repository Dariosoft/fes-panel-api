from django.test import Client, SimpleTestCase
from django.urls import get_resolver, reverse

from identity.views import LoginView, LogoutView, WhoAmIView


class OptionalAuthAndDoorTests(SimpleTestCase):
    def test_rf1_existing_panel_route_usable_without_login(self):
        """RF-1: GET /panel responds without requiring authentication."""
        client = Client()
        response = client.get("/panel")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["service"], "panel-api")

    def test_rf7_identity_operations_are_under_panel_prefix(self):
        """RF-7: enter / leave / whoami are the panel's only identity door under /panel."""
        self.assertEqual(reverse("panel-whoami"), "/panel/me")
        self.assertEqual(reverse("panel-logout"), "/panel/session/logout")
        self.assertEqual(reverse("panel-login-google"), "/panel/session/google")

        resolver = get_resolver()
        patterns = {str(p.pattern) for p in resolver.url_patterns}
        self.assertIn("panel/", patterns)

        whoami = resolver.resolve("/panel/me")
        logout = resolver.resolve("/panel/session/logout")
        login = resolver.resolve("/panel/session/google")
        self.assertEqual(whoami.func.view_class, WhoAmIView)
        self.assertEqual(logout.func.view_class, LogoutView)
        self.assertEqual(login.func.view_class, LoginView)

    def test_rf14_no_store_login_endpoints(self):
        """RF-14: this API does not expose store/tienda login routes."""
        client = Client()
        for path in (
            "/panel/store/login",
            "/panel/tienda/login",
            "/panel/session/store",
            "/accounts/session/google",
        ):
            response = client.get(path)
            self.assertEqual(response.status_code, 404, msg=path)
            response = client.post(path)
            self.assertEqual(response.status_code, 404, msg=path)
