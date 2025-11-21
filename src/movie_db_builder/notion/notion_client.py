import httpx

from movie_db_builder.notion.notion_config import NotionConfig


class NotionClient:
    def __init__(self, config: NotionConfig) -> None:
        self.config = config

    def perform_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict = None,
    ) -> httpx.Response | None:
        headers: dict[str:str] = {
            "Authorization": f"Bearer {self.config.notion_api_key}",
            "Content-Type": "application/json",
            "API-Version": self.config.API_VERSION,
        }

        url: str = f"{self.config.API_BASE_URL}/{endpoint}"
        match method:
            case "GET":
                return httpx.get(url, headers=headers, params=params)
            case _:
                return None
