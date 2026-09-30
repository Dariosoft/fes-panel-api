.PHONY: lint test check verify

export PYTHONPATH := src:.

lint:
	python -m ruff check .
	python -m ruff format --check .

test:
	python src/manage.py test tests

check:
	python src/manage.py check
	python src/manage.py makemigrations --check --dry-run

verify: lint check test
