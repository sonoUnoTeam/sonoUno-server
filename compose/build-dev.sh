#! /usr/bin/env sh

# Exit in case of error
set -e

export SONOUNO_PATH=$(dirname "$(readlink -f "$0")")
if [ -x "$(command -v poetry)" ]; then
  cd ${SONOUNO_PATH}/../backend
  echo "__version__ = '$(poetry version --short)'" > sonouno_server/_version.py
  cd -
fi
ARGS="-f ${SONOUNO_PATH}/docker-compose.yml -f ${SONOUNO_PATH}/docker-compose-dev.yml"

docker-compose $ARGS --env-file ${SONOUNO_PATH}/.env config > ${SONOUNO_PATH}/docker-stack.yml

docker-compose -f ${SONOUNO_PATH}/docker-stack.yml build
