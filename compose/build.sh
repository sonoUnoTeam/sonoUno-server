#! /usr/bin/env bash

# Exit in case of error
set -e

export SONOUNO_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export INSTALL_DEV=${INSTALL_DEV:-false}

if [ $INSTALL_DEV = false ]
then
  INSTALL_DEV=
fi
ARGS="-f ${SONOUNO_PATH}/docker-compose.yml ${INSTALL_DEV:+-f ${SONOUNO_PATH}/docker-compose-dev.yml}"

DOMAIN=backend \
SMTP_HOST="" \
docker-compose $ARGS config > ${SONOUNO_PATH}/docker-stack.yml

docker-compose -f ${SONOUNO_PATH}/docker-stack.yml build
