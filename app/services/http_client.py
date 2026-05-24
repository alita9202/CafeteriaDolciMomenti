import json
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class HttpClientConfig:
    timeout_seconds: int = 20
    max_retries: int = 2
    retry_backoff_seconds: float = 0.75


class HttpClientError(Exception):
    """Raised for non-recoverable HTTP client failures."""


class RetryableHttpError(HttpClientError):
    """Raised when the request failed after all retries."""


class HttpClient:
    """Small reusable JSON HTTP client with timeout/retry handling."""

    def __init__(self, config: HttpClientConfig | None = None):
        self.config = config or HttpClientConfig()

    def post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        headers = headers or {}
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=url,
            data=data,
            headers={
                "Content-Type": "application/json",
                **headers,
            },
            method="POST",
        )

        attempts = self.config.max_retries + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                with request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                    response_data = resp.read().decode("utf-8")
                    return json.loads(response_data)
            except error.HTTPError as exc:
                status = getattr(exc, "code", None)
                body = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else ""
                if status in (408, 429, 500, 502, 503, 504) and attempt < attempts - 1:
                    time.sleep(self.config.retry_backoff_seconds * (attempt + 1))
                    last_error = exc
                    continue
                raise HttpClientError(f"HTTP {status}: {body}") from exc
            except (error.URLError, TimeoutError) as exc:
                if attempt < attempts - 1:
                    time.sleep(self.config.retry_backoff_seconds * (attempt + 1))
                    last_error = exc
                    continue
                last_error = exc

        raise RetryableHttpError(f"Request failed after retries: {last_error}")
