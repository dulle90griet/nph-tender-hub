PYTHON_INTERPETER = python
WD := $(shell pwd)
PYTHONPATH := $(wd):$(wd)/src
SHELL = /bin/bash
PIP = pip

## Create Python interpreter environment
create-environment:
	@echo ">>> About to create Python environment..."
	@echo ">>> Checking Python version."
	$(PYTHON_INTERPETER) --version
	@echo ">>> Setting up virtual environment..."
	$(PIP) install -q virtualenv
	virtualenv .venv --python=$(PYTHON_INTERPETER)

## Define utility variable to help us call Python from the venv
ACTIVATE_ENV := source ./.venv/bin/activate

## Function: execute Python-related commands within the project's environment
define execute_in_env
	$(ACTIVATE_ENV) && $1
endef

## Build the requirements shared with Lambda functions
shared-requirements:
	create-environment
	$(call execute_in_env, $(PIP) install -r .requirements.txt)

###############################################################################
# Set Up

## Install ruff
ruff:
	$(call execute_in_env, $(PIP) install ruff)

## Install coverage
coverage:
	$(call execute_in_env, $(PIP) install coverage)

## Install bandit
bandit:
	$(call execute_in_env, $(PIP) install bandit)

## Install pip-audit
pip-audit:
	$(call execute_in_env, $(PIP) install pip-audit)

## Install boto3
boto3:
	$(call execute_in_env, $(PIP) install boto3)

## Install moto
moto:
	$(call execute_in_env, $(PIP) install moto)

## Install pytest
pytest:
	$(call execute_in_env, $(PIP) install pytest)
	$(call execute_in_env, $(PIP) install pytest-cov)

## Set up dev requirements
dev-setup: ruff coverage bandit pip-audit moto pytest

###############################################################################
# Build / Run

## Run the security tests
security-tests:
	$(call execute_in_env, pip-audit -r requirements.txt)
	$(call execute_in_env, bandit -rlll ./src ./test)

## Run ruff linting and formatting
run-ruff:
	$(call execute_in_env, ruff check --fix ./src ./test)
	$(call execute_in_env, ruff format --check ./src ./test)

## Run bandit
run-bandit:
	$(call execute_in_env, bandit -rlll ./src ./test)

## Run Terraform validation and formatting
terraform-checks:
	$(call execute_in_env, terraform validate)
	$(call execute_in_env, terraform fmt ./infra)

## Run unit tests:
unit-tests:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} pytest -v test/)

## Check coverage
check-coverage:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} pytest --cov=src --cov-report term-missing test/)

## Run all checks
run-checks: security-tests run-ruff run-bandit terraform-checks unit-tests check-coverage
