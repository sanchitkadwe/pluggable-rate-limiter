from typing import Dict, Any, Optional
from rate_limiter.extractors.base import BaseKeyExtractor
from rate_limiter.config.schema import ExtractorConfig


class HeaderKeyExtractor(BaseKeyExtractor):
    def __init__(self, config: ExtractorConfig):
        self.header_name = config.header_name.lower() if config.header_name else "x-api-key"

    def extract_key(
        self,
        headers: Dict[str, str],
        client_ip: Optional[str],
        path: str,
        method: str,
        query_params: Optional[Dict[str, str]] = None,
    ) -> str:
        headers_lower = {k.lower(): v for k, v in headers.items()}

        if self.header_name in headers_lower and headers_lower[self.header_name]:
            return f"header:{headers_lower[self.header_name]}"

        return client_ip or "127.0.0.1"
