SHELL := /bin/bash
WD := $(shell pwd)
PYTHONPATH := $(wd):$(wd)/src
PYTHON_VERSION := $(shell grep "^requires-python" pyproject.toml | cut -d'"' -f2 | sed 's/>=//')
PIP = pip

# # Try to include .env, fail gracefully if missing
# -include .env
# # Space-separated list of vars required from .env
# REQUIRED_VARS := ""

.PHONY: install audit clean


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

prepare-psycopg-layer:
	uv export --only-group psycopg-layer --output-file requirements-psycopg.txt
	mkdir -p build/psycopg-layer/python
	$(PIP) install -r requirements-psycopg.txt \
		--platform manylinux2014_x86_64 \
		--target=build/psycopg-layer/python \
		--implementation cp \
		--python-version $(PYTHON_VERSION) \
		--only-binary=:all: \
		--upgrade \
		--no-deps

# Check that env exists and required vars are set
# .env-check:
# 	@if [ ! -f .env ]; then \
# 		echo "Error: .env file not found"; \
# 		exit 1; \
# 	fi
# 	@$(foreach var,$(REQUIRED_VARS),\
# 		if [ -z "$($(var))" ]; then \
# 			echo "Error: $(var) not set in .env"; \
# 			exit 1; \
# 		fi; \
# 	)

define zip_to_bucket
	@# arg1: path/to/code/file.py, arg2: s3-bucket-name
	$(eval FILEPATH := $(strip $1))
	$(eval BUCKET := $(strip $2))

	@# Get filename from path, then strip ext
	$(eval FILENAME := "$(notdir "$(FILEPATH)")")
	$(eval FILENAME := "$(basename "$(FILENAME)")")

	@# Zip it up
	@printf "\n%s\n" "Zipping $(FILEPATH) to packages/temp/$(FILENAME).zip ..."
	@mkdir -p packages/temp/
	@zip -j "packages/temp/$(FILENAME).zip" "$(FILEPATH)"

	@# Upload to S3
	@echo "Attempting upload to S3 ..."
	@source .env && aws s3 cp "packages/temp/$(FILENAME).zip" "s3://$(BUCKET)/$(FILENAME)/current.zip"
endef

deploy-to-dev:
	$(eval CODE_BUCKET := $(shell \
		cat infra/envs/dev/terraform.tfvars | \
		grep CODE_BUCKET | \
		sed -E "s/\s*CODE_BUCKET\s*=\s*['\"]?([^'\"]+)['\"]?\s*$$/\1/" | \
		xargs))
	@echo "Bucket name retrieved from infra/envs/dev/terraform.tfvars: \"$(CODE_BUCKET)\""
	$(call zip_to_bucket, src/lambdas/create_budibase_instance.py, $(CODE_BUCKET))
	$(call zip_to_bucket, src/lambdas/destroy_budibase_instance.py, $(CODE_BUCKET))
	$(call zip_to_bucket, src/lambdas/ci_checks_for_rds.py, $(CODE_BUCKET))
	@printf "\n%s\n" "Switching into 'dev' Terraform environment ..."
	@cd infra && ./switch_env.sh dev
	@printf "\n%s\n" "Running terraform plan ..."
	@cd infra && terraform plan -out=tfplan -no-color -var-file="envs/dev/terraform.tfvars" 2>&1 > plan.out
	@printf "\n%s\n" "Plan successfully output."
	@echo "If you wish to proceed with the plan in infra/plan.out, type Y: ";
	@read RESPONSE; \
	if [[ "$$RESPONSE" == "Y" ]]; then \
		cd infra && terraform apply tfplan; \
	else \
		printf "\n%s\n" "Terraform plan will not be applied. Exiting."; \
	fi

clean:
	rm -rf packages/temp build
