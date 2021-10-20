import jwt
import ory_hydra_client
import pytest
from ory_hydra_client.api import admin_api
from ory_hydra_client.model.o_auth2_client import OAuth2Client
from ory_hydra_client.model.string_slice_pipe_delimiter import StringSlicePipeDelimiter

from hydratokengen import HydraTokenGen, TokenGenerateException


@pytest.fixture(scope="session")
def hydra_admin_api_instance():
    admin_configuration = ory_hydra_client.Configuration(host="http://localhost:4445")
    admin_client = ory_hydra_client.ApiClient(admin_configuration)
    return admin_api.AdminApi(admin_client)


@pytest.fixture(scope="session")
def hydra_client_factory(hydra_admin_api_instance):
    def factory(token_endpoint_auth_method="client_secret_basic"):
        body = OAuth2Client(
            name="test",
            grant_types=StringSlicePipeDelimiter(
                ["authorization_code", "refresh_token"]
            ),
            response_types=StringSlicePipeDelimiter(["code", "id_token"]),
            scope="openid offline",
            redirect_uris=StringSlicePipeDelimiter(["http://localhost/callback"]),
            contacts=StringSlicePipeDelimiter([]),
            token_endpoint_auth_method=token_endpoint_auth_method,
        )

        return hydra_admin_api_instance.create_o_auth2_client(body)

    return factory


def test_generate(hydra_client_factory):
    hydra_client = hydra_client_factory()

    generator = HydraTokenGen(
        hydra_public_url="http://localhost:4444",
        hydra_admin_url="http://localhost:4445",
        client_id=hydra_client["client_id"],
        client_secret=hydra_client["client_secret"],
        redirect_uri=hydra_client["redirect_uris"].value[0],
    )

    token = generator.generate(
        subject="1234",
        access_token={"claim1": "value1"},
        id_token={"claim2": "value2"},
    )

    assert token.get("access_token")
    assert token.get("id_token")
    assert token.get("expires_in")
    assert not token.get("refresh_token")

    access_token = jwt.decode(
        token["access_token"], options={"verify_signature": False}
    )
    assert access_token["sub"] == "1234"
    assert access_token["ext"]["claim1"] == "value1"

    id_token = jwt.decode(token["id_token"], options={"verify_signature": False})
    assert id_token["sub"] == "1234"
    assert id_token["claim2"] == "value2"


def test_generate_offline_scope(hydra_client_factory):
    hydra_client = hydra_client_factory()

    generator = HydraTokenGen(
        hydra_public_url="http://localhost:4444",
        hydra_admin_url="http://localhost:4445",
        client_id=hydra_client["client_id"],
        client_secret=hydra_client["client_secret"],
        redirect_uri=hydra_client["redirect_uris"].value[0],
        scope="openid offline",
    )

    token = generator.generate(
        subject="1234",
        access_token={"claim1": "value1"},
        id_token={"claim2": "value2"},
    )

    assert token.get("access_token")
    assert token.get("id_token")
    assert token.get("expires_in")
    assert token.get("refresh_token")


def test_generate_client_secret_post(hydra_client_factory):
    hydra_client = hydra_client_factory(token_endpoint_auth_method="client_secret_post")

    generator = HydraTokenGen(
        hydra_public_url="http://localhost:4444",
        hydra_admin_url="http://localhost:4445",
        client_id=hydra_client["client_id"],
        client_secret=hydra_client["client_secret"],
        redirect_uri=hydra_client["redirect_uris"].value[0],
        token_endpoint_auth_method="client_secret_post",
    )

    generator.generate(
        subject="1234",
        access_token={"claim1": "value1"},
        id_token={"claim2": "value2"},
    )


def test_generate_invalid_client_id(hydra_client_factory):
    hydra_client = hydra_client_factory()

    generator = HydraTokenGen(
        hydra_public_url="http://localhost:4444",
        hydra_admin_url="http://localhost:4445",
        client_id="invalid",
        client_secret=hydra_client["client_secret"],
        redirect_uri=hydra_client["redirect_uris"].value[0],
    )

    with pytest.raises(TokenGenerateException):
        generator.generate(
            subject="1234",
            access_token={"claim1": "value1"},
            id_token={"claim2": "value2"},
        )


def test_generate_invalid_public_url(hydra_client_factory):
    hydra_client = hydra_client_factory()

    generator = HydraTokenGen(
        hydra_public_url="http://localhost:4445",
        hydra_admin_url="http://localhost:4445",
        client_id=hydra_client["client_id"],
        client_secret=hydra_client["client_secret"],
        redirect_uri=hydra_client["redirect_uris"].value[0],
    )

    with pytest.raises(TokenGenerateException):
        generator.generate(
            subject="1234",
            access_token={"claim1": "value1"},
            id_token={"claim2": "value2"},
        )
