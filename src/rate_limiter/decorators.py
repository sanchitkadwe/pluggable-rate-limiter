import functools
import asyncio
from typing import Optional, Callable
from rate_limiter.engine import RateLimiter
from rate_limiter.config.schema import RateLimiterConfig, RuleConfig, AlgorithmType


class RateLimitExceededException(Exception):
    def __init__(self, message: str, retry_after: float):
        super().__init__(message)
        self.retry_after = retry_after


def rate_limit(
    max_requests: int = 10,
    window_seconds: float = 60.0,
    algorithm: AlgorithmType = AlgorithmType.TOKEN_BUCKET,
    key_func: Optional[Callable[..., str]] = None,
    limiter: Optional[RateLimiter] = None,
):
    engine = limiter or RateLimiter()

    def decorator(fn):
        rule = RuleConfig(
            name=f"decorator:{fn.__name__}",
            path=f"func:{fn.__name__}",
            methods=["*"],
            algorithm=algorithm,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            key_id = key_func(*args, **kwargs) if key_func else "global"
            full_key = f"decorator:{fn.__name__}:{key_id}"
            algo = engine._algorithms[algorithm]

            result = await algo.evaluate(full_key, engine.storage, rule)
            if not result.allowed:
                raise RateLimitExceededException(
                    f"Rate limit exceeded for '{fn.__name__}'",
                    retry_after=result.retry_after,
                )

            return await fn(*args, **kwargs)

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            key_id = key_func(*args, **kwargs) if key_func else "global"
            full_key = f"decorator:{fn.__name__}:{key_id}"
            algo = engine._algorithms[algorithm]

            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(
                    algo.evaluate(full_key, engine.storage, rule)
                )
            finally:
                loop.close()

            if not result.allowed:
                raise RateLimitExceededException(
                    f"Rate limit exceeded for '{fn.__name__}'",
                    retry_after=result.retry_after,
                )

            return fn(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper

    return decorator
