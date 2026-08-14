import time
import uuid
from rate_limiter.algorithms.base import BaseAlgorithm
from rate_limiter.storage.base import BaseStorage, RateLimitResult
from rate_limiter.config.schema import RuleConfig


class SlidingWindowLogAlgorithm(BaseAlgorithm):
    async def evaluate(
        self, key: str, storage: BaseStorage, rule: RuleConfig
    ) -> RateLimitResult:
        now = time.time()
        request_id = f"{now}-{uuid.uuid4().hex[:8]}"

        res = await storage.eval_script(
            "sliding_window_log",
            keys=[key],
            args=[rule.max_requests, rule.window_seconds, now, request_id],
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
