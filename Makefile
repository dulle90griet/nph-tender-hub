WD := $(shell pwd)
PYTHONPATH := $(wd):$(wd)/src
PIP = pip

.PHONY: install audit

install:
	uv sync --group local-dev

audit:
	uv run pip-audit

security-checks:
	uv run bandit -rlll ./src ./test

code-checks:
	uv run ruff check ./src ./test
	uv run ruff format --check ./src ./test

terraform-checks:
	terraform fmt --check ./infra
	cd infra && uv run terraform validate

unit-tests:
	PYTHONPATH=${PYTHONPATH} uv run pytest -v --cov=src --cov-report term-missing test/

all-checks: audit security-checks code-checks terraform-checks unit-tests

prepare-layer:
	uv export --only-group lambda-layer --output-file requirements-lambda.txt
	$(PIP) install -r requirements-lambda.txt -t build/layer/python
