from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class CacheEntry:
    center: tuple[float, float]
    fetch_dist: float
    path: str

    def to_dict(self) -> dict:
        return asdict(self)


def load_cache_index(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_cache_index(path: Path, index: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=2, sort_keys=True)


def find_covering_entry(entries: list[CacheEntry], required_fetch_dist: float) -> CacheEntry | None:
    candidates = [entry for entry in entries if entry.fetch_dist >= required_fetch_dist]
    if not candidates:
        return None
    return sorted(candidates, key=lambda entry: entry.fetch_dist)[0]
