#! /usr/bin/env bash

# Exit in case of error
set -e

export SONOUNO_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
${SONOUNO_PATH}/run.sh -d
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml exec -T sonouno-server bash /code/scripts/run-tests.sh "$@"
${SONOUNO_PATH}/rm.sh
