# RateLimiterX

> A pluggable, distributed, policy-driven rate limiting framework that can run as an SDK, middleware, API Gateway plugin, Sidecar, or Standalone Service.

---

## Vision

Modern applications require rate limiting at different layers of the architecture.

Some applications prefer enforcing limits inside the application server as middleware.

Others perform rate limiting at the API Gateway.

Large-scale systems often centralize rate limiting as an independent distributed service shared by multiple applications.

Most existing libraries tightly couple themselves to one framework, one deployment model, or one storage backend.

**RateLimiterX** aims to solve this problem by providing a single core engine that can be deployed anywhere while keeping the same configuration, algorithms, and policies.

The core engine remains unchanged regardless of where it is deployed.

---

# Goals

- Completely pluggable architecture
- Framework agnostic
- Deployment agnostic
- Policy-driven configuration
- Multiple rate limiting algorithms
- Distributed by design
- Extensible through plugins
- Production-ready observability
- High performance
- Easy integration

---

# Core Philosophy

One Core.

Multiple Adapters.

```
                   +----------------------+
                   |  RateLimiter Engine  |
                   +----------------------+
                              ▲
                              │
        ---------------------------------------------
        │           │           │          │
        ▼           ▼           ▼          ▼

    Django     FastAPI      Gateway     HTTP API

        │           │           │          │
        └───────────┴───────────┴──────────┘

                   Same Core Engine
```

The core engine knows nothing about

- Django
- Flask
- FastAPI
- API Gateway
- Kubernetes
- HTTP
- gRPC

Adapters translate platform-specific requests into a common internal request format.

---

# Features

## Algorithms

- Fixed Window
- Sliding Window
- Sliding Log
- Token Bucket
- Leaky Bucket

---

## Storage Backends

- In-Memory
- Redis
- Redis Cluster

Future

- DynamoDB
- Cassandra
- CockroachDB
- Aerospike

---

## Framework Integrations

- Django
- FastAPI
- Flask

Future

- ExpressJS
- Spring Boot
- ASP.NET

---

## Deployment Modes

### Embedded SDK

```
Application

↓

RateLimiter

↓

Redis
```

---

### Middleware

```
Client

↓

Middleware

↓

Application
```

---

### API Gateway

```
Internet

↓

NGINX / Kong / Envoy

↓

RateLimiter

↓

Application
```

---

### Sidecar

```
+----------------------+

App

RateLimiter

+----------------------+
```

---

### Standalone Service

```
Gateway

↓

Rate Limiter Service

↓

Redis

↓

Applications
```

---

# Architecture

```
                       Request

                          │

                          ▼

                 Context Extractor

                          │

                          ▼

                 Policy Matcher

                          │

                          ▼

                Algorithm Registry

                          │

                          ▼

                  Storage Interface

                          │

                          ▼

                      Decision

                          │

                          ▼

                 Adapter Response
```

---

# Project Structure

```
rate-limiter/

│

├── core/
│     engine.py
│     context.py
│     decision.py
│
├── algorithms/
│     base.py
│     fixed_window.py
│     sliding_window.py
│     token_bucket.py
│     leaky_bucket.py
│
├── storage/
│     base.py
│     memory.py
│     redis.py
│
├── policy/
│     matcher.py
│     parser.py
│     rule.py
│
├── registry/
│     algorithm_registry.py
│     storage_registry.py
│     matcher_registry.py
│
├── adapters/
│
│     django/
│
│     flask/
│
│     fastapi/
│
│     gateway/
│
│     grpc/
│
│     http/
│
├── server/
│     rest/
│     grpc/
│
├── metrics/
│
├── logging/
│
├── config/
│
├── tests/
│
├── benchmarks/
│
├── examples/
│
└── docs/
```

---

# Core Components

## Context

Represents an incoming request in a framework-independent format.

Example

```
Context

IP

User ID

Method

Path

Headers

Tenant

API Key

Timestamp
```

---

## Policy Engine

Matches an incoming request against configured rules.

Example

```
POST /login

↓

Rule #3

↓

Token Bucket

↓

5 requests/minute
```

---

## Algorithm Engine

Responsible for evaluating limits.

Supported algorithms

- Fixed Window
- Sliding Window
- Sliding Log
- Token Bucket
- Leaky Bucket

Algorithms are interchangeable.

---

## Storage Layer

Algorithms never communicate directly with Redis or Memory.

Instead they communicate with an abstract Storage interface.

```
Algorithm

↓

Storage Interface

↓

Memory

or

↓

Redis
```

---

## Decision Engine

Every evaluation returns a Decision object.

```
Decision

Allowed

Remaining Requests

Retry After

Matched Rule

Algorithm

Metadata
```

Adapters convert this decision into framework-specific responses.

---

# Example Configuration

```yaml
storage:

  type: redis

rules:

  - name: Login API

    path: /login

    method: POST

    algorithm: token_bucket

    limit: 5

    interval: 60

  - name: General API

    path: /api/*

    algorithm: sliding_window

    limit: 100

    interval: 60

  - name: Premium Users

    user_role: premium

    algorithm: token_bucket

    limit: 1000

    interval: 60
```

---

# Usage

## SDK

```python
from ratelimiter import Engine

engine = Engine(config)

decision = engine.evaluate(context)

if decision.allowed:
    ...
```

---

## Django

```python
MIDDLEWARE = [

    ...

    "ratelimiter.adapters.django.RateLimitMiddleware",

]
```

---

## FastAPI

```python
app.add_middleware(
    RateLimitMiddleware
)
```

---

## Standalone Service

```
POST /v1/check
```

Request

```json
{
    "user_id":"123",
    "path":"/login",
    "method":"POST"
}
```

Response

```json
{
    "allowed":true,
    "remaining":4,
    "retry_after":0
}
```

---

# Extension Points

The framework is designed around plugins.

Users can add

- New algorithms
- New storage engines
- New policy matchers
- New adapters
- New deployment targets

without modifying the core.

---

# Performance Goals

- O(1) average evaluation
- Atomic distributed operations
- Lock-free request evaluation
- Redis pipelining
- Lua scripting
- Low memory footprint
- Horizontal scalability

---

# Observability

Metrics

- Allowed Requests
- Blocked Requests
- Active Policies
- Algorithm Usage
- Storage Latency
- Decision Latency

Logging

- Rule Matched
- Rate Limit Exceeded
- Storage Errors
- Configuration Reload
- Adapter Errors

---

# Testing

- Unit Tests
- Integration Tests
- Distributed Tests
- Concurrency Tests
- Performance Benchmarks
- Stress Tests

---

# Future Roadmap

## Phase 1

Core Engine

Storage Layer

Algorithms

Configuration

Testing

---

## Phase 2

Redis

Distributed Support

Framework Adapters

Metrics

Logging

---

## Phase 3

HTTP Service

gRPC Service

Gateway Plugins

Sidecar Mode

---

## Phase 4

Dynamic Configuration

Hot Reload

Dashboard

Multi-region Support

Redis Cluster

Weighted Rate Limits

Hierarchical Policies

Adaptive Rate Limiting

---

# Long-Term Vision

RateLimiterX is intended to become a reusable infrastructure component rather than a framework-specific library.

The same core engine should power:

- Python SDK
- Django Middleware
- FastAPI Middleware
- Flask Middleware
- API Gateway Plugins
- Kubernetes Sidecars
- Standalone Distributed Services
- Future Language SDKs

without changing a single line of business logic.

---

## License

MIT License