import time
from rate_limiter.algorithms.base import BaseAlgorithm
from rate_limiter.storage.base import BaseStorage, RateLimitResult
from rate_limiter.config.schema import RuleConfig


class LeakyBucketAlgorithm(BaseAlgorithm):
    async def evaluate(
        self, key: str, storage: BaseStorage, rule: RuleConfig
    ) -> RateLimitResult:
        capacity = rule.burst_capacity or rule.max_requests
        leak_rate = rule.leak_rate or (rule.max_requests / rule.window_seconds)
        now = time.time()

        res = await storage.eval_script(
            "leaky_bucket",
            keys=[key],
            args=[capacity, leak_rate, now, 1.0],
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
