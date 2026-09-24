.PHONY: lint test check verify

lint:
	python -m ruff check .
	python -m ruff format --check .

test:
	python manage.py test

check:
	python manage.py check
	python manage.py makemigrations --check --dry-run

verify: lint check test
