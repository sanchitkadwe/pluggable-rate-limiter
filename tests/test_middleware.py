import pytest
import uuid
import httpx
from server.app import app


@pytest.mark.asyncio
async def test_multi_method_rate_limiting():
    client_ip = f"192.168.1.{uuid.uuid4().hex[:6]}"
    headers = {"X-Forwarded-For": client_ip}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Test GET /api/data (Limit 10 req / 30s)
        for _ in range(10):
            res = await client.get("/api/data", headers=headers)
            assert res.status_code == 200
            assert "X-RateLimit-Limit" in res.headers

        # 11th GET request should be blocked (429)
        res_blocked = await client.get("/api/data", headers=headers)
        assert res_blocked.status_code == 429
        assert "Retry-After" in res_blocked.headers

        # 2. Test PUT /api/resource/42 (Limit 3 req / 30s)
        put_results = []
        for _ in range(4):
            r = await client.put("/api/resource/42", json={"val": 1}, headers=headers)
            put_results.append(r.status_code)

        assert put_results == [200, 200, 200, 429]

        # 3. Test DELETE /api/resource/42 (Limit 1 req / 30s)
        del1 = await client.delete("/api/resource/42", headers=headers)
        del2 = await client.delete("/api/resource/42", headers=headers)

        assert del1.status_code == 200
        assert del2.status_code == 429
