"""Storage abstraction tests: the JsonBackend and the StorageService facade
behave exactly like the original file engine, and a backend can be injected."""

import json

from app.services.storage_service import StorageService
from app.storage.json_backend import JsonBackend
from app.storage.backend import StorageBackend


def test_json_backend_roundtrip(tmp_path):
    b = JsonBackend(str(tmp_path))
    assert b.read_list("things.json") == []          # ensures + empty
    b.append("things.json", {"id": 1})
    b.append("things.json", {"id": 2})
    assert b.read_list("things.json") == [{"id": 1}, {"id": 2}]
    b.write_list("things.json", [{"id": 9}])
    assert b.read_list("things.json") == [{"id": 9}]
    # written atomically as pretty JSON on disk
    on_disk = json.load(open(tmp_path / "things.json"))
    assert on_disk == [{"id": 9}]


def test_json_backend_tolerates_corrupt_file(tmp_path):
    (tmp_path / "bad.json").write_text("{ not json")
    b = JsonBackend(str(tmp_path))
    assert b.read_list("bad.json") == []             # corrupt -> empty, no crash


def test_storage_service_delegates_to_backend(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    assert isinstance(s.backend, JsonBackend)
    assert isinstance(s.backend, StorageBackend)     # satisfies the protocol
    s.append("x.json", {"a": 1})
    assert s.read_list("x.json") == [{"a": 1}]
    s.write_list("x.json", [])
    assert s.read_list("x.json") == []
    assert s.data_dir == str(tmp_path)               # kept for backward compat


def test_backend_is_injectable(tmp_path):
    class CountingBackend(JsonBackend):
        reads = 0
        def read_list(self, filename):
            type(self).reads += 1
            return super().read_list(filename)

    injected = CountingBackend(str(tmp_path))
    s = StorageService(data_dir=str(tmp_path), backend=injected)
    s.read_list("y.json")
    assert injected.reads >= 1                        # facade used the injected backend


def test_storage_service_still_ensures_known_files(tmp_path):
    StorageService(data_dir=str(tmp_path))
    # a well-known collection is created on init (as before)
    assert (tmp_path / "tasks.json").exists()
