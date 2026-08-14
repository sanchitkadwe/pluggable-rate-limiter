import json
import math
import asyncio
from typing import Callable, Any
from rate_limiter.engine import RateLimiter


class WSGIRateLimitMiddleware:
    def __init__(self, app: Callable, limiter: RateLimiter):
        self.app = app
        self.limiter = limiter

    def __call__(self, environ: dict, start_response: Callable) -> Any:
        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET")
        client_ip = environ.get("REMOTE_ADDR", "127.0.0.1")

        headers = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").lower()
                headers[header_name] = value

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                self.limiter.is_allowed(
                    path=path,
                    method=method,
                    headers=headers,
                    client_ip=client_ip,
                )
            )
        finally:
            loop.close()

        header_config = self.limiter._config.headers

        if not result.allowed:
            headers_list = [("Content-Type", "application/json")]
            if header_config.include_headers:
                headers_list.extend([
                    (header_config.limit_header, str(result.limit)),
                    (header_config.remaining_header, "0"),
                    (header_config.reset_header, str(int(math.ceil(result.reset_after)))),
                    (header_config.retry_after_header, str(int(math.ceil(result.retry_after)))),
                ])

            start_response("429 Too Many Requests", headers_list)
            body = json.dumps({
                "error": "Too Many Requests",
                "message": "Rate limit exceeded.",
                "detail": {"retry_after_seconds": int(math.ceil(result.retry_after))},
            }).encode("utf-8")
            return [body]

        def custom_start_response(status, response_headers, exc_info=None):
            if header_config.include_headers:
                response_headers.extend([
                    (header_config.limit_header, str(result.limit)),
                    (header_config.remaining_header, str(result.remaining)),
                    (header_config.reset_header, str(int(math.ceil(result.reset_after)))),
                ])
            return start_response(status, response_headers, exc_info)

        return self.app(environ, custom_start_response)
