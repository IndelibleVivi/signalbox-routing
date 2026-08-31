PYTHON ?= python3

.PHONY: verify schemas contracts test

verify: schemas contracts test

schemas:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/validate_schemas.py

contracts:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/validate.py

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -p 'test_*.py'
