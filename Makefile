.PHONY: clean
SHELL := /bin/bash

PACKAGE_NAME := rosreestr2coord
#PYPI_REPO := some_url
#PYPI_USER := some_user
#PYPI_PASSWORD := some_pwd

# Run cleanup of tmp files
clean:
	find . -name ".pytest_cache" -exec rm -rf "{}" +
	find . -name \*.log -delete
	find . -name \*.coverage -delete
	rm -rf *.gz
	rm -rf .mypy_cache
	rm -rf .tox
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

# creates virtual environment and install dependencies
setup:
	poetry run pip install -U pip
#	poetry install --no-dev
	poetry install -v

# usual unit-tests with coverage
unit-tests:
	poetry run pytest --cov=$(PACKAGE_NAME) -o log_cli=true --log-cli-level=INFO tests/

# run tests against all supported python versions
tox-tests:
	poetry run tox

type-checking:
	poetry run mypy --config-file pyproject.toml $(PACKAGE_NAME)/*.py tests/

pep-checking:
	poetry run flake8 --format='%(path)s:%(row)d:%(col)d: %(text)s' $(PACKAGE_NAME)
