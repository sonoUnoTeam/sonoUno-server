#! /usr/bin/env sh
# This script should only be run for the CI or local development

export SONOUNO_PATH=$(dirname "$(readlink -f "$0")")
INSTALL_DEV=true ${SONOUNO_PATH}/build.sh
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml -f ${SONOUNO_PATH}/docker-compose-test.yml up -d
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml exec -T sonouno-server bash /code/scripts/run-tests.sh "$@"
${SONOUNO_PATH}/rm.sh
