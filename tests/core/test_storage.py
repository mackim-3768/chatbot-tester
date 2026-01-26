import json
import tempfile
from pathlib import Path

import pytest
from lm_eval_so.core.storage import LocalFileSystemStorage, StorageBackend

class TestLocalFileSystemStorage:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)
            
    @pytest.fixture
    def storage(self, temp_dir):
        return LocalFileSystemStorage(temp_dir)

    def test_save_and_load_json(self, storage):
        key = "data.json"
        data = {"hello": "world"}
        
        path = storage.save_json(key, data)
        assert Path(path).exists()
        
        loaded = storage.load_json(key)
        assert loaded == data

    def test_save_and_load_json_nested(self, storage):
        key = "folder/data.json"
        data = {"foo": 123}
        
        storage.save_json(key, data)
        assert storage.exists(key)
        
        loaded = storage.load_json(key)
        assert loaded == data

    def test_save_jsonl(self, storage):
        key = "data.jsonl"
        data = [{"a": 1}, {"b": 2}]
        
        storage.save_jsonl(key, data)
        
        # Verify content manually
        path = Path(storage.get_path(key))
        with path.open("r") as f:
            lines = [json.loads(line) for line in f]
            assert lines == data

    def test_not_found(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.load_json("nonexistent.json")

    def test_exists(self, storage):
        assert not storage.exists("foo.json")
        storage.save_json("foo.json", {})
        assert storage.exists("foo.json")
