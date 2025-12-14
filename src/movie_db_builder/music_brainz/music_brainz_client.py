import asyncio
import time

import httpx

from movie_db_builder.music_brainz.models import MusicBrainzRelease
from movie_db_builder.music_brainz.music_brainz_config import MusicBrainzConfig


class MusicBrainzClient:
    def __init__(self, cfg: MusicBrainzConfig):
        self._client = httpx.AsyncClient(
            base_url=cfg.BASE_URL,
            headers={
                "User-Agent": cfg.user_agent,
                "Accept": "application/json",
            },
            timeout=10.0,
        )
        self._lock = asyncio.Lock()
        self._last_request = 0.0
        self.rate_limit = cfg.rate_limit

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()

    async def _rate_limit(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - elapsed)
            self._last_request = time.monotonic()

    async def perform(
        self,
        endpoint: str,
        params: dict | None = None,
        method: str = "GET",
        json: dict | None = None,
    ):
        await self._rate_limit()

        response = await self._client.request(
            method=method,
            url=endpoint,
            params=params,
            json=json,
        )
        response.raise_for_status()
        return response.json()

    async def get_release(self, release_id: str):
        r: httpx.Response | None = await self.perform(
            endpoint=f"/release/{release_id}", params={"inc": "genres"}
        )

        if r is None:
            raise RuntimeError(
                f"MusicBrainz returned no response for release {release_id}"
            )

        data = r.json()

        try:
            release = MusicBrainzRelease(**data)
        except TypeError as e:
            raise TypeError(
                f"MusicBrainzRelease parsing failed. API response was: {data}"
            ) from e

        return release

    async def close(self):
        await self._client.aclose()
