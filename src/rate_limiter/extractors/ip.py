from typing import Dict, Any, Optional
from rate_limiter.extractors.base import BaseKeyExtractor
from rate_limiter.config.schema import ExtractorConfig


class IPKeyExtractor(BaseKeyExtractor):
    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.use_x_forwarded_for = config.use_x_forwarded_for if config else True

    def extract_key(
        self,
        headers: Dict[str, str],
        client_ip: Optional[str],
        path: str,
        method: str,
        query_params: Optional[Dict[str, str]] = None,
    ) -> str:
        headers_lower = {k.lower(): v for k, v in headers.items()}

        if self.use_x_forwarded_for and "x-forwarded-for" in headers_lower:
            ip_list = headers_lower["x-forwarded-for"].split(",")
            if ip_list:
                return ip_list[0].strip()

        if "x-real-ip" in headers_lower:
            return headers_lower["x-real-ip"].strip()

        return client_ip or "127.0.0.1"
