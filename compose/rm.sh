#! /usr/bin/env sh

export SONOUNO_PATH=$(dirname "$(readlink -f "$0")")
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml down -v --remove-orphans
docker network prune --force