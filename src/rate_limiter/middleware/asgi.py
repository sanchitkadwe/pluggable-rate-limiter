import json
import math
from typing import Optional, Callable
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.responses import JSONResponse
from rate_limiter.engine import RateLimiter


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, limiter: RateLimiter):
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/")
        method = scope.get("method", "GET")

        if path.startswith("/dashboard") or path.startswith("/favicon.ico"):
            await self.app(scope, receive, send)
            return

        raw_headers = scope.get("headers", [])
        headers = {}
        for name, value in raw_headers:
            headers[name.decode("latin1").lower()] = value.decode("latin1")

        client = scope.get("client")
        client_ip = client[0] if client else "127.0.0.1"

        result = await self.limiter.is_allowed(
            path=path,
            method=method,
            headers=headers,
            client_ip=client_ip,
        )

        header_config = self.limiter._config.headers

        if not result.allowed:
            response_headers = {}
            if header_config.include_headers:
                response_headers[header_config.limit_header] = str(result.limit)
                response_headers[header_config.remaining_header] = "0"
                response_headers[header_config.reset_header] = str(int(math.ceil(result.reset_after)))
                response_headers[header_config.retry_after_header] = str(int(math.ceil(result.retry_after)))

            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "detail": {
                        "limit": result.limit,
                        "retry_after_seconds": int(math.ceil(result.retry_after)),
                    },
                },
                headers=response_headers,
            )
            await response(scope, receive, send)
            return

        if header_config.include_headers:
            async def send_with_headers(message):
                if message["type"] == "http.response.start":
                    response_headers = list(message.get("headers", []))
                    response_headers.append((header_config.limit_header.encode("latin1"), str(result.limit).encode("latin1")))
                    response_headers.append((header_config.remaining_header.encode("latin1"), str(result.remaining).encode("latin1")))
                    response_headers.append((header_config.reset_header.encode("latin1"), str(int(math.ceil(result.reset_after))).encode("latin1")))
                    message["headers"] = response_headers
                await send(message)

            await self.app(scope, receive, send_with_headers)
        else:
            await self.app(scope, receive, send)
