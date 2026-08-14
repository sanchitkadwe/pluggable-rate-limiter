import time
from rate_limiter.algorithms.base import BaseAlgorithm
from rate_limiter.storage.base import BaseStorage, RateLimitResult
from rate_limiter.config.schema import RuleConfig


class FixedWindowAlgorithm(BaseAlgorithm):
    async def evaluate(
        self, key: str, storage: BaseStorage, rule: RuleConfig
    ) -> RateLimitResult:
        now = time.time()
        window_sec = rule.window_seconds
        current_window = int(now // window_sec)
        window_key = f"{key}:{current_window}"

        res = await storage.eval_script(
            "fixed_window",
            keys=[window_key],
            args=[rule.max_requests, window_sec, now],
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
