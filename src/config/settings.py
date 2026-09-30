import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-local-development-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "*").split(",")]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ACCOUNT_API_BASE_URL = os.environ.get(
    "ACCOUNT_API_BASE_URL",
    "http://account-api.apps.svc.cluster.local:8080",
).rstrip("/")
ACCOUNTS_PUBLIC_BASE_URL = os.environ.get(
    "ACCOUNTS_PUBLIC_BASE_URL",
    ACCOUNT_API_BASE_URL,
).rstrip("/")
PANEL_PUBLIC_ORIGIN = os.environ.get("PANEL_PUBLIC_ORIGIN", "http://localhost:5174").rstrip("/")
SESSION_COOKIE_DOMAIN = os.environ.get("SESSION_COOKIE_DOMAIN") or None
ACCOUNT_API_TIMEOUT_SECONDS = float(os.environ.get("ACCOUNT_API_TIMEOUT_SECONDS", "5"))

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "corsheaders",
    "rest_framework",
    "identity",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]
TEMPLATES = []
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "panel"),
        "USER": os.environ.get("DATABASE_USERNAME", "panel"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", "panel-local"),
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [PANEL_PUBLIC_ORIGIN]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
