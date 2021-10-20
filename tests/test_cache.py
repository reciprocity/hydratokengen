import mock
import time

from hydratokengen import CachedTokenGen


def test_generate():
    mock_token = {"access_token": "ACCESSTOKEN", "expires_in": 301}
    generator = mock.Mock()
    generator.generate = mock.Mock(side_effect=lambda *args, **kwargs: mock_token)
    cache = CachedTokenGen(generator)

    token = cache.generate(
        subject="1234",
        access_token={"claim1": "value1"},
        id_token={"claim2": "value2"},
    )
    assert token.get("access_token")

    assert generator.generate.call_count == 1

    token = cache.generate(
        subject="1234",
        access_token={"claim1": "value1"},
        id_token={"claim2": "value2"},
    )
    assert token.get("access_token")

    assert generator.generate.call_count == 1

    time.sleep(1.5)

    token = cache.generate(
        subject="1234",
        access_token={"claim1": "value1"},
        id_token={"claim2": "value2"},
    )

    assert generator.generate.call_count == 2


def test_generate_different_args():
    mock_token1 = {"access_token": "ACCESSTOKEN1", "expires_in": 3600}
    mock_token2 = {"access_token": "ACCESSTOKEN2", "expires_in": 3600}

    generator = mock.Mock()

    def generate(subject, id_token, access_token):
        if subject == "1":
            return mock_token1
        return mock_token2

    generator.generate = mock.Mock(side_effect=generate)

    cache = CachedTokenGen(generator)

    token = cache.generate(
        subject="1",
        access_token={"claim1": "value1"},
        id_token={"claim2": "value2"},
    )
    assert token["access_token"] == "ACCESSTOKEN1"

    token = cache.generate(
        subject="2",
        access_token={"claim1": "value1"},
        id_token={"claim2": "value2"},
    )
    assert token["access_token"] == "ACCESSTOKEN2"

    assert generator.generate.call_count == 2
