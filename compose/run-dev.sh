#! /usr/bin/env sh
# This script should only be used for local development.
# For the development, staging and production environments, the SALT must be a secret.

set -ex

export SONOUNO_PATH=$(dirname "$(readlink -f "$0")")
${SONOUNO_PATH}/build-dev.sh
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml up "$@"
