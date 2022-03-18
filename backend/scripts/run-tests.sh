#! /usr/bin/env bash
set -ex

TESTING=true poetry run pytest --cov=sonouno_server --cov-report=term-missing "${@}"
