from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class StorageType(str, Enum):
    MEMORY = "memory"
    REDIS = "redis"


class AlgorithmType(str, Enum):
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW_LOG = "sliding_window_log"
    SLIDING_WINDOW_COUNTER = "sliding_window_counter"


class ExtractorType(str, Enum):
    IP = "ip"
    HEADER = "header"
    QUERY = "query"
    COMPOSITE = "composite"


class ExtractorConfig(BaseModel):
    type: ExtractorType = ExtractorType.IP
    header_name: Optional[str] = "X-API-Key"
    param_name: Optional[str] = "api_key"
    use_x_forwarded_for: bool = True


class StorageConfig(BaseModel):
    type: StorageType = StorageType.REDIS
    redis_url: str = "redis://localhost:6379/0"
    fallback_to_memory: bool = True
    key_prefix: str = "ratelimit"
    connection_timeout: float = 2.0


class RuleConfig(BaseModel):
    name: str
    path: str = "*"
    methods: List[str] = Field(default_factory=lambda: ["*"])
    algorithm: Optional[AlgorithmType] = None
    max_requests: int = 60
    window_seconds: float = 60.0
    burst_capacity: Optional[int] = None
    leak_rate: Optional[float] = None
    extractor: Optional[ExtractorConfig] = None
    enabled: bool = True

    @field_validator("methods", mode="before")
    @classmethod
    def normalize_methods(cls, val):
        if isinstance(val, str):
            return [val.upper()]
        if isinstance(val, list):
            return [m.upper() for m in val]
        return ["*"]


class HeaderConfig(BaseModel):
    include_headers: bool = True
    limit_header: str = "X-RateLimit-Limit"
    remaining_header: str = "X-RateLimit-Remaining"
    reset_header: str = "X-RateLimit-Reset"
    retry_after_header: str = "Retry-After"


class RateLimiterConfig(BaseModel):
    version: str = "1.0"
    storage: StorageConfig = Field(default_factory=StorageConfig)
    default_algorithm: AlgorithmType = AlgorithmType.TOKEN_BUCKET
    default_max_requests: int = 60
    default_window_seconds: float = 60.0
    default_burst_capacity: int = 60
    default_leak_rate: float = 1.0
    extractor: ExtractorConfig = Field(default_factory=ExtractorConfig)
    headers: HeaderConfig = Field(default_factory=HeaderConfig)
    rules: List[RuleConfig] = Field(default_factory=list)
    hot_reload: bool = True
    poll_interval_seconds: float = 2.0
