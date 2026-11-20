.PHONY: lint test coverage check verify

export PYTHONPATH := src:.

lint:
	python -m ruff check .
	python -m ruff format --check .

test:
	python src/manage.py test tests

coverage:
	python -m coverage run --source=src src/manage.py test tests
	python -m coverage xml
	python -m coverage report --fail-under=90

check:
	python src/manage.py check
	python src/manage.py makemigrations --check --dry-run

verify: lint check coverage
