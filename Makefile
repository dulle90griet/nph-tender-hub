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

terraform-checks:
	uv run terraform fmt ./infra

lint-format-validate:
	uv run ruff check --fix ./src ./test
	uv run ruff format ./src ./test
	terraform fmt ./infra
	cd infra && uv run terraform validate

unit-tests:
	PYTHONPATH=${PYTHONPATH} uv run pytest -v --cov=src --cov-report term-missing test/

run-checks: audit security-checks terraform-checks lint-format-validate unit-tests

prepare-layer:
	uv export --only-group lambda-layer --output-file requirements-lambda.txt
	$(PIP) install -r requirements-lambda.txt -t build/layer/python
