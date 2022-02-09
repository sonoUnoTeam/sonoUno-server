#! /usr/bin/env sh
# This script should only be used for local development.
# For the development, staging and production environments, the SALT must be a secret.

# Exit in case of error
set -e

export SONOUNO_PATH=$(dirname "$(readlink -f "$0")")
export SALT='$2b$12$Sft/hbpkZnDMTQIkDLyH1.'
INSTALL_DEV=true ${SONOUNO_PATH}/build.sh
docker-compose -f ${SONOUNO_PATH}/docker-stack.yml up "$@"
