# API Contract: Health Endpoint

**Base path**: `/api/v1`
**Authentication**: None (public)

---

## GET /api/v1/health

**Description**: Returns the health status of the application and its dependencies.
**Auth**: None (public)

### Responses

| Status | Description | Body |
|--------|-------------|------|
| 200 | Service is healthy | `HealthResponse` |
| 503 | Database unreachable | `HealthResponse` with `database: "unhealthy"` |

### Example Response (200)

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-03-03T12:00:00Z"
}
```

### Example Response (503)

```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "timestamp": "2026-03-03T12:00:00Z"
}
```
