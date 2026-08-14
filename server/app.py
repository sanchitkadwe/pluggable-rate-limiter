import os
import sys
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from rate_limiter import RateLimiter, RateLimitMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server.app")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rate_limiter.yaml")

app = FastAPI(
    title="Rate Limiter Test Server",
    description="API server for testing rate limits across GET, POST, PUT, PATCH, and DELETE endpoints.",
    version="1.0.0",
)

rate_limiter_engine = RateLimiter(config_path=CONFIG_PATH)
app.add_middleware(RateLimitMiddleware, limiter=rate_limiter_engine)


@app.get("/api/data")
async def get_data(request: Request):
    return {
        "status": "success",
        "method": "GET",
        "endpoint": "/api/data",
        "message": "Data fetched successfully",
        "timestamp": time.time(),
    }


@app.post("/api/data")
async def post_data(request: Request, payload: Optional[Dict[str, Any]] = None):
    return {
        "status": "success",
        "method": "POST",
        "endpoint": "/api/data",
        "message": "Data created successfully",
        "payload": payload or {},
        "timestamp": time.time(),
    }


@app.put("/api/resource/{item_id}")
async def put_resource(item_id: str, request: Request, payload: Optional[Dict[str, Any]] = None):
    return {
        "status": "success",
        "method": "PUT",
        "endpoint": f"/api/resource/{item_id}",
        "message": f"Resource {item_id} updated",
        "payload": payload or {},
        "timestamp": time.time(),
    }


@app.patch("/api/resource/{item_id}")
async def patch_resource(item_id: str, request: Request, payload: Optional[Dict[str, Any]] = None):
    return {
        "status": "success",
        "method": "PATCH",
        "endpoint": f"/api/resource/{item_id}",
        "message": f"Resource {item_id} patched",
        "payload": payload or {},
        "timestamp": time.time(),
    }


@app.delete("/api/resource/{item_id}")
async def delete_resource(item_id: str, request: Request):
    return {
        "status": "success",
        "method": "DELETE",
        "endpoint": f"/api/resource/{item_id}",
        "message": f"Resource {item_id} deleted",
        "timestamp": time.time(),
    }


@app.get("/api/unlimited")
async def get_unlimited():
    return {
        "status": "success",
        "message": "Unlimited endpoint response",
        "timestamp": time.time(),
    }


@app.get("/stats")
async def get_stats():
    return {
        "storage_backend": type(rate_limiter_engine.storage).__name__,
        "rules_count": len(rate_limiter_engine._config.rules),
        "default_algorithm": rate_limiter_engine._config.default_algorithm,
        "rules": [r.model_dump() for r in rate_limiter_engine._config.rules],
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rate Limiter Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 1rem;
        }
        .header h1 { font-size: 1.5rem; color: #f8fafc; font-weight: 600; }
        .badge { background: #1e293b; padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.85rem; color: #38bdf8; font-weight: 500; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .card {
            background: #1e293b;
            border-radius: 8px;
            padding: 1.25rem;
            border: 1px solid #334155;
        }
        .card h3 { font-size: 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; }
        .card p { font-size: 0.85rem; color: #94a3b8; margin-bottom: 1rem; }
        .method {
            padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;
        }
        .GET { background: #0284c7; color: #fff; }
        .POST { background: #16a34a; color: #fff; }
        .PUT { background: #ca8a04; color: #fff; }
        .PATCH { background: #9333ea; color: #fff; }
        .DELETE { background: #dc2626; color: #fff; }

        .btn {
            width: 100%;
            padding: 0.5rem;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            background: #2563eb;
            color: #fff;
            font-size: 0.9rem;
        }
        .btn:hover { background: #1d4ed8; }
        .res-box {
            margin-top: 0.75rem;
            background: #0f172a;
            padding: 0.75rem;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.8rem;
            border-left: 3px solid #475569;
        }
        .logs-card {
            background: #1e293b;
            border-radius: 8px;
            padding: 1.25rem;
            border: 1px solid #334155;
        }
        .logs-card h3 { margin-bottom: 1rem; font-size: 1rem; }
        .log-list { list-style: none; font-family: monospace; font-size: 0.85rem; max-height: 220px; overflow-y: auto; }
        .log-item { padding: 0.4rem 0; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; }
        .ok { color: #4ade80; }
        .blocked { color: #f87171; font-weight: 600; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Rate Limiter Test Dashboard</h1>
        <div id="storage-badge" class="badge">Backend: Loading...</div>
    </div>

    <div class="grid">
        <div class="card">
            <h3><span>GET /api/data</span> <span class="method GET">GET</span></h3>
            <p>Token Bucket (10 req / 30s)</p>
            <button class="btn" onclick="sendReq('GET', '/api/data', 'get-res')">Send Request</button>
            <div id="get-res" class="res-box">Click button to test</div>
        </div>

        <div class="card">
            <h3><span>POST /api/data</span> <span class="method POST">POST</span></h3>
            <p>Fixed Window (5 req / 30s)</p>
            <button class="btn" style="background:#16a34a;" onclick="sendReq('POST', '/api/data', 'post-res')">Send Request</button>
            <div id="post-res" class="res-box">Click button to test</div>
        </div>

        <div class="card">
            <h3><span>PUT /api/resource/1</span> <span class="method PUT">PUT</span></h3>
            <p>Sliding Window Counter (3 req / 30s)</p>
            <button class="btn" style="background:#ca8a04;" onclick="sendReq('PUT', '/api/resource/1', 'put-res')">Send Request</button>
            <div id="put-res" class="res-box">Click button to test</div>
        </div>

        <div class="card">
            <h3><span>PATCH /api/resource/1</span> <span class="method PATCH">PATCH</span></h3>
            <p>Leaky Bucket (2 req / 30s)</p>
            <button class="btn" style="background:#9333ea;" onclick="sendReq('PATCH', '/api/resource/1', 'patch-res')">Send Request</button>
            <div id="patch-res" class="res-box">Click button to test</div>
        </div>

        <div class="card">
            <h3><span>DELETE /api/resource/1</span> <span class="method DELETE">DELETE</span></h3>
            <p>Sliding Window Log (1 req / 30s)</p>
            <button class="btn" style="background:#dc2626;" onclick="sendReq('DELETE', '/api/resource/1', 'delete-res')">Send Request</button>
            <div id="delete-res" class="res-box">Click button to test</div>
        </div>

        <div class="card">
            <h3><span>GET /api/unlimited</span> <span class="method GET">GET</span></h3>
            <p>High Limit (1000 req / 60s)</p>
            <button class="btn" style="background:#475569;" onclick="sendReq('GET', '/api/unlimited', 'unlimited-res')">Send Request</button>
            <div id="unlimited-res" class="res-box">Click button to test</div>
        </div>
    </div>

    <div class="logs-card">
        <h3>Request Log</h3>
        <ul id="log-list" class="log-list">
            <li class="log-item" style="color: #64748b;">No requests sent yet.</li>
        </ul>
    </div>

    <script>
        async function fetchStats() {
            try {
                const res = await fetch('/stats');
                const data = await res.json();
                document.getElementById('storage-badge').innerText = 'Storage: ' + data.storage_backend;
            } catch (e) {}
        }
        fetchStats();

        async function sendReq(method, path, targetId) {
            const el = document.getElementById(targetId);
            el.innerText = 'Sending...';

            try {
                const res = await fetch(path, { method: method });
                const limit = res.headers.get('X-RateLimit-Limit') || 'N/A';
                const remaining = res.headers.get('X-RateLimit-Remaining') || 'N/A';
                const reset = res.headers.get('X-RateLimit-Reset') || 'N/A';
                const retryAfter = res.headers.get('Retry-After') || 'N/A';

                el.innerHTML = `Status: ${res.status}<br>` +
                    `Limit: ${limit} | Remaining: ${remaining}<br>` +
                    `Reset: ${reset}s | Retry After: ${retryAfter}s`;

                el.style.borderLeftColor = res.status === 200 ? '#4ade80' : '#f87171';

                addLog(method, path, res.status, remaining, retryAfter);
            } catch (err) {
                el.innerText = 'Error: ' + err.message;
            }
        }

        function addLog(method, path, status, remaining, retryAfter) {
            const list = document.getElementById('log-list');
            const item = document.createElement('li');
            item.className = 'log-item';
            const timeStr = new Date().toLocaleTimeString();

            const statusClass = status === 200 ? 'ok' : 'blocked';
            const msg = status === 200
                ? `SUCCESS (Remaining: ${remaining})`
                : `BLOCKED 429 (Retry After: ${retryAfter}s)`;

            item.innerHTML = `<span>${timeStr} - ${method} ${path}</span> <span class="${statusClass}">${status} ${msg}</span>`;
            list.insertBefore(item, list.firstChild);
        }
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050)
