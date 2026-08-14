from abc import ABC, abstractmethod
from rate_limiter.storage.base import BaseStorage, RateLimitResult
from rate_limiter.config.schema import RuleConfig


class BaseAlgorithm(ABC):
    @abstractmethod
    async def evaluate(
        self, key: str, storage: BaseStorage, rule: RuleConfig
    ) -> RateLimitResult:
        pass
