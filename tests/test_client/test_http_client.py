"""Tests for HTTP client chain of responsibility (src/movie_db_builder/client/client.py)."""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock

import httpx

import sys
sys.path.insert(0, "/home/user/movie_db_builder/src")

from movie_db_builder.client.client import (
    HTTPExecutor,
    RateLimiter,
    RetryHandler,
    AuthProvider,
    HTTPClient,
)


class TestHTTPExecutor:
    """Tests for HTTPExecutor class."""

    def test_executor_get_request(self, respx_mock):
        """Test executes GET with correct params."""
        respx_mock.get("https://api.example.com/test").mock(
            return_value=httpx.Response(200, json={"result": "ok"})
        )

        executor = HTTPExecutor()
        response = executor.handle(
            method="GET",
            url="https://api.example.com/test",
            headers={"Content-Type": "application/json"},
            params={"q": "search"},
        )

        assert response.status_code == 200
        assert response.json() == {"result": "ok"}

    def test_executor_post_request(self, respx_mock):
        """Test executes POST with JSON body."""
        respx_mock.post("https://api.example.com/create").mock(
            return_value=httpx.Response(201, json={"id": 1})
        )

        executor = HTTPExecutor()
        response = executor.handle(
            method="POST",
            url="https://api.example.com/create",
            headers={"Content-Type": "application/json"},
            json={"name": "test"},
        )

        assert response.status_code == 201

    def test_executor_raises_on_error(self, respx_mock):
        """Test raises HTTPStatusError for 4xx/5xx."""
        respx_mock.get("https://api.example.com/error").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        executor = HTTPExecutor()
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            executor.handle(
                method="GET",
                url="https://api.example.com/error",
                headers={},
            )

        assert exc_info.value.response.status_code == 404


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_first_request_no_delay(self):
        """Test first request is immediate."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        limiter = RateLimiter(mock_handler, requests_per_second=1.0)

        start = time.time()
        limiter.handle("GET", "https://api.example.com", {})
        elapsed = time.time() - start

        # First request should be nearly instant
        assert elapsed < 0.1

    def test_rate_limiter_enforces_delay(self):
        """Test subsequent requests wait."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        # 2 requests per second = 0.5s between requests
        limiter = RateLimiter(mock_handler, requests_per_second=2.0)

        # First request
        limiter.handle("GET", "https://api.example.com", {})

        # Second request should wait
        start = time.time()
        limiter.handle("GET", "https://api.example.com", {})
        elapsed = time.time() - start

        # Should have waited approximately 0.5s (allow some tolerance)
        assert elapsed >= 0.4

    def test_rate_limiter_custom_rate(self):
        """Test different requests_per_second."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        # 10 requests per second = 0.1s between requests
        limiter = RateLimiter(mock_handler, requests_per_second=10.0)

        assert limiter.min_interval == 0.1


class TestRetryHandler:
    """Tests for RetryHandler class."""

    def test_retry_success_first_attempt(self):
        """Test no retry on success."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        retry_handler = RetryHandler(mock_handler, max_retries=3)
        response = retry_handler.handle("GET", "https://api.example.com", {})

        assert response.status_code == 200
        assert mock_handler.handle.call_count == 1

    def test_retry_on_429(self):
        """Test retries rate limit errors."""
        mock_handler = Mock()
        # First call raises 429, second succeeds
        mock_handler.handle.side_effect = [
            httpx.HTTPStatusError(
                "Rate limited",
                request=Mock(),
                response=httpx.Response(429),
            ),
            httpx.Response(200),
        ]

        with patch("time.sleep"):  # Skip actual sleeping
            retry_handler = RetryHandler(mock_handler, max_retries=3)
            response = retry_handler.handle("GET", "https://api.example.com", {})

        assert response.status_code == 200
        assert mock_handler.handle.call_count == 2

    def test_retry_on_5xx(self):
        """Test retries server errors."""
        mock_handler = Mock()
        # First call raises 503, second succeeds
        mock_handler.handle.side_effect = [
            httpx.HTTPStatusError(
                "Service Unavailable",
                request=Mock(),
                response=httpx.Response(503),
            ),
            httpx.Response(200),
        ]

        with patch("time.sleep"):
            retry_handler = RetryHandler(mock_handler, max_retries=3)
            response = retry_handler.handle("GET", "https://api.example.com", {})

        assert response.status_code == 200

    def test_no_retry_on_4xx(self):
        """Test no retry for client errors (except 429)."""
        mock_handler = Mock()
        mock_handler.handle.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=httpx.Response(404),
        )

        retry_handler = RetryHandler(mock_handler, max_retries=3)

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            retry_handler.handle("GET", "https://api.example.com", {})

        assert exc_info.value.response.status_code == 404
        # Should only call once (no retry)
        assert mock_handler.handle.call_count == 1

    def test_retry_max_attempts_exceeded(self):
        """Test raises after max retries."""
        mock_handler = Mock()
        mock_handler.handle.side_effect = httpx.HTTPStatusError(
            "Rate limited",
            request=Mock(),
            response=httpx.Response(429),
        )

        with patch("time.sleep"):
            retry_handler = RetryHandler(mock_handler, max_retries=2)

            with pytest.raises(httpx.HTTPStatusError):
                retry_handler.handle("GET", "https://api.example.com", {})

        # Initial + 2 retries = 3 calls
        assert mock_handler.handle.call_count == 3

    def test_retry_exponential_backoff(self):
        """Test backoff timing verification."""
        mock_handler = Mock()
        mock_handler.handle.side_effect = httpx.HTTPStatusError(
            "Rate limited",
            request=Mock(),
            response=httpx.Response(429),
        )

        sleep_times = []

        def track_sleep(seconds):
            sleep_times.append(seconds)

        with patch("time.sleep", side_effect=track_sleep):
            retry_handler = RetryHandler(
                mock_handler, max_retries=3, backoff_factor=1.0
            )

            with pytest.raises(httpx.HTTPStatusError):
                retry_handler.handle("GET", "https://api.example.com", {})

        # backoff_factor * 2^attempt: 1*1=1, 1*2=2, 1*4=4
        assert sleep_times == [1.0, 2.0, 4.0]

    def test_retry_on_request_error(self):
        """Test retries on RequestError."""
        mock_handler = Mock()
        mock_handler.handle.side_effect = [
            httpx.RequestError("Connection failed"),
            httpx.Response(200),
        ]

        with patch("time.sleep"):
            retry_handler = RetryHandler(mock_handler, max_retries=3)
            response = retry_handler.handle("GET", "https://api.example.com", {})

        assert response.status_code == 200


class TestAuthProvider:
    """Tests for AuthProvider class."""

    def test_auth_provider_injects_headers(self):
        """Test adds auth headers."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        def get_auth():
            return {"Authorization": "Bearer token123"}

        auth_provider = AuthProvider(mock_handler, get_auth)
        auth_provider.handle("GET", "https://api.example.com", {})

        # Check the handler was called with merged headers
        call_args = mock_handler.handle.call_args
        headers = call_args[0][2]  # Third positional argument
        assert headers["Authorization"] == "Bearer token123"

    def test_auth_provider_merges_headers(self):
        """Test combines with existing headers."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        def get_auth():
            return {"Authorization": "Bearer token123"}

        auth_provider = AuthProvider(mock_handler, get_auth)
        auth_provider.handle(
            "GET",
            "https://api.example.com",
            {"Content-Type": "application/json"},
        )

        call_args = mock_handler.handle.call_args
        headers = call_args[0][2]
        assert headers["Authorization"] == "Bearer token123"
        assert headers["Content-Type"] == "application/json"


class TestHTTPClient:
    """Tests for HTTPClient class."""

    def test_http_client_url_construction(self):
        """Test base_url + endpoint."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        client = HTTPClient("https://api.example.com", mock_handler)
        client.request("/users")

        call_args = mock_handler.handle.call_args
        url = call_args[1]["url"] if "url" in call_args[1] else call_args[0][1]
        assert url == "https://api.example.com/users"

    def test_http_client_url_strips_slashes(self):
        """Test trailing/leading slash handling."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        client = HTTPClient("https://api.example.com/", mock_handler)
        client.request("users")

        call_args = mock_handler.handle.call_args
        url = call_args[1]["url"] if "url" in call_args[1] else call_args[0][1]
        assert url == "https://api.example.com/users"

    def test_http_client_get_convenience(self):
        """Test get() method."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        client = HTTPClient("https://api.example.com", mock_handler)
        client.get("/users", params={"limit": 10})

        call_args = mock_handler.handle.call_args
        method = call_args[1]["method"] if "method" in call_args[1] else call_args[0][0]
        assert method == "GET"

    def test_http_client_post_convenience(self):
        """Test post() method."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(201)

        client = HTTPClient("https://api.example.com", mock_handler)
        client.post("/users", json={"name": "test"})

        call_args = mock_handler.handle.call_args
        method = call_args[1]["method"] if "method" in call_args[1] else call_args[0][0]
        assert method == "POST"

    def test_http_client_default_headers(self):
        """Test Content-Type is added by default."""
        mock_handler = Mock()
        mock_handler.handle.return_value = httpx.Response(200)

        client = HTTPClient("https://api.example.com", mock_handler)
        client.request("/users")

        call_args = mock_handler.handle.call_args
        headers = call_args[1]["headers"] if "headers" in call_args[1] else call_args[0][2]
        assert headers["Content-Type"] == "application/json"


@pytest.fixture
def respx_mock():
    """Provide respx mock for HTTP testing."""
    import respx

    with respx.mock:
        yield respx
