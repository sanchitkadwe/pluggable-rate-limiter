import os
import logging
from typing import Dict, Any, List, Optional
import redis.asyncio as redis
from rate_limiter.storage.base import BaseStorage
from rate_limiter.storage.memory import InMemoryStorage

logger = logging.getLogger("rate_limiter.storage.redis")

LUA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lua")


class RedisStorage(BaseStorage):
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        fallback_to_memory: bool = True,
        connection_timeout: float = 2.0,
    ):
        self.redis_url = redis_url
        self.fallback_to_memory = fallback_to_memory
        self.connection_timeout = connection_timeout
        self.client: Optional[redis.Redis] = None
        self._memory_fallback = InMemoryStorage() if fallback_to_memory else None
        self._lua_scripts: Dict[str, Any] = {}
        self._scripts_loaded = False

    async def _init_redis(self):
        if self._scripts_loaded:
            return

        try:
            self.client = redis.from_url(
                self.redis_url,
                socket_connect_timeout=self.connection_timeout,
                decode_responses=True,
            )
            await self.client.ping()

            scripts = [
                "token_bucket",
                "fixed_window",
                "sliding_window_log",
                "sliding_window_counter",
                "leaky_bucket",
            ]
            for script_name in scripts:
                file_path = os.path.join(LUA_DIR, f"{script_name}.lua")
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                        self._lua_scripts[script_name] = self.client.register_script(code)

            self._scripts_loaded = True
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(
                f"Could not connect to Redis at {self.redis_url}: {e}."
                + (" Using in-memory fallback." if self.fallback_to_memory else "")
            )
            self.client = None

    async def eval_script(
        self, script_name: str, keys: List[str], args: List[Any]
    ) -> List[Any]:
        if not self._scripts_loaded and self.client is None:
            await self._init_redis()

        if self.client is not None and script_name in self._lua_scripts:
            try:
                script_obj = self._lua_scripts[script_name]
                result = await script_obj(keys=keys, args=args)
                return [int(result[0]), int(result[1]), float(result[2])]
            except Exception as e:
                logger.error(f"Redis script execution failed for {script_name}: {e}")
                if self.fallback_to_memory and self._memory_fallback:
                    return await self._memory_fallback.eval_script(
                        script_name, keys, args
                    )
                raise
        elif self.fallback_to_memory and self._memory_fallback:
            return await self._memory_fallback.eval_script(script_name, keys, args)
        else:
            raise RuntimeError("Redis is unavailable and in-memory fallback is disabled.")

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None
        if self._memory_fallback:
            await self._memory_fallback.close()
