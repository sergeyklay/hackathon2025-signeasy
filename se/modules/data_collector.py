import json
import pickle
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union


class DataCollector(ABC):
    """Abstract base class for collecting and storing data."""

    @abstractmethod
    def store(self, data: Any, key: Optional[str] = None) -> None:
        """Store a piece of data with an optional key."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Cleanup resources if needed."""
        pass


class JSONLCollector(DataCollector):
    """Stores data as JSON Lines format, with each entry on a new line."""

    def __init__(self, file_path: Union[str, Path], ensure_ascii: bool = False):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_ascii = ensure_ascii

    def store(self, data: Any, key: Optional[str] = None) -> None:
        entry = {"timestamp": datetime.now().isoformat(), "key": key, "data": data}

        with open(self.file_path, "a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=self.ensure_ascii)
            f.write("\n")

    def close(self) -> None:
        pass


class PickleCollector(DataCollector):
    """Stores data in pickle format for complex Python objects."""

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = []

    def store(self, data: Any, key: Optional[str] = None) -> None:
        entry = {"timestamp": datetime.now().isoformat(), "key": key, "data": data}
        self.data.append(entry)

    def close(self) -> None:
        with open(self.file_path, "wb") as f:
            pickle.dump(self.data, f)
