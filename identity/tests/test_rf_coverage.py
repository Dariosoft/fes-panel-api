"""RF-1 … RF-14 automated coverage map for spec 001."""

from django.test import SimpleTestCase
from django.test.runner import DiscoverRunner

RF_COVERAGE = {
    "RF-1": [
        "identity.tests.test_endpoints.WhoAmIEndpointTests.test_rf1_rf8_whoami_anonymous_without_session",
        "identity.tests.test_door_limits.OptionalAuthAndDoorTests.test_rf1_existing_panel_route_usable_without_login",
    ],
    "RF-2": [
        "identity.tests.test_endpoints.LoginEndpointTests.test_rf2_rf5_login_success_opens_shared_session",
        "identity.tests.test_services.IdentityServiceTests.test_login_with_google_success_without_local_account_writes",
    ],
    "RF-3": [
        "identity.tests.test_endpoints.LoginEndpointTests.test_rf3_login_without_panel_membership",
    ],
    "RF-4": [
        "identity.tests.test_endpoints.LoginEndpointTests.test_rf4_rejects_non_google_provider",
    ],
    "RF-5": [
        "identity.tests.test_endpoints.LoginEndpointTests.test_rf2_rf5_login_success_opens_shared_session",
    ],
    "RF-6": [
        "identity.tests.test_endpoints.LogoutEndpointTests.test_rf6_rf13_logout_authenticated_closes_shared_session",
        "identity.tests.test_post_logout_flow.PostLogoutFlowTests.test_rf6_rf13_login_logout_then_whoami_is_anonymous",
    ],
    "RF-7": [
        "identity.tests.test_door_limits.OptionalAuthAndDoorTests.test_rf7_identity_operations_are_under_panel_prefix",
        "identity.tests.test_endpoints.LoginEndpointTests.test_rf4_rejects_non_google_provider",
    ],
    "RF-8": [
        "identity.tests.test_endpoints.WhoAmIEndpointTests.test_rf1_rf8_whoami_anonymous_without_session",
        "identity.tests.test_endpoints.WhoAmIEndpointTests.test_rf8_rf13_whoami_authenticated_with_session",
    ],
    "RF-9": [
        "identity.tests.test_endpoints.LoginEndpointTests.test_rf9_relogin_replaces_current_account",
    ],
    "RF-10": [
        "identity.tests.test_endpoints.LogoutEndpointTests.test_rf10_logout_without_session_is_idempotent",
    ],
    "RF-11": [
        "identity.tests.test_endpoints.LoginEndpointTests.test_rf11_google_rejection_does_not_authenticate",
        "identity.tests.test_account_client.AccountClientTests.test_confirm_google_access_rejects_business_error",
    ],
    "RF-12": [
        "identity.tests.test_endpoints.LoginEndpointTests.test_rf12_account_unavailable_does_not_authenticate",
        "identity.tests.test_account_client.AccountClientTests.test_confirm_google_access_maps_timeout_to_unavailable",
        "identity.tests.test_account_client.AccountClientTests.test_confirm_google_access_maps_5xx_to_unavailable",
    ],
    "RF-13": [
        "identity.tests.test_endpoints.WhoAmIEndpointTests.test_rf8_rf13_whoami_authenticated_with_session",
        "identity.tests.test_endpoints.LogoutEndpointTests.test_rf6_rf13_logout_authenticated_closes_shared_session",
        "identity.tests.test_post_logout_flow.PostLogoutFlowTests.test_rf6_rf13_login_logout_then_whoami_is_anonymous",
    ],
    "RF-14": [
        "identity.tests.test_door_limits.OptionalAuthAndDoorTests.test_rf14_no_store_login_endpoints",
    ],
}


class RfCoverageTests(SimpleTestCase):
    def test_all_functional_requirements_have_named_tests(self):
        """Every RF-1…RF-14 maps to at least one automated test id."""
        expected = {f"RF-{i}" for i in range(1, 15)}
        self.assertEqual(set(RF_COVERAGE), expected)
        for rf, tests in RF_COVERAGE.items():
            self.assertGreaterEqual(len(tests), 1, msg=rf)
            for test_id in tests:
                self.assertIn(".", test_id)
                self.assertTrue(test_id.startswith("identity.tests."), msg=test_id)

    def test_rf_coverage_test_ids_are_discoverable(self):
        """Coverage entries resolve to methods Django's test loader can import."""
        loader = DiscoverRunner(verbosity=0).test_loader
        for rf, tests in RF_COVERAGE.items():
            for test_id in tests:
                suite = loader.loadTestsFromName(test_id)
                self.assertGreater(suite.countTestCases(), 0, msg=f"{rf}: {test_id}")
