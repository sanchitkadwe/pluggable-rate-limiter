import os
import yaml
import logging
import asyncio
from typing import Optional, Callable
from rate_limiter.config.schema import RateLimiterConfig

logger = logging.getLogger("rate_limiter.config")


class ConfigLoader:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config: RateLimiterConfig = RateLimiterConfig()
        self._last_modified: float = 0.0
        self._callbacks = []
        self._reload_task: Optional[asyncio.Task] = None

        if config_path:
            self.load_from_file(config_path)

    @property
    def config(self) -> RateLimiterConfig:
        return self._config

    def load_from_file(self, path: str) -> RateLimiterConfig:
        if not os.path.exists(path):
            logger.warning(f"Config file {path} not found, using default configuration")
            return self._config

        try:
            mtime = os.path.getmtime(path)
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            new_config = RateLimiterConfig.model_validate(data)
            self._config = new_config
            self.config_path = path
            self._last_modified = mtime
            logger.info(f"Loaded config from {path}")
            return self._config
        except Exception as e:
            logger.error(f"Failed to load YAML config from {path}: {e}")
            raise

    def load_from_dict(self, data: dict) -> RateLimiterConfig:
        self._config = RateLimiterConfig.model_validate(data)
        return self._config

    def register_on_change(self, callback: Callable[[RateLimiterConfig], None]):
        self._callbacks.append(callback)

    def check_for_reload(self) -> bool:
        if not self.config_path or not os.path.exists(self.config_path):
            return False

        try:
            mtime = os.path.getmtime(self.config_path)
            if mtime > self._last_modified:
                logger.info(f"Config file {self.config_path} changed, reloading")
                self.load_from_file(self.config_path)
                for callback in self._callbacks:
                    try:
                        callback(self._config)
                    except Exception as e:
                        logger.error(f"Error in config reload callback: {e}")
                return True
        except Exception as e:
            logger.error(f"Failed to check config file timestamp: {e}")
        return False

    async def start_hot_reload_watcher(self):
        if not self.config_path or self._reload_task:
            return

        async def watch():
            while True:
                await asyncio.sleep(self._config.poll_interval_seconds)
                if self._config.hot_reload:
                    self.check_for_reload()

        self._reload_task = asyncio.create_task(watch())

    def stop_hot_reload_watcher(self):
        if self._reload_task:
            self._reload_task.cancel()
            self._reload_task = None
