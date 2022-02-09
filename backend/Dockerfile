# Pull base image
FROM python:3.10-slim

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code/

# Install Poetry
RUN apt-get update && apt-get install -y curl
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python \
 && cd /usr/local/bin \
 && ln -s /opt/poetry/bin/poetry \
 && poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /code/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ \"${INSTALL_DEV}\" == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"
RUN bash -c "poetry run pip install fastapi-mail==1.0.2"

# For development, Jupyter remote kernel, Hydrogen
# Using inside the container:
# jupyter lab --ip=0.0.0.0 --allow-root --NotebookApp.custom_display_url=http://127.0.0.1:8888
ARG INSTALL_JUPYTER=false
RUN bash -c "if [ \"${INSTALL_JUPYTER}\" == 'true' ] ; then pip install jupyterlab ; fi"

COPY . /code

ENV PYTHONPATH=/code
