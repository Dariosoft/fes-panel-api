import ast
import importlib
import unittest
from pathlib import Path


class CatalogDomainTests(unittest.TestCase):
    def test_cookie_name_and_errors_are_distinct(self):
        from catalog.domain import (
            SESSION_COOKIE_NAME,
            CatalogServiceUnavailable,
            SessionServiceUnavailable,
        )

        self.assertEqual(SESSION_COOKIE_NAME, "fes_session")
        self.assertTrue(issubclass(SessionServiceUnavailable, Exception))
        self.assertTrue(issubclass(CatalogServiceUnavailable, Exception))
        self.assertIsNot(SessionServiceUnavailable, CatalogServiceUnavailable)
        self.assertFalse(issubclass(SessionServiceUnavailable, CatalogServiceUnavailable))
        self.assertFalse(issubclass(CatalogServiceUnavailable, SessionServiceUnavailable))

    def test_domain_module_has_no_framework_imports(self):
        domain_root = Path(__file__).resolve().parents[2] / "src" / "catalog" / "domain"
        forbidden = {"django", "rest_framework"}
        for path in domain_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module.split(".")[0]]
                else:
                    continue
                for name in names:
                    self.assertNotIn(name, forbidden, f"{path} imports {name}")

    def test_domain_imports_without_django_setup(self):
        module = importlib.import_module("catalog.domain")
        self.assertEqual(module.SESSION_COOKIE_NAME, "fes_session")
