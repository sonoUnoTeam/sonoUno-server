#! /usr/bin/env bash

# Exit in case of error
set -e

export SONOUNO_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml down -v --remove-orphans
