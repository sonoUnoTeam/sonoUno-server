# Pull base image
FROM python:3.10-slim

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN adduser --disabled-password --gecos '' sonounoclient


WORKDIR /notebooks/

# Add Python dependencies
RUN pip install --upgrade pip
RUN pip install --root-user-action=ignore requests jupyterlab
RUN pip install --root-user-action=ignore sonounolib==0.5.1

# copy application files
COPY demo_client.ipynb shortwav.py ./

USER sonounoclient

ENTRYPOINT ["jupyter", "lab"]
