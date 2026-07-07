"""Storage backend protocol — the seam that lets us swap JSON for Postgres.

The whole app talks to collections of JSON-like documents through
``StorageService`` (read_list / append / write_list). This protocol captures
exactly that contract so a JSON file backend and a Postgres (JSONB) backend are
interchangeable, with no change to the 140+ services above.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StorageBackend(Protocol):
    """A named collection of documents (one 'filename' == one collection)."""

    def ensure(self, filename: str) -> None:
        """Make sure the collection exists (create empty if missing)."""
        ...

    def read_list(self, filename: str) -> list[dict[str, Any]]:
        """Return all documents in the collection (empty list if none)."""
        ...

    def append(self, filename: str, item: dict[str, Any]) -> None:
        """Append one document to the collection."""
        ...

    def write_list(self, filename: str, items: list[dict[str, Any]]) -> None:
        """Replace the whole collection with ``items``."""
        ...
