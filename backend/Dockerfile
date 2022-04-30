# Pull base image
FROM python:3.10-slim

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code/

RUN pip install fastapi-mail==1.0.2

COPY requirements.txt .
RUN pip install -r requirements.txt

# Make some libraries available in the transform interpretor.
# This is a temporary solution, code execution should be performed in a container,
# not in the server's process.
RUN pip install requests pandas astropy


COPY requirements-package.txt .
COPY dist dist

RUN pip install --no-index --find-links dist -r requirements-package.txt

COPY scripts scripts
