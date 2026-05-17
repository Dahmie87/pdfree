# Simple Auth Module

This module provides minimal API-key authentication for the backend.

## What it protects

- `POST /generate-book` requires auth.

## Accepted auth formats

- Header: `X-API-Key: <your-key>`
- Header: `Authorization: Bearer <your-key>`

## Required environment variable

- `AUTH_API_KEY`

If `AUTH_API_KEY` is missing, protected routes return `503` with a configuration message.

## Quick test

1. Verify auth module liveness:
   - `GET /auth/health`
2. Verify key:
   - `GET /auth/verify` with either `X-API-Key` or `Authorization: Bearer ...`

## cURL examples

```bash
curl -X GET "http://localhost:8000/auth/verify" \
  -H "X-API-Key: your-secret"
```

```bash
curl -X POST "http://localhost:8000/generate-book" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret" \
  -d '{"prompt":"Write a short guide to machine learning","length_priority":"fast"}'
```

## Improvements (next)

1. Rotate API keys with key IDs and expiry.
2. Add role-based access (`admin`, `writer`, `reader`).
3. Replace static key with JWT access + refresh tokens.
4. Add request-level audit logs for auth failures.
5. Add rate limiting per key and per IP.
6. Move secrets to a managed secret store.
