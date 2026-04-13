import pickle
from pathlib import Path

from app.cache_coverage import CacheRequest
from app.cache_runtime import CacheLookupResult, find_reusable_layer, register_layer_cache


def test_find_reusable_layer_hits_larger_cached_entry_for_smaller_request(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    graph_path = cache_dir / "graph_shanghai_6000.pkl"
    graph_path.write_bytes(pickle.dumps({"kind": "graph", "name": "large"}))
    index = {
        "31.23040,121.47370": {
            "graph": [
                {
                    "center": [31.2304, 121.4737],
                    "fetch_dist": 6000.0,
                    "path": str(graph_path),
                }
            ]
        }
    }
    result = find_reusable_layer(
        index=index,
        layer_name="graph",
        request=CacheRequest(point=(31.2304, 121.4737), dist=10000, width=10, height=10),
    )
    assert isinstance(result, CacheLookupResult)
    assert result.path == str(graph_path)


def test_register_layer_cache_adds_index_entry():
    index = {}
    register_layer_cache(
        index=index,
        center=(31.23041, 121.47374),
        layer_name="graph",
        fetch_dist=3333.333,
        path="cache/graph_shanghai_3333.pkl",
    )
    assert index["31.23041,121.47374"]["graph"][0]["fetch_dist"] == 3333.333
