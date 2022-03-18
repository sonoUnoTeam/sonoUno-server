# sonoUno server
The sonification-as-a-service platform.

## Intro

This app provides a basic account API on top of a [MongoDB]() store with the following features:

- Registration
- Email verification
- Password reset
- JWT auth login and refresh
- User and transform model CRUD

## Backend Requirements

* [Python 3.10](https://www.python.org/downloads/)
* [Docker](https://www.docker.com/).
* [Docker Compose](https://docs.docker.com/compose/install/).
* [Poetry](https://python-poetry.org/) for Python package and environment management.

## Frontend Requirements

* Node.js (with `npm`).

## Backend local development

* Start the stack with Docker Compose:

```bash
compose/run.sh
```

* Now you can open your browser and interact with these URLs:

Frontend, built with Docker, with routes handled based on the path: http://localhost

Backend, JSON based web API based on OpenAPI: http://localhost:8001/api/

Automatic interactive documentation with Swagger UI (from the OpenAPI backend): http://localhost:8001/docs

Alternative automatic documentation with ReDoc (from the OpenAPI backend): http://localhost:8001/redoc

mongo-express, MongoDB web administration: http://localhost:8081

## General workflow

The dependencies are managed with [Poetry](https://python-poetry.org/), go there and install it.

From `./backend/` you can install all the dependencies with:

```console
$ poetry install
```

Then you can start a shell session with the new environment with:

```console
$ poetry shell
```

## Secret salt generation

For new environment a salt should be generated and kept secret. To do that, just run the script:

```bash
backend/scripts/gen_salt.py
```

There are other settings in `config.py` and the included `.env` file. Assuming you've changed the SALT value, everything should run as-is if there is a local [MongoDB]() instance running ([see below](#test) for a Docker solution). Any email links will be printed to the console by default.

## Tests

To run the test suite:

```bash
compose/run-tests-backend.sh
```

[MongoDB]: https://www.mongodb.com "MongoDB NoSQL homepage"
[FastAPI]: https://fastapi.tiangolo.com "FastAPI web framework"
[Beanie ODM]: https://roman-right.github.io/beanie/ "Beanie object-document mapper"
[Starlette]: https://www.starlette.io "Starlette web framework"
[PyDantic]: https://pydantic-docs.helpmanual.io "PyDantic model validation"
[fastapi-jwt-auth]: https://github.com/IndominusByte/fastapi-jwt-auth "JWT auth for FastAPI"
[fastapi-mail]: https://github.com/sabuhish/fastapi-mail "FastAPI mail server"
[uvicorn]: https://www.uvicorn.org "Uvicorn ASGI web server"