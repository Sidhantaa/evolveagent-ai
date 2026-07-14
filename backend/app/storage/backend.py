"""Storage backend protocol — the seam that lets us swap JSON for Postgres.

The whole app talks to collections of JSON-like documents through
``StorageService`` (read_list / append / write_list). This protocol captures
exactly that contract so a JSON file backend and a Postgres (JSONB) backend are
interchangeable, with no change to the 140+ services above.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable


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

    def update_list(self, filename: str, mutator: Callable[[list[dict[str, Any]]], Any]) -> Any:
        """Atomically read the collection, call ``mutator(items)`` to mutate it
        in place, then write the result back -- all under one lock/transaction,
        so no other read_list/append/write_list/update_list call for the same
        collection can land in between and be silently lost. Returns whatever
        ``mutator`` returns. Use this instead of a separate read_list() +
        write_list() pair whenever the write depends on the read (a
        find-mutate-persist sequence) -- that pattern is not atomic otherwise."""
        ...

    def stats(self) -> dict[str, Any]:
        """Lightweight status: ``{kind, collections, total_documents}``."""
        ...
