The sonoUno server APIs are described using [OpenAPI v3.1](https://www.openapis.org).
They can be consulted at the url [http://api.sonouno.org.ar/redoc](http://api.sonouno.org.ar/redoc).

To see an example showing how these APIs can be used, a dockerized [Jupyter notebook](https://gitlab.com/pchanial/sonouno-server/-/blob/main/backend/demo/demo_client.ipynb) has been made available. It uses the production server APIs to login a test user, to create a transform, to execute a job and to play the resulting audio file.

```bash
$ docker run --network host --rm pchanial/sonouno-server-demo
```

The technical stack is the following:

- Docker compose for the container orchestration
- FastAPI for the Python 3.10 web application
- MongoDB for the user, transform and job database
- MinIO, an S3-compatible object store, to serve the sonification outputs
- Nginx to serve the application
