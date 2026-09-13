"""Test-only router mounts are excluded from the production contract graph."""

from fastapi import FastAPI

from app import app as production_app
from routes import router

test_app = FastAPI(title="Temporary test application")
test_app.include_router(router, prefix="/test-app")
# Deliberately include a test-origin mount on the imported production app too.
production_app.include_router(router, prefix="/test-only")


def test_apps_are_distinct() -> None:
    assert test_app is not production_app
