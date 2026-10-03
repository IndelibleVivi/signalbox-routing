PYTHON ?= python3

.PHONY: verify schemas contracts handoff scenarios test

verify: schemas contracts handoff scenarios test

schemas:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/validate_schemas.py

contracts:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/validate.py

handoff:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m scripts.handoff --evaluated-at 2026-10-03T00:00:03Z --summary

scenarios:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m scripts.replay --summary

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -p 'test_*.py'
