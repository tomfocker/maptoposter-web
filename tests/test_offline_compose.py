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
