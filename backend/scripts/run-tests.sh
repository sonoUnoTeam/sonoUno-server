#! /usr/bin/env bash
set -ex

poetry run pytest --cov=sonouno_server --cov-report=term-missing "${@}"
