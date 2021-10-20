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
docker run --rm \
  -e SECRETS_SYSTEM=youReallyNeedToChangeThis \
  -e DSN=sqlite:///tmp/db.sqlite?_fk=true \
  -e URLS_SELF_ISSUER=http://127.0.0.1:4444 \
  -e URLS_CONSENT=http://placeholder/consent \
  -e URLS_LOGIN=http://placeholder/login \
  -e URLS_POST_LOGOUT_REDIRECT=http://placeholder/logout \
  -e STRATEGIES_ACCESS_TOKEN=jwt \
  -p 4444:4444 \
  -p 4445:4445 \
  --name "hydratokengentest" \
  --entrypoint "" \
  oryd/hydra:v1.10.6-sqlite \
  sh -c 'hydra migrate sql -e --yes && hydra serve all --dangerous-force-http'
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
