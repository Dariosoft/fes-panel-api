from django.test import SimpleTestCase
from django.urls import resolve

from shops.views import live


class UrlTests(SimpleTestCase):
    def test_live_route(self):
        self.assertEqual(resolve("/health/live").func, live)
