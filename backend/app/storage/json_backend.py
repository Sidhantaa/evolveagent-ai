"""JSON file-per-collection storage backend.

This is the *original* StorageService engine, extracted verbatim so behavior is
byte-for-byte identical: one JSON file per collection under ``data_dir``, guarded
by a single process lock, with atomic writes via a temp file + os.replace.
"""

from __future__ import annotations

import json
import os
from threading import Lock
from typing import Any, Callable
from uuid import uuid4


class JsonBackend:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self._lock = Lock()
        os.makedirs(self.data_dir, exist_ok=True)

    def _path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def ensure(self, filename: str) -> None:
        path = self._path(filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as file:
                json.dump([], file)

    def read_list(self, filename: str) -> list[dict[str, Any]]:
        self.ensure(filename)
        with self._lock:
            with open(self._path(filename), "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
        return data if isinstance(data, list) else []

    def append(self, filename: str, item: dict[str, Any]) -> None:
        with self._lock:
            self.ensure(filename)
            with open(self._path(filename), "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
            if not isinstance(data, list):
                data = []
            data.append(item)
            self._atomic_write(filename, data)

    def write_list(self, filename: str, items: list[dict[str, Any]]) -> None:
        with self._lock:
            self.ensure(filename)
            self._atomic_write(filename, items)

    def update_list(self, filename: str, mutator: Callable[[list[dict[str, Any]]], Any]) -> Any:
        # Holds the SAME lock as read_list/append/write_list for the entire
        # read-mutate-write sequence, closing the lost-update race a plain
        # read_list() + write_list() pair has (another thread's append() or
        # write_list() landing in the gap between them would otherwise be
        # silently overwritten by this call's stale snapshot).
        with self._lock:
            self.ensure(filename)
            with open(self._path(filename), "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
            if not isinstance(data, list):
                data = []
            result = mutator(data)
            self._atomic_write(filename, data)
            return result

    def _atomic_write(self, filename: str, items: list[dict[str, Any]]) -> None:
        path = self._path(filename)
        temp_path = f"{path}.{uuid4().hex}.tmp"
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(items, file, indent=2)
        os.replace(temp_path, path)

    def stats(self) -> dict[str, Any]:
        files = [f for f in os.listdir(self.data_dir) if f.endswith(".json")] if os.path.isdir(self.data_dir) else []
        total = sum(len(self.read_list(f)) for f in files)
        return {"kind": "json", "collections": len(files), "total_documents": total}
