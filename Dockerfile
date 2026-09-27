FROM python:3.14.7-slim-trixie AS verify
ENV PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONPATH=/app/src:/app
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --requirement requirements-dev.txt
COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
RUN python -m ruff check . \
    && python -m ruff format --check . \
    && python src/manage.py check \
    && python src/manage.py makemigrations --check --dry-run \
    && python src/manage.py test tests

FROM python:3.14.7-slim-trixie
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONPATH=/app/src \
    HOME=/tmp \
    OTEL_SERVICE_NAME=panel-api \
    OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability.svc.cluster.local:4318 \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
    OTEL_METRICS_EXPORTER=none \
    OTEL_LOGS_EXPORTER=otlp \
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY requirements.txt ./
RUN pip install --requirement requirements.txt
COPY --from=verify --chown=10001:10001 /app/src ./src
USER 10001:10001
EXPOSE 8000
CMD ["opentelemetry-instrument", "gunicorn", "config.wsgi:application", "--bind=0.0.0.0:8000", "--workers=2", "--threads=2", "--access-logfile=-", "--error-logfile=-"]
