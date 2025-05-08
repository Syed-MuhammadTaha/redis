import pytest
from kvstore.store import KVStore

def test_put_get():
    store = KVStore()
    store.put("key1", "value1")
    value, found = store.get("key1")
    assert found
    assert value == "value1"

def test_get_nonexistent():
    store = KVStore()
    value, found = store.get("nonexistent")
    assert not found
    assert value is None

def test_delete():
    store = KVStore()
    store.put("key1", "value1")
    assert store.delete("key1")
    value, found = store.get("key1")
    assert not found
    assert value is None

def test_delete_nonexistent():
    store = KVStore()
    assert not store.delete("nonexistent")

def test_get_all():
    store = KVStore()
    store.put("key1", "value1")
    store.put("key2", "value2")
    all_items = store.get_all()
    assert len(all_items) == 2
    assert all_items["key1"] == "value1"
    assert all_items["key2"] == "value2"

def test_version_tracking():
    store = KVStore()
    store.put("key1", "value1")
    version1 = store.get_version("key1")
    store.put("key1", "value2")
    version2 = store.get_version("key1")
    assert version2 > version1

def test_thread_safety():
    import threading
    store = KVStore()
    num_threads = 10
    num_operations = 100

    def worker():
        for i in range(num_operations):
            key = f"key{i % 5}"
            store.put(key, f"value{i}")
            store.get(key)
            if i % 2 == 0:
                store.delete(key)

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify the store is in a consistent state
    all_items = store.get_all()
    assert len(all_items) <= 5  # We only used 5 different keys 