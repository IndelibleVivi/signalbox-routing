PYTHON ?= python3

.PHONY: verify contracts test

verify: contracts test

contracts:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/validate.py

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -p 'test_*.py'
