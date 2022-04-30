#! /usr/bin/env sh
# This script should only be run for the CI or local development

set -ex

export SONOUNO_PATH=$(dirname "$(readlink -f "$0")")
${SONOUNO_PATH}/build-dev.sh
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml -f ${SONOUNO_PATH}/docker-compose-test.yml up -d
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml exec -T sonouno-server bash /code/scripts/run-tests.sh "$@"
${SONOUNO_PATH}/rm.sh
