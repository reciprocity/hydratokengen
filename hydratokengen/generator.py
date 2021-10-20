from typing import Any, Dict, List
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import ory_hydra_client
import requests
from ory_hydra_client.api import admin_api
from ory_hydra_client.model.accept_consent_request import AcceptConsentRequest
from ory_hydra_client.model.accept_login_request import AcceptLoginRequest
from ory_hydra_client.model.consent_request import ConsentRequest
from ory_hydra_client.model.consent_request_session import ConsentRequestSession

from .exceptions import TokenGenerateException

Token = Dict[str, Any]


class HydraTokenGen:
    def __init__(
        self,
        hydra_public_url: str,
        hydra_admin_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: str = "openid",
        token_endpoint_auth_method: str = "client_secret_basic",  # or "client_secret_post"
    ):
        self._hydra_public_url = hydra_public_url
        self._hydra_admin_url = hydra_admin_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._scope = scope
        self._token_endpoint_auth_method = token_endpoint_auth_method

        self._admin_configuration = ory_hydra_client.Configuration(host=hydra_admin_url)
        self._admin_client = ory_hydra_client.ApiClient(self._admin_configuration)
        self._admin_api_instance = admin_api.AdminApi(self._admin_client)

        self._hydra_public_url_parsed = urlparse(self._hydra_public_url)
        self._auth_url = f"{self._hydra_public_url}/oauth2/auth"
        self._token_url = f"{self._hydra_public_url}/oauth2/token"

        self._public_session = requests.Session()
        self._token_session = requests.Session()

    def generate(
        self,
        subject: str,
        access_token: Dict[str, Any],
        id_token: Dict[str, Any],
    ) -> Token:
        try:
            login_challenge = self._start_flow()

            redirect = self._accept_login_request(login_challenge, subject)

            consent_challenge = self._get_consent_challenge(redirect)

            consent_request = self._validate_consent_request(consent_challenge)

            redirect = self._accept_consent_request(
                consent_challenge, access_token, id_token, consent_request
            )

            code = self._get_code(redirect)

            token = self._exchange_code(code)

            return token
        except Exception as exc:
            raise TokenGenerateException(f"Failed to generate Hydra token") from exc

    def _start_flow(self) -> str:
        auth_code_url_query = urlencode(
            {
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "response_type": "code",
                "scope": self._scope,
                "state": "hydratokengen",
            }
        )
        auth_code_url = f"{self._auth_url}?{auth_code_url_query}"

        location_query = self._get_oauth2_flow_query(auth_code_url)

        login_challenge = location_query["login_challenge"][0]

        return login_challenge

    def _accept_login_request(self, login_challenge: str, subject: str) -> str:
        body = AcceptLoginRequest(subject=subject)

        api_response = self._admin_api_instance.accept_login_request(
            login_challenge, body=body
        )

        return api_response["redirect_to"]

    def _get_consent_challenge(self, auth_code_url: str) -> str:
        auth_code_url = urlunparse(
            self._hydra_public_url_parsed[:2] + urlparse(auth_code_url)[2:]
        )

        location_query = self._get_oauth2_flow_query(auth_code_url)

        consent_challenge = location_query["consent_challenge"][0]

        return consent_challenge

    def _validate_consent_request(self, consent_challenge: str) -> ConsentRequest:
        return self._admin_api_instance.get_consent_request(consent_challenge)

    def _accept_consent_request(
        self,
        consent_challenge: str,
        access_token: Dict[str, Any],
        id_token: Dict[str, Any],
        consent_request: ConsentRequest,
    ) -> str:
        body = AcceptConsentRequest(
            grant_access_token_audience=consent_request[
                "requested_access_token_audience"
            ],
            grant_scope=consent_request["requested_scope"],
            session=ConsentRequestSession(access_token=access_token, id_token=id_token),
        )

        api_response = self._admin_api_instance.accept_consent_request(
            consent_challenge, body=body
        )

        return api_response["redirect_to"]

    def _get_code(self, auth_code_url: str) -> str:
        auth_code_url = urlunparse(
            self._hydra_public_url_parsed[:2] + urlparse(auth_code_url)[2:]
        )

        location_query = self._get_oauth2_flow_query(auth_code_url)

        code = location_query["code"][0]

        return code

    def _exchange_code(self, code: str) -> Dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "redirect_uri": self._redirect_uri,
            "code": code,
        }

        if self._token_endpoint_auth_method == "client_secret_basic":
            auth = (self._client_id, self._client_secret)
        elif self._token_endpoint_auth_method == "client_secret_post":
            auth = None
            data["client_id"] = self._client_id
            data["client_secret"] = self._client_secret
        else:
            raise ValueError(
                f"Invalid token_endpoint_auth_method: {self._token_endpoint_auth_method}"
            )

        res = self._token_session.post(self._token_url, data=data, auth=auth)

        res.raise_for_status()

        return res.json()

    def _get_oauth2_flow_query(self, auth_code_url: str) -> Dict[str, List[str]]:
        res = self._public_session.get(auth_code_url, allow_redirects=False)

        if res.status_code != 302:
            raise requests.HTTPError(
                f"Expected status to be 302 but got: {res.status_code}", res
            )

        location = res.headers["Location"]
        if not location:
            raise KeyError("Missing Location header in response")

        query = parse_qs(urlparse(location).query)

        if query.get("error"):
            error = query["error"][0]
            if query.get("error_description"):
                error_description = query["error_description"][0]
                error = f"{error}: {error_description}"
            raise Exception(f"OAuth 2 flow start error: {error}")

        return query
