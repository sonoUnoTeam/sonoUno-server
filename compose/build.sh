#! /usr/bin/env sh

# Exit in case of error
set -e

export SONOUNO_PATH=$(dirname "$(readlink -f "$0")")
: ${INSTALL_DEV:="false"}
if [ $INSTALL_DEV = false ]
then
  INSTALL_DEV=
fi
ARGS="-f ${SONOUNO_PATH}/docker-compose.yml ${INSTALL_DEV:+-f ${SONOUNO_PATH}/docker-compose-dev.yml}"

DOMAIN=backend \
docker-compose $ARGS config > ${SONOUNO_PATH}/docker-stack.yml

docker-compose -f ${SONOUNO_PATH}/docker-stack.yml build
