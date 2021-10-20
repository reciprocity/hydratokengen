# HydraTokenGen

ORY Hydra JWT generator.

## Install

```sh
pip install hydratokengen
```

## Usage

```py
from hydratokengen import CachedTokenGen, HydraTokenGen

hydra_token_gen = CachedTokenGen(HydraTokenGen(
    hydra_public_url="http://localhost:4444",
    hydra_admin_url="http://localhost:4445",
    client_id="636986d6-f505-486a-839c-57bb6a881aca",
    client_secret="CLIENTSECRET",
    redirect_uri="http://localhost/callback",
))

token = hydra_token_gen.generate(
    subject="1234",
    access_token={"claim1": "value1"},
    id_token={"claim2": "value2"},
)
```

## Development

### Format code

```sh
poetry run black hydratokengen tests
```

### Testing

Start Hydra:

```sh
docker-compose up -d
```

Install dependencies:

```sh
poetry install
```

Run tests

```sh
poetry run pytest
```

HTML coverage report:

```sh
poetry run pytest --cov=hydratokengen --cov-report=html

open htmlcov/index.html
```

### Publish a new version

Bump the version number in `hydratokengen/__init__.py` and run:

```sh
poetry publish
```
