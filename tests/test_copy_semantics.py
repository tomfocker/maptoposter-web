from pathlib import Path


def test_index_template_uses_map_range_wording():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert "地图范围" in template
    assert "渲染半径" not in template


def test_readme_mentions_offline_compose_mode():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "docker-compose.offline-cn.yml" in readme
    assert "地图范围" in readme
