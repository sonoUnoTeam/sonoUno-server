#! /usr/bin/env sh
set -ex

export SONOUNO_PATH=$(dirname "$(readlink -f "$0")")

cd ${SONOUNO_PATH}/../backend
poetry build
poetry export --no-plugins > requirements.txt
echo "sonouno_server=="$(poetry version --short) > requirements-package.txt
cd -

docker-compose -f ${SONOUNO_PATH}/docker-compose.yml --env-file ${SONOUNO_PATH}/.env config > ${SONOUNO_PATH}/docker-stack.yml
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml build
