"""A small HTTP contract with a bounded query and response model."""

from fastapi import APIRouter, Query
from pydantic import BaseModel


class Book(BaseModel):
    """A title returned by the reading-list endpoint."""

    title: str


router = APIRouter(tags=["books"])


@router.get("/books", response_model=list[Book])
def list_books(limit: int = Query(default=10, ge=1, le=100)) -> list[Book]:
    """Return up to the requested number of books."""
    return [Book(title="The Python Tutorial")][:limit]
