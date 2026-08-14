import pytest
import uuid
import asyncio
from rate_limiter.storage.memory import InMemoryStorage
from rate_limiter.storage.redis_storage import RedisStorage
from rate_limiter.config.schema import RuleConfig, AlgorithmType
from rate_limiter.algorithms.token_bucket import TokenBucketAlgorithm
from rate_limiter.algorithms.fixed_window import FixedWindowAlgorithm
from rate_limiter.algorithms.sliding_window_log import SlidingWindowLogAlgorithm
from rate_limiter.algorithms.sliding_window_counter import SlidingWindowCounterAlgorithm
from rate_limiter.algorithms.leaky_bucket import LeakyBucketAlgorithm


@pytest.mark.asyncio
async def test_redis_connection_and_ping():
    storage = RedisStorage(redis_url="redis://localhost:6379/0", fallback_to_memory=False)
    await storage._init_redis()
    assert storage.client is not None
    assert await storage.client.ping() is True
    await storage.close()


@pytest.mark.asyncio
async def test_token_bucket_redis():
    storage = RedisStorage(redis_url="redis://localhost:6379/0")
    algo = TokenBucketAlgorithm()
    rule = RuleConfig(name="test_tb", max_requests=3, window_seconds=10.0, burst_capacity=3)

    key = f"test_tb_redis_{uuid.uuid4().hex[:6]}"
    res1 = await algo.evaluate(key, storage, rule)
    res2 = await algo.evaluate(key, storage, rule)
    res3 = await algo.evaluate(key, storage, rule)
    res4 = await algo.evaluate(key, storage, rule)

    assert res1.allowed is True
    assert res2.allowed is True
    assert res3.allowed is True
    assert res4.allowed is False
    assert res4.remaining == 0
    assert res4.retry_after > 0
    await storage.close()


@pytest.mark.asyncio
async def test_fixed_window_redis():
    storage = RedisStorage(redis_url="redis://localhost:6379/0")
    algo = FixedWindowAlgorithm()
    rule = RuleConfig(name="test_fw", max_requests=2, window_seconds=5.0)

    key = f"test_fw_redis_{uuid.uuid4().hex[:6]}"
    res1 = await algo.evaluate(key, storage, rule)
    res2 = await algo.evaluate(key, storage, rule)
    res3 = await algo.evaluate(key, storage, rule)

    assert res1.allowed is True
    assert res2.allowed is True
    assert res3.allowed is False
    await storage.close()


@pytest.mark.asyncio
async def test_sliding_window_log_redis():
    storage = RedisStorage(redis_url="redis://localhost:6379/0")
    algo = SlidingWindowLogAlgorithm()
    rule = RuleConfig(name="test_swl", max_requests=2, window_seconds=5.0)

    key = f"test_swl_redis_{uuid.uuid4().hex[:6]}"
    res1 = await algo.evaluate(key, storage, rule)
    res2 = await algo.evaluate(key, storage, rule)
    res3 = await algo.evaluate(key, storage, rule)

    assert res1.allowed is True
    assert res2.allowed is True
    assert res3.allowed is False
    await storage.close()


@pytest.mark.asyncio
async def test_sliding_window_counter_redis():
    storage = RedisStorage(redis_url="redis://localhost:6379/0")
    algo = SlidingWindowCounterAlgorithm()
    rule = RuleConfig(name="test_swc", max_requests=2, window_seconds=10.0)

    key = f"test_swc_redis_{uuid.uuid4().hex[:6]}"
    res1 = await algo.evaluate(key, storage, rule)
    res2 = await algo.evaluate(key, storage, rule)
    res3 = await algo.evaluate(key, storage, rule)

    assert res1.allowed is True
    assert res2.allowed is True
    assert res3.allowed is False
    await storage.close()


@pytest.mark.asyncio
async def test_leaky_bucket_redis():
    storage = RedisStorage(redis_url="redis://localhost:6379/0")
    algo = LeakyBucketAlgorithm()
    rule = RuleConfig(name="test_lb", max_requests=2, window_seconds=10.0, burst_capacity=2, leak_rate=0.1)

    key = f"test_lb_redis_{uuid.uuid4().hex[:6]}"
    res1 = await algo.evaluate(key, storage, rule)
    res2 = await algo.evaluate(key, storage, rule)
    res3 = await algo.evaluate(key, storage, rule)

    assert res1.allowed is True
    assert res2.allowed is True
    assert res3.allowed is False
    await storage.close()


@pytest.mark.asyncio
async def test_redis_fallback_to_memory():
    # Attempt connection to invalid Redis port with fallback enabled
    storage = RedisStorage(redis_url="redis://localhost:9999/0", fallback_to_memory=True, connection_timeout=0.2)
    algo = FixedWindowAlgorithm()
    rule = RuleConfig(name="test_fallback", max_requests=1, window_seconds=5.0)

    key = f"test_fallback_{uuid.uuid4().hex[:6]}"
    res1 = await algo.evaluate(key, storage, rule)
    res2 = await algo.evaluate(key, storage, rule)

    assert res1.allowed is True
    assert res2.allowed is False
    await storage.close()
