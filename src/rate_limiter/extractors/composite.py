from typing import Dict, Any, Optional
from rate_limiter.extractors.base import BaseKeyExtractor
from rate_limiter.extractors.ip import IPKeyExtractor
from rate_limiter.config.schema import ExtractorConfig


class CompositeKeyExtractor(BaseKeyExtractor):
    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.ip_extractor = IPKeyExtractor(config)
        self.header_name = config.header_name.lower() if (config and config.header_name) else None

    def extract_key(
        self,
        headers: Dict[str, str],
        client_ip: Optional[str],
        path: str,
        method: str,
        query_params: Optional[Dict[str, str]] = None,
    ) -> str:
        headers_lower = {k.lower(): v for k, v in headers.items()}

        if self.header_name and self.header_name in headers_lower and headers_lower[self.header_name]:
            identity = f"hdr:{headers_lower[self.header_name]}"
        else:
            identity = f"ip:{self.ip_extractor.extract_key(headers, client_ip, path, method)}"

        return f"{identity}:{method.upper()}:{path}"
