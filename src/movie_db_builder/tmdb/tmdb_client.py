import httpx

from movie_db_builder.tmdb.models import TMDBGenre, TMDBGenresQuery, TMDBMovie
from movie_db_builder.tmdb.tmdb_config import TMDBConfig


class TMDBClient:
    def __init__(self, config: TMDBConfig) -> None:
        self.config = config

    def perform_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict | None = None,
        data: dict | None = None,
    ) -> httpx.Response | None:
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.config.api_token}",
            "Content-Type": "application/json",
        }

        url: str = f"{self.config.api_base_url}/{endpoint}"
        match method:
            case "GET":
                return httpx.get(url, headers=headers, params=params)
            case "POST":
                return httpx.post(url, headers=headers, params=params, data=data)
            case _:
                return None

    def get_movie_details(
        self, movie_id: str, append_to_response: list[str] | None = None
    ) -> TMDBMovie | None:
        movie_endpoint: str = f"/movie/{movie_id}"
        r: httpx.Response | None = self.perform_request(
            endpoint=movie_endpoint,
            method="GET",
            params={"append_to_response": append_to_response},
            data=None,
        )

        if r is None:
            raise RuntimeError(f"TMDB API returned no response for {movie_id}")

        data = r.json()

        try:
            movie = TMDBMovie(**data)
        except TypeError as e:
            raise TypeError(
                f"TMDBMovie parsing failed, API response was: {data}"
            ) from e

        return movie

    def get_genres(self) -> list[TMDBGenre]:
        r: httpx.Response | None = self.perform_request(
            endpoint="/genre/movie/list", method="GET"
        )
        if r is None:
            raise RuntimeError("TMDB API resturned no response for genre list")

        data = r.json()

        try:
            genres_query = TMDBGenresQuery(**data)
        except TypeError as e:
            raise TypeError(
                f"TMDBGenresQuery parsing failed, API response was: {data}"
            ) from e

        return genres_query.genres
