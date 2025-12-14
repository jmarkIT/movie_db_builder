import time

import httpx

from movie_db_builder.notion.models import (
    NotionDatabaseQueryResponse,
    NotionPage,
)
from movie_db_builder.notion.notion_config import NotionConfig


class NotionClient:
    def __init__(self, config: NotionConfig) -> None:
        self.config = config
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self.max_retries = 3
        self.backoff_factor = 0.5
        self.client = httpx.Client(timeout=self.timeout)

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

        for attempt in range(1, self.max_retries + 1):
            try:
                match method:
                    case "GET":
                        response = httpx.get(url, headers=headers, params=params)
                    case "POST":
                        response = httpx.post(
                            url, headers=headers, params=params, json=data
                        )
                    case _:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response

            except httpx.TimeoutException:
                if attempt == self.max_retries:
                    raise RuntimeError(
                        f"Request to {url} timed out after {self.max_retries} attempts"
                    )
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                # Retry on transiet errors and rate limiting
                if (
                    status not in (429, 500, 502, 503, 504)
                    or attempt == self.max_retries
                ):
                    raise RuntimeError(
                        f"Notion API error {status} for {url}: {e.response.text}"
                    ) from e
            except httpx.RequestError as e:
                if attempt == self.max_retries:
                    raise RuntimeError(f"Network error while requesting {url}") from e

            time.sleep(self.backoff_factor * (2 ** (attempt - 1)))

        return None

    def get_page(self, page_id: str) -> NotionPage:
        r: httpx.Response | None = self.perform_request(
            endpoint=f"pages/{page_id}", method="GET", params=None
        )

        if r is None:
            raise RuntimeError(f"Notion API returned no response for page {page_id}")

        data = r.json()

        try:
            page = NotionPage(**data)
        except TypeError as e:
            raise TypeError(
                f"NotionPage parsing failed. API response was: {data}"
            ) from e

        return page

    def get_datasource_rows(self, data_source_id: str) -> list[NotionPage]:
        datasource_rows: list[NotionPage] = []
        r: httpx.Response | None = self.perform_request(
            endpoint=f"data_sources/{data_source_id}/query", method="POST", params=None
        )

        if r is None:
            raise RuntimeError(
                f"Notion API returned no response for datasource query {data_source_id}"
            )
        data = r.json()

        try:
            query_results = NotionDatabaseQueryResponse(**data)
        except TypeError:
            raise TypeError(
                f"NotionDataBaseQueryResponse parsing failed. API response was: {data}"
            )

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

            if r is None:
                raise RuntimeError(
                    f"Notion API returned no response for datasource query {data_source_id}"
                )
            data = r.json()

            try:
                query_results = NotionDatabaseQueryResponse(**data)
            except TypeError:
                raise TypeError(
                    f"NotionDataBaseQueryResponse parsing failed. API response was: {data}"
                )

            datasource_rows.extend(query_results.results)

        return datasource_rows

        def close(self) -> None:
            self.client.close()
