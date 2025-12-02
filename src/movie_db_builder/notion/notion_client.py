import httpx

from movie_db_builder.notion.models import (
    NotionDatabaseQueryResponse,
    NotionPage,
)
from movie_db_builder.notion.notion_config import NotionConfig


class NotionClient:
    def __init__(self, config: NotionConfig) -> None:
        self.config = config

    def perform_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict | None = None,
        data: dict | None = None,
    ) -> httpx.Response | None:
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.config.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.config.API_VERSION,
        }

        url: str = f"{self.config.API_BASE_URL}/{endpoint}"
        match method:
            case "GET":
                return httpx.get(url, headers=headers, params=params)
            case "POST":
                return httpx.post(url, headers=headers, params=params, json=data)
            case _:
                return None

    def get_page(self, page_id: str) -> NotionPage:
        r: httpx.Response | None = self.perform_request(
            endpoint=f"pages/{page_id}", method="GET", params=None
        )
        return NotionPage(**r.json())

    def get_datasource_rows(self, data_source_id: str) -> list[NotionPage]:
        datasource_rows: list[NotionPage] = []
        r: httpx.Response | None = self.perform_request(
            endpoint=f"data_sources/{data_source_id}/query", method="POST", params=None
        )
        query_results = NotionDatabaseQueryResponse(**r.json())
        datasource_rows.extend(query_results.results)
        while query_results.has_more:
            # body = NotionDatabaseQueryBody(start_cursor=query_results.next_cursor)
            body = {"start_cursor": query_results.next_cursor}
            r = self.perform_request(
                f"data_sources/{data_source_id}/query",
                method="POST",
                params=None,
                data=body,
            )

            query_results = NotionDatabaseQueryResponse(**r.json())

            datasource_rows.extend(query_results.results)

        return datasource_rows
