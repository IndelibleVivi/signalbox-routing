PYTHON ?= python3
SITE_PORT ?= 8765

.PHONY: verify schemas contracts handoff scenarios test site site-verify site-serve

verify: schemas contracts handoff scenarios site-verify test

schemas:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/validate_schemas.py

contracts:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) scripts/validate.py

handoff:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m scripts.handoff --evaluated-at 2026-10-03T00:00:03Z --summary

scenarios:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m scripts.replay --summary

site:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m scripts.build_site

site-verify:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m scripts.build_site --check

site-serve: site
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m scripts.build_site --serve --port $(SITE_PORT)

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -p 'test_*.py'
