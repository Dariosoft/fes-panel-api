from django.test import SimpleTestCase
from django.urls import resolve

from analytics.api.views import PanelAnalyticsMetricsView, PanelAnalyticsTimelineView
from common.health.views import live
from notifications.api.views import PanelFeedView


class PanelProxyUrlTests(SimpleTestCase):
    def test_analytics_routes(self):
        timeline = resolve("/panel/analytics/timeline")
        metrics = resolve("/panel/analytics/metrics")

        self.assertIs(timeline.func.view_class, PanelAnalyticsTimelineView)
        self.assertIs(metrics.func.view_class, PanelAnalyticsMetricsView)

    def test_notifications_feed_route(self):
        match = resolve("/panel/notifications/feed")

        self.assertIs(match.func.view_class, PanelFeedView)

    def test_existing_routes_are_preserved(self):
        self.assertEqual(resolve("/panel/identity/session").url_name, "panel-session")
        self.assertEqual(resolve("/panel/catalog/products").url_name, "panel-catalog-products")
        self.assertEqual(resolve("/panel/shop").url_name, "panel-shop")
        self.assertIs(resolve("/health/live").func, live)
