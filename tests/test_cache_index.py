from pathlib import Path

from app.cache_index import CacheEntry, find_covering_entry, load_cache_index, save_cache_index


def test_load_cache_index_returns_empty_when_missing(tmp_path: Path):
    assert load_cache_index(tmp_path / "index.json") == {}


def test_save_and_load_cache_index_round_trip(tmp_path: Path):
    path = tmp_path / "index.json"
    index = {
        "31.23041,121.47374": {
            "graph": [
                CacheEntry(center=(31.23041, 121.47374), fetch_dist=3333.333, path="graph_a.pkl").to_dict()
            ]
        }
    }
    save_cache_index(path, index)
    loaded = load_cache_index(path)
    assert loaded["31.23041,121.47374"]["graph"][0]["path"] == "graph_a.pkl"


def test_find_covering_entry_prefers_smallest_sufficient_entry():
    entries = [
        CacheEntry(center=(31.23041, 121.47374), fetch_dist=6000.0, path="graph_large.pkl"),
        CacheEntry(center=(31.23041, 121.47374), fetch_dist=3333.333, path="graph_medium.pkl"),
        CacheEntry(center=(31.23041, 121.47374), fetch_dist=2000.0, path="graph_small.pkl"),
    ]
    match = find_covering_entry(entries, required_fetch_dist=2500.0)
    assert match.path == "graph_medium.pkl"
