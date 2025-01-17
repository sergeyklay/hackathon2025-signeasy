import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from se.modules.data_collector import JSONLCollector, PickleCollector


@pytest.fixture
def jsonl_file() -> Generator[Path, None, None]:
    file_path = Path("test_data.jsonl")
    yield file_path
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def jsonl_collector(jsonl_file: Path) -> JSONLCollector:
    return JSONLCollector(jsonl_file)


@pytest.fixture
def pickle_file() -> Generator[Path, None, None]:
    file_path = Path("test_data.pkl")
    yield file_path
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def pickle_collector(pickle_file: Path) -> PickleCollector:
    return PickleCollector(pickle_file)


def test_jsonl_store_data_without_key(
    jsonl_collector: JSONLCollector, jsonl_file: Path
) -> None:
    test_data = {"test": "value"}
    jsonl_collector.store(test_data)

    with open(jsonl_file, "r", encoding="utf-8") as f:
        stored = json.loads(f.readline())

    assert stored["data"] == test_data
    assert stored["key"] is None
    assert datetime.fromisoformat(stored["timestamp"])


def test_jsonl_store_data_with_key(
    jsonl_collector: JSONLCollector, jsonl_file: Path
) -> None:
    test_data = {"test": "value"}
    test_key = "test_key"
    jsonl_collector.store(test_data, test_key)

    with open(jsonl_file, "r", encoding="utf-8") as f:
        stored = json.loads(f.readline())

    assert stored["data"] == test_data
    assert stored["key"] == test_key


def test_jsonl_multiple_entries(
    jsonl_collector: JSONLCollector, jsonl_file: Path
) -> None:
    entries = [{"id": i} for i in range(3)]
    for entry in entries:
        jsonl_collector.store(entry)

    with open(jsonl_file, "r", encoding="utf-8") as f:
        stored = [json.loads(line) for line in f]

    assert len(stored) == len(entries)
    for stored_entry, original_entry in zip(stored, entries):
        assert stored_entry["data"] == original_entry


def test_pickle_store_data_without_key(
    pickle_collector: PickleCollector, pickle_file: Path
) -> None:
    test_data = {"test": "value"}
    pickle_collector.store(test_data)
    pickle_collector.close()

    with open(pickle_file, "rb") as f:
        stored = pickle.load(f)

    assert len(stored) == 1
    assert stored[0]["data"] == test_data
    assert stored[0]["key"] is None
    assert datetime.fromisoformat(stored[0]["timestamp"])


def test_pickle_store_data_with_key(
    pickle_collector: PickleCollector, pickle_file: Path
) -> None:
    test_data = {"test": "value"}
    test_key = "test_key"
    pickle_collector.store(test_data, test_key)
    pickle_collector.close()

    with open(pickle_file, "rb") as f:
        stored = pickle.load(f)

    assert len(stored) == 1
    assert stored[0]["data"] == test_data
    assert stored[0]["key"] == test_key


def test_pickle_multiple_entries(
    pickle_collector: PickleCollector, pickle_file: Path
) -> None:
    entries = [{"id": i} for i in range(3)]
    for entry in entries:
        pickle_collector.store(entry)
    pickle_collector.close()

    with open(pickle_file, "rb") as f:
        stored = pickle.load(f)

    assert len(stored) == len(entries)
    for stored_entry, original_entry in zip(stored, entries):
        assert stored_entry["data"] == original_entry
