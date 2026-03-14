"""Jinja2 HTML page routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from backend.config.templates import templates
from backend.services import newsletter_service

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Render the homepage with the latest newsletter or empty state."""
    edition = await newsletter_service.get_latest()
    if edition is None:
        return templates.TemplateResponse(request, "empty.html")
    return templates.TemplateResponse(
        request, "index.html", {"edition": edition}
    )


@router.get("/archive", response_class=HTMLResponse)
async def archive_page(request: Request, page: int = 1):
    """Render the archive listing page with search and month filter."""
    archive = await newsletter_service.list_paginated(page=page, per_page=10)
    years = await newsletter_service.get_available_years()
    return templates.TemplateResponse(
        request, "archive.html", {"archive": archive, "years": years}
    )


@router.get("/edition/{edition_id}", response_class=HTMLResponse)
async def edition_page(request: Request, edition_id: str):
    """Render a single edition full-view page."""
    edition = await newsletter_service.get_by_id(edition_id)
    if edition is None:
        return templates.TemplateResponse(request, "empty.html")
    return templates.TemplateResponse(
        request, "edition.html", {"edition": edition}
    )
