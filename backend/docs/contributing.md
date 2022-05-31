The sonoUno library uses [pre-commit](https://pre-commit.com) to ensure code quality and uniformity.
To install the pre-commit hooks:

```bash
$ pip install --user pre-commit
$ cd sonouno-server
$ pre-commit install
```

The project also uses [poetry](https://python-poetry.org) to manage its package dependencies.
To install poetry and a versioning plugin:
```bash
$ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python
$ ${XDG_DATA_HOME:-~/.local/share}/pypoetry/venv/bin/pip install poetry-dynamic-versioning
```

To install the project and its development dependencies:
```bash
$ cd backend
$ poetry install
```

To run the project (inside the backend directory):
```bash
$ ../compose/run-dev.sh
```
In case of failure, check that on linux, the apache2 service is stopped:
```bash
$ sudo service apache2 stop
```

To run the test suite and activate the debugger in case of error:
```bash
$ ../compose/run-tests-backend.sh --pdb
```
