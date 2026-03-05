# API Contract: Newsletter Endpoints

**Base path**: `/api/v1`
**Authentication**: `X-API-Key` header (required for write operations only)

---

## POST /api/v1/newsletter/generate

**Description**: Triggers generation of a new newsletter edition via LLM.
**Auth**: Required (`X-API-Key` header)

### Request

- **Headers**: `X-API-Key: <api-key-from-env>`
- **Body**: None

### Responses

| Status | Description | Body |
|--------|-------------|------|
| 201 | Edition created successfully | `NewsletterEdition` (full object with all sections) |
| 401 | Missing or invalid API key | `{ "detail": "Invalid or missing API key" }` |
| 409 | Generation already in progress | `{ "detail": "Newsletter generation is already in progress" }` |
| 502 | LLM service unavailable or returned unparseable content | `{ "detail": "LLM service error: <message>" }` |
| 500 | Internal server error | `{ "detail": "Internal server error" }` |

### Example Response (201)

```json
{
  "id": "65f2a1b3c4d5e6f7a8b9c0d1",
  "edition_number": 42,
  "headline": "AI Reshapes Enterprise Workflows as Agents Go Mainstream",
  "executive_summary": "This week saw major breakthroughs in...",
  "status": "published",
  "sections": [
    {
      "section_type": "trending_topics",
      "display_order": 1,
      "title": "Trending AI Topics",
      "description": "The conversation everyone is having...",
      "content_items": [
        {
          "title": "Autonomous AI Agents Enter the Enterprise",
          "summary": "Major tech companies unveiled agent frameworks...",
          "source_url": "https://example.com/article",
          "source_name": "TechReview",
          "relevance_score": 0.95,
          "source_date": "2026-03-01T00:00:00Z"
        }
      ],
      "job_listings": null
    }
  ],
  "created_at": "2026-03-03T12:00:00Z",
  "published_at": "2026-03-03T12:04:30Z"
}
```

---

## GET /api/v1/newsletter/latest

**Description**: Returns the most recently published newsletter edition.
**Auth**: None (public)

### Responses

| Status | Description | Body |
|--------|-------------|------|
| 200 | Latest edition returned | `NewsletterEdition` |
| 404 | No editions exist | `{ "detail": "No newsletter editions found" }` |

---

## GET /api/v1/newsletter/{edition_id}

**Description**: Returns a specific newsletter edition by its MongoDB ID.
**Auth**: None (public)

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| edition_id | string | MongoDB ObjectId as string |

### Responses

| Status | Description | Body |
|--------|-------------|------|
| 200 | Edition found | `NewsletterEdition` |
| 404 | Edition not found | `{ "detail": "Edition not found" }` |
| 422 | Invalid edition_id format | Validation error |

---

## GET /api/v1/newsletter/archive

**Description**: Returns a paginated list of published editions (newest first) for the archive page.
**Auth**: None (public)

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | integer | 1 | Page number (1-based) |
| per_page | integer | 10 | Editions per page (fixed at 10 per FR-004) |

### Responses

| Status | Description | Body |
|--------|-------------|------|
| 200 | Archive page returned | `ArchiveResponse` |

### Example Response (200)

```json
{
  "editions": [
    {
      "id": "65f2a1b3c4d5e6f7a8b9c0d1",
      "edition_number": 42,
      "headline": "AI Reshapes Enterprise Workflows...",
      "executive_summary": "This week saw major breakthroughs...",
      "created_at": "2026-03-03T12:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 10,
  "total_pages": 5
}
```

**Note**: Archive list items are a lightweight projection — `sections` are not included to keep the response small. Full edition data is fetched via `GET /api/v1/newsletter/{edition_id}`.

---

## Page Routes (Jinja2 HTML)

These routes serve server-rendered HTML pages.

| Method | Path | Description | Template |
|--------|------|-------------|----------|
| GET | `/` | Homepage — latest newsletter edition | `index.html` / `empty.html` |
| GET | `/archive` | Archive listing (paginated) | `archive.html` |
| GET | `/edition/{edition_id}` | Single edition full view | `edition.html` |
