# Offline Cache Compose Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an offline-cache Docker packaging flow for major China cities, keep the main image slim, preserve online fallback, and make previously cached map data reusable across poster size changes.

**Architecture:** Keep the current rendering behavior and `dist` semantics, but move cache selection from exact-key lookup toward coverage-aware lookup. Introduce small focused cache helper modules, seed-cache build assets, and an offline Docker Compose override that seeds a named cache volume on first run. User-facing copy changes explain `dist` as a map-range control rather than a strict radius.

**Tech Stack:** Python 3.11, FastAPI, OSMnx, Geopy, pickle/JSON cache files, Docker Compose, pytest for development tests

---

## File Map

### New Files

- `app/cache_coverage.py`
  Pure helpers for translating request inputs into effective fetch coverage and reusable coverage checks.
- `app/cache_index.py`
  JSON-backed cache index loader/saver and "smallest sufficient coverage" lookup helpers.
- `app/cache_runtime.py`
  Runtime bridge that looks up reusable cached layers, registers new ones, and shields `create_map_poster.py` from index details.
- `data/cn_major_cities.json`
  Seed manifest containing the selected China city list and tier metadata.
- `scripts/build_cn_offline_seed.py`
  Seed builder that generates cache files and an `index.json` for the offline cache image.
- `docker-compose.offline-cn.yml`
  Offline-mode override using a named volume plus one-shot cache init service.
- `Dockerfile.seed-cache`
  Minimal image that packages `/seed-cache` assets for distribution.
- `requirements-dev.txt`
  Development-only test dependencies.
- `tests/test_cache_coverage.py`
  Unit tests for distance/coverage math.
- `tests/test_cache_index.py`
  Unit tests for index persistence and selection.
- `tests/test_cache_runtime.py`
  Unit tests for cross-size reuse and new-entry registration.
- `tests/test_seed_manifest.py`
  Tests for the city manifest and seed metadata.
- `tests/test_offline_compose.py`
  Tests that validate offline override wiring and service/volume expectations.
- `tests/test_copy_semantics.py`
  Tests that guard the updated map-range wording in the template and README.

### Modified Files

- `create_map_poster.py`
  Replace direct exact-key cache dependence with coverage-aware runtime lookup before online fetches.
- `app/templates/index.html`
  Change the visible distance label/help text from radius wording to map-range wording.
- `README.md`
  Document the offline compose mode and clarify the map-range semantics.
- `requirements.txt`
  Keep runtime dependencies untouched unless a missing runtime dependency for new modules is discovered.
- `pyproject.toml`
  Keep build metadata as-is unless test/distribution metadata needs a small update.

## Task 1: Add Coverage Math Helpers And Test Harness

**Files:**
- Create: `requirements-dev.txt`
- Create: `app/cache_coverage.py`
- Create: `tests/test_cache_coverage.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cache_coverage.py
from app.cache_coverage import (
    CacheRequest,
    compute_fetch_context,
    normalize_point,
    request_fits_within_cached_coverage,
)


def test_compute_fetch_context_matches_existing_formula_for_default_poster():
    ctx = compute_fetch_context(
        CacheRequest(
            point=(31.2304, 121.4737),
            dist=10000,
            width=12,
            height=16,
            map_x_offset=0.0,
            map_y_offset=0.0,
        )
    )
    assert round(ctx.fetch_dist, 3) == 3333.333
    assert ctx.fetch_point == (31.2304, 121.4737)


def test_compute_fetch_context_expands_for_offsets():
    ctx = compute_fetch_context(
        CacheRequest(
            point=(31.2304, 121.4737),
            dist=10000,
            width=12,
            height=16,
            map_x_offset=0.4,
            map_y_offset=-0.2,
        )
    )
    assert ctx.fetch_dist > 3333.333


def test_request_fits_within_cached_coverage_for_same_center_and_smaller_need():
    request = CacheRequest(
        point=(31.2304, 121.4737),
        dist=8000,
        width=10,
        height=10,
        map_x_offset=0.0,
        map_y_offset=0.0,
    )
    assert request_fits_within_cached_coverage(
        request=request,
        cached_center=(31.2304, 121.4737),
        cached_fetch_dist=4000.0,
    )


def test_normalize_point_rounds_to_stable_precision():
    assert normalize_point((31.2304123, 121.4737444)) == (31.23041, 121.47374)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_cache_coverage.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.cache_coverage'`

- [ ] **Step 3: Write the minimal implementation**

```python
# app/cache_coverage.py
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CacheRequest:
    point: tuple[float, float]
    dist: float
    width: float
    height: float
    map_x_offset: float = 0.0
    map_y_offset: float = 0.0


@dataclass(frozen=True)
class FetchContext:
    fetch_point: tuple[float, float]
    fetch_dist: float


def normalize_point(point: tuple[float, float], precision: int = 5) -> tuple[float, float]:
    lat, lon = point
    return (round(lat, precision), round(lon, precision))


def compute_fetch_context(request: CacheRequest) -> FetchContext:
    compensated_dist = request.dist * (max(request.height, request.width) / min(request.height, request.width)) / 4
    lat_shift_m = request.map_y_offset * compensated_dist
    lon_shift_m = -request.map_x_offset * compensated_dist
    meters_per_deg_lat = 111320.0
    meters_per_deg_lon = 111320.0 * abs(math.cos(math.radians(request.point[0])))
    fetch_point = (
        request.point[0] + lat_shift_m / meters_per_deg_lat,
        request.point[1] + lon_shift_m / max(meters_per_deg_lon, 1e-9),
    )
    offset_extra = max(abs(request.map_x_offset), abs(request.map_y_offset)) * 0.5
    return FetchContext(fetch_point=fetch_point, fetch_dist=compensated_dist * (1 + offset_extra))


def request_fits_within_cached_coverage(
    request: CacheRequest,
    cached_center: tuple[float, float],
    cached_fetch_dist: float,
) -> bool:
    context = compute_fetch_context(request)
    return normalize_point(context.fetch_point) == normalize_point(cached_center) and cached_fetch_dist >= context.fetch_dist
```

```text
# requirements-dev.txt
-r requirements.txt
pytest==8.4.2
PyYAML==6.0.2
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_cache_coverage.py -v`

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add requirements-dev.txt app/cache_coverage.py tests/test_cache_coverage.py
git commit -m "test: add cache coverage helpers"
```

## Task 2: Add JSON Cache Index And Smallest-Sufficient Match Selection

**Files:**
- Create: `app/cache_index.py`
- Create: `tests/test_cache_index.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cache_index.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_cache_index.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.cache_index'`

- [ ] **Step 3: Write the minimal implementation**

```python
# app/cache_index.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_cache_index.py -v`

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add app/cache_index.py tests/test_cache_index.py
git commit -m "feat: add cache index persistence helpers"
```

## Task 3: Refactor Runtime Caching To Reuse Coverage Across Size Changes

**Files:**
- Create: `app/cache_runtime.py`
- Create: `tests/test_cache_runtime.py`
- Modify: `create_map_poster.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cache_runtime.py
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
        "31.23041,121.47374": {
            "graph": [
                {
                    "center": [31.23041, 121.47374],
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


def test_register_layer_cache_adds_index_entry(tmp_path: Path):
    index = {}
    register_layer_cache(
        index=index,
        center=(31.23041, 121.47374),
        layer_name="graph",
        fetch_dist=3333.333,
        path="cache/graph_shanghai_3333.pkl",
    )
    assert index["31.23041,121.47374"]["graph"][0]["fetch_dist"] == 3333.333
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_cache_runtime.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.cache_runtime'`

- [ ] **Step 3: Write the minimal implementation**

```python
# app/cache_runtime.py
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
```

```python
# create_map_poster.py (integration excerpt)
from pathlib import Path

from app.cache_coverage import CacheRequest, compute_fetch_context
from app.cache_index import load_cache_index, save_cache_index
from app.cache_runtime import find_reusable_layer, load_pickle_from_path, register_layer_cache


INDEX_PATH = CACHE_DIR / "index.json"


def _reuse_or_fetch_layer(layer_name, request, fetch_fn, cache_filename):
    index = load_cache_index(INDEX_PATH)
    reusable = find_reusable_layer(index=index, layer_name=layer_name, request=request)
    if reusable is not None:
        print(f"✓ Reusing cached {layer_name} coverage from {reusable.path}")
        return load_pickle_from_path(reusable.path)

    context = compute_fetch_context(request)
    data = fetch_fn(context.fetch_point, context.fetch_dist)
    if data is not None:
        register_layer_cache(
            index=index,
            center=context.fetch_point,
            layer_name=layer_name,
            fetch_dist=context.fetch_dist,
            path=str(Path(CACHE_DIR) / cache_filename),
        )
        save_cache_index(INDEX_PATH, index)
    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_cache_runtime.py tests/test_cache_coverage.py tests/test_cache_index.py -v`

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/cache_runtime.py create_map_poster.py tests/test_cache_runtime.py
git commit -m "feat: reuse cached map coverage across size changes"
```

## Task 4: Add Offline Seed Manifest And Seed-Build Pipeline

**Files:**
- Create: `data/cn_major_cities.json`
- Create: `scripts/build_cn_offline_seed.py`
- Create: `Dockerfile.seed-cache`
- Create: `tests/test_seed_manifest.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_seed_manifest.py
import json
from pathlib import Path


def test_seed_manifest_contains_major_and_mega_tiers():
    manifest = json.loads(Path("data/cn_major_cities.json").read_text(encoding="utf-8"))
    assert "base_tier" in manifest
    assert "mega_city_tier" in manifest
    assert "Beijing" in manifest["mega_city_tier"]["cities"]
    assert manifest["base_tier"]["dist"] == 10000
    assert manifest["mega_city_tier"]["dist"] == 18000
    assert len(manifest["base_tier"]["cities"]) >= 70
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_seed_manifest.py -v`

Expected: FAIL with `FileNotFoundError: data/cn_major_cities.json`

- [ ] **Step 3: Write the minimal implementation**

```json
{
  "base_tier": {
    "dist": 10000,
    "cities": [
      "Beijing",
      "Shanghai",
      "Tianjin",
      "Chongqing",
      "Guangzhou",
      "Shenzhen",
      "Foshan",
      "Dongguan",
      "Zhuhai",
      "Zhongshan",
      "Huizhou",
      "Hangzhou",
      "Ningbo",
      "Wenzhou",
      "Jiaxing",
      "Shaoxing",
      "Jinhua",
      "Taizhou",
      "Huzhou",
      "Nanjing",
      "Suzhou",
      "Wuxi",
      "Changzhou",
      "Nantong",
      "Xuzhou",
      "Yangzhou",
      "Yancheng",
      "Wuhan",
      "Yichang",
      "Xiangyang",
      "Chengdu",
      "Mianyang",
      "Deyang",
      "Yibin",
      "Xi'an",
      "Baoji",
      "Zhengzhou",
      "Luoyang",
      "Nanyang",
      "Changsha",
      "Zhuzhou",
      "Hefei",
      "Wuhu",
      "Fuzhou",
      "Xiamen",
      "Quanzhou",
      "Jinan",
      "Qingdao",
      "Yantai",
      "Weifang",
      "Linyi",
      "Shenyang",
      "Dalian",
      "Harbin",
      "Changchun",
      "Kunming",
      "Guiyang",
      "Nanning",
      "Nanchang",
      "Taiyuan",
      "Shijiazhuang",
      "Urumqi",
      "Lanzhou",
      "Hohhot",
      "Haikou",
      "Sanya",
      "Lhasa",
      "Yinchuan",
      "Xining",
      "Ordos",
      "Qinhuangdao",
      "Zibo",
      "Ningde",
      "Shantou",
      "Jilin"
    ]
  },
  "mega_city_tier": {
    "dist": 18000,
    "cities": [
      "Beijing",
      "Shanghai",
      "Guangzhou",
      "Shenzhen",
      "Chongqing",
      "Chengdu",
      "Wuhan",
      "Hangzhou"
    ]
  }
}
```

```python
# scripts/build_cn_offline_seed.py
from pathlib import Path
import json
import shutil
import subprocess


def main() -> None:
    manifest = json.loads(Path("data/cn_major_cities.json").read_text(encoding="utf-8"))
    output_dir = Path("offline-seed/cn-major-v1")
    output_dir.mkdir(parents=True, exist_ok=True)
    for tier_name in ("base_tier", "mega_city_tier"):
        dist = manifest[tier_name]["dist"]
        for city in manifest[tier_name]["cities"]:
            subprocess.run(
                [
                    "python3",
                    "create_map_poster.py",
                    "--city",
                    city,
                    "--country",
                    "China",
                    "--distance",
                    str(dist),
                    "--theme",
                    "terracotta",
                ],
                check=True,
            )
    for file in Path("cache").glob("*"):
        shutil.copy2(file, output_dir / file.name)


if __name__ == "__main__":
    main()
```

```dockerfile
# Dockerfile.seed-cache
FROM alpine:3.22
WORKDIR /seed-cache
COPY offline-seed/cn-major-v1/ /seed-cache/
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_seed_manifest.py -v`

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add data/cn_major_cities.json scripts/build_cn_offline_seed.py Dockerfile.seed-cache tests/test_seed_manifest.py
git commit -m "feat: add china offline seed manifest"
```

## Task 5: Add Offline Compose Override And Seed Init Flow

**Files:**
- Create: `docker-compose.offline-cn.yml`
- Create: `tests/test_offline_compose.py`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_offline_compose.py
from pathlib import Path
import yaml


def test_offline_compose_defines_cache_init_and_named_volume():
    data = yaml.safe_load(Path("docker-compose.offline-cn.yml").read_text(encoding="utf-8"))
    assert "cache-init" in data["services"]
    assert "map_cache" in data["volumes"]


def test_offline_compose_overrides_app_cache_mount_with_named_volume():
    data = yaml.safe_load(Path("docker-compose.offline-cn.yml").read_text(encoding="utf-8"))
    volumes = data["services"]["maptoposter"]["volumes"]
    assert "map_cache:/app/cache" in volumes
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_offline_compose.py -v`

Expected: FAIL with `FileNotFoundError: docker-compose.offline-cn.yml`

- [ ] **Step 3: Write the minimal implementation**

```yaml
# docker-compose.offline-cn.yml
services:
  maptoposter:
    image: maptoposter-web:latest
    depends_on:
      cache-init:
        condition: service_completed_successfully
    volumes:
      - ./posters:/app/posters
      - map_cache:/app/cache

  cache-init:
    image: maptoposter-cache:cn-major-v1
    volumes:
      - map_cache:/app/cache
    command:
      - /bin/sh
      - -lc
      - |
        if [ -z "$(ls -A /app/cache 2>/dev/null)" ]; then
          cp -R /seed-cache/. /app/cache/
          echo "Seeded offline cache into named volume."
        else
          echo "Cache volume already populated; skipping seed copy."
        fi
    restart: "no"

volumes:
  map_cache:
```

```yaml
# docker-compose.yml
services:
  maptoposter:
    build: .
    image: maptoposter-web:latest
    ports:
      - "8000:8000"
    volumes:
      - ./posters:/app/posters
      - ./cache:/app/cache
    restart: always
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_offline_compose.py -v`

Expected: `2 passed`

Run: `docker compose -f docker-compose.yml -f docker-compose.offline-cn.yml config > /tmp/maptoposter-offline.yml`

Expected: command exits `0`

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml docker-compose.offline-cn.yml tests/test_offline_compose.py
git commit -m "feat: add offline compose override"
```

## Task 6: Update UI And README Copy To Match Original Distance Semantics

**Files:**
- Modify: `app/templates/index.html`
- Modify: `README.md`
- Create: `tests/test_copy_semantics.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_copy_semantics.py
from pathlib import Path


def test_index_template_uses_map_range_wording():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert "地图范围" in template
    assert "渲染半径" not in template


def test_readme_mentions_offline_compose_mode():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "docker-compose.offline-cn.yml" in readme
    assert "地图范围" in readme
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_copy_semantics.py -v`

Expected: FAIL because the old wording is still present

- [ ] **Step 3: Write the minimal implementation**

```html
<!-- app/templates/index.html -->
<label class="block text-sm font-medium text-gray-700 mb-1">4. 地图范围</label>
<input
  type="number"
  name="dist"
  value="4000"
  class="w-full border rounded px-3 py-2 text-sm"
  title="数值越大，海报包含的城市范围越广"
>
<p class="mt-2 text-xs text-gray-500">
  4000-6000 适合小而密的城市中心；8000-12000 适合中等城市或聚焦 downtown；15000-20000 适合大都市更完整的城市视图。
</p>
```

```markdown
<!-- README.md -->
### 离线中国城市缓存模式

如果你希望首次启动就内置中国主要城市的常用地图缓存，同时仍保留在线补全能力，可以使用：

```bash
docker compose -f docker-compose.yml -f docker-compose.offline-cn.yml up -d
```

这里的 `distance`/`dist` 表示海报的地图范围参数，而不是严格的真实半径。推荐区间仍然与原项目保持一致：

- `4000-6000`：小而密的城市中心
- `8000-12000`：中等城市或聚焦 downtown
- `15000-20000`：大都市更完整的城市视图
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_copy_semantics.py tests/test_offline_compose.py tests/test_cache_runtime.py -v`

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/templates/index.html README.md tests/test_copy_semantics.py
git commit -m "docs: clarify map range wording"
```

## Self-Review

### Spec Coverage

- Slim main image plus separate offline cache image: covered by Task 4 and Task 5.
- Preserve online fallback by default: covered by Task 3 and Task 5.
- Seed major China cities plus mega-city extended tier: covered by Task 4.
- Reuse cached map data across size changes: covered by Task 1, Task 2, and Task 3.
- Update user-facing wording without redefining `dist`: covered by Task 6.

### Placeholder Scan

- No `TODO` or `TBD` markers remain.
- Every task has concrete file paths, commands, and expected outcomes.
- Each code step contains actual snippets instead of abstract instructions.

### Type Consistency

- `CacheRequest` is introduced in Task 1 and reused consistently in Task 3.
- `CacheEntry` is introduced in Task 2 and reused consistently in Task 3.
- `find_covering_entry` remains the single "smallest sufficient match" selector.

## Suggested Verification Sequence

Run this broader check after all tasks are complete:

```bash
python3 -m pytest tests/test_cache_coverage.py tests/test_cache_index.py tests/test_cache_runtime.py tests/test_seed_manifest.py tests/test_offline_compose.py tests/test_copy_semantics.py -v
docker compose -f docker-compose.yml -f docker-compose.offline-cn.yml config
```
