import time
from rate_limiter.algorithms.base import BaseAlgorithm
from rate_limiter.storage.base import BaseStorage, RateLimitResult
from rate_limiter.config.schema import RuleConfig


class SlidingWindowCounterAlgorithm(BaseAlgorithm):
    async def evaluate(
        self, key: str, storage: BaseStorage, rule: RuleConfig
    ) -> RateLimitResult:
        now = time.time()
        window_sec = rule.window_seconds
        current_window = int(now // window_sec)
        previous_window = current_window - 1
        time_into_current = now - (current_window * window_sec)

        current_key = f"{key}:{current_window}"
        previous_key = f"{key}:{previous_window}"

        res = await storage.eval_script(
            "sliding_window_counter",
            keys=[current_key, previous_key],
            args=[rule.max_requests, window_sec, time_into_current],
        )

        allowed = bool(res[0])
        remaining = int(res[1])
        reset_after = float(res[2])
        retry_after = reset_after if not allowed else 0.0

        return RateLimitResult(
            allowed=allowed,
            limit=rule.max_requests,
            remaining=remaining,
            reset_after=reset_after,
            retry_after=retry_after,
        )
