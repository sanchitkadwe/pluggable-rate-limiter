import time
import asyncio
from typing import Dict, Any, List
from rate_limiter.storage.base import BaseStorage


class InMemoryStorage(BaseStorage):
    def __init__(self):
        self._lock = asyncio.Lock()
        self._data: Dict[str, Any] = {}

    async def eval_script(
        self, script_name: str, keys: List[str], args: List[Any]
    ) -> List[Any]:
        async with self._lock:
            now = float(args[2]) if len(args) > 2 else time.time()

            if script_name == "token_bucket":
                return self._token_bucket(
                    key=keys[0],
                    max_capacity=float(args[0]),
                    refill_rate=float(args[1]),
                    now=now,
                    requested=float(args[3]) if len(args) > 3 else 1.0,
                )
            elif script_name == "fixed_window":
                return self._fixed_window(
                    key=keys[0],
                    max_requests=int(args[0]),
                    window_seconds=float(args[1]),
                    now=now,
                )
            elif script_name == "sliding_window_log":
                return self._sliding_window_log(
                    key=keys[0],
                    max_requests=int(args[0]),
                    window_seconds=float(args[1]),
                    now=now,
                    request_id=str(args[3]) if len(args) > 3 else str(now),
                )
            elif script_name == "sliding_window_counter":
                return self._sliding_window_counter(
                    current_key=keys[0],
                    previous_key=keys[1],
                    max_requests=int(args[0]),
                    window_seconds=float(args[1]),
                    time_into_current=float(args[2]),
                )
            elif script_name == "leaky_bucket":
                return self._leaky_bucket(
                    key=keys[0],
                    max_capacity=float(args[0]),
                    leak_rate=float(args[1]),
                    now=now,
                    requested=float(args[3]) if len(args) > 3 else 1.0,
                )
            else:
                raise ValueError(f"Unknown script: {script_name}")

    def _token_bucket(self, key, max_capacity, refill_rate, now, requested):
        entry = self._data.get(key, {"tokens": max_capacity, "last_updated": now})
        delta = max(0.0, now - entry["last_updated"])
        tokens = min(max_capacity, entry["tokens"] + delta * refill_rate)
        entry["last_updated"] = now

        if tokens >= requested:
            tokens -= requested
            entry["tokens"] = tokens
            self._data[key] = entry
            return [1, int(tokens), 0.0]
        else:
            entry["tokens"] = tokens
            self._data[key] = entry
            needed = requested - tokens
            reset_after = needed / refill_rate
            return [0, int(tokens), reset_after]

    def _fixed_window(self, key, max_requests, window_seconds, now):
        entry = self._data.get(key, {"count": 0, "reset_at": now + window_seconds})
        if now >= entry["reset_at"]:
            entry = {"count": 0, "reset_at": now + window_seconds}

        entry["count"] += 1
        self._data[key] = entry

        remaining = max(0, max_requests - entry["count"])
        reset_after = max(0.0, entry["reset_at"] - now)
        allowed = 1 if entry["count"] <= max_requests else 0
        return [allowed, remaining, reset_after]

    def _sliding_window_log(self, key, max_requests, window_seconds, now, request_id):
        timestamps = self._data.get(key, [])
        cutoff = now - window_seconds
        timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(timestamps) < max_requests:
            timestamps.append(now)
            self._data[key] = timestamps
            remaining = max_requests - len(timestamps)
            return [1, remaining, window_seconds]
        else:
            self._data[key] = timestamps
            oldest = timestamps[0] if timestamps else now
            reset_after = max(0.0, (oldest + window_seconds) - now)
            return [0, 0, reset_after]

    def _sliding_window_counter(
        self, current_key, previous_key, max_requests, window_seconds, time_into_current
    ):
        current_count = self._data.get(current_key, 0)
        previous_count = self._data.get(previous_key, 0)

        weight = (window_seconds - time_into_current) / window_seconds
        estimated_count = previous_count * weight + current_count

        reset_after = window_seconds - time_into_current

        if estimated_count < max_requests:
            self._data[current_key] = current_count + 1
            remaining = max(0, int(max_requests - (estimated_count + 1)))
            return [1, remaining, reset_after]
        else:
            return [0, 0, reset_after]

    def _leaky_bucket(self, key, max_capacity, leak_rate, now, requested):
        entry = self._data.get(key, {"water": 0.0, "last_leak": now})
        delta = max(0.0, now - entry["last_leak"])
        water = max(0.0, entry["water"] - delta * leak_rate)
        entry["last_leak"] = now

        if water + requested <= max_capacity:
            water += requested
            entry["water"] = water
            self._data[key] = entry
            remaining = int(max_capacity - water)
            return [1, remaining, 0.0]
        else:
            entry["water"] = water
            self._data[key] = entry
            overflow = (water + requested) - max_capacity
            reset_after = overflow / leak_rate
            return [0, 0, reset_after]

    async def close(self):
        self._data.clear()
