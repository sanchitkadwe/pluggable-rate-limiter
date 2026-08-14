from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from rate_limiter.config.schema import ExtractorConfig


class BaseKeyExtractor(ABC):
    @abstractmethod
    def extract_key(
        self,
        headers: Dict[str, str],
        client_ip: Optional[str],
        path: str,
        method: str,
        query_params: Optional[Dict[str, str]] = None,
    ) -> str:
        pass
