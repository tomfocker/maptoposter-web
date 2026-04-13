from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pickle

from app.cache_coverage import CacheRequest, compute_fetch_context, normalize_point
from app.cache_index import CacheEntry, find_covering_entry


@dataclass(frozen=True)
class CacheLookupResult:
    center: tuple[float, float]
    fetch_dist: float
    path: str


def _point_key(point: tuple[float, float]) -> str:
    lat, lon = normalize_point(point)
    return f"{lat:.5f},{lon:.5f}"


def find_reusable_layer(index: dict, layer_name: str, request: CacheRequest) -> CacheLookupResult | None:
    context = compute_fetch_context(request)
    point_key = _point_key(context.fetch_point)
    layer_entries = index.get(point_key, {}).get(layer_name, [])
    entries = [
        CacheEntry(center=tuple(entry["center"]), fetch_dist=entry["fetch_dist"], path=entry["path"])
        for entry in layer_entries
    ]
    match = find_covering_entry(entries, required_fetch_dist=context.fetch_dist)
    if match is None:
        return None
    return CacheLookupResult(center=match.center, fetch_dist=match.fetch_dist, path=match.path)


def load_pickle_from_path(path: str):
    with Path(path).open("rb") as handle:
        return pickle.load(handle)


def register_layer_cache(index: dict, center: tuple[float, float], layer_name: str, fetch_dist: float, path: str) -> None:
    point_key = _point_key(center)
    index.setdefault(point_key, {}).setdefault(layer_name, []).append(
        {
            "center": list(normalize_point(center)),
            "fetch_dist": fetch_dist,
            "path": path,
        }
    )
