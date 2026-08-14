from abc import ABC, abstractmethod
from typing import Tuple, Optional, Any, List
from dataclasses import dataclass


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_after: float
    retry_after: float


class BaseStorage(ABC):
    @abstractmethod
    async def eval_script(
        self, script: str, keys: List[str], args: List[Any]
    ) -> Any:
        pass

    @abstractmethod
    async def close(self):
        pass
