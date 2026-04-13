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
