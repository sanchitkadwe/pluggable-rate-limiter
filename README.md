# Python Rate Limiter

A flexible rate limiter library for Python applications. It supports multiple rate limiting algorithms, YAML configuration, Redis for distributed deployments, and in-memory storage for single-node setups.

Included are middlewares for FastAPI/Starlette and Flask/WSGI, function decorators, and a sample server with a testing dashboard.

## Features

- **Rate Limiting Algorithms**: Token Bucket, Leaky Bucket, Fixed Window, Sliding Window Log, and Sliding Window Counter.
- **Storage Backends**: Redis (using Lua scripts for atomic operations) with fallback to in-memory storage.
- **YAML Configuration**: Dynamic configuration for routes, HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`), limits, and key extraction.
- **Hot Reloading**: Automatically reloads configuration when `rate_limiter.yaml` changes.
- **Integrations**: ASGI middleware (FastAPI/Starlette), WSGI middleware (Flask), and function decorators.
- **CLI & Testing Dashboard**: Command line tool for load testing and a web dashboard for manual testing.

---

## Installation

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Redis Setup (Optional)

If Redis is available at `localhost:6379`, the rate limiter connects automatically. If Redis is down or not installed, it falls back to in-memory mode.

To run Redis in Docker:
```bash
docker run -d --name redis-rate-limiter -p 6379:6379 redis:alpine
```

---

## Running the Demo Server

Start the test server (listens on `0.0.0.0:8050`):

```bash
PYTHONPATH=src .venv/bin/rate-limiter serve --port 8050
```

- Web Dashboard: Open `http://localhost:8050/dashboard` in a browser.
- Server Stats: `http://localhost:8050/stats`

---

## Load Testing

You can use the built-in CLI tool to send test requests:

```bash
# Test PUT requests
PYTHONPATH=src .venv/bin/rate-limiter test --url http://localhost:8050/api/resource/1 --method PUT -n 5

# Test GET requests
PYTHONPATH=src .venv/bin/rate-limiter test --url http://localhost:8050/api/data --method GET -n 12
```

Sample output:
```
  Rate Limiter Load Test Results (PUT http://localhost:8050/api/resource/1)
┏━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Req # ┃ Status Code  ┃   Allowed    ┃ Remaining ┃ Retry After ┃ Time (ms) ┃
┡━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│     1 │    200 OK    │     YES      │         2 │           - │      11.2 │
│     2 │    200 OK    │     YES      │         1 │           - │       7.8 │
│     3 │    200 OK    │     YES      │         0 │           - │       3.2 │
│     4 │ 429 TOO MANY │ NO (BLOCKED) │         0 │           5 │       2.0 │
│     5 │ 429 TOO MANY │ NO (BLOCKED) │         0 │           5 │       6.2 │
└───────┴──────────────┴──────────────┴───────────┴─────────────┴───────────┘
Summary: Total: 5 | Allowed: 3 | Blocked: 2
```

---
## Running Tests

```bash
.venv/bin/pytest -v
```

---

## Project Layout

```
.
├── rate_limiter.yaml
├── README.md
├── requirements.txt
├── pyproject.toml
├── src/
│   └── rate_limiter/
│       ├── algorithms/
│       ├── config/
│       ├── extractors/
│       ├── lua/
│       ├── middleware/
│       ├── storage/
│       ├── cli.py
│       ├── decorators.py
│       └── engine.py
├── server/
│   └── app.py
└── tests/
```
