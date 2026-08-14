import pytest
from rate_limiter.config.schema import RateLimiterConfig, AlgorithmType, StorageType
from rate_limiter.config.loader import ConfigLoader


def test_default_config_schema():
    cfg = RateLimiterConfig()
    assert cfg.storage.type == StorageType.REDIS
    assert cfg.default_algorithm == AlgorithmType.TOKEN_BUCKET
    assert cfg.default_max_requests == 60


def test_dict_loader():
    loader = ConfigLoader()
    raw = {
        "storage": {"type": "memory"},
        "default_algorithm": "sliding_window_counter",
        "rules": [
            {
                "name": "put_rule",
                "path": "/api/resource/*",
                "methods": ["PUT"],
                "algorithm": "sliding_window_counter",
                "max_requests": 3,
                "window_seconds": 10.0,
            }
        ],
    }
    config = loader.load_from_dict(raw)
    assert config.storage.type == StorageType.MEMORY
    assert len(config.rules) == 1
    assert config.rules[0].methods == ["PUT"]
    assert config.rules[0].max_requests == 3
