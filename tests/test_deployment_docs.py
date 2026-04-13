from pathlib import Path


def test_readme_mentions_slim_and_offline_enhanced_modes():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "精简在线版" in readme
    assert "离线增强版" in readme
    assert "中文文案" in readme


def test_offline_compose_documents_seeded_cache_behavior():
    compose = Path("docker-compose.offline-cn.yml").read_text(encoding="utf-8")
    assert "首次启动" in compose
    assert "在线补全" in compose
