SHELL := /bin/bash
WD := $(shell pwd)
PYTHONPATH := $(wd):$(wd)/src
PIP = pip

# Try to include .env, fail gracefully if missing
-include .env
# Space-separated list of vars required from .env
REQUIRED_VARS := CODE_BUCKET_DEV

.PHONY: install audit


###############################################################################
## CI checks

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
	cd infra && terraform validate

unit-tests:
	PYTHONPATH=${PYTHONPATH} uv run pytest -v --cov=src --cov-report term-missing test/

all-checks: audit security-checks code-checks terraform-checks unit-tests


###############################################################################
## CD layer and code deployment

prepare-layer:
	uv export --only-group lambda-layer --output-file requirements-lambda.txt
	$(PIP) install -r requirements-lambda.txt -t build/layer/python

# Check that env exists and required vars are set
.env-check:
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found"; \
		exit 1; \
	fi
	@$(foreach var,$(REQUIRED_VARS),\
		if [ -z "$($(var))" ]; then \
			echo "Error: $(var) not set in .env"; \
			exit 1; \
		fi; \
	)

define zip_to_bucket
	@# arg1: path/to/code/file.py, arg2: s3-bucket-name
	$(eval FILEPATH := $(strip $1))
	$(eval BUCKET := $(strip $2))

	@# Get filename from path, then strip ext
	$(eval FILENAME := "$(notdir "$(FILEPATH)")")
	$(eval FILENAME := "$(basename "$(FILENAME)")")

	@# Zip it up
	@echo "Zipping $(FILEPATH) to packages/temp/$(FILENAME).zip ..."
	@mkdir -p packages/temp/
	@zip -j "packages/temp/$(FILENAME).zip" "$(FILEPATH)"

	@# Upload to S3
	@echo "Attempting upload to S3 using CODE_BUCKET_DEV var expected in .env ..."
	@source .env && aws s3 cp "packages/temp/$(FILENAME).zip" "s3://$(BUCKET)/current.zip"
endef

zip-it-up: .env-check
	$(call zip_to_bucket, src/create_budibase_instance.py, $(CODE_BUCKET_DEV))
