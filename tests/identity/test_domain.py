import ast
import importlib
import unittest
from pathlib import Path


class DomainConstantsTests(unittest.TestCase):
    def test_session_cookie_name_and_error_are_pure(self):
        from identity.domain import SESSION_COOKIE_NAME, AccountServiceUnavailable

        self.assertEqual(SESSION_COOKIE_NAME, "fes_session")
        self.assertTrue(issubclass(AccountServiceUnavailable, Exception))

    def test_domain_module_has_no_django_or_shops_imports(self):
        domain_root = Path(__file__).resolve().parents[2] / "identity" / "domain"
        forbidden = {"django", "rest_framework", "shops"}
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
        module = importlib.import_module("identity.domain")
        self.assertEqual(module.SESSION_COOKIE_NAME, "fes_session")
