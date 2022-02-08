#! /usr/bin/env bash
set -ex

poetry run python gen_salt.py
poetry run pytest --cov=app --cov-report=term-missing "${@}"
