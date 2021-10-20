from dataclasses import dataclass
import datetime
from typing import Any, Dict

from .generator import HydraTokenGen, Token


class CachedTokenGen:
    def __init__(self, generator: HydraTokenGen):
        self._generator = generator

        self._cache: Dict[str, _CacheEntry] = {}

        # subtract 5 minutes from the token expiration to reduce clock drift
        # problems
        self.clock_drift_seconds: int = 300

    def generate(
        self,
        subject: str,
        access_token: Dict[str, Any],
        id_token: Dict[str, Any],
    ):
        cache_key = str((subject, access_token, id_token))

        if cache_key in self._cache:
            entry = self._cache[cache_key]

            if entry.expiration > self._now():
                return entry.token

        token = self._generator.generate(subject, access_token, id_token)

        expiration = self._now() + datetime.timedelta(
            seconds=int(token["expires_in"]) - self.clock_drift_seconds
        )

        self._cache[cache_key] = _CacheEntry(token=token, expiration=expiration)

        return token

    def _now(self):
        return datetime.datetime.now()


@dataclass
class _CacheEntry:
    token: Token
    expiration: datetime.datetime
