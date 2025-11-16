import httpx

from movie_db_builder.tmdb.models import TMDBMovie, TMDBGenresQuery, TMDBGenre
from movie_db_builder.tmdb.tmdb_config import TMDBConfig


class TMDBClient:
    def __init__(self, config: TMDBConfig):
        self.config = config

    def perform_request(
        self, endpoint: str, method: str = "GET", params=None, data=None
    ) -> httpx.Response | None:
        headers = {
            "Authorization": f"Bearer {self.config.api_token}",
            "Content-Type": "application/json",
        }

        url = f"{self.config.api_base_url}/{endpoint}"
        match method:
            case "GET":
                return httpx.get(url, headers=headers, params=params)
            case _:
                return None

    def get_movie_details(
        self, movie_id: str, append_to_response: list[str] | None = None
    ) -> TMDBMovie | None:
        movie_endpoint = f"/movie/{movie_id}"
        r = self.perform_request(
            endpoint=movie_endpoint,
            method="GET",
            params={"append_to_response": append_to_response},
            data=None,
        )
        return TMDBMovie(**r.json())

    def get_genres(self) -> list[TMDBGenre]:
        r = self.perform_request(endpoint="/genre/movie/list", method="GET")
        genres_query = TMDBGenresQuery(**r.json())
        return genres_query.genres
