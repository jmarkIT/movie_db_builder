import time
from typing import Any, Protocol, Callable

import httpx


class RequestHandler(Protocol):
    def handle(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response: ...


class HTTPExecutor:
    def handle(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        response: httpx.Response = httpx.request(
            method=method, url=url, headers=headers, params=params, json=json
        )
        response.raise_for_status()
        return response


class RateLimiter:
    def __init__(self, handler: RequestHandler, requests_per_second: float):
        self.handler: RequestHandler = handler
        self.min_interval: int | float = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def handle(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        self.last_request_time = time.time()
        return self.handler.handle(method, url, headers, params, json)


class RetryHandler:
    def __init__(
        self,
        handler: RequestHandler,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        retry_statuses: set[int] | None = None,
    ):
        self.handler = handler
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_statuses = retry_statuses or {429, 500, 502, 503, 504}

    def handle(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        last_exception: httpx.HTTPStatusError | httpx.RequestError = httpx.RequestError(
            "Max retries exceeded"
        )

        for attempt in range(self.max_retries + 1):
            try:
                response = self.handler.handle(method, url, headers, params, json)
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code not in self.retry_statuses:
                    raise
                last_exception = e

                if attempt < self.max_retries:
                    wait_time = self.backoff_factor * (2**attempt)
                    time.sleep(wait_time)
            except httpx.RequestError as e:
                last_exception = e

                if attempt < self.max_retries:
                    wait_time = self.backoff_factor * (2**attempt)
                    time.sleep(wait_time)

        raise last_exception


class AuthProvider:
    def __init__(
        self, handler: RequestHandler, get_auth_headers: Callable[[], dict[str, str]]
    ):
        self.handler = handler
        self.get_auth_headers = get_auth_headers

    def handle(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        merged_headers = {**headers, **self.get_auth_headers()}
        return self.handler.handle(method, url, merged_headers, params, json)


class HTTPClient:
    def __init__(self, base_url: str, handler: RequestHandler):
        self.base_url = base_url.rstrip("/")
        self.handler = handler

    def request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = headers or {"Content-Type": "application/json"}

        return self.handler.handle(
            method=method, url=url, headers=headers, params=params, json=json
        )

    def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        return self.request(endpoint, method="GET", params=params)

    def post(self, endpoint: str, json: dict[str, Any] | None = None) -> httpx.Response:
        return self.request(endpoint=endpoint, method="POST", json=json)
