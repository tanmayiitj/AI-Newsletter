"""Shared Jinja2 templates instance."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
