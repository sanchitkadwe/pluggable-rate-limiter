import fnmatch
import logging
from typing import Optional, Dict, Any, List
from rate_limiter.config.schema import (
    RateLimiterConfig,
    RuleConfig,
    AlgorithmType,
    StorageType,
    ExtractorType,
)
from rate_limiter.config.loader import ConfigLoader
from rate_limiter.storage.base import BaseStorage, RateLimitResult
from rate_limiter.storage.memory import InMemoryStorage
from rate_limiter.storage.redis_storage import RedisStorage
from rate_limiter.algorithms.base import BaseAlgorithm
from rate_limiter.algorithms.token_bucket import TokenBucketAlgorithm
from rate_limiter.algorithms.leaky_bucket import LeakyBucketAlgorithm
from rate_limiter.algorithms.fixed_window import FixedWindowAlgorithm
from rate_limiter.algorithms.sliding_window_log import SlidingWindowLogAlgorithm
from rate_limiter.algorithms.sliding_window_counter import SlidingWindowCounterAlgorithm
from rate_limiter.extractors.base import BaseKeyExtractor
from rate_limiter.extractors.ip import IPKeyExtractor
from rate_limiter.extractors.header import HeaderKeyExtractor
from rate_limiter.extractors.composite import CompositeKeyExtractor

logger = logging.getLogger("rate_limiter.engine")


class RateLimiter:
    def __init__(
        self,
        config: Optional[RateLimiterConfig] = None,
        config_path: Optional[str] = None,
    ):
        if config_path:
            self.loader = ConfigLoader(config_path)
            self._config = self.loader.config
        elif config:
            self.loader = None
            self._config = config
        else:
            self.loader = None
            self._config = RateLimiterConfig()

        self._algorithms: Dict[AlgorithmType, BaseAlgorithm] = {
            AlgorithmType.TOKEN_BUCKET: TokenBucketAlgorithm(),
            AlgorithmType.LEAKY_BUCKET: LeakyBucketAlgorithm(),
            AlgorithmType.FIXED_WINDOW: FixedWindowAlgorithm(),
            AlgorithmType.SLIDING_WINDOW_LOG: SlidingWindowLogAlgorithm(),
            AlgorithmType.SLIDING_WINDOW_COUNTER: SlidingWindowCounterAlgorithm(),
        }

        self.storage: BaseStorage = self._init_storage()

        if self.loader:
            self.loader.register_on_change(self._on_config_reloaded)

    def _init_storage(self) -> BaseStorage:
        storage_config = self._config.storage
        if storage_config.type == StorageType.REDIS:
            return RedisStorage(
                redis_url=storage_config.redis_url,
                fallback_to_memory=storage_config.fallback_to_memory,
                connection_timeout=storage_config.connection_timeout,
            )
        else:
            return InMemoryStorage()

    def _on_config_reloaded(self, new_config: RateLimiterConfig):
        logger.info("Updated rate limiter configuration")
        self._config = new_config

    def resolve_rule(self, path: str, method: str) -> RuleConfig:
        method = method.upper()

        for rule in self._config.rules:
            if not rule.enabled:
                continue

            method_match = "*" in rule.methods or method in rule.methods
            if not method_match:
                continue

            if fnmatch.fnmatch(path, rule.path):
                return rule

        return RuleConfig(
            name="default_fallback",
            path="*",
            methods=["*"],
            algorithm=self._config.default_algorithm,
            max_requests=self._config.default_max_requests,
            window_seconds=self._config.default_window_seconds,
            burst_capacity=self._config.default_burst_capacity,
            leak_rate=self._config.default_leak_rate,
        )

    def get_extractor(self, rule: RuleConfig) -> BaseKeyExtractor:
        extractor_config = rule.extractor or self._config.extractor
        if extractor_config.type == ExtractorType.HEADER:
            return HeaderKeyExtractor(extractor_config)
        elif extractor_config.type == ExtractorType.COMPOSITE:
            return CompositeKeyExtractor(extractor_config)
        else:
            return IPKeyExtractor(extractor_config)

    async def is_allowed(
        self,
        path: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        client_ip: Optional[str] = None,
        query_params: Optional[Dict[str, str]] = None,
    ) -> RateLimitResult:
        headers = headers or {}

        rule = self.resolve_rule(path, method)
        extractor = self.get_extractor(rule)
        client_key = extractor.extract_key(headers, client_ip, path, method, query_params)

        prefix = self._config.storage.key_prefix
        storage_key = f"{prefix}:{rule.name}:{client_key}"

        algorithm_type = rule.algorithm or self._config.default_algorithm
        algorithm = self._algorithms.get(algorithm_type, self._algorithms[AlgorithmType.TOKEN_BUCKET])

        result = await algorithm.evaluate(storage_key, self.storage, rule)
        return result

    async def close(self):
        if self.storage:
            await self.storage.close()
        if self.loader:
            self.loader.stop_hot_reload_watcher()
