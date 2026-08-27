.PHONY: validate test

validate:
	python scripts/validate_bootstrap.py

test:
	pytest
