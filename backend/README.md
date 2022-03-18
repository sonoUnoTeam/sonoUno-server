# sonoUno server
The backend that provides sonification-as-a-service.

## Intro

This app provides a basic account API on top of a [MongoDB]() store with the following features:

- Registration
- Email verification
- Password reset
- JWT auth login and refresh
- User and transform model CRUD

It's built on top of these libraries to provide those features:

- [FastAPI]() - Python async micro framework built on [Starlette]() and [PyDantic]()
- [Beanie ODM]() - Async [MongoDB]() object-document mapper built on [PyDantic]()
- [fastapi-jwt-auth]() - JWT auth for [FastAPI]()
- [fastapi-mail]() - Mail server manager for [FastAPI]()

## Setup

The sonoUno server codebase is written for Python 3.10 and above.

First we'll need to install our requirements.

```bash
poetry install
```

Before we run the server, there is one config variable you'll need to generate the password salt. To do this, just run the script in this repo.

```bash
python gen_salt.py
```

There are other settings in `config.py` and the included `.env` file. Assuming you've changed the SALT value, everything should run as-is if there is a local [MongoDB]() instance running ([see below](#test) for a Docker solution). Any email links will be printed to the console by default.

## Run

This sample uses [uvicorn]() as our ASGI web server. This allows us to run our server code in a much more robust and configurable environment than the development server. For example, ASGI servers let you run multiple workers that recycle themselves after a set amount of time or number of requests.

```bash
poetry run uvicorn sonouno_server.main:app --reload --port 8080
```

The sonoUno server API should now be available at http://localhost:8080

## Test

The sample app also comes with a test suite to get you started.
In order to run them, the tests need access to a [MongoDB]() store that is emptied at the end of each test. The easiest way to do this is to run a Mongo container in the background.

```bash
docker run -d --net host mongo
```
To run the test suite:
```bash
poetry run pytest
```

[MongoDB]: https://www.mongodb.com "MongoDB NoSQL homepage"
[FastAPI]: https://fastapi.tiangolo.com "FastAPI web framework"
[Beanie ODM]: https://roman-right.github.io/beanie/ "Beanie object-document mapper"
[Starlette]: https://www.starlette.io "Starlette web framework"
[PyDantic]: https://pydantic-docs.helpmanual.io "PyDantic model validation"
[fastapi-jwt-auth]: https://github.com/IndominusByte/fastapi-jwt-auth "JWT auth for FastAPI"
[fastapi-mail]: https://github.com/sabuhish/fastapi-mail "FastAPI mail server"
[uvicorn]: https://www.uvicorn.org "Uvicorn ASGI web server"