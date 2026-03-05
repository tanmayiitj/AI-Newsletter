# Data Model: AI Pulse Newsletter

**Date**: 2026-03-03
**Feature**: `001-ai-pulse-newsletter`
**Source**: [spec.md](./spec.md) Key Entities + [research.md](./research.md)

---

## Entities

### 1. ContentItem

An individual article, finding, or news item within a newsletter section.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | ✅ | Headline of the content item |
| summary | string | ✅ | 2-3 sentence summary of the item |
| source_url | string | ✅ | URL to the original source |
| source_name | string | ✅ | Name of the source (e.g., "MIT Technology Review") |
| relevance_score | float | ❌ | 0.0–1.0 relevance score assigned by LLM (default: 0.0) |
| source_date | datetime | ❌ | Publication date of the original source |

**Validation rules**:
- `title`: 1–200 characters
- `summary`: 1–1000 characters
- `source_url`: Must be a valid URL (starts with `http://` or `https://`)
- `relevance_score`: 0.0 ≤ value ≤ 1.0

---

### 2. JobListing

A job posting within the jobs board section.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| role_title | string | ✅ | Job role title (e.g., "ML Engineer") |
| company_name | string | ✅ | Hiring company name |
| location_type | enum | ✅ | One of: `remote`, `hybrid`, `onsite` |
| experience_tier | enum | ✅ | One of: `1-2yr`, `2-4yr` |
| description | string | ✅ | Brief job description |
| apply_url | string | ✅ | External URL to apply |

**Validation rules**:
- `role_title`: 1–150 characters
- `company_name`: 1–150 characters
- `location_type`: Must be one of `remote`, `hybrid`, `onsite`
- `experience_tier`: Must be one of `1-2yr`, `2-4yr`
- `description`: 1–500 characters
- `apply_url`: Must be a valid URL

---

### 3. NewsletterSection

A thematic block within a newsletter edition.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| section_type | enum | ✅ | One of: `trending_topics`, `top_developments`, `corporate_tools`, `future_requirements`, `jobs_board` |
| display_order | integer | ✅ | Rendering order (1-based) |
| title | string | ✅ | Display title for the section |
| description | string | ❌ | Brief narrative intro for the section |
| content_items | list[ContentItem] | ✅ | Content items (empty list if none; placeholder rendered in frontend) |
| job_listings | list[JobListing] | ❌ | Only populated for `jobs_board` section type |

**Validation rules**:
- `section_type`: Must be a valid enum value
- `display_order`: ≥ 1
- `title`: 1–200 characters
- `content_items`: List (may be empty per FR-012 placeholder policy)
- `job_listings`: Only present when `section_type == "jobs_board"`

**Section display order convention**:
1. `trending_topics`
2. `top_developments`
3. `corporate_tools`
4. `future_requirements`
5. `jobs_board`

---

### 4. NewsletterEdition

A single newsletter issue — the top-level document stored in MongoDB.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | PyObjectId | ❌ | MongoDB `_id`, auto-generated |
| edition_number | integer | ✅ | Sequential edition number |
| headline | string | ✅ | Main headline for this edition |
| executive_summary | string | ✅ | 2-4 sentence overview of the edition |
| status | enum | ✅ | One of: `draft`, `published` |
| sections | list[NewsletterSection] | ✅ | Ordered list of content sections |
| created_at | datetime | ✅ | Auto-set on creation (UTC) |
| published_at | datetime | ❌ | Set when status transitions to `published` |

**Validation rules**:
- `edition_number`: ≥ 1, unique
- `headline`: 1–300 characters
- `executive_summary`: 1–2000 characters
- `status`: Must be `draft` or `published`
- `sections`: Must contain exactly 5 sections (one per `section_type`)
- `created_at`: Auto-set, immutable after creation

**State transitions**:
- `draft` → `published`: Set `published_at` to current UTC time. Once published, content is immutable.

---

## Relationships

```text
NewsletterEdition (1)
  └── has many → NewsletterSection (5 per edition)
       ├── has many → ContentItem (≥0 items)
       └── has many → JobListing (only for jobs_board section)
```

All entities are embedded within the `NewsletterEdition` document (no separate collections). This matches MongoDB's document-oriented model and avoids joins.

---

## MongoDB Collection

**Collection name**: `editions`

**Indexes**:
- `edition_number`: Unique ascending index (fast lookup by number)
- `status, created_at`: Compound index (efficient "latest published" query)
- `created_at`: Descending index (archive listing, pagination)

---

## Enumerations

### SectionType

```
trending_topics
top_developments
corporate_tools
future_requirements
jobs_board
```

### LocationType

```
remote
hybrid
onsite
```

### ExperienceTier

```
1-2yr
2-4yr
```

### EditionStatus

```
draft
published
```
