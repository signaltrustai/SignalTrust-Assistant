"""Tests for the OmniJARVIS core memory store."""

import pytest

from assistant.core.memory_store import MemoryStore


@pytest.fixture
def store(tmp_path):
    return MemoryStore(store_file=tmp_path / "store.json")


class TestMemoryStore:
    def test_add_entry(self, store):
        entry = store.add_entry({"content": "test note"}, tags=["test"])
        assert entry["id"] == 1
        assert entry["data"]["content"] == "test note"
        assert "test" in entry["tags"]

    def test_get_entries(self, store):
        store.add_entry({"content": "note 1"})
        store.add_entry({"content": "note 2"})
        entries = store.get_entries()
        assert len(entries) == 2
        # Most recent first
        assert entries[0]["data"]["content"] == "note 2"

    def test_get_entries_with_limit(self, store):
        for i in range(10):
            store.add_entry({"content": f"note {i}"})
        entries = store.get_entries(limit=3)
        assert len(entries) == 3

    def test_get_entries_filter_tags(self, store):
        store.add_entry({"content": "tagged"}, tags=["important"])
        store.add_entry({"content": "untagged"})
        entries = store.get_entries(tags=["important"])
        assert len(entries) == 1

    def test_search(self, store):
        store.add_entry({"content": "deploy to production"})
        store.add_entry({"content": "update docs"})
        results = store.search("deploy")
        assert len(results) == 1

    def test_get_entry(self, store):
        entry = store.add_entry({"content": "findme"})
        found = store.get_entry(entry["id"])
        assert found is not None
        assert found["data"]["content"] == "findme"

    def test_delete_entry(self, store):
        entry = store.add_entry({"content": "deleteme"})
        assert store.delete_entry(entry["id"])
        assert store.get_entry(entry["id"]) is None

    def test_count(self, store):
        assert store.count() == 0
        store.add_entry({"content": "one"})
        assert store.count() == 1

    def test_summarise_session(self, store):
        store.add_entry({"content": "first note"})
        summary = store.summarise_session()
        assert "first note" in summary

    def test_persistence(self, tmp_path):
        sf = tmp_path / "store.json"
        s1 = MemoryStore(store_file=sf)
        s1.add_entry({"content": "persistent"})
        s2 = MemoryStore(store_file=sf)
        assert s2.count() == 1
